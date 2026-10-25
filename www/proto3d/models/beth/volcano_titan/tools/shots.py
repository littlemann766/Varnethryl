import bpy,math,sys,numpy as np
from mathutils import Vector
f,pref=sys.argv[-2],sys.argv[-1]
bpy.ops.wm.read_factory_settings(use_empty=True)
sc=bpy.context.scene; sc.render.engine='CYCLES'; sc.cycles.samples=32; sc.render.resolution_x=960; sc.render.resolution_y=540
try: sc.cycles.use_denoising=True
except: pass
bpy.ops.import_scene.gltf(filepath=f)
w=bpy.data.worlds.new('w'); sc.world=w; w.use_nodes=True; bg=w.node_tree.nodes['Background']; bg.inputs[0].default_value=(0.42,0.45,0.5,1); bg.inputs[1].default_value=0.7
bpy.ops.object.light_add(type='SUN',rotation=(math.radians(55),0,math.radians(-140))); bpy.context.object.data.energy=3.2
bpy.ops.mesh.primitive_plane_add(size=900,location=(0,0,-0.05)); g=bpy.context.object; m=bpy.data.materials.new('g'); m.use_nodes=True; m.node_tree.nodes['Principled BSDF'].inputs[0].default_value=(0.12,0.14,0.08,1); g.data.materials.append(m)
for o in bpy.data.objects:
    if 'lava' in o.name: pl=bpy.data.lights.new('l','POINT')
cam=bpy.data.objects.new('c',bpy.data.cameras.new('c')); sc.collection.objects.link(cam); sc.camera=cam
P=dict(hero=((-230,-200,40),(0,0,40),28),aerial=((60,-150,260),(0,0,30),30),path=((np.float64(-115.17), np.float64(-81.73), np.float64(3.92)),(np.float64(-69.57), np.float64(-113.95), np.float64(10.42)),18),arena=((-24,24,50),(6,-6,39),18),arenaclose=((-6,6,43),(-38,-14,45),20))
sel=sys.argv[-3].split(',') if len(sys.argv)>3 and ',' in sys.argv[-3] else list(P)
for k in sel:
    if k not in P: continue
    loc,tg,lens=P[k]; cam.location=loc; cam.data.lens=lens; cam.data.clip_end=3000
    cam.rotation_euler=(Vector(tg)-Vector(loc)).to_track_quat('-Z','Y').to_euler()
    sc.render.filepath=f'{pref}_{k}.png'; bpy.ops.render.render(write_still=True)
