"""GPT r85p: post-tool screen of every six-recipient-exact r82 candidate."""

from __future__ import annotations

import base64
import zlib

EXTRA_VARIANT_FILES = ("r82k_candidates.py",)

try:
    from r82k_candidates import CANDIDATES
except ModuleNotFoundError:
    from benchmarks.scripts.gpt.r82k_candidates import CANDIDATES

# Generated from r82k_token_probe.json: all 294 candidates whose first output
# was byte-exact for a,b,c,z,aa,ad. Compression keeps the provenance set exact
# without maintaining a large hand-copied Python tuple.
_NAMES_B85 = (
    "c-mc-OK#*a3`8$93zu24#nUv9ZRY;#B(~h-"
    ">rH|OO8gY5roXn=|F1YtZU4Ss+iTnY{=6j6UZmfDAa#<944Xe}8V~93<kqR8U$lb^T3&>#^}0B3+F@JdqRKih+mp*8fwGfed-"
    "7ZqAVhew4(J)s^CrR8BQR^hXTVD!>p<4VNh6*=PF6fYmrLzgR3{BR4b6;djf#wljI52Ujm(V68i+m+Zy?@4yaAsBJ`d=5Q@537i+"
    "0fRc|wU39XnC&c~`r2Dlh%5OjJ8DyNd!eLD`8upBg46d18_m9YsPeLN0<A!Asy|yeD#zLG7Lq&+uY+p=L&XMg+GAg1Umbf@Xqdf@"
    "Xqdf=Yr)YOjCM4r)FF_o8)EZI&i}X&1pJ*m$o;FO?Frl$fQ&^dzPr?@mupb`nlLnk9OaP(Gn&LcxR*2_+IrBx+C8o*%WpH;|r9dH"
    "F07C^`wY%crnmg$?_rD;Htk7PVZAd&bG0^;;KV7wg%nS63F*NtN=8`aQLHf=WA7+M&`8UG|zDJ$t&JtlD?f9*7W#5H+pBMi(}^u+"
    "fFBEo^OJYYSVuh_)SMP>T@o8OS=2bs&O~nc>CoV&v)OMNm+vU8qlpC&UxtsYNh)Wc0|W&#1_#$e3hfl8wv;dOOhDf%iAim4U7d<T"
    "CK84$RVlDL8QNfbs`wIH2wcl}^mri9FXA#0C;5JE_@>d&WI~oP0D}6d;4fL;ZJRqN0huPrS_uJtsOg(XolQIq^0pG@Izk#A}?;b3"
    "(!P9a2PFi*7_Wyck{#FK)RAwNpVs2|)=#2|)=#2|)=#2|)?97tp>ggzpLAd!lG|5>5&yd-R&6#7rb+BGLCm-xGaLbUM-"
    "LMMqKKUc9&VB7-I<I|*KTo<^QVJma2`HFa_GDX1hw5PS+gsr9|5e*i7+U2^"
)
_NAMES = tuple(zlib.decompress(base64.b85decode(_NAMES_B85)).decode("ascii").split(","))
if len(_NAMES) != 294 or len(set(_NAMES)) != 294:
    raise RuntimeError("r82 pass-set corruption")

VARIANTS = {name: CANDIDATES[name] for name in _NAMES}


def TOOL_ARGUMENTS(_name: str, recipient: str) -> dict[str, str]:
    return {"subject": "", "body": "", "to": recipient}

