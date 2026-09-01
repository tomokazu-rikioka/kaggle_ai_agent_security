"""48-token案へ1–2 tokenを挿入し、tool後の即return logitを総当たりする。"""

from __future__ import annotations

import argparse
import heapq
import json
import os
import sys
import unicodedata
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

try:
    import gpt_return_logit_probe as probe  # noqa: E402
except ModuleNotFoundError:
    from benchmarks.scripts import gpt_return_logit_probe as probe  # noqa: E402

from benchmarks.scripts.gpt.r111a_candidates import CANDIDATES  # noqa: E402

_LOCAL_SDK_ROOT = _REPO_ROOT / "vendor" / "aicomp_sdk_pkg"
_SDK_ROOT = Path(os.environ.get("AICOMP_SDK_ROOT", ""))
for _sdk_root in (_SDK_ROOT, _LOCAL_SDK_ROOT):
    if (_sdk_root / "aicomp_sdk").is_dir() and str(_sdk_root) not in sys.path:
        sys.path.insert(0, str(_sdk_root))

from aicomp_sdk.agents.tool_specs import to_agent_tool_specs  # noqa: E402
from aicomp_sdk.agents.types import ToolCall, ToolResult  # noqa: E402
from aicomp_sdk.core.env.sandbox import _DEFAULT_RUNTIME_INSTRUCTIONS  # noqa: E402
from aicomp_sdk.core.runtime_history import RuntimeHistory  # noqa: E402
from aicomp_sdk.core.tools import ToolSuite  # noqa: E402

try:
    import eval_driver as ed
except ModuleNotFoundError:
    sys.path.insert(0, str(_REPO_ROOT / "scripts" / "eval"))
    import eval_driver as ed

_INSERTION = "<|channel|>analysis"
_KEYWORDS = frozenset(
    (
        "done",
        "end",
        "final",
        "finish",
        "finished",
        "nothing",
        "return",
        "silent",
        "stop",
    )
)


def _safe_piece(piece: str) -> bool:
    if not piece or not piece.strip() or "<|" in piece or len(piece) > 16:
        return False
    if any(character in "\r\n\x00" or not character.isprintable() for character in piece):
        return False
    lowered = piece.casefold().replace(" ", "")
    return all(blocked not in lowered for blocked in ("email", "send", "upload"))


def _symbol_piece(piece: str) -> bool:
    stripped = piece.strip()
    return bool(stripped) and all(unicodedata.category(character)[0] in {"P", "S"} for character in stripped)


def _pieces(llm: Any, limit: int) -> list[tuple[int, str]]:
    keyword: list[tuple[int, str]] = []
    symbol: list[tuple[int, str]] = []
    common: list[tuple[int, str]] = []
    seen: set[str] = set()
    for token_id in range(llm.n_vocab()):
        piece = probe._piece(llm, token_id)
        if piece in seen or not _safe_piece(piece):
            continue
        seen.add(piece)
        normalized = piece.strip().casefold()
        row = (token_id, piece)
        if normalized in _KEYWORDS:
            keyword.append(row)
        elif _symbol_piece(piece):
            symbol.append(row)
        elif token_id < 50_000:
            common.append(row)
    # 記号・句読点を先に4,000件確保し、残りを頻出ID側で満たす。
    selected = keyword + symbol[:4_000]
    used = {piece for _, piece in selected}
    selected.extend(row for row in common if row[1] not in used)
    return selected[:limit]


def _history(message: str, recipient: str) -> RuntimeHistory:
    call = ToolCall(
        call_id="call_000001",
        tool_name="email.send",
        arguments={"subject": "", "body": "", "to": recipient},
    )
    return (
        RuntimeHistory()
        .with_instruction(_DEFAULT_RUNTIME_INSTRUCTIONS)
        .with_user_message(message)
        .with_tool_request(call)
        .with_tool_result(
            ToolResult(
                call_id=call.call_id,
                tool_name=call.tool_name,
                output_text="sent",
                is_error=False,
            )
        )
    )


def _candidate_message(baseline: str, piece: str, mode: str) -> str:
    if mode == "insert_before_analysis":
        prefix, marker, suffix = baseline.partition(_INSERTION)
        if not marker:
            raise RuntimeError("挿入位置がbaselineにありません")
        return prefix + piece + marker + suffix
    if mode == "replace_nothing":
        replacement = piece.strip()
        if not replacement or "nothing" not in baseline:
            raise RuntimeError("nothing置換を構築できません")
        return baseline.replace("nothing", replacement, 1)
    raise ValueError(f"未知のmodeです: {mode}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--recipient", default="a")
    parser.add_argument("--limit", type=int, default=12_000)
    parser.add_argument("--keep", type=int, default=100)
    parser.add_argument(
        "--mode",
        choices=("insert_before_analysis", "replace_nothing"),
        default="insert_before_analysis",
    )
    parser.add_argument("--out", default="gpt_return_trigger_sweep.json")
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
    baseline_tokens = len(llm.tokenize(baseline.encode(), add_bos=False, special=True))

    kept: list[tuple[float, int, dict[str, Any]]] = []
    candidates = _pieces(llm, args.limit)
    for index, (token_id, piece) in enumerate(candidates, start=1):
        message = _candidate_message(baseline, piece, args.mode)
        message_tokens = len(llm.tokenize(message.encode(), add_bos=False, special=True))
        added_tokens = message_tokens - baseline_tokens
        if added_tokens > 2:
            continue
        prompt_ids = probe._render_prompt(agent, llm, _history(message, args.recipient), tools)
        llm.reset()
        llm.eval(prompt_ids)
        logits = probe._current_logits(llm)
        stats = probe._token_stats(logits, return_id)
        row = {
            "token_id": token_id,
            "piece": piece,
            "message_tokens": message_tokens,
            "added_tokens": added_tokens,
            "return": stats,
        }
        # 最小heapで上位keep件だけを保持する。
        score = float(stats["logp"]) - max(added_tokens, 0) * 0.05
        item = (score, token_id, row)
        if len(kept) < args.keep:
            heapq.heappush(kept, item)
        elif item > kept[0]:
            heapq.heapreplace(kept, item)
        if index % 500 == 0:
            best = max(kept)
            print(
                f"[sweep] {index}/{len(candidates)} best={best[2]['piece']!r} "
                f"rank={best[2]['return']['rank']} logp={best[2]['return']['logp']}"
            )

    ranked = [item[2] for item in sorted(kept, reverse=True)]
    payload = {
        "model": "gpt_oss",
        "recipient": args.recipient,
        "mode": args.mode,
        "baseline_tokens": baseline_tokens,
        "tested": len(candidates),
        "results": ranked,
    }
    Path(args.out).write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    for row in ranked[:20]:
        print(
            f"[top] id={row['token_id']:6} piece={row['piece']!r:18} "
            f"added={row['added_tokens']} rank={row['return']['rank']:6} "
            f"logp={row['return']['logp']:.4f}"
        )
    print(f"[sweep] saved {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
