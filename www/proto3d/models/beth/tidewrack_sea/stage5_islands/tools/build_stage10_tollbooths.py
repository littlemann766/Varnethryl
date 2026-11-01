#!/usr/bin/env python3
"""Beth: Saltglass stage 10 - timber toll booths for the lift keeper (dock + top) with a price sign (RIDE 5, PASS 150).
Static -> meshes/B/coast_isl_saltglass_tollbooths{,_lod1,_col}.glb (auto-loaded by the coast_ prefix).
Moving -> props/sg_crank_handle.glb (origin = crank axle, spins about local X; the keeper's crank clip = 1 rev / s).
Booth frame: origin = booth floor centre, front (counter + sign) faces +z (north, toward the walkway). Keeper stands at local (0, 0, -0.5) facing +z."""
import os, sys, math, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_stage5 as B5
import numpy as np, trimesh
from build_stage5 import C, T, box, cyl, merge, _g
ROOT5 = B5.ROOT5; OUT = os.path.join(ROOT5, 'meshes', 'B'); _g['OUT'] = OUT
TIM = C(128, 92, 60); TIM2 = C(96, 66, 42); PLANK = C(150, 112, 74); ROOF = C(78, 92, 98); ROOF2 = C(64, 76, 82); BOARD = C(196, 172, 128); INK = C(44, 32, 24); GOLD = C(226, 184, 70); IRON = C(58, 60, 66); ST2 = C(146, 138, 146); LAMP = C(255, 196, 110)
FONT = {'R': ['110', '101', '110', '101', '101'], 'I': ['111', '010', '010', '010', '111'], 'D': ['110', '101', '101', '101', '110'], 'E': ['111', '100', '110', '100', '111'],
        'P': ['110', '101', '110', '100', '100'], 'A': ['010', '101', '111', '101', '101'], 'S': ['011', '100', '010', '001', '110'], '1': ['010', '110', '010', '010', '111'],
        '5': ['111', '100', '110', '001', '110'], '0': ['111', '101', '101', '101', '111'], ' ': ['000'] * 5}
def text(s, x0, y0, z, px, col):
    out = []; x = x0
    for ch in s:
        g = FONT[ch]
        for r, row in enumerate(g):
            for c, b in enumerate(row):
                if b == '1': out.append(box((px, px, 0.03), col, (x + c * px + px / 2, y0 - r * px - px / 2, z)))
        x += 4 * px
    return out
def coin(x, y, z, r): return [T(cyl(r, 0.03, GOLD, sec=10), (x, y, z), (math.pi / 2, 0, 0)), T(cyl(r * 0.45, 0.04, C(180, 140, 50), sec=6), (x, y, z + 0.005), (math.pi / 2, 0, 0))]
def booth(top):
    S, CO, GL = [], [], []
    dk = box((5.0, 0.5, 4.2), TIM2, (0, -0.25, 0)); S.append(dk); CO.append(dk)
    for x in np.linspace(-2.3, 2.3, 9): S.append(box((0.5, 0.04, 4.2), PLANK, (x, 0.01, 0)))
    for x, z in [(-1.6, -1.5), (1.6, -1.5), (-1.6, 1.1), (1.6, 1.1)]: S.append(box((0.18, 2.6, 0.18), TIM, (x, 1.3, z)))
    for p in [box((3.2, 2.4, 0.1), PLANK, (0, 1.2, -1.5)), box((0.1, 2.4, 2.6), PLANK, (-1.6, 1.2, -0.2)), box((0.1, 1.0, 2.6), PLANK, (1.6, 0.5, -0.2)), box((3.2, 1.05, 0.12), PLANK, (0, 0.525, 1.1))]:
        S.append(p); CO.append(p)
    S.append(box((3.5, 0.08, 0.5), TIM, (0, 1.09, 1.25)))   # counter top
    for y in np.arange(0.2, 2.4, 0.3): S.append(box((3.22, 0.03, 0.12), TIM2, (0, y, -1.44)))   # plank seams
    for sd in (-1, 1): S.append(T(box((2.2, 0.08, 4.0), ROOF if sd < 0 else ROOF2, (0, 0, 0)), (sd * 0.95, 2.95, -0.2), (0, 0, sd * -0.42)))   # pitched roof (ridge along z)
    S.append(box((0.12, 0.12, 4.0), TIM2, (0, 3.36, -0.2)))
    # sign board on the front gable
    S.append(box((2.6, 0.75, 0.06), BOARD, (0, 2.35, 1.22))); S.append(box((2.7, 0.06, 0.08), TIM2, (0, 2.74, 1.22))); S.append(box((2.7, 0.06, 0.08), TIM2, (0, 1.96, 1.22)))
    S += text('RIDE 5', -1.05, 2.66, 1.26, 0.05, INK) + coin(0.55, 2.56, 1.26, 0.08)
    S += text('PASS 150', -1.05, 2.36, 1.26, 0.05, INK) + coin(0.85, 2.26, 1.26, 0.08)
    # winch: frame posts, drum + rope down toward the shaft, axle at the keeper's crank point (local 0, 1.12, -0.3)
    for x in (-0.62, 0.62): S.append(box((0.12, 1.2, 0.2), TIM2, (x, 0.6, -0.3)))
    S.append(T(cyl(0.035, 1.3, IRON, sec=6), (0, 1.12, -0.3), (0, 0, math.pi / 2)))
    S.append(T(cyl(0.22, 0.4, TIM, sec=10), (-0.95, 1.12, -0.3), (0, 0, math.pi / 2))); S.append(T(cyl(0.26, 0.06, IRON, sec=10), (-0.73, 1.12, -0.3), (0, 0, math.pi / 2)))
    S.append(box((0.6, 0.5, 0.4), TIM2, (-0.95, 0.25, -0.3)))
    S.append(box((0.4, 0.3, 0.3), C(110, 80, 50), (1.1, 1.24, 0.95)))   # coin box on the counter
    S += coin(1.1, 1.4, 0.95, 0.06)
    GL.append(box((0.22, 0.3, 0.22), LAMP, (1.75, 2.3, 1.25))); S.append(box((0.05, 0.4, 0.05), IRON, (1.75, 2.55, 1.25)))
    if not top:
        for x, z in [(-2.2, -1.8), (2.2, -1.8), (-2.2, 1.8), (2.2, 1.8)]: S.append(cyl(0.22, 24, TIM2, (x, -12.5, z), sec=6))
    else:   # cantilevered off the lift shaft (no pillars through the dock booth below): iron struts to the shaft's west posts
        for z in (-1.8, 1.4): S.append(T(box((0.12, 0.12, 3.6), IRON), (2.3, -1.4, z), (0, math.pi / 2, 0.75)))
    return S, CO, GL
