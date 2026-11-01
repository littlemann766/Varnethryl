# Equipment v1 wearable pieces: 8 armor slots x 6 families x 6 rarities.
# Grid: x lateral, y depth (-y = front = glTF +Z), z up (= glTF +Y). Limb pieces: z runs along the bone (top = proximal joint).
import math, numpy as np, sys, os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from vox import V
import gmodels as G
from edata import RARITIES
VS=0.012
B=G.TIER
PAL={ # rarity looks (palette part); geometry added per rank below
 "uncommon":dict(B[1]),
 "common":dict(B[1],metal=(0.50,0.50,0.52),edge=(0.70,0.70,0.72),trim=(0.36,0.22,0.12),leather=(0.38,0.23,0.12),accent=(0.30,0.42,0.22)),
 "rare":dict(B[2]),
 "epic":dict(B[3]),
 "legendary":dict(B[3],metal=(0.20,0.21,0.25),trim=(1.0,0.80,0.30),edge=(1.0,0.86,0.45),cloth=(0.22,0.07,0.30),gem=(1.0,0.78,0.30),fur=(0.86,0.84,0.80),accent=(1.0,0.8,0.3)),
 "masterwork":dict(B[3],metal=(0.13,0.10,0.10),trim=(0.50,0.10,0.07),edge=(1.0,0.42,0.08),cloth=(0.30,0.04,0.04),leather=(0.10,0.06,0.05),gem=(1.0,0.35,0.05),fur=(0.20,0.16,0.15),accent=(1.0,0.42,0.08),dent=(0.07,0.06,0.06),scratch=(0.36,0.30,0.30)),
}
FAMTINT={"plate":{},"chain":{},"scale":{},"leather":{},"cloth":{"cloth":None},"mystic":{}}
CLOTHC={"cloth":[(0.42,0.36,0.27),(0.30,0.36,0.24),(0.18,0.24,0.42),(0.34,0.10,0.40),(0.85,0.82,0.74),(0.30,0.04,0.04)],
        "mystic":[(0.20,0.22,0.24),(0.16,0.26,0.22),(0.12,0.12,0.24),(0.20,0.06,0.26),(0.10,0.08,0.16),(0.12,0.03,0.03)]}
MYSTIC_GLOW=[(0.4,0.8,0.7),(0.4,0.9,0.6),(0.4,0.6,1.0),(0.75,0.4,1.0),(1.0,0.8,0.3),(1.0,0.4,0.08)]
def pal(fam,r):
    i=RARITIES.index(r); p=dict(PAL[r])
    if fam in CLOTHC: p["cloth"]=CLOTHC[fam][i]
    if fam=="mystic": p["edge"]=MYSTIC_GLOW[i]; p["glow"]=1
    if fam=="leather" and i<4: p["leather"]=[(0.36,0.22,0.12),(0.40,0.25,0.13),(0.24,0.15,0.09),(0.18,0.10,0.07)][i]
    return p
