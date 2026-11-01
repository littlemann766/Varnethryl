# Equipment v1 weapons: own meshes per family per rarity + 7 named weapons. Pivot conventions match gmodels (phase 2) so gear_attach.json holds.
import math,numpy as np,sys,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from vox import V
import gmodels as G, armor3d as A
from edata import RARITIES
VS=G.VS_W
def P(r): 
    p=dict(A.pal("plate",r)); i=RARITIES.index(r)
    p["wood"]=[(0.40,0.26,0.14),(0.38,0.25,0.13),(0.26,0.16,0.09),(0.20,0.11,0.07),(0.16,0.09,0.06),(0.10,0.06,0.05)][i]
    return p
def notch(v,p,rng,n):
    e=[k for k,q in enumerate(v.pal) if q and q[0]==p['edge']]
    idx=np.argwhere(np.isin(v.g,e))
    for q in idx[rng.random(len(idx))<n]: v.g[tuple(q)]=0
def runes(v,cells,p,col=None):
    c=v.c(col or p['edge'],1)
    for k,(x,y,z) in enumerate(cells):
        if k%3!=2: v.put(x,y,z,c)
def finish(v,p,i,seed):
    rng=np.random.default_rng(seed)
    if i<=1: notch(v,p,rng,0.10 if i==0 else 0.04)
    if i>=4: A.filigree(v,p)
    G.wear(v,p,seed)
    if i==5: A.molten(v,p,seed)
    return v
def blade(v,cx,cy,z0,L,W,b,e,taper=6,wave=0,fuller=None):
    cells=[]
    for z in range(z0,z0+L):
        k=z-z0; w=W if k<L-taper else max(0,round(W*(L-k)/taper))
        off=int(round(wave*math.sin(k*0.35))) if wave else 0
        for x in range(-w,w+1):
            th=1 if abs(x)<w else 0
            v.box(cx+x+off,cx+x+off,cy-th,cy+th,z,z,b)
        v.put(cx-w-1+off,cy,z,e); v.put(cx+w+1+off,cy,z,e)
        if fuller is not None and k<L*0.7: v.put(cx+off,cy-1,z,fuller); v.put(cx+off,cy+1,z,fuller); cells.append((cx+off,cy-2,z))
    return cells
def guardbar(v,cx,cy,gz,g,col,i,droop=0):
    for x in range(-g,g+1):
        dz=int(droop*(abs(x)/max(1,g))**2)
        v.box(cx+x,cx+x,cy-1,cy+1,gz-dz,gz+1-dz,col)
    if i>=3:
        for s in (-1,1): v.ball(cx+s*g,cy,gz-droop,1.6,col)
def sword_like(p,i,L,W,grip,g,kind="sword",named=None):
    n=L+grip+14; v=V(2*g+11,11,n); cx=g+5; cy=5
    tr=v.c(p['trim']); b=v.c(p['metal']); e=v.c(p['edge'],p['glow']); fu=v.c(G.TIER[1]['dent'] if i<2 else p['dent'])
    G._grip(v,cx,cy,2,grip+1,p)
    v.box(cx-1,cx+1,cy-1,cy+1,0,1,tr)            # pommel
    if i>=2: v.ball(cx,cy,0.5,2.2,tr)
    if i>=3: G.M  # noop
    gz=grip+2
    guardbar(v,cx,cy,gz,g,tr,i,droop=(2 if i>=3 else 0))
    if kind=="rapier":
        for a in range(0,13): t=math.pi*a/12; v.put(cx+5*math.cos(t),cy-2,gz-1-4*math.sin(t)*0.6+2,tr)
        if i>=2:
            for a in range(0,13): t=math.pi*a/12; v.put(cx+4*math.cos(t),cy+2,gz-1-3*math.sin(t)*0.6+2,tr)
    if i>=2: v.box(cx-W-1,cx+W+1,cy-1,cy+1,gz+2,gz+3,b)   # ricasso block
    cells=blade(v,cx,cy,gz+4,L,W,b,e,taper=6 if kind!="dagger" else 5,wave=(1 if i==5 and kind=="greatsword" else 0),fuller=fu if kind!="rapier" else None)
    if i>=3 and kind in("sword","greatsword"):  # parrying lugs
        for s in (-1,1): v.box(cx+s*(W+2),cx+s*(W+2),cy,cy,gz+8,gz+9,tr)
    if i>=4: runes(v,cells[2:int(len(cells)*0.8)],p)
    if i>=1 and p.get('gem'): v.box(cx,cx,cy-2,cy-2,gz,gz+1,v.c(p['gem'],1 if i>=3 else 0))
    return v,(cx+0.5,cy+0.5,(2+grip)/2)
