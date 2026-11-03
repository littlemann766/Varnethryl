import bpy,bmesh,numpy as np
from mathutils import Vector
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath='/workspace/uploads/ref_armor.glb')
o=[x for x in bpy.data.objects if x.type=='MESH'][0]
bpy.context.view_layer.objects.active=o; o.select_set(True)
bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.separate(type='LOOSE'); bpy.ops.object.mode_set(mode='OBJECT')
parts=[x for x in bpy.data.objects if x.type=='MESH']; print('loose parts',len(parts))
L=[];R=[]
for p in parts:
    c=np.mean([v.co[:] for v in p.data.vertices],0); (L if c[0]<2.5 else R).append(p)
def join(ps,name):
    for x in bpy.data.objects: x.select_set(False)
    for p in ps: p.select_set(True)
    bpy.context.view_layer.objects.active=ps[0]; bpy.ops.object.join(); ob=bpy.context.active_object; ob.name=name; return ob
m=join(L,'ref_male'); f=join(R,'ref_female')
for ob in (m,f):
    co=np.array([v.co[:] for v in ob.data.vertices]); print(ob.name,len(ob.data.polygons),co.min(0).round(2),co.max(0).round(2))
    for x in bpy.data.objects: x.select_set(False)
    ob.select_set(True)
    bpy.ops.export_scene.gltf(filepath=f'/workspace/uploads/{ob.name}.glb',use_selection=True,export_image_format='AUTO')
