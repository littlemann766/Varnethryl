# Minimal prep of the ORIGINAL frost troll A (varn-core 9e6ad07): drop stray Icosphere + old Darius rig, bake transforms, scale to 5.715 m, feet at origin. Geometry/UVs/material untouched.
import bpy,sys,numpy as np
src,dst=sys.argv[-2],sys.argv[-1]
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=src)
for o in list(bpy.data.objects):
    if o.name.startswith('Icosphere'): bpy.data.objects.remove(o)
m=[o for o in bpy.data.objects if o.type=='MESH'][0]; mw=m.matrix_world.copy(); m.parent=None; m.modifiers.clear()
for vg in list(m.vertex_groups): m.vertex_groups.remove(vg)
m.data.transform(mw); m.matrix_world.identity()
for o in list(bpy.data.objects):
    if o.type=='ARMATURE': bpy.data.objects.remove(o)
for a in list(bpy.data.actions): bpy.data.actions.remove(a)
P=np.array([v.co[:] for v in m.data.vertices]); lo,hi=P.min(0),P.max(0); k=5.715/(hi[2]-lo[2])
from mathutils import Matrix,Vector
m.data.transform(Matrix.Scale(k,4)@Matrix.Translation(Vector((-(lo[0]+hi[0])/2,-(lo[1]+hi[1])/2,-lo[2]))))
P=np.array([v.co[:] for v in m.data.vertices]);print('PREP scale',round(k,4),'bb',P.min(0).round(2),P.max(0).round(2),len(P))
bpy.ops.export_scene.gltf(filepath=dst,export_format='GLB')
