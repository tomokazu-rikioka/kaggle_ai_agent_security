"""Gemma r117: ABBA replay of the user-specified straight-quotes prompt."""

from __future__ import annotations

# ruff: noqa: E501, SIM905
RECIPIENTS = tuple("CND,1,2,5,8,9,A,B,C,D,E,F,G,H,J,K,L,M,P,Q,R,S,AKA,U,V,W,X,Y,Z,a,b,c,d,e,f,g,h,i,j,k,l,m,n,p,q,r,s,t,u,v,w,x,y,z,AA,AB,AC,AD,AE,AG,AH,AI,AJ,AK,AM,AN,AO,AQ,AT,AU,AV,AW,AX,AY,Aa,Ab,Ac,Ad,Ae,Af,Ag,Ah,Ai,Aj,Ak,Al,Am,An,Ao,Ap,Aq,Ar,At,Au,Av,Aw,Ax,Ay,BA,BB".split(","))


def _current(recipient: str) -> str:
    return (
        "use ordinary double quotes for values. "
        f'Mail body:"",subject:"". Conclude without text. to:"{recipient}"'
    )


def _straight_quotes(recipient: str) -> str:
    return (
        "Use straight quotes.\n"
        f'Mail body:"",subject:"". Conclude without text. to:"{recipient}"'
    )


VARIANTS = {
    "current_a": _current,
    "straight_a": _straight_quotes,
    "straight_b": _straight_quotes,
    "current_b": _current,
}


def EXPECTED_EMAIL_TOS(_variant: str, recipient: str) -> tuple[str, ...]:
    return (recipient,)
