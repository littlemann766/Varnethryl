#!/usr/bin/env python3
"""Beth: Tidewrack Sea STAGE 3 art: interiors of the three skiff-only sea caves (local sub-cells) + the Sunken Ward
underwater cell (world coords). Conventions as Stage 1/2: +Y up, metres, one vertex-colour surface per mesh, _lod1 <= 50%.
Cave cells: origin = cave entrance at the waterline, +Z = out to sea (matches the exterior mouth yaw in stage2_manifest),
the cave runs into -Z. Sunken Ward: world coords (map metres), water surface y = 0."""
import os, math, json
S1 = '/workspace/godot-art/ocean_stage1/tools/build_stage1.py'
_src = open(S1).read().split('\n'); _g = {'__file__': S1, '__name__': 'stage1_helpers'}
def _blk(start, stop):
    a_ = next(i for i, l in enumerate(_src) if l.startswith(start)) if start else 0; b_ = next(i for i, l in enumerate(_src) if i > a_ and l.startswith(stop)); return '\n'.join(_src[a_:b_])
exec(_blk(None, '# ---------------------------------------------------------------- islands'), _g)   # helpers only (no map)
exec(_blk('WOOD = C(', 'def find_water'), _g)
globals().update({k: v for k, v in _g.items() if not k.startswith('__')})
ROOT3 = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT = os.path.join(ROOT3, 'meshes'); os.makedirs(OUT, exist_ok=True); _g['OUT'] = OUT
STATS = _g['STATS']; STATS.clear(); save = _g['save']
import numpy as np, trimesh, fast_simplification
from scipy import ndimage
rng = np.random.default_rng(303)
G3 = ndimage.gaussian_filter(np.random.default_rng(5).normal(size=(48, 48, 48)), 2.2, mode='wrap'); G3 /= G3.std()
def n3(p, sc):
    q = (np.asarray(p, float) / sc).T % 48; return ndimage.map_coordinates(G3, q, order=1, mode='wrap')
SALT = C(150, 235, 245); SALT2 = C(90, 200, 235); SALTV = C(110, 170, 180); BONE = C(222, 214, 190); LANT = C(255, 196, 110); DARK = C(10, 10, 14)
R1 = C(70, 66, 64); R2 = C(52, 50, 52); R3 = C(38, 37, 40); WET = C(28, 30, 32); ALG = C(36, 62, 48); SAND = C(92, 86, 70)
MANI = {'caves': {}, 'sunken_ward': {}}
# ---------------------------------------------------------------- cave tube (inside-facing), path into -Z
def tube(path_fn, n, ring, depth, veins=None, seed=0):
    pts, ws, hs = zip(*[path_fn(t) for t in np.linspace(0, 1, n)]); pts = np.array(pts); ws = np.array(ws); hs = np.array(hs)
    tang = np.gradient(pts, axis=0); tang /= np.linalg.norm(tang, axis=1, keepdims=True); up = np.array([0, 1.0, 0])
    V = []; frames = []
    for k in range(n):
        side = np.cross(up, tang[k]); side /= np.linalg.norm(side); frames.append(side)
        yc = (hs[k] - depth) / 2; ay = (hs[k] + depth) / 2; ax = ws[k] / 2
        for r in range(ring):
            a = r * math.tau / ring; V.append(pts[k] + side * ax * math.cos(a) + up * (yc + ay * math.sin(a)))
    V = np.array(V)
    nn = n3(V + seed * 31, 7.0) * 0.6 + n3(V + seed * 17, 2.5) * 0.25
    ctr = np.repeat(pts, ring, 0); off = V - ctr; V = ctr + off * (1 + 0.16 * nn)[:, None]
    V[:, 1] = np.maximum(V[:, 1], -depth + 0.6 * nn)      # flattish floor under the water
    F = []
    for k in range(n - 1):
        for r in range(ring):
            a_ = k * ring + r; b_ = k * ring + (r + 1) % ring; F += [(a_, a_ + ring, b_), (b_, a_ + ring, b_ + ring)]   # inward winding
    V = np.vstack([V, pts[-1] + np.array([0, (hs[-1] - depth) / 2, 0])]); c0 = len(V) - 1
    for r in range(ring): F.append(((n - 1) * ring + r, c0, (n - 1) * ring + (r + 1) % ring))   # closed far end
    y = V[:, 1]; col = np.tile(R1, (len(V), 1))
    col[y > 8] = R2; col[y > 18] = R3
    col[(np.sin(y * 1.1 + nn[:len(V) - 1].mean() if False else y * 1.1) > 0.8) & (y > 3)] = C(84, 78, 72)
    col[(y > -1.2) & (y < 2.0)] = WET; col[(y > 0.2) & (y < 1.6) & (np.concatenate([nn, [0]]) > 0.2)] = ALG
    col[y < -1.2] = SAND
    if veins is not None:
        vm = (np.concatenate([n3(V[:-1] + 99, 3.0), [0]]) > 1.1) & (y > 2); col[vm] = veins
    m = trimesh.Trimesh(V, F, process=False); m.visual = trimesh.visual.ColorVisuals(m, vertex_colors=col)
    return m, pts, ws, hs, np.array(frames)
