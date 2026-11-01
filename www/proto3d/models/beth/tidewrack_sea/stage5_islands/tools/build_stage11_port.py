#!/usr/bin/env python3
"""Beth: Saltglass stage 11 - the port moves to the sheltered WEST cove (-2350, 90). Medieval timber-and-stone harbour:
stone quay, timber jetty on piles, mooring posts, harbourmaster's hut, crates/barrels, lantern posts; a terraced sea stair of cut
stone (3 flights at 18.8 deg, solid masonry, no stilts) up the 25 m cove cliff, then a winding cobble -> dirt path (every grid step
<= 20 deg) to the plateau, the Lookout, the Clifftop Cache and the other Saltglass POIs.
Static -> meshes/B/coast_isl_saltglass_port{,_lod1,_glow,_col}.glb (auto-loaded by the coast_ prefix).
Needs tools/data/stage11_H2.npz (final surface heightfield) + tools/data/stage11_routes.json (path planner, see tools/plan_stage11_routes.py)."""
import os, sys, math, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_stage5 as B5
import numpy as np, trimesh
from scipy.ndimage import map_coordinates
from build_stage5 import C, T, box, cyl, merge, _g, paint
ROOT5 = B5.ROOT5; OUT = os.path.join(ROOT5, 'meshes', 'B'); _g['OUT'] = OUT
import os; _D = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
HX, HZ, HH = np.load(os.path.join(_D, 'stage11_H2.npz'))['H']; hx0, hz0 = HX[0, 0], HZ[0, 0]
def TH(x, z): return float(map_coordinates(HH, [[(z - hz0) / 2], [(x - hx0) / 2]], order=1)[0])
STN = C(150, 142, 130); STN2 = C(122, 114, 104); STN3 = C(170, 162, 148); MOSS = C(96, 116, 70); WOOD = C(122, 88, 56); WOOD2 = C(92, 64, 40); PLANK = C(148, 112, 74)
ROOF = C(92, 70, 58); ROOF2 = C(110, 84, 66); IRON = C(52, 54, 58); LAMP = C(255, 196, 110); ROPE = C(176, 150, 104); COB = C(138, 128, 116); DIRT = C(150, 128, 96); DIRT2 = C(132, 112, 84)
rng = np.random.default_rng(11)
S, CO, GL = [], [], []
def prism(a, b, w, ybot, col):   # solid masonry block under a straight deck a->b (top follows the deck), down to ybot
    a = np.array(a, float); b = np.array(b, float); u = b - a; d = np.array([u[0], 0, u[2]]); d /= np.linalg.norm(d); n = np.array([-d[2], 0, d[0]]) * w / 2
    P = [a - n, a + n, b + n, b - n]; V = [p for p in P] + [np.array([p[0], ybot, p[2]]) for p in P]
    m = trimesh.convex.convex_hull(np.array(V)); return paint(m, col)
def deck(a, b, w, rails=(), steps=False, ybot=None, col=STN):
    a = np.array(a, float); b = np.array(b, float)
    if ybot is None: ybot = min(TH(*q[[0, 2]]) for q in (a, b, (a + b) / 2)) - 1.5
    m = prism(a, b, w, ybot, col); S.append(m); CO.append(m)
    u = b - a; Lh = math.hypot(u[0], u[2]); yaw = math.atan2(u[0], u[2]); d = np.array([u[0], 0, u[2]]) / Lh; n = np.array([-d[2], 0, d[0]])
    if steps and abs(u[1]) > 0.5:   # cut stone steps (visual; the collider is the smooth top)
        ns = int(abs(u[1]) / 0.2)
        for k in range(ns):
            t = (k + 0.5) / ns; q = a + u * t; S.append(T(box((w - 0.1, 0.2, Lh / ns + 0.02), STN3 if k % 2 else STN), (q[0], q[1] - 0.1 + 0.06, q[2]), (0, yaw, 0)))
    for y in np.arange(ybot + 1.6, max(a[1], b[1]) - 0.8, 1.6):   # coursed masonry bands on the long faces
        for sd in (-1, 1):
            q0 = a + n * sd * (w / 2 + 0.03); q1 = b + n * sd * (w / 2 + 0.03); top = min(a[1], b[1])
            if y > top - 0.6: continue
            mid = (q0 + q1) / 2; S.append(T(box((0.08, 0.12, Lh), STN2), (mid[0], y, mid[2]), (0, yaw, 0)))
    for r in rails:   # parapet: 'L' / 'R' looking a->b
        sd = -1 if r == 'L' else 1
        q0 = a + n * sd * (w / 2 - 0.2); q1 = b + n * sd * (w / 2 - 0.2)
        pm = prism(q0 + [0, 0.9, 0], q1 + [0, 0.9, 0], 0.4, min(q0[1], q1[1]) - 0.2, STN2); S.append(pm); CO.append(pm)
    return a, b