def sword(p,i): return sword_like(p,i,42+2*i,2+(1 if i>=3 else 0),9,6+i)
def rapier(p,i): return sword_like(p,i,52+i,0,8,4+i//2,"rapier")
def greatsword(p,i): return sword_like(p,i,60+3*i,3+(1 if i>=2 else 0),16,9+i)
def dagger(p,i): return sword_like(p,i,15+i,2,6,3+i//2,"dagger")
def axe(p,i,double=None):
    L=52; head=13+i; v=V(44,11,L+8); cx=22; cy=5; h=v.c(p['wood']); m=v.c(p['metal']); e=v.c(p['edge'],p['glow']); tr=v.c(p['trim'])
    v.box(cx-1,cx,cy-1,cy,0,L,h); G._grip(v,cx,cy,2,12,p)
    for z in range(16,L-10,6): v.box(cx-1,cx,cy-1,cy,z,z,tr if i>=2 else h)  # langets / bands
    sides=[1,-1] if (double if double is not None else i>=4) else [1]
    for s in sides:
        hh=head if s==1 else head-4
        for k in range(hh):
            top=L-3+int(k*0.35); bot=L-10-int(k*0.75)-(int(k*0.5) if k>hh*0.4 else 0)
            x=cx+s*(2+k); v.box(x,x,cy-(1 if k<hh-3 else 0),cy+(1 if k<hh-3 else 0),bot,top,m)
        x=cx+s*(2+hh); v.box(x,x,cy,cy,L-10-int(hh*0.75)-int(hh*0.5),L-3+int(hh*0.35),e)
    v.box(cx-2,cx+1,cy-1,cy+1,L-11,L-1,tr)
    if i>=3:  # top spike + back spike
        for z in range(L,L+6-(0 if i>=4 else 2)): v.box(cx-1,cx,cy,cy,z,z,m)
        if len(sides)==1:
            for k in range(4+i): v.box(cx-2-k,cx-2-k,cy,cy,L-6+k//2-1,L-6+k//2,m)
    if i>=4: runes(v,[(cx+6+k,cy-2,L-6) for k in range(head-6)],p)
    return v,(cx,cy,7)
def mace(p,i):
    L=44; v=V(23,23,L+16); cx=cy=11; h=v.c(p['wood']); m=v.c(p['metal']); e=v.c(p['edge'],p['glow']); tr=v.c(p['trim'])
    v.box(cx-1,cx,cy-1,cy,0,L,v.c(p['metal'] if i>=2 else p['wood'])); G._grip(v,cx,cy,2,12,p)
    v.ball(cx-0.5,cy-0.5,L+5,3.5+0.3*i,m)
    fl=6+(2 if i>=3 else 0)
    for a in range(fl):
        t=a*2*math.pi/fl
        for r in range(3,8+i//2):
            for z in range(L,L+10): v.put(cx-0.5+r*math.cos(t),cy-0.5+r*math.sin(t),z if r<7 or abs(z-(L+5))<4 else -9,e if r>=6+i//2 else m)
    v.box(cx-1,cx,cy-1,cy,L+10,L+12+(3 if i>=3 else 0),e)
    v.box(cx-2,cx+1,cy-2,cy+1,L-2,L-1,tr)
    return v,(cx,cy,7)
def spear(p,i):
    L=118; v=V(19,9,L+26); cx=9; cy=4; h=v.c(p['wood']); m=v.c(p['metal']); e=v.c(p['edge'],p['glow']); tr=v.c(p['trim'])
    v.box(cx,cx+1,cy,cy+1,0,L,h); v.box(cx-1,cx+2,cy-1,cy+2,L-4,L+1,tr)
    hl=17+2*i
    for z in range(L+2,L+2+hl):
        u=(z-L-1)/hl; w=max(0,int(3.6*math.sin(math.pi*min(1,u*1.25))+0.5))
        v.box(cx-w,cx+w+1,cy,cy+1,z,z,m); v.put(cx-w-1,cy,z,e); v.put(cx+w+2,cy,z,e)
    if i>=2:  # winged lugs
        for s in (-1,1): v.box(cx+(s*4 if s>0 else -3),cx+(s*6 if s>0 else -5),cy,cy+1,L-1,L,tr if i>=3 else m)
    if i>=3: v.box(cx-1,cx+2,cy-1,cy+2,4,6,tr)  # butt spike cap
    if i>=4: runes(v,[(cx,cy-1,z) for z in range(L+4,L+hl-4)],p)
    G._grip(v,cx,cy,36,48,p,False); return v,(cx+0.5,cy+0.5,42)
def staff(p,i,orb=None):
    L=104; v=V(21,21,L+22); cx=cy=10; h=v.c(p['wood']); t=v.c(p['trim'])
    for z in range(0,L+1):
        o=int(round(0.8*math.sin(z*0.12))) if i<=1 else 0
        v.box(cx+o,cx+1+o,cy,cy+1,z,z,h)
    for z in (20,48,L-2)+((34,62,76) if i>=3 else ()): v.box(cx-1,cx+2,cy-1,cy+2,z,z+1,t)
    prongs=6+2*i
    for a in range(prongs):
        ang=a*2*math.pi/prongs; v.line((cx+0.5,cy+0.5,L),(cx+0.5+(5+i*0.5)*math.cos(ang),cy+0.5+(5+i*0.5)*math.sin(ang),L+9+i),t)
    gc=orb or p['gem'] or (0.7,0.75,0.8)
    v.ball(cx+0.5,cy+0.5,L+9+i*0.6,3+0.3*i,v.c(gc,1 if i>=2 or orb else 0))
    if i>=4:
        for a in range(4): ang=a*math.pi/2+0.4; v.line((cx+0.5,cy+0.5,L+3),(cx+0.5+9*math.cos(ang),cy+0.5+9*math.sin(ang),L+15),t)
    return v,(cx+1,cy+1,46)
def scythe(p,i,glow=None):
    v0,_=staff(dict(p,gem=None),min(i,2)); v0.g[:,:,-20:]=0
    L=104; big=V(70,21,L+22); big.pal=v0.pal; big.g[0:21,:,:]=v0.g; v=big; cx=10
    m=v.c(p['metal']); e=v.c(glow or p['edge'],1 if glow else p['glow']); tr=v.c(p['trim'])
    v.box(cx-1,cx+2,8,12,L-3,L+1,tr)
    n=44+3*i
    for k in range(n):
        z=L+2-int(9*math.sin(math.pi*k/(n+6)))+int(k*0.1); x=cx+2+k
        th=max(2,7+i//2-k//9); v.box(x,x,10,10,z-th,z,m); v.box(x,x,9,11,z-th//2,z-th//2,m); v.put(x,10,z-th-1,e)
    if i>=3:
        for k in range(6): v.box(cx-1-k,cx-1-k,10,10,L-2+k//2,L-1+k//2,m)
    return v,(cx+1,11,46)
def wrap_old(fn,p,i):
    v,vs,pv=fn(p); 
    return v,pv
def bow(p,i):
    v,vs,pv=G.bow(p)
    if i>=2: 
        for z in (8,v.g.shape[2]-10): v.box(4,8,3,4,z,z+1,v.c(p['trim']))
    if i>=3:
        for z,x in ((1,2),(v.g.shape[2]-3,2)): v.box(x,x+3,3,4,z,z+1,v.c(p['trim']))
        v.box(16,16,1,1,30,60,v.c(p['edge'],1))
    return v,pv
def crossbow(p,i):
    v,vs,pv=G.crossbow(p)
    if i>=2: v.box(21,25,6,8,11,11,v.c(p['trim']))
    if i>=3:
        for s in (-1,1): v.box(23+s*20,23+s*20,9,12,9,11,v.c(p['trim']))
    if i>=4: v.box(23,23,12,40,11,11,v.c(p['edge'],1))
    return v,pv
def lute(p,i):
    v,vs,pv=G.lute(p)
    if i>=3: v.ball(12,5,12,10.6,0); v,vs,pv=G.lute(p); v.box(4,20,1,1,2,3,v.c(p['trim']))
    return v,pv
def whip(p,i):
    v,vs,pv=G.whip(p)
    if i>=3: v.box(14,16,14,16,15,17,v.c(p['trim']))
    return v,pv
def knuckles(p,i):
    v=V(14,12,18); m=v.c(p['metal']); w=v.c(p['leather']); e=v.c(p['edge'],p['glow']); tr=v.c(p['trim'])
    v.box(2,11,3,8,0,14,w); v.box(2,11,1,2,2,12,m)
    for z in (3,6,9,12): v.box(1,12,0,2,z,z,e if i>=2 else m)
    if i>=3:
        for z in (3,6,9,12): v.box(6,7,0,0,z,z,tr)
    if i>=4:
        for z in (3,9): v.put(6,0,z,v.c(p['gem'],1))
    return v,(6.5,6,7)
FAM={"sword":sword,"rapier":rapier,"greatsword":greatsword,"dagger":dagger,"axe":axe,"mace":mace,"spear":spear,"staff":staff,"scythe":scythe,"bow":bow,"crossbow":crossbow,"lute":lute,"whip":whip,"knuckles":knuckles}
def build(fam,r):
    i=RARITIES.index(r); p=P(r); v,pv=FAM[fam](p,i); return finish(v,p,i,100+i*7+len(fam)),VS,pv
# ---------------- named weapons ----------------
def named(iid):
    i=4
    if iid=="worldbreaker":
        p=dict(P("masterwork"),metal=(0.10,0.09,0.09),edge=(1.0,0.45,0.08),trim=(0.30,0.18,0.12),gem=(1.0,0.5,0.1))
        v,pv=sword_like(p,5,74,5,18,14,"greatsword"); X,Y,Z=np.indices(v.g.shape)
        e=v.c((1.0,0.5,0.1),1); rng=np.random.default_rng(1); m=[k for k,q in enumerate(v.pal) if q and q[0]==p['metal']]
        idx=np.argwhere(np.isin(v.g,m)&(Z>22))
        for q in idx[rng.random(len(idx))<0.06]: 
            for k in range(4): 
                t=q+np.array([rng.integers(-1,2),0,k])
                if all(0<=t[j]<v.g.shape[j] for j in range(3)) and v.g[tuple(t)] in m: v.g[tuple(t)]=e
        for z in range(26,90,9): v.box(int(pv[0])-7,int(pv[0])-6,4,6,z,z+3,v.c(p['metal']))   # stepped spine teeth
        return finish(v,p,5,1),VS,pv
    if iid=="winters_end":
        p=dict(P("legendary"),metal=(0.70,0.78,0.86),edge=(0.55,0.90,1.0),trim=(0.85,0.90,0.96),gem=(0.5,0.9,1.0),glow=1)
        v,pv=sword_like(p,4,50,2,10,10,"sword"); cx=int(pv[0])
        c=v.c((0.65,0.92,1.0),1)
        for s in (-1,1):
            for k in range(5): v.box(cx+s*(10+k//2),cx+s*(10+k//2),5,5,12+k*2,13+k*2,c)   # ice-crystal quillons
        return finish(v,p,4,2),VS,pv
    if iid=="soulrender":
        p=dict(P("legendary"),wood=(0.80,0.76,0.66),metal=(0.16,0.17,0.15),edge=(0.45,1.0,0.55),trim=(0.40,0.42,0.36),glow=1,gem=(0.4,1.0,0.5))
        v,pv=scythe(p,5,glow=(0.45,1.0,0.55)); v.ball(10,10,104,3.5,v.c((0.86,0.84,0.76)))  # skull
        v.put(9,7,105,v.c((0.4,1.0,0.5),1)); v.put(12,7,105,v.c((0.4,1.0,0.5),1))
        return finish(v,p,4,3),VS,pv
    if iid=="dawnbringer":
        p=dict(P("legendary"),metal=(0.92,0.90,0.84),edge=(1.0,0.88,0.5),trim=(1.0,0.80,0.30),gem=(1.0,0.95,0.7),glow=1)
        v,pv=sword_like(p,4,48,3,10,9,"sword"); cx=int(pv[0]); gz=12
        g=v.c((1.0,0.80,0.30)); gl=v.c((1.0,0.92,0.6),1)
        for a in range(16):
            t=a*2*math.pi/16
            for r in range(3,7 if a%2 else 9): v.put(cx+r*math.cos(t),5,gz+r*math.sin(t),gl if r>=6 else g)  # sun disc
        return finish(v,p,4,4),VS,pv
    if iid=="voidfang":
        p=dict(P("legendary"),metal=(0.10,0.06,0.14),edge=(0.70,0.30,1.0),trim=(0.25,0.12,0.30),gem=(0.8,0.3,1.0),glow=1)
        v,pv=sword_like(p,5,64,4,16,11,"greatsword"); cx=int(pv[0])
        for z in range(30,84,7):   # fang serrations
            for s in (-1,1): v.box(cx+s*7,cx+s*8,5,5,z,z+1,v.c(p['edge'],1))
        return finish(v,p,4,5),VS,pv
    if iid=="serpents_kiss":
        p=dict(P("legendary"),metal=(0.20,0.28,0.18),edge=(0.55,1.0,0.30),trim=(0.70,0.62,0.30),gem=(0.4,1.0,0.3),glow=1)
        n=40; v=V(17,11,n); cx=8; cy=5; tr=v.c(p['trim']); b=v.c(p['metal']); e=v.c(p['edge'],1)
        G._grip(v,cx,cy,2,7,p); v.ball(cx,cy,1,2,tr)
        for k in range(8): v.put(cx-4+k,cy,9+int(1.5*math.sin(k*0.9)),tr)   # serpent-coil guard
        v.ball(cx+4,cy-1,10,1.6,tr); v.put(cx+5,cy-2,10,e)                 # snake head
        blade(v,cx,cy,11,24,2,b,e,taper=6,wave=1)
        return finish(v,p,4,6),VS,(cx+0.5,cy+0.5,4.5)
    if iid=="eternal_cinder":
        p=dict(P("legendary"),wood=(0.18,0.10,0.07),trim=(0.85,0.55,0.20),gem=(1.0,0.45,0.10),glow=1)
        v,pv=staff(p,5,orb=(1.0,0.5,0.1)); X,Y,Z=np.indices(v.g.shape); f=v.c((1.0,0.30,0.05),1); f2=v.c((1.0,0.75,0.2),1)
        for a in range(5):   # feather flames
            t=a*2*math.pi/5
            for k in range(10): v.put(10.5+(3+k*0.4)*math.cos(t),10.5+(3+k*0.4)*math.sin(t),114+k,f if k<6 else f2)
        return finish(v,p,4,7),VS,pv
