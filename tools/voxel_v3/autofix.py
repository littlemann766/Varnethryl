# iterative arm abduction on frames where arm/weapon cells hit leg cells (check1 logic), per side
import bpy,sys,math,os,json
import numpy as np
from mathutils import Matrix
a=sys.argv[sys.argv.index('--')+1:]; blend,acts,out=a[0],a[1].split(','),a[2]
bpy.ops.wm.open_mainfile(filepath=blend); sc=bpy.context.scene; sc.render.fps=30; sc.render.fps_base=1
arm=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]
ob=[o for o in bpy.data.objects if o.type=='MESH' and o.parent==arm and len(o.data.vertices)>1000][0]
me=ob.data; n=len(me.vertices); S=0.018
co=np.empty(n*3); me.vertices.foreach_get('co',co); co=np.c_[co.reshape(-1,3),np.ones(n)]
W=(np.array(ob.matrix_world)@co.T).T
gi=np.array([max(v.groups,key=lambda g:g.weight).group if v.groups else -1 for v in me.vertices])
gname={g.index:g.name for g in ob.vertex_groups}
def cls(nm):
    l=nm.lower().replace('mixamorig:','')
    if l.startswith('cape'): return 'cape'
    if any(t in l for t in ('upperarm','forearm','leftarm','rightarm','hand','fingers','index','middle','ring','pinky','thumb','weapon')): return 'arm'
    if any(t in l for t in ('thigh','shin','foot','toe','upleg','leftleg','rightleg')): return 'leg'
    return 'x'
def side(nm):
    l=nm.lower()
    return 'L' if ('left' in l or l.endswith('_l') or '.l' in l) else ('R' if ('right' in l or l.endswith('_r') or '.r' in l) else '?')
C=np.array([cls(gname.get(g,'')) for g in gi]); SD=np.array([side(gname.get(g,'')) for g in gi])
groups=[(g,nm) for g,nm in gname.items() if nm in arm.pose.bones]
def hits_now():
    P=np.zeros((n,3))
    for g,nm in groups:
        M=np.array(arm.matrix_world@arm.pose.bones[nm].matrix@arm.data.bones[nm].matrix_local.inverted()@arm.matrix_world.inverted())
        idx=gi==g; P[idx]=(M@W[idx].T).T[:,:3]
    T=np.floor(P/S).astype(int)
    legs=set(map(tuple,T[C=='leg']))
    am=np.where(C=='arm')[0]
    h=[i for i in am if tuple(T[i]) in legs]
    return len(h),sum(SD[i]=='L' for i in h),sum(SD[i]=='R' for i in h)
arm.animation_data.action=None
for pb in arm.pose.bones: pb.matrix_basis=Matrix()
bpy.context.view_layer.update(); base=hits_now()[0]
TB=arm.data.bones
UP={'L':[x for x in ('upperArm_L','mixamorig:LeftArm') if x in TB],'R':[x for x in ('upperArm_R','mixamorig:RightArm') if x in TB]}
H='mixamorig:Hips' if 'mixamorig:Hips' in TB else 'hips'
rep={}
for an in acts:
    A=bpy.data.actions[an]; arm.animation_data.action=A; f0,f1=[int(round(x)) for x in A.frame_range]
    ang={s:np.zeros(f1+1) for s in 'LR'}
    orig={}
    for f in range(f0,f1+1):
        sc.frame_set(f); orig[f]={nm:(arm.matrix_world@arm.pose.bones[nm].matrix).copy() for s in 'LR' for nm in UP[s]}
    for it in range(14):
        bad=0; maxh=0
        need={s:np.zeros(f1+1) for s in 'LR'}
        for f in range(f0,f1+1):
            sc.frame_set(f); t,l,r=hits_now(); t=max(0,t-base); maxh=max(maxh,t)
            if t>0:
                bad+=t>24
                if l>0 or (l==0 and r==0): need['L'][f]=1
                if r>0: need['R'][f]=1
        print('IT',an,it,'bad',bad,'max',maxh,flush=True)
        if maxh==0: break
        for s in 'LR':
            nd=need[s]
            for f in range(f0,f1+1):
                if nd[max(f0,f-2):f+3].any(): ang[s][f]+=5
        # smooth and apply
        for f in range(f0,f1+1):
            sc.frame_set(f)
            for s in 'LR':
                k=ang[s][max(f0,f-3):f+4].mean() if ang[s].any() else 0
                for nm in UP[s]:
                    M=orig[f][nm]; h=M.translation
                    hx=(arm.matrix_world@arm.pose.bones[H].head).x
                    sgn=-1 if h.x>hx else 1
                    R=Matrix.Translation(h)@Matrix.Rotation(math.radians(sgn*k),4,'Y')@Matrix.Translation(-h)
                    pb=arm.pose.bones[nm]; pb.matrix=arm.matrix_world.inverted()@R@M
                    bpy.context.view_layer.update()
                    pb.keyframe_insert('rotation_quaternion',frame=f)
    rep[an]={'iters':it,'max_hits':int(maxh),'max_deg':float(max(ang['L'].max(),ang['R'].max()))}
print('AUTOFIX',json.dumps(rep))
bpy.ops.wm.save_as_mainfile(filepath=out)
