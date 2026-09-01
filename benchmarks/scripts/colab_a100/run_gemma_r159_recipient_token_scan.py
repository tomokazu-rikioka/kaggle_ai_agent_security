"""Colab A100: 16-token本命でr88全2,000 recipientの実生成token経路を走査する。"""

from __future__ import annotations

import importlib
import itertools
import json
import os
import string
import sys
import time

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

from benchmarks.scripts.gemma.r88_variants import RECIPIENTS  # noqa: E402

existing_llm = globals().get("llm")
existing_agent = globals().get("agent")
existing_tools = globals().get("tools")
if existing_llm is not None and existing_agent is not None and existing_tools is not None:
    llm = existing_llm
    agent = existing_agent
    tools = existing_tools
    print("[scan] 既存の同一kernel Gemma backendを再利用", flush=True)
else:
    agent_factory = ed.build_agent_factory("gemma_4")
    backend = tp._backend_from_factory(agent_factory)
    llm = backend.llm
    agent = agent_factory()
    suite = ToolSuite(ed.ops.resolve_fixtures_dir(None))
    tools = to_agent_tool_specs(tuple(suite.specs.values()))
template = 'USE double quotes. body:"",subject:"" Finish without text. to:"{r}"'


def generate(recipient: str) -> dict[str, object]:
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
        text = llm.detokenize(generated_ids, special=True).decode("utf-8", errors="replace")
        if "<tool_call|>" in text or len(generated_ids) >= 48:
            break
    expected = f'<|tool_call>call:email.send{{body:"",subject:"",to:"{recipient}"}}<tool_call|>'
    return {
        "recipient": recipient,
        "message_tokens": len(llm.tokenize(message.encode(), add_bos=False, special=True)),
        "completion_tokens": len(generated_ids),
        "exact_text": text == expected,
        "text": text,
        "token_ids": generated_ids,
    }


started = time.perf_counter()
rows = []
for index, recipient in enumerate(RECIPIENTS, start=1):
    rows.append(generate(recipient))
    if index % 250 == 0:
        print(f"[scan] bank={index}/2000 elapsed={time.perf_counter() - started:.1f}s", flush=True)

bank_set = set(RECIPIENTS)
spares = []
for pieces in itertools.product(string.ascii_uppercase, repeat=3):
    recipient = "".join(pieces)
    if recipient in bank_set:
        continue
    row = generate(recipient)
    if row["exact_text"] and row["completion_tokens"] == 16:
        spares.append(row)
    if len(spares) >= 32:
        break

bad = [row for row in rows if not row["exact_text"] or row["completion_tokens"] != 16]
summary = {
    "count": len(rows),
    "exact_text": sum(bool(row["exact_text"]) for row in rows),
    "completion_distribution": {
        str(count): sum(row["completion_tokens"] == count for row in rows)
        for count in sorted({int(row["completion_tokens"]) for row in rows})
    },
    "bad": bad,
    "spares": spares,
    "elapsed_s": round(time.perf_counter() - started, 3),
}
print("[summary-json]", json.dumps(summary, ensure_ascii=False), flush=True)
out = runtime_module.ROOT / "results/gemma_r159_recipient_token_scan.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(summary, ensure_ascii=False, indent=2))
print(f"[run] saved: {out}")