# ---------------- terraced sea stair (cut stone) up the east cliff of the cove
Y0 = 2.2; G = 0.34; ZA, ZB = 78.0, 102.0; COLS = [-2338.0, -2334.0, -2330.0]; W = 3.6
FL = []; y = Y0
for k, xc in enumerate(COLS):
    a, b = (ZB, ZA) if k % 2 == 0 else (ZA, ZB); y1 = y + G * abs(b - a)
    FL.append(deck((xc, y, a), (xc, y1, b), W, rails=('L',) if k % 2 == 0 else ('R',), steps=True)); y = y1   # parapet on the sea (west) side
YT = y
LND = []
LND.append(deck((-2340.0, FL[0][1][1], 76.0), (-2332.2, FL[0][1][1], 76.0), 4.0, rails=('L',)))   # f0 -> f1 (south end), parapet on the sea (south) side
LND.append(deck((-2336.0, FL[1][1][1], 104.0), (-2328.2, FL[1][1][1], 104.0), 4.0, rails=('R',)))   # f1 -> f2 (north end)
top_a = np.array([-2332.0, YT, 76.0]); top_m = np.array([-2328.0, YT, 76.0]); top_e = np.array([-2319.5, max(YT, TH(-2319.5, 76.0) + 0.02), 76.0])
LND.append(deck(top_a, top_m, 4.0, rails=('L',))); LND.append(deck(top_m, top_e, 3.6, rails=(), steps=True))   # top walk, then a short stepped ramp onto the headland
# ---------------- quay, jetty, harbour dressing
QX0, QX1, QZ0, QZ1 = -2344.0, -2329.0, 99.0, 110.0
q = box((QX1 - QX0, 8.2, QZ1 - QZ0), STN, ((QX0 + QX1) / 2, Y0 - 4.1, (QZ0 + QZ1) / 2)); S.append(q); CO.append(q)
for x in np.arange(QX0 + 0.5, QX1, 1.0): S.append(box((0.9, 0.05, QZ1 - QZ0 - 0.2), STN3 if int(x) % 2 else STN, (x, Y0 + 0.02, (QZ0 + QZ1) / 2)))   # flagstones
for yb in (0.4, -1.0): S.append(box((0.1, 0.15, QZ1 - QZ0), STN2, (QX0 - 0.03, yb, (QZ0 + QZ1) / 2)))
S.append(box((QX1 - QX0, 0.6, 0.1), MOSS, ((QX0 + QX1) / 2, -0.2, QZ0 - 0.04)))   # weed line
JA = np.array([QX0, Y0, 101.5]); JB = np.array([-2368.0, Y0, 92.0]); ju = JB - JA; JL = float(np.linalg.norm(ju)); jyaw = math.atan2(ju[0], ju[2]); jd = ju / JL; jn = np.array([-jd[2], 0, jd[0]])
jm = (JA + JB) / 2; jdk = T(box((3.4, 0.3, JL), PLANK), (jm[0], Y0 - 0.15, jm[2]), (0, jyaw, 0)); S.append(jdk); CO.append(jdk)
for t in np.linspace(0, 1, int(JL / 0.5)): p = JA + ju * t; S.append(T(box((3.5, 0.04, 0.06), WOOD2), (p[0], Y0 + 0.005, p[2]), (0, jyaw, 0)))   # plank seams
for t in np.linspace(0.04, 1.0, int(JL / 3) + 1):
    for sd in (-1, 1):
        p = JA + ju * t + jn * sd * 1.6; S.append(cyl(0.18, 9.0, WOOD2, (p[0], Y0 - 4.6, p[2]), sec=6))
    p = JA + ju * t; S.append(T(box((3.6, 0.25, 0.25), WOOD), (p[0], Y0 - 0.45, p[2]), (0, jyaw, 0)))
for t in (0.35, 0.7, 1.0):   # mooring posts with rope coils
    for sd in (-1, 1):
        p = JA + ju * t + jn * sd * 1.55; mp_ = cyl(0.16, 1.1, WOOD2, (p[0], Y0 + 0.55, p[2]), sec=6); S.append(mp_)
        S.append(cyl(0.2, 0.12, ROPE, (p[0], Y0 + 0.75, p[2]), sec=6))
