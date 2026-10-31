import bpy,sys,math
from mathutils import Vector
a=sys.argv[sys.argv.index('--')+1:]; out=a[0]
bpy.ops.wm.read_factory_settings(use_empty=True)
sc=bpy.context.scene; sc.render.fps=30; sc.render.fps_base=1
D='/workspace/godot-voxel/assets/volcano/worldboss/'
def imp(f,name):
    old=set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=D+f)
    o=[x for x in set(bpy.data.objects)-old if x.type=='MESH'][0]; o.name=name; return o
m0=imp('wb_ash_fiend.glb','ash_fiend'); m1=imp('wb_ash_fiend_lod1.glb','ash_fiend_lod1')
for o in (m0,m1):
    bpy.context.view_layer.objects.active=o; o.select_set(True); bpy.ops.object.transform_apply(location=True,rotation=True,scale=True); o.select_set(False)
# gltf (x,y,z) -> blender (x,-z,y)
def P(x,y,z): return Vector((x,-z,y))
J={'root':(P(0,0,0),P(0,0.25,0)),
 'hips':(P(0,0.92,0.02),P(0,1.12,0.02)),'spine':(P(0,1.12,0.02),P(0,1.32,0.05)),'spine2':(P(0,1.32,0.05),P(0,1.52,0.07)),
 'chest':(P(0,1.52,0.07),P(0,1.80,0.07)),'neck':(P(0,1.80,0.08),P(0,1.97,0.28)),'head':(P(0,1.97,0.28),P(0,2.30,0.32))}
for s,k in (('L',1),('R',-1)):
    J.update({'shoulder_'+s:(P(k*0.10,1.74,0.05),P(k*0.56,1.73,0.04)),'upperArm_'+s:(P(k*0.56,1.73,0.04),P(k*0.88,1.30,0.08)),
     'foreArm_'+s:(P(k*0.88,1.30,0.08),P(k*1.15,0.94,0.14)),'hand_'+s:(P(k*1.15,0.94,0.14),P(k*1.20,0.86,0.15)),
     'fingers_'+s:(P(k*1.20,0.86,0.15),P(k*1.24,0.78,0.16)),
     'thigh_'+s:(P(k*0.21,0.90,0.03),P(k*0.265,0.50,0.10)),'shin_'+s:(P(k*0.265,0.50,0.10),P(k*0.295,0.12,-0.04)),
     'foot_'+s:(P(k*0.295,0.12,-0.04),P(k*0.30,0.04,0.12)),'toe_'+s:(P(k*0.30,0.04,0.12),P(k*0.30,0.03,0.20))})
PAR={'hips':'root','spine':'hips','spine2':'spine','chest':'spine2','neck':'chest','head':'neck'}
for s in 'LR':
    PAR.update({'shoulder_'+s:'chest','upperArm_'+s:'shoulder_'+s,'foreArm_'+s:'upperArm_'+s,'hand_'+s:'foreArm_'+s,'fingers_'+s:'hand_'+s,
                'thigh_'+s:'hips','shin_'+s:'thigh_'+s,'foot_'+s:'shin_'+s,'toe_'+s:'foot_'+s})
ad=bpy.data.armatures.new('ash_fiend_Rig'); arm=bpy.data.objects.new('ash_fiend_Rig',ad); sc.collection.objects.link(arm)
bpy.context.view_layer.objects.active=arm; bpy.ops.object.mode_set(mode='EDIT')
for n,(h,t) in J.items():
    b=ad.edit_bones.new(n); b.head=h; b.tail=t; b.roll=0
for n,p in PAR.items():
    b=ad.edit_bones[n]; b.parent=ad.edit_bones[p]; b.use_connect=False
ad.edit_bones['root'].use_deform=False
bpy.ops.object.mode_set(mode='OBJECT')
for o in (m0,m1):
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); arm.select_set(True); bpy.context.view_layer.objects.active=arm
    bpy.ops.object.parent_set(type='ARMATURE_AUTO')
    print('weights',o.name,len(o.vertex_groups),sum(1 for v in o.data.vertices if len(v.groups)==0))
def segd(p,h,t):
    d=t-h; u=max(0,min(1,(p-h).dot(d)/d.length_squared)); return (p-(h+d*u)).length
DEF=[n for n in J if n!='root']
for o in (m0,m1):
    vg={g.name:g for g in o.vertex_groups}
    for v in o.data.vertices:
        tot=sum(g.weight for g in v.groups)
        if tot<1e-3:
            best=min(DEF,key=lambda n:segd(v.co,J[n][0],J[n][1])); vg[best].add([v.index],1.0,'REPLACE')
    bpy.context.view_layer.objects.active=o
    bpy.ops.object.vertex_group_limit_total(group_select_mode='ALL',limit=4)
    bpy.ops.object.vertex_group_normalize_all(lock_active=False)
    print('fixed',o.name,sum(1 for v in o.data.vertices if sum(g.weight for g in v.groups)<1e-3))
bpy.ops.wm.save_as_mainfile(filepath=out)
