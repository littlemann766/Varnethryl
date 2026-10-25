import bpy,numpy as np,math
from PIL import Image
# radial glow texture: bright molten collar fading out, with splash streaks
N=512; y,x=np.mgrid[0:N,0:N]/(N-1)*2-1; r=np.hypot(x,y); a=np.arctan2(y,x)
rng=np.random.default_rng(5); streak=np.zeros_like(r)
for k,amp in [(9,.5),(17,.3),(31,.2)]: streak+=amp*np.sin(k*a+rng.uniform(0,6))
edge=0.62+0.10*streak
al=np.clip((edge-r)/0.38,0,1)**1.4
heat=np.clip(1-r/edge,0,1)
col=np.stack([np.full_like(r,1.0),0.25+0.55*heat**2,0.03+0.25*heat**4],-1)
img=np.dstack([col,al]); Image.fromarray((img*255).astype(np.uint8)).save('/tmp/volc_out/titan_lava_ring.png')
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_circle_add(vertices=48,radius=1.0,fill_type='TRIFAN'); o=bpy.context.object; o.name='titan_lava_ring'
me=o.data; ul=me.uv_layers.new() if not me.uv_layers else me.uv_layers[0]
for lp in me.loops:
    v=me.vertices[lp.vertex_index].co; ul.data[lp.index].uv=(v.x*0.5+0.5,v.y*0.5+0.5)
m=bpy.data.materials.new('titan_lava_ring'); m.use_nodes=True; nt=m.node_tree; b=nt.nodes['Principled BSDF']
t=nt.nodes.new('ShaderNodeTexImage'); t.image=bpy.data.images.load('/tmp/volc_out/titan_lava_ring.png')
nt.links.new(t.outputs['Color'],b.inputs['Base Color']); nt.links.new(t.outputs['Color'],b.inputs['Emission Color']); nt.links.new(t.outputs['Alpha'],b.inputs['Alpha'])
b.inputs['Emission Strength'].default_value=5.0; b.inputs['Roughness'].default_value=0.6
m.blend_method='BLEND' if hasattr(m,'blend_method') else None
try: m.surface_render_method='BLENDED'
except: pass
o.data.materials.append(m)
bpy.ops.export_scene.gltf(filepath='/tmp/volc_out/titan_lava_ring.glb',export_format='GLB',export_yup=True,export_apply=True)
print('ring tris',len(me.polygons))
