import json,glob,os,sys
CF='/workspace/godot-art/voxel_cast/cape_fix32/checks/'
def bsum(f):
    if not os.path.exists(f): return None
    d=json.load(open(f)); c=d.get('checks',d)
    return {k:v.get('arm_in_leg',0) for k,v in c.items() if isinstance(v,dict)}
for f in sorted(glob.glob('m33/*_pass2.alfix.json')):
    n=f[4:-17]; p1=json.load(open('m33/%s_pass1.alfix.json'%n)); p2=json.load(open(f))
    bb=bsum(CF+'%s_voxel.before.json'%n) or bsum(CF+'%s_voxel.after.json'%n) or {}
    after={k:v['after_raw_max'] for k,v in p2.items()}
    m=json.load(open('m33/%s_meas.json'%n))['clips']
    ch=json.load(open('m33/%s_check1.json'%n)) if os.path.exists('m33/%s_check1.json'%n) else {}
    cb=max([v.get('cape_in_body_verts_max') or 0 for k,v in ch.items() if k!='rest_baseline'] or [-1])
    line=[n,'beth_before_max',max(bb.values()) if bb else '-', 'sum',sum(bb.values()) if bb else '-','after_max',max(after.values()),'nonzero',{k:v for k,v in after.items() if v},'run abd',round(m['run']['arm_abd_max']),'walk abd',round(m['walk']['arm_abd_max']),'maxflip',max(round(v['flip_max']) for v in m.values()),'cape_in_body',cb]
    for l in sorted(glob.glob('m33/%s_voxel_lod*_lod.alfix.json'%n)):
        L=json.load(open(l)); line+=[l.split('_voxel_')[1][:4],'before',max(v['before_raw_max'] for v in L.values()),'after',max(v['after_raw_max'] for v in L.values())]
    print(*line)
