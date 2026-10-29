import bpy,sys,math,os
from mathutils import Vector
a=sys.argv[sys.argv.index('--')+1:]
blend,clips,outdir,camoff,W,H,N=a[0],a[1].split(','),a[2],[float(x) for x in a[3].split(',')],int(a[4]),int(a[5]),int(a[6])
bpy.ops.wm.open_mainfile(filepath=blend)
sc=bpy.context.scene; arm=[o for o in sc.objects if o.type=='ARMATURE'][0]
sc.render.engine='BLENDER_WORKBENCH'; sc.display.shading.light='STUDIO'; sc.display.shading.color_type='TEXTURE'
sc.display.shading.show_shadows=os.environ.get('SHADOW','0')=='1'; sc.display.shading.show_cavity=False
sc.render.resolution_x=W; sc.render.resolution_y=H; sc.render.film_transparent=False
if sc.world is None: sc.world=bpy.data.worlds.new('W')
sc.world.color=(0.62,0.66,0.72)
cam=bpy.data.objects.new('C',bpy.data.cameras.new('C')); sc.collection.objects.link(cam); sc.camera=cam; cam.data.lens=float(os.environ.get('LENS','40'))
bpy.ops.mesh.primitive_plane_add(size=20); fl=bpy.context.object
m=bpy.data.materials.new('fl'); m.diffuse_color=(0.35,0.37,0.4,1); fl.data.materials.append(m)
for an in clips:
    if an not in bpy.data.actions: continue
    act=bpy.data.actions[an]; arm.animation_data.action=act; f0,f1=[int(x) for x in act.frame_range]
    L=max(1,f1-f0)
    os.makedirs(f'{outdir}/{an}',exist_ok=True)
    tz=1.0 if not an.startswith('fly') else 1.0
    for i in range(N):
        f=f0+(i%L); sc.frame_set(f)
        hp=arm.matrix_world@arm.pose.bones[[b.name for b in arm.pose.bones if b.name.lower().endswith('hips')][0]].head
        tgt=Vector((0,0,hp.z*0.85 if not an.startswith('fly') else hp.z))
        cam.location=tgt+Vector(camoff); d=tgt-cam.location; cam.rotation_euler=d.to_track_quat('-Z','Y').to_euler()
        sc.render.filepath=f'{outdir}/{an}/{i:04d}.png'; bpy.ops.render.render(write_still=True)
