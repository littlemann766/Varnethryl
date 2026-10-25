"""Copy the 'intro' animation from a Blender round-trip GLB into the ORIGINAL GLB (materials/mesh untouched), mapping nodes by name.
Checks that each animated node's rest TRS matches between the two files. usage: orig.glb roundtrip.glb out.glb"""
import sys, json, numpy as np; sys.path.insert(0, '/workspace/varn-core/tools/rig_fix'); from fix_arms import GLB
o, r = GLB(sys.argv[1]), GLB(sys.argv[2]); out = sys.argv[3]; NAMES = sys.argv[4].split(',') if len(sys.argv) > 4 else ['intro']
on = {n.get('name'): i for i, n in enumerate(o.j['nodes'])}
res = {}
for NAME in NAMES:
    SRC, NAME = (NAME.split(':') + [NAME])[:2] if ':' in NAME else (NAME, NAME)
    ra = [a for a in r.j['animations'] if a['name'] == SRC][0]
    o.j['animations'] = [a for a in o.j['animations'] if a['name'] != NAME]
    na = {'name': NAME, 'channels': [], 'samplers': []}; worst = 0; cache = {}
    for c in ra['channels']:
        rn = r.j['nodes'][c['target']['node']]; nm = rn.get('name')
        if nm not in on: continue
        onode = o.j['nodes'][on[nm]]
        for k, d in (('translation', [0,0,0]), ('rotation', [0,0,0,1]), ('scale', [1,1,1])):
            a_, b_ = np.array(rn.get(k, d)), np.array(onode.get(k, d))
            if k == 'rotation' and a_ @ b_ < 0: b_ = -b_
            worst = max(worst, float(np.abs(a_ - b_).max()))
        s_ = ra['samplers'][c['sampler']]
        if s_['input'] not in cache:
            cache[s_['input']] = o.add(r.read(s_['input'])); t = r.read(s_['input']); acc = o.j['accessors'][cache[s_['input']]]; acc['min'] = [float(t.min())]; acc['max'] = [float(t.max())]
        na['samplers'].append({'input': cache[s_['input']], 'output': o.add(r.read(s_['output'])), 'interpolation': s_.get('interpolation', 'LINEAR')})
        na['channels'].append({'sampler': len(na['samplers'])-1, 'target': {'node': on[nm], 'path': c['target']['path']}})
    o.j['animations'].append(na); res[NAME] = (len(na['channels']), round(worst, 5))
o.save(out)
print(json.dumps({'out': out, 'spliced': res, 'anims': [a['name'] for a in o.j['animations']]}))
