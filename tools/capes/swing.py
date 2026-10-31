# max upper-arm abduction (deg, frontal plane, 0 = hanging down) in a clip. usage: blender -b -P swing.py -- f.glb clip
import bpy,sys,math
a=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.context.scene.render.fps=30; bpy.ops.import_scene.gltf(filepath=a[0]); sc=bpy.context.scene
arm=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]; arm.animation_data_create()
act=[x for x in bpy.data.actions if x.name.rsplit('_',2)[0]==a[1]][0]; arm.animation_data.action=act
ua=[b.name for b in arm.pose.bones if 'upperarm' in b.name.lower()]; m={u:0 for u in ua}
for fr in range(int(act.frame_range[0]),int(act.frame_range[1])+1):
    sc.frame_set(fr)
    for u in ua:
        pb=arm.pose.bones[u]; c=[x for x in pb.children if 'arm' in x.name.lower()][0]; d=(arm.matrix_world@c.head)-(arm.matrix_world@pb.head)
        m[u]=max(m[u],math.degrees(math.asin(min(1,abs(d.x)/d.length))))
print('SWING',a[0].split('/')[-1],a[1],{k:round(v,1) for k,v in m.items()})
