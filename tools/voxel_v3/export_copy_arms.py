import bpy,sys
a=sys.argv[sys.argv.index('--')+1:]; bpy.ops.wm.open_mainfile(filepath=a[0])
# optional: copy upper-arm rotation curves from a LOD0 blend (LOD consistency)
if len(a)>2:
    with bpy.data.libraries.load(a[2]) as (src,dst): dst.actions=list(src.actions)
    names=[A.name for A in bpy.data.actions if A.library is None and not A.name.endswith('.001')]
    for nm in names:
        A=bpy.data.actions[nm]; S=bpy.data.actions.get(nm+'.001')
        if S is None: continue
        for fc in [f for f in S.fcurves if ('upperArm' in f.data_path or 'Arm"' in f.data_path) and 'rotation_quaternion' in f.data_path]:
            old=A.fcurves.find(fc.data_path,index=fc.array_index)
            if old: A.fcurves.remove(old)
            n=A.fcurves.new(fc.data_path,index=fc.array_index,action_group=fc.group.name if fc.group else '')
            n.keyframe_points.add(len(fc.keyframe_points))
            for i,k in enumerate(fc.keyframe_points): n.keyframe_points[i].co=k.co; n.keyframe_points[i].interpolation='LINEAR'
            n.update()
    for nm in names:
        S=bpy.data.actions.get(nm+'.001')
        if S: bpy.data.actions.remove(S)
    print('COPIED')
arm=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]
arm.animation_data.action=bpy.data.actions.get('idle') or bpy.data.actions[0]
bpy.ops.wm.save_as_mainfile(filepath=a[1]+'.blend')
bpy.ops.export_scene.gltf(filepath=a[1],export_format='GLB',export_animation_mode='ACTIONS',export_force_sampling=True)
