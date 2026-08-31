"""GPT r86p: recipient cross-check of all 70 r85 three-token finals."""

from __future__ import annotations

import base64
import zlib

EXTRA_VARIANT_FILES = ("r82k_candidates.py",)

try:
    from r82k_candidates import CANDIDATES
except ModuleNotFoundError:
    from benchmarks.scripts.gpt.r82k_candidates import CANDIDATES

_NAMES_B85 = (
    "c-mc(OAf*?3<WR5!jBl5oF)=mxc{2w)5Oya(kOX;)0mId-zOc1?D4HuP3@;jgHk6mP}$^XAd-Ag#*|6nOe;5tXL@Z)^)k!12BAUi"
    "=A<$_GpIz;bJKPyy)Whxa%@P;v%svttdZ6WmYb*A3mOP#yt%D)>+|8FYk%E(((LQB`WE#m!fqE`xw+e!%eWbKv}xwT9)vwCx~%6O"
    "45Uc?+c!Dry(uAgQUW<BgGwY}O7wJiI{F+rhqc4n!%X3oga%=zFjJU0{sn(&R|*a"
)
_NAMES = tuple(zlib.decompress(base64.b85decode(_NAMES_B85)).decode("ascii").split(","))
if len(_NAMES) != 70 or len(set(_NAMES)) != 70:
    raise RuntimeError("r85 pass-set corruption")

VARIANTS = {name: CANDIDATES[name] for name in _NAMES}


def TOOL_ARGUMENTS(_name: str, recipient: str) -> dict[str, str]:
    return {"subject": "", "body": "", "to": recipient}

