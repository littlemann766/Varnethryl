import bpy,sys,math
from mathutils import Matrix,Vector,Quaternion
a=sys.argv[sys.argv.index('--')+1:]; src,height,role,out=a[0],float(a[1]),a[2],a[3]
bpy.ops.wm.read_factory_settings(use_empty=True); sc=bpy.context.scene; sc.render.fps=30; sc.render.fps_base=1
bpy.ops.import_scene.gltf(filepath=src)
for o in list(bpy.data.objects):
    if o.name.startswith('Icosphere') or o.type=='EMPTY' and not o.children: pass
for o in list(bpy.data.objects):
    if o.name.startswith('Icosphere'): bpy.data.objects.remove(o)
for act in list(bpy.data.actions): bpy.data.actions.remove(act)
arm=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]
body=[o for o in bpy.data.objects if o.type=='MESH'][0]; body.name='Body'
# unparent from empties, apply transforms, scale to height
for o in (arm,body):
    mw=o.matrix_world.copy(); o.parent=None; o.matrix_world=mw
body.parent=arm; body.matrix_parent_inverse=arm.matrix_world.inverted()
for o in list(bpy.data.objects):
    if o.type=='EMPTY': bpy.data.objects.remove(o)
bpy.context.view_layer.update()
bpy.ops.object.select_all(action='DESELECT')
for o in (arm,body): o.select_set(True)
bpy.context.view_layer.objects.active=arm
bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
bpy.context.view_layer.update()
zs=[(body.matrix_world@v.co).z for v in body.data.vertices]; h0=max(zs)-min(zs); k=height/h0
arm.scale=(k,k,k); bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
bpy.context.view_layer.update()
zs=[(body.matrix_world@v.co).z for v in body.data.vertices]; print('HEIGHT',max(zs)-min(zs),'minz',min(zs))
P='mixamorig:'
bones=arm.data.bones; pbs=arm.pose.bones
for pb in pbs: pb.rotation_mode='QUATERNION'
order=[]
def walk(b):
    order.append(b.name); [walk(c) for c in b.children]
[walk(b) for b in bones if not b.parent]
def R(x=0,y=0,z=0):
    return (Matrix.Rotation(math.radians(z),4,'Z')@Matrix.Rotation(math.radians(y),4,'Y')@Matrix.Rotation(math.radians(x),4,'X'))
def pose(rots,hipoff=Vector()):
    Pm={}
    for n in order:
        b=bones[n]; Rb=b.matrix_local
        if b.parent:
            Rp=b.parent.matrix_local; Pp=Pm[b.parent.name]
            base=Pp@Rp.inverted()@Rb; Q=(Pp@Rp.inverted()).to_quaternion().to_matrix().to_4x4()
        else:
            base=Matrix.Translation(hipoff)@Rb; Q=Matrix()
        r=rots.get(n.replace(P,''))
        if r is not None:
            h=base.translation
            M=Matrix.Translation(h)@Q@r@Q.inverted()@Matrix.Translation(-h)@base
        else: M=base
        Pm[n]=M
        if b.parent: pbs[n].matrix_basis=(Rp.inverted()@Rb).inverted()@Pm[b.parent.name].inverted()@M
        else: pbs[n].matrix_basis=Rb.inverted()@M
def key(f):
    for pb in pbs:
        pb.keyframe_insert('rotation_quaternion',frame=f)
        if pb.parent is None: pb.keyframe_insert('location',frame=f)
S=math.sin; C=math.cos; TAU=2*math.pi
right_attacker=True
def clip(name,n,fn,loop=True):
    act=bpy.data.actions.new(name); act.use_fake_user=True
    arm.animation_data_create(); arm.animation_data.action=act
    for f in range(n+1):
        t=f/n
        rots,hip=fn(t if not loop else t%1.0)
        pose(rots,hip); key(f)
    print('CLIP',name,n)
H=height
def idle(t):
    b=S(TAU*t)
    return {'Spine1':R(x=-1.5*b),'Spine2':R(x=-1*b),'Neck':R(x=1*b),'LeftArm':R(y=2*b,x=-2*b),'RightArm':R(y=-2*b,x=-2*b),
            'LeftForeArm':R(x=-5),'RightForeArm':R(x=-5)},Vector((0,0,-0.004*H*(1-C(TAU*t))/2))
def gait(t,A_th,A_sh,A_arm,A_el,lean,bob):
    p=TAU*t
    th=lambda ph: R(x=-A_th*S(ph))
    sh=lambda ph: R(x=A_sh*max(0,S(ph+math.pi*0.6))+5)
    ft=lambda ph: R(x=-8*S(ph))
    return {'LeftUpLeg':th(p),'RightUpLeg':th(p+math.pi),'LeftLeg':sh(p),'RightLeg':sh(p+math.pi),'LeftFoot':ft(p),'RightFoot':ft(p+math.pi),
            'LeftArm':R(x=A_arm*S(p)),'RightArm':R(x=A_arm*S(p+math.pi)),'LeftForeArm':R(x=-A_el-A_el*0.4*max(0,-S(p))),'RightForeArm':R(x=-A_el-A_el*0.4*max(0,S(p))),
            'Spine':R(x=-lean,z=4*S(p)),'Spine2':R(z=-4*S(p)),'Neck':R(x=lean*0.6)},Vector((0,0,-bob*H*abs(C(p))))
def attack(t):
    # windup 0-0.35 raise right arm overhead, strike 0.35-0.55, recover
    def ease(x): x=min(1,max(0,x)); return x*x*(3-2*x)
    up=ease(t/0.35); dn=ease((t-0.35)/0.18); rec=ease((t-0.65)/0.35)
    ang=-160*up+190*dn; ang*= (1-rec)
    tw=(-18*up+36*dn)*(1-rec)
    lean=(-6*up+14*dn)*(1-rec)
    r={'RightArm':R(x=ang,y=-10*up*(1-rec)),'RightForeArm':R(x=(-40*up+30*dn)*(1-rec)),'Spine1':R(x=-lean*0.5,z=tw*0.5),'Spine2':R(x=-lean*0.5,z=tw*0.5),
       'LeftArm':R(x=(-35*up)*(1-rec)),'LeftForeArm':R(x=-30*(1-rec)*up),
       'LeftUpLeg':R(x=-15*(up)*(1-rec)),'LeftLeg':R(x=20*up*(1-rec)),'RightUpLeg':R(x=10*up*(1-rec)),'RightLeg':R(x=10*up*(1-rec))}
    return r,Vector((0,0,-0.03*H*dn*(1-rec)))
def hit(t):
    e=S(math.pi*min(1,t*1.4))*(1-t)
    return {'Spine1':R(x=10*e),'Spine2':R(x=8*e),'Neck':R(x=12*e),'LeftArm':R(y=10*e),'RightArm':R(y=-10*e),'LeftForeArm':R(x=-20*e),'RightForeArm':R(x=-20*e),'LeftLeg':R(x=10*e),'RightLeg':R(x=10*e)},Vector((0,0.04*H*e,-0.02*H*e))
clip('idle',60,idle)
clip('walk',32,lambda t:gait(t,24,40,16,12,3,0.012))
clip('attack',30,attack,loop=False)
if role=='villain':
    clip('run',20,lambda t:gait(t,32,70,34,60,9,0.02))
    clip('hit',15,hit,loop=False)
arm.animation_data.action=None
for pb in pbs: pb.matrix_basis=Matrix()
bpy.ops.wm.save_as_mainfile(filepath=out+'.blend')
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.export_scene.gltf(filepath=out+'.glb',export_format='GLB',export_animation_mode='ACTIONS',export_force_sampling=True)
