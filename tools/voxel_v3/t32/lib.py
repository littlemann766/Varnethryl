import bpy,math
import numpy as np
from mathutils import Matrix,Vector,Quaternion
def scene_arm():
    arm=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]
    ob=[o for o in bpy.data.objects if o.type=='MESH' and o.parent==arm and len(o.data.vertices)>1000]
    return arm,(ob[0] if ob else None)
def resolve(arm):
    TB=arm.data.bones; R={}
    if 'mixamorig:Hips' in TB:
        P='mixamorig:'; R['hips']=P+'Hips'; R['spine']=P+'Spine'
        for s,w in (('L','Left'),('R','Right')):
            R.update({'uarm'+s:P+w+'Arm','farm'+s:P+w+'ForeArm','hand'+s:P+w+'Hand','thigh'+s:P+w+'UpLeg','shin'+s:P+w+'Leg','foot'+s:P+w+'Foot'})
    else:
        R['hips']='hips'; R['spine']='spine'
        for s in 'LR':
            R.update({'uarm'+s:'upperArm_'+s,'farm'+s:'foreArm_'+s,'hand'+s:'hand_'+s,'thigh'+s:'thigh_'+s,'shin'+s:'shin_'+s,'foot'+s:'foot_'+s})
    return {k:v for k,v in R.items() if v in TB}
def sample(arm,act,names=None):
    """armature-space 4x4 per frame for bones (list of Matrix)"""
    sc=bpy.context.scene; arm.animation_data.action=act; f0,f1=[int(round(x)) for x in act.frame_range]
    names=names or [b.name for b in arm.data.bones]; out={n:[] for n in names}
    for f in range(f0,f1+1):
        sc.frame_set(f)
        for n in names: out[n].append(arm.pose.bones[n].matrix.copy())
    return f0,f1,out
def order(arm):
    o=[]
    def w(b): o.append(b.name); [w(c) for c in b.children]
    [w(b) for b in arm.data.bones if not b.parent]
    return o
def fc_quat(act,arm,bn):
    pb=arm.pose.bones[bn]; pb.rotation_mode='QUATERNION'; dp='pose.bones["%s"].rotation_quaternion'%bn
    fcs=[act.fcurves.find(dp,index=k) for k in range(4)]
    if fcs[0] is None: fcs=[act.fcurves.new(dp,index=k,action_group=bn) for k in range(4)]
    return fcs
def write_rot(act,arm,bn,f0,quats):
    """quats: list per frame (from f0). sets/creates keys at integer frames, keeps continuity"""
    fcs=fc_quat(act,arm,bn); prev=None
    qs=[]
    for q in quats:
        q=q.normalized()
        if prev is not None and q.dot(prev)<0: q=-q
        prev=q; qs.append(q)
    for k,fc in enumerate(fcs):
        idx={int(round(p.co[0])):i for i,p in enumerate(fc.keyframe_points)}
        for j,q in enumerate(qs):
            f=f0+j
            if f in idx:
                p=fc.keyframe_points[idx[f]]; p.co[1]=q[k]; p.handle_left[1]=q[k]; p.handle_right[1]=q[k]; p.interpolation='LINEAR'
            else:
                p=fc.keyframe_points.insert(f,q[k]); p.interpolation='LINEAR'
        fc.update()
def basis_from(arm,bn,Mnew,Pnew):
    b=arm.data.bones[bn]
    if b.parent: rel=b.parent.matrix_local.inverted()@b.matrix_local; L=rel.inverted()@Pnew.inverted()@Mnew
    else: L=b.matrix_local.inverted()@Mnew
    return L.to_quaternion()
def apply_world(arm,act,f0,M,changed):
    """M: dict bone->list of armature-space matrices (orig, already modified for 'changed'). recompute bases for changed bones and
    propagate: unchanged children keep basis (so their M must be recomputed by caller if needed)."""
    for bn in order(arm):
        if bn not in changed: continue
        par=arm.data.bones[bn].parent
        qs=[basis_from(arm,bn,M[bn][i],M[par.name][i] if par else None) for i in range(len(M[bn]))]
        write_rot(act,arm,bn,f0,qs)
def fk_child(arm,bn,Mpar_old,Mpar_new,Mold):
    """child keeps local -> new world"""
    return Mpar_new@Mpar_old.inverted()@Mold
def ang(q1,q2):
    d=abs(q1.dot(q2)); d=min(1.0,d); return math.degrees(2*math.acos(d))