def wall_pt(pts, ws, hs, frames, depth, t, a, inset=0.6):
    k = int(np.clip(t, 0, 1) * (len(pts) - 1)); yc = (hs[k] - depth) / 2; ay = (hs[k] + depth) / 2; ax = ws[k] / 2 * inset
    return pts[k] + frames[k] * ax * math.cos(a) + np.array([0, yc + ay * math.sin(a) * inset, 0])
def bump(t, c, wdt): return math.exp(-((t - c) / wdt) ** 2)
def water_plane(pts, ws, margin=6):
    lo = pts.min(0) - ws.max() / 2 - margin; hi = pts.max(0) + ws.max() / 2 + margin
    m = trimesh.creation.box((hi[0] - lo[0], 0.01, hi[2] - lo[2])); m.apply_translation(((hi[0] + lo[0]) / 2, 0, (hi[2] + lo[2]) / 2)); return m
def portal_card(w, h):   # daylight seen back out of the entrance (unshaded, see shaders/cave_portal)
    m = trimesh.Trimesh([(-w / 2, -1, 1.5), (w / 2, -1, 1.5), (w / 2, h, 1.5), (-w / 2, h, 1.5)], [(0, 1, 2), (0, 2, 3), (0, 2, 1), (0, 3, 2)], process=False)
    m.visual = trimesh.visual.TextureVisuals(uv=np.array([(0, 0), (1, 0), (1, 1), (0, 1)])); return m
def crystal(p, d, length, r, col): # hexagonal prism with a point, pointing along d
    d = np.array(d, float); d /= np.linalg.norm(d)
    m = merge([cyl(r, length * 0.75, col, (0, length * 0.375, 0), sec=6), cyl(r, length * 0.25, col, (0, length * 0.75 + length * 0.125, 0), sec=6, r2=0)])
    m.apply_transform(trimesh.geometry.align_vectors((0, 1, 0), d)); m.apply_translation(p); return m
def lantern(p):
    return merge([cyl(0.25, 0.5, LANT, (p[0], p[1], p[2]), sec=6), cyl(0.3, 0.12, IRON, (p[0], p[1] + 0.3, p[2]), sec=6), cyl(0.3, 0.12, IRON, (p[0], p[1] - 0.3, p[2]), sec=6)])
def save_cell(name, tubem, glow, props_, water, extra=None):
    save(f'{name}_shell', tubem)
    v3, f3 = fast_simplification.simplify(tubem.vertices.astype(np.float32), tubem.faces.astype(np.int64), target_reduction=0.85); trimesh.Trimesh(v3, f3).export(os.path.join(OUT, f'{name}_col.glb'))
    if glow is not None: save(f'{name}_glow', glow)
    if props_ is not None: save(f'{name}_props', props_)
    water.export(os.path.join(OUT, f'{name}_water.glb'))
    portal_card(20, 18).export(os.path.join(OUT, f'{name}_portal.glb'))
