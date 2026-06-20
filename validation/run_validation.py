"""ローカル検証パイプライン本体。

公式ゲートウェイ（jed_attack_gateway.py）と同じ手順を再現する:
  1) attack.run(env) を **1 回**実行して候補（ユーザーメッセージ連鎖）を生成（public 環境で探索）
  2) 同じ候補リストを各ガードレールへ **リプレイ** → eval_predicates → score_attack
生成とリプレイを分離するのは、複数ガードレール比較で生成（モデル実行）を繰り返さないため。

使用例:
  # ロジック層（GPU 不要・数秒）: ベースライン攻撃を 3 ガードレールで採点
  python -m validation.run_validation --agent deterministic \
      --guardrails public,strict,provenance --budget-s 30

  # 実モデル smoke（Mac Metal）: gpt-oss を public で 10 候補
  python -m validation.run_validation --agent gpt_oss --guardrails public \
      --candidates 10 --budget-s 600 --env gym

  # 生成済み候補を読み込んで採点だけやり直す
  python -m validation.run_validation --candidates-in runs/cand.json --agent gpt_oss
"""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import json
import sys
import time
from pathlib import Path
from typing import Any

import validation.paths as paths  # noqa: F401  (import 副作用で sys.path を整える)
from validation.agents_local import NO_GPU_AGENTS, build_local_agent_factory
from validation.guardrails_local import (
    DEFAULT_GUARDRAILS,
    GUARDRAILS,
    get_guardrail_factory,
)
from validation.report import format_report, predicate_breakdown

from aicomp_sdk.attacks.contracts import AttackAlgorithmBase, AttackCandidate, AttackRunConfig
from aicomp_sdk.core.predicates import eval_predicates
from aicomp_sdk.evaluation import ops

DEFAULT_SEED = 123  # 公式 ATTACK_SEED


# ----------------------------------------------------------------------------- attack 読込
def load_attack_class(spec: str | None) -> type[AttackAlgorithmBase]:
    """--attack の指定から AttackAlgorithm クラスを得る。

    spec:
      None / "baseline" / "goexplore" -> 同梱の Go-Explore ベースライン
      末尾 .py のパス                 -> そのファイルから AttackAlgorithmBase 派生を探す
      "pkg.mod:Class" / "pkg.mod"      -> モジュール import
    """
    if spec in (None, "baseline", "goexplore"):
        mod = importlib.import_module("aicomp_sdk.attacks.baselines.attacker_goexplore")
        return _pick_attack_class(mod)

    if spec.endswith(".py"):
        path = Path(spec).resolve()
        if not path.is_file():
            raise FileNotFoundError(f"--attack のファイルが見つかりません: {path}")
        module_name = f"_user_attack_{path.stem}"
        loader = importlib.util.spec_from_file_location(module_name, path)
        assert loader and loader.loader
        mod = importlib.util.module_from_spec(loader)
        sys.modules[module_name] = mod
        loader.loader.exec_module(mod)
        return _pick_attack_class(mod)

    module_path, _, cls_name = spec.partition(":")
    mod = importlib.import_module(module_path)
    if cls_name:
        return getattr(mod, cls_name)
    return _pick_attack_class(mod)


def _pick_attack_class(mod: Any) -> type[AttackAlgorithmBase]:
    # "AttackAlgorithm" を優先、無ければ AttackAlgorithmBase の具象派生を探す
    cand = getattr(mod, "AttackAlgorithm", None)
    if isinstance(cand, type) and issubclass(cand, AttackAlgorithmBase):
        return cand
    for obj in vars(mod).values():
        if (
            isinstance(obj, type)
            and issubclass(obj, AttackAlgorithmBase)
            and obj is not AttackAlgorithmBase
        ):
            return obj
    raise TypeError(f"{mod.__name__} に AttackAlgorithmBase 派生クラスが見つかりません")


