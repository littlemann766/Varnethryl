# Generic shared MALE armour set (one mesh per piece, all heroes). Built in Darius' rest space (male reference rig),
# skinned by bone NAME with chain-interpolated weights so the piece follows any male rig's joint layout.
# usage: python3 gen_generic.py <outdir>
import bpy,sys,os,json,math,numpy as np
OUT=sys.argv[-1]; os.makedirs(OUT,exist_ok=True)
RIG='/workspace/godot-voxel/voxel/darius_voxel_noweapon.glb'   # read-only
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=RIG)
ARM=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]
for o in list(bpy.data.objects):
    if o is not ARM: bpy.data.objects.remove(o)
for a in list(bpy.data.actions): bpy.data.actions.remove(a)
ARM.animation_data_clear()
BH={b.name:np.array(ARM.matrix_world@b.head_local) for b in ARM.data.bones}
STEEL=np.array([0.50,0.52,0.55]); EDGE=np.array([0.70,0.71,0.73]); DARK=np.array([0.03,0.03,0.035]); LEATH=np.array([0.30,0.17,0.09])
MAIL=np.array([0.46,0.47,0.50]); MAILD=np.array([0.22,0.22,0.24]); RIV=np.array([0.80,0.78,0.70]); BRASS=np.array([0.62,0.48,0.24])
def nz(v): n=np.linalg.norm(v,axis=-1,keepdims=True); return v/np.maximum(n,1e-9)
class Mesh:
    def __init__(s): s.V=[]; s.F=[]; s.C=[]
    def add(s,V,F,C):
        o=sum(len(v) for v in s.V); s.V.append(np.asarray(V,float)); s.F+=[[i+o for i in f] for f in F]; s.C.append(np.broadcast_to(np.asarray(C,float),(len(V),3)).copy())
    def arrays(s): return np.vstack(s.V),np.array(s.F),np.vstack(s.C)
def frames(P,up=np.array([0,-1.0,0])):
    T=np.gradient(P,axis=0); T=nz(T); U=nz(up-(T@up)[:,None]*T); W=np.cross(T,U); return T,U,W
def loft(M,P,A,B,N=24,th=(0,2*math.pi),t=0.010,ex=2.4,col=None,push=None,rim=0.004,up=np.array([0,-1.0,0]),U=None,W=None,closed=None):
    """P[K,3] path, A/B radii along U/W (U=front by default). th arc range (0=front). shell thickness t (inward). col(k,j,ang,pt)->rgb."""
    N=max(8,int(round(N*NM))); P=np.asarray(P,float); K=len(P); A=np.broadcast_to(np.asarray(A,float),(K,)); B=np.broadcast_to(np.asarray(B,float),(K,))
    if U is None: _,U,W=frames(P,up)
    full=abs(th[1]-th[0]-2*math.pi)<1e-6 if closed is None else closed
    J=N if full else N+1; ang=np.linspace(th[0],th[1],J,endpoint=not full)
    c,s=np.cos(ang),np.sin(ang); e=2/ex
    cs=np.sign(c)*np.abs(c)**e; ss=np.sign(s)*np.abs(s)**e
    def ring(k,dr):
        a=A[k]+dr; b=B[k]+dr; pts=P[k]+np.outer(cs*a,U[k])+np.outer(ss*b,W[k])
        if push is not None: pts=pts+push(k,ang,pts,U[k],W[k])
        return pts
    rimk=lambda k:rim if k in (0,K-1) else 0.0
    O=np.array([ring(k,rimk(k)) for k in range(K)]); I=np.array([ring(k,-t+rimk(k)*0.3) for k in range(K)])
    V=np.vstack([O.reshape(-1,3),I.reshape(-1,3)]); off=K*J; F=[]
    km=K//2; Tm=P[min(km+1,K-1)]-P[max(km-1,0)]; flip=np.dot(np.cross(W[km],Tm),U[km])<0
    idx=lambda k,j:k*J+(j%J)
    jr=range(J) if full else range(J-1)
    for k in range(K-1):
        for j in jr:
            a,b,cc,d=idx(k,j),idx(k,j+1),idx(k+1,j+1),idx(k+1,j)
            F+=[[a,b,cc],[a,cc,d],[off+a,off+cc,off+b],[off+a,off+d,off+cc]]
    for k in (0,K-1):   # end caps (rim)
        for j in jr:
            a,b=idx(k,j),idx(k,j+1); F+=[[a,off+b,b],[a,off+a,off+b]] if k==0 else [[a,b,off+b],[a,off+b,off+a]]
    if not full:
        for j in (0,J-1):
            for k in range(K-1):
                a,d=idx(k,j),idx(k+1,j); F+=[[a,off+a,off+d],[a,off+d,d]] if j==J-1 else [[a,d,off+d],[a,off+d,off+a]]
    if flip: F=[f[::-1] for f in F]
    C=np.zeros((len(V),3))
    for k in range(K):
        for jj in range(J):
            cc_=col(k,jj,ang[jj],O[k,jj]) if col else STEEL
            if k in (0,K-1) and rim>0: cc_=EDGE
            if (not full) and jj in (0,J-1) and rim>0: cc_=EDGE
            C[k*J+jj]=cc_; C[off+k*J+jj]=np.minimum(cc_,STEEL*0.55)
    M.add(V,F,C); return O
