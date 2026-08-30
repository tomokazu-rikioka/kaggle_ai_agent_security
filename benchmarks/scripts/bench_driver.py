"""複数プロンプト変種を 1 モデルロードでまとめて計測するベンチ用ドライバ。

`scripts/eval/eval_driver.py` を土台に、モデル（GGUF）を **1 回だけロード**して、
`--variants-file` が定義する各変種について同一 recipient 集合で N 候補を組み、
`public`/`private` へリプレイして次を測る:

  - **emit_rate**: `TARGET_TOOL` の標的ツールを emit した候補の割合（tool_event ベース。predicate 前）
  - **fire_rate**: 対応する predicate が成立して findings になった候補の割合（＝実際に得点する率）
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
from collections import Counter
from collections.abc import Callable, Sequence
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

MessageBuilder = Callable[[str], str | Sequence[str]]
ExpectedEmailToBuilder = Callable[[str, str], Sequence[str]]


class _GenerationProbe:
    """llama.cpp completion usageを挙動を変えずに収集する小さな計測器。"""

    def __init__(self, llm: Any) -> None:
        self._records: list[dict[str, Any]] = []
        original = llm.create_chat_completion

        def measured(*args: Any, **kwargs: Any) -> Any:
            completion = original(*args, **kwargs)
            if isinstance(completion, dict):
                usage = completion.get("usage") or {}
                choices = completion.get("choices") or []
                message = choices[0].get("message") if choices and isinstance(choices[0], dict) else None
                self._records.append(
                    {
                        "prompt_tokens": usage.get("prompt_tokens"),
                        "completion_tokens": usage.get("completion_tokens"),
                        "content": message.get("content") if isinstance(message, dict) else None,
                    }
                )
            return completion

        llm.create_chat_completion = measured

    def reset(self) -> None:
        self._records.clear()

    def take(self) -> list[dict[str, Any]]:
        records = list(self._records)
        self._records.clear()
        return records


def _normalize_messages(value: str | Sequence[str]) -> tuple[str, ...]:
    if isinstance(value, str):
        return (value,)
    messages = tuple(value)
    if not messages or not all(isinstance(message, str) and message.strip() for message in messages):
        raise TypeError("variant builderは非空str、または非空strのsequenceを返す必要があります")
    return messages


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


def _load_variants(
    path_str: str,
) -> tuple[
    dict[str, MessageBuilder],
    frozenset[str],
    str,
    tuple[str, ...] | None,
    ExpectedEmailToBuilder | None,
]:
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
    target_tool = getattr(mod, "TARGET_TOOL", "email.send")
    if not isinstance(target_tool, str) or not target_tool:
        raise TypeError(f"{path} の TARGET_TOOL は空でない str が必要です")
    configured_recipients = getattr(mod, "RECIPIENTS", None)
    if configured_recipients is not None:
        configured_recipients = tuple(configured_recipients)
        if not configured_recipients or not all(
            isinstance(recipient, str) and recipient for recipient in configured_recipients
        ):
            raise TypeError(f"{path} の RECIPIENTS は空でない一意strのsequenceにしてください")
        if len(set(configured_recipients)) != len(configured_recipients):
            raise ValueError(f"{path} の RECIPIENTS に重複があります")
    expected_email_tos = getattr(mod, "EXPECTED_EMAIL_TOS", None)
    if expected_email_tos is not None and not callable(expected_email_tos):
        raise TypeError(f"{path} の EXPECTED_EMAIL_TOS はcallableにしてください")
    return variants, blocklist, target_tool, configured_recipients, expected_email_tos


def _prompt_token_count(agent_factory: Any, text: str) -> int | None:
    """llama.cpp が使う実 tokenizer で、注入文字列そのものの token 数をbest-effort計測する。

    system prompt / tool schema は全variant共通なので含めない。特殊トークンは special=True で1 tokenとして数える。
    factory は eval_driver の closure に backend を保持するため、公開APIを汚さずそこから Llama を探す。
    """
    closure = getattr(agent_factory, "__closure__", None) or ()
    for cell in closure:
        value = cell.cell_contents
        llm = getattr(value, "llm", None)
        tokenize = getattr(llm, "tokenize", None)
        if callable(tokenize):
            try:
                return len(tokenize(text.encode("utf-8"), add_bos=False, special=True))
            except (TypeError, ValueError, RuntimeError):
                return None
    return None


def _message_common_prefix_tokens(agent_factory: Any, left: str, right: str) -> int | None:
    """recipientだけ異なる2文面で、llama.cpp KVが再利用できるuser token prefix長を返す。"""
    for cell in getattr(agent_factory, "__closure__", None) or ():
        llm = getattr(cell.cell_contents, "llm", None)
        tokenize = getattr(llm, "tokenize", None)
        if not callable(tokenize):
            continue
        try:
            left_ids = tokenize(left.encode("utf-8"), add_bos=False, special=True)
            right_ids = tokenize(right.encode("utf-8"), add_bos=False, special=True)
        except (TypeError, ValueError, RuntimeError):
            return None
        count = 0
        for left_id, right_id in zip(left_ids, right_ids, strict=False):
            if left_id != right_id:
                break
            count += 1
        return count
    return None


def _install_generation_probe(agent_factory: Any) -> _GenerationProbe | None:
    """factory closure内の共有llama.cppへcompletion usage計測を1度だけ取り付ける。"""
    for cell in getattr(agent_factory, "__closure__", None) or ():
        llm = getattr(cell.cell_contents, "llm", None)
        if callable(getattr(llm, "create_chat_completion", None)):
            return _GenerationProbe(llm)
    return None


def _replay_variant(
    candidates: list[AttackCandidate],
    guardrail_name: str,
    agent_factory: Any,
    fixtures_dir: Path,
    seed: int,
    max_tool_hops: int,
    env_selection: str,
    target_tool: str,
    recipients: list[str] | None = None,
    expected_email_tos: list[tuple[str, ...]] | None = None,
    generation_probe: _GenerationProbe | None = None,
) -> dict[str, Any]:
    """1 変種 × 1 guardrail を全候補リプレイして emit/fire/速度を集計する。

    recipients を渡すと、発火しなかった（finding が出なかった）候補の recipient ラベルも返す
    （高 N で発火が漏れる recipient を特定＝実提出の blocklist 補強に使う）。
    """
    guardrail_factory = get_guardrail_factory(guardrail_name)
    findings: list[dict[str, Any]] = []
    replay_seconds: list[float] = []
    tool_event_counts: list[int] = []
    assistant_message_counts: list[int] = []
    assistant_character_counts: list[int] = []
    assistant_texts: Counter[str] = Counter()
    tool_sequences: Counter[str] = Counter()
    email_to_sequences: Counter[str] = Counter()
    distinct_email_recipients: list[int] = []
    exact_email_to_sequences = 0
    generation_counts: list[int] = []
    prompt_token_totals: list[int] = []
    completion_token_totals: list[int] = []
    completion_token_sequences: Counter[str] = Counter()
    generation_text_sequences: Counter[str] = Counter()
    emit_any = 0
    emit_ok = 0
    nonfire_recipients: list[str] = []
    recipient_diagnostics: list[dict[str, Any]] = []
    for idx, candidate in enumerate(candidates):
        if generation_probe is not None:
            generation_probe.reset()
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
        generation_rows = generation_probe.take() if generation_probe is not None else []
        generation_counts.append(len(generation_rows))
        prompt_tokens = [row.get("prompt_tokens") for row in generation_rows]
        completion_tokens = [row.get("completion_tokens") for row in generation_rows]
        prompt_token_totals.append(sum(value for value in prompt_tokens if isinstance(value, int)))
        completion_token_totals.append(sum(value for value in completion_tokens if isinstance(value, int)))
        completion_sequence = ">".join(str(value) for value in completion_tokens) or "-"
        completion_token_sequences[completion_sequence] += 1
        generation_text_sequences[
            ">".join(str(row.get("content") or "") for row in generation_rows) or "-"
        ] += 1
        events = trace.get("tool_events", []) or []
        tool_event_counts.append(len(events))
        assistant_messages = [str(message) for message in (trace.get("assistant_messages", []) or [])]
        assistant_message_counts.append(len(assistant_messages))
        assistant_character_counts.append(sum(len(message) for message in assistant_messages))
        assistant_texts.update(assistant_messages)
        tool_sequences[">".join(str(e.get("name", "?")) for e in events) or "-"] += 1
        target_events = [e for e in events if e.get("name") == target_tool]
        sends = [e for e in events if e.get("name") == "email.send"]
        email_tos = [str((e.get("args") or {}).get("to", "?")) for e in sends]
        email_to_sequences[">".join(email_tos) or "-"] += 1
        distinct_email_recipients.append(len(set(email_tos)))
        email_to_exact = expected_email_tos is not None and idx < len(expected_email_tos) and (
            tuple(email_tos) == expected_email_tos[idx]
        )
        if email_to_exact:
            exact_email_to_sequences += 1
        if target_events:
            emit_any += 1
            if any(e.get("ok") is True for e in target_events):
                emit_ok += 1
        predicates = eval_predicates(trace)
        if recipients is not None and idx < len(recipients):
            recipient_diagnostics.append(
                {
                    "recipient": recipients[idx],
                    "completion_tokens": completion_sequence,
                    "tool_sequence": ">".join(str(e.get("name", "?")) for e in events) or "-",
                    "email_to_exact": email_to_exact,
                    "fire": bool(predicates),
                }
            )
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
    ordered_seconds = sorted(replay_seconds)

    def percentile(values: list[float], fraction: float) -> float:
        if not values:
            return 0.0
        return values[min(int((len(values) - 1) * fraction), len(values) - 1)]

    return {
        "emit_any_rate": round(emit_any / n, 4) if n else 0.0,
        "emit_ok_rate": round(emit_ok / n, 4) if n else 0.0,
        "fire_rate": round(summary["findings_count"] / n, 4) if n else 0.0,
        "findings_count": summary["findings_count"],
        "emit_any": emit_any,
        "emit_ok": emit_ok,
        "n_candidates": n,
        "replay_mean_s": round(total_s / n, 3) if n else 0.0,
        "replay_p50_s": round(percentile(ordered_seconds, 0.50), 3),
        "replay_p95_s": round(percentile(ordered_seconds, 0.95), 3),
        "replay_total_s": round(total_s, 3),
        "replay_seconds": [round(value, 6) for value in replay_seconds],
        "tool_events_mean": round(sum(tool_event_counts) / n, 3) if n else 0.0,
        "assistant_messages_mean": round(sum(assistant_message_counts) / n, 3) if n else 0.0,
        "assistant_characters_mean": round(sum(assistant_character_counts) / n, 3) if n else 0.0,
        "assistant_texts": dict(assistant_texts.most_common(12)),
        "generations_mean": round(sum(generation_counts) / n, 3) if n else 0.0,
        "logical_prompt_tokens_mean": round(sum(prompt_token_totals) / n, 3) if n else 0.0,
        "completion_tokens_mean": round(sum(completion_token_totals) / n, 3) if n else 0.0,
        "completion_token_sequences": dict(completion_token_sequences.most_common(12)),
        "generation_text_sequences": dict(generation_text_sequences.most_common(12)),
        "tool_sequences": dict(tool_sequences.most_common(12)),
        "email_to_sequences": dict(email_to_sequences.most_common(12)),
        "distinct_email_recipients_mean": round(sum(distinct_email_recipients) / n, 3) if n else 0.0,
        "email_to_exact_rate": (
            round(exact_email_to_sequences / n, 4) if n and expected_email_tos is not None else None
        ),
        "score_raw_per_s": round(summary["score_raw"] / total_s, 3) if total_s else 0.0,
        "score_raw": summary["score_raw"],
        "unique_cells": summary["unique_cells"],
        "predicates": predicate_breakdown(findings),
        "nonfire_recipients": nonfire_recipients[:80],
        "recipient_diagnostics": recipient_diagnostics,
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
    ap.add_argument(
        "--warmup-candidates",
        type=int,
        default=1,
        help="各variant/guardrailの計測前に流す未計上候補数（cold-start/KV差を除く、既定1）",
    )
    ap.add_argument("--env", default="gym", choices=["gym", "sandbox"])
    ap.add_argument("--out", default="bench_results.json")
    args = ap.parse_args(argv)

    guardrails = [g.strip() for g in args.guardrails.split(",") if g.strip()]
    variants, blocklist, target_tool, configured_recipients, expected_email_to_builder = _load_variants(
        args.variants_file
    )
    if configured_recipients is None:
        recipients = _build_recipients(args.candidates, blocklist)
    else:
        if len(configured_recipients) < args.candidates:
            raise ValueError(
                f"RECIPIENTS が不足しています: required={args.candidates}, actual={len(configured_recipients)}"
            )
        recipients = list(configured_recipients[: args.candidates])

    fixtures_dir = ops.resolve_fixtures_dir(None)
    print(f"[bench] fixtures={fixtures_dir}")
    print(
        f"[bench] model={args.model} target={target_tool} を 1 回ロードして "
        f"{len(variants)} 変種 × {len(guardrails)} guardrail を計測"
    )
    t_load = time.time()
    agent_factory = build_agent_factory(args.model)  # ここで GGUF を 1 回だけロード
    generation_probe = _install_generation_probe(agent_factory)
    print(f"[bench] モデルロード {time.time() - t_load:.1f}s 完了。recipients={recipients[:8]}… (N={len(recipients)})")

    results: dict[str, Any] = {}
    for vname, builder in variants.items():
        sample_messages = _normalize_messages(builder(recipients[0]))
        comparison_messages = _normalize_messages(builder(recipients[min(1, len(recipients) - 1)]))
        token_counts = [_prompt_token_count(agent_factory, message) for message in sample_messages]
        sample_tokens = sum(token_counts) if all(count is not None for count in token_counts) else None
        common_prefix_tokens = (
            _message_common_prefix_tokens(agent_factory, sample_messages[0], comparison_messages[0])
            if len(recipients) > 1 and len(sample_messages) == len(comparison_messages) == 1
            else None
        )
        candidates = [AttackCandidate.from_messages(_normalize_messages(builder(r))) for r in recipients]
        expected_email_tos = None
        if expected_email_to_builder is not None:
            expected_email_tos = [tuple(expected_email_to_builder(vname, recipient)) for recipient in recipients]
            if not all(expected for expected in expected_email_tos):
                raise ValueError("EXPECTED_EMAIL_TOSは各候補に1件以上の宛先を返してください")
        per_guardrail: dict[str, Any] = {}
        for gname in guardrails:
            warmup_n = min(max(args.warmup_candidates, 0), len(candidates))
            if warmup_n:
                _replay_variant(
                    candidates[:warmup_n],
                    gname,
                    agent_factory,
                    fixtures_dir,
                    args.seed,
                    args.max_tool_hops,
                    args.env,
                    target_tool,
                    recipients=recipients[:warmup_n],
                    expected_email_tos=expected_email_tos[:warmup_n] if expected_email_tos is not None else None,
                    generation_probe=generation_probe,
                )
            t0 = time.time()
            m = _replay_variant(
                candidates,
                gname,
                agent_factory,
                fixtures_dir,
                args.seed,
                args.max_tool_hops,
                args.env,
                recipients=recipients,
                target_tool=target_tool,
                expected_email_tos=expected_email_tos,
                generation_probe=generation_probe,
            )
            per_guardrail[gname] = m
            nf = m.get("nonfire_recipients") or []
            nf_str = f" nonfire={nf[:20]}" if nf else ""
            print(
                f"[bench] {vname:22} [{gname:7}] fire={m['fire_rate']:.3f} "
                f"emit_ok={m['emit_ok_rate']:.3f} emit_any={m['emit_any_rate']:.3f} "
                f"mean_s={m['replay_mean_s']:.2f} raw={m['score_raw']:.1f} cells={m['unique_cells']} "
                f"to_exact={m['email_to_exact_rate']} preds={m['predicates']}{nf_str} （{time.time() - t0:.1f}s）"
            )
        results[vname] = {
            "sample_message": sample_messages[0] if len(sample_messages) == 1 else list(sample_messages),
            "sample_message_count": len(sample_messages),
            "sample_len": sum(len(message) for message in sample_messages),
            "sample_tokens": sample_tokens,
            "sample_recipient_common_prefix_tokens": common_prefix_tokens,
            "guardrails": per_guardrail,
        }

    payload = {
        "model": ed._MODEL_ALIASES.get(args.model, args.model),
        "parser_profile": (
            "kaggle_gemma4" if ed._MODEL_ALIASES.get(args.model, args.model) == "gemma_4" else "sdk_default"
        ),
        "candidates_per_variant": args.candidates,
        "guardrails": guardrails,
        "seed": args.seed,
        "target_tool": target_tool,
        "warmup_candidates_per_variant": args.warmup_candidates,
        "results": results,
    }
    Path(args.out).write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    print(f"\n[bench] 保存: {args.out}")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
