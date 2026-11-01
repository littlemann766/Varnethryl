#!/usr/bin/env python3
"""Beth: Saltglass stage 9 - dock lift + locked shortcut ramp (Dark Souls style) + skybridge to the plateau.
Static parts -> meshes/B/coast_isl_saltglass_lift{,_lod1,_col}.glb (tw_sea.gd auto-loads them by the coast_ prefix).
Moving parts -> props/sg_lift_platform.glb, props/sg_shortcut_gate.glb, props/sg_lever.glb (NOT auto-loaded; wired by props/*.tscn).
Layout (world m): dock walkway north of the pier head -> gate landing L0 (y 20.4, z -76) -> 10 ramp runs at 17.5 deg in a 2-lane
switchback tower in the water (x -2103.4..-2095.2, z -74..-50) -> top landing (y 108.7) -> skybridge 82 m WNW onto the plateau
(-2172, 107.3, -22). Lift shaft (x -2104, z -82) runs 20.4 -> 108.7 beside the tower; both share the top landing.
Writes the stage-9 block of stage5_manifest.json islands.saltglass.stage9 (routes for tools/walk5.gd)."""
import os, sys, math, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_stage5 as B5
import numpy as np, trimesh
from build_stage5 import C, T, box, cyl, merge, _g
ROOT5 = B5.ROOT5; OUT = os.path.join(ROOT5, 'meshes', 'B'); _g['OUT'] = OUT
import glob
def _env():   # ground under the new parts: the Saltglass patch collider + the game's stage-2 colliders (read only)
    ms = []
    for f in [os.path.join(OUT, 'coast_isl_saltglass_col.glb')] + [g for g in glob.glob('/workspace/godot-voxel/tidewrack/stage2/meshes/coast_*_col.glb') if 'isl_' not in g]:
        m = trimesh.load(f, force='scene').to_geometry(); v = m.vertices
        if ((v[:, 0] > -2260) & (v[:, 0] < -2060) & (v[:, 2] > -160) & (v[:, 2] < 110)).any(): ms.append(m)
    return trimesh.util.concatenate(ms)
ENV = _env()
def H(x, z):
    l, _, _ = ENV.ray.intersects_location([[x, 300, z]], [[0, -1, 0]], multiple_hits=False); return float(l[0][1]) if len(l) else -5.0
ST = C(176, 168, 172); ST2 = C(146, 138, 146); IRON = C(58, 60, 66); WOODD = C(110, 78, 50); BRASS = C(200, 160, 80); LAMP = C(255, 196, 110)
S, CO, GL = [], [], []
def deck(a, b, w, rails=('L', 'R'), treads=False, endrails=(), pillars=True, col=ST2):
    """slab from a to b (top surface on the a-b line), rails 'L'/'R' (left/right looking a->b), endrails 'A'/'B' across the ends"""
    a = np.array(a, float); b = np.array(b, float); u = b - a; Lh = math.hypot(u[0], u[2]); yaw = math.atan2(u[0], u[2]); pitch = -math.atan2(u[1], Lh); Ls = math.hypot(Lh, u[1]); mid = (a + b) / 2
    def place(m, lat=0.0, up=0.0, al=0.0): return T(T(m, (lat, up, al), (pitch, 0, 0)), mid, (0, yaw, 0))
    dk = place(box((w, 0.5, Ls), col), 0, -0.25); S.append(dk); CO.append(dk)
    if treads:
        for k in range(int(Ls / 1.2)): S.append(place(box((w - 0.2, 0.05, 0.14), ST, (0, 0.02, -Ls / 2 + 0.6 + k * 1.2))))
    for r in rails:
        sd = 1 if r == 'R' else -1; rl = place(box((0.3, 1.1, Ls), ST), -sd * (w / 2 + 0.15), 0.55); S.append(rl); CO.append(rl)   # local +x is the left side looking a->b
    for e in endrails:
        q = a if e == 'A' else b; rl = T(box((w + 0.6, 1.1, 0.3), ST), (0, 0, 0)); rl = T(rl, (q[0], q[1] + 0.55, q[2]), (0, yaw, 0)); S.append(rl); CO.append(rl)
    if pillars:
        for tt in np.linspace(0.15, 0.85, max(2, int(Lh / 14) + 1)):
            q = a + u * tt; g = H(q[0], q[2]); h = q[1] - 0.5 - g + 1.0
            if h > 0.6: S.append(cyl(0.55 if h < 40 else 0.9, h, ST2, (q[0], g - 1.0 + h / 2, q[2]), sec=6))
    return a, b
