"""r042上位片の2-token組合せでtool後の即return logitを探索する。"""

from __future__ import annotations

import argparse
import base64
import heapq
import json
import os
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

try:
    import gpt_return_logit_probe as probe
    import gpt_return_trigger_sweep as trigger
except ModuleNotFoundError:
    from benchmarks.scripts import gpt_return_logit_probe as probe
    from benchmarks.scripts import gpt_return_trigger_sweep as trigger

from benchmarks.scripts.gpt.r111a_candidates import CANDIDATES  # noqa: E402

_LOCAL_SDK_ROOT = _REPO_ROOT / "vendor" / "aicomp_sdk_pkg"
_SDK_ROOT = Path(os.environ.get("AICOMP_SDK_ROOT", ""))
for _sdk_root in (_SDK_ROOT, _LOCAL_SDK_ROOT):
    if (_sdk_root / "aicomp_sdk").is_dir() and str(_sdk_root) not in sys.path:
        sys.path.insert(0, str(_sdk_root))

from aicomp_sdk.agents.tool_specs import to_agent_tool_specs  # noqa: E402
from aicomp_sdk.core.tools import ToolSuite  # noqa: E402

try:
    import eval_driver as ed
except ModuleNotFoundError:
    sys.path.insert(0, str(_REPO_ROOT / "scripts" / "eval"))
    import eval_driver as ed


# r042の標準出力へ残った上位20片に、終了意味の基本語を加える。
_SEEDS = tuple(
    dict.fromkeys(
        (
            "Delete",
            "delete",
            "=True",
            "']}",
            " delete",
            " echo",
            "Stop",
            "Finish",
            " sleep",
            " print",
            " STOP",
            "finish",
            " Stop",
            " filter",
            "account",
            " alert",
            "list",
            " error",
            ".print",
            " stop",
            "done",
            "end",
            "final",
            "finished",
            "return",
            "silent",
            "nothing",
        )
    )
)


def _common_prefix(left: list[int], right: list[int]) -> int:
    count = 0
    for left_id, right_id in zip(left, right, strict=False):
        if left_id != right_id:
            break
        count += 1
    return count


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--recipient", default="a")
    parser.add_argument("--keep", type=int, default=100)
    parser.add_argument("--out", default="gpt_return_pair_sweep.json")
    args = parser.parse_args()

    fixtures_dir = ed.ops.resolve_fixtures_dir(None)
    factory = ed.build_agent_factory("gpt_oss")
    backend = probe._backend_from_factory(factory)
    llm = backend.llm
    agent = factory()
    suite = ToolSuite(fixtures_dir)
    tools = to_agent_tool_specs(tuple(suite.specs.values()))
    return_id = llm.tokenize(b"<|return|>", add_bos=False, special=True)[0]

    baseline = CANDIDATES["demo_full"](args.recipient)
    prefix, marker, suffix = baseline.partition(trigger._INSERTION)
    if not marker:
        raise RuntimeError("挿入位置がbaselineにありません")
    baseline_tokens = len(llm.tokenize(baseline.encode(), add_bos=False, special=True))
    history_builder = lambda message: trigger._history(message, args.recipient)  # noqa: E731

    rows: list[dict[str, Any]] = []
    shared_ids: list[int] | None = None
    for left in _SEEDS:
        for right in _SEEDS:
            piece = left + right
            message = prefix + piece + marker + suffix
            prompt_ids = probe._render_prompt(agent, llm, history_builder(message), tools)
            message_tokens = len(llm.tokenize(message.encode(), add_bos=False, special=True))
            rows.append(
                {
                    "left": left,
                    "right": right,
                    "piece": piece,
                    "message_tokens": message_tokens,
                    "added_tokens": message_tokens - baseline_tokens,
                    "prompt_ids": prompt_ids,
                }
            )
            shared_ids = (
                list(prompt_ids) if shared_ids is None else shared_ids[: _common_prefix(shared_ids, prompt_ids)]
            )
    if not shared_ids:
        raise RuntimeError("共通prefixが空です")

    # 完全再評価とprefix KV再利用の結果が一致することを最初の候補で検証する。
    first_prompt = rows[0]["prompt_ids"]
    llm.reset()
    llm.eval(first_prompt)
    full_stats = probe._token_stats(probe._current_logits(llm), return_id)
    llm.reset()
    llm.eval(shared_ids)
    llm.eval(first_prompt[len(shared_ids) :])
    cached_stats = probe._token_stats(probe._current_logits(llm), return_id)
    use_shared_kv = full_stats == cached_stats
    if not use_shared_kv:
        print(f"[pair] KV再利用は不一致のため完全再評価へ切替: full={full_stats} cached={cached_stats}")

    kept: list[tuple[float, int, dict[str, Any]]] = []
    if use_shared_kv:
        llm.reset()
        llm.eval(shared_ids)
    for index, row in enumerate(rows, start=1):
        prompt_ids = row.pop("prompt_ids")
        if use_shared_kv:
            llm.n_tokens = len(shared_ids)
            llm.eval(prompt_ids[len(shared_ids) :])
        else:
            llm.reset()
            llm.eval(prompt_ids)
        stats = probe._token_stats(probe._current_logits(llm), return_id)
        row["return"] = stats
        score = float(stats["logp"]) - max(int(row["added_tokens"]), 0) * 0.05
        item = (score, index, row)
        if len(kept) < args.keep:
            heapq.heappush(kept, item)
        elif item > kept[0]:
            heapq.heapreplace(kept, item)

    ranked = [item[2] for item in sorted(kept, reverse=True)]
    payload = {
        "model": "gpt_oss",
        "recipient": args.recipient,
        "baseline_tokens": baseline_tokens,
        "seed_count": len(_SEEDS),
        "tested": len(rows),
        "shared_prompt_tokens": len(shared_ids),
        "kv_validation": {"full": full_stats, "cached": cached_stats, "used": use_shared_kv},
        "results": ranked,
    }
    output = Path(args.out)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    for row in ranked[:20]:
        print(
            f"[top] piece={row['piece']!r:28} added={row['added_tokens']} "
            f"rank={row['return']['rank']:6} logp={row['return']['logp']:.4f}"
        )
    encoded = base64.b64encode(output.read_bytes()).decode("ascii")
    print(f"RESULT_BASE64_BEGIN {output.name} {len(encoded)}")
    print(encoded)
    print(f"RESULT_BASE64_END {output.name}")
    print(f"[pair] tested={len(rows)} shared={len(shared_ids)} saved={output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
