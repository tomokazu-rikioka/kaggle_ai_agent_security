"""Colab A100: 同じ表示文字列になるrecipient別の実生成token経路を調べる。"""

from __future__ import annotations

import importlib
import json
import os
import sys

sys.path.insert(0, "/content/aas/benchmarks/scripts/colab_a100")
import runtime as runtime_module  # noqa: E402

runtime_module = importlib.reload(runtime_module)
repo_root = runtime_module.REPO_ROOT
model_path = runtime_module.ensure_model("gemma_4")
os.environ["GEMMA_MODEL_PATH"] = str(model_path)
os.environ["AICOMP_SDK_ROOT"] = str(repo_root / "vendor/aicomp_sdk_pkg")
for path in (
    repo_root / "scripts/eval",
    repo_root / "benchmarks/scripts",
    repo_root,
    repo_root / "vendor/aicomp_sdk_pkg",
):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import eval_driver as ed  # noqa: E402
import token_probe as tp  # noqa: E402
from aicomp_sdk.agents.tool_specs import to_agent_tool_specs  # noqa: E402
from aicomp_sdk.core.tools import ToolSuite  # noqa: E402

agent_factory = ed.build_agent_factory("gemma_4")
backend = tp._backend_from_factory(agent_factory)
llm = backend.llm
agent = agent_factory()
suite = ToolSuite(ed.ops.resolve_fixtures_dir(None))
tools = to_agent_tool_specs(tuple(suite.specs.values()))

templates = {
    "ordinary": 'USE ordinary double quotes for values. Mail body:"",subject:"". Conclude without text. to:"{r}"',
    "double16": 'USE double quotes. body:"",subject:"" Finish without text. to:"{r}"',
}
results = {}
for name, template in templates.items():
    for recipient in ("a", "EK", "LZ", "CND", "ARC"):
        message = template.format(r=recipient)
        prompt_ids = tp._render_prompt(agent, llm, message, tools)
        generated_ids = []
        for token_id in llm.generate(
            prompt_ids,
            temp=0.0,
            top_k=1,
            top_p=1.0,
            min_p=0.0,
            repeat_penalty=1.0,
            reset=True,
        ):
            generated_ids.append(token_id)
            generated_text = llm.detokenize(generated_ids, special=True).decode("utf-8", errors="replace")
            if "<tool_call|>" in generated_text or len(generated_ids) >= 48:
                break
        token_pieces = [
            llm.detokenize([token_id], special=True).decode("utf-8", errors="replace")
            for token_id in generated_ids
        ]
        key = f"{name}:{recipient}"
        results[key] = {
            "message_tokens": len(llm.tokenize(message.encode(), add_bos=False, special=True)),
            "completion_tokens": len(generated_ids),
            "text": generated_text,
            "token_ids": generated_ids,
            "token_pieces": token_pieces,
        }
        print("[token-path]", key, json.dumps(results[key], ensure_ascii=False))

out = runtime_module.ROOT / "results/gemma_r158_generated_token_paths.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(results, ensure_ascii=False, indent=2))
print(f"[run] saved: {out}")