def dome(M,c,r,n=np.array([0,0,1.0]),seg=6,col=RIV,h=None):
    n=nz(n); u=nz(np.cross(n,[0.3,0.5,0.81])); w=np.cross(n,u); h=r*0.7 if h is None else h
    V=[c+n*h]+[c+u*r*math.cos(a)+w*r*math.sin(a) for a in np.linspace(0,2*math.pi,seg,endpoint=False)]
    V+=[c-n*0.003+u*r*math.cos(a)+w*r*math.sin(a) for a in np.linspace(0,2*math.pi,seg,endpoint=False)]
    F=[[0,1+i,1+(i+1)%seg] for i in range(seg)]+[[1+i,1+seg+i,1+(i+1)%seg] for i in range(seg)]+[[1+(i+1)%seg,1+seg+i,1+seg+(i+1)%seg] for i in range(seg)]
    M.add(V,F,col)
def rivets(M,O,k,js,ctr,r=0.0055):
    for j in js:
        p=O[k,j%O.shape[1]]; dome(M,p,r,p-ctr)
def box(M,c,ax,hs,col):   # oriented box ax=3 axes rows
    ax=np.asarray(ax,float); V=[c+sx*hs[0]*ax[0]+sy*hs[1]*ax[1]+sz*hs[2]*ax[2] for sx in(-1,1) for sy in(-1,1) for sz in(-1,1)]
    F=[[0,1,3],[0,3,2],[4,6,7],[4,7,5],[0,4,5],[0,5,1],[2,3,7],[2,7,6],[0,2,6],[0,6,4],[1,5,7],[1,7,3]]; M.add(V,F,col)
