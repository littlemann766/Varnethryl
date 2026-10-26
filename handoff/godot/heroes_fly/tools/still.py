import bpy,sys,math
from mathutils import Vector
a=sys.argv[sys.argv.index('--')+1:]; src,outp=a[0],a[1]; mode=a[2] if len(a)>2 else 'still'
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.context.scene.render.fps=30; bpy.ops.import_scene.gltf(filepath=src)
for o in list(bpy.data.objects):
    if o.type=='MESH' and o.name.lower().startswith('icosphere'): bpy.data.objects.remove(o)
arm=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]
print('ACTS',[x.name for x in bpy.data.actions])
sc=bpy.context.scene; sc.render.engine='BLENDER_WORKBENCH'; sc.display.shading.light='STUDIO'; sc.display.shading.color_type='TEXTURE'
sc.render.resolution_x=480; sc.render.resolution_y=540; sc.render.fps=30
cam=bpy.data.objects.new('cam',bpy.data.cameras.new('c')); sc.collection.objects.link(cam); sc.camera=cam
cam.data.type='ORTHO'
H=2.2
def setcam(view, h):
    tgt=Vector((0,0,h*0.55)); d=6
    if view=='side': pos=tgt+Vector((d,0,0))
    else: pos=tgt+Vector((d*0.7,-d*0.7,d*0.25))
    cam.location=pos; cam.rotation_euler=(tgt-pos).to_track_quat('-Z','Y').to_euler(); cam.data.ortho_scale=h*1.35
import re
cn=lambda n: re.match(r'(fly_(?:bank_[LR]|[a-z]+))',n).group(1)
arm.animation_data_create()
for tr in arm.animation_data.nla_tracks: tr.mute=True
hh=float(a[3]) if len(a)>3 else 1.905
if mode=='close':
    import os
    sc.render.resolution_x=480; sc.render.resolution_y=540; cam.data.type='PERSP'; cam.data.lens=50
    for nm in ('fly_hover','fly_forward','fly_fast','fly_ascend','fly_descend','fly_bank_L','fly_bank_R'):
        act=[x for x in bpy.data.actions if x.name.startswith(nm)][0]; arm.animation_data.action=act; s0,e0=map(int,act.frame_range)
        for fr in range(s0,e0):
            sc.frame_set(fr); pb=arm.pose.bones['upperChest' if 'upperChest' in arm.pose.bones else 'chest']
            tg=arm.matrix_world@pb.head
            for vw,off in (('q34back',Vector((1.1,1.3,0.9))),('top',Vector((0.05,1.6,2.6)))):
                pos=tg+off; cam.location=pos; cam.rotation_euler=(tg-pos).to_track_quat('-Z','Y').to_euler()
                sc.render.filepath=f"{outp}/{nm}_{vw}/f_{fr:04d}.png"; bpy.ops.render.render(write_still=True)
elif mode=='one':
    act=[x for x in bpy.data.actions if x.name.startswith('fly_forward')][0]; arm.animation_data.action=act; sc.frame_set(8)
    sc.render.resolution_x=320; sc.render.resolution_y=320; setcam('q34',hh); cam.data.ortho_scale=hh*1.5; sc.render.filepath=outp; bpy.ops.render.render(write_still=True)
elif mode=='still':
    for act in [x for x in bpy.data.actions if x.name.startswith('fly_')]:
        arm.animation_data.action=act
        fr=int(act.frame_range[1]*0.25); sc.frame_set(fr)
        for v in ('side','q34'):
            setcam(v,hh); sc.render.filepath=f"{outp}_{cn(act.name)}_{v}.png"; bpy.ops.render.render(write_still=True)
else:
    import os
    for act in [x for x in bpy.data.actions if x.name.startswith('fly_')]:
        arm.animation_data.action=act; s,e=map(int,act.frame_range)
        for v in ('side','q34'):
            setcam(v,hh); sc.frame_start=s; sc.frame_end=e-1
            sc.render.image_settings.file_format='PNG'; sc.render.filepath=f"{outp}/{cn(act.name)}_{v}/f_"; bpy.ops.render.render(animation=True)