Y0, YT = 20.4, 108.68
SITES = {'dock': ((-2109.5, Y0, -80.4), False), 'top': ((-2109.5, YT, -80.4), True)}
S, CO, GL = [], [], []
for k, (o, top) in SITES.items():
    s_, c_, g_ = booth(top); S += [T(m, o) for m in s_]; CO += [T(m, o) for m in c_]; GL += [T(m, o) for m in g_]
B5.save('coast_isl_saltglass_tollbooths', merge(S)); B5.save('coast_isl_saltglass_tollbooths_glow', merge(GL), lod=False)
colm = merge([trimesh.Trimesh(c.vertices, c.faces, process=False) for c in CO]); colm.export(os.path.join(OUT, 'coast_isl_saltglass_tollbooths_col.glb'))
print('booths', B5.STATS['coast_isl_saltglass_tollbooths'], 'col', len(colm.faces))
PR = os.path.join(ROOT5, 'props'); _g['OUT'] = PR
h = [T(cyl(0.03, 0.34, IRON, sec=6), (0, 0, 0), (0, 0, math.pi / 2))]   # hub
for x in (-0.16, 0.16): h.append(box((0.03, 0.03, 0.11), IRON, (x, 0, 0.04)))   # arms (radius 0.08)
h.append(T(cyl(0.025, 0.36, C(120, 84, 52), sec=6), (0, 0, 0.08), (0, 0, math.pi / 2)))   # wooden grip bar the gloves hold
B5.save('sg_crank_handle', merge(h), lod=False)
r3 = lambda v: [round(float(x), 2) for x in v]
blk = {'files': {'mesh': 'coast_isl_saltglass_tollbooths', 'lod1': 'coast_isl_saltglass_tollbooths_lod1', 'glow': 'coast_isl_saltglass_tollbooths_glow', 'col': 'coast_isl_saltglass_tollbooths_col'},
       'prices': {'ride': 5, 'season_pass': 150, 'pass_item': 'saltglass_lift_pass'}}
for k, (o, top) in SITES.items():
    o = np.array(o); blk[k] = {'booth': r3(o), 'keeper': r3(o + [0, 0, -0.5]), 'keeper_yaw_deg': 0.0, 'crank_axle': r3(o + [0, 1.12, -0.3]), 'window': r3(o + [0, 0, 3.2])}
mp = os.path.join(ROOT5, 'stage5_manifest.json'); man = json.load(open(mp)); man['islands']['saltglass']['stage10'] = blk
man['stats'] = {**man.get('stats', {}), **{k: v for k, v in B5.STATS.items() if 'toll' in k or k.startswith('sg_')}}
json.dump(man, open(mp, 'w'), indent=1, default=float); print(json.dumps(blk)[:400])
