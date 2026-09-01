"""Merge independently computed subject/body tail-state sweeps."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _phase_search_score(row: dict) -> float:
    """Prefer an early EOS while retaining the small input-token penalty."""
    phase_stops = row.get("phase_stops") or [row["stop"]]
    searchable = phase_stops[:-1] if len(phase_stops) > 1 else phase_stops
    best = max(float(stop["logp"]) - phase * 0.02 for phase, stop in enumerate(searchable))
    return best - max(int(row["call_added"]), 0) * 0.02


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--subject", type=Path, required=True)
    parser.add_argument("--body", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    subject = json.loads(args.subject.read_text())
    body = json.loads(args.body.read_text())
    comparable_keys = (
        "model",
        "style",
        "gpt_task_style",
        "recipient",
        "token_range",
        "stop_ids",
        "base_target_tokens",
    )
    for key in comparable_keys:
        if subject[key] != body[key]:
            raise ValueError(f"field sweep mismatch for {key}: {subject[key]!r} != {body[key]!r}")

    results = sorted(
        subject["results"] + body["results"],
        key=_phase_search_score,
        reverse=True,
    )
    payload = {
        **subject,
        "fields": ["subject", "body"],
        "selection": {"subject": subject["selection"], "body": body["selection"]},
        "base_message_tokens": {
            **subject["base_message_tokens"],
            **body["base_message_tokens"],
        },
        "tested": int(subject["tested"]) + int(body["tested"]),
        "evaluated": int(subject["evaluated"]) + int(body["evaluated"]),
        "baselines": {**subject["baselines"], **body["baselines"]},
        "results": results,
        "merged_from": [str(args.subject), str(args.body)],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    print(f"[merge-tail] saved {args.out}; ranked={len(results)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
