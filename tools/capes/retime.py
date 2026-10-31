# Undo the 24fps-import speed-up (clips 1.25x or 1.5625x too fast). usage: blender -b -P retime.py -- in.glb out.glb [walk_frames_target=40]
# factor = target/current walk length (snapped to 1.25^n). Scales every key time of every action; mesh/skin/capes untouched.
import bpy,sys,json,math
a=sys.argv[sys.argv.index('--')+1:]; T=40; REF=a[2] if len(a)>2 else None  # REF = clean glb of same hero (per-clip lengths)
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.context.scene.render.fps=30
RL={}
if REF:
    bpy.ops.import_scene.gltf(filepath=REF); RL={x.name.split('_'+x.name.split('_')[-2]+'_')[0] if False else x.name.rsplit('_',2)[0]:x.frame_range[1] for x in bpy.data.actions}
    bpy.ops.wm.read_factory_settings(use_empty=True); bpy.context.scene.render.fps=30
bpy.ops.import_scene.gltf(filepath=a[0])
w=[x for x in bpy.data.actions if x.name.startswith('walk_')][0]; r=T/w.frame_range[1]
n=round(math.log(r,1.25)); F=1.25**n; print('FACTOR',round(r,4),'->',F)
if n:
    for act in bpy.data.actions:
        cl=act.name.rsplit('_',2)[0]; Fa=(RL[cl]/act.frame_range[1]) if cl in RL and act.frame_range[1]>0 else F
        if abs(Fa/F-1)>0.15: Fa=F
        for fc in act.fcurves:
            for kp in fc.keyframe_points:
                kp.co[0]*=Fa; kp.handle_left[0]*=Fa; kp.handle_right[0]*=Fa
            fc.update()
        act.frame_range=(act.frame_range[0]*F,act.frame_range[1]*F) if act.use_frame_range else act.frame_range
json.dump({'factor':F},open(a[1].replace('.glb','.retime.json'),'w'))
bpy.ops.export_scene.gltf(filepath=a[1],export_format='GLB',export_animation_mode='ACTIONS',export_force_sampling=True,export_yup=True,export_skins=True,export_apply=False)
