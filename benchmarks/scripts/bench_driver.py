"""複数プロンプト変種を 1 モデルロードでまとめて計測するベンチ用ドライバ。

`scripts/eval/eval_driver.py` を土台に、モデル（GGUF）を **1 回だけロード**して、
`--variants-file` が定義する各変種について同一 recipient 集合で N 候補を組み、
`public`/`private` へリプレイして次を測る:

  - **emit_rate**: 標的が `email.send` を emit した候補の割合（tool_event ベース。predicate 前）
      - emit_any = email.send を出した（guardrail が block しても数える）
      - emit_ok  = email.send が ok=True で実行された（＝採点対象になり得る）
  - **fire_rate**: CONFUSED_DEPUTY が成立して findings になった候補の割合（＝実際に得点する率）
  - **replay_mean_s**: 1 候補あたりのリプレイ時間（候補速度）

emit と fire の差で「モデルが出していないのか / guardrail が block したのか /
述語が抑制されたのか」を切り分ける。CONFUSED_DEPUTY は last_user に "send"/"email"/"upload" が
含まれると user_allows_share=True で **抑制される**（SDK predicates.py 確定）ので、
emit_ok>0 でも fire=0 なら文面に禁止語が入っている合図。

eval_driver は候補ごとに Llama を作り直さず backend を使い回す（`_build_gguf_agent_factory`）ので、
変種をまたいでもモデルロードは 1 回で済む＝1 カーネルで 1 トラック分の A/B が丸ごと取れる。

使い方（Kaggle 評価カーネル内で）:
    python bench_driver.py --model gpt_oss --variants-file variants.py \
        --candidates 30 --guardrails public,private --out bench_results.json
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

# eval_driver は import 時に SDK / research guardrails を sys.path 解決する。
# 評価カーネルでは eval_driver.py と guardrails/ が /kaggle/working に展開済み。
import eval_driver as ed
from eval_driver import (
    AttackCandidate,
    build_agent_factory,
    eval_predicates,
    get_guardrail_factory,
    ops,
    predicate_breakdown,
)

MessageBuilder = Callable[[str], str]


def _alpha_label(index: int) -> str:
    """0->a, 1->b, ... 25->z, 26->aa ...（baseline と同じ採番）。distinct recipient=distinct cell。"""
    if index < 0:
        raise ValueError("index must be non-negative")
    chars: list[str] = []
    value = index
    while True:
        value, remainder = divmod(value, 26)
        chars.append(chr(ord("a") + remainder))
        if value == 0:
            return "".join(reversed(chars))
        value -= 1


def _build_recipients(n: int, blocklist: frozenset[str]) -> list[str]:
    recipients: list[str] = []
    cursor = 0
    while len(recipients) < n:
        label = _alpha_label(cursor)
        cursor += 1
        if label not in blocklist:
            recipients.append(label)
    return recipients


def _load_variants(path_str: str) -> tuple[dict[str, MessageBuilder], frozenset[str]]:
    path = Path(path_str).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"--variants-file が見つかりません: {path}")
    spec = importlib.util.spec_from_file_location("_bench_variants", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    variants = getattr(mod, "VARIANTS", None)
    if not isinstance(variants, dict) or not variants:
        raise TypeError(f"{path} は VARIANTS: dict[str, Callable] を定義する必要があります")
    blocklist = frozenset(getattr(mod, "RECIPIENT_BLOCKLIST", frozenset()))
    return variants, blocklist


def _replay_variant(
    candidates: list[AttackCandidate],
    guardrail_name: str,
    agent_factory: Any,
    fixtures_dir: Path,
    seed: int,
    max_tool_hops: int,
    env_selection: str,
    recipients: list[str] | None = None,
) -> dict[str, Any]:
    """1 変種 × 1 guardrail を全候補リプレイして emit/fire/速度を集計する。

    recipients を渡すと、発火しなかった（finding が出なかった）候補の recipient ラベルも返す
    （高 N で発火が漏れる recipient を特定＝実提出の blocklist 補強に使う）。
    """
    guardrail_factory = get_guardrail_factory(guardrail_name)
    findings: list[dict[str, Any]] = []
    replay_seconds: list[float] = []
    emit_any = 0
    emit_ok = 0
    nonfire_recipients: list[str] = []
    for idx, candidate in enumerate(candidates):
        t0 = time.monotonic()
        trace = ops._replay_candidate_trace(
            candidate=candidate,
            index=idx,
            seed=seed,
            fixtures_dir=fixtures_dir,
            agent_factory=agent_factory,
            guardrail=guardrail_factory(),
            env_selection=env_selection,
            max_tool_hops=max_tool_hops,
            hook_registry_factory=ops.HookRegistry,
            output_controller=None,
        )
        replay_seconds.append(time.monotonic() - t0)
        events = trace.get("tool_events", []) or []
        sends = [e for e in events if e.get("name") == "email.send"]
        if sends:
            emit_any += 1
            if any(e.get("ok") is True for e in sends):
                emit_ok += 1
        predicates = eval_predicates(trace)
        if not predicates and recipients is not None and idx < len(recipients):
            nonfire_recipients.append(recipients[idx])
        if predicates:
            findings.append(
                {
                    "seed": trace["seed"],
                    "user_messages": list(trace.get("user_messages", [])),
                    "trace": trace,
                    "predicates": predicates,
                    "cell_signature": ops.cell_signature(
                        trace.get("tool_events", []),
                        egress_data=trace.get("egress", []),
                        user_messages=trace.get("user_messages", []),
                    ),
                    "score_cell_signature": ops.cell_signature(trace.get("tool_events", [])),
                }
            )
    summary = ops.summarize_attack_findings(findings)
    n = len(candidates)
    total_s = sum(replay_seconds)
    return {
        "emit_any_rate": round(emit_any / n, 4) if n else 0.0,
        "emit_ok_rate": round(emit_ok / n, 4) if n else 0.0,
        "fire_rate": round(summary["findings_count"] / n, 4) if n else 0.0,
        "findings_count": summary["findings_count"],
        "emit_any": emit_any,
        "emit_ok": emit_ok,
        "n_candidates": n,
        "replay_mean_s": round(total_s / n, 3) if n else 0.0,
        "replay_total_s": round(total_s, 3),
        "score_raw": summary["score_raw"],
        "unique_cells": summary["unique_cells"],
        "predicates": predicate_breakdown(findings),
        "nonfire_recipients": nonfire_recipients[:80],
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="複数プロンプト変種の emit/fire/候補速度をまとめて計測")
    ap.add_argument("--model", default="gpt_oss", choices=["gpt_oss", "gemma_4", "gemma"])
    ap.add_argument("--variants-file", required=True, help="VARIANTS を定義した .py")
    ap.add_argument("--candidates", type=int, default=30, help="変種ごとの候補数 N（既定 30）")
    ap.add_argument("--guardrails", default="public,private", help="カンマ区切り（public,private,allow,denyN,...）")
    ap.add_argument("--budget-s", type=float, default=8000.0)
    ap.add_argument("--seed", type=int, default=ed.DEFAULT_SEED)
    ap.add_argument("--max-tool-hops", type=int, default=8)
    ap.add_argument("--env", default="gym", choices=["gym", "sandbox"])
    ap.add_argument("--out", default="bench_results.json")
    args = ap.parse_args(argv)

    guardrails = [g.strip() for g in args.guardrails.split(",") if g.strip()]
    variants, blocklist = _load_variants(args.variants_file)
    recipients = _build_recipients(args.candidates, blocklist)

    fixtures_dir = ops.resolve_fixtures_dir(None)
    print(f"[bench] fixtures={fixtures_dir}")
    print(f"[bench] model={args.model} を 1 回ロードして {len(variants)} 変種 × {len(guardrails)} guardrail を計測")
    t_load = time.time()
    agent_factory = build_agent_factory(args.model)  # ここで GGUF を 1 回だけロード
    print(f"[bench] モデルロード {time.time() - t_load:.1f}s 完了。recipients={recipients[:8]}… (N={len(recipients)})")

    results: dict[str, Any] = {}
    for vname, builder in variants.items():
        sample = builder(recipients[0])
        candidates = [AttackCandidate.from_messages((builder(r),)) for r in recipients]
        per_guardrail: dict[str, Any] = {}
        for gname in guardrails:
            t0 = time.time()
            m = _replay_variant(
                candidates, gname, agent_factory, fixtures_dir, args.seed,
                args.max_tool_hops, args.env, recipients=recipients,
            )
            per_guardrail[gname] = m
            nf = m.get("nonfire_recipients") or []
            nf_str = f" nonfire={nf[:20]}" if nf else ""
            print(
                f"[bench] {vname:22} [{gname:7}] fire={m['fire_rate']:.3f} "
                f"emit_ok={m['emit_ok_rate']:.3f} emit_any={m['emit_any_rate']:.3f} "
                f"mean_s={m['replay_mean_s']:.2f} raw={m['score_raw']:.1f} cells={m['unique_cells']} "
                f"preds={m['predicates']}{nf_str} （{time.time() - t0:.1f}s）"
            )
        results[vname] = {"sample_message": sample, "sample_len": len(sample), "guardrails": per_guardrail}

    payload = {
        "model": ed._MODEL_ALIASES.get(args.model, args.model),
        "candidates_per_variant": args.candidates,
        "guardrails": guardrails,
        "seed": args.seed,
        "results": results,
    }
    Path(args.out).write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    print(f"\n[bench] 保存: {args.out}")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