Y0, RUN, NR, DEG = 20.40, 28.0, 10, 17.5
RISE = RUN * math.tan(math.radians(DEG)); YT = Y0 + RISE * NR
LX = [-2097.0, -2101.6]; ZS, ZN = -74.0, -50.0 + 0.0; ZN = ZS + RUN   # lane x, south/north foot of the runs
SH = (-2104.0, -82.0)   # lift shaft centre
PH = (-2123.66, 20.22, -90.27)
# --- dock walkway: pier head -> north -> east along L0
w1a, w1b = deck((-2124.6, 20.35, -89.2), (-2124.6, Y0, -78.0), 3.0, rails=('L',), pillars=True)   # rail 'L' = local +x; looking north that is the sea (east) side
deck((-2126.1, Y0, -76.0), (-2110.0, Y0, -76.0), 4.0, rails=('R',), pillars=True)   # looking east: 'R' = north rail
S.append(box((12.9, 1.1, 0.3), ST, (-2116.55, Y0 + 0.55, -78.15))); CO.append(S[-1])   # south rail east of the W1 joint
# L0 gate landing x -2110..-2095 (south rail with a gap for the shaft connector, north rail up to the ramp foot)
deck((-2110.0, Y0, -76.0), (-2095.0, Y0, -76.0), 4.0, rails=(), endrails=('B',))
for x0, x1 in [(-2110.0, -2105.6), (-2102.4, -2095.0)]: S.append(box((x1 - x0, 1.1, 0.3), ST, ((x0 + x1) / 2, Y0 + 0.55, -78.15))); CO.append(S[-1])
S.append(box((10.0, 1.1, 0.3), ST, (-2105.0 + 0.0 - 0.0, Y0 + 0.55, -73.85))); CO.append(S[-1])   # north rail x -2110..-2100 (ramp foot at -2098.8 stays open)
deck((-2104.0, Y0, -78.0), (-2104.0, Y0, -79.9), 3.2, rails=('L', 'R'), pillars=False)   # connector to the lift (bottom)
# gate frame at x -2100.0 across L0 (portcullis slot; leaf = props/sg_shortcut_gate.glb)
GX = -2100.0
for zz in (-78.3, -73.7):
    S.append(box((1.0, 4.2, 0.8), ST2, (GX, Y0 + 2.1, zz))); CO.append(S[-1])
S.append(box((1.2, 3.6, 5.4), ST2, (GX, Y0 + 3.8 + 1.8, -76.0))); CO.append(S[-1])   # gatehouse block over the slot (raised leaf hides inside)
GL.append(box((0.3, 0.3, 0.3), LAMP, (GX - 0.7, Y0 + 3.4, -78.9)))
# --- ramp tower
RUNS, LANDS = [], []
for r in range(NR):
    lane = r % 2; y0 = Y0 + RISE * r; y1 = y0 + RISE
    za, zb = (ZS, ZN) if lane == 0 else (ZN, ZS)
    RUNS.append(deck((LX[lane], y0, za), (LX[lane], y1, zb), 3.6, treads=True, pillars=False))
    if r < NR - 1:
        zl = ZN + 2.0 if lane == 0 else ZS - 2.0
        a, b = (-2103.6, -2095.0)
        LANDS.append(deck((a, y1, zl), (b, y1, zl), 4.0, rails=('R',) if lane == 0 else ('L',), endrails=('A', 'B'), pillars=False))
# top landing (shared with the lift top) x -2112..-2095 at z -76; skybridge leaves its west end
deck((-2112.0, YT, -76.0), (-2095.0, YT, -76.0), 4.0, rails=(), endrails=('B',), pillars=False)
for x0, x1 in [(-2112.0, -2105.6), (-2102.4, -2099.6 + 0.0)]: S.append(box((x1 - x0, 1.1, 0.3), ST, ((x0 + x1) / 2, YT + 0.55, -78.15))); CO.append(S[-1])
S.append(box((3.0, 1.1, 0.3), ST, (-2096.5, YT + 0.55, -78.15))); CO.append(S[-1])
for x0, x1 in [(-2112.0, -2103.7), (-2099.5, -2095.0)]: S.append(box((x1 - x0, 1.1, 0.3), ST, ((x0 + x1) / 2, YT + 0.55, -73.85))); CO.append(S[-1])   # north rail, open over the last run's head (lane x -2103.4..-2099.8)
for cx in (-2104.25, -2094.35):
    for cz in (-78.6, -60.0, -41.4):
        g = H(cx, cz); S.append(cyl(0.45, YT + 1.2 - g + 1.0, ST2, (cx, (YT + 1.2 + g - 1.0) / 2, cz), sec=6))   # tower columns outside every deck
