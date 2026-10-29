import json,sys
for fam,mf,rf in (('worldboss','meas_s11.json','s11.report.json'),('voxel','meas_vs2.json','vs2.report.json')):
    d=json.load(open(mf)); r=json.load(open(rf))
    for c,info in r.items():
        if c.startswith('_') or c=='wb_walk': continue
        row=[]
        for e in info['effectors']:
            s=e[-1]
            def h(f):
                x=d[c][f]
                return min(x['foot_'+s],x['shin_'+s]) if e.startswith('foot') else min(x['fist_'+s],x['forearm_'+s])
            row.append((e,[h(f) for f in info['hold_frames']]))
        print(fam,c,'impact',info['impact_frame'],info['impact_s'],row)
