import bpy,sys,os,math,numpy as np
from mathutils import Quaternion,Vector
G=sys.argv[-1]; OUT=f'/tmp/kr/{G}'; SH='/workspace/shots/knight_rig'
bpy.ops.wm.open_mainfile(filepath=f'{OUT}/stage2.blend')
ARM=bpy.data.objects['knight_rig']; fig=bpy.data.objects[f'knight_{G}']; me=fig.data; ARM.data.pose_position='POSE'
sc=bpy.context.scene
for a in bpy.data.actions:
    for fc in list(a.fcurves) if hasattr(a,'fcurves') else []:
        bn=fc.data_path.split('"')[1] if '"' in fc.data_path else ''
        if (fc.data_path.endswith('location') and bn not in ('hips','root')) or fc.data_path.endswith('scale'): a.fcurves.remove(fc)
# heat colour: stretch (all ~0 -> blue) ; plus bone-id colour layer
worst=np.load(f'{OUT}/worst_v5.npy'); me.calc_loop_triangles()
vs=np.zeros(len(me.vertices))
for t,w in zip(me.loop_triangles,worst):
    for v in t.vertices: vs[v]=max(vs[v],w)
def heat(x):
    x=np.clip(x/0.10,0,1); return np.stack([x,0.25*(1-abs(x-0.5)*2)+0.1,1-x],1)
H=heat(vs); ca=me.color_attributes.new('heat','FLOAT_COLOR','POINT')
for i,c in enumerate(H): ca.data[i].color=(*c,1)
gid=np.zeros(len(me.vertices),int)
for v in me.vertices:
    if len(v.groups): gid[v.index]=max(v.groups,key=lambda g:g.weight).group
rng=np.random.default_rng(3); pal=rng.uniform(0.15,1.0,(len(fig.vertex_groups),3))
cb=me.color_attributes.new('boneid','FLOAT_COLOR','POINT')
for i in range(len(me.vertices)): cb.data[i].color=(*pal[gid[i]],1)
for pb in ARM.pose.bones: pb.rotation_mode='QUATERNION'
ARM.animation_data_create()
def q(ax,deg): return Quaternion(ax,math.radians(deg))
POSES=[('rest',{}),('arms_up',{'upperArm_L':q((0,1,0),-140),'upperArm_R':q((0,1,0),140)}),
 ('elbows_140',{'foreArm_L':q((1,0,0),140),'foreArm_R':q((1,0,0),140)}),
 ('kick',{'thigh_L':q((1,0,0),-95),'shin_L':q((1,0,0),110),'thigh_R':q((1,0,0),30)}),
 ('crouch',{'thigh_L':q((1,0,0),-110),'thigh_R':q((1,0,0),-110),'shin_L':q((1,0,0),130),'shin_R':q((1,0,0),130),'foot_L':q((1,0,0),-30),'foot_R':q((1,0,0),-30)}),
 ('spine_twist',{'spine2':q((0,0,1),25),'chest':q((0,0,1),20),'upperChest':q((0,0,1),15),'neck':q((0,0,1),35),'head':q((0,0,1),35)}),
 ('wings_flap',{f'wing_{X}_0{i}':q((0,1,0),(25 if X=="L" else -25)) for X in 'LR' for i in range(1,5)}),
 ('tabard_swing',{**{f'tabard_F_0{i}':q((1,0,0),-30) for i in (1,2,3)},**{f'tabard_B_0{i}':q((1,0,0),30) for i in (1,2,3)}})]
acts=[a for a in bpy.data.actions if a.name.split('.')[0] in ('walk','attack','attack1','run','hit')]
for a in acts[:3]: POSES.append((a.name.split('.')[0],('ACT',a)))
def setpose(p):
    ARM.animation_data.action=None
    for pb in ARM.pose.bones: pb.location=(0,0,0); pb.rotation_quaternion=(1,0,0,0)
    if isinstance(p,tuple):
        ARM.animation_data.action=p[1]; f0,f1=p[1].frame_range; sc.frame_set(int(f0+(f1-f0)*0.45))
    else:
        for b,qq in p.items():
            if b in ARM.pose.bones: ARM.pose.bones[b].rotation_quaternion=qq
    bpy.context.view_layer.update()
sc.render.resolution_x=420; sc.render.resolution_y=560
cam=bpy.data.objects.new('cam',bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera=cam; cam.data.type='ORTHO'; cam.data.ortho_scale=2.6
w=bpy.data.worlds.new('w'); sc.world=w; w.use_nodes=True; w.node_tree.nodes['Background'].inputs[0].default_value=(0.55,0.57,0.6,1); w.node_tree.nodes['Background'].inputs[1].default_value=0.9
sun=bpy.data.objects.new('sun',bpy.data.lights.new('sun','SUN')); sc.collection.objects.link(sun); sun.rotation_euler=(math.radians(50),0,math.radians(-30)); sun.data.energy=3.5
def look(yaw,tgt=(0,-0.1,1.0),dist=5,el=0.6,size=2.6):
    cam.data.ortho_scale=size; t=Vector(tgt); cam.location=t+Vector((math.sin(math.radians(yaw))*dist,-math.cos(math.radians(yaw))*dist,el)); cam.rotation_euler=(t-cam.location).to_track_quat('-Z','Y').to_euler()
def shot(path):
    sc.render.filepath=path; bpy.ops.render.render(write_still=True)
os.makedirs(SH+'/raw',exist_ok=True)
# deformation heat + bone-id (workbench)
sc.render.engine='BLENDER_WORKBENCH'; sh=sc.display.shading; sh.light='STUDIO'; sh.color_type='VERTEX'
for nm,p in POSES:
    setpose(p)
    for layer in ('heat','boneid'):
        me.color_attributes.active_color=me.color_attributes[layer]
        look(30 if nm not in ('wings_flap','tabard_swing') else 150); shot(f'{SH}/raw/{G}_{nm}_{layer}.png')
# beauty (eevee, textured)
sc.render.engine='BLENDER_EEVEE'
for nm,p in [('rest',{}),('walk',None),('attack',None),('arms_up',POSES[1][1]),('crouch',POSES[4][1])]:
    if p is None:
        aa=[a for a in acts if a.name.startswith(nm)]
        if not aa: continue
        p=('ACT',aa[0])
    setpose(p)
    for yaw,tag in ((20,'front'),(200,'back')):
        look(yaw); shot(f'{SH}/raw/{G}_beauty_{nm}_{tag}.png')
setpose({}); look(15,(0,-0.1,1.62),size=0.75); shot(f'{SH}/raw/{G}_beauty_helm.png')
