"""Move the arms-down offset Rd from upperArm onto shoulder (for rigs whose arm skin is weighted mostly to shoulder).
upper' = Rd^-1 * upper ; shoulder' = Rd (shoulder rest is identity, unanimated or replaced). usage: in.glb out.glb"""
import sys, numpy as np; sys.path.insert(0, __file__.rsplit('/',1)[0]); import fix_arms as f
g = f.GLB(sys.argv[1]); N = g.j['nodes']; by = {n.get('name'): i for i, n in enumerate(N)}
for an in g.j['animations']:
    for s in 'LR':
        cu = [c for c in an['channels'] if c['target'].get('node') == by['upperArm_'+s] and c['target']['path'] == 'rotation']
        if not cu: continue
        cu = cu[0]
        smp = an['samplers'][cu['sampler']]; q = g.read(smp['output'])
        Rd = q[0] if an['name'] == 'idle' else None
        # Rd is the swing-free part: recover by removing twist about world X
        tw = q.copy(); tw[:, 1:3] = 0; tw /= np.linalg.norm(tw, axis=1, keepdims=True)
        Rd = f.qmul(f.qinv(tw), q)            # q = Rx(th)·Rd
        Rd0 = Rd.mean(0); Rd0 /= np.linalg.norm(Rd0)
        nu = f.qmul(f.qmul(np.repeat(f.qinv(Rd0)[None], len(q), 0), q), np.repeat(f.qinv(Rd0)[None], len(q), 0)) if False else f.qmul(np.repeat(f.qinv(Rd0)[None], len(q), 0), f.qmul(q, np.repeat(f.qinv(Rd0)[None], len(q), 0)))
        nu = f.qmul(nu, np.repeat(Rd0[None], len(q), 0))  # = Rd^-1 Rx Rd : swing about world X expressed under shoulder
        smp['output'] = g.add(nu)
        cs = [c for c in an['channels'] if c['target'].get('node') == by['shoulder_'+s] and c['target']['path'] == 'rotation']
        inp = smp['input']
        if cs: sq = g.read(an['samplers'][cs[0]['sampler']]['output']); an['samplers'].append({'input': an['samplers'][cs[0]['sampler']]['input'], 'output': g.add(f.qmul(sq, np.repeat(Rd0[None], len(sq), 0)))}); cs[0]['sampler'] = len(an['samplers'])-1
        else: an['samplers'].append({'input': inp, 'output': g.add(np.repeat(Rd0[None], g.j['accessors'][inp]['count'], 0))}); an['channels'].append({'sampler': len(an['samplers'])-1, 'target': {'node': by['shoulder_'+s], 'path': 'rotation'}})
g.save(sys.argv[2])
