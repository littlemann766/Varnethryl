import bpy,sys,math
from mathutils import Vector
args=sys.argv[sys.argv.index('--')+1:]; src,out,clip,fr=args[0],args[1],args[2],int(args[3])
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=src)
arm=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]
if clip=='none':
  arm.animation_data_create(); arm.animation_data.action=None
  for pb in arm.pose.bones: pb.matrix_basis.identity()
else:
  arm.animation_data_create(); arm.animation_data.action=[a for a in bpy.data.actions if a.name.startswith(clip)][0]
sc=bpy.context.scene; sc.frame_set(fr)
cam=bpy.data.objects.new('c',bpy.data.cameras.new('c'));sc.collection.objects.link(cam);cam.location=(6,-14,4);cam.rotation_euler=(math.radians(82),0,math.radians(23));sc.camera=cam
sc.render.engine='BLENDER_WORKBENCH';sc.render.resolution_x=800;sc.render.resolution_y=800;sc.render.filepath=out;bpy.ops.render.render(write_still=True)
