#!/usr/bin/env python3
"""Rig-based arm fix for Varnethryl GLBs (clips only; mesh, skin, skeleton untouched).
1) 21-bone rigs (identity joint orientations, arms resting near T/A pose): every clip's upper-arm / forearm / hand
   rotations are re-authored: arms-down offset, the clip's world-X swing becomes a real fore/aft pendulum about the lowered
   arm's lateral axis, forearm roll becomes elbow flex, hand roll removed (palms face the thighs).
   Swing sign is solved per rig from the run/walk leg phase (arm opposite the leg).
2) Other humanoid rigs: hand/forearm roll about the bone's own axis is removed (80%), swing kept.
Usage: fix_arms.py in.glb out.glb [--lat 9] [--report]"""
import json, struct, sys, math, re
import numpy as np
def qmul(a, b):
    x1,y1,z1,w1 = a.T if a.ndim>1 else a; x2,y2,z2,w2 = b.T if b.ndim>1 else b
    return np.stack([w1*x2+x1*w2+y1*z2-z1*y2, w1*y2-x1*z2+y1*w2+z1*x2, w1*z2+x1*y2-y1*x2+z1*w2, w1*w2-x1*x2-y1*y2-z1*z2], -1)
def qaxis(ax, ang):
    ax = np.asarray(ax, float); ax = ax/np.linalg.norm(ax); s = np.sin(np.asarray(ang)/2)[..., None]
    return np.concatenate([ax*s, np.cos(np.asarray(ang)/2)[..., None]], -1)
def qinv(q): return q*np.array([-1,-1,-1,1])
def qrot(q, v):
    u = q[:3]; w = q[3]; return 2*np.dot(u,v)*u + (w*w-np.dot(u,u))*v + 2*w*np.cross(u,v)
def from_to(a, b):
    a = a/np.linalg.norm(a); b = b/np.linalg.norm(b); c = np.cross(a,b); d = np.dot(a,b)
    q = np.array([c[0],c[1],c[2],1+d]); return q/np.linalg.norm(q)
def twist_angle(q, ax):  # signed twist of q about unit axis ax
    q = q*np.where(q[..., 3:4] < 0, -1.0, 1.0); p = q[..., :3] @ ax; return 2*np.arctan2(p, q[..., 3])
def remove_twist(q, ax, keep=0.2):
    p = (q[..., :3] @ ax)[..., None]*ax; tw = np.concatenate([p, q[..., 3:4]], -1); tw /= np.linalg.norm(tw, axis=-1, keepdims=True)
    sw = qmul(q, qinv(tw)); ang = 2*np.arctan2(np.linalg.norm(tw[..., :3], axis=-1)*np.sign(tw[..., :3] @ ax), tw[..., 3])
    return qmul(sw, qaxis(ax, ang*keep))
class GLB:
    def __init__(s, path):
        b = open(path, 'rb').read(); o = 12; s.chunks = []
        while o < len(b):
            ln, ty = struct.unpack('<II', b[o:o+8]); s.chunks.append([ty, bytearray(b[o+8:o+8+ln])]); o += 8+ln
        s.j = json.loads(s.chunks[0][1].decode()); s.bin = s.chunks[1][1]
    def read(s, ai):
        a = s.j['accessors'][ai]; bv = s.j['bufferViews'][a['bufferView']]; n = {'SCALAR':1,'VEC3':3,'VEC4':4}[a['type']]
        assert a['componentType'] == 5126 and not bv.get('byteStride'), 'only tight float accessors'
        off = bv.get('byteOffset',0)+a.get('byteOffset',0); return np.frombuffer(bytes(s.bin[off:off+a['count']*n*4]), '<f4').reshape(a['count'], n).astype(float)
    def add(s, arr):
        arr = np.asarray(arr, '<f4'); 
        while len(s.bin) % 4: s.bin.append(0)
        off = len(s.bin); s.bin += arr.tobytes(); s.j['bufferViews'].append({'buffer':0,'byteOffset':off,'byteLength':arr.nbytes})
        s.j['accessors'].append({'bufferView':len(s.j['bufferViews'])-1,'componentType':5126,'count':arr.shape[0],'type':{1:'SCALAR',3:'VEC3',4:'VEC4'}[arr.shape[1]]}); return len(s.j['accessors'])-1
    def save(s, path):
        while len(s.bin) % 4: s.bin.append(0)
        s.j['buffers'][0]['byteLength'] = len(s.bin); js = json.dumps(s.j, separators=(',',':')).encode()
        while len(js) % 4: js += b' '
        out = b''.join(struct.pack('<II', len(c), t)+bytes(c) for t, c in [(0x4E4F534A, js), (0x004E4942, s.bin)])
        open(path, 'wb').write(struct.pack('<III', 0x46546C67, 2, 12+len(out))+out)