for z in np.arange(QZ0 + 1.0, QZ1, 3.0): S.append(cyl(0.22, 0.7, IRON, (QX0 + 0.4, Y0 + 0.35, z), sec=8)); S.append(cyl(0.3, 0.1, IRON, (QX0 + 0.4, Y0 + 0.72, z), sec=8))   # quay bollards
def lantern(x, z, y=None):
    y = TH(x, z) if y is None else y
    S.append(cyl(0.1, 2.6, WOOD2, (x, y + 1.3, z), sec=6)); S.append(box((0.6, 0.08, 0.08), WOOD2, (x + 0.25, y + 2.55, z)))
    S.append(box((0.3, 0.05, 0.3), IRON, (x + 0.5, y + 2.62, z))); GL.append(box((0.22, 0.3, 0.22), LAMP, (x + 0.5, y + 2.4, z))); S.append(box((0.32, 0.05, 0.32), IRON, (x + 0.5, y + 2.22, z)))
for p in (JA + ju * 0.5 + jn * 1.55, JB + jn * 1.55): lantern(p[0], p[2], Y0)
lantern(QX1 - 0.6, QZ1 - 0.5, Y0); lantern(-2340.6, 99.6, Y0)
# harbourmaster's hut (NE corner of the quay): stone footing, timber frame + plank walls, shingle roof, door to the west
hx, hz = -2340.6, 107.6
for p in [box((4.4, 0.4, 4.2), STN2, (hx, Y0 + 0.2, hz)), box((0.12, 2.4, 4.0), PLANK, (hx + 2.0, Y0 + 1.6, hz)), box((4.0, 2.4, 0.12), PLANK, (hx, Y0 + 1.6, hz - 2.0)), box((4.0, 2.4, 0.12), PLANK, (hx, Y0 + 1.6, hz + 2.0)),
          box((0.12, 2.4, 1.3), PLANK, (hx - 2.0, Y0 + 1.6, hz - 1.35)), box((0.12, 2.4, 1.3), PLANK, (hx - 2.0, Y0 + 1.6, hz + 1.35)), box((0.12, 0.6, 1.4), PLANK, (hx - 2.0, Y0 + 2.5, hz))]:
    S.append(p); CO.append(p)
for dx, dz in [(-2, -2), (2, -2), (-2, 2), (2, 2)]: S.append(box((0.22, 2.6, 0.22), WOOD2, (hx + dx, Y0 + 1.7, hz + dz)))
for sd in (-1, 1): S.append(T(box((2.8, 0.1, 4.8), ROOF if sd < 0 else ROOF2), (hx + sd * 1.15, Y0 + 3.55, hz), (0, 0, sd * -0.6)))
S.append(box((0.5, 1.4, 0.5), STN2, (hx + 1.4, Y0 + 4.0, hz + 1.2)))   # chimney
S.append(box((0.08, 0.5, 0.9), C(196, 170, 120), (hx - 2.08, Y0 + 2.2, hz + 1.35)))   # notice board
GL.append(box((0.2, 0.25, 0.2), LAMP, (hx - 2.2, Y0 + 2.5, hz - 0.9)))
for (cx, cz, s_) in [(-2334.6, 108.9, 1.0), (-2333.4, 109.1, 0.8), (-2334.4, 107.8, 0.7), (-2331.0, 109.2, 0.9)]:   # crates
    cr = box((s_, s_, s_), WOOD, (cx, Y0 + s_ / 2, cz), (0, rng.uniform(-0.3, 0.3), 0)); S.append(cr); CO.append(cr)
    S.append(box((s_ + 0.02, 0.08, s_ + 0.02), WOOD2, (cx, Y0 + s_ * 0.5, cz)))
for (bx, bz) in [(-2336.6, 109.3), (-2335.8, 109.4), (-2330.0, 107.6)]:   # barrels
    S.append(cyl(0.38, 0.95, WOOD, (bx, Y0 + 0.48, bz), sec=8)); S.append(cyl(0.4, 0.06, IRON, (bx, Y0 + 0.75, bz), sec=8)); S.append(cyl(0.4, 0.06, IRON, (bx, Y0 + 0.2, bz), sec=8))
for (lx_, lz_) in [(-2341.5, 76.0), (-2333.8, 104.0), (-2326.0, 76.0)]: lantern(lx_, lz_ - 1.6 if lz_ < 90 else lz_ + 1.6, None if False else (FL[0][1][1] if lx_ < -2340 else FL[1][1][1] if lz_ > 90 else YT))
# ---------------- winding path: cobbles for the first stretch, then a dirt track, draped on the island surface
RT = json.load(open(os.path.join(_D, 'stage11_routes.json')))
segs = set(); tracks = []
for nm, r in RT.items():
    pts = r['pts']
    for k in range(len(pts) - 1):
        key = (round(pts[k][0]), round(pts[k][2]), round(pts[k + 1][0]), round(pts[k + 1][2]))
        if key in segs or key[2:] + key[:2] in segs: continue
        segs.add(key); tracks.append((pts[k], pts[k + 1]))
