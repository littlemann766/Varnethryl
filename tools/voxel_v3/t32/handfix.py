import bpy,sys,json,math
import numpy as np
from mathutils import Quaternion,Matrix
a=sys.argv[sys.argv.index('--')+1:]; src,outglb,qjson=a[0],a[1],a[2]; mode=a[3]  # mode: compute|apply
bpy.ops.wm.open_mainfile(filepath=src); sc=bpy.context.scene; sc.render.fps=30; sc.render.fps_base=1
arm=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]
MX='mixamorig:LeftHand' in arm.data.bones
def BN(k,s):
    if MX: return {'hand':'mixamorig:%sHand','fore':'mixamorig:%sForeArm'}[k]%('Left' if s=='L' else 'Right')
    return {'hand':'hand_','fore':'foreArm_'}[k]+s
def rel(s):
    pb=arm.pose.bones[BN('hand',s)]; pf=arm.pose.bones[BN('fore',s)]
    Rr=arm.data.bones[BN('hand',s)].matrix_local.to_3x3(); F0=arm.data.bones[BN('fore',s)].matrix_local.to_3x3()
    return ((F0.inverted()@Rr).inverted()@pf.matrix.to_3x3().inverted()@pb.matrix.to_3x3()).to_quaternion()
def avgq(qs):
    A=np.array([[q.w,q.x,q.y,q.z] for q in qs]); A[A@A[0]<0]*=-1; w,v=np.linalg.eigh(A.T@A); return Quaternion(v[:,-1])
if mode=='compute':
    Q={}
    for act in bpy.data.actions:
        arm.animation_data.action=act; f0,f1=map(int,act.frame_range)
        for s in 'LR':
            qs=[]
            for f in range(f0,f1+1):
                sc.frame_set(f); qs.append(rel(s))
            m=avgq(qs); ang=[math.degrees(q.rotation_difference(Quaternion()).angle) for q in qs]
            ang=[x if x<=180 else 360-x for x in ang]
            dev=[math.degrees(m.rotation_difference(q).angle) for q in qs]; dev=[x if x<=180 else 360-x for x in dev]
            ma=math.degrees(m.angle); ma=ma if ma<=180 else 360-ma
            fix= ma>30 and float(np.percentile(dev,90))<35
            Q.setdefault(act.name,{})[s]={'mean_offset_deg':round(ma,1),'max_wrist_deg':round(max(ang),1),'p90_motion_deg':round(float(np.percentile(dev,90)),1),'fix':bool(fix),'q':list(m)}
    json.dump(Q,open(qjson,'w'),indent=1); sys.exit()
Q=json.load(open(qjson))
for act in bpy.data.actions:
    if act.name not in Q: continue
    sides=[s for s in 'LR' if Q[act.name][s]['fix']]
    if not sides: continue
    arm.animation_data.action=act; f0,f1=map(int,act.frame_range)
    for s in sides:
        Qi=Quaternion(Q[act.name][s]['q']).inverted(); pn=arm.pose.bones[BN('hand',s)].name
        fcs=[act.fcurves.find('pose.bones["%s"].rotation_quaternion'%pn,index=k) for k in range(4)]
        if fcs[0] is None:
            arm.pose.bones[pn].rotation_mode='QUATERNION'; fcs=[act.fcurves.new('pose.bones["%s"].rotation_quaternion'%pn,index=k,action_group=pn) for k in range(4)]
            for k,fc in enumerate(fcs): fc.keyframe_points.insert(f0,[1,0,0,0][k])
        n=len(fcs[0].keyframe_points); assert all(len(fc.keyframe_points)==n for fc in fcs)
        prev=None
        for t in range(n):
            q=Quaternion([fc.keyframe_points[t].co[1] for fc in fcs])@Qi
            if prev is not None and q.dot(prev)<0: q.negate()
            prev=q
            for k,fc in enumerate(fcs): fc.keyframe_points[t].co[1]=q[k]; fc.keyframe_points[t].handle_left[1]=q[k]; fc.keyframe_points[t].handle_right[1]=q[k]
        for fc in fcs: fc.update()
    print('FIXED',act.name,sides)
arm.animation_data.action=bpy.data.actions['idle'] if 'idle' in bpy.data.actions else bpy.data.actions[0]
bpy.ops.wm.save_as_mainfile(filepath=outglb+'.blend')
bpy.ops.export_scene.gltf(filepath=outglb,export_format='GLB',export_animation_mode='ACTIONS',export_force_sampling=True)