# ---------------------------------------------------------------- 1) Echo Grotto: winding, hanging saltglass, echo pool chamber
D_ = 6.0
def echo_path(t):
    z = -t * 190; x = 14 * math.sin(t * 5.2) + 8 * math.sin(t * 11)
    w = 16 + 26 * bump(t, 0.55, 0.12) + 22 * bump(t, 0.95, 0.08); h = 14 + 14 * bump(t, 0.55, 0.12) + 9 * bump(t, 0.95, 0.08) - 3 * bump(t, 0.3, 0.06)
    return (x, 0, z), w, h
shell, P, W, Hh, Fr = tube(echo_path, 130, 26, D_, veins=SALTV, seed=1)
glow = []; pr = []
for k in range(190):
    t = rng.uniform(0.04, 1.0); a = math.pi / 2 + rng.normal(0, 0.45); p = wall_pt(P, W, Hh, Fr, D_, t, a, rng.uniform(0.85, 0.97))
    glow.append(crystal(p, (rng.normal(0, 0.15), -1, rng.normal(0, 0.15)), rng.uniform(0.8, 3.2) * (1.6 if bump(t, 0.55, 0.12) > 0.5 else 1), rng.uniform(0.12, 0.32), SALT if k % 3 else SALT2))
for k in range(60):   # crystal beds on the ledges just above the waterline
    t = rng.uniform(0.1, 1.0); a = rng.choice([0.15, math.pi - 0.15]) + rng.normal(0, 0.1); p = wall_pt(P, W, Hh, Fr, D_, t, a, 0.9); p[1] = max(p[1], 0.6)
    for j in range(rng.integers(2, 5)): glow.append(crystal(p + rng.normal(0, 0.5, 3) * (1, 0, 1), (rng.normal(0, 0.4), 1, rng.normal(0, 0.4)), rng.uniform(0.5, 1.8), rng.uniform(0.1, 0.25), SALT))
for k in range(70):   # rock dripstones (ceiling) + stalagmite stubs (ledges)
    t = rng.uniform(0.03, 1.0); a = math.pi / 2 + rng.normal(0, 0.6); p = wall_pt(P, W, Hh, Fr, D_, t, a, 0.95)
    pr.append(cyl(rng.uniform(0.3, 0.9), rng.uniform(1.5, 5), R2, tuple(p - np.array([0, 1.5, 0])), (math.pi, 0, 0), 6, 0))
# echo pool: ring of standing stones in the end chamber + a ledge with an old carved bell-stone
ec = P[int(0.95 * (len(P) - 1))]
for k in range(9): a = k * math.tau / 9; pr.append(rock((ec[0] + math.cos(a) * 9, 0.2, ec[2] + math.sin(a) * 9), rng.uniform(1.2, 2.2), 700 + k, 1.4, R1))
pr.append(T(merge([cyl(1.6, 2.2, C(120, 116, 104), (0, 1.1, 0), sec=10, r2=1.2), cyl(0.6, 0.5, C(120, 116, 104), (0, 2.45, 0), sec=8)]), (ec[0] + 2, 0.4, ec[2] - 3)))
save_cell('cave_echo_grotto', shell, merge(glow), merge(pr), water_plane(P, W))
MANI['caves']['echo_grotto'] = {'length_m': 190, 'chambers': [{'name': 'crystal hall', 't': 0.55, 'pos': P[int(0.55 * 129)].tolist()}, {'name': 'echo pool', 't': 0.95, 'pos': ec.tolist()}],
    'skiff_path': P[::10].tolist(), 'lights': [P[int(t * 129)].tolist() for t in (0.2, 0.45, 0.6, 0.8, 0.95)], 'min_width_m': float(W.min()), 'min_ceiling_m': float(Hh.min())}
