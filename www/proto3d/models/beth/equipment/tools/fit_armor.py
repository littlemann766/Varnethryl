# Per-hero bone-local attach transforms + hide rules for Equipment v1 wearable parts. Reads Lucian's rigs (read-only).
import sys,os,json,numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import fit_attach as F; from edata import HERO_FAMILY
from fit_attach import hero_data,place,nrm
def frame(Y,Zh):
    Y=nrm(Y); Z=nrm(Zh-np.dot(Zh,Y)*Y); X=np.cross(Y,Z); return np.c_[X,Y,Z]
def mir(d,s):
    if s=='R': d['scale'][0]=-d['scale'][0]; d['mirror_of']=d.pop('_part')
    else: d.pop('_part')
    return d
VS=0.012
RW={"upperArm":((0.3,0.8),45,(0.035,0.095)),"foreArm":((0.5,0.9),55,(0.035,0.085)),"thigh":((0.4,0.8),55,(0.06,0.125)),"shin":((0.6,0.95),55,(0.045,0.1))}
def limb_info(B,S,dom,b0,b1):
    a=B[b0][:3,3]; c=B[b1][:3,3]; d=c-a; L=float(np.linalg.norm(d)); u=d/L
    (t0,t1),pc,(lo,hi)=RW[b0.split("_")[0]]
    P=S[dom==b0]
    if len(P)==0: return a,c,u,L,(lo+hi)/2
    t=(P-a)@u; m=(t>t0*L)&(t<t1*L)
    if m.sum()<20: return a,c,u,L,(lo+hi)/2
    r=np.linalg.norm(P[m]-(a+np.outer(t[m],u)),axis=1)
    return a,c,u,L,float(np.clip(np.percentile(r,pc),lo,hi))