deck((-2104.0, YT, -78.0), (-2104.0, YT, -79.9), 3.2, rails=('L', 'R'), pillars=False)
SB_A = (-2112.0, YT, -76.0); SB_E = (-2172.0, H(-2172.0, -22.0) + 0.05, -22.0)
u = np.array(SB_E) - np.array(SB_A); n = int(math.ceil(math.hypot(u[0], u[2]) / 16)); SBP = [list(np.array(SB_A) + u * t) for t in np.linspace(0, 1, n + 1)]
for i in range(n): deck(SBP[i], SBP[i + 1], 3.6, rails=('L', 'R'), pillars=(i < n - 1))
ext = np.array(SB_E) + u / np.linalg.norm(u) * 3.0; deck(SB_E, (ext[0], SB_E[1] - 0.6, ext[2]), 3.6, rails=(), pillars=False)   # end tucked into the plateau
for p in SBP[1:-1]: GL.append(box((0.25, 0.4, 0.25), LAMP, (p[0], p[1] + 1.5, p[2])))
# --- lift shaft (open on the north side at the bottom and top doors), static
sx, sz = SH; for_ = []
for dx in (-2.1, 2.1):
    for dz in (-2.1, 2.1):
        S.append(box((0.4, YT + 4.5 - (-2.0), 0.4), IRON, (sx + dx, (YT + 4.5 - 2.0) / 2, sz + dz))); CO.append(S[-1])
for y in np.arange(Y0 + 4.0, YT, 6.0):   # cross bracing (outside the 3.6 m cage, so it never touches the platform)
    for (dx, dz, wx, wz) in [(0, -2.1, 4.6, 0.25), (0, 2.1, 4.6, 0.25), (-2.1, 0, 0.25, 4.6), (2.1, 0, 0.25, 4.6)]:
        if dz == 2.1 and (abs(y - Y0) < 3.0 or abs(y - YT) < 3.0): continue
        S.append(box((wx, 0.25, wz), IRON, (sx + dx, y, sz + dz)))
for (dx, dz, wx, wz) in [(0, -2.15, 4.6, 0.2), (-2.15, 0, 0.2, 4.6), (2.15, 0, 0.2, 4.6)]:   # rails round the cage at both stops, door side open
    for y in (Y0, YT): S.append(box((wx, 1.2, wz), IRON, (sx + dx, y + 0.6, sz + dz))); CO.append(S[-1])
S.append(box((5.4, 0.6, 5.4), WOODD, (sx, YT + 4.8, sz))); S.append(cyl(0.8, 1.6, IRON, (sx, YT + 3.9, sz), rot=(math.pi / 2, 0, 0), sec=10))   # winch house + drum
S.append(box((4.6, 0.6, 4.6), ST2, (sx, Y0 - 0.9, sz))); CO.append(S[-1])   # pit floor under the parked platform
S.append(cyl(1.6, Y0 + 1.0, ST2, (sx, Y0 / 2 - 1.5, sz), sec=8))
for y in (Y0, YT): GL.append(box((0.3, 0.3, 0.3), LAMP, (sx - 2.4, y + 2.2, sz + 2.4)))
allm = merge(S); B5.save('coast_isl_saltglass_lift', allm); B5.save('coast_isl_saltglass_lift_glow', merge(GL), lod=False)
colm = merge([trimesh.Trimesh(c.vertices, c.faces, process=False) for c in CO]); colm.export(os.path.join(OUT, 'coast_isl_saltglass_lift_col.glb'))
st = B5.STATS['coast_isl_saltglass_lift']; print('tris', st, 'col', len(colm.faces))
# --- moving props (origin = their pivot), props/
PR = os.path.join(ROOT5, 'props'); os.makedirs(PR, exist_ok=True); _g['OUT'] = PR
plat = [box((3.6, 0.3, 3.6), WOODD, (0, -0.15, 0))] + [box((0.12, 0.3, 3.6), IRON, (x, -0.15, 0)) for x in (-1.2, 0, 1.2)]
plat += [box((3.6, 1.1, 0.12), IRON, (0, 0.55, -1.74)), box((0.12, 1.1, 3.6), IRON, (-1.74, 0.55, 0)), box((0.12, 1.1, 3.6), IRON, (1.74, 0.55, 0))]
plat += [box((0.5, 1.0, 0.3), BRASS, (1.2, 0.5, -1.5))] + [box((0.1, 4.0, 0.1), IRON, (x, 2.0, -1.74)) for x in (-1.74, 1.74)] + [box((3.6, 0.1, 0.1), IRON, (0, 4.0, -1.74))]
B5.save('sg_lift_platform', merge(plat))
gate = [box((0.12, 3.4, 0.12), IRON, (0, 1.7, z)) for z in np.linspace(-1.95, 1.95, 11)] + [box((0.14, 0.14, 4.0), IRON, (0, y, 0)) for y in (0.4, 1.4, 2.4, 3.3)]
gate += [cyl(0.05, 0.3, IRON, (0, -0.1, z), sec=4, r2=0, rot=(math.pi, 0, 0)) for z in np.linspace(-1.95, 1.95, 11)]
B5.save('sg_shortcut_gate', merge(gate))
lev = [box((0.5, 1.0, 0.4), ST2, (0, 0.5, 0)), cyl(0.06, 0.9, IRON, (0, 1.4, 0), sec=6), ball_ := box((0.16, 0.16, 0.16), BRASS, (0, 1.9, 0))]
B5.save('sg_lever', merge(lev), lod=False)
_g['OUT'] = OUT
# --- manifest block (world points for the walk test and for Lucky's wiring)
r3 = lambda v: [round(float(x), 2) for x in v]
ramp_pts = []
for r, (a, b) in enumerate(RUNS):   # run, then across its turn landing (centre line of each lane) so the walker clears the run rails before turning
    ramp_pts += [r3(a + np.array([0, 0.08, 0])), r3(b + np.array([0, 0.08, 0]))]
    if r < NR - 1:
        zl = ZN + 2.0 if r % 2 == 0 else ZS - 2.0; ramp_pts += [r3((LX[r % 2], b[1] + 0.08, zl)), r3((LX[1 - r % 2], b[1] + 0.08, zl))]
