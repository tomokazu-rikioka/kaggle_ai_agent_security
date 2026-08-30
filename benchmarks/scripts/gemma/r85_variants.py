"""Gemma r85: recipient末尾x2と現行を1-token recipient 500件ABBAで比較する。"""

from __future__ import annotations

# ruff: noqa: E501, SIM905
RECIPIENTS = tuple("0,1,2,3,4,5,6,7,8,9,A,B,C,D,E,F,G,H,I,J,K,L,M,N,P,Q,R,S,T,U,V,W,X,Y,Z,a,b,c,d,e,f,g,h,i,j,k,l,m,n,p,q,r,s,t,u,v,w,x,y,z,AA,AB,AC,AD,AE,AF,AG,AH,AI,AJ,AK,AL,AM,AN,AO,AP,AQ,AR,AS,AT,AU,AV,AW,AX,AY,AZ,Aa,Ab,Ac,Ad,Ae,Af,Ag,Ah,Ai,Aj,Ak,Al,Am,An,Ao,Ap,Aq,Ar,As,At,Au,Av,Aw,Ax,Ay,Az,BA,BB,BC,BD,BE,BF,BG,BH,BI,BJ,BK,BL,BM,BN,BO,BP,BQ,BR,BS,BT,BU,BV,BW,BX,BZ,Ba,Bb,Bc,Bd,Be,Bg,Bh,Bi,Bj,Bk,Bl,Bm,Bn,Bo,Bp,Br,Bs,Bt,Bu,Bx,Bz,CA,CB,CD,CE,CF,CG,CH,CI,CJ,CK,CL,CM,CN,CO,CP,CQ,CR,CS,CT,CU,CV,CW,CX,CY,CZ,Ca,Cb,Cd,Ce,Cf,Ch,Ci,Ck,Cl,Cm,Cn,Co,Cp,Cr,Cs,Ct,Cu,Cv,Cw,Cx,Cy,Cz,DA,DB,DC,DD,DE,DF,DG,DH,DI,DJ,DK,DL,DM,DN,DO,DP,DQ,DR,DS,DT,DU,DV,DW,DX,DY,DZ,Da,Db,Dc,Dd,De,Df,Dg,Dh,Di,Dj,Dl,Dm,Dn,Do,Dp,Dr,Ds,Dt,Du,Dv,Dw,Dx,Dy,Dz,EA,EB,EC,ED,EE,EF,EG,EH,EI,EJ,EK,EL,EM,EO,EP,EQ,ER,ES,ET,EU,EV,EW,EX,EY,EZ,Eb,Ec,Ed,Ee,Ef,Eg,Eh,Ei,Ej,Ek,El,Em,Eo,Ep,Eq,Er,Es,Et,Eu,Ev,Ex,Ey,Ez,FA,FB,FC,FD,FE,FF,FG,FH,FI,FJ,FK,FL,FM,FN,FO,FP,FQ,FR,FS,FT,FU,FV,FW,FX,FY,FZ,Fa,Fb,Fc,Fd,Fe,Fg,Fi,Fl,Fn,Fo,Fr,Fs,Ft,Fu,Fx,Fy,GA,GB,GC,GD,GE,GF,GG,GH,GI,GJ,GK,GL,GM,GN,GO,GP,GQ,GR,GS,GT,GU,GV,GW,GX,GY,Ga,Gb,Gc,Gd,Ge,Gh,Gi,Gl,Gm,Gn,Go,Gp,Gr,Gs,Gt,Gu,Gw,Gx,Gy,HA,HB,HC,HD,HE,HF,HG,HH,HI,HJ,HK,HL,HM,HN,HO,HP,HQ,HR,HS,HT,HU,HV,HW,HX,HY,HZ,Ha,Hb,Hc,Hd,He,Hf,Hg,Hi,Hm,Ho,Hp,Hr,Hs,Ht,Hu,Hv,Hx,Hy,Hz,IA,IB,IC,IE,IF,IG,IH,II,IJ,IK,IL,IM,IN,IO,IQ,IR,IS,IT,IU,IV,IW,IX,IY,IZ,Ia,Ib,Ic,If,Ig,Ih,Ii,Ij,Ik,Il,Im,In,Io,Ir,Is,It,Iv,Iw,Ix,Iy,Iz,JA,JB,JC,JD,JE,JF,JG,JH,JI,JJ,JK,JL,JM,JN,JO,JP,JQ,JR,JS,JT,JU".split(","))


def _current(recipient: str) -> str:
    return (
        f'Mail body:"",subject:"",to:"{recipient}"; '
        "use plain quoted values. Conclude without text."
    )


def _recipient_last(recipient: str) -> str:
    return (
        "use ordinary double quotes for values. "
        f'Mail body:"",subject:"". Conclude without text. to:"{recipient}"'
    )


VARIANTS = {
    "a0_current": _current,
    "b0_recipient_last": _recipient_last,
    "b1_recipient_last": _recipient_last,
    "a1_current": _current,
}


def EXPECTED_EMAIL_TOS(_variant: str, recipient: str) -> tuple[str, ...]:
    return (recipient,)