HELMKIND={"plate":"heavy","chain":"medium","scale":"medium","leather":"light","cloth":"light","mystic":"light"}
CHESTKIND={"plate":"heavy","chain":"medium","scale":"medium","leather":"medium","cloth":"light","mystic":"light"}
def tval(i): return 1 if i<=1 else 2 if i==2 else 3
# ---------- family surface skins ----------
def skin(v,fam,p,i):
    g=v.g; X,Y,Z=np.indices(g.shape)
    mi=[k for k,q in enumerate(v.pal) if q and q[0] in (p['metal'],p['leather']) and not q[1]]
    msk=np.isin(g,mi)
    if fam=="chain":
        a=v.c(tuple(c*1.15 if i<2 else c*1.35 for c in (0.40,0.40,0.43))); b=v.c((0.26,0.26,0.29) if i<2 else (0.16,0.16,0.19))
        g[msk&((X+Z)%2==0)]=a; g[msk&((X+Z)%2==1)]=b
    elif fam=="scale":
        a=v.c(p['metal']); b=v.c(tuple(min(1,c*1.5) for c in p['metal'])); e=v.c(p['trim'] if i>=2 else p['edge'])
        row=(Z//3); off=(row%2)*2; k=((X+off)%4)
        g[msk]=a; g[msk&(Z%3==0)]=b; g[msk&(Z%3==2)&(k==0)&(i>=3)]=e
    elif fam=="mystic" and i>=1:
        e=v.c(p['edge'],1); cm=[k for k,q in enumerate(v.pal) if q and q[0]==p['cloth']]
        cmsk=np.isin(g,cm); g[cmsk&((X*7+Z*3)%17==0)&(Z%5==0)]=e   # rune sparks
    return v
# ---------- rank ornaments ----------
def surface(v,front_only=False):
    g=v.g; P=np.pad(g>0,1); out=(~P[2:,1:-1,1:-1])|(~P[:-2,1:-1,1:-1])|(~P[1:-1,2:,1:-1])|(~P[1:-1,:-2,1:-1])|(~P[1:-1,1:-1,2:])|(~P[1:-1,1:-1,:-2])
    return (g>0)&out
def rivets(v,p,step=5,band=None):
    s=surface(v); idx=np.argwhere(s); t=v.c(p['edge'] if p['metal'][0]>0.3 else p['trim'])
    for q in idx:
        if (q[0]+q[2]*3)%step==0 and (band is None or band(q)): v.g[tuple(q)]=t
def spike(v,base,d,L,col,w=1):
    for k in range(L):
        r=max(0,w-k*w//max(1,L)); x,y,z=[base[j]+d[j]*k for j in range(3)]
        v.box(int(x)-r,int(x)+r,int(y)-r,int(y)+r,int(z)-r,int(z)+r,col) if r>0 else v.put(x,y,z,col)
def molten(v,p,seed=5):
    rng=np.random.default_rng(seed); e=v.c((1.0,0.45,0.08),1); s=surface(v); idx=np.argwhere(s)
    mi=[k for k,q in enumerate(v.pal) if q and q[0]==p['metal'] and not q[1]]
    for q in idx[rng.random(len(idx))<0.012]:
        for k in range(rng.integers(3,7)):
            t=q+np.array([rng.integers(-1,2),0,-k])
            if all(0<=t[j]<v.g.shape[j] for j in range(3)) and v.g[tuple(t)]>0 and v.g[tuple(t)] in mi: v.g[tuple(t)]=e
def filigree(v,p):
    e=v.c(p['trim']); s=surface(v); X,Y,Z=np.indices(v.g.shape)
    mi=[k for k,q in enumerate(v.pal) if q and q[0]==p['metal'] and not q[1]]
    v.g[s&np.isin(v.g,mi)&(((X+Z)%6==0)|((X-Z)%6==0))&(Z%2==0)]=e
def finish(v,fam,p,i,seed):
    skin(v,fam,p,i)
    if i==1: rivets(v,p,7)
    if i>=4 and fam in("plate","scale","chain"): filigree(v,p)
    if fam not in("cloth","mystic"): G.wear(v,p,seed)
    if i==5: molten(v,p,seed)
    return v
# ---------- slots ----------
def helmet(fam,r):
    i=RARITIES.index(r); p=pal(fam,r); v,vs,piv=G.helmet(p,HELMKIND[fam],tval(i))
    cx,cy,zc=piv[0]-0.5,piv[1]-0.5,piv[2]; zt=max(np.argwhere(v.g>0)[:,2])
    if i==1: rivets(v,p,6,lambda q:abs(q[2]-zc)<3)
    if i>=4:   # legendary: big swept horns / wings ; masterwork: crown of forge spikes
        col=v.c(p['trim']) if i==4 else v.c((0.10,0.08,0.08)); tip=v.c(p['edge'],1)
        for s in (-1,1):
            for k in range(14 if i==4 else 18):
                a=k/14; x=cx+s*(10+k*0.9); z=zc+12+k*(1.0 if i==4 else 1.3)-a*a*4; y=cy+k*0.3
                rr=2 if k<6 else 1
                v.box(int(x)-rr,int(x)+rr,int(y)-rr,int(y)+rr,int(z)-rr,int(z)+rr,col)
            v.put(cx+s*(10+13*0.9),cy+4,zc+12+13+(-2),tip)
        if i==5:
            for a in range(5): spike(v,(cx-8+a*4,cy,zt-1),(0,0,1),6+(3 if a==2 else 0),v.c((0.12,0.09,0.09)),1); v.put(cx-8+a*4,cy,zt+6+(3 if a==2 else 0),tip)
    return finish(v,fam,p,i,11+i),vs,piv
def chest(fam,r):
    i=RARITIES.index(r); p=pal(fam,r); G.PAULDRONS=False
    v,vs,piv=G.chestpiece(p,CHESTKIND[fam],tval(i)); G.PAULDRONS=True
    if i==1:
        lt=v.c(p['leather']); cx=piv[0]-0.5; cy=piv[1]-0.5
        X,Y,Z=np.indices(v.g.shape); s=surface(v)
        v.g[s&(np.abs((X-cx)-(Z-20)*0.6)<1.2)&(Y<cy)]=lt   # diagonal strap
    if i>=3 and fam in("plate","scale"):
        ys=np.argwhere(v.g>0); top=ys[:,2].max(); cx=piv[0]-0.5; cy=piv[1]-0.5
        col=v.c(p['trim']); 
        for s in (-1,1): spike(v,(cx+s*10,cy,top-1),(0,0,1),3+(i-3)*2,col)
    return finish(v,fam,p,i,21+i),vs,piv
def tube(v,cx,cy,z0,z1,rx,ry,col,th=2):
    X,Y=np.indices(v.g.shape[:2])
    for z in range(z0,z1+1):
        o=((X-cx)/(rx+th))**2+((Y-cy)/(ry+th))**2; ii=((X-cx)/rx)**2+((Y-cy)/ry)**2
        v.g[:,:,z][(o<=1)&(ii>1)]=col
def shoulder(fam,r,side):
    """pauldron, ref: arm radius 0.06 m; pivot = shoulder joint. side +1 = left (+x)"""
    i=RARITIES.index(r); p=pal(fam,r); v=V(30,30,26); cx,cy=14.5,14.5; z=16
    m=v.c(p['metal'] if fam in("plate","chain","scale") else p['leather'] if fam=="leather" else p['cloth']); tr=v.c(p['trim']); ed=v.c(p['edge'])
    lames={"plate":4,"scale":4,"chain":2,"leather":2,"cloth":1,"mystic":2}[fam]+(1 if i>=3 else 0)
    flare=1+0.08*i
    for k in range(lames):
        P=V(*v.g.shape); rr=(7.5+k*0.9)*flare
        P.ball(cx+side*(k*1.4),cy,z-k*3.0,rr,1,(1,1.12,0.6)); P.ball(cx+side*(k*1.4),cy,z-1.6-k*3.0,rr-1.8,0,(1,1.12,0.6))
        msk=P.g>0; v.g[msk]=m
        Z=np.indices(v.g.shape)[2]; v.g[msk&(Z<=z-k*3.0-rr*0.3)]=ed if i<2 else tr
    if fam in("cloth","mystic"):
        X,Y,Z=np.indices(v.g.shape); v.g[(v.g>0)&(Z<z-4)&((X+Y)%3==0)]=0
        if i>=2: v.g[(v.g>0)&(Z==z-5)]=tr
    if i>=2 and fam in("plate","scale","chain"):   # raised haute-piece guard on the neck side
        for zz in range(z,z+4+i): v.box(int(cx-side*5),int(cx-side*5),int(cy-6),int(cy+6),zz,zz,tr if i>=3 else m)
    if i>=3:
        sp=v.c(p['trim'] if i<5 else (0.12,0.09,0.09)); 
        for a in range(i-1): spike(v,(cx+side*(2+a*2),cy-3+a*3,z+5),(side*0.4,0,1),4+i,sp)
    if i>=4: v.put(cx+side*2,cy-9,z,v.c(p['gem'],1))
    return finish(v,fam,p,i,31+i),VS,(cx+0.5,cy+0.5,z+2)
def glove(fam,r,side):
    """vambrace + gauntlet along the forearm; ref forearm length 0.24 m (20 vox), radius 0.045 m. pivot = elbow (top)."""
    i=RARITIES.index(r); p=pal(fam,r); L=22; v=V(20,20,L+10); cx=cy=9.5
    m=v.c(p['metal'] if fam in("plate","scale","chain") else p['leather'] if fam in("leather",) else p['cloth']); tr=v.c(p['trim']); ed=v.c(p['edge']); lt=v.c(p['leather'])
    z0=4; zt=z0+L
    tube(v,cx,cy,z0+2,zt-6,3.4,3.4,m)   # vambrace (lower forearm)
    flare=2+i//2
    for z in range(z0+L-8,z0+L-5): tube(v,cx,cy,z,z,3.4+(z-(z0+L-8))*0.6+flare*0.4,3.4+(z-(z0+L-8))*0.6,m if fam!="cloth" else lt)   # cuff flare near elbow? (top of glove)
    # gauntlet hand plate at the wrist end (z low)
    v.box(int(cx)-3,int(cx)+3,int(cy)-4,int(cy)+4,1,z0+2,m if fam!="cloth" else lt)
    for z in (z0+6,z0+11): tube(v,cx,cy,z,z,3.5,3.5,tr if i>=2 else lt,1)
    if i>=1: v.box(int(cx)-3,int(cx)+3,int(cy)-5,int(cy)-5,2,3,ed)   # knuckles
    if i>=3: 
        for a in range(3): spike(v,(cx-2+a*2,cy-5,2),(0,-1,0),2+i//2,tr)
        for z in range(z0+3,zt-6,3): v.put(cx+side*4,cy,z,tr)
    if i>=4: v.put(cx,cy-4,z0+9,v.c(p['gem'],1))
    return finish(v,fam,p,i,41+i),VS,(cx+0.5,cy+0.5,zt)
def leg(fam,r,side):
    """cuisse on the thigh + knee cop; ref thigh 0.40 m (33 vox), radius 0.075 m. pivot = hip joint (top)."""
    i=RARITIES.index(r); p=pal(fam,r); L=36; v=V(26,26,L+6); cx=cy=12.5
    m=v.c(p['metal'] if fam in("plate","scale","chain") else p['leather'] if fam=="leather" else p['cloth']); tr=v.c(p['trim']); ed=v.c(p['edge'])
    zt=L+2; tube(v,cx,cy,4,zt-2,6.0,6.0,m)
    if fam in("plate","scale"): 
        for z in range(8,zt-2,6): tube(v,cx,cy,z,z,6.0,6.0,ed if i<2 else tr,2)
        v.ball(cx,cy-6,4,4.2+0.2*i,m,(1,0.7,1)); v.ball(cx,cy-8,4,1.6,tr if i>=2 else ed)   # knee cop
        if i>=3: spike(v,(cx,cy-10,4),(0,-1,0.3),3+i,tr)
    elif fam in("cloth","mystic"):
        tube(v,cx,cy,1,6,6.2,6.2,m); 
        if i>=2: tube(v,cx,cy,zt-4,zt-3,6.3,6.3,tr,2)
    else:
        if i>=1: 
            for z in (12,22): tube(v,cx,cy,z,z,6.1,6.1,v.c(p['leather']),2)
        v.ball(cx,cy-6,4,3.5,m,(1,0.7,1))
    # tasset over the hip at the top
    if fam!="cloth": v.box(int(cx)-6,int(cx)+6,int(cy)-8,int(cy)-7,zt-6,zt+1,m if i<4 else tr)
    return finish(v,fam,p,i,51+i),VS,(cx+0.5,cy+0.5,zt)
def boot_shin(fam,r,side):
    """greave on lower shin; ref shin 0.40 m (33 vox), radius 0.06 m. pivot = knee (top)"""
    i=RARITIES.index(r); p=pal(fam,r); L=34; v=V(24,24,L+6); cx=cy=11.5
    m=v.c(p['metal'] if fam in("plate","scale") else p['leather'] if fam in("leather","chain") else p['cloth']); tr=v.c(p['trim']); ed=v.c(p['edge'])
    zt=L+2; top=int(zt-L*0.45)
    tube(v,cx,cy,2,top,4.8,4.8,m); tube(v,cx,cy,top-2,top,5.6+0.3*i,5.6+0.3*i,ed if i<2 else tr,1)  # cuff
    if fam in("plate","scale") and i>=2: v.box(int(cx),int(cx)+1,int(cy)-7,int(cy)-7,4,top,tr)
    if i>=3: spike(v,(cx,cy-7,top-2),(0,-1,0.6),2+i,tr)
    return finish(v,fam,p,i,61+i),VS,(cx+0.5,cy+0.5,zt)
def boot_foot(fam,r,side):
    """sabaton/boot foot; ref foot length 0.24 m along -y, pivot = ankle. Foot points to -y (front)."""
    i=RARITIES.index(r); p=pal(fam,r); v=V(16,30,14); cx=7.5; cy=20
    m=v.c(p['metal'] if fam in("plate","scale") else p['leather'] if fam in("leather","chain") else p['cloth']); tr=v.c(p['trim']); ed=v.c(p['edge']); sole=v.c((0.12,0.08,0.06))
    v.box(int(cx)-4,int(cx)+4,cy-18,cy+4,1,7,m); v.box(int(cx)-4,int(cx)+4,cy-18,cy+4,0,0,sole)
    v.box(int(cx)-3,int(cx)+3,cy-20,cy-18,0,5,m)   # toe
    if fam in("plate","scale"):
        for y in range(cy-16,cy,4): v.box(int(cx)-4,int(cx)+4,y,y,7,8,ed if i<2 else tr)
    else: v.box(int(cx)-4,int(cx)+4,cy-6,cy-5,4,8,v.c(p['leather']) if fam!="leather" else tr)
    if i>=3: v.box(int(cx)-1,int(cx)+1,cy-22,cy-20,1,3,tr)
    if i>=4: v.box(int(cx)-4,int(cx)+4,cy+5,cy+5,1,4,tr)  # spur plate
    return finish(v,fam,p,i,71+i),VS,(cx+0.5,cy+0.5,8)
def belt(fam,r):
    """ref hips 0.36 w x 0.24 d; pivot = centre of belt"""
    i=RARITIES.index(r); p=pal(fam,r); v=V(40,30,14); cx,cy=19.5,14.5; z=6
    lt=v.c(p['leather'] if fam!="mystic" else p['cloth']); tr=v.c(p['trim']); ed=v.c(p['edge']); m=v.c(p['metal'])
    X,Y=np.indices(v.g.shape[:2]); o=((X-cx)/17)**2+((Y-cy)/12)**2; ii=((X-cx)/15)**2+((Y-cy)/10)**2
    for zz in range(z-1,z+2): v.g[:,:,zz][(o<=1)&(ii>1)]=lt
    v.box(int(cx)-2,int(cx)+2,int(cy-12)-1,int(cy-12),z-2,z+2,tr if i>=2 else ed)   # buckle
    if i>=1: 
        for s in (-1,1): v.box(int(cx+s*13)-2,int(cx+s*13)+2,int(cy-8),int(cy-5),z-5,z-1,lt)  # pouches
    if fam in("plate","scale","chain"):
        for s in (-1,1): v.box(int(cx+s*9)-3,int(cx+s*9)+3,int(cy-11)-1,int(cy-11),z-6,z-2,m)   # faulds
    if i>=3: v.ball(cx,cy-13,z,1.6,v.c(p['gem'],1))
    if i>=4: 
        for s in (-1,1): v.box(int(cx+s*5),int(cx+s*5),int(cy-12)-1,int(cy-12)-1,z,z,tr)
    if fam in("cloth","mystic"): v.box(int(cx)+3,int(cx)+4,int(cy-12),int(cy-11),z-9,z-1,lt)   # sash tail
    return finish(v,fam,p,i,81+i),VS,(cx+0.5,cy+0.5,z)
def cloak(fam,r):
    """rigid cloak on the chest bone. ref width 0.46 m, length 0.95 m from shoulders; pivot = top centre of the back."""
    i=RARITIES.index(r); p=pal(fam,r); H=78; v=V(52,22,H+8); cx=25.5; cy=6
    c=v.c(p['cloth']); c2=v.c(tuple(x*0.8 for x in p['cloth'])); tr=v.c(p['trim']); fur=v.c(p['fur']); e=v.c(p['edge'],1)
    zt=H+4
    for z in range(2,zt+1):
        u=(zt-z)/H; w=13+u*9+i*0.6; back=int(cy+2+u*7)
        for x in range(int(cx-w),int(cx+w)+1):
            dx=(x-cx)/w; y=int(back-(1-dx*dx)*-2+abs(dx)*-6)
            col=c2 if (x%6==0) else c
            v.put(x,y,z,col); v.put(x,y+1,z,col)
        if z<4+(3 if i>=3 else 0): v.g[:,:,z][v.g[:,:,z]>0]=tr if i>=2 else c2   # hem trim
    X,Y,Z=np.indices(v.g.shape)
    v.g[(v.g>0)&(Z<14)&(((X*13)%7)<1+(5-i)%3)&(i<=1)]=0   # ragged hem on poor cloaks
    # collar
    if fam=="plate" or i>=3:
        for z in range(zt-4,zt+3): v.box(int(cx-14),int(cx+14),0,int(cy+4),z,z,fur if fam in("plate","scale","chain","leather") else tr)
        v.g[(Z>=zt-4)&(np.abs(X-cx)<9)&(Y<cy)]=0
    if fam in("leather","cloth","mystic"):   # hood folded on the back
        v.ball(cx,cy+7,zt-6,6.5,c,(1.2,0.7,0.9))
    for s in (-1,1): v.ball(cx+s*13,1,zt-2,1.8,tr if i>=1 else c2)  # clasps
    if i>=3: 
        for z in range(10,zt-10,8): v.put(cx,int(cy+2+(zt-z)/H*7)+2,z,tr)
    if i>=4: v.g[(v.g==c)&(np.abs(X-cx)<2)&(Z>20)&(Z<50)&(Z%3==0)]=e   # embroidered rune line
    if i==5: v.g[(v.g==c)&(Z<8)]=e
    return finish(v,fam,p,i,91+i),VS,(cx+0.5,1,zt)
PARTS={"helmet":[("helmet",helmet,None)],"chest":[("chest",chest,None)],
 "shoulders":[("shoulder_L",shoulder,1)],"gloves":[("glove_L",glove,1)],
 "legs":[("leg_L",leg,1)],"boots":[("boot_shin_L",boot_shin,1),("boot_foot_L",boot_foot,1)],
 "belt":[("belt",belt,None)],"cloak":[("cloak",cloak,None)]}
def build(slot,fam,r):
    out=[]
    for part,fn,side in PARTS[slot]:
        v,vs,piv=fn(fam,r) if side is None else fn(fam,r,side)
        out.append((part,v,vs,piv))
    return out
