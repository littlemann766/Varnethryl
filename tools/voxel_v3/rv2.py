import bpy,sys,os
from mathutils import Vector
a=sys.argv[sys.argv.index('--')+1:]; blend,an,outdir,reps=a[0],a[1],a[2],int(a[3])
bpy.ops.wm.open_mainfile(filepath=blend); sc=bpy.context.scene; sc.render.fps=30
arm=[o for o in sc.objects if o.type=='ARMATURE'][0]
for o in list(sc.objects):
    if o.type=='MESH' and o.parent!=arm: bpy.data.objects.remove(o)
sc.render.engine='BLENDER_WORKBENCH'; sh=sc.display.shading
sh.light='STUDIO'; sh.color_type='TEXTURE'; sh.show_shadows=True; sh.shadow_intensity=0.35; sh.show_cavity=False; sh.show_backface_culling=False
sc.display.render_aa='8'; sh.background_type='WORLD'
if sc.world is None: sc.world=bpy.data.worlds.new('W')
sc.world.color=(0.55,0.62,0.72)
sc.render.resolution_x=1280; sc.render.resolution_y=720; sc.view_settings.view_transform='Standard'
bpy.ops.mesh.primitive_plane_add(size=60); fl=bpy.context.object
m=bpy.data.materials.new('fl'); m.diffuse_color=(0.42,0.44,0.40,1); fl.data.materials.append(m); sh.color_type='TEXTURE'
cam=bpy.data.objects.new('C',bpy.data.cameras.new('C')); sc.collection.objects.link(cam); sc.camera=cam; cam.data.lens=50
A=bpy.data.actions[an]; arm.animation_data.action=A; f0,f1=[int(round(x)) for x in A.frame_range]
H=[b.name for b in arm.pose.bones if b.name.lower().endswith('hips')][0]
hp=[]
for f in range(f0,f1+1): sc.frame_set(f); hp.append((arm.matrix_world@arm.pose.bones[H].head).copy())
cx=sum(p.x for p in hp)/len(hp); cy=sum(p.y for p in hp)/len(hp)
os.makedirs(outdir,exist_ok=True); i=0
for r in range(reps):
    for f in range(f0,f1+1):
        sc.frame_set(f)
        t=Vector((hp[f-f0].x if an in('walk','run') else cx, hp[f-f0].y if an in('walk','run') else cy, 0.95))
        cam.location=t+Vector((3.0,-5.3,1.0)); cam.rotation_euler=(t-cam.location).to_track_quat('-Z','Y').to_euler()
        sc.render.filepath=f'{outdir}/{i:04d}.png'; bpy.ops.render.render(write_still=True); i+=1
