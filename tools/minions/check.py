import bpy,sys,math,json
import numpy as np
a=sys.argv[sys.argv.index('--')+1:]; blend,out=a[0],a[1]
bpy.ops.wm.open_mainfile(filepath=blend); sc=bpy.context.scene; sc.render.fps=30
arm=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]
me=[o for o in bpy.data.objects if o.type=='MESH' and 'lod1' not in o.name][0]
ARMB=[g.index for g in me.vertex_groups if any(k in g.name for k in ('upperArm','foreArm','hand','fingers'))]
w=np.zeros((len(me.data.vertices),)); 
armv=[v.index for v in me.data.vertices if sum(g.weight for g in v.groups if g.group in ARMB)>0.6]
armv=np.array(armv,dtype=int)
LEGS=[b for b in ('thigh_L','shin_L','thigh_R','shin_R') if b in arm.pose.bones]
R=float(a[2]) if len(a)>2 else 0.09
print('ARMV',len(armv))
res={}
dg=bpy.context.evaluated_depsgraph_get()
for act in bpy.data.actions:
    arm.animation_data.action=act; f0,f1=[int(x) for x in act.frame_range]
    prev=None; maxsnap=(0,'',0); minz=[]; inter=[]
    for f in range(f0,f1+1):
        sc.frame_set(f); dg=bpy.context.evaluated_depsgraph_get()
        ev=me.evaluated_get(dg); m=ev.to_mesh(); co=np.empty(len(m.vertices)*3); m.vertices.foreach_get('co',co); co=co.reshape(-1,3); ev.to_mesh_clear()
        co=co@np.array(me.matrix_world.to_3x3()).T+np.array(me.matrix_world.translation)
        minz.append(float(co[:,2].min()))
        A=co[armv]; n=0
        for b in LEGS:
            pb=arm.pose.bones[b]; h=np.array(arm.matrix_world@pb.head); t=np.array(arm.matrix_world@pb.tail); d=t-h
            u=np.clip(((A-h)@d)/(d@d),0,1); dist=np.linalg.norm(A-(h+np.outer(u,d)),axis=1); n+=int((dist<R).sum())
        inter.append(n)
        q={pb.name:(arm.matrix_world@pb.matrix).to_quaternion() for pb in arm.pose.bones}
        qp={pb.name:(pb.matrix if pb.parent is None else pb.parent.matrix.inverted()@pb.matrix).to_quaternion() for pb in arm.pose.bones}
        if prev is not None:
            for k in qp:
                d=math.degrees(prev[k].rotation_difference(qp[k]).angle)
                if d>180: d=360-d
                if d>maxsnap[0]: maxsnap=(d,k,f)
        prev=qp
    res[act.name]={'frames':f1-f0,'min_z_first':round(minz[0],3),'min_z_min':round(min(minz),3),'min_z_max':round(max(minz),3),'min_z_last':round(minz[-1],3),
      'arm_leg_verts_max':max(inter),'arm_leg_frames':sum(1 for x in inter if x>0),'max_frame_step_deg':round(maxsnap[0],1),'max_step_bone':maxsnap[1],'max_step_frame':maxsnap[2]}
    print('CHK',act.name,res[act.name])
json.dump(res,open(out,'w'),indent=1)
