# shield orientation per clip: shield = verts bound to LeftHandThumb3. PCA: normal=min axis, long=max axis.
import sys,bpy,numpy as np,json,math
sys.path.insert(0,'/workspace/varn-core/tools/capes'); from lib import *
a=sys.argv[sys.argv.index('--')+1:]
me,arm=load(a[0]); sc=bpy.context.scene; sc.render.fps=30; co,dom=vinfo(me); SB=a[2] if len(a)>2 else 'mixamorig:LeftHandThumb3'
m=dom==SB; W=np.c_[co[m],np.ones(m.sum())]; mw=arm.matrix_world
def fwd():
    hb=arm.pose.bones['mixamorig:Hips']; R=(mw@hb.matrix).to_3x3()@(mw@arm.data.bones['mixamorig:Hips'].matrix_local).to_3x3().inverted()
    f=np.array(R@FWD0); f[2]=0; return f/np.linalg.norm(f)
# rest forward: toe - foot
lt=mw@arm.data.bones['mixamorig:LeftToeBase'].head_local; lf=mw@arm.data.bones['mixamorig:LeftFoot'].head_local; FWD0=(lt-lf); FWD0.z=0; FWD0.normalize()
def meas(P,f,body):
    c=P.mean(0); U,S,Vt=np.linalg.svd(P-c,full_matrices=False); n=Vt[2]; L=Vt[0]
    if np.dot(c-body,n)<0: n=-n   # face away from body
    nf=math.degrees(math.acos(np.clip(np.dot(n,f),-1,1))); lv=math.degrees(math.acos(abs(L[2])))
    return nf,lv,S.round(3).tolist()
res={}
P=co[m]; print('SHM rest fwd',list(FWD0),'normal-vs-fwd,long-vs-vertical,sv',meas(P,np.array(FWD0),np.array(mw@arm.data.bones['mixamorig:Spine1'].head_local)))
for act in sorted(bpy.data.actions,key=lambda x:x.name):
    cl=act.name.split('_'+arm.name)[0]
    if a[1]!='all' and cl not in a[1].split(','): continue
    arm.animation_data.action=act; f0,f1=map(int,act.frame_range); N=[];Lv=[]
    for fr in range(f0,f1+1):
        sc.frame_set(fr); M=np.array(mw@arm.pose.bones[SB].matrix@arm.data.bones[SB].matrix_local.inverted()); P=(M@W.T).T[:,:3]
        nf,lv,_=meas(P,fwd(),np.array(mw@arm.pose.bones['mixamorig:Spine1'].head)); N.append(nf); Lv.append(lv)
    res[cl]={'normal_vs_fwd_med':round(float(np.median(N)),1),'min':round(min(N),1),'max':round(max(N),1),'long_vs_vert_med':round(float(np.median(Lv)),1)}
    print('SHM',cl,res[cl],flush=True)
if len(a)>3: json.dump(res,open(a[3],'w'),indent=1)