dock_to_L0 = [r3((-2124.6, 20.45, -88.0)), r3((-2124.6, Y0 + 0.08, -76.0)), r3((-2104.0, Y0 + 0.08, -76.0))]
up = dock_to_L0 + [r3((-2098.2, Y0 + 0.08, -76.0)), r3((LX[0], Y0 + 0.08, -76.0))] + ramp_pts + [r3((-2104.0, YT + 0.08, -76.0)), r3((-2110.0, YT + 0.08, -76.0))] + [r3(np.array(p) + [0, 0.08, 0]) for p in SBP] + [r3(ext + [0, -0.5, 0])]
lift_bottom = r3((SH[0], Y0, SH[1])); lift_top = r3((SH[0], YT, SH[1]))
blk = {'note': 'stage 9: dock lift + locked shortcut ramp + skybridge (README Stage 9)', 'files': {'mesh': 'coast_isl_saltglass_lift', 'lod1': 'coast_isl_saltglass_lift_lod1', 'glow': 'coast_isl_saltglass_lift_glow', 'col': 'coast_isl_saltglass_lift_col'},
       'ramp': {'runs': NR, 'deg': DEG, 'run_m': RUN, 'rise_m': round(RISE * NR, 2), 'bottom': r3((LX[0], Y0, ZS)), 'top': r3((LX[1], YT, ZS))},
       'skybridge': {'a': r3(SB_A), 'b': r3(SB_E), 'len_m': round(float(math.hypot(u[0], u[2])), 1)},
       'gate': {'pos': r3((GX, Y0, -76.0)), 'yaw_deg': 90.0, 'size': [0.3, 3.4, 4.0], 'raise_m': 3.6, 'lever': r3((-2097.6, Y0, -77.4)), 'flag': 'saltglass_shortcut_open'},
       'lift': {'bottom': lift_bottom, 'top': lift_top, 'travel_m': round(YT - Y0, 2), 'speed': 6.0, 'door': 'north (+z)', 'call_bottom': r3((-2105.8, Y0, -77.7)), 'call_top': r3((-2105.8, YT, -77.7))},
       'routes': {'shortcut_up': up, 'dock_to_gate': dock_to_L0 + [r3((-2098.0, Y0 + 0.08, -76.0))], 'shortcut_down_to_lever': list(reversed(up))[:-3] + [r3((-2097.6, Y0 + 0.08, -76.6))],
                  'dock_to_lift': dock_to_L0 + [r3((SH[0], Y0 + 0.08, -79.0)), r3((SH[0], Y0 + 0.08, SH[1]))], 'lift_to_plateau': [r3((SH[0], YT + 0.08, -79.0)), r3((SH[0], YT + 0.08, -76.0)), r3((-2110.0, YT + 0.08, -76.0))] + [r3(np.array(p) + [0, 0.08, 0]) for p in SBP] + [r3(ext + [0, -0.5, 0])]}}
mp = os.path.join(ROOT5, 'stage5_manifest.json'); man = json.load(open(mp)); man['islands']['saltglass']['stage9'] = blk
man['stats'] = {**man.get('stats', {}), **{k: v for k, v in B5.STATS.items() if 'lift' in k or k.startswith('sg_')}}
json.dump(man, open(mp, 'w'), indent=1, default=float); print(json.dumps({k: blk[k] for k in ('ramp', 'skybridge', 'lift')}))
