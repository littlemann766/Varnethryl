# Gear voxel models. Grid: x lateral, y depth (-y = front = glTF +Z), z up (= glTF +Y).
# Each fn(p) -> (V, vs, pivot_voxel_xyz). p = tier palette dict.
import math, numpy as np
from vox import V
TIER={
 1:dict(metal=(0.44,0.44,0.47),edge=(0.62,0.62,0.64),trim=(0.34,0.24,0.15),wood=(0.40,0.26,0.14),leather=(0.33,0.20,0.11),cloth=(0.40,0.33,0.24),fur=(0.42,0.34,0.26),gem=None,glow=0,accent=(0.5,0.4,0.3),dent=(0.30,0.29,0.30),scratch=(0.66,0.66,0.68),rust=(0.42,0.25,0.14)),
 2:dict(metal=(0.22,0.23,0.26),edge=(0.70,0.72,0.76),trim=(0.72,0.54,0.24),wood=(0.30,0.18,0.10),leather=(0.22,0.13,0.08),cloth=(0.45,0.08,0.08),fur=(0.30,0.27,0.25),gem=(0.85,0.12,0.10),glow=0,accent=(0.72,0.54,0.24),dent=(0.13,0.13,0.15),scratch=(0.52,0.53,0.56),rust=(0.28,0.18,0.12)),
 3:dict(metal=(0.28,0.30,0.34),edge=(0.55,0.90,1.00),trim=(0.98,0.76,0.26),wood=(0.18,0.10,0.06),leather=(0.14,0.08,0.06),cloth=(0.40,0.06,0.10),fur=(0.80,0.78,0.74),gem=(0.35,0.85,1.0),glow=1,accent=(0.98,0.76,0.26),dent=(0.17,0.18,0.21),scratch=(0.62,0.64,0.68),rust=(0.2,0.2,0.22)),
}
def wear(v,p,seed=1):
    """battle-worn pass: dents (dark), scratches (light streaks), a little rust on T1"""
    rng=np.random.default_rng(seed); mi=[i for i,q in enumerate(v.pal) if q and q[0]==p['metal'] and not q[1]]
    if not mi: return v
    idx=np.argwhere(np.isin(v.g,mi)); 
    if len(idx)==0: return v
    d=v.c(p['dent']); sc=v.c(p['scratch']); r=v.c(p['rust'])
    for q in idx[rng.random(len(idx))<0.05]: v.g[tuple(q)]=d
    for q in idx[rng.random(len(idx))<0.012]:
        for k in range(4):
            t=q+np.array([k,0,-k]); 
            if all(0<=t[j]<v.g.shape[j] for j in range(3)) and v.g[tuple(t)] in mi: v.g[tuple(t)]=sc
    if p['metal'][0]>0.4:
        for q in idx[rng.random(len(idx))<0.02]: v.g[tuple(q)]=r
    return v
PAULDRONS=True
def M(n,m=None,k=None): return V(n,m,k)
# ---------- weapons (blade along +z, pivot = grip centre) ----------
VS_W=0.015
def _grip(v,cx,cy,z0,z1,p,wrap=True):
    g=v.c(p['leather']); t=v.c(p['trim'])
    v.box(cx-1,cx+1,cy-1,cy+1,z0,z1,g)
    if wrap:
        for z in range(z0,z1+1,3): v.box(cx-1,cx+1,cy-1,cy+1,z,z,t)
def _gem(v,x,y,z,p):
    if p['gem']: v.box(x,x,y-2,y+2,z,z,v.c(p['gem'],1))
def sword(p,L=44,W=2,grip=9,guard=7,rap=False):
    n=L+grip+8; v=M(2*guard+5,9,n); cx=guard+2; cy=4
    _grip(v,cx,cy,2,grip+1,p); v.box(cx-1,cx+1,cy-1,cy+1,0,1,v.c(p['trim']))  # pommel
    gz=grip+2; v.box(cx-guard,cx+guard,cy-1,cy+1,gz,gz+1,v.c(p['trim']))
    if rap:
        for a in range(0,13): t=math.pi*a/12; v.put(cx+5*math.cos(t),cy-2,gz-1-4*math.sin(t)*0.6+2,v.c(p['trim']))
    b=v.c(p['metal'],0); e=v.c(p['edge'],p['glow'])
    for z in range(gz+2,gz+2+L):
        w=W if z<gz+2+L-6 else max(0,int(W*(gz+2+L-z)/6))
        v.box(cx-w,cx+w,cy,cy,z,z,b); v.put(cx-w-1,cy,z,e); v.put(cx+w+1,cy,z,e)
    v.box(cx,cx,cy,cy,gz+2,gz+2+L,v.c(p['edge']))  # fuller
    _gem(v,cx,cy,gz,p)
    return v,VS_W,(cx+0.5,cy+0.5,(2+grip)/2)