def main(src, dst, lat_deg=None, report=False):
    g = GLB(src); j = g.j; N = j['nodes']; byname = {n.get('name'): i for i, n in enumerate(N)}
    skin = j['skins'][0]['joints'] if j.get('skins') else []; names = {N[i].get('name') for i in skin}
    rot = lambda i: np.array(N[i].get('rotation', [0,0,0,1]), float); tr = lambda i: np.array(N[i].get('translation', [0,0,0]), float)
    rep = {'file': src.split('/')[-1], 'bones': len(skin), 'mode': None, 'clips': {}}
    if not all(k in byname for k in ['upperArm_L','foreArm_L','hand_L','upperArm_R','foreArm_R','hand_R']):
        rep['mode'] = 'no-arms'; g.save(dst) if dst else None; return rep
    ident = all(np.allclose(rot(i), [0,0,0,1], atol=1e-4) for i in skin if N[i].get('name') != 'root')
    down = np.array([0,0,-1.0]) if ident else None
    small = len(skin) <= 27 and ident and 'fingers_L' not in names
    def chan(anim, node, path):
        for c in anim['channels']:
            if c['target'].get('node') == node and c['target']['path'] == path: return c
    if small:
        rep['mode'] = '21-bone retarget'
        side = {}
        for s, sg in [('L',1),('R',-1)]:
            a = tr(byname['foreArm_'+s]); a /= np.linalg.norm(a); rest_lat = math.degrees(math.acos(-a[2]))
            lt = lat_deg if lat_deg is not None else (22 if rest_lat > 85 else 9)
            tgt = np.array([sg*math.sin(math.radians(lt)), 0, -math.cos(math.radians(lt))]); Rd = from_to(a, tgt)
            side[s] = dict(sg=sg, Rd=Rd, X=qrot(qinv(Rd), np.array([1.0,0,0])), rest_lat=round(rest_lat,1), lat=lt)
        rep['restArm'] = {s: side[s]['rest_lat'] for s in side}
        # swing sign: in run (else walk) the RIGHT arm must be forward (Rx<0 moves a hanging arm toward -Y = forward) when the LEFT thigh is forward
        sign = 1.0
        for nm in ['run', 'walk']:
            an = next((a for a in j['animations'] if a['name'] == nm), None)
            if not an: continue
            ca, cl = chan(an, byname['upperArm_R'], 'rotation'), chan(an, byname['thigh_L'], 'rotation')
            if ca and cl:
                ta = twist_angle(g.read(an['samplers'][ca['sampler']]['output']), np.array([1.0,0,0]))
                tl = twist_angle(g.read(an['samplers'][cl['sampler']]['output']), np.array([1.0,0,0]))
                if len(ta) == len(tl) and np.std(ta) > 1e-3 and np.std(tl) > 1e-3: sign = 1.0 if np.corrcoef(ta, tl)[0,1] >= 0 else -1.0; break
        rep['swingSign'] = sign
        for an in j['animations']:
            nm = an['name'].lower(); gain = 1.35 if 'run' in nm else 1.15 if 'walk' in nm else 1.0
            base = 72 if 'run' in nm else 16 if 'walk' in nm else 8 if 'idle' in nm else 20
            info = {}
            for s, S in side.items():
                cu, cf, ch = (chan(an, byname[f'{b}_{s}'], 'rotation') for b in ('upperArm', 'foreArm', 'hand'))
                if not (cu and cf and ch):  # clip leaves some arm bones at the T rest: give them an identity track so they get lowered too
                    inp = max((sm['input'] for sm in an['samplers']), key=lambda k: j['accessors'][k]['count'])
                    for bn, c0 in (('upperArm', cu), ('foreArm', cf), ('hand', ch)):
                        if c0: continue
                        an['samplers'].append({'input': inp, 'output': g.add(np.tile([0,0,0,1.0], (j['accessors'][inp]['count'], 1)))})
                        an['channels'].append({'sampler': len(an['samplers'])-1, 'target': {'node': byname[f'{bn}_{s}'], 'path': 'rotation'}})
                    cu, cf, ch = (chan(an, byname[f'{b}_{s}'], 'rotation') for b in ('upperArm', 'foreArm', 'hand'))
                if cu:
                    q = g.read(an['samplers'][cu['sampler']]['output']); th = twist_angle(q, np.array([1.0,0,0]))*sign*gain
                    nq = qmul(qaxis([1,0,0], th), np.repeat(S['Rd'][None], len(q), 0))
                    an['samplers'].append({'input': an['samplers'][cu['sampler']]['input'], 'output': g.add(nq), 'interpolation': an['samplers'][cu['sampler']].get('interpolation','LINEAR')}); cu['sampler'] = len(an['samplers'])-1
                    info[s] = [round(math.degrees(th.min())), round(math.degrees(th.max()))]
                for c, extra in [(cf, base), (ch, 6)]:
                    if not c: continue
                    q = g.read(an['samplers'][c['sampler']]['output']); th = np.abs(twist_angle(q, np.array([1.0,0,0])))
                    flex = np.radians(extra) + (0.5*th if c is cf and 'attack' in nm or c is cf and 'skill' in nm else 0)
                    nq = qaxis(S['X'], -np.broadcast_to(flex, th.shape))
                    an['samplers'].append({'input': an['samplers'][c['sampler']]['input'], 'output': g.add(nq), 'interpolation': an['samplers'][c['sampler']].get('interpolation','LINEAR')}); c['sampler'] = len(an['samplers'])-1
            rep['clips'][an['name']] = info
    else:
        rep['mode'] = 'roll removal'
        for an in j['animations']:
            info = {}
            for s in 'LR':
                for b, child in [('foreArm', 'hand'), ('hand', None)]:
                    i = byname[f'{b}_{s}']; c = chan(an, i, 'rotation')
                    if not c: continue
                    kids = N[i].get('children', []); ax = None
                    cand = [byname.get(f'{child}_{s}')] if child else [k for k in kids]
                    for k in cand:
                        if k is not None and np.linalg.norm(tr(k)) > 1e-5: ax = tr(k)/np.linalg.norm(tr(k)); break
                    if ax is None: continue
                    q = g.read(an['samplers'][c['sampler']]['output']); r0 = rot(i)
                    rel = qmul(np.repeat(qinv(r0)[None], len(q), 0), q); tw0 = np.degrees(np.ptp(twist_angle(rel, ax)))
                    nq = qmul(np.repeat(r0[None], len(q), 0), remove_twist(rel, ax, 0.2))
                    an['samplers'].append({'input': an['samplers'][c['sampler']]['input'], 'output': g.add(nq), 'interpolation': an['samplers'][c['sampler']].get('interpolation','LINEAR')}); c['sampler'] = len(an['samplers'])-1
                    info[f'{b}_{s}'] = round(float(tw0))
            rep['clips'][an['name']] = info
    if dst: g.save(dst)
    return rep
if __name__ == '__main__':
    a = sys.argv[1:]; lat = float(a[a.index('--lat')+1]) if '--lat' in a else None
    print(json.dumps(main(a[0], a[1] if len(a) > 1 and not a[1].startswith('--') else None, lat)))
