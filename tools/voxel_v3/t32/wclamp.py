# clamp hand rotation (relative to rest) to MAXD deg in given clips by slerp toward rest; weapon stays parented to hand -> grip kept
import bpy,sys,json,math,os
from mathutils import Quaternion
a=sys.argv[sys.argv.index('--')+1:]; src,out=a[0],a[1]; CL=os.environ['CL'].split(','); MAXD=float(os.environ.get('MAXD','45')); BS=os.environ.get('BONES','hand_L,hand_R').split(',')
if src.endswith('.blend'): bpy.ops.wm.open_mainfile(filepath=src)
else:
    bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=src)
    for x in list(bpy.data.actions): x.name=x.name[:x.name.rindex('_',0,x.name.rindex('_'))] if x.name.count('_')>=2 and x.name.endswith('_Rig') else (x.name[:-9] if x.name.endswith('_Armature') else x.name)
sc=bpy.context.scene; sc.render.fps=30; sc.render.fps_base=1
arm=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]; rep={}
for act in bpy.data.actions:
    if act.name not in CL: continue
    for bn in BS:
        if bn not in arm.pose.bones: continue
        fcs=[act.fcurves.find('pose.bones["%s"].rotation_quaternion'%bn,index=k) for k in range(4)]
        if any(f is None for f in fcs): continue
        n=len(fcs[0].keyframe_points); b4=af=0
        for t in range(n):
            q=Quaternion([fcs[k].keyframe_points[t].co[1] for k in range(4)]); 
            if q.w<0: q.negate()
            d=math.degrees(q.angle); b4=max(b4,d)
            if d>MAXD: q=Quaternion().slerp(q,MAXD/d)
            af=max(af,math.degrees(q.angle))
            for k in range(4):
                p=fcs[k].keyframe_points[t]; p.co[1]=q[k]; p.handle_left[1]=q[k]; p.handle_right[1]=q[k]
        for f in fcs: f.update()
        rep['%s/%s'%(act.name,bn)]=[round(b4,1),round(af,1)]
print('WCLAMP',json.dumps(rep)); json.dump(rep,open(out+'.wclamp.json','w'),indent=1)
for o in list(bpy.data.objects):
    if o.name.startswith('Icosphere'): bpy.data.objects.remove(o)
for x in bpy.data.actions: x.use_fake_user=True
arm.animation_data.action=bpy.data.actions.get('idle') or bpy.data.actions[0]
bpy.ops.wm.save_as_mainfile(filepath=out+'.blend')
bpy.ops.export_scene.gltf(filepath=out,export_format='GLB',export_animation_mode='ACTIONS',export_force_sampling=True)
