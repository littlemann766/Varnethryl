import bpy,math,sys
from mathutils import Vector
st=int(sys.argv[-2]); pref=sys.argv[-1]
S=1.3362; ROOT={1:26.8,2:21.0,3:18.4}[st]; GLOW={1:1.0,2:2.2,3:4.0}[st]; RING={1:7.0,2:7.0,3:8.0}[st]; YAW=40
bpy.ops.wm.read_factory_settings(use_empty=True)
sc=bpy.context.scene; sc.render.engine='CYCLES'; sc.cycles.samples=32; sc.render.resolution_x=960; sc.render.resolution_y=540; sc.cycles.use_denoising=True
D='/workspace/godot-art/volcano/'
for f in [D+'volcano_titan_lod1.glb',f'/tmp/volc_out/volcano_arena_stage{st}.glb']: bpy.ops.import_scene.gltf(filepath=f)
before=set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=D+'titan/ashentitan_volcano_glow.glb')
new=[o for o in bpy.data.objects if o not in before]
for o in new:
    if o.name.startswith('Icosphere'): o.hide_render=True
for o in new:
    if o.parent is None: o.location=(0,0,ROOT); o.scale=(S,S,S); o.rotation_euler=(0,0,math.radians(YAW))
arm=[o for o in new if o.type=='ARMATURE'][0]
arm.animation_data_create(); arm.animation_data.action=bpy.data.actions['idle']; sc.frame_set(12)
for m in bpy.data.materials:
    if m.use_nodes:
        b=next((n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
        if b and b.inputs['Emission Color'].links:
            n=b.inputs['Emission Color'].links[0].from_node
            if getattr(n,'image',None) and 'titan' in n.image.name: b.inputs['Emission Strength'].default_value=GLOW
before=set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath='/tmp/volc_out/titan_lava_ring.glb')
for o in bpy.data.objects:
    if o not in before: o.location=(0,0,38.03); o.scale=(RING,RING,1)
w=bpy.data.worlds.new('w'); sc.world=w; w.use_nodes=True; bg=w.node_tree.nodes['Background']; bg.inputs[0].default_value=(0.42,0.45,0.5,1); bg.inputs[1].default_value=0.7
bpy.ops.object.light_add(type='SUN',rotation=(math.radians(55),0,math.radians(-140))); bpy.context.object.data.energy=3.2
cam=bpy.data.objects.new('c',bpy.data.cameras.new('c')); sc.collection.objects.link(cam); sc.camera=cam
# landing direction (blender xy) ~ (0.643,-0.766)
P=dict(hero=((22.5,-26.8,56),(0,0,44),17),
       player=((16.1,-19.2,42.6),(0,0,ROOT+20.5),18),
       side=((-24,-12,41.5),(0,0,ROOT+19),18))
for k,(loc,tg,lens) in [(k,P[k]) for k in (sys.argv[-3].split(',') if ',' in sys.argv[-3] or sys.argv[-3] in P else P)]:
    cam.location=loc; cam.data.lens=lens; cam.data.clip_end=3000
    cam.rotation_euler=(Vector(tg)-Vector(loc)).to_track_quat('-Z','Y').to_euler()
    sc.render.filepath=f'{pref}_s{st}_{k}.png'; bpy.ops.render.render(write_still=True)
