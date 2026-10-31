import bpy,sys,math,json
import numpy as np
from mathutils import Vector,Matrix,Euler
a=sys.argv[sys.argv.index('--')+1:]; out=a[0]
bpy.ops.wm.read_factory_settings(use_empty=True)
sc=bpy.context.scene; sc.render.fps=30; sc.render.fps_base=1
D='/workspace/godot-voxel/assets/volcano/worldboss/'
def imp(f,name):
    old=set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=D+f)
    o=[x for x in set(bpy.data.objects)-old if x.type=='MESH'][0]; o.name=name; return o
m0=imp('wb_ember_wisp.glb','ember_wisp'); m1=imp('wb_ember_wisp_lod1.glb','ember_wisp_lod1')
for o in (m0,m1):
    bpy.context.view_layer.objects.active=o; o.select_set(True); bpy.ops.object.transform_apply(location=True,rotation=True,scale=True); o.select_set(False)
def P(x,y,z): return Vector((x,-z,y))
J={'root':(P(0,0,0),P(0,0.2,0)),'core':(P(0,-0.15,0),P(0,0.25,0)),'crown':(P(0,0.25,-0.05),P(0,0.55,-0.1)),'crown2':(P(0,0.55,-0.1),P(0,0.88,-0.2)),
   'flare_L':(P(0.2,0.45,-0.1),P(0.6,0.5,-0.1)),'flare_R':(P(-0.2,0.45,-0.1),P(-0.6,0.5,-0.1)),
   'tail1':(P(0,-0.1,-0.15),P(0,-0.3,-0.45)),'tail2':(P(0,-0.3,-0.45),P(0,-0.43,-0.72)),'tail3':(P(0,-0.43,-0.72),P(0,-0.6,-1.08)),
   'shards':(P(0,0,0),P(0,0.15,0))}
PAR={'core':'root','crown':'core','crown2':'crown','flare_L':'core','flare_R':'core','tail1':'core','tail2':'tail1','tail3':'tail2','shards':'core'}
# shard components from LOD0
def comps(o):
    me=o.data; n=len(me.vertices); par=list(range(n))
    def f(x):
        while par[x]!=x: par[x]=par[par[x]]; x=par[x]
        return x
    for e in me.edges:
        a_,b_=f(e.vertices[0]),f(e.vertices[1])
        if a_!=b_: par[a_]=b_
    g={}
    for i in range(n): g.setdefault(f(i),[]).append(i)
    return list(g.values())
def shardlist(o):
    out=[]
    for c in comps(o):
        co=np.array([o.data.vertices[i].co for i in c]); ctr=co.mean(0)   # blender coords
        r=math.hypot(ctr[0],ctr[1])
        if r>0.5 and abs(ctr[2])<0.2 and len(c)<=40: out.append((ctr,c))
    return out
S0=shardlist(m0); S1=shardlist(m1); print('shards',len(S0),len(S1))
S0.sort(key=lambda s:math.atan2(s[0][1],s[0][0]))
for i,(ctr,c) in enumerate(S0):
    h=Vector(ctr); J[f'shard_{i}']=(h,h+Vector((0,0,0.12))); PAR[f'shard_{i}']='shards'
ad=bpy.data.armatures.new('ember_wisp_Rig'); arm=bpy.data.objects.new('ember_wisp_Rig',ad); sc.collection.objects.link(arm)
bpy.context.view_layer.objects.active=arm; bpy.ops.object.mode_set(mode='EDIT')
for n,(h,t) in J.items():
    b=ad.edit_bones.new(n); b.head=h; b.tail=t; b.roll=0
for n,p in PAR.items(): ad.edit_bones[n].parent=ad.edit_bones[p]
for n in ('root','shards'): ad.edit_bones[n].use_deform=False
bpy.ops.object.mode_set(mode='OBJECT')
BODY=['core','crown','crown2','flare_L','flare_R','tail1','tail2','tail3']
def segd(p,h,t):
    d=t-h; u=max(0,min(1,(p-h).dot(d)/d.length_squared)); return (p-(h+d*u)).length
for o,SL in ((m0,S0),(m1,S1)):
    vg={n:o.vertex_groups.new(name=n) for n in J if n not in ('root','shards')}
    shardv={}
    for ctr,c in SL:
        k=min(range(len(S0)),key=lambda i:(Vector(S0[i][0])-Vector(ctr)).length)
        for v in c: shardv[v]=f'shard_{k}'
    for v in o.data.vertices:
        if v.index in shardv: vg[shardv[v.index]].add([v.index],1.0,'REPLACE'); continue
        d=sorted((segd(v.co,J[n][0],J[n][1]),n) for n in BODY)
        w=[(1/(max(x,0.02)**4),n) for x,n in d[:2]]; s=sum(x for x,_ in w)
        for x,n in w: vg[n].add([v.index],x/s,'REPLACE')
    mod=o.modifiers.new('Armature','ARMATURE'); mod.object=arm; o.parent=arm