# ----------------------------------------------------------------------------- 生成
def generate_candidates(
    *,
    attack_cls: type[AttackAlgorithmBase],
    agent_factory,
    fixtures_dir: Path,
    seed: int,
    budget_s: float,
    max_tool_hops: int,
    env_selection: str,
    max_candidates: int | None,
    gen_guardrail: str = "public",
) -> list[AttackCandidate]:
    """attack.run() を 1 回実行して候補を得る（gateway の attack フェーズ相当）。

    既定の探索ガードレールは public（gateway と同じ）。ロジック層で探索器に
    何か見つけさせたい場合は gen_guardrail="allow" を使う（ただし allow で見つけた
    攻撃は public でブロックされ得る — それ自体が「転移しない」というシグナル）。
    """
    run_config = AttackRunConfig(time_budget_s=budget_s, max_tool_hops=max_tool_hops)
    run_env = ops._OpaqueAttackEnv(
        ops.build_attack_env(
            seed=seed,
            fixtures_dir=fixtures_dir,
            agent_factory=agent_factory,
            guardrail=get_guardrail_factory(gen_guardrail)(),
            env_selection=env_selection,
            max_tool_hops=run_config.max_tool_hops,
            hook_registry=ops._build_hook_registry(ops.HookRegistry),
        )
    )
    run_env.reset()
    attacker = attack_cls(config={})
    candidates = attacker.run(run_env, run_config)
    if not isinstance(candidates, list):
        raise TypeError("AttackAlgorithm.run は list[AttackCandidate] を返す必要があります")
    candidates = candidates[: ops.MAX_REPLAY_FINDINGS]
    if max_candidates is not None:
        candidates = candidates[:max_candidates]
    return candidates


