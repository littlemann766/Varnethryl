# Computes per-hero gear attach transforms (bone-local, Godot/glTF space) from Lucian's rigs (read only).
import sys,os,json,numpy as np
sys.path.insert(0,os.path.dirname(__file__)); from gl import load,globals_; import gdata
VOX="/workspace/vmain/voxel"
VS_A=0.012
def nrm(v): v=np.asarray(v,float); return v/np.linalg.norm(v)
def quat(R):
    m=R; t=np.trace(m)
    if t>0: s=np.sqrt(t+1)*2; w=0.25*s; x=(m[2,1]-m[1,2])/s; y=(m[0,2]-m[2,0])/s; z=(m[1,0]-m[0,1])/s
    elif m[0,0]>m[1,1] and m[0,0]>m[2,2]: s=np.sqrt(1+m[0,0]-m[1,1]-m[2,2])*2; w=(m[2,1]-m[1,2])/s; x=0.25*s; y=(m[0,1]+m[1,0])/s; z=(m[0,2]+m[2,0])/s
    elif m[1,1]>m[2,2]: s=np.sqrt(1+m[1,1]-m[0,0]-m[2,2])*2; w=(m[0,2]-m[2,0])/s; x=(m[0,1]+m[1,0])/s; y=0.25*s; z=(m[1,2]+m[2,1])/s
    else: s=np.sqrt(1+m[2,2]-m[0,0]-m[1,1])*2; w=(m[1,0]-m[0,1])/s; x=(m[0,2]+m[2,0])/s; y=(m[1,2]+m[2,1])/s; z=0.25*s
    return [round(float(c),5) for c in (x,y,z,w)]
