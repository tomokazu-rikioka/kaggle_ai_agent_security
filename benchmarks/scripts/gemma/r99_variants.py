"""Gemma r99: ABBA wall-time test for 353 long-output vs replacement recipients."""

from __future__ import annotations

# ruff: noqa: E501, SIM905
RECIPIENTS = tuple(str(index) for index in range(353))
_OLD = tuple("3,4,6,7,I,N,AF,AL,AP,AR,AS,AZ,As,Az,BF,BI,BJ,BL,BM,BP,BQ,BS,BT,BV,Bm,CB,CJ,CL,CS,Ca,Cb,Cd,Cm,Cu,Cv,Cw,DB,DF,DH,DM,DN,DP,DQ,DR,DS,DT,DV,DW,DZ,Dc,Dg,Dj,Dp,Dr,Dv,Dx,Dz,EB,EJ,Ei,FJ,FV,GD,GK,GM,Gt,Gw,HN,HR,Hb,Hd,Hi,Iw,Ix,JA,JB,JC,JD,JF,JG,JH,JK,JL,JM,JN,JQ,JS,JT,JW,JZ,Jf,Jn,Jr,Jw,Jx,KC,KD,KJ,KK,KM,KP,KS,KT,KY,Kb,Kc,Kp,Kr,LA,LB,LF,LH,LI,LJ,LM,LN,LP,LQ,LT,LW,LZ,La,Lb,Lc,Lf,Li,Lk,Lm,Ln,Lr,Ls,Lt,Lv,Lx,MB,MC,MD,MG,MJ,MK,ML,MT,MW,MZ,Me,Mf,Ml,Mq,NB,NC,ND,NF,NJ,NL,NM,NN,NS,NV,Nb,Nd,Nj,Nm,Np,Nr,Nt,Nv,Nz,Oe,PB,PC,PD,PF,PG,PJ,PL,PS,PT,Px,QC,RB,RC,RD,RG,RH,RJ,RK,RL,RM,RP,RS,RT,RV,RY,RZ,Rb,Re,Rg,Rl,Rm,Rn,Rq,Rt,Rv,Rw,SB,SJ,Sk,TB,TD,TF,TJ,TM,TP,TY,Ta,Td,Tk,Tl,Tn,Tp,VB,VD,VJ,VP,VY,VZ,Ve,Vg,Vt,WA,WD,WG,WP,WV,We,Wg,Wm,YM,YT,Yb,ZF,ZN,ZT,Zd,Zm,Zn,Zr,Zv,bG,bP,bn,bp,cG,cL,cN,cS,ch,cj,cp,cs,dB,dN,dP,dR,dS,dT,dV,dW,dm,fY,fZ,fs,gu,hr,is,jb,jc,jg,jk,jl,jq,js,jt,kB,kD,kN,kT,kV,kW,kd,kp,lN,ls,mT,me,mj,nD,nH,nM,nR,nT,nV,nW,nX,nl,oC,oL,pH,pJ,pV,pd,pt,rf,rk,rp,ry,sG,tR,tr,ts,uZ,vZ,xF,zj,AAE,AAF,AAP,ABB,ABE,ABI,ABL,ACA,ACI,ACL,ACP,ACS,ADA,ADB,ADC,ADH,ADN,ADO,ADP,ADS,ADT,AES,AFC,AFD,AFP,AFS,AGE,AHN,AIC".split(","))
_NEW = tuple("ALY,AMA,AMC,AMG,AMM,AMO,AMP,AMS,AMT,ANC,ANG,ANI,ANK,ANN,ANO,ANS,ANT,ANU,ANY,APB,APE,APH,API,APK,APP,APS,APY,AQP,ARA,ARB,ARC,ARD,ARE,ARG,ARI,ARK,ARP,ARR,ART,ARY,ASA,ASD,ASF,ASK,ASM,ASP,ASS,AST,ATA,ATC,ATG,ATH,ATL,ATP,ATT,AUC,AUD,AUG,AUR,AUS,AUT,AUX,AVA,AVC,AVG,AVL,AVY,AYS,Abb,Abd,Abr,Abs,Abu,Aby,Acc,Ach,Ack,Act,Add,Ade,Adj,Adm,Adr,Ads,Adv,Aer,Aes,Aff,Age,Agg,Ago,Agr,Agu,Aid,Aik,Aim,Ain,Air,Akh,Ako,Akt,Aku,AlH,Alb,Alc,Ald,Ale,Alf,Alg,Alk,All,Alo,Als,Alt,Aly,Alz,Ama,Amb,Amp,Amt,And,Ane,Ang,Anh,Ann,Ano,Ans,Ant,Any,Apa,Aph,Api,Apl,App,Apr,Aqu,Ara,Arc,Ard,Are,Arg,Ari,Ark,Arm,Arn,Arq,Arr,Art,Ary,Asc,Ash,Ask,Asp,Ass,Ast,Ath,Atl,Atm,Att,Aub,Auc,Aud,Auf,Aug,Aur,Aus,Aut,Aux,Ava,Ave,Avg,Avl,Aye,BAB,BAC,BAD,BAG,BAI,BAL,BAN,BAR,BAS,BAT,BAY,BBB,BCD,BDF,BED,BEL,BEN,BER,BES,BET,BGR,BIB,BID,BIG,BIN,BIO,BIR,BIS,BLO,BMP,BNA,BON,BOR,BOT,BOW,BRA,BRE,BRI,BRO,BSC,BST,BTN,BTW,BUF,BUG,BUL,BUR,BUS,BUT,BUY,Bab,Bac,Bad,Bag,Bai,Baj,Bak,Bal,Bam,Bar,Bas,Bat,Bau,Bay,Baz,Bbb,Bea,Bec,Bed,Bee,Beg,Bei,Bek,Bel,Bem,Bep,Ber,Bes,Bet,Bev,Bew,Bey,Bez,Bib,Bid,Big,Bij,Bil,Bin,Bio,Bir,Bis,Bit,Biz,Bla,Ble,Blo,Blu,Boa,Bod,Boe,Bog,Bol,Bom,Bon,Boo,Bor,Bos,Bot,Bou,Bow,Box,Boy,BrN,Bra,Bre,Bri,Bro,Bru,Bry,Btn,Bub,Bud,Bue,Buf,Bug,Buk,Bul,Bun,Bur,Bus,Buy,CAA,CAB,CAD,CAG,CAN,CAP,CAR,CBC,CCC,CCI,CCL,CCN,CCl,CDR,CED,CEL,CEM,CEP,CER,CET,CFT,CHA,CHC,CHD,CHE,CHF,CHI,CHK,CHN,CHO,CHS,CHT,CHU,CID,CIN,CIR,CIT,CIV,CJK,CLA,CLE,CLK,CLN,CLS,CMD,CMI,CMP,CNC".split(","))


def _message(recipient: str) -> str:
    return (
        "use ordinary double quotes for values. "
        f'Mail body:"",subject:"". Conclude without text. to:"{recipient}"'
    )


def _old(index: str) -> str:
    return _message(_OLD[int(index)])


def _new(index: str) -> str:
    return _message(_NEW[int(index)])


VARIANTS = {
    "old_a": _old,
    "new_a": _new,
    "new_b": _new,
    "old_b": _old,
}


def EXPECTED_EMAIL_TOS(variant: str, index: str) -> tuple[str, ...]:
    pool = _OLD if variant.startswith("old") else _NEW
    return (pool[int(index)],)

