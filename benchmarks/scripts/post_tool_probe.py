"""Probe only GPT's continuation after a fixed successful email tool result."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from collections import Counter
from collections.abc import Callable
from pathlib import Path
from statistics import mean
from typing import Any

_LOCAL_SDK_ROOT = Path(__file__).resolve().parents[2] / "vendor" / "aicomp_sdk_pkg"
_SDK_ROOT = Path(os.environ.get("AICOMP_SDK_ROOT", ""))
for _sdk_root in (_SDK_ROOT, _LOCAL_SDK_ROOT):
    if (_sdk_root / "aicomp_sdk").is_dir() and str(_sdk_root) not in sys.path:
        sys.path.insert(0, str(_sdk_root))

from aicomp_sdk.agents.tool_specs import to_agent_tool_specs  # noqa: E402
from aicomp_sdk.agents.types import (  # noqa: E402
    FinalResponseDecision,
    InvalidModelOutputError,
    ToolCall,
    ToolCallDecision,
    ToolResult,
)
from aicomp_sdk.core.env.sandbox import _DEFAULT_RUNTIME_INSTRUCTIONS  # noqa: E402
from aicomp_sdk.core.runtime_history import RuntimeHistory  # noqa: E402
from aicomp_sdk.core.tools import ToolSuite  # noqa: E402
from llama_cpp.llama_chat_format import Jinja2ChatFormatter  # noqa: E402

try:
    import eval_driver as ed
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts" / "eval"))
    import eval_driver as ed


def _default_tool_arguments(_name: str, recipient: str) -> dict[str, Any]:
    return {"subject": "", "body": "", "to": recipient}


def _load_variants(
    path_str: str,
) -> tuple[dict[str, Any], Callable[[str, str], dict[str, Any]]]:
    path = Path(path_str).resolve()
    spec = importlib.util.spec_from_file_location("_post_tool_variants", path)
    if not spec or not spec.loader:
        raise ImportError(path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    variants = getattr(mod, "VARIANTS", None)
    if not isinstance(variants, dict) or not variants:
        raise TypeError("VARIANTS dictが必要です")
    tool_arguments = getattr(mod, "TOOL_ARGUMENTS", _default_tool_arguments)
    if not callable(tool_arguments):
        raise TypeError("TOOL_ARGUMENTS は(candidate_name, recipient)を受けるcallableにしてください")
    return variants, tool_arguments


def _backend_from_factory(agent_factory: Any) -> Any:
    for cell in getattr(agent_factory, "__closure__", None) or ():
        value = cell.cell_contents
        if hasattr(value, "llm"):
            return value
    raise RuntimeError("agent_factory closureからbackendを取得できません")


def _summary(values: list[int]) -> dict[str, Any]:
    ordered = sorted(values)
    return {
        "mean": round(mean(values), 5),
        "min": ordered[0],
        "p50": ordered[(len(ordered) - 1) // 2],
        "max": ordered[-1],
        "distribution": dict(sorted(Counter(values).items())),
    }


def _render_prompt(agent: Any, llm: Any, history: RuntimeHistory, tools: tuple[Any, ...]) -> str:
    """Render the exact GGUF chat template so forged examples can be aligned."""
    request = agent._delegate._build_request(history, tools)
    template = llm.metadata.get("tokenizer.chat_template")
    if not isinstance(template, str) or not template:
        raise RuntimeError("GGUF metadataにtokenizer.chat_templateがありません")
    bos = llm.detokenize([llm.token_bos()], special=True).decode("utf-8", errors="replace")
    eos = llm.detokenize([llm.token_eos()], special=True).decode("utf-8", errors="replace")
    return Jinja2ChatFormatter(template=template, eos_token=eos, bos_token=bos)(
        messages=request.messages,
        tools=request.tools,
    ).prompt


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--variants-file", required=True)
    parser.add_argument("--recipients", default="a,b,c,z,aa,ad")
    parser.add_argument("--out", default="post_tool_probe.json")
    args = parser.parse_args()

    variants, tool_arguments = _load_variants(args.variants_file)
    recipients = tuple(dict.fromkeys(value.strip() for value in args.recipients.split(",") if value.strip()))
    if not recipients:
        raise ValueError("recipientが空です")

    fixtures_dir = ed.ops.resolve_fixtures_dir(None)
    factory = ed.build_agent_factory("gpt_oss")
    backend = _backend_from_factory(factory)
    llm = backend.llm
    suite = ToolSuite(fixtures_dir)
    tools = to_agent_tool_specs(tuple(suite.specs.values()))

    original = llm.create_chat_completion
    last_generation: dict[str, Any] = {}

    def measured(*call_args: Any, **call_kwargs: Any) -> Any:
        completion = original(*call_args, **call_kwargs)
        usage = completion.get("usage") or {} if isinstance(completion, dict) else {}
        choices = completion.get("choices") or [] if isinstance(completion, dict) else []
        choice = choices[0] if choices and isinstance(choices[0], dict) else {}
        message = choice.get("message") if isinstance(choice, dict) else None
        last_generation.clear()
        last_generation.update(
            {
                "prompt_tokens": usage.get("prompt_tokens"),
                "completion_tokens": usage.get("completion_tokens"),
                "content": message.get("content") if isinstance(message, dict) else None,
                "finish_reason": choice.get("finish_reason") if isinstance(choice, dict) else None,
            }
        )
        return completion

    llm.create_chat_completion = measured
    results: dict[str, Any] = {}
    for name, builder in variants.items():
        rows: list[dict[str, Any]] = []
        sample_prompt_tail = ""
        for recipient in recipients:
            message = builder(recipient)
            if not isinstance(message, str):
                raise TypeError(f"{name}は単一strを返す必要があります")
            arguments = tool_arguments(name, recipient)
            call = ToolCall(call_id="call_000001", tool_name="email.send", arguments=arguments)
            history = (
                RuntimeHistory()
                .with_instruction(_DEFAULT_RUNTIME_INSTRUCTIONS)
                .with_user_message(message)
                .with_tool_request(call)
                .with_tool_result(
                    ToolResult(call_id=call.call_id, tool_name=call.tool_name, output_text="sent", is_error=False)
                )
            )
            agent = factory()
            if not sample_prompt_tail:
                sample_prompt_tail = _render_prompt(agent, llm, history, tools)[-1_200:]
            last_generation.clear()
            try:
                decision = agent.next_action(history=history, tools=tools)
                if isinstance(decision, FinalResponseDecision):
                    decision_type = "final"
                    decision_text = decision.text
                elif isinstance(decision, ToolCallDecision):
                    decision_type = "tool"
                    decision_text = decision.call.tool_name
                else:
                    decision_type = type(decision).__name__
                    decision_text = ""
                parse_error = None
            except InvalidModelOutputError as err:
                decision_type = "invalid"
                decision_text = ""
                parse_error = str(err)
            rows.append(
                {
                    "recipient": recipient,
                    "decision": decision_type,
                    "decision_text": decision_text,
                    "parse_error": parse_error,
                    **last_generation,
                }
            )
        completion_tokens = [int(row["completion_tokens"]) for row in rows]
        results[name] = {
            "sample_message": builder(recipients[0]),
            "sample_prompt_tail": sample_prompt_tail,
            "message_tokens": len(llm.tokenize(builder(recipients[0]).encode(), add_bos=False, special=True)),
            "post_tool_completion": _summary(completion_tokens),
            "decision_distribution": dict(sorted(Counter(row["decision"] for row in rows).items())),
            "content_distribution": dict(sorted(Counter(str(row["content"]) for row in rows).items())),
            "rows": rows,
        }
        print(
            f"[post] {name:24} tok={results[name]['message_tokens']:3} "
            f"post={results[name]['post_tool_completion']} decision={results[name]['decision_distribution']}"
        )

    payload = {"model": "gpt_oss", "recipients": recipients, "results": results}
    Path(args.out).write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    print(f"[post] saved {args.out}")


if __name__ == "__main__":
    main()