arm.rotation_mode='QUATERNION'
# ---------- clips ----------
for pb in arm.pose.bones: pb.rotation_mode='QUATERNION'
ORDER=['root','core','crown','crown2','flare_L','flare_R','tail1','tail2','tail3','shards']+[f'shard_{i}' for i in range(len(S0))]
REST={n:ad.bones[n].matrix_local.copy() for n in ORDER}
def piv(n,rot=Euler((0,0,0)),loc=Vector((0,0,0)),scl=1.0):
    h=REST[n].translation
    return Matrix.Translation(h+Vector(loc))@rot.to_matrix().to_4x4()@Matrix.Scale(scl,4)@Matrix.Translation(-h)
def key(f,L):
    W={}
    for n in ORDER:
        p=PAR.get(n); Dp=W[p] if p else Matrix.Identity(4)
        W[n]=Dp@L.get(n,Matrix.Identity(4))
        pb=arm.pose.bones[n]; Mw=W[n]@REST[n]
        Pm=(W[p]@REST[p]) if p else Matrix.Identity(4); Pr=REST[p] if p else Matrix.Identity(4)
        pb.matrix_basis=(Pr.inverted()@REST[n]).inverted()@Pm.inverted()@Mw
        pb.keyframe_insert('rotation_quaternion',frame=f); pb.keyframe_insert('location',frame=f); pb.keyframe_insert('scale',frame=f)
R=math.radians; NS=len(S0)
def sm(x): x=max(0,min(1,x)); return x*x*(3-2*x)
def base(t,f,lean=0.0,bob=0.08,bobhz=1.0,sway=6,tailamp=12,tailphase=0.0,spin=0.0,shard_r=1.0,crown_s=1.0,flick=0.04,tailstretch=0.0):
    L={}
    z=bob*math.sin(2*math.pi*t*bobhz)
    L['root']=piv('root',loc=(0,0,z))
    L['core']=piv('core',Euler((R(lean),0,0)))
    w=2*math.pi*t*bobhz*2
    L['crown']=piv('crown',Euler((R(sway*math.sin(w)-lean*0.6),R(sway*0.5*math.cos(w)),0)),scl=crown_s*(1+flick*math.sin(w*2)))
    L['crown2']=piv('crown2',Euler((R(sway*1.4*math.sin(w-0.8)-lean*0.5),R(sway*0.7*math.cos(w-0.8)),0)),scl=1+flick*math.sin(w*3))
    for s_,sg in (('L',1),('R',-1)):
        L['flare_'+s_]=piv('flare_'+s_,Euler((0,R(sg*8*math.sin(w+sg)),0)),scl=1+flick*1.5*math.sin(w+sg))
    for i,tb in enumerate(('tail1','tail2','tail3')):
        L[tb]=piv(tb,Euler((R(tailstretch*(i+1)*4),0,R(tailamp*(0.6+0.4*i)*math.sin(w*0.5-i*0.9+tailphase)))))
    L['shards']=piv('shards',Euler((0,0,R(spin))))
    for i in range(NS):
        c=REST[f'shard_{i}'].translation; L[f'shard_{i}']=piv(f'shard_{i}',Euler((0,0,R(360*t+i*40))),loc=Vector((c.x*(shard_r-1),c.y*(shard_r-1),0.04*math.sin(w+i))))
    return L
def clip(name,n,fn,loop):
    act=bpy.data.actions.new(name); act.use_fake_user=True; arm.animation_data_create(); arm.animation_data.action=act
    for f in range(n+1): key(f,fn(f))
    return act
EV={}
# loops: whole cycles so frame 0 == frame n
clip('idle',60,lambda f:base(f/60,f,bob=0.08,bobhz=1,spin=360*f/60),True)
clip('walk',40,lambda f:base(f/40,f,lean=14,bob=0.06,bobhz=1,sway=8,tailamp=16,spin=360*f/40,tailstretch=1.5),True)
clip('run',24,lambda f:base(f/24,f,lean=30,bob=0.05,bobhz=1,sway=10,tailamp=10,spin=360*f/24,shard_r=0.85,crown_s=0.95,tailstretch=4),True)
def attack(f):  # ember lash: windup 0-14 (rear back, flare up), hold to 16, strike 16-20 (lunge), contact 20, recover to 36
    t=f/36; L=base(t,f,bob=0.03,spin=10*f)
    if f<=14: k=sm(f/14); back=0.35*k; up=0.18*k; tilt=-22*k; cs=1+0.25*k
    elif f<=16: back=0.35; up=0.18; tilt=-22; cs=1.25
    elif f<=20: k=((f-16)/4)**2; back=0.35-1.25*k; up=0.18-0.28*k; tilt=-22+60*k; cs=1.25-0.1*k
    else: k=sm((f-20)/16); back=-0.9*(1-k); up=-0.1*(1-k); tilt=38*(1-k); cs=1.15-0.15*k
    L['root']=piv('root',loc=(0,back,up)); L['core']=piv('core',Euler((R(tilt),0,0)),scl=1.0)
    L['crown']=piv('crown',Euler((R(-tilt*0.5),0,0)),scl=cs)
    for i,tb in enumerate(('tail1','tail2','tail3')): L[tb]=piv(tb,Euler((R(tilt*0.2),0,R(6*math.sin(f*0.5-i)))))
    return L
