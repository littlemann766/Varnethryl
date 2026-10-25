import bpy,math,sys,re
from mathutils import Vector
files,pref,cams,glow=sys.argv[-4].split(','),sys.argv[-3],sys.argv[-2].split(','),float(sys.argv[-1])
src=open('/tmp/volc/shots.py').read(); exec(re.search(r'^P=dict\(.*$',src,re.M).group(0))
P.update(stage=((-44,-48,88),(0,2,44),20))
bpy.ops.wm.read_factory_settings(use_empty=True)
sc=bpy.context.scene; sc.render.engine='CYCLES'; sc.cycles.samples=32; sc.render.resolution_x=960; sc.render.resolution_y=540; sc.cycles.use_denoising=True
for f in files:
    before=set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=f)
    if 'ashentitan' in f:
        new=[o for o in bpy.data.objects if o not in before and o.parent is None]
        for o in new: o.location=(0,4,39.05); o.rotation_euler=(0,0,math.radians(200))
        for m in bpy.data.materials:
            if m.use_nodes:
                b=next((n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
                if b and b.inputs['Emission Color'].links and 'titan' in str(b.inputs['Emission Color'].links[0].from_node.image.name): b.inputs['Emission Strength'].default_value=glow
w=bpy.data.worlds.new('w'); sc.world=w; w.use_nodes=True; bg=w.node_tree.nodes['Background']; bg.inputs[0].default_value=(0.42,0.45,0.5,1); bg.inputs[1].default_value=0.7
bpy.ops.object.light_add(type='SUN',rotation=(math.radians(55),0,math.radians(-140))); bpy.context.object.data.energy=3.2
bpy.ops.mesh.primitive_plane_add(size=900,location=(0,0,-0.05)); g=bpy.context.object; m=bpy.data.materials.new('g'); m.use_nodes=True; m.node_tree.nodes['Principled BSDF'].inputs[0].default_value=(0.12,0.14,0.08,1); g.data.materials.append(m)
cam=bpy.data.objects.new('c',bpy.data.cameras.new('c')); sc.collection.objects.link(cam); sc.camera=cam
for k in cams:
    loc,tg,lens=P[k]; cam.location=loc; cam.data.lens=lens; cam.data.clip_end=3000
    cam.rotation_euler=(Vector(tg)-Vector(loc)).to_track_quat('-Z','Y').to_euler()
    sc.render.filepath=f'{pref}_{k}.png'; bpy.ops.render.render(write_still=True)