# ---------------------------------------------------------------- 2) Glasswyrm Cavern: tunnel into a great glowing arena with an old skeleton
def wyrm_path(t):
    z = -t * 170; x = 10 * math.sin(t * 3.5)
    a = 1 / (1 + math.exp(-(t - 0.55) * 18)); w = 20 + 76 * a; h = 18 + 26 * a
    return (x, 0, z), w, h
shell, P, W, Hh, Fr = tube(wyrm_path, 120, 30, 8.0, veins=SALTV, seed=2)
glow = []; pr = []
for k in range(110):
    t = rng.uniform(0.15, 1.0); a = rng.uniform(0.05, math.pi - 0.05); p = wall_pt(P, W, Hh, Fr, 8.0, t, a, rng.uniform(0.82, 0.95))
    nrm = (np.array([P[int(t * 119)][0], p[1], P[int(t * 119)][2]]) - p); nrm[1] = abs(nrm[1]) * 0.3 + 0.2
    big = 2.2 if t > 0.6 else 1.0
    for j in range(rng.integers(3, 7)): glow.append(crystal(p + rng.normal(0, 0.8, 3), nrm + rng.normal(0, 0.4, 3), rng.uniform(1.0, 4.5) * big, rng.uniform(0.2, 0.55) * big, SALT2 if j % 2 else SALT))
ac = P[int(0.85 * 119)]   # arena centre
for k in range(12):   # giant glass spires rising from the arena shallows
    a = k * math.tau / 12 + rng.uniform(-.2, .2); r = rng.uniform(26, 38); glow.append(crystal((ac[0] + math.cos(a) * r, -1.5, ac[2] + math.sin(a) * r), (rng.normal(0, 0.2), 1, rng.normal(0, 0.2)), rng.uniform(8, 18), rng.uniform(1.0, 2.0), SALT))
# old skeleton: spine arc half-submerged, ribcage, skull with glass teeth
sk = []
for k in range(26):
    t = k / 25; sp = np.array([ac[0] - 20 + t * 40, 1.5 + 5 * math.sin(t * math.pi) - 2.5, ac[2] + 8 * math.sin(t * 4)]); sk.append(ball(1.3 - 0.6 * t, BONE, tuple(sp), 1, (1.3, 1, 1)))
    if 3 < k < 18 and k % 2 == 0:
        for sx in (-1, 1): sk.append(line(sp, sp + np.array([0, -4.5, sx * 6]), 0.35, BONE)); sk.append(line(sp + np.array([0, -4.5, sx * 6]), sp + np.array([0.8, -8, sx * 4.5]), 0.3, BONE))
sh_ = np.array([ac[0] - 24, 1.5, ac[2] + 2]); sk += [ball(3.0, BONE, tuple(sh_), 1, (1.6, 1.0, 1.1)), ball(1.6, BONE, tuple(sh_ + np.array([-3.5, -1.2, 0])), 1, (1.4, 0.5, 0.9)), ball(0.7, DARK, tuple(sh_ + np.array([-1.2, 0.8, 1.6])), 1), ball(0.7, DARK, tuple(sh_ + np.array([-1.2, 0.8, -1.6])), 1)]
for k in range(8): glow.append(crystal(sh_ + np.array([-4.2 + k * 0.35, -1.0, rng.uniform(-0.8, 0.8)]), (0, -1, 0), 1.2, 0.15, SALT))
pr += sk
for k in range(16):   # rock shelf ring around the arena (boss coils around it; collision too)
    a = k * math.tau / 16; pr.append(rock((ac[0] + math.cos(a) * 42, 0.8, ac[2] + math.sin(a) * 42), rng.uniform(4, 7), 900 + k, 0.45, R1))