o0 = top_e
for (a, b) in tracks:
    a = np.array(a); b = np.array(b); d0 = math.hypot(a[0] - o0[0], a[2] - o0[2]); u = b - a; Lh = math.hypot(u[0], u[2]); yaw = math.atan2(u[0], u[2])
    col = COB if d0 < 70 else (DIRT if rng.random() < 0.6 else DIRT2); m = (a + b) / 2
    ya, yb = TH(a[0], a[2]) + 0.07, TH(b[0], b[2]) + 0.07; pitch = -math.atan2(yb - ya, Lh)
    S.append(T(T(box((2.6, 0.06, Lh + 0.6), col), (0, 0, 0), (pitch, 0, 0)), (m[0], (ya + yb) / 2, m[2]), (0, yaw, 0)))
    if d0 < 70 and rng.random() < 0.35:   # kerb stones
        for sd in (-1, 1): S.append(T(box((0.3, 0.2, 0.5), STN2), (m[0] + math.cos(yaw) * sd * 1.45, (ya + yb) / 2 + 0.05, m[2] - math.sin(yaw) * sd * 1.45), (0, yaw, 0)))
# lantern posts every ~45 m along the main path (to the Cache)
main = RT['Clifftop Cache']['pts']; acc = 0.0; nxt = 20.0
for k in range(len(main) - 1):
    acc += math.hypot(main[k + 1][0] - main[k][0], main[k + 1][2] - main[k][2])
    if acc > nxt:
        a = np.array(main[k]); b = np.array(main[k + 1]); u = b - a; n = np.array([-u[2], 0, u[0]]) / (np.linalg.norm(u) + 1e-9); p = a + n * 2.2; lantern(p[0], p[2]); nxt += 45.0
allm = merge(S); B5.save('coast_isl_saltglass_port', allm); B5.save('coast_isl_saltglass_port_glow', merge(GL), lod=False)
colm = merge([trimesh.Trimesh(c.vertices, c.faces, process=False) for c in CO]); colm.export(os.path.join(OUT, 'coast_isl_saltglass_port_col.glb'))
print('port', B5.STATS['coast_isl_saltglass_port'], 'col', len(colm.faces))
# ---------------- landing + routes (manifest)
r3 = lambda v: [round(float(x), 2) for x in v]
moor = np.array([-2372.0, 0.0, 90.5]); shore = np.array([JA[0], Y0, JA[2]]); inl = (shore - moor)[[0, 2]]; inl = inl / np.linalg.norm(inl)
stair = [r3((-2338.0, Y0 + 0.08, 103.0))]
for k, (a, b) in enumerate(FL):
    stair += [r3(a + [0, 0.08, 0]), r3(b + [0, 0.08, 0])]
    if k < len(FL) - 1:
        zl = 76.0 if k % 2 == 0 else 104.0; stair += [r3((COLS[k], b[1] + 0.08, zl)), r3((COLS[k + 1], b[1] + 0.08, zl))]
stair += [r3((COLS[-1], YT + 0.08, 76.0)), r3(top_m + [0, 0.08, 0]), r3(top_e + [0, 0.08, 0])]
dock = [r3(JA + jd * -1.0 + [0, 0.08, 0]), r3((-2340.0, Y0 + 0.08, 104.0))]
pre = dock + stair
blk = {'note': 'stage 11: Saltglass port moved to the west cove (README Stage 11)', 'files': {'mesh': 'coast_isl_saltglass_port', 'lod1': 'coast_isl_saltglass_port_lod1', 'glow': 'coast_isl_saltglass_port_glow', 'col': 'coast_isl_saltglass_port_col'},
       'landing': {'moor': r3(moor), 'shore': r3(shore), 'inland': r3(inl), 'pier_m': round(float(np.linalg.norm((shore - moor)[[0, 2]])), 1)},
       'quay': [QX0, QZ0, QX1, QZ1, Y0], 'jetty': {'a': r3(JA), 'b': r3(JB), 'w': 3.4}, 'sea_stair': {'flights': len(FL), 'deg': round(math.degrees(math.atan(G)), 1), 'bottom': r3(FL[0][0]), 'top': r3(top_e)},
       'routes': {}}
for nm, r in RT.items(): blk['routes'][nm] = pre + [r3(p) for p in r['pts']]
cc = blk['routes']['Clifftop Cache']; k = next(i for i, p in enumerate(cc) if p[1] > 100.0); blk['routes']['dock_to_plateau'] = cc[:k + 1]
json.dump(blk, open(os.path.join(_D, 'stage11_port_block.json'), 'w'), indent=1); print('stair top', r3(top_e), 'YT', round(YT, 2))
