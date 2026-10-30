# post: build 'jump' (start+loop+land), copy cape curves for new clips from reference clips, then hand-offset fix on new clips
import bpy,sys,json,math
sys.path.insert(0,'/workspace/t32/tools'); from lib import *
a=sys.argv[sys.argv.index('--')+1:]; src,out=a[0],a[1]
bpy.ops.wm.open_mainfile(filepath=src); arm,ob=scene_arm(); A=bpy.data.actions
def concat(name,parts):
    new=A.get(name); 
    if new: A.remove(new)
    new=A.new(name); new.use_fake_user=True; off=0
    for pn in parts:
        P=A[pn]; f0,f1=[int(round(x)) for x in P.frame_range]
        for fc in P.fcurves:
            nf=new.fcurves.find(fc.data_path,index=fc.array_index) or new.fcurves.new(fc.data_path,index=fc.array_index,action_group=fc.group.name if fc.group else '')
            for f in range(f0,f1+1 if pn==parts[-1] else f1):
                p=nf.keyframe_points.insert(off+f-f0,fc.evaluate(f)); p.interpolation='LINEAR'
        off+=(f1-f0)
    return new
concat('jump',['jump_start','jump_loop','jump_land'])
REF={'jump':'fly_ascend','jump_start':'fly_ascend','jump_loop':'fly_ascend','jump_land':'fly_descend','swim_tread':'fly_hover','swim_stroke':'fly_forward'}
caps=[b.name for b in arm.data.bones if b.name.lower().startswith('cape')]
rep={}
for nm,rf in REF.items():
    if nm not in A or rf not in A or not caps: continue
    T=A[nm]; R=A[rf]; t0,t1=[int(round(x)) for x in T.frame_range]; r0,r1=[int(round(x)) for x in R.frame_range]; rn=max(1,r1-r0)
    for fc in list(T.fcurves):
        if any('"%s"'%c in fc.data_path for c in caps): T.fcurves.remove(fc)
    k=0
    for fc in R.fcurves:
        if not any('"%s"'%c in fc.data_path for c in caps): continue
        nf=T.fcurves.new(fc.data_path,index=fc.array_index,action_group=fc.group.name if fc.group else '')
        for f in range(t0,t1+1):
            p=nf.keyframe_points.insert(f,fc.evaluate(r0+((f-t0)*rn/(t1-t0) if nm in('jump','jump_land','jump_start') else (f-t0)%rn))); p.interpolation='LINEAR'
        k+=1
    rep[nm]={'cape_ref':rf,'curves':k}
json.dump(rep,open(out+'.newclips.json','w'),indent=1)
arm.animation_data.action=A.get('idle') or A[0]
bpy.ops.wm.save_as_mainfile(filepath=out)