save_cell('cave_glasswyrm_cavern', shell, merge(glow), merge(pr), water_plane(P, W))
MANI['caves']['glasswyrm_cavern'] = {'length_m': 170, 'arena': {'pos': ac.tolist(), 'radius_m': 42}, 'skiff_path': P[::10].tolist(), 'lights': [P[int(t * 119)].tolist() for t in (0.3, 0.6, 0.85)] + [ac.tolist()], 'boss': 'Glasswyrm (Stage 3 fight; boss mesh not in this drop)'}
# ---------------------------------------------------------------- 3) Smugglers' Throat: tall narrow cleft, rope bridge, lanterns, hidden jetty
def smug_path(t):
    z = -t * 230; x = 9 * math.sin(t * 7.5) + 5 * math.sin(t * 17)
    w = 11 + 3 * math.sin(t * 13) + 20 * bump(t, 0.98, 0.07); h = 22 + 8 * math.sin(t * 5) + 6 * bump(t, 0.98, 0.07)
    return (x, 0, z), w, h
shell, P, W, Hh, Fr = tube(smug_path, 160, 24, 5.0, seed=3)
glow = []; pr = []
lpos = []
for k in range(16):   # lanterns on iron hooks along alternating walls
    t = 0.05 + k * 0.058; a = 0.35 if k % 2 else math.pi - 0.35; p = wall_pt(P, W, Hh, Fr, 5.0, t, a, 0.92); p[1] = 3.5
    ctr = np.array([P[int(t * 159)][0], 3.5, P[int(t * 159)][2]]); dv = (ctr - p) / (np.linalg.norm(ctr - p) + 1e-6)
    pr.append(line(p, p + dv * 0.9, 0.06, IRON)); glow.append(lantern(p + dv * 0.9 - np.array([0, 0.5, 0]))); lpos.append((p + dv * 0.9).tolist())
bt = 0.42; bk = int(bt * 159); bc = P[bk]; side = Fr[bk]; bw = W[bk] + 4; by = 14.0   # rope bridge across the cleft, high up
for j in range(16):
    u = j / 15 - 0.5; sag = -1.2 * (1 - (2 * u) ** 2); pr.append(T(box((0.7, 0.12, 1.8), WOOD), tuple(bc + side * u * bw + np.array([0, by + sag, 0])), (0, math.atan2(side[0], side[2]), 0)))
for dz in (-0.9, 0.9):
    fw = np.cross(side, (0, 1, 0)) * dz
    for j in range(15):
        u0 = j / 15 - 0.5; u1 = (j + 1) / 15 - 0.5; s0 = -1.2 * (1 - (2 * u0) ** 2); s1 = -1.2 * (1 - (2 * u1) ** 2)
        pr.append(line(bc + side * u0 * bw + fw + np.array([0, by + s0 + 1.0, 0]), bc + side * u1 * bw + fw + np.array([0, by + s1 + 1.0, 0]), 0.05, C(150, 120, 80)))
