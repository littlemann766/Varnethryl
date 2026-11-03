import bpy,sys,os,math,numpy as np
from mathutils import Quaternion,Vector
G=sys.argv[-2]; STG=sys.argv[-1]; OUT=f'/tmp/kr/{G}'; RAW=f'/tmp/kr/bt_{G}_{STG}'; os.makedirs(RAW,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=f'{OUT}/{STG}.blend')
ARM=bpy.data.objects['knight_rig']; fig=bpy.data.objects[f'knight_{G}']; me=fig.data; ARM.data.pose_position='POSE'; sc=bpy.context.scene
for a in bpy.data.actions:
    for fc in list(a.fcurves) if hasattr(a,'fcurves') else []:
        bn=fc.data_path.split('"')[1] if '"' in fc.data_path else ''
        if (fc.data_path.endswith('location') and bn not in ('hips','root')) or fc.data_path.endswith('scale'): a.fcurves.remove(fc)
exec(open('/tmp/kr/mat.py').read()); setup_mat(me)
for pb in ARM.pose.bones: pb.rotation_mode='QUATERNION'
ARM.animation_data_create()
def q(ax,deg): return Quaternion(ax,math.radians(deg))
exec(open('/tmp/kr/poses_ext.py').read())
acts={a.name.split('.')[0]:a for a in bpy.data.actions}
def setpose(nm):
    ARM.animation_data.action=None
    for pb in ARM.pose.bones: pb.location=(0,0,0); pb.rotation_quaternion=(1,0,0,0)
    if nm in EXT:
        for b,qq in EXT[nm].items():
            if b in ARM.pose.bones: ARM.pose.bones[b].rotation_quaternion=qq
    elif nm!='rest':
        k=[x for x in acts if x.startswith(nm)]
        if k: a=acts[k[0]]; ARM.animation_data.action=a; f0,f1=a.frame_range; sc.frame_set(int(f0+(f1-f0)*float(__import__('os').environ.get('FR','0.45'))))
    bpy.context.view_layer.update()
sc.render.engine='BLENDER_EEVEE'; sc.eevee.taa_render_samples=24; sc.view_settings.view_transform='Standard'; sc.render.resolution_x=360; sc.render.resolution_y=480
cam=bpy.data.objects.new('cam',bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera=cam; cam.data.type='ORTHO'
w=bpy.data.worlds.new('w'); sc.world=w; w.use_nodes=True; w.node_tree.nodes['Background'].inputs[0].default_value=(0.55,0.57,0.6,1); w.node_tree.nodes['Background'].inputs[1].default_value=0.9
sun=bpy.data.objects.new('sun',bpy.data.lights.new('sun','SUN')); sc.collection.objects.link(sun); sun.rotation_euler=(math.radians(50),0,math.radians(-30)); sun.data.energy=3.5
def look(yaw,tgt,size,dist=5,el=0.6):
    cam.data.ortho_scale=size; t=Vector(tgt); cam.location=t+Vector((math.sin(math.radians(yaw))*dist,-math.cos(math.radians(yaw))*dist,el)); cam.rotation_euler=(t-cam.location).to_track_quat('-Z','Y').to_euler()
SH=[(n,y,(0,-0.1,1.0),2.6) for n in ('idle','walk','run','attack','hit','death') for y in (30,110)]
for i,(nm,yaw,tg,sz) in enumerate(SH):
    setpose(nm); look(yaw,tg,sz); sc.render.filepath=f'{RAW}/{i:02d}_{nm}_{yaw}.png'; bpy.ops.render.render(write_still=True)