def fit(h):
    B,vb,S=hero_data(h)
    # dominant bone per vertex again (hero_data hides it): recompute cheaply
    j,acc=F.load(f"{F.VOX}/{h}_voxel.glb"); sk=j['skins'][0]; names=[j['nodes'][i]['name'] for i in sk['joints']]
    mn=[i for i,nd in enumerate(j['nodes']) if 'mesh' in nd][0]; J=[];W=[]
    for p in j['meshes'][j['nodes'][mn]['mesh']]['primitives']:
        J.append(acc(p['attributes']['JOINTS_0']).astype(int)); W.append(acc(p['attributes']['WEIGHTS_0']))
    J=np.vstack(J);W=np.vstack(W); dom=np.array(names)[J[np.arange(len(J)),W.argmax(1)]]
    base=F.fit(h)["slots"]; out={"family":HERO_FAMILY[h],"parts":{},"hide":{}}
    out["parts"]["helmet"]=base["head"]; out["parts"]["chest"]=base["chest"]
    fwd=np.array([0,0,1.]); up=np.array([0,1.,0])
    hip=B["hips"][:3,3]; uL=B["upperArm_L"][:3,3]; uR=B["upperArm_R"][:3,3]
    for s,sg in (("L",1),("R",-1)):
        # shoulder: pauldron on upperArm, world-aligned at rest
        a,c,u,L,r=limb_info(B,S,dom,"upperArm_"+s,"foreArm_"+s); k=float(np.clip((r+0.015)/0.07,0.7,1.5))
        sx=sg*1  # mesh already built per side
        pos=a+np.array([sg*0.015,0.035,0.0]); out["parts"]["shoulder_"+s]=mir({"_part":"shoulder_L","bone":"upperArm_"+s,**place(B["upperArm_"+s],np.eye(3),[k,k,k],pos)},s)
        # glove: forearm, grid +z (glTF +Y) points back to elbow
        a,c,u,L,r=limb_info(B,S,dom,"foreArm_"+s,"hand_"+s); kr=float(np.clip((r+0.006)/0.041,0.6,1.8)); kl=float(np.clip((L+0.04)/0.264,0.5,1.6))
        R=frame(-u,fwd); out["parts"]["glove_"+s]=mir({"_part":"glove_L","bone":"foreArm_"+s,**place(B["foreArm_"+s],R,[kr,kl,kr],a)},s)
        # leg: thigh
        a,c,u,L,r=limb_info(B,S,dom,"thigh_"+s,"shin_"+s); kr=float(np.clip((r+0.006)/0.072,0.6,1.8)); kl=float(np.clip(L/0.408,0.5,1.6))
        R=frame(-u,fwd); out["parts"]["leg_"+s]=mir({"_part":"leg_L","bone":"thigh_"+s,**place(B["thigh_"+s],R,[kr,kl,kr],a+u*0.0)},s)
        # boots: shin + foot
        a,c,u,L,r=limb_info(B,S,dom,"shin_"+s,"foot_"+s); kr=float(np.clip((r+0.006)/0.0576,0.6,1.8)); kl=float(np.clip(L/0.384,0.5,1.6))
        R=frame(-u,fwd); out["parts"]["boot_shin_"+s]=mir({"_part":"boot_shin_L","bone":"shin_"+s,**place(B["shin_"+s],R,[kr,kl,kr],a)},s)
        fa=B["foot_"+s][:3,3]; kw=float(np.clip((r+0.012)/0.054,0.7,1.6)); kz=kw*0.95; kh=float(np.clip(fa[1]/0.096,0.5,1.4))
        out["parts"]["boot_foot_"+s]=mir({"_part":"boot_foot_L","bone":"foot_"+s,**place(B["foot_"+s],np.eye(3),[kw,kh,kz],[fa[0],fa[1],fa[2]-0.02])},s)
    # belt at waist
    yb=hip[1]+0.04; band=S[(np.abs(S[:,1]-yb)<0.03)&(np.isin(dom,["hips","spine","thigh_L","thigh_R"]))]
    if len(band)<10: band=S[np.abs(S[:,1]-yb)<0.04]
    lo=np.percentile(band,3,0); hi=np.percentile(band,97,0); cz=(lo[2]+hi[2])/2
    twb=abs(uL[0]-uR[0]); kx=float(np.clip(min(hi[0]-lo[0]+0.03,twb*0.92)/0.384,0.6,1.5)); kz=float(np.clip(min(hi[2]-lo[2]+0.03,twb*0.62)/0.264,0.6,1.5))
    out["parts"]["belt"]={"bone":"hips",**place(B["hips"],np.eye(3),[kx,1.0,kz],[0.0,yb,cz])}
    # cloak: back of torso, hangs to the knee
    top=max(uL[1],uR[1])+0.02; tb=S[(np.abs(S[:,1]-(top-0.12))<0.05)&(np.isin(dom,["chest","spine"]))]
    zb=float(np.percentile(tb[:,2],3)) if len(tb) else -0.12; tw=abs(uL[0]-uR[0])
    knee=B["shin_L"][:3,3][1]; kl=float(np.clip((top-knee)/0.936,0.4,1.4)); kw=float(np.clip(tw/0.42,0.7,1.6))
    out["parts"]["cloak"]={"bone":"chest",**place(B["chest"],np.eye(3),[kw,kl,kw],[0.0,top,zb-0.015])}
    # ---------------- hide rules (rest-pose model space; vertex selector = dominant bone + region) ----------------
    hb=vb("head"); hs=hb[1]-hb[0]
    eye=hb[0][1]+hs[1]*0.45
    out["hide"]["helmet_full"]=[{"bones":["head"],"aabb":[[float(hb[0][0]+0.01),float(eye),float(hb[0][2]+0.01)],[float(hb[1][0]-0.01),float(hb[1][1]+0.2),float(hb[1][2]-0.01)]],"why":"hair/ears/hat inside a closed helm"},
                                {"bones":["head"],"aabb":[[float(hb[0][0]-0.2),float(hb[1][1]-0.01),float(hb[0][2]-0.2)],[float(hb[1][0]+0.2),float(hb[1][1]+0.6),float(hb[1][2]+0.2)]],"why":"tall hats/hair spikes above the helm"}]
    out["hide"]["helmet_open"]=[out["hide"]["helmet_full"][1],{"bones":["head"],"aabb":[[float(hb[0][0]-0.2),float(eye+hs[1]*0.2),float(hb[0][2]-0.2)],[float(hb[1][0]+0.2),float(hb[1][1]+0.6),float(hb[1][2]+0.2)]],"why":"hair crown under coif/hood"}]
    out["hide"]["cloak"]=[{"bones":[b for b in B if b.startswith("cape")],"aabb":None,"why":"hero's built-in cape replaced by the cloak"}]
    out["hide"]["boots"]=[{"bones":["foot_L","foot_R"],"aabb":None,"why":"bare feet/shoes inside boots"}]
    out["hide"]["gloves"]=[]
    # robe/tabard hem: skirt verts below the knee that sit away from the leg core, so greaves + sabatons show
    kn=float((B["shin_L"][:3,3][1]+B["shin_R"][:3,3][1])/2); rs=max(limb_info(B,S,dom,"shin_L","foot_L")[4],limb_info(B,S,dom,"shin_R","foot_R")[4])
    legs=[[[round(float(x),4) for x in B[a+s][:3,3]],[round(float(x),4) for x in B[b+s][:3,3]]] for s in ("_L","_R") for a,b in (("thigh","shin"),("shin","foot"))]
    skb=sorted(set(dom.tolist())-{"foot_L","foot_R","toe_L","toe_R","hand_L","hand_R","foreArm_L","foreArm_R","head","neck"})
    out["hide"]["robe_hem"]=[{"bones":[b for b in skb if not b.startswith("cape")],"skirt":{"below_y":round(kn+0.06,3),"legs":legs,"keep_radius":round(rs+0.045,3)},"why":"shorten robe/tabard skirt at the knee when leg armour (legs or boots) is worn"}]
    # baked weapons: hand verts far from the fist
    bw=[]
    for s in ("R","L"):
        P=S[dom=="hand_"+s]
        if len(P)==0: continue
        if np.max(P.max(0)-P.min(0))>0.28:
            fc=np.median(P,0) if False else B["hand_"+s][:3,3]
            d=np.linalg.norm(P-fc,axis=1); rad=float(min(0.09,np.percentile(d,25)+0.02))
            bw.append({"bones":["hand_"+s],"sphere_keep":{"center":[round(float(x),4) for x in fc],"radius":round(rad,3)},"why":"built-in weapon on hand_"+s+" (keep fist sphere, collapse the rest) when a main_hand/off_hand item is equipped"})
    out["hide"]["baked_weapon"]=bw
    return out