clip('attack',36,attack,False)
EV['attack']={'name':'ember_lash','windup_start_frame':0,'windup_peak_frame':14,'hit_frame':20,'recover_frame':36,'reach_m':1.3,'type':'melee lunge','hit_point_model':[0,0.1,1.25]}
def attack2(f):  # shard burst: windup 0-18 contract + spin up, release 18-21, contact 21, shards return 22-42
    t=f/42
    if f<=18: k=sm(f/18); r=1-0.45*k; spin=f*6+ (k*k)*120; cs=1-0.15*k; up=0.1*k
    elif f<=21: k=(f-18)/3; r=0.55+3.2*k; spin=228+30*k; cs=0.85+0.45*k; up=0.1-0.1*k
    else: k=sm((f-21)/21); r=3.75-2.75*k; spin=258+102*k; cs=1.3-0.3*k; up=0
    L=base(t,f,bob=0.0,spin=spin,shard_r=r,crown_s=cs)
    L['root']=piv('root',loc=(0,0,up))
    return L
clip('attack2',42,attack2,False)
EV['attack2']={'name':'shard_burst','windup_start_frame':0,'windup_peak_frame':18,'hit_frame':21,'recover_frame':42,'type':'aoe ring','aoe_radius_m':2.2,'hit_point_model':[0,0,0]}
def hit(f):
    if f<=3: k=sm(f/3)
    else: k=1-sm((f-3)/9)
    L=base(f/12,f,bob=0,spin=8*f,crown_s=1-0.2*k)
    L['root']=piv('root',loc=(0,0.28*k,0.05*k)); L['core']=piv('core',Euler((R(25*k),0,R(8*k))),scl=1-0.12*k)
    return L
clip('hit',12,hit,False)
HOVER=2.0
def death(f):
    # 0-12 shudder + flicker, 12-32 gravity fall (s=g t^2/2 scaled to land at f=32), 32-38 squash bounce, 38-54 settle + fade
    L=base(min(f,12)/60,f,bob=0,spin=6*min(f,20),crown_s=1.0)
    land=HOVER-float(__import__('os').environ.get('LANDOFF','0.87'))
    if f<=12: z=0.04*math.sin(f*2.2); tilt=0; sq=1; cs=1+0.1*math.sin(f*1.7)
    elif f<=32: k=(f-12)/20; z=-land*k*k; tilt=70*k*k; sq=1; cs=1-0.5*k
    elif f<=38: k=(f-32)/6; z=-land+0.12*math.sin(math.pi*k); tilt=70+8*math.sin(math.pi*k); sq=0.8+0.2*k; cs=0.5-0.1*k
    else: k=sm((f-38)/16); z=-land; tilt=78; sq=1.0-0.12*k; cs=0.4-0.15*k
    L['root']=piv('root',loc=(0,0,z)); L['core']=piv('core',Euler((0,R(tilt),0)),scl=sq)
    L['crown']=piv('crown',Euler((R(-20*(cs<1)),0,0)),scl=max(0.2,cs)); L['crown2']=piv('crown2',scl=max(0.2,cs))
    if f>32:
        k=sm((f-32)/10)
        for i in range(NS):
            c=REST[f'shard_{i}'].translation; L[f'shard_{i}']=piv(f'shard_{i}',Euler((R(90*k),0,R(4*f+i*40))),loc=Vector((c.x*0.4*k,c.y*0.4*k,-0.25*k)))
    return L
clip('death',54,death,False)
land_=HOVER-float(__import__('os').environ.get('LANDOFF','0.87'))
EV['death']={'ground_impact_frame':32,'ground_impact_time':round(32/30,3),'fall_m':round(land_,3),'note':'assumes node at ground+2.0 (world_boss.gd); lands on the ground at f32, small bounce, settles'}
arm.animation_data.action=bpy.data.actions['idle']
json.dump(EV,open(out.replace('.blend','.ev.json'),'w'),indent=1)
json.dump({k:{'speed_mps':v} for k,v in (('walk',2.5),('run',6.0))},open(out.replace('.blend','.speeds.json'),'w'))
bpy.ops.wm.save_as_mainfile(filepath=out)