def rapier(p): return sword(p,L=54,W=0,grip=8,guard=5,rap=True)
def greatsword(p): return sword(p,L=66,W=3,grip=16,guard=11)
def dagger(p): return sword(p,L=16,W=2,grip=6,guard=4)
def axe(p,L=52,head=14,beard=True,double=False,haft=True):
    v=M(36,9,L+4); cx=18; cy=4; h=v.c(p['wood']); m=v.c(p['metal']); e=v.c(p['edge'],p['glow'])
    v.box(cx-1,cx,cy-1,cy,0,L,h); _grip(v,cx,cy,2,12,p)
    for s in ([1,-1] if double else [1]):
        for i in range(head):
            hgt=4+int(i*0.6)+ (int(i*0.4) if beard else 0)
            x=cx+s*(2+i); v.box(min(x,x),max(x,x),cy,cy,L-6-hgt+ (4 if beard else 0),L-4+int(i*0.25),m)
        x=cx+s*(2+head); v.box(x,x,cy,cy,L-8-int(head*0.6)-4,L-1,e)
    v.box(cx-2,cx+1,cy-1,cy+1,L-8,L-2,v.c(p['trim']))
    _gem(v,cx,cy,L-5,p)
    return v,VS_W,(cx,cy,7)
def mace(p):
    L=44; v=M(17,17,L+12); cx=cy=8; h=v.c(p['wood']); m=v.c(p['metal']); e=v.c(p['edge'],p['glow'])
    v.box(cx-1,cx,cy-1,cy,0,L,h); _grip(v,cx,cy,2,12,p)
    v.ball(cx-0.5,cy-0.5,L+4,5,m)
    for a in range(6):
        t=a*math.pi/3
        for r in range(4,8): v.put(cx-0.5+r*math.cos(t),cy-0.5+r*math.sin(t),L+4,e)
    v.box(cx-1,cx,cy-1,cy,L+9,L+11,e); return v,VS_W,(cx,cy,7)
def spear(p):
    L=118; v=M(11,7,L+18); cx=5; cy=3; h=v.c(p['wood']); m=v.c(p['metal']); e=v.c(p['edge'],p['glow'])
    v.box(cx,cx+1,cy,cy+1,0,L,h); v.box(cx-1,cx+2,cy-1,cy+2,L-2,L+1,v.c(p["trim"]))
    for z in range(L+2,L+17):
        w=max(0,int(3*math.sin(math.pi*(z-L-1)/17)+0.5)); v.box(cx-w,cx+w,cy,cy,z,z,m); v.put(cx,cy,z,e)
    _grip(v,cx,cy,36,48,p,False); return v,VS_W,(cx+0.5,cy+0.5,42)
def staff(p):
    L=104; v=M(15,15,L+16); cx=cy=7; h=v.c(p['wood']); t=v.c(p['trim'])
    v.box(cx,cx+1,cy,cy+1,0,L,h)
    for z in (20,48,L-2): v.box(cx-1,cx+2,cy-1,cy+2,z,z+1,t)
    for a in range(10):
        ang=a*2*math.pi/10; v.line((cx+0.5,cy+0.5,L),(cx+0.5+5*math.cos(ang),cy+0.5+5*math.sin(ang),L+8),t)
    v.ball(cx+0.5,cy+0.5,L+8,3,v.c(p['gem'] or (0.7,0.75,0.8),1))
    return v,VS_W,(cx+1,cy+1,46)
