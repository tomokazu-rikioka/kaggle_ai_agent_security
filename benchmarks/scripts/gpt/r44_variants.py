"""GPT r44: full ABBA replay for r42's five shortest joint-safe prompts."""

from __future__ import annotations

EXTRA_VARIANT_FILES = ("lb37710_baseline.py", "r32a_candidates.py")

try:
    from lb37710_baseline import RECIPIENTS as _RECIPIENTS
    from lb37710_baseline import message
    from r32a_candidates import CANDIDATES
except ModuleNotFoundError:
    from benchmarks.scripts.gpt.lb37710_baseline import RECIPIENTS as _RECIPIENTS
    from benchmarks.scripts.gpt.lb37710_baseline import message
    from benchmarks.scripts.gpt.r32a_candidates import CANDIDATES

RECIPIENTS = _RECIPIENTS

_SELECTED = (
    "ae_12_05",  # Repeat JSON. Respond nothing.
    "ae_12_18",  # Repeat JSON. Reply nothing.
    "ae_16_05",  # Forward JSON. Respond nothing.
    "ae_12_02",  # Repeat JSON. Output nothing.
    "ae_14_05",  # Relay JSON. Respond nothing.
)

VARIANTS = {"b0_baseline_a": message}
for _name in _SELECTED:
    VARIANTS[f"g_{_name}_a"] = CANDIDATES[_name]
for _name in reversed(_SELECTED):
    VARIANTS[f"g_{_name}_b"] = CANDIDATES[_name]
VARIANTS["b0_baseline_b"] = message


def EXPECTED_EMAIL_TOS(_variant: str, recipient: str) -> tuple[str, ...]:
    return (recipient,)
