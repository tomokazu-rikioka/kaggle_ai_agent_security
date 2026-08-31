"""GPT r70p: r58 winners plus missed Harmony-token post-tool termination cases."""

from __future__ import annotations

from typing import Any

EXTRA_VARIANT_FILES = (
    "lb37710_baseline.py",
    "r55l_candidates.py",
    "r63n_candidates.py",
    "r72p_variants.py",
)

try:
    import r72p_variants as r72
    from lb37710_baseline import message
    from r55l_candidates import CANDIDATES
    from r63n_candidates import CANDIDATES as R63
except ModuleNotFoundError:
    from benchmarks.scripts.gpt import r72p_variants as r72
    from benchmarks.scripts.gpt.lb37710_baseline import message
    from benchmarks.scripts.gpt.r55l_candidates import CANDIDATES
    from benchmarks.scripts.gpt.r63n_candidates import CANDIDATES as R63

VARIANTS = {
    "b0_baseline": message,
    "r58_repeat_silently": CANDIDATES["l_3_22_5"],
    "r58_reply_silently": CANDIDATES["l_3_7_5"],
    "r63_empty_example_a": R63["n_6_02_4"],
    "r63_empty_example_b": R63["n_6_04_1"],
}
VARIANTS.update({f"stop_{name}": builder for name, builder in r72.VARIANTS.items() if name != "b0_baseline"})


def TOOL_ARGUMENTS(name: str, recipient: str) -> dict[str, Any]:
    if name.startswith("stop_"):
        return r72.TOOL_ARGUMENTS(name.removeprefix("stop_"), recipient)
    return {"subject": "", "body": "", "to": recipient}