# ----------------------------------------------------------------------------- リプレイ+採点
def replay_and_score(
    *,
    candidates: list[AttackCandidate],
    guardrail_name: str,
    agent_factory,
    fixtures_dir: Path,
    seed: int,
    max_tool_hops: int,
    env_selection: str,
    progress_every: int = 25,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """候補を 1 つのガードレールへリプレイし、findings と summary を返す（gateway の replay 相当）。"""
    guardrail_factory = get_guardrail_factory(guardrail_name)
    findings: list[dict[str, Any]] = []
    n = len(candidates)
    for idx, candidate in enumerate(candidates):
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
        predicates = eval_predicates(trace)
        if not predicates:
            continue
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
        if progress_every and (idx + 1) % progress_every == 0:
            print(f"  [{guardrail_name}] {idx + 1}/{n} 候補リプレイ済 / findings={len(findings)}")
    summary = ops.summarize_attack_findings(findings)
    return summary, findings


# ----------------------------------------------------------------------------- 候補 I/O
def candidates_to_json(candidates: list[AttackCandidate]) -> list[list[str]]:
    return [list(c.user_messages) for c in candidates]


def candidates_from_json(data: list[list[str]]) -> list[AttackCandidate]:
    return [AttackCandidate.from_messages(msgs) for msgs in data]


# ----------------------------------------------------------------------------- main
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="ローカル検証パイプライン（AI Agent Security）")
    ap.add_argument("--attack", default="baseline", help="attack .py パス / module[:Class] / 'baseline'")
    ap.add_argument("--agent", default="deterministic", choices=["deterministic", "gpt_oss", "gemma_4", "gemma"])
    ap.add_argument("--guardrails", default=",".join(DEFAULT_GUARDRAILS), help=f"カンマ区切り: {', '.join(GUARDRAILS)}")
    ap.add_argument("--candidates", type=int, default=None, help="生成候補数の上限（smoke 用）")
    ap.add_argument("--budget-s", type=float, default=60.0, help="生成フェーズの時間予算（秒）")
    ap.add_argument("--seed", type=int, default=DEFAULT_SEED)
    ap.add_argument("--gen-guardrail", default="public", choices=list(GUARDRAILS), help="探索フェーズのガードレール（既定 public=gateway 同等）")
    ap.add_argument("--env", default="gym", choices=["gym", "sandbox"], help="採点は gym（公式と同じ）")
    ap.add_argument("--max-tool-hops", type=int, default=8)
    ap.add_argument("--candidates-in", default=None, help="生成をスキップして候補 JSON を読み込む")
    ap.add_argument("--candidates-out", default=None, help="生成した候補 JSON の保存先")
    ap.add_argument("--report-out", default=None, help="レポートのテキスト保存先")
    ap.add_argument("--summary-out", default=None, help="ガードレール別スコアの JSON 保存先")
    args = ap.parse_args(argv)

    guardrails = [g.strip() for g in args.guardrails.split(",") if g.strip()]
    for g in guardrails:
        if g not in GUARDRAILS:
            ap.error(f"未知のガードレール '{g}'。選択肢: {', '.join(GUARDRAILS)}")

    fixtures_dir = paths.resolve_fixtures_dir(None)
    print(f"[run] fixtures={fixtures_dir}")
    if args.agent not in NO_GPU_AGENTS:
        print(f"[run] agent={args.agent} は実モデル（GPU/Metal 必須・GGUF ロードに時間がかかります）")

    agent_factory = build_local_agent_factory(args.agent)

    # --- 候補の用意（読込 or 生成） ---
    if args.candidates_in:
        data = json.loads(Path(args.candidates_in).read_text())
        candidates = candidates_from_json(data)
        if args.candidates is not None:
            candidates = candidates[: args.candidates]
        print(f"[run] 候補を読込: {len(candidates)} 件 <- {args.candidates_in}")
    else:
        attack_cls = load_attack_class(args.attack)
        print(f"[run] attack={attack_cls.__module__}.{attack_cls.__name__} で生成中…")
        t0 = time.time()
        candidates = generate_candidates(
            attack_cls=attack_cls,
            agent_factory=agent_factory,
            fixtures_dir=fixtures_dir,
            seed=args.seed,
            budget_s=args.budget_s,
            max_tool_hops=args.max_tool_hops,
            env_selection=args.env,
            max_candidates=args.candidates,
            gen_guardrail=args.gen_guardrail,
        )
        print(f"[run] {len(candidates)} 候補を生成（{time.time() - t0:.1f}s, gen_guardrail={args.gen_guardrail}）")

    if args.candidates_out:
        Path(args.candidates_out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.candidates_out).write_text(json.dumps(candidates_to_json(candidates), ensure_ascii=False, indent=2))
        print(f"[run] 候補を保存: {args.candidates_out}")

    if not candidates:
        print("[run] 候補が 0 件です。budget-s を増やすか attack を確認してください。")
        return 1

    # --- ガードレール別にリプレイ+採点 ---
    rows: list[dict[str, Any]] = []
    for gname in guardrails:
        print(f"[run] '{gname}' ガードレールへリプレイ（{len(candidates)} 候補）…")
        t0 = time.time()
        summary, findings = replay_and_score(
            candidates=candidates,
            guardrail_name=gname,
            agent_factory=agent_factory,
            fixtures_dir=fixtures_dir,
            seed=args.seed,
            max_tool_hops=args.max_tool_hops,
            env_selection=args.env,
        )
        print(f"[run]   -> score={summary['score']:.3f} raw={summary['score_raw']:.1f} "
              f"findings={summary['findings_count']} cells={summary['unique_cells']} "
              f"（{time.time() - t0:.1f}s）")
        rows.append({"guardrail": gname, "summary": summary, "breakdown": predicate_breakdown(findings)})

    report = format_report(
        agent=args.agent,
        n_candidates=len(candidates),
        seed=args.seed,
        env_selection=args.env,
        rows=rows,
    )
    print("\n" + report)
    if args.report_out:
        Path(args.report_out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.report_out).write_text(report)
        print(f"[run] レポート保存: {args.report_out}")

    if args.summary_out:
        payload = {
            "agent": args.agent,
            "n_candidates": len(candidates),
            "seed": args.seed,
            "env": args.env,
            "guardrails": {
                r["guardrail"]: {
                    "score": r["summary"]["score"],
                    "score_raw": r["summary"]["score_raw"],
                    "findings_count": r["summary"]["findings_count"],
                    "unique_cells": r["summary"]["unique_cells"],
                }
                for r in rows
            },
        }
        Path(args.summary_out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.summary_out).write_text(json.dumps(payload, ensure_ascii=False, indent=2))
        print(f"[run] サマリ保存: {args.summary_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
