import bpy,sys,json
a=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.read_factory_settings(use_empty=True); sc=bpy.context.scene; sc.render.fps=30
bpy.ops.import_scene.gltf(filepath=a[0]); arm=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]
r={}
for act in bpy.data.actions:
    nm=act.name.rsplit('_',2)[0] if act.name.endswith('_Rig') else act.name
    nm=[c for c in a[1].split(',') if act.name.startswith(c+'_') or act.name==c]
    if not nm: continue
    arm.animation_data.action=act; f0,f1=map(int,act.frame_range); mx=0
    for f in range(f0,f1+1):
        sc.frame_set(f); r.setdefault(nm[0],[]).append([list(arm.matrix_world@arm.pose.bones[b].tail) for b in ('hand_L','hand_R')])
json.dump(r,open(a[2],'w'))