def strap(M,P,A,B,th,w=0.012,U=None,W=None,col=LEATH,N=14):
    P=np.asarray(P,float); T=nz(P[1]-P[0]); Pp=np.array([P[0]-T*w,P[0]+T*w])
    O=loft(M,Pp,A,B,N=N,th=th,t=0.004,rim=0,col=lambda *a:col,U=np.array([U,U]) if U is not None else None,W=np.array([W,W]) if W is not None else None)
    m=O[0,len(O[0])//2]; return O
# ---------------- weights ----------------
def chain_w(Pts,chain,blend=0.22):
    """chain=[(bone, joint_pos)...] with final (None,end) ; returns list of dict"""
    J=np.array([c[1] for c in chain]); bones=[c[0] for c in chain[:-1]]; out=[]
    for p in Pts:
        best=None
        for i in range(len(J)-1):
            d=J[i+1]-J[i]; L=d@d; t=np.clip((p-J[i])@d/L,0,1); dist=np.linalg.norm(p-J[i]-t*d)
            if best is None or dist<best[0]-1e-6: best=(dist,i,t)
        _,i,t=best; w={bones[i]:1.0}
        if t<blend and i>0: a=0.5+0.5*t/blend; w={bones[i]:a,bones[i-1]:1-a}
        elif t>1-blend and i<len(bones)-1: a=0.5+0.5*(1-t)/blend; w={bones[i]:a,bones[i+1]:1-a}
        out.append(w)
    return out
def mirror_name(n): return n[:-2]+'_R' if n.endswith('_L') else n
# ---------------- pieces ----------------
hz=BH['hips'][2]; nkz=BH['neck'][2]; cy=-0.088
def torso(M):
    # cuirass: breastplate + backplate, keel ridge, pec shaping, plackart, faulds, mail skirt, gorget
    Z=np.array([0.935,0.975,1.03,1.09,1.16,1.24,1.31,1.37,1.42,1.465,1.50,1.525])
    HW=np.array([0.162,0.158,0.150,0.146,0.152,0.170,0.186,0.196,0.198,0.188,0.160,0.118])
    HD=np.array([0.118,0.114,0.108,0.106,0.112,0.124,0.132,0.134,0.128,0.118,0.100,0.082])
    P=np.c_[np.zeros_like(Z),np.full_like(Z,cy),Z]
    def push(k,ang,pts,U,W):
        x=pts[:,0]; fr=np.cos(ang)>0
        keel=0.016*np.exp(-(x/0.03)**2)*np.clip((Z[k]-1.0)/0.3,0,1)*(Z[k]<1.47)
        pec=0.010*np.exp(-((np.abs(x)-0.085)/0.05)**2)*np.exp(-((Z[k]-1.33)/0.06)**2)
        d=np.zeros_like(pts); d[:,1]=-(keel+pec)*fr; return d
    def col(k,j,a,p):
        if abs(p[0])<0.004 and math.cos(a)>0.9 and 1.05<Z[k]<1.46: return EDGE
        return STEEL
    O=loft(M,P,HD,HW,N=44,t=0.011,push=push,col=col,rim=0.005)
    rivets(M,O,len(Z)-2,[6,10,34,38],np.array([0,cy,1.5]))
    for k in (2,):   # plackart (lower belly overlap plate, front only)
        Zp=np.linspace(0.975,1.20,6); Pp=np.c_[np.zeros(6),np.full(6,cy),Zp]
        Op=loft(M,Pp,np.interp(Zp,Z,HD)+0.010,np.interp(Zp,Z,HW)+0.006,N=26,th=(-1.15,1.15),t=0.008,ex=2.4,
                push=lambda k,a,pts,U,W:np.c_[np.zeros(len(a)),-0.012*np.exp(-(pts[:,0]/0.03)**2)*(k>1)*np.minimum(1,(k-1)/2),np.zeros(len(a))]*np.array([0,1,0]),rim=0.004,
                col=lambda k,j,a,p:STEEL*1.04)
        rivets(M,Op,5,[3,9,17,23],np.array([0,cy,1.15]),0.005)
    # back: two straps across the shoulder blades are implied by the pauldrons' leather; add belt
    Zb=np.array([0.925,0.965]); Pb=np.c_[np.zeros(2),np.full(2,cy),Zb]
    Ob=loft(M,Pb,np.full(2,0.126),np.full(2,0.170),N=40,t=0.006,rim=0,col=lambda *a:LEATH)
    box(M,Ob[1,0]+np.array([0,-0.004,-0.02]),np.eye(3),(0.020,0.006,0.020),BRASS)
    # faulds: 3 overlapping lames flaring down
    for i in range(3):
        z0=0.935-i*0.045; Zf=np.array([z0,z0-0.055]); Pf=np.c_[np.zeros(2),np.full(2,cy),Zf]
        Of=loft(M,Pf,np.array([0.124+i*0.008,0.136+i*0.010]),np.array([0.168+i*0.008,0.182+i*0.010]),N=40,th=(-2.25,2.25),t=0.008,rim=0.004)
        rivets(M,Of,0,[4,12,20,28,36],np.array([0,cy,z0]),0.0045)
    # mail skirt under faulds (rings of mail = alternating dark rows)
    Zm=np.linspace(0.90,0.72,8); Pm=np.c_[np.zeros(8),np.full(8,cy),Zm]
    loft(M,Pm,np.linspace(0.122,0.150,8),np.linspace(0.165,0.192,8),N=40,t=0.004,rim=0,
         col=lambda k,j,a,p:MAIL if (k+j)%2 else MAILD,push=lambda k,a,pts,U,W:np.zeros_like(pts))
    # gorget
    for i in range(2):
        Zg=np.array([1.515+i*0.03,1.565+i*0.03]); Pg=np.c_[np.zeros(2),np.full(2,cy-0.004),Zg]
        loft(M,Pg,np.array([0.098-i*0.014,0.078-i*0.012]),np.array([0.122-i*0.016,0.096-i*0.012]),N=36,t=0.007,rim=0.004)
    return [('hips',np.array([0,cy,0.70])),('spine',np.array([0,cy,0.978])),('spine2',np.array([0,cy,1.147])),('chest',np.array([0,cy,1.316])),('upperChest',np.array([0,cy,1.448])),('neck',np.array([0,cy,1.551])),(None,np.array([0,cy,1.62]))]
def helm(M):
    hc=np.array([0,-0.100,0]); Z=np.array([1.545,1.575,1.62,1.67,1.715,1.733,1.738,1.752,1.757,1.775,1.80,1.83,1.855,1.872,1.884])
    HW=np.array([0.130,0.124,0.127,0.132,0.134,0.134,0.134,0.133,0.133,0.131,0.124,0.110,0.088,0.058,0.022])
    HD=np.array([0.148,0.140,0.145,0.151,0.154,0.155,0.155,0.154,0.154,0.151,0.142,0.126,0.100,0.066,0.025])
    P=np.c_[np.zeros_like(Z),np.full_like(Z,hc[1]+0.006),Z]
    slit=lambda k,a:(k in (6,7)) and math.cos(a)>0.42 and not (abs(math.sin(a))<0.06)   # eye slit, nasal bar left in the middle
    def push(k,ang,pts,U,W):
        d=np.zeros_like(pts); fr=np.clip(np.cos(ang),0,1)
        d[:,1]-=0.022*np.exp(-(pts[:,0]/0.028)**2)*fr*(Z[k]<1.86)          # face keel (sugarloaf point)
        sl=np.array([slit(k,a) for a in ang]); d[sl]+=-np.outer(np.cos(ang[sl]),U)*0.016   # recessed slit
        if k in (9,): d+=np.outer(np.cos(ang),U)*0.0+np.c_[np.zeros(len(ang)),np.zeros(len(ang)),np.zeros(len(ang))]
        cr=0.012*np.exp(-(pts[:,0]/0.012)**2)*(Z[k]>1.81); d[:,2]+=cr                       # crest ridge front-to-back
        return d
    def col(k,j,a,p):
        if slit(k,a): return DARK
        if k in (9,10) : return EDGE*0.92   # brow band
        if 2<=k<=4 and math.sin(a)<-0.25 and math.cos(a)>0.05 and (j%3==0): return DARK   # breaths (right cheek)
        if abs(p[0])<0.006 and math.cos(a)>0.8: return EDGE
        return STEEL*1.08
    O=loft(M,P,HD,HW,N=64,t=0.012,push=push,col=col,rim=0.006)
    ctr=np.array([0,hc[1],1.72])
    rivets(M,O,9,[8,16,24,32,40,48,56],ctr,0.0058); rivets(M,O,1,list(range(0,64,6)),ctr,0.005)
    # brow band (raised)
    Pb=np.c_[np.zeros(2),np.full(2,hc[1]+0.006),np.array([1.764,1.784])]
    loft(M,Pb,np.full(2,0.156),np.full(2,0.137),N=64,t=0.006,rim=0.002,col=lambda *a:EDGE*0.9,push=lambda k,ang,pts,U,W:np.c_[np.zeros(len(ang)),-0.022*np.exp(-(pts[:,0]/0.028)**2)*np.clip(np.cos(ang),0,1),np.zeros(len(ang))])
    # cross reinforcement on the crown
    Pc=np.c_[np.zeros(9),np.full(9,hc[1]+0.006),np.linspace(1.60,1.70,9)]
    return [('head',np.array([0,-0.10,1.60])),(None,np.array([0,-0.10,1.95]))]
def pauldron_L(M):
    s=BH['upperArm_L']; e=BH['foreArm_L']; ax=nz(e-s); out=nz(np.array([1,0,0.35]))
    c=s+np.array([0.022,0,0.030])
    # main dome: rings around axis 'out' (pointing outward-up from the shoulder), forming a cap
    K=9; tt=np.linspace(0,1,K); Pd=np.array([c+out*(0.070-0.095*t) for t in tt])
    rad=0.115*np.sin(np.clip(tt*1.35+0.12,0,math.pi/2))+0.004
    Up=np.tile(nz(np.array([0,-1.0,0])),(K,1)); Wp=np.tile(nz(np.cross(out,[0,-1.0,0])),(K,1))
    Od=loft(M,Pd,rad*0.95,rad*1.05,N=40,th=(-2.6,2.6),t=0.010,rim=0.006,U=Up,W=Wp,closed=False,push=lambda k,a,pts,U,W:np.outer(np.full(len(a),0.006*(k==4)),out))
    rivets(M,Od,K-1,[4,12,20,28,36],c,0.0058)
    # 3 tight flared lames down the upper arm
    Pl=[]
    for i in range(3):
        t0=0.10+i*0.13; p0=s+ax*(t0*np.linalg.norm(e-s)); p1=s+ax*((t0+0.15)*np.linalg.norm(e-s))
        Ol=loft(M,np.array([p0,p1]),np.array([0.084-i*0.007,0.092-i*0.007]),np.array([0.076-i*0.006,0.084-i*0.006]),N=30,th=(-2.5,2.5),t=0.008,rim=0.004,up=np.array([0,-1.0,0]))
        rivets(M,Ol,0,[4,15,26],p0,0.0048)
    # rerebrace tube + strap
    p0=s+ax*0.48*np.linalg.norm(e-s); p1=s+ax*0.90*np.linalg.norm(e-s)
    loft(M,np.array([p0,p0*0.5+p1*0.5,p1]),np.array([0.062,0.058,0.056]),np.array([0.058,0.054,0.052]),N=28,t=0.008,rim=0.004)
    strap(M,np.array([s+ax*0.66*np.linalg.norm(e-s)]*2),0.066,0.062,(1.2,5.1),N=12)
    # leather arming strap over the shoulder top
    return [('shoulder_L',BH['shoulder_L']),('upperArm_L',s),('foreArm_L',e)],0.15
def glove_L(M):
    s=BH['upperArm_L']; e=BH['foreArm_L']; h=BH['hand_L']; fa=nz(h-e); L=np.linalg.norm(h-e)
    # couter (elbow cop) with side fan
    cE=e+np.array([0,0.020,0.0])   # elbow points back (+y)
    bk=nz(np.array([0,1.0,0])-(np.array([0,1.0,0])@fa)*fa)
    K=6; tt=np.linspace(0,1,K); Pc=np.array([cE+bk*(0.050-0.060*t) for t in tt]); rad=0.062*np.sin(np.clip(tt*1.4+0.15,0,math.pi/2))
    Uc=np.tile(fa,(K,1)); Wc=np.tile(nz(np.cross(bk,fa)),(K,1))
    Oc=loft(M,Pc,rad,rad*0.9,N=26,th=(-2.8,2.8),t=0.008,rim=0.005,U=Uc,W=Wc,closed=False)
    dome(M,cE+bk*0.052,0.010,bk,seg=8,col=EDGE)
    # vambrace
    Pv=np.array([e+fa*L*t for t in np.linspace(0.12,0.97,6)])
    Ov=loft(M,Pv,np.linspace(0.052,0.040,6),np.linspace(0.048,0.036,6),N=30,t=0.007,rim=0.004,
            push=lambda k,a,pts,U,W:np.outer(0.008*np.exp(-(np.sin(a)/0.25)**2)*(np.cos(a)>0),U))   # top ridge
    for t in (0.35,0.75): strap(M,np.array([e+fa*L*t]*2),0.048-t*0.01,0.044-t*0.01,(1.4,4.9),N=12)
    # flared gauntlet cuff
    Pg=np.array([h-fa*0.035,h+fa*0.012]); Og=loft(M,Pg,np.array([0.046,0.058]),np.array([0.040,0.050]),N=30,t=0.007,rim=0.005)
    rivets(M,Og,1,[3,10,18,25],h,0.0045)
    # hand: back-of-hand plate + finger lames (mitten), palm leather
    hd=nz(BH['middle3_L']-h); Lh=np.linalg.norm(BH['middle3_L']-h)+0.03
    for i,(t0,t1) in enumerate([(0.0,0.42),(0.38,0.58),(0.55,0.73),(0.70,0.86),(0.83,1.0)]):
        Ph=np.array([h+hd*Lh*t0,h+hd*Lh*t1]); w=0.040-0.003*i
        loft(M,Ph,np.array([w,w-0.002]),np.array([0.022,0.020]),N=22,t=0.006,rim=0.003,up=np.array([0,-1.0,0]),col=lambda *a:STEEL if True else LEATH)
    # thumb
    th=BH['thumb1_L']; td=nz(BH['thumb3_L']-th)
    loft(M,np.array([th,th+td*0.06]),np.array([0.016,0.013]),np.array([0.014,0.011]),N=14,t=0.005,rim=0.002)
    return [('upperArm_L',s),('foreArm_L',e),('hand_L',h),(None,h+hd*0.2)],0.12
def leg_L(M):
    s=BH['thigh_L']; e=BH['shin_L']; ax=nz(e-s); L=np.linalg.norm(e-s)
    # cuisse (front/side plate) over mail
    tt=np.linspace(0.10,0.90,8); Pc=np.array([s+ax*L*t for t in tt])
    Oc=loft(M,Pc,np.linspace(0.088,0.068,8),np.linspace(0.084,0.064,8),N=34,th=(-2.2,2.2),t=0.009,rim=0.005,
            push=lambda k,a,pts,U,W:np.outer(0.009*np.exp(-(np.sin(a)/0.22)**2)*(np.cos(a)>0),U))
    rivets(M,Oc,0,[4,10,17,24,30],s+ax*L*0.1,0.005)
    # mail behind
    loft(M,Pc,np.linspace(0.080,0.060,8),np.linspace(0.078,0.058,8),N=34,t=0.004,rim=0,col=lambda k,j,a,p:MAIL if (k+j)%2 else MAILD)
    for t in (0.30,0.68): strap(M,np.array([s+ax*L*t]*2),0.092-t*0.025,0.088-t*0.025,(2.0,4.3),N=10)
    # poleyn: knee cup + side wing
    kc=e+np.array([0,-0.045,0.005]); fw=np.array([0,-1.0,0]); K=7; tt=np.linspace(0,1,K)
    Pk=np.array([kc+fw*(0.035-0.045*t) for t in tt]); rad=0.060*np.sin(np.clip(tt*1.45+0.15,0,math.pi/2))+0.002
    Ok=loft(M,Pk,rad,rad*0.95,N=28,U=np.tile([0,0,1.0],(K,1)),W=np.tile([1.0,0,0],(K,1)),t=0.008,rim=0.005)
    dome(M,kc+fw*0.037,0.011,fw,seg=8,col=EDGE)
    Pw=np.array([kc+np.array([0.050,0.02,0.02]),kc+np.array([0.064,0.03,-0.02])])
    loft(M,Pw,np.array([0.030,0.026]),np.array([0.020,0.016]),N=16,t=0.006,rim=0.003,up=np.array([0,-1.0,0]))
    return [('hips',BH['hips']+np.array([0.09,0,0.06])),('thigh_L',s),('shin_L',e),(None,e+ax*0.25)],0.15
def boot_L(M):
    k=BH['shin_L']; a=BH['foot_L']; ax=nz(a-k); L=np.linalg.norm(a-k)
    # greave: closed tube with front ridge + strap
    tt=np.linspace(0.12,0.96,8); Pg=np.array([k+ax*L*t for t in tt])
    rr=np.interp(tt,[0.12,0.45,0.96],[0.060,0.064,0.048])
    loft(M,Pg,rr,rr*0.92,N=34,t=0.008,rim=0.005,push=lambda kk,an,pts,U,W:np.outer(0.010*np.exp(-(np.sin(an)/0.22)**2)*(np.cos(an)>0),U))
    for t in (0.40,0.82): strap(M,np.array([k+ax*L*t]*2),np.interp(t,[0.12,0.45,0.96],[0.060,0.064,0.048])+0.004,np.interp(t,[0.12,0.45,0.96],[0.060,0.064,0.048])*0.92+0.004,(2.2,4.1),N=10)
    # sabaton: lames from ankle to pointed toe (front -y), flat sole
    x=a[0]; Y=np.array([0.055,0.030,0.0,-0.035,-0.070,-0.105,-0.135,-0.165,-0.185])
    Wd=np.array([0.050,0.054,0.056,0.056,0.054,0.050,0.044,0.034,0.016]); Ht=np.array([0.11,0.115,0.105,0.085,0.070,0.060,0.052,0.042,0.022])
    P=np.c_[np.full(len(Y),x),Y,Ht*0.5]; U=np.tile([0,0,1.0],(len(Y),1)); W=np.tile([1.0,0,0],(len(Y),1))
    def push(kk,an,pts,Uu,Ww):
        d=np.zeros_like(pts); d[:,2]=np.maximum(0.0,-pts[:,2]); return d   # flatten sole at z=0
    def col(kk,j,an,p): return LEATH*0.6 if p[2]<0.012 else STEEL
    Os=loft(M,P,Ht*0.5,Wd,N=30,t=0.008,rim=0.004,U=U,W=W,push=push,col=col)
    for kk in (3,5,7): rivets(M,Os,kk,[0],np.array([x,Y[kk],0.0]),0.0045)
    for kk,yy in enumerate([0.0,-0.035,-0.070,-0.105]):   # lame lips
        Pl=np.array([[x,yy+0.006,Ht[kk+2]*0.5],[x,yy-0.006,Ht[kk+2]*0.5]])
        loft(M,Pl,np.full(2,Ht[kk+2]*0.5+0.004),np.full(2,Wd[kk+2]+0.004),N=20,th=(-1.7,1.7),t=0.004,rim=0,U=np.tile([0,0,1.0],(2,1)),W=np.tile([1.0,0,0],(2,1)),col=lambda *a:EDGE*0.9)
    return [('shin_L',k),('foot_L',a),('toe_L',BH['toe_L']),(None,np.array([x,-0.20,0.03]))],0.2
# ---------------- build / export ----------------
TRI={}
NM=1.0
NMS={'shoulder_L':1.45,'shoulder_R':1.45,'glove_L':1.45,'glove_R':1.45,'leg_L':1.25,'leg_R':1.25,'boot_L':1.35,'boot_R':1.35}
def build(name,fn,mirror=False):
    global NM; NM=NMS.get(name,1.0); M=Mesh(); r=fn(M); chain,bl=(r if isinstance(r,tuple) else (r,0.22))
    V,F,C=M.arrays(); W=chain_w(V,chain,bl)
    if mirror:
        V=V*np.array([-1,1,1]); F=F[:,::-1]; W=[{mirror_name(k):v for k,v in w.items()} for w in W]
    me=bpy.data.meshes.new(name); me.from_pydata(V.tolist(),[],F.tolist()); me.update()
    ca=me.color_attributes.new('Col','BYTE_COLOR','POINT')
    for i,c in enumerate(C): ca.data[i].color_srgb=(*np.clip(c,0,1),1.0)
    ob=bpy.data.objects.new(name,me); bpy.context.collection.objects.link(ob)
    for i,w in enumerate(W):
        for b,x in w.items():
            g=ob.vertex_groups.get(b) or ob.vertex_groups.new(name=b); g.add([i],x,'REPLACE')
    ob.parent=ARM; md=ob.modifiers.new('arm','ARMATURE'); md.object=ARM
    mat=bpy.data.materials.new('armor_steel'); mat.use_nodes=True; bs=mat.node_tree.nodes['Principled BSDF']
    vc=mat.node_tree.nodes.new('ShaderNodeVertexColor'); vc.layer_name='Col'; mat.node_tree.links.new(vc.outputs['Color'],bs.inputs['Base Color'])
    bs.inputs['Metallic'].default_value=0.6; bs.inputs['Roughness'].default_value=0.45; me.materials.append(mat)
    bpy.context.view_layer.objects.active=ob
    for o in bpy.data.objects: o.select_set(False)
    ob.select_set(True); bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.object.mode_set(mode='OBJECT')
    for pl in ob.data.polygons: pl.use_smooth=True
    try: ob.data.set_sharp_from_angle(angle=math.radians(50))
    except Exception as ex: print('sharp',ex)
    n=len(ob.data.polygons)
    def export(o,path):
        for x in bpy.data.objects: x.select_set(False)
        o.select_set(True); ARM.select_set(True)
        bpy.ops.export_scene.gltf(filepath=path,use_selection=True,export_animations=False,export_skins=True,export_vertex_color='ACTIVE',export_all_vertex_colors=False,export_apply=False)
    export(ob,f'{OUT}/generic_male_plate_{name}.glb')
    lo=ob.copy(); lo.data=ob.data.copy(); bpy.context.collection.objects.link(lo); lo.name=name+'_lod1'
    d=lo.modifiers.new('dec','DECIMATE'); d.ratio=0.45; bpy.context.view_layer.objects.active=lo
    for x in bpy.data.objects: x.select_set(False)
    lo.select_set(True); bpy.ops.object.modifier_move_to_index(modifier='dec',index=0); bpy.ops.object.modifier_apply(modifier='dec')
    n1=len(lo.data.polygons); export(lo,f'{OUT}/generic_male_plate_{name}_lod1.glb')
    TRI[name]={'high':n,'lod1':n1,'ratio':round(n1/n,3)}; print('PIECE',name,n,n1)
    bpy.data.objects.remove(lo); bpy.data.objects.remove(ob)
ONLY=os.environ.get('ONLY','').split(',') if os.environ.get('ONLY') else None
for nm,fn,mr in [('helm',helm,False),('chest',torso,False),('shoulder_L',pauldron_L,False),('shoulder_R',pauldron_L,True),('glove_L',glove_L,False),('glove_R',glove_L,True),
                 ('leg_L',leg_L,False),('leg_R',leg_L,True),('boot_L',boot_L,False),('boot_R',boot_L,True)]:
    if ONLY and nm not in ONLY: continue
    build(nm,fn,mr)
json.dump(TRI,open(f'{OUT}/generic_male_plate_tris.json','w'),indent=1)
