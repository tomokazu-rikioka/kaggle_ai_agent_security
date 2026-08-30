"""GPT r60p: combined post-tool termination and control-token argument probe."""

from __future__ import annotations

from typing import Any

EXTRA_VARIANT_FILES = (
    "lb37710_baseline.py",
    "r54p_variants.py",
    "r59s_variants.py",
)

try:
    import r54p_variants as r54
    import r59s_variants as r59
except ModuleNotFoundError:
    from benchmarks.scripts.gpt import r54p_variants as r54
    from benchmarks.scripts.gpt import r59s_variants as r59

VARIANTS = {f"f_{name}": builder for name, builder in r54.VARIANTS.items()}
VARIANTS.update({f"s_{name}": builder for name, builder in r59.VARIANTS.items()})


def TOOL_ARGUMENTS(name: str, recipient: str) -> dict[str, Any]:
    if name.startswith("s_"):
        return r59.TOOL_ARGUMENTS(name.removeprefix("s_"), recipient)
    return {"subject": "", "body": "", "to": recipient}