def hero_data(h):
    j,acc=load(f"{VOX}/{h}_voxel.glb"); G=globals_(j); sk=j['skins'][0]; joints=sk['joints']; names=[j['nodes'][i]['name'] for i in joints]
    IBM=acc(sk['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1)
    mn=[i for i,nd in enumerate(j['nodes']) if 'mesh' in nd][0]; P=[];J=[];W=[]
    for p in j['meshes'][j['nodes'][mn]['mesh']]['primitives']:
        a=p['attributes']; P.append(acc(a['POSITION'])); J.append(acc(a['JOINTS_0']).astype(int)); W.append(acc(a['WEIGHTS_0']))
    P=np.vstack(P);J=np.vstack(J);W=np.vstack(W); ph=np.c_[P,np.ones(len(P))]; S=np.zeros((len(P),3))
    Ms=np.array([G[joints[q]]@IBM[q] for q in range(len(joints))])
    for k in range(4): S+=W[:,k:k+1]*np.einsum('nij,nj->ni',Ms[J[:,k]],ph)[:,:3]
    dom=np.array(names)[J[np.arange(len(J)),W.argmax(1)]]
    B={n:G[joints[i]] for i,n in enumerate(names)}
    def vb(*bs):
        s=S[np.isin(dom,bs)]; return (s.min(0),s.max(0)) if len(s) else None
    return B,vb,S
def place(Gb,R,S,pos):
    # world transform W = [R*S | pos]; local = inv(Gb) W ; return bone-local pos, quat, scale
    Rb=Gb[:3,:3]; sb=np.linalg.norm(Rb,axis=0); Rb=Rb/sb
    lp=Rb.T@(np.asarray(pos)-Gb[:3,3])/sb; lr=Rb.T@R
    return {"position":[round(float(c),4) for c in lp],"rotation":quat(lr),"scale":[round(float(c),4) for c in S]}
def frame(Y,Xhint):
    Y=nrm(Y); X=nrm(Xhint-np.dot(Xhint,Y)*Y); Z=np.cross(X,Y); return np.c_[X,Y,Z]
def fit(h):
    fam,hands,weight,shield=gdata.HEROES[h]; B,vb,S=hero_data(h); out={"weight":weight,"weapon_family":fam,"slots":{}}
    height=S[:,1].max()-S[:,1].min(); out["height_m"]=round(float(height),3)
    ws=float(np.clip(height/1.85,0.75,1.08))
    up=np.array([0,1.,0]); fwd=np.array([0,0,1.])
    if weight=="companion":
        nb=[b for b in ("neck2","neck1","neck3") if b in B][0]; nbox=vb(*[b for b in ("neck1","neck2","neck3") if b in B])
        if nbox is None:
            hbx=vb("head"); c=B[nb][:3,3]; size=float(np.max(hbx[1]-hbx[0]))*0.75
        else: c=(nbox[0]+nbox[1])/2; size=float(np.max(nbox[1]-nbox[0]))
        ch=[b for b in B if b.startswith('head')][0]; d=nrm(B['head'][:3,3]-B[nb][:3,3])
        s=float(np.clip(size*0.42/0.104,0.6,2.0)); R=frame(d,fwd)
        out["slots"]["collar"]={"bone":nb,**place(B[nb],R,[s,s,s],B[nb][:3,3]*0.5+c*0.5)}
        return out
    # head
    hb=vb("head"); hc=(hb[0]+hb[1])/2; hs=hb[1]-hb[0]
    s=0.92*float(np.clip(max((hs[0]+0.03)/0.331,(hs[2]+0.03)/0.355),0.7,1.5))
    hy=hb[0][1]+hs[1]*0.42
    out["slots"]["head"]={"bone":"head",**place(B["head"],np.eye(3),[s,s,s],[0.0 if abs(hc[0])<0.05 else hc[0],hy,hc[2]])}
    # chest
    uL=B["upperArm_L"][:3,3]; uR=B["upperArm_R"][:3,3]; hip=B["hips"][:3,3]
    cb=vb("chest","spine")
    tw=float(np.clip(abs(uL[0]-uR[0])*0.86,0.30,0.62))
    top=max(uL[1],uR[1])+0.035; bot=hip[1]+0.03; th=top-bot
    band=S[(np.abs(S[:,1]-(top-0.14))<0.05)&(np.abs(S[:,0])<tw/3)][:,2]
    zf=float(np.percentile(band,97)); zb=float(np.percentile(band,3))
    dep=float(np.clip(zf-zb+0.03,0.2,0.48)); cz=(zf+zb)/2+0.01
    sx,sy,sz=tw/0.42,th/0.432,dep/0.264
    out["slots"]["chest"]={"bone":"chest",**place(B["chest"],np.eye(3),[sx,sy,sz],[0.0,bot+0.62*th,cz])}
    front=cz+dep/2+0.01
    out["slots"]["trinket"]={"bone":"chest",**place(B["chest"],np.eye(3),[1,1,1],[0.0,top-0.05,front+0.015])}
    def handpos(side):
        hb_=vb("hand_"+side); fb=vb("foreArm_"+side); hd=B["hand_"+side][:3,3]
        fa=(fb[0]+fb[1])/2 if fb is not None else B["foreArm_"+side][:3,3]
        ok=hb_ is not None and np.max(hb_[1]-hb_[0])<0.3
        p=(hb_[0]+hb_[1])/2 if ok else hd; d=nrm(p-fa)
        if not ok: p=hd+d*0.06
        return p,d
    for side in ("R","L"):
        if side not in hands: continue
        p,d=handpos(side); key="weapon" if side==hands[0] else "weapon_offhand"
        if fam in("bow",): R=frame(up,d)
        elif fam=="crossbow": R=frame(up,np.cross(up,fwd)); R=np.c_[R[:,0],R[:,1],R[:,2]]
        elif fam=="knuckles": Z=d; Y=nrm(up-np.dot(up,Z)*Z); X=np.cross(Y,Z); R=np.c_[X,Y,Z]
        else: a=nrm(fwd-np.dot(fwd,d)*d); R=frame(a,np.cross(a,d) if np.linalg.norm(np.cross(a,d))>0.1 else up)
        out["slots"][key]={"bone":"hand_"+side,**place(B["hand_"+side],R,[ws,ws,ws],p)}
    if fam=="lute":   # slung across the back
        th_=np.radians(-30); R=np.array([[np.cos(th_),-np.sin(th_),0],[np.sin(th_),np.cos(th_),0],[0,0,1]])@np.array([[-1,0,0],[0,1,0],[0,0,-1]])
        out["slots"]["weapon"]={"bone":"chest","note":"lute rides on the back; move to hand_R for the strum clip",**place(B["chest"],R,[ws,ws,ws],[0,bot+0.55*th,cz-dep/2-0.06])}
    if shield:
        hd,d=handpos("L"); fb=vb("foreArm_L"); fa=(fb[0]+fb[1])/2 if fb is not None else B["foreArm_L"][:3,3]; c=fa*0.5+hd*0.5
        R=frame(nrm(up-np.dot(up,d)*d),d); s=0.78*ws
        out["slots"]["shield"]={"bone":"foreArm_L",**place(B["foreArm_L"],R,[s,s,s],c+R[:,2]*0.06)}
    p,d=handpos("R"); a=nrm(fwd-np.dot(fwd,d)*d)
    out["slots"]["ring"]={"bone":"hand_R",**place(B["hand_R"],frame(d,a),[ws,ws,ws],p+d*0.02)}
    return out
if __name__=="__main__":
    res={"_note":"Bone-local transforms for BoneAttachment3D children. basis = Basis(Quaternion(rotation)) * Basis.from_scale(scale); origin = position. Computed from each hero's skinned rest pose (vmain/voxel/<id>_voxel.glb, Lucian's rigs, unedited).","heroes":{}}
    for h in gdata.HEROES: res["heroes"][h]=fit(h); print(h,list(res["heroes"][h]["slots"]))
    json.dump(res,open(sys.argv[1],"w"),indent=1)