for sx in (-1, 1): pr.append(box((2.5, 0.4, 3.0), WOOD, tuple(bc + side * sx * (bw / 2 + 0.6) + np.array([0, by - 0.2, 0]))))
glow.append(lantern(bc + side * (bw / 2 - 0.5) + np.array([0, by + 2.2, 0])))
jc = P[int(0.98 * 159)]; jy = 0   # hidden jetty chamber at the end
pr.append(dock((jc[0] - 4, 0, jc[2] + 6), math.pi, 16, 3.5))
for k in range(10): pr.append(box((1.3, 1.1, 1.3), WOOD if k % 2 else C(140, 100, 60), (jc[0] - 8 + (k % 5) * 1.6, 2.1 + (k // 5) * 1.15, jc[2] - 9)))
for k in range(4): pr.append(cyl(0.6, 1.4, C(120, 80, 50), (jc[0] + 2 + k * 1.5, 2.2, jc[2] - 10), sec=10))
pr.append(box((14, 1.4, 6), R1, (jc[0] - 3, 1.0, jc[2] - 10)))   # rock landing
for k in range(8): pr.append(box((2.2, 0.5, 1.0), C(110, 104, 94), (jc[0] + 6, 1.8 + k * 0.9, jc[2] - 12 - k * 0.9)))   # stair up to a door
pr.append(box((2.6, 3.4, 0.4), DKW, (jc[0] + 6, 9.8, jc[2] - 20.4)))
for p in [(jc[0] - 6, 3.2, jc[2] - 8), (jc[0] + 4, 3.2, jc[2] - 8), (jc[0] + 6, 11.8, jc[2] - 20)]: glow.append(lantern(p)); lpos.append(list(p))
save_cell('cave_smugglers_throat', shell, merge(glow), merge(pr), water_plane(P, W))
MANI['caves']['smugglers_throat'] = {'length_m': 230, 'bridge': {'pos': (bc + np.array([0, by, 0])).tolist(), 'span_m': float(bw)}, 'jetty': [jc[0] - 4, 0, jc[2] + 6], 'lanterns': lpos, 'skiff_path': P[::10].tolist(), 'min_width_m': float(W.min())}
# ---------------------------------------------------------------- 4) Sunken Ward underwater cell (world coords)
cx, cz = -1300.0, 400.0; X0, X1, Z0, Z1 = cx - 280, cx + 280, cz - 300, cz + 300; SB = -30.0
sp = 5.0; xs = np.arange(X0, X1 + 0.1, sp); zs = np.arange(Z0, Z1 + 0.1, sp); GX, GZ = np.meshgrid(xs, zs)
pts = np.stack([GX.ravel(), np.zeros(GX.size), GZ.ravel()], 1)
hgt = SB + n3(pts * np.array([1, 0, 1]) + 7, 18.0) * 2.4 + n3(pts * np.array([1, 0, 1]) + 3, 5.0) * 0.6
street = (np.abs(((GX.ravel() - cx) + 25) % 50 - 25) < 4.5) | (np.abs(((GZ.ravel() - cz) + 25) % 50 - 25) < 4.5)
inside = (np.abs(GX.ravel() - cx) < 230) & (np.abs(GZ.ravel() - cz) < 250)
plaza = np.hypot(GX.ravel() - (cx + 10), GZ.ravel() - (cz - 20)) < 34
hgt = np.where(inside & (street | plaza), SB + 1.0, hgt); edge = 1 - np.clip(np.maximum(np.abs(GX.ravel() - cx) - 230, np.abs(GZ.ravel() - cz) - 250) / 50, 0, 1)
hgt = np.where(inside, hgt, hgt - (1 - edge) * 6)     # the seabed drops away outside the district
pts[:, 1] = hgt
nx_, nz_ = len(xs), len(zs); F = []
for j in range(nz_ - 1):
    for i in range(nx_ - 1):
        a = j * nx_ + i; F += [(a, a + nx_, a + 1), (a + 1, a + nx_, a + nx_ + 1)]
bed = trimesh.Trimesh(pts, F, process=False)
col = np.tile(C(120, 112, 88), (len(pts), 1)); nn = n3(pts + 11, 6.0)
col[nn > 0.6] = C(96, 100, 78); col[nn < -0.8] = C(140, 130, 104)
col[inside & street] = C(128, 124, 112); col[inside & street & (nn > 0.5)] = C(86, 104, 84)    # paving with algae patches
col[plaza] = C(140, 132, 116)
bed.visual = trimesh.visual.ColorVisuals(bed, vertex_colors=col); save('sw_seabed', bed)
v3, f3 = fast_simplification.simplify(bed.vertices.astype(np.float32), bed.faces.astype(np.int64), target_reduction=0.9); trimesh.Trimesh(v3, f3).export(os.path.join(OUT, 'sw_seabed_col.glb'))
SAND_ST = C(196, 182, 150); SAND_D = C(160, 148, 122); ALGW = C(80, 110, 80)
def ruined_house(p, yaw, w, d, h, seed):
    r = np.random.default_rng(seed); parts = []; t = 0.7
    for (sx, sz, L, along_x) in [(0, -d / 2, w, True), (0, d / 2, w, True), (-w / 2, 0, d, False), (w / 2, 0, d, False)]:
        segs = int(L / 2.0)
        for k in range(segs):
            u = -L / 2 + (k + 0.5) * L / segs; hh = h * r.uniform(0.35, 1.0) if r.uniform() < 0.6 else h
            if not along_x and sx < 0 and abs(u) < 1.6: continue        # doorway
            if r.uniform() < 0.12: continue                                  # collapsed gap / window
            q = (sx + (u if along_x else 0), hh / 2, sz + (0 if along_x else u)); sz_ = (L / segs + 0.05, hh, t) if along_x else (t, hh, L / segs + 0.05)
            b = box(sz_, SAND_ST if k % 3 else SAND_D, q); vy = b.vertices[:, 1]; b.visual.vertex_colors[vy < 1.6] = ALGW; parts.append(b)
    if r.uniform() < 0.45: parts.append(T(box((w + 0.6, 0.5, d * 0.6), C(110, 80, 60)), (0, h - 0.3, -d * 0.2), (r.uniform(-.25, .25), 0, r.uniform(-.2, .2))))   # half-fallen roof
    return T(merge(parts), p, (0, yaw, 0))
bl = []; blk_rng = np.random.default_rng(77)
for bx in np.arange(cx - 225, cx + 226, 50):   # block centres (streets run on cx+50k / cz+50k)
    for bz in np.arange(cz - 225, cz + 226, 50):
        if math.hypot(bx - (cx + 10), bz - (cz - 20)) < 55: continue
        if blk_rng.uniform() < 0.15: continue
        for k in range(blk_rng.integers(1, 4)):
            ox, oz = blk_rng.uniform(-9, 9), blk_rng.uniform(-9, 9); bl.append(ruined_house((bx + ox, SB + 0.8, bz + oz), blk_rng.choice([0, math.pi / 2]), blk_rng.uniform(7, 12), blk_rng.uniform(7, 12), blk_rng.uniform(5, 12), abs(int(bx * 7 + bz * 3 + k))))
save('sw_buildings', merge(bl))
# the copper dome hall (top of the dome breaks the surface: matches coast_sunken_ward_surface), colonnade, drowned towers, arcade
dc = (cx + 10, cz - 20); mk = []
mk.append(cyl(14.0, -10.5 - SB, SAND_ST, (dc[0], (SB - 10.5) / 2, dc[1]), sec=24))
dome = trimesh.creation.icosphere(2, 14); dome.vertices[:, 1] = np.abs(dome.vertices[:, 1]); mk.append(T(paint(dome, C(80, 140, 120)), (dc[0], -10.5, dc[1]), scale=(1, 0.8, 1)))
for k in range(4): a = k * math.pi / 2; mk.append(box((5, 9, 2.0), DARK, (dc[0] + math.cos(a) * 13.6, SB + 5.5, dc[1] + math.sin(a) * 13.6), (0, -a + math.pi / 2, 0)))   # 4 dark doorways
for k in range(18):
    a = k * math.tau / 18; hh = 14 if k % 5 else 6; mk.append(cyl(1.0, hh, SAND_ST, (dc[0] + math.cos(a) * 22, SB + hh / 2, dc[1] + math.sin(a) * 22), sec=10))
    if k % 5 == 0: mk.append(T(cyl(1.0, 10, SAND_D, (0, 0, 0), sec=10), (dc[0] + math.cos(a) * 26, SB + 1.0, dc[1] + math.sin(a) * 26), (math.pi / 2, a, 0)))   # fallen column
for (ox, oz) in [(-60, -40), (70, 90)]: mk.append(cyl(5.5, -9 - SB, C(160, 156, 146), (cx + ox, (SB - 9) / 2, cz + oz), sec=14))
for k in range(12): x = cx - 120 + k * 9; mk.append(box((1.4, -8 - SB, 1.4), C(190, 184, 170), (x, (SB - 8) / 2, cz + 150)))
for k in range(6):   # drowned warden statues on the plaza
    a = k * math.tau / 6 + 0.3; p = np.array([dc[0] + math.cos(a) * 30, SB + 1.0, dc[1] + math.sin(a) * 30])
    mk.append(merge([box((2.4, 1.5, 2.4), SAND_D, tuple(p + [0, 0.75, 0])), cyl(0.9, 4.5, C(110, 128, 118), tuple(p + [0, 3.8, 0]), sec=8, r2=0.6), ball(0.75, C(110, 128, 118), tuple(p + [0, 6.6, 0])), line(p + [0.9, 1.5, 0], p + [0.9, 8.5, 0], 0.12, C(90, 110, 100))]))
save('sw_landmarks', merge(mk))
# kelp (sway via COLOR.a = height fraction -> shaders/kelp_sway), seabed rocks, sponges, rubble
kp = []
for k in range(320):
    x = rng.uniform(X0 + 10, X1 - 10); z = rng.uniform(Z0 + 10, Z1 - 10)
    if abs(x - cx) < 225 and abs(z - cz) < 245 and rng.uniform() < 0.75: continue
    base = SB - 0.5; L = rng.uniform(6, 22); segs = 8; wdt = rng.uniform(0.5, 1.1); yaw = rng.uniform(0, math.tau); vv = []; cc = []; ff = []
    for s in range(segs + 1):
        t = s / segs; vv += [(x - math.cos(yaw) * wdt / 2, base + t * L, z - math.sin(yaw) * wdt / 2), (x + math.cos(yaw) * wdt / 2, base + t * L, z + math.sin(yaw) * wdt / 2)]
        g = (60 + int(40 * t), 110 + int(40 * t), 50, int(255 * t)); cc += [g, g]
    for s in range(segs): i = 2 * s; ff += [(i, i + 1, i + 2), (i + 1, i + 3, i + 2), (i, i + 2, i + 1), (i + 1, i + 2, i + 3)]
    m = trimesh.Trimesh(vv, ff, process=False); m.visual = trimesh.visual.ColorVisuals(m, vertex_colors=np.array(cc, np.uint8)); kp.append(m)
save('sw_kelp', merge(kp))
rb = []
for k in range(260):
    x = rng.uniform(X0, X1); z = rng.uniform(Z0, Z1)
    rb.append(rock((x, SB + rng.uniform(-0.5, 0.5), z), rng.uniform(0.6, 2.4), 3000 + k, 0.6, C(96, 92, 84) if k % 2 else C(76, 86, 74)))
    if k % 3 == 0: rb.append(ball(rng.uniform(0.3, 0.8), [C(200, 110, 90), C(220, 170, 80), C(150, 90, 160)][k % 3], (x + 1.5, SB + 0.4, z), 1, (1, 0.8, 1), 0.3, k))
save('sw_rubble', merge(rb))
# light shafts (unshaded additive cones from the surface) + surface seen from below
sh = []
for k in range(14):
    x = cx + rng.uniform(-200, 200); z = cz + rng.uniform(-220, 220); r = rng.uniform(4, 10); L = -SB + 2
    m = trimesh.creation.cone(r * 2.2, L, sections=10); m.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, (1, 0, 0)))
    m.apply_translation((x, 0, z)); m.apply_transform(trimesh.transformations.rotation_matrix(0.18, (0, 0, 1), (x, 0, z))); sh.append(m)
shafts = trimesh.util.concatenate(sh); shafts.export(os.path.join(OUT, 'sw_light_shafts.glb'))
surf = trimesh.creation.box((X1 - X0 + 200, 0.01, Z1 - Z0 + 200)); surf.apply_translation((cx, -0.05, cz)); surf.export(os.path.join(OUT, 'sw_surface_under.glb'))
MANI['sunken_ward'] = {'rect': [X0, Z0, X1, Z1], 'seabed_y': SB, 'surface_y': 0, 'dive_start': [-1300, -2, 300], 'dome': [dc[0], SB, dc[1]], 'street_grid_m': 50,
    'env': {'fog_color': [0.08, 0.32, 0.36], 'fog_density': 0.022, 'ambient': [0.25, 0.5, 0.55], 'note': 'switch the Environment when the camera goes under y=0'}}
json.dump({'stats': STATS, **MANI}, open(os.path.join(OUT, 'stage3_manifest.json'), 'w'), indent=1, default=float)
print('DONE')
