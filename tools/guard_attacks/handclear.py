# per clip, find ONE constant wrist offset per hand (rotation about the hand's local X/Z at the wrist) that keeps the
# weapon/shield voxels (hand subtree) out of the leg voxels; constant => no snaps, grip stays consistent through the clip
import bpy,sys,json,math,os
import numpy as np
from mathutils import Quaternion,Vector
a=sys.argv[sys.argv.index('--')+1:]; blend,acts,out=a[0],a[1].split(','),a[2]
bpy.ops.wm.open_mainfile(filepath=blend); sc=bpy.context.scene; sc.render.fps=30
arm=[o for o in sc.objects if o.type=='ARMATURE'][0]
ob=[o for o in sc.objects if o.type=='MESH' and o.parent==arm and len(o.data.vertices)>1000][0]
me=ob.data; n=len(me.vertices); S=0.018
co=np.empty(n*3); me.vertices.foreach_get('co',co); co=np.c_[co.reshape(-1,3),np.ones(n)]
W=(np.array(ob.matrix_world)@co.T).T
gname={g.index:g.name for g in ob.vertex_groups}
gi=np.array([v.groups[0].group if v.groups else -1 for v in me.vertices])
dom=np.array([gname.get(g,'') for g in gi],dtype=object)
def cls(nm):
    l=nm.lower().replace('mixamorig:','')
    if l.startswith('cape'): return 'cape'
    if any(t in l for t in ('upperarm','forearm','leftarm','rightarm','hand','fingers','index','middle','ring','pinky','thumb','weapon')): return 'arm'
    if any(t in l for t in ('thigh','shin','foot','toe','upleg','leftleg','rightleg')): return 'leg'
    return 'body'
C=np.array([cls(x) for x in dom])
P='mixamorig:'
def sub(bn): return {bn}|{c.name for c in arm.data.bones[bn].children_recursive}
HM={s:np.isin(dom,list(sub(P+s+'Hand'))) for s in ('Left','Right')}
AM={s:np.isin(dom,list(sub(P+s+'Arm'))) for s in ('Left','Right')}
def K(Pp):
    k=np.floor(Pp/S).astype(np.int64); return (k[:,0]+4096)*67108864+(k[:,1]+4096)*8192+(k[:,2]+4096)
names=sorted(set(dom)-{''})
def pose():
    Pp=np.zeros((n,3))
    for nm in names:
        if nm not in arm.pose.bones: continue
        M=np.array(arm.matrix_world@arm.pose.bones[nm].matrix@arm.data.bones[nm].matrix_local.inverted()@arm.matrix_world.inverted()); i=dom==nm
        Pp[i]=(M@W[i].T).T[:,:3]
    return Pp
def rotm(axis,ang):
    x,y,z=axis; c,s=math.cos(ang),math.sin(ang); Cc=1-c
    return np.array([[c+x*x*Cc,x*y*Cc-z*s,x*z*Cc+y*s],[y*x*Cc+z*s,c+y*y*Cc,y*z*Cc-x*s],[z*x*Cc-y*s,z*y*Cc+x*s,c+z*z*Cc]])
LIM=int(os.environ.get('WLIM','30')); GR=[(x,z) for x in range(-LIM,LIM+1,15) for z in range(-LIM,LIM+1,15)]
def SW(ax,az):
    qo=Quaternion((1,0,0),math.radians(ax))@Quaternion((0,0,1),math.radians(az)); tw=Quaternion((qo.w,0,qo.y,0)).normalized(); qo=qo@tw.inverted()
    return np.array(qo.to_matrix())
GR.sort(key=lambda t:abs(t[0])+abs(t[1]))
# rest baseline per hand
arm.animation_data.action=None
for pb in arm.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update(); P0=pose(); L0=set(K(P0[C=='leg']))
base={s:int(np.isin(K(P0[AM[s]]),list(L0)).sum()) for s in HM}
res={}
for an in acts:
    act=bpy.data.actions[an]; arm.animation_data.action=act; f1=int(act.frame_range[1])
    frames=[]
    for f in range(0,f1+1):
        sc.frame_set(f); Pp=pose(); legs=np.unique(K(Pp[C=='leg']))
        hd={}
        for s in HM:
            pb=arm.pose.bones[P+s+'Hand']; Mw=arm.matrix_world@pb.matrix
            hd[s]=(np.array(Mw.translation),np.array(Mw.to_3x3()))
        frames.append((Pp,legs,hd))
    res[an]={}
    for s in ('Left','Right'):
        def cost(ax,az):
            tot=[]
            for Pp,legs,hd in frames:
                piv,R=hd[s]; Rl=R@SW(ax,az)@R.T
                Q=Pp[AM[s]].copy(); hm=HM[s][AM[s]]; Q[hm]=(Q[hm]-piv)@Rl.T+piv
                tot.append(max(0,int(np.isin(K(Q),legs).sum())-base[s]))
            return tot
        c0=cost(0,0); best=(max(c0),sum(c0),0,0)
        if max(c0)>8:
            for ax,az in GR[1:]:
                c=cost(ax,az)
                if (max(c),sum(c))<best[:2]: best=(max(c),sum(c),ax,az)
                if max(c)<=8: break
        _,_,ax,az=best
        res[an][s]={'before_max':max(c0),'after_max':best[0],'wrist_offset_deg':{'x':ax,'z':az}}
        if ax or az:
            pn=P+s+'Hand'; qo=Quaternion((1,0,0),math.radians(ax))@Quaternion((0,0,1),math.radians(az))
            tw=Quaternion((qo.w,0,qo.y,0)).normalized(); qo=qo@tw.inverted()  # swing only, no twist about the bone axis
            fcs=[act.fcurves.find(f'pose.bones["{pn}"].rotation_quaternion',index=k) for k in range(4)]
            for t in range(len(fcs[0].keyframe_points)):
                q=Quaternion([fc.keyframe_points[t].co[1] for fc in fcs])@qo
                for k,fc in enumerate(fcs):
                    p=fc.keyframe_points[t]; p.co[1]=q[k]; p.handle_left[1]=q[k]; p.handle_right[1]=q[k]
            for fc in fcs: fc.update()
    print('HC',an,json.dumps(res[an]),flush=True)
json.dump(res,open(out+'.handclear.json','w'),indent=1)
bpy.ops.wm.save_as_mainfile(filepath=out+'.blend')
