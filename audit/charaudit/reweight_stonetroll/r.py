import bpy,math,sys
from mathutils import Vector
clips=['idle','walk','run','attack1','attack2','attack3']
for tag,f in [('before','/workspace/hero-motion/godot-fixed/stonetroll_lod1.glb'),('after','/workspace/hero-motion/beth-reweight/stonetroll_lod1.glb'),('afterHigh','/workspace/hero-motion/beth-reweight/stonetroll.glb'),('afterLod2','/workspace/hero-motion/beth-reweight/stonetroll_lod2.glb')]:
    bpy.ops.wm.read_factory_settings(use_empty=True); sc=bpy.context.scene
    bpy.ops.import_scene.gltf(filepath=f)
    arm=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]
    sc.render.engine='BLENDER_WORKBENCH'; sc.display.shading.light='STUDIO'; sc.display.shading.color_type='TEXTURE'
    sc.render.resolution_x=260; sc.render.resolution_y=300
    cam=bpy.data.objects.new('c',bpy.data.cameras.new('c')); sc.collection.objects.link(cam); sc.camera=cam; cam.data.type='ORTHO'; cam.data.ortho_scale=8
    for c in clips:
        a=bpy.data.actions.get(c); arm.animation_data_create(); arm.animation_data.action=a
        if getattr(a,'slots',None): arm.animation_data.action_slot=a.slots[0]
        r=a.frame_range
        for fr,view in [(0.5,'f'),(0.5,'q')]:
            sc.frame_set(int(r[0]+(r[1]-r[0])*fr))
            cen=Vector((0,0,2.9)); d=Vector((0,-10,0)) if view=='f' else Vector((7,-7,1))
            cam.location=cen+d; cam.rotation_euler=(-d).to_track_quat('-Z','Y').to_euler()
            sc.render.filepath=f'/tmp/rw/{tag}_{c}_{view}.png'; bpy.ops.render.render(write_still=True)
