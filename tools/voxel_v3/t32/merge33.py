# base = Beth cape_fix32 glb (mesh, capes, cape curves); motion = my v3 blend actions (non-cape curves); new clips get cape curves from Beth's reference clip
import bpy,sys,json
a=sys.argv[sys.argv.index('--')+1:]; beth,mine,out=a
bpy.ops.wm.read_factory_settings(use_empty=True); sc=bpy.context.scene; sc.render.fps=30; sc.render.fps_base=1
bpy.ops.import_scene.gltf(filepath=beth)
def clean(n):
    for s in ('_Rig','_Armature'):
        if n.endswith(s): n=n[:n.rindex('_',0,len(n)-len(s))] if n.count('_')>=2 and s=='_Rig' else n[:-len(s)]
    return n
arm=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]
for x in list(bpy.data.actions): x.name='B__'+clean(x.name)
with bpy.data.libraries.load(mine) as (fr,to): to.actions=list(fr.actions)
iscape=lambda dp: dp.startswith('pose.bones["capeV') or dp.startswith('pose.bones["cape')
REF={'jump':'fly_ascend','jump_start':'fly_ascend','jump_loop':'fly_ascend','jump_land':'fly_descend','swim_tread':'fly_hover','swim_stroke':'fly_forward'}
rep={}
for M in [x for x in bpy.data.actions if not x.name.startswith('B__')]:
    nm=M.name; Bn=bpy.data.actions.get('B__'+nm); M.use_fake_user=True
    src=Bn if Bn else bpy.data.actions.get('B__'+REF.get(nm,''))
    for fc in list(M.fcurves):
        if iscape(fc.data_path): M.fcurves.remove(fc)
    if src is None: rep[nm]='no cape src'; continue
    t0,t1=[int(round(x)) for x in M.frame_range]; r0,r1=[int(round(x)) for x in src.frame_range]
    for fc in src.fcurves:
        if not iscape(fc.data_path): continue
        nf=M.fcurves.new(fc.data_path,index=fc.array_index,action_group=fc.group.name if fc.group else '')
        for f in range(t0,t1+1):
            if Bn: v=fc.evaluate(f)
            else: v=fc.evaluate(r0+((f-t0)%max(1,r1-r0)))
            p=nf.keyframe_points.insert(f,v); p.interpolation='LINEAR'
    rep[nm]='beth same clip' if Bn else 'beth '+src.name[3:]
for x in [x for x in bpy.data.actions if x.name.startswith('B__')]: bpy.data.actions.remove(x)
for o in list(bpy.data.objects):
    if o.name.startswith('Icosphere'): bpy.data.objects.remove(o)
arm.animation_data.action=bpy.data.actions.get('idle') or bpy.data.actions[0]
print('MERGE',json.dumps(rep)); json.dump(rep,open(out+'.merge.json','w'),indent=1)
bpy.ops.wm.save_as_mainfile(filepath=out)
