import bpy,sys
from collections import Counter
a=sys.argv[sys.argv.index('--')+1:]; bpy.ops.wm.open_mainfile(filepath=a[0])
arm=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]
ob=[o for o in bpy.data.objects if o.type=='MESH' and o.parent==arm and len(o.data.vertices)>1000][0]
me=ob.data; gn={g.index:g.name for g in ob.vertex_groups}
img=[n.image for n in ob.active_material.node_tree.nodes if n.type=='TEX_IMAGE'][0]; W,H=img.size; px=list(img.pixels)
def find(col):
  for y in range(H):
    for x in range(W):
      i=(y*W+x)*4
      if tuple(round(t*255) for t in px[i:i+3])==col: return ((x+.5)/W,(y+.5)/H)
UP=find((99,58,25)); SOLE=find((82,41,16)); print('UV',UP,SOLE)
uvl=me.uv_layers.active.data; FEET={'foot_L','foot_R','toe_L','toe_R'}
ps=[p for p in me.polygons if gn[max(me.vertices[p.vertices[0]].groups,key=lambda q:q.weight).group] in FEET]
zmin=min(min(me.vertices[v].co.z for v in p.vertices) for p in ps); n=0
for p in ps:
  zb=min(me.vertices[v].co.z for v in p.vertices); uv=SOLE if zb<zmin+0.02 else UP
  for l in p.loop_indices: uvl[l].uv=uv
  n+=1
print('RECOLORED',n,'zmin',zmin)
arm.animation_data.action=bpy.data.actions['idle']
bpy.ops.wm.save_as_mainfile(filepath=a[1]+'.blend')
bpy.ops.export_scene.gltf(filepath=a[1],export_format='GLB',export_animation_mode='ACTIONS',export_force_sampling=True)
