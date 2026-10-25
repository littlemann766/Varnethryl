import bpy,math,json
from mathutils import Vector
R=json.load(open('res.json'))
for r in R:
    if not r.get('ua') or not r.get('hand'): continue
    bpy.ops.wm.read_factory_settings(use_empty=True); sc=bpy.context.scene
    bpy.ops.import_scene.gltf(filepath=r['file'])
    arm=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]
    act=bpy.data.actions['run']; arm.animation_data_create(); arm.animation_data.action=act
    if getattr(act,'slots',None): arm.animation_data.action_slot=act.slots[0]
    fr=act.frame_range; mx=0; mxs=0
    for k in range(8):
        sc.frame_set(int(fr[0]+(fr[1]-fr[0])*k/8))
        for ua in (r['ua'],r['ua'].replace('_L','_R')):
          for b in (ua, ua.replace('upperArm','foreArm')):
            if b not in arm.pose.bones: continue
            pb=arm.pose.bones[b]; rest=pb.bone.matrix_local.to_quaternion(); cur=pb.matrix.to_quaternion()
            d=cur@rest.inverted(); ang=math.degrees(d.angle);
            if ang>180: ang=360-ang
            ch=[c for c in pb.children]
            dirv=((ch[0].bone.head_local-pb.bone.head_local) if ch else (pb.bone.tail_local-pb.bone.head_local)).normalized()
            ax=d.axis; tw=abs(ax.dot(dirv))*ang
            mx=max(mx,tw); mxs=max(mxs,ang)
    r['run_max_rot']=round(mxs); r['run_max_twist']=round(mx)
    print(r['name'],r['run_max_rot'],r['run_max_twist'])
json.dump(R,open('res.json','w'),indent=1)
