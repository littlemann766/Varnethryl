import json,numpy as np,sys
ext=('arms_up','arms_forward','elbows_140','wrist_twist90','kick','crouch','split','spine_twist','spine_bend','fist','wings_flap','tabard_sway15','tabard_swing')
for g in ('male','female'):
    d=json.load(open(f'/tmp/kr/{g}/stretch_{sys.argv[1]}.json'))['per_pose']
    A=np.array([v for k,v in d.items() if k.endswith('#tex') and k[:-4] not in ext]); E={k[:-4]:v for k,v in d.items() if k.endswith('#tex') and k[:-4] in ext}
    print(g,'ANIM max',A[:,0].max().round(3),'worst per-pose p95',A[:,1].max().round(3),'median p95',np.median(A[:,1]).round(3),'median tris>10%',np.median(A[:,3]))
    print('  ',{k:[round(x,2) for x in v[:2]]+[v[3]] for k,v in E.items()})