if __name__=="__main__":
    res={"_note":"Equipment v1 attach transforms (bone-local; basis = Basis(Quaternion(rotation))*Basis.from_scale(scale); origin=position) and hide rules. Hide selectors use the REST pose model-space position of each vertex + its dominant bone; collapse matching vertices (degenerate) at load with MeshDataTool. aabb null = all verts of those bones.","heroes":{}}
    for h in HERO_FAMILY: res["heroes"][h]=fit(h); print(h,len(res["heroes"][h]["parts"]),[x["bones"][0] for x in res["heroes"][h]["hide"]["baked_weapon"]])
    json.dump(res,open(sys.argv[1],"w"),indent=1)
def companion_collar(h,b0,b1,bone,pc=80):
    B,vb,S=hero_data(h); a=B[b0][:3,3]; c=B[b1][:3,3]; d=nrm(c-a); m=(a+c)/2
    t=(S-m)@d; P=S[np.abs(t)<0.03]; r=np.linalg.norm(P-(m+np.outer(t[np.abs(t)<0.03],d)),axis=1); r=r[r<0.2]
    nr=float(np.percentile(r,pc)) if len(r)>10 else 0.06
    k=float(np.clip((nr+0.008)/0.104,0.3,2.0)); R=frame(d,np.array([0,0,1.]))
    return {"bone":bone,"neck_radius_m":round(nr,3),**place(B[bone],R,[k,k,k],m)}
def companions():
    return {"pip":{"collar":companion_collar("pip","spine3","head","neck1"),"note":"fixed: collar now sits on the neck between spine3 and head (was on neck2 at bone origin, inside the head)."},
            "phoenix":{"collar":companion_collar("phoenix","neck1","neck3","neck2",35)}}
if __name__=="__main__" and len(sys.argv)>2:
    json.dump(companions(),open(sys.argv[2],"w"),indent=1); print(companions())