def scythe(p):
    v,vs,pv=staff(dict(p,gem=None)); v.g[:,:, -16:]=0
    L=104; m=v.c(p['metal']); e=v.c(p['edge'],p['glow']); cx=7
    big=M(60,15,L+16); big.pal=v.pal; big.g[0:15,:,:]=v.g; v=big
    v.box(cx-1,cx+2,6,8,L-3,L+1,v.c(p['trim']))
    for i in range(44):
        z=L+2-int(8*math.sin(math.pi*i/50))+int(i*0.1); x=cx+2+i
        th=max(2,6-i//10); v.box(x,x,7,7,z-th,z,m); v.put(x,7,z-th-1,e)
    return v,vs,(cx+1,8,46)
def bow(p):
    H=92; v=M(26,7,H+2); cy=3; w=v.c(p['wood']); s=v.c((0.9,0.88,0.8)); g=v.c(p['leather']); t=v.c(p['trim'])
    for z in range(H+1):
        u=(z-H/2)/(H/2); x=4+int(round(12*(1-u*u)))
        v.box(x,x+1,cy,cy+1,z,z,w)
    v.box(3,3,cy,cy,1,H-1,s); v.box(15,17,cy-1,cy+2,H//2-5,H//2+5,g); v.box(15,17,cy-1,cy+2,H//2-6,H//2-6,t); v.box(15,17,cy-1,cy+2,H//2+6,H//2+6,t)
    if p['glow']: v.put(16,cy-1,H//2,v.c(p['gem'],1))
    return v,VS_W,(16.5,cy+0.5,H/2)
def crossbow(p):
    # stock along -y (front), prod along x; grip pivot under stock rear
    v=M(46,52,14); cx=23; st=v.c(p['wood']); m=v.c(p['metal']); s=v.c((0.9,0.88,0.8)); t=v.c(p['trim'])
    v.box(cx-1,cx+1,6,50,8,10,st); v.box(cx-1,cx+1,40,50,4,8,st)  # stock + butt
    v.box(cx-1,cx+1,30,33,2,8,v.c(p['leather']))  # grip
    for i in range(-20,21):
        y=6+int(abs(i)**1.6/12); v.box(cx+i,cx+i,y,y+1,9,10,m)
    v.line((cx-20,6+int(20**1.6/12)+1,10),(cx,26,11),s); v.line((cx+20,6+int(20**1.6/12)+1,10),(cx,26,11),s)
    v.box(cx-1,cx+1,4,5,8,10,t); _gem(v,cx,24,11,p)
    return v,VS_W,(cx+0.5,31.5,5)
def lute(p):
    v=M(24,10,60); cx=12; cy=5; b=v.c(p['wood']); f=v.c(tuple(min(1,c+0.25) for c in p['wood'])); t=v.c(p['trim'])
    v.ball(cx,cy,12,10,b,(1,0.45,1.15)); v.box(cx-8,cx+8,cy-4,cy-4,4,22,0)
    X,Z=np.indices((24,60))
    for x in range(24):
        for z in range(60):
            if ((x-cx)/1)**2+((z-12)/1.15)**2<=81: v.g[x,cy-4,z]=f
    v.ball(cx,cy-4,15,2,v.c((0.1,0.07,0.05)))
    v.box(cx-1,cx+1,cy-3,cy,22,50,b); v.box(cx-2,cx+2,cy-3,cy+1,50,57,t)
    for x in (cx-1,cx,cx+1): v.line((x,cy-5,6),(x,cy-4,52),v.c((0.9,0.88,0.8)))
    _gem(v,cx,cy,54,p); return v,VS_W,(cx,cy,30)
def whip(p):
    v=M(30,30,30); cx=15; cy=15; g=v.c(p['leather']); t=v.c(p['trim']); e=v.c(p['edge'] if p['glow'] else p['leather'],p['glow'])
    _grip(v,cx,cy,0,14,p); v.box(cx-1,cx+1,cy-1,cy+1,15,16,t)
    for i in range(240):
        a=i*0.11; r=9+2*math.sin(i*0.05); v.put(cx+r*math.cos(a),cy+r*math.sin(a),17-i*0.06 if i<200 else 5,g if i%9 else e)
    return v,VS_W,(cx,cy,7)
def knuckles(p):
    v=M(12,10,16); m=v.c(p['metal']); w=v.c(p['leather']); e=v.c(p['edge'],p['glow'])
    v.box(1,10,2,7,0,13,w); v.box(1,10,0,1,2,11,m)
    for z in (3,6,9): v.box(0,11,0,1,z,z,e)
    return v,VS_W,(5.5,5,7)
WEAPON={"sword":sword,"rapier":rapier,"greatsword":greatsword,"dagger":dagger,"axe":axe,"mace":mace,"spear":spear,"staff":staff,
        "scythe":scythe,"bow":bow,"crossbow":crossbow,"lute":lute,"whip":whip,"knuckles":knuckles}
# ---------- helmets (ref inner head 0.33w x 0.355d; pivot = shell centre) ----------
VS_A=0.012
def helmet(p,kind,t):
    W,D,H=26,28,30; pad=3; v=M(W+2*pad+30,D+2*pad+22,H+34); cx=v.g.shape[0]/2-0.5; cy=v.g.shape[1]/2-0.5+4
    m=v.c(p['metal']); tr=v.c(p['trim']); cl=v.c(p['cloth']); lt=v.c(p['leather']); e=v.c(p['edge'],p['glow']); ed=v.c(p['edge'])
    mail=v.c((0.36,0.37,0.40) if t>1 else (0.48,0.48,0.5)); fur=v.c(p['fur']); dk=v.c((0.04,0.04,0.05))
    X,Y,Z=np.indices(v.g.shape); zc=12
    rx,ry,rz=W/2+pad,D/2+pad,H*0.8
    def ell(ax,ay,az,zc_=zc,cy_=cy): return ((X-cx)/ax)**2+((Y-cy_)/ay)**2+((Z-zc_)/az)**2
    front=Y<cy-ry*0.35
    eyez=zc+rz*0.33
    def slit(z0,h,w,glow=False):
        msk=front&(np.abs(Z-z0)<=h)&(np.abs(X-cx)<w)&(np.abs(X-cx)>1.2)&(v.g>0)
        v.g[msk]=e if glow else dk
    def breaths(side):
        for z in range(int(zc-9),int(zc+1),3):
            for k in range(3):
                x=int(cx+side*(4+k*3)); col=v.g[x,:,z]
                ys=np.where(col>0)[0]
                if len(ys): v.g[x,ys[0],z]=dk
    if kind=="heavy":
        if t in (1,3):   # great helm: flat-topped barrel, full face
            cyl=(((X-cx)/rx)**2+((Y-cy)/ry)**2<=1)&(((X-cx)/(rx-2.4))**2+((Y-cy)/(ry-2.4))**2>1)&(Z>=zc-12)&(Z<=zc+int(rz*0.75))
            v.g[cyl]=m
            dome=(ell(rx,ry,rz*0.35,zc+int(rz*0.75))<=1)&(Z>=zc+int(rz*0.75)); v.g[dome]=m
            # front ridge (prow) for aggression
            for z in range(zc-12,zc+int(rz*0.8)):
                y=int(cy-ry)-1; v.box(int(cx),int(cx)+1,max(0,y-1),y,z,z,ed if t==1 else tr)
            slit(eyez,1.6,W*0.44,glow=(t==3)); v.g[front&(np.abs(X-cx-0.5)<=1.0)&(Z<eyez)&(Z>eyez-9)&(v.g>0)&(v.g!=tr)&(v.g!=ed)]=dk if t==1 else v.g[front&(np.abs(X-cx-0.5)<=1.0)&(Z<eyez)&(Z>eyez-9)&(v.g>0)&(v.g!=tr)&(v.g!=ed)]; breaths(1); breaths(-1)
            band=cyl&(Z>=eyez+3)&(Z<=eyez+4); v.g[band]=tr if t==3 else ed
            rim=cyl&(Z<=zc-11); v.g[rim]=tr if t==3 else ed
            if t==3:  # horns + crest
                for s_ in (-1,1):
                    for i in range(22):
                        a=i/21; x=cx+s_*(rx+1+a*9); z=zc+rz*0.6+a*a*16-4*a; r=2.6*(1-a)+0.8
                        v.ball(x,cy+1,z,r,v.c((0.86,0.82,0.70)) if i<19 else tr)
                for i in range(18): v.box(int(cx),int(cx)+1,int(cy-ry*0.6+i*1.1),int(cy-ry*0.6+i*1.1)+1,zc+int(rz*0.95),zc+int(rz*0.95)+6-abs(i-6)//3,cl)
        else:  # T2 houndskull visored bascinet + mail aventail
            sh=(ell(rx,ry,rz*1.1)<=1)&(ell(rx-2.3,ry-2.3,rz*1.1-2.3)>1)&(Z>=zc-2); v.g[sh]=m
            for z in range(zc+int(rz*0.9),zc+int(rz*1.15)): v.ball(cx,cy+2,z,max(0.6,3-(z-zc-rz*0.9)*0.4),m)  # pointed crown
            for i in range(14):   # snout visor
                z0=zc-6+i*0.0; r=9-i*0.55
                yy=int(cy-ry)-i+2
                msk=(np.abs(Y-yy)<1)&(((X-cx)/r)**2+((Z-(eyez-4))/(r*0.95))**2<=1); v.g[msk]=m
            slit(eyez,0.9,W*0.38); v.g[front&(np.abs(Z-eyez+8)<=0.8)&(np.abs(X-cx)<5)&(v.g>0)]=dk
            for z in range(int(eyez-12),int(eyez),3):
                for x in (int(cx)-3,int(cx)+3): 
                    ys=np.where(v.g[x,:,z]>0)[0]; 
                    if len(ys): v.g[x,ys[0],z]=dk
            av=(ell(rx+2,ry+2,rz)<=1.0)&(ell(rx,ry,rz)>1.0)&(Z<zc-1)&(Z>=zc-12)&(Y>cy-ry*0.3); v.g[av]=mail
            for s_ in (-1,1): v.ball(cx+s_*(rx-1),cy-ry*0.3,eyez-1,1.6,tr)  # visor pivots
            v.g[sh&(Z==zc-2)]=tr
    elif kind=="medium":
        sh=(ell(rx,ry,rz)<=1)&(ell(rx-2.2,ry-2.2,rz-2.2)>1)&(Z>=zc+1); v.g[sh]=m
        av=(ell(rx+1.5,ry+1.5,rz)<=1.0)&(ell(rx-0.5,ry-0.5,rz)>1.0)&(Z<zc+2)&(Z>=zc-12)&(Y>cy-ry*0.15); v.g[av]=mail
        v.box(int(cx),int(cx)+1,int(cy-ry)-1,int(cy-ry)+3,zc-8,zc+int(rz*0.7),tr if t>1 else ed)   # nasal
        v.g[sh&(Z<=zc+2)]=tr if t>1 else ed
        if t>=2:  # spectacle guard
            for s_ in (-1,1):
                for a in range(24):
                    th=a*2*math.pi/24; x=cx+s_*5+3.6*math.cos(th); z=eyez+3.0*math.sin(th)
                    ys=np.where(v.g[int(x),:,int(z)]>0)[0]; y=(ys[0] if len(ys) else int(cy-ry))-1
                    v.put(x,max(0,y),z,tr)
            v.g[(Z>=zc+rz-1)&sh]=tr
        if t==3:  # crest + swept wings
            for i in range(26): v.box(int(cx),int(cx)+1,int(cy-ry*0.7+i*1.2),int(cy-ry*0.7+i*1.2)+1,zc+int(rz)-2,zc+int(rz)+5-abs(i-8)//3,tr)
            for s_ in (-1,1):
                for i in range(16):
                    v.box(int(cx+s_*(rx-1+i*0.5)),int(cx+s_*(rx-1+i*0.5)),int(cy+i*0.6),int(cy+i*0.6)+1,int(zc+rz*0.3+i*0.9),int(zc+rz*0.3+i*0.9)+max(1,6-i//3),ed)
            for s_ in (-1,1): v.put(cx+s_*5,cy-ry-1,eyez,e)
    else:  # light: hood / cowl
        col=cl if t>1 else lt
        sh=(ell(rx+1,ry+1,rz)<=1)&(ell(rx-1.2,ry-1.2,rz-1.2)>1)&(Z>=zc-4); v.g[sh]=col
        low=(ell(rx+3,ry+3,rz)<=1.2)&(ell(rx+1,ry+1,rz)>1.0)&(Z<zc+2)&(Z>=zc-12)&(Y>cy-ry*0.4); v.g[low]=col
        # peak drawn forward
        for i in range(8): v.ball(cx,cy-ry*0.5-i*0.8,zc+rz*0.9-i*0.6,3-i*0.25,col)
        face=front&(Z<zc+rz*0.62)&(Z>zc-8)&(np.abs(X-cx)<W*0.34); v.g[face&(v.g==col)]=0
        shadow=(Y>=cy-ry*0.5)&(Y<cy-ry*0.3)&(Z<zc+rz*0.55)&(Z>zc-6)&(np.abs(X-cx)<W*0.3); v.g[shadow&(v.g==0)]=dk   # face in shadow
        if t==1:
            v.g[(ell(rx+3.5,ry+3.5,rz)<=1.3)&(ell(rx+2,ry+2,rz)>1.25)&(Z<zc-6)&(Z>=zc-14)]=mail
        if t>=2:  # half mask + gilt edge
            msk=(Y>=cy-ry*0.5-1)&(Y<=cy-ry*0.5)&(Z<eyez-3)&(Z>zc-8)&(np.abs(X-cx)<W*0.32); v.g[msk]=m
            for s_ in (-1,1): v.box(int(cx+s_*4),int(cx+s_*4)+1,int(cy-ry*0.5)+1,int(cy-ry*0.5)+1,int(eyez),int(eyez),e if t==3 else v.c((0.9,0.85,0.7)))
        if t==3:  # gilt circlet with spikes
            ring=(ell(rx+1.6,ry+1.6,rz)<=1)&(ell(rx+0.4,ry+0.4,rz)>1)&(np.abs(Z-(zc+rz*0.55))<1.2); v.g[ring]=tr
            for a in range(7):
                th=math.pi*(0.15+0.7*a/6); x=cx+(rx+1)*math.cos(th); y=cy-(ry+1)*math.sin(th)
                v.box(int(x),int(x)+1,int(y),int(y)+1,int(zc+rz*0.55),int(zc+rz*0.55)+4+(2 if a==3 else 0),tr)
    return v,VS_A,(cx+0.5,cy+0.5,zc)
# ---------- chest (ref torso 0.42w x 0.26d x 0.42h, pivot = chest-bone height, centre) ----------
def chestpiece(p,kind,t):
    W,D,H=35,22,36; v=M(W+30,D+18,H+12); cx=v.g.shape[0]/2-0.5; cy=v.g.shape[1]/2-0.5
    m=v.c(p['metal']); tr=v.c(p['trim']); cl=v.c(p['cloth']); lt=v.c(p['leather']); e=v.c(p['edge'],p['glow']); ed=v.c(p['edge'])
    mail=v.c((0.36,0.37,0.40) if t>1 else (0.48,0.48,0.5)); fur=v.c(p['fur']); fur2=v.c(tuple(c*0.75 for c in p['fur']))
    X,Y=np.indices(v.g.shape[:2]); Z3=np.indices(v.g.shape)[2]; z0=2; top=z0+H-1
    rng=np.random.default_rng(7)
    def prof(z):
        u=(z-z0)/H; rx=W/2*(0.78+0.22*min(1,u/0.7)); ry=D/2*(0.88+0.12*min(1,u/0.7))
        if u>0.84: k=(u-0.84)/0.16; rx*=1-0.12*k; ry*=1-0.35*k
        return rx,ry
    def shellmask(z,th=2):
        rx,ry=prof(z); o=((X-cx)/(rx+th))**2+((Y-cy)/(ry+th))**2; i=((X-cx)/rx)**2+((Y-cy)/ry)**2; return (o<=1)&(i>1)
    for z in range(z0,top+1):
        sl=shellmask(z)
        if z>=top-2: rx,ry=prof(z); sl=(((X-cx)/(rx+2))**2+((Y-cy)/(ry+2))**2<=1)&(((X-cx)/(W*0.2))**2+((Y-cy)/(D*0.32))**2>1)
        if kind=="heavy": col=m
        elif kind=="medium": col=lt if t==1 else np.where(((X+z)%3==0),v.c(p['trim'] if t==3 else (0.6,0.6,0.62)),cl if t==3 else lt)   # brigandine rivets
        else: col=cl
        v.g[:,:,z][sl]=col[sl] if isinstance(col,np.ndarray) else col
        if kind=="heavy" and (z-z0)%7==0 and z<top-10: v.g[:,:,z][sl]=ed if t==1 else tr   # lames
        if kind=="light" and z<z0+9:
            k=(z0+9-z)*0.6; rx,ry=prof(z); o2=((X-cx)/(rx+2+k))**2+((Y-cy)/(ry+2+k*0.8))**2; i2=((X-cx)/(rx+k))**2+((Y-cy)/(ry+k*0.8))**2
            v.g[:,:,z][(o2<=1)&(i2>1)]=cl
    if kind=="heavy":  # central ridge (peascod)
        for z in range(z0+4,top-4):
            rx,ry=prof(z); v.box(int(cx),int(cx)+1,int(round(cy-ry-3)),int(round(cy-ry-3)),z,z,m)
    # gorget
    if kind!="light" or t>=2:
        for z in range(top-1,top+5):
            o=((X-cx)/(W*0.29))**2+((Y-cy)/(D*0.44))**2; i=((X-cx)/(W*0.22))**2+((Y-cy)/(D*0.33))**2
            v.g[:,:,z][(o<=1)&(i>1)]=(tr if z==top+4 and t>1 and kind!="light" else (m if kind!="light" else cl))
    # flared layered pauldrons
    if kind!="light" and PAULDRONS:
        lames=4 if kind=="heavy" else 2
        for s_ in (-1,1):
            for k in range(lames):
                P=M(*v.g.shape); r=7.5+k*0.9 if kind=="heavy" else 6.5
                P.ball(cx+s_*(W/2+3+k*1.6),cy,top-1-k*3.2,r,1,(1,1.15,0.55)); P.ball(cx+s_*(W/2+3+k*1.6),cy,top-2.5-k*3.2,r-1.6,0,(1,1.15,0.55))
                msk=P.g>0; msk&=Z3<=top+3
                v.g[msk]=m if kind=="heavy" else (lt if t==1 else m)
                edge=msk&(Z3<=top-1-k*3.2-r*0.35)
                v.g[edge]=ed if t==1 else tr
            if kind=="heavy" and t>=2:   # spiked/raised haute-piece
                for z in range(top,top+6): v.box(int(cx+s_*(W/2+1)),int(cx+s_*(W/2+1)),int(cy-6),int(cy+6),z,z,tr if t==3 else m)
    # mantle: fur (heavy) / cloth (medium & light), across shoulders and down the back
    if kind=="heavy" or t>=2:
        col1,col2=(fur,fur2) if kind=="heavy" else (cl,cl)
        for z in range(top-6,top+4):
            rx,ry=prof(min(z,top)); o=((X-cx)/(rx+5.5))**2+((Y-cy)/(ry+5))**2; i=((X-cx)/(rx+2.2))**2+((Y-cy)/(ry+2.2))**2
            msk=(o<=1)&(i>1)&((Y>cy-ry*0.4)|(z>=top+1))&(((X-cx)/(W*0.24))**2+((Y-cy)/(D*0.38))**2>1)
            noise=rng.random(msk.shape)<0.35
            v.g[:,:,z][msk]=np.where(noise,col2,col1)[msk]
        if kind!="heavy" or t==3:   # cape tail down the back
            for z in range(z0+6,top-5):
                rx,ry=prof(z); msk=(Y>=int(cy+ry+2))&(Y<=int(cy+ry+3))&(np.abs(X-cx)<rx*0.85-(top-z)*0.05)
                v.g[:,:,z][msk]=cl
    rx,ry=prof(z0); belt=(((X-cx)/(rx+2.5))**2+((Y-cy)/(ry+2.5))**2<=1)&(((X-cx)/rx)**2+((Y-cy)/ry)**2>1)
    for z in (z0,z0+1,z0+2): v.g[:,:,z][belt]=lt if t==1 else tr
    if kind=="light" and t>=2:   # stole with gilt edge down the front
        for z in range(z0+3,top):
            rx,ry=prof(z)
            for s_ in (-1,1): v.box(int(cx+s_*5)-1,int(cx+s_*5)+1,int(round(cy-ry-2)),int(round(cy-ry-2)),z,z,tr if (z%4) else e)
    if t==3:  # glowing sigil on the breast
        rx,ry=prof(z0+21); fy=int(round(cy-ry-(4 if kind=="heavy" else 2)))
        for (dx,dz) in [(0,0),(0,1),(0,2),(0,3),(-1,2),(1,2),(-2,2),(2,2),(0,-1)]: v.put(cx+dx,fy,z0+19+dz,e)
    return wear(v,p,3+t) if kind!="light" else v,VS_A,(cx+0.5,cy+0.5,z0+H*0.62)
def shield(p,t):
    S=40 if t==1 else 44; v=M(S+2,6,S+10); cx=S/2+0.5; w=v.c(p['wood']); m=v.c(p['metal']); tr=v.c(p['trim']); c=v.c(p['cloth']); e=v.c(p['edge'],p['glow'])
    for x in range(S+2):
        for z in range(S+10):
            dx=(x-cx)/(S/2); dz=(z-(S+10)*0.62)/(S*0.6)
            if t==1: ok=dx*dx+((z-(S+10)/2)/(S/2))**2<=1   # round
            else: ok=abs(dx)<=1 and (dz>=-0.15 and z<S+8 or dx*dx+(dz+0.15)**2*1.0<=1 and dz<0) if True else False
            if t!=1: ok=(abs(dx)<=1 and z<S+8 and z>=(S+10)*0.62-S*0.09) or (dx*dx+((z-((S+10)*0.62-S*0.09))/(S*0.7))**2<=1 and z<(S+10)*0.62)
            if ok: v.g[x,1,z]=w; v.g[x,2,z]=w
    border=(v.g[:,1,:]>0); import scipy.ndimage as nd
    er=nd.binary_erosion(border,iterations=2); v.g[:,1,:][border&~er]=m
    if t>=2:
        mask=er.copy(); X,Z=np.indices(mask.shape)
        v.g[:,1,:][mask&(np.abs(X-cx)<3)]=tr; v.g[:,1,:][mask&(np.abs(Z-(S+10)*0.62)<3)]=tr
        v.g[:,1,:][mask&(np.abs(X-cx)>=3)&(np.abs(Z-(S+10)*0.62)>=3)&((X<cx)^(Z<(S+10)*0.62))]=c
    zb=int((S+10)*0.55); v.ball(cx,0.5,zb,3,m if t<3 else e)
    v.box(int(cx)-1,int(cx)+1,3,4,zb-6,zb+6,v.c(p['leather']))  # handle at back
    return v,VS_W,(cx,4,zb)
def ring(p,t):
    v=M(9,9,9); c=v.c(p['trim'] if t>1 else p['metal'])
    for a in range(40):
        th=a*2*math.pi/40; v.put(4+3.2*math.cos(th),4+3.2*math.sin(th),4,c)
    v.box(3,5,0,1,4,5,c)
    if t>=2: v.box(4,4,0,0,5,6,v.c(p['gem'],1 if t==3 else 0))
    return v,0.006,(4,4,4)
def amulet(p,t):
    v=M(28,6,34); ch=v.c(p['trim'] if t>1 else p['metal'])
    for i in range(60):
        a=math.pi*i/59; v.put(14+11*math.cos(a),2,14+18*math.sin(a),ch)
    v.ball(14,2.5,9,4 if t<3 else 5,ch,(1,0.4,1)); v.ball(14,1.5,9,2.5 if t>1 else 2,v.c(p['gem'] or (0.55,0.5,0.4),1 if t==3 else 0),(1,0.6,1))
    return v,0.008,(14,2.5,30)
def collar(p,t,r=13):
    v=M(2*r+6,2*r+6,6); cx=r+2.5; lt=v.c(p['leather'] if t<3 else p['cloth']); tr=v.c(p['trim'])
    X,Y=np.indices(v.g.shape[:2]); d=np.sqrt((X-cx)**2+(Y-cx)**2)
    for z in (2,3): v.g[:,:,z][(d<=r+1)&(d>r-1)]=lt
    v.g[:,:,2][(d<=r+1)&(d>r-1)&((X+Y)%5==0)]=tr
    v.ball(cx,cx-r-1.5,1.5,2.2,tr); 
    if t>=2: v.put(cx,cx-r-3,1,v.c(p['gem'],1))
    return v,0.008,(cx,cx,2.5)
