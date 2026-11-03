# v6: connective (band-blended) pieces -> rigid on a mid-joint helper (50% of child rotation): zero texture smear, small end gaps
import bpy,sys,json,numpy as np,collections
from mathutils import Vector
G=sys.argv[-1]; OUT=f'/tmp/kr/{G}'; F=f'{OUT}/stage6.blend'
bpy.ops.wm.open_mainfile(filepath=F)
ARM=bpy.data.objects['knight_rig']; fig=bpy.data.objects[f'knight_{G}']; me=fig.data
gn=[g.name for g in fig.vertex_groups]; PAR={b.name:(b.parent.name if b.parent else None) for b in ARM.data.bones}
pid=np.zeros(len(me.vertices),np.int32); me.attributes['part'].data.foreach_get('value',pid)
W=[{gn[g.group]:g.weight for g in v.groups if g.weight>1e-4} for v in me.vertices]
band=np.array([len(w)>1 for w in W])
parts=np.unique(pid[band]); jobs={}
for p in parts:
    ids=np.where(pid==p)[0]; c=collections.Counter()
    for i in ids:
        for b,x in W[i].items(): c[b.replace('foreArm_twist','foreArm')]+=x
    (a,_),(b,_)=c.most_common(2) if len(c)>1 else (c.most_common(1)[0],c.most_common(1)[0])
    if PAR.get(b)==a: par,ch=a,b
    elif PAR.get(a)==b: par,ch=b,a
    else: par,ch=a,None
    jobs[p]=(ids,par,ch)
need=sorted(set((par,ch) for _,par,ch in jobs.values() if ch))
bpy.context.view_layer.objects.active=ARM
for o in bpy.data.objects: o.select_set(False)
ARM.select_set(True); bpy.ops.object.mode_set(mode='EDIT'); eb=ARM.data.edit_bones
for par,ch in need:
    n='mid_'+ch
    if n in eb: continue
    b=eb.new(n); b.head=eb[ch].head.copy(); b.tail=b.head+Vector((0,0.05,0)); b.roll=0; b.parent=eb[par]; b.use_deform=True
bpy.ops.object.mode_set(mode='OBJECT')
pb=ARM.pose.bones
for par,ch in need:
    n='mid_'+ch; pb[n].rotation_mode='QUATERNION'
    if not pb[n].constraints:
        c=pb[n].constraints.new('COPY_ROTATION'); c.target=ARM; c.subtarget=ch; c.target_space='LOCAL'; c.owner_space='LOCAL'; c.mix_mode='ADD'; c.influence=0.5
    if n not in fig.vertex_groups: fig.vertex_groups.new(name=n)
cnt=collections.Counter()
for p,(ids,par,ch) in jobs.items():
    tgt='mid_'+ch if ch else par
    L=[int(i) for i in ids]
    for g in fig.vertex_groups: g.remove(L)
    fig.vertex_groups[tgt].add(L,1.0,'REPLACE'); cnt[tgt]+=1
bl=np.zeros(len(me.vertices),np.int32); me.attributes['blended'].data.foreach_set('value',bl)
print('MIDRIG parts',len(jobs),'helpers',len(need),dict(cnt))
r=json.load(open(OUT+'/bind3_report.json')); r['midrig']={'parts':len(jobs),'helpers':[f'mid_{c}' for _,c in need]}; json.dump(r,open(OUT+'/bind3_report.json','w'),indent=1)
bpy.ops.wm.save_as_mainfile(filepath=F)
