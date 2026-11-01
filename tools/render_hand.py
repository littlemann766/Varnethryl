# render full body + hand close-up (rest pose, idle frame 0) for before/after sheets
import bpy,sys,math
from mathutils import Vector
a=sys.argv[sys.argv.index('--')+1:]; src,outp,cx,cy,cz=a[0],a[1],*map(float,a[2:5])
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
for o in list(bpy.data.objects):
    if o.name.startswith('Icosphere'): bpy.data.objects.remove(o)
sc=bpy.context.scene; sc.render.engine='BLENDER_WORKBENCH'; sc.display.shading.color_type='TEXTURE'; sc.display.shading.light='STUDIO'
sc.render.resolution_x=sc.render.resolution_y=512; sc.render.film_transparent=False
sc.world=bpy.data.worlds.new('w'); sc.display.shading.show_cavity=True
arm=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]
if arm.animation_data: arm.animation_data.action=None
for pb in arm.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
cam=bpy.data.objects.new('c',bpy.data.cameras.new('c')); sc.collection.objects.link(cam); sc.camera=cam
ob=max([o for o in bpy.data.objects if o.type=='MESH'],key=lambda o:len(o.data.vertices))
C=Vector((cx,-cz,cy))
print('MW',ob.matrix_world,arm.matrix_world)
def shoot(target,dist,ortho,name,az):
    cam.data.type='ORTHO'; cam.data.ortho_scale=ortho
    d=Vector((math.sin(az),-math.cos(az),0.25)).normalized()
    cam.location=target+d*dist; cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
    sc.render.filepath=outp+name; bpy.ops.render.render(write_still=True)
shoot(Vector((0,0,1.0)),6,2.4,'_body.png',0.5)
shoot(C,3,0.4,'_handA.png',0.5)
shoot(C,3,0.4,'_handB.png',math.pi+0.5)
