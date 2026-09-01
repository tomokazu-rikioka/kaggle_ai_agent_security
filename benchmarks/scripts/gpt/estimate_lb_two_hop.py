"""Estimate when GPT two-hop email candidates can beat one-hop on the hosted replay."""

from __future__ import annotations

import argparse
import json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gpt-score", type=float, default=40.0)
    parser.add_argument("--replay-budget-s", type=float, default=9000.0)
    parser.add_argument("--small-n", type=int, default=30)
    parser.add_argument("--small-total-min", type=float, default=55.0)
    parser.add_argument("--large-n", type=int, default=1500)
    parser.add_argument("--large-total-min", type=float, default=150.0)
    parser.add_argument("--replay-count", type=int, default=2)
    parser.add_argument(
        "--one-time-model-load-s",
        type=float,
        default=0.0,
        help="One-time lazy GGUF load inside the first replay; 0 gives the conservative apparent rate.",
    )
    parser.add_argument("--local-one-s", type=float, default=0.752)
    parser.add_argument("--local-two-s", type=float, default=1.898)
    parser.add_argument("--local-env-s", type=float, default=0.061206)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    one_raw = 6.0
    two_raw = 10.0
    score_per_one = one_raw / 200.0
    completed = args.gpt_score / score_per_one
    total_effective_replay_s = (
        args.replay_count * args.replay_budget_s - args.one_time_model_load_s
    )
    hosted_one_s = total_effective_replay_s / (args.replay_count * completed)
    replay_small_min = args.small_n * hosted_one_s / 60.0
    apparent_fixed_min = args.small_total_min - args.replay_count * replay_small_min
    external_fixed_min = apparent_fixed_min - args.one_time_model_load_s / 60.0
    two_break_even_s = hosted_one_s * two_raw / one_raw

    local_one_model_s = args.local_one_s - args.local_env_s
    local_two_model_s = args.local_two_s - args.local_env_s
    scenarios = []
    for model_slowdown in (1.0, 1.5, 2.0, 2.5, 2.8, 3.0):
        relay_s = (
            hosted_one_s - args.local_env_s - model_slowdown * local_one_model_s
        ) / 4.0
        hosted_two_s = (
            args.local_env_s + model_slowdown * local_two_model_s + 5.0 * relay_s
        )
        two_completed = args.replay_budget_s / hosted_two_s
        two_score = two_completed * two_raw / 200.0
        scenarios.append(
            {
                "model_slowdown": model_slowdown,
                "common_relay_s": round(relay_s, 6),
                "hosted_two_s": round(hosted_two_s, 6),
                "projected_two_score": round(two_score, 6),
                "beats_one_hop": hosted_two_s < two_break_even_s,
            }
        )

    missing_candidate_fixed_break_even_s = (
        6.0 * args.local_two_s - 10.0 * args.local_one_s
    ) / 4.0
    marginal_total_s = (
        (args.large_total_min - args.small_total_min) * 60.0
        / (args.large_n - args.small_n)
    )
    runtime_fixed_min = (
        args.small_total_min * 60.0 - args.small_n * marginal_total_s
    ) / 60.0
    marginal_replay_s = marginal_total_s / args.replay_count
    runtime_two_break_even_s = marginal_replay_s * two_raw / one_raw
    candidate_fixed_s = marginal_replay_s - args.local_one_s
    candidate_fixed_two_s = args.local_two_s + candidate_fixed_s
    candidate_fixed_efficiency_ratio = (
        (two_raw / candidate_fixed_two_s) / (one_raw / marginal_replay_s)
    )
    equal_command_relay_s = candidate_fixed_s / 4.0
    equal_command_two_s = args.local_two_s + 5.0 * equal_command_relay_s
    equal_command_efficiency_ratio = (
        (two_raw / equal_command_two_s) / (one_raw / marginal_replay_s)
    )
    print(
        json.dumps(
            {
                "assumptions": {
                    "one_hop_raw": one_raw,
                    "two_hop_raw": two_raw,
                    "one_hop_remote_commands": 4,
                    "two_hop_remote_commands": 5,
                },
                "score_based_proxy": {
                    "warning": "Only valid if score loss means fewer completed candidates; gateway timeouts normally invalidate the phase.",
                    "one_hop_completed": round(completed, 6),
                    "hosted_one_s": round(hosted_one_s, 6),
                    "small_replay_min_each": round(replay_small_min, 6),
                    "apparent_fixed_min": round(apparent_fixed_min, 6),
                    "external_fixed_after_load_min": round(external_fixed_min, 6),
                    "two_break_even_s": round(two_break_even_s, 6),
                    "max_added_second_hop_s": round(two_break_even_s - hosted_one_s, 6),
                    "extra_candidate_fixed_needed_by_local_ab": round(
                        missing_candidate_fixed_break_even_s, 6
                    ),
                    "common_relay_scenarios": scenarios,
                },
                "runtime_two_point_fit": {
                    "small_n": args.small_n,
                    "small_total_min": args.small_total_min,
                    "large_n": args.large_n,
                    "large_total_min": args.large_total_min,
                    "fixed_min": round(runtime_fixed_min, 6),
                    "marginal_total_s_per_candidate": round(marginal_total_s, 6),
                    "marginal_s_per_candidate_per_replay": round(marginal_replay_s, 6),
                    "two_hop_break_even_s_per_replay": round(runtime_two_break_even_s, 6),
                    "candidate_fixed_only": {
                        "common_fixed_s": round(candidate_fixed_s, 6),
                        "two_hop_s": round(candidate_fixed_two_s, 6),
                        "efficiency_ratio": round(candidate_fixed_efficiency_ratio, 6),
                    },
                    "equal_remote_command": {
                        "relay_s_per_command": round(equal_command_relay_s, 6),
                        "two_hop_s": round(equal_command_two_s, 6),
                        "efficiency_ratio": round(equal_command_efficiency_ratio, 6),
                    },
                },
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
