import bpy,sys
from mathutils import Vector
a=sys.argv[sys.argv.index('--')+1:]; bpy.ops.wm.open_mainfile(filepath=a[0])
sc=bpy.context.scene; arm=[o for o in sc.objects if o.type=='ARMATURE'][0]
for o in sc.objects:
  if o.type=='MESH' and not (o.parent==arm and len(o.data.vertices)>1000): o.hide_render=True
sc.render.engine='BLENDER_WORKBENCH'; sc.display.shading.light='STUDIO'; sc.display.shading.color_type='TEXTURE'
W=int(a[3]) if len(a)>3 else 240; sc.render.resolution_x=W; sc.render.resolution_y=int(W*1.25)
cam=bpy.data.objects.new('C',bpy.data.cameras.new('C')); sc.collection.objects.link(cam); sc.camera=cam
cam.data.type='ORTHO'; cam.data.ortho_scale=float(a[4]) if len(a)>4 else 2.3; zc=float(a[5]) if len(a)>5 else 1.0
for act in a[2].split(','):
  if act not in bpy.data.actions: continue
  A=bpy.data.actions[act]; arm.animation_data.action=A; f0,f1=[int(x) for x in A.frame_range]
  for k,t in enumerate((0.05,0.3,0.55,0.8)):
    sc.frame_set(int(f0+t*(f1-f0)))
    for v,loc in enumerate([Vector((0,-6,zc)),Vector((6,0,zc))]):
      cam.location=loc; cam.rotation_euler=(Vector((0,0,zc))-loc).to_track_quat('-Z','Y').to_euler()
      sc.render.filepath=f'{a[1]}_{act}_{k}{v}.png'; bpy.ops.render.render(write_still=True)
