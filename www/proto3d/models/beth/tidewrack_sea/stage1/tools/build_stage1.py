#!/usr/bin/env python3
"""Beth: Tidewrack Sea STAGE 1 art builder (Archipelago region A + Brinecrown Coil + ship upgrade add-ons).
Pure numpy/trimesh, no Blender. Godot coords: +Y up, metres, map origin = Archipelago centre, north = -Z.
Every mesh = ONE vertex-coloured surface (1 draw call) + a _lod1 at <=50% tris. Outputs to ../meshes."""
import numpy as np, trimesh, json, math, os, fast_simplification
from scipy import ndimage
from scipy.spatial import cKDTree
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); OUT = os.path.join(ROOT, 'meshes'); os.makedirs(OUT, exist_ok=True)
SHIPS = os.path.join(os.path.dirname(ROOT), 'ships')
rng = np.random.default_rng(7); STATS = {}
def C(*c): return np.array(c + ((255,) if len(c) == 3 else ()), np.uint8)
def paint(m, col):
    m.visual = trimesh.visual.ColorVisuals(m, vertex_colors=np.tile(col, (len(m.vertices), 1))); return m
def T(m, pos=(0, 0, 0), rot=(0, 0, 0), scale=None):
    m = m.copy()
    if scale is not None: m.apply_scale(scale)
    for ax, a in zip([(1, 0, 0), (0, 1, 0), (0, 0, 1)], rot):
        if a: m.apply_transform(trimesh.transformations.rotation_matrix(a, ax))
    m.apply_translation(pos); return m
def box(size, col, pos=(0, 0, 0), rot=(0, 0, 0)): return T(paint(trimesh.creation.box(size), col), pos, rot)
def cyl(r, h, col, pos=(0, 0, 0), rot=(0, 0, 0), sec=10, r2=None):
    m = trimesh.creation.cone(r, h, sections=sec) if r2 == 0 else trimesh.creation.cylinder(r, h, sections=sec)
    if r2 not in (None, 0):  # taper
        v = m.vertices; t = (v[:, 2] - v[:, 2].min()) / max(1e-6, np.ptp(v[:, 2])); k = 1 + (r2 / r - 1) * t; v[:, 0] *= k; v[:, 1] *= k
    if r2 == 0: m.apply_translation((0, 0, -h / 2 + 0))
    m.apply_transform(trimesh.transformations.rotation_matrix(-math.pi / 2, (1, 0, 0)))  # z-axis -> y-axis
    return T(paint(m, col), pos, rot)
def ball(r, col, pos=(0, 0, 0), sub=1, scale=None, noise=0.0, seed=0):
    m = trimesh.creation.icosphere(sub, r)
    if noise: rr = np.random.default_rng(seed); m.vertices *= (1 + rr.uniform(-noise, noise, (len(m.vertices), 1)))
    return T(paint(m, col), pos, scale=scale)
def line(a, b, r, col, sec=5):
    a = np.array(a, float); b = np.array(b, float); d = b - a; L = np.linalg.norm(d)
    m = paint(trimesh.creation.cylinder(r, L, sections=sec), col)
    m.apply_transform(trimesh.geometry.align_vectors((0, 0, 1), d / L)); m.apply_translation((a + b) / 2); return m
def merge(parts): return trimesh.util.concatenate([p for p in parts if p is not None])
def save(name, m, lod=True, ratio=0.5):
    m = m.copy(); m.merge_vertices(merge_tex=True, merge_norm=True) if False else None
    vcol = np.array(m.visual.vertex_colors).copy(); vcol[:, :3] = np.round((vcol[:, :3] / 255.0) ** 2.2 * 255).astype(np.uint8)  # glTF COLOR_0 is linear
    m.visual = trimesh.visual.ColorVisuals(m, vertex_colors=vcol)
    p = os.path.join(OUT, name + '.glb'); m.export(p); STATS[name] = {'tris': int(len(m.faces))}
    if lod:
        rr_ = ratio * 0.9
        while True:
            v2, f2 = fast_simplification.simplify(np.asarray(m.vertices, np.float32), np.asarray(m.faces, np.int64), target_reduction=1 - rr_)
            if len(f2) <= ratio * len(m.faces) or rr_ < 0.1: break
            rr_ *= 0.85
        col = m.visual.vertex_colors[cKDTree(m.vertices).query(v2)[1]]
        l = trimesh.Trimesh(v2, f2, process=False); l.visual = trimesh.visual.ColorVisuals(l, vertex_colors=col)
        if len(f2) > ratio * len(m.faces):  # simplifier floor on tiny boxes: drop the smallest detail pieces (crates, bollards) in lod1
            parts_ = sorted(l.split(only_watertight=False), key=lambda p: p.area); tot = len(f2)
            while tot > ratio * len(m.faces) and parts_: tot -= len(parts_.pop(0).faces)
            l = trimesh.util.concatenate(parts_); v2, f2 = l.vertices, l.faces; col = m.visual.vertex_colors[cKDTree(m.vertices).query(v2)[1]]; l = trimesh.Trimesh(v2, f2, process=False); l.visual = trimesh.visual.ColorVisuals(l, vertex_colors=col)
        l.export(os.path.join(OUT, name + '_lod1.glb')); STATS[name]['lod1'] = int(len(f2)); STATS[name]['lod1_pct'] = round(100 * len(f2) / len(m.faces), 1)
    print(name, STATS[name])
# ---------------------------------------------------------------- islands from the v4 land mask
D = np.load(os.path.join(ROOT, 'map', 'tidewrack_land_v4.npz')); LF = D['land_f']; N1 = D['N1']; S = LF.shape[0]; pm = S / 6000.0
def px(x, z): return S / 2 + x * pm, S / 2 + z * pm
X0, Z0, X1, Z1 = -1200, -1300, 1500, 1300
def height_field(lf, n):
    land = np.where(lf > 0, np.where(lf < 18, lf * 0.09, 1.6 + (lf - 18) * (0.11 + 0.05 * n) + np.clip(n, 0, None) * 9), 0)
    cliff = (n > 0.8) & (lf > 0)
    land = np.where(cliff, np.maximum(land, np.clip(lf, 0, 12) * 1.6 + (lf > 12) * (lf - 12) * 0.12), land)
    sea = np.maximum(lf * 0.18, -12.0)
    return np.where(lf > 0, np.minimum(land, 70), sea)
def sample(x, z):
    i, j = px(x, z); return float(height_field(ndimage.map_coordinates(LF, [[j], [i]], order=1), ndimage.map_coordinates(N1, [[j], [i]], order=1))[0])
def shore_dir(x, z):  # unit vector from land towards the sea
    i, j = px(x, z); g = np.gradient(ndimage.gaussian_filter(LF, 2)); gx = g[1][int(j), int(i)]; gz = g[0][int(j), int(i)]; v = -np.array([gx, gz]); return v / (np.linalg.norm(v) + 1e-9)
def nearest_shore(x, z, want_land=True):
    i0, j0 = px(x, z); best = None
    for r in range(0, 120, 1):
        for a in np.linspace(0, 2 * math.pi, 24 + r, endpoint=False):
            i = int(i0 + math.cos(a) * r); j = int(j0 + math.sin(a) * r)
            if 0 < LF[j, i] < 4: best = ((i - S / 2) / pm, (j - S / 2) / pm); break
        if best: break
    return best or (x, z)
# islets + rocks from the map's scatter live only in `solid`: give them a signed field too so the 3D matches the shore texture
_inside = ndimage.distance_transform_edt(D['solid']) / pm; _out = D['dist_m']
LF = np.where(D['solid'] > 0, np.maximum(LF, _inside * 1.4), np.maximum(LF, -_out)).astype(np.float32)
step = 2
i0, j0 = map(int, px(X0, Z0)); i1, j1 = map(int, px(X1, Z1))
lf = LF[j0:j1:step, i0:i1:step]; n = N1[j0:j1:step, i0:i1:step]; H = height_field(lf, n)
keep = lf > -45
gz, gx = np.mgrid[j0:j1:step, i0:i1:step]; WXg = (gx - S / 2) / pm; WZg = (gz - S / 2) / pm
idx = -np.ones(lf.shape, int); idx[keep] = np.arange(keep.sum())
V = np.stack([WXg[keep], H[keep], WZg[keep]], 1)
q = keep[:-1, :-1] & keep[1:, :-1] & keep[:-1, 1:] & keep[1:, 1:]
a = idx[:-1, :-1][q]; b = idx[:-1, 1:][q]; c_ = idx[1:, :-1][q]; d = idx[1:, 1:][q]
Fc = np.concatenate([np.stack([a, c_, b], 1), np.stack([b, c_, d], 1)])
isl = trimesh.Trimesh(V, Fc, process=False)
# drop under-water-only patches far from land (keep a shallow apron); colour by height + slope
nrm = isl.vertex_normals; slope = 1 - np.abs(nrm[:, 1]); h = V[:, 1]; nn = n[keep]
col = np.zeros((len(V), 4), np.uint8); col[:, 3] = 255
col[:] = C(84, 128, 62); col[h > 30] = C(70, 100, 54); col[(h > 45)] = C(110, 112, 98)
col[(h < 2.2)] = C(214, 196, 140); col[h < 0] = C(170, 160, 120); col[h < -4] = C(110, 120, 105)
rock = (slope > 0.45) & (h > 0.5); col[rock] = C(108, 100, 92); col[(slope > 0.65) & (h > 0)] = C(76, 70, 66)
isl.visual = trimesh.visual.ColorVisuals(isl, vertex_colors=col)
# simplify the flat sea-bed apron hard, keep the land: decimate whole mesh to a budget
v2, f2 = fast_simplification.simplify(isl.vertices.astype(np.float32), isl.faces.astype(np.int64), target_reduction=max(0, 1 - 150000 / len(isl.faces)))
isl2 = trimesh.Trimesh(v2, f2, process=False); isl2.visual = trimesh.visual.ColorVisuals(isl2, vertex_colors=col[cKDTree(V).query(v2)[1]])
save('arch_islands', isl2)
# collider: coarse land-only hull of the islands (y>-1)
v3, f3 = fast_simplification.simplify(v2, f2, target_reduction=0.93); trimesh.Trimesh(v3, f3).export(os.path.join(OUT, 'arch_islands_col.glb'))
# shore-distance texture for the water shader (region A, 1 px = 3 m, R = metres to land /255*255m)
from PIL import Image
dm = np.clip(D['dist_m'][j0:j1, i0:i1], 0, 255).astype(np.uint8); Image.fromarray(dm).save(os.path.join(ROOT, 'shaders', 'arch_shore_dist.png'))
json.dump({'x0': X0, 'z0': Z0, 'x1': X1, 'z1': Z1, 'px_m': 1 / pm, 'note': 'R channel = metres to nearest land (0..255)'}, open(os.path.join(ROOT, 'shaders', 'arch_shore_dist.json'), 'w'), indent=1, default=float)
# ---------------------------------------------------------------- props
WOOD = C(112, 78, 48); DKW = C(70, 50, 34); STONE = C(150, 145, 135); DST = C(96, 92, 88); ROOF = C(150, 62, 44); ROOF2 = C(60, 84, 120); PLAST = C(222, 210, 186); BRASS = C(196, 150, 60); IRON = C(60, 62, 66)
def house(p, yaw, w, d, hgt, roof):
    b = box((w, hgt, d), PLAST, (0, hgt / 2, 0)); r = trimesh.creation.extrude_triangle if False else None
    prism = trimesh.Trimesh([(-w / 2 - .3, 0, -d / 2 - .3), (w / 2 + .3, 0, -d / 2 - .3), (0, w * 0.45, -d / 2 - .3), (-w / 2 - .3, 0, d / 2 + .3), (w / 2 + .3, 0, d / 2 + .3), (0, w * 0.45, d / 2 + .3)],
                            [(0, 2, 1), (3, 4, 5), (0, 3, 5), (0, 5, 2), (1, 2, 5), (1, 5, 4), (0, 1, 4), (0, 4, 3)])
    prism = T(paint(prism, roof), (0, hgt, 0))
    beams = [box((0.3, hgt, 0.3), DKW, (sx * w / 2, hgt / 2, sz * d / 2)) for sx in (-1, 1) for sz in (-1, 1)]
    return T(merge([b, prism] + beams), p, (0, yaw, 0))
def dock(p, yaw, length, width=4.0):
    parts = [box((width, 0.4, length), WOOD, (0, 1.4, length / 2))]
    for k in range(int(length / 4) + 1):
        for sx in (-1, 1): parts.append(cyl(0.25, 5, DKW, (sx * width / 2, -1.2, k * 4)))
    for k in range(0, int(length), 7): parts.append(cyl(0.18, 0.9, IRON, (width / 2 - 0.3, 2.0, k + 1)))
    return T(merge(parts), p, (0, yaw, 0))
def rock(p, r, seed, squash=0.7, col=DST): return ball(r, col, p, 1, (1, squash, 1), 0.25, seed)
def natural_stack(x, z, h, r, seed):
    """Weathered sea stack (Stage 3 fix for the pale cones): stacked, leaning, eroded tiers; dark wet foot with a
    wave-cut notch, darker grey-brown rock with pale strata, lichen/guano on the cap. One merged piece."""
    rr = np.random.default_rng(seed); parts = []; y = -4.0; rad = r * 1.15; lean = rr.uniform(-0.06, 0.06, 2); ox = oz = 0.0
    tiers = rr.integers(3, 6); th = (h + 4) / tiers
    for k in range(tiers):
        m = trimesh.creation.cylinder(1.0, 1.0, sections=12); m = m.subdivide()
        v = m.vertices; v[:, 2] += 0.5   # 0..1 along z
        ang = np.arctan2(v[:, 1], v[:, 0]); t = v[:, 2]
        bump = 1 + 0.22 * np.sin(ang * 3 + seed + k) * np.cos(ang * 5 - k) + rr.uniform(-0.12, 0.12, len(v))
        rk = rad * (1 - 0.18 * t) * (0.78 if (k == 0) else 1.0) ** (1 - t)
        v[:, 0] *= rk * bump; v[:, 1] *= rk * bump * rr.uniform(0.75, 1.0); v[:, 2] *= th * rr.uniform(0.85, 1.1)
        m.apply_transform(trimesh.transformations.rotation_matrix(-math.pi / 2, (1, 0, 0)))
        m.apply_translation((ox, y, oz)); yy = m.vertices[:, 1]
        col = np.tile(C(84, 78, 72), (len(yy), 1))
        col[(np.sin(yy * 1.7 + seed) > 0.75)] = C(118, 110, 98)                     # pale strata lines
        col[yy < 1.6] = C(40, 40, 42); col[(yy > 0.2) & (yy < 1.6) & (np.sin(ang * 7) > 0.3)] = C(46, 64, 50)   # wet foot + weed
        col[(yy < 1.0) & (yy > -0.5)] = C(30, 30, 32)                                 # wave-cut notch shadow
        m.visual = trimesh.visual.ColorVisuals(m, vertex_colors=col); parts.append(m)
        y += th * 0.92; rad *= rr.uniform(0.72, 0.9); ox += lean[0] * th + rr.uniform(-0.6, 0.6); oz += lean[1] * th + rr.uniform(-0.6, 0.6)
    cap = ball(rad * 1.25, C(96, 104, 78), (ox, y - th * 0.15, oz), 1, (1, 0.45, 1), 0.3, seed + 9)   # lichen/grass cap
    cap.visual.vertex_colors[np.random.default_rng(seed).uniform(size=len(cap.vertices)) > 0.6] = C(206, 204, 192)   # guano flecks
    parts.append(cap)
    for k in range(rr.integers(2, 5)): parts.append(rock((rr.uniform(-r, r) * 1.6, rr.uniform(-1.5, 0.2), rr.uniform(-r, r) * 1.6), rr.uniform(1.2, 2.6), seed * 7 + k, 0.6, C(52, 50, 50)))   # fallen blocks
    return T(merge(parts), (x, 0, z), (0, rr.uniform(0, math.tau), 0))
def find_water(x, z, mind, rmax=600):
    for _r in range(0, rmax, 8):
        for _a in np.linspace(0, 2 * math.pi, 36, endpoint=False):
            _x = x + math.cos(_a) * _r; _z = z + math.sin(_a) * _r; _i, _j = px(_x, _z)
            if D['dist_m'][int(_j), int(_i)] > mind: return _x, _z
    return x, z
def open_cam(x, z, dist_, up):  # camera spot over open water looking at (x, z)
    best = None
    for _a in np.linspace(0, 2 * math.pi, 48, endpoint=False):
        _x = x + math.cos(_a) * dist_; _z = z + math.sin(_a) * dist_; _i, _j = px(_x, _z); d_ = D['dist_m'][int(_j), int(_i)]
        if best is None or d_ > best[0]: best = (d_, _x, _z)
    return [best[1], up, best[2]]
def yaw_of(v): return math.atan2(v[0], v[1])
props = {}
# Gullhaven port
gx_, gz_ = nearest_shore(-420, -380); sd = shore_dir(gx_, gz_); gy = yaw_of(sd)
gp = []
gp.append(dock((gx_, 0, gz_), gy, 48, 5)); gp.append(dock((gx_ + sd[1] * 22, 0, gz_ - sd[0] * 22), gy, 30))
for k in range(16):
    back = 10 + (k // 4) * 11; side = (k % 4 - 1.5) * 12 + rng.uniform(-2, 2)
    hx = gx_ - sd[0] * back + sd[1] * side; hz = gz_ - sd[1] * back - sd[0] * side
    gp.append(house((hx, sample(hx, hz) - 0.3, hz), gy + rng.uniform(-.2, .2), rng.uniform(6, 9), rng.uniform(6, 10), rng.uniform(4, 7), ROOF if k % 3 else ROOF2))
crx, crz = gx_ + sd[0] * 40, gz_ + sd[1] * 40
gp += [cyl(0.5, 12, DKW, (crx, 6, crz)), line((crx, 11.5, crz), (crx + sd[0] * 8, 10, crz + sd[1] * 8), 0.3, DKW), line((crx + sd[0] * 8, 10, crz + sd[1] * 8), (crx + sd[0] * 8, 4, crz + sd[1] * 8), 0.05, IRON)]
for k in range(10): gp.append(box((1.4, 1.2, 1.4), WOOD if k % 2 else C(140, 100, 60), (gx_ + sd[0] * (6 + k * 2.5) + sd[1] * 1.5, 2.2, gz_ + sd[1] * (6 + k * 2.5) - sd[0] * 1.5)))
_dm = D['dist_m']; _best = None
for _r in range(50, 200, 10):
    for _a in np.linspace(0, 2 * math.pi, 48, endpoint=False):
        _x = gx_ + math.cos(_a) * _r; _z = gz_ + math.sin(_a) * _r; _i, _j = px(_x, _z)
        if _dm[int(_j), int(_i)] > 35: _best = (_x, _z); break
    if _best: break
props['gullhaven'] = {'pos': [gx_, 0, gz_], 'yaw': gy, 'anchor': [_best[0], 0, _best[1]]}; save('arch_gullhaven_port', merge(gp))
# Lantern Rock lighthouse (on its islet)
lx, lz = find_water(0, -40, 22); ly = 9.0
lp = [T(ball(1.0, STONE, (0, 0, 0), 1, None, 0.25, 3), (lx, (ly - 6) / 2, lz), scale=(17, (ly + 6) / 2, 17)), cyl(3.4, 22, PLAST, (lx, ly + 11, lz), sec=14, r2=2.4), cyl(3.5, 1.2, C(170, 40, 36), (lx, ly + 7, lz), sec=14), cyl(3.2, 1.2, C(170, 40, 36), (lx, ly + 15, lz), sec=14),
      cyl(3.0, 0.6, IRON, (lx, ly + 22.3, lz), sec=14), cyl(2.0, 3.0, C(255, 220, 130), (lx, ly + 24, lz), sec=10), cyl(2.6, 2.2, IRON, (lx, ly + 26.4, lz), sec=10, r2=0), house((lx + 7, ly, lz + 3), 0.4, 6, 5, 3.5, ROOF)]
props['lantern_rock'] = {'pos': [lx, ly, lz], 'light_y': ly + 24, 'cam': open_cam(lx, lz, 75, 20)}; save('arch_lantern_rock', merge(lp))
# Wreck Reef: reef rocks + 3 original broken galleon hulks (ribs, keel, snapped masts), half sunk
def hulk(seed, L=26):
    r = np.random.default_rng(seed); parts = [box((0.8, 0.8, L), DKW, (0, -1.2, 0))]
    for k in range(int(L / 1.6)):
        z = -L / 2 + k * 1.6; w = 3.8 * math.sin(math.pi * (k + 0.5) / (L / 1.6)) + 0.6
        if r.uniform() < 0.25: continue
        for sx in (-1, 1):
            parts.append(line((0, -1.2, z), (sx * w, 0.8, z), 0.22, DKW)); parts.append(line((sx * w, 0.8, z), (sx * w * 0.9, 3.6 + r.uniform(-.5, .5), z), 0.2, DKW))
    for k in range(int(L / 3)):  # some intact planks on one side
        z = -L / 2 + k * 3; w = 3.8 * math.sin(math.pi * (k * 3 + 1.5) / L) + 0.6
        parts.append(box((0.25, 2.4, 3.0), WOOD, (-w * 0.95, 1.2, z + 1.5), (0, 0, 0.15)))
    parts.append(T(cyl(0.45, 14, DKW), (0, 6, -2), (0.9, 0, 0.3))); parts.append(cyl(0.5, 5, DKW, (0, 2.5, 6)))
    parts.append(T(box((9, 0.12, 5), C(200, 190, 160)), (2, 2.5, -6), (0.6, 0.3, 0.9)))  # torn sail
    return merge(parts)
wx, wz = find_water(130, -420, 95); wp_ = []
for k, (ox, oz, yw, roll, sink) in enumerate([(-30, 10, 0.4, 0.5, 2.5), (25, -18, 2.1, -0.35, 1.5), (5, 40, -0.9, 0.9, 3.5)]):
    wp_.append(T(hulk(10 + k), (wx + ox, -sink, wz + oz), (0, yw, roll)))
for k in range(40):
    a = rng.uniform(0, 2 * math.pi); rr = rng.uniform(10, 90); wp_.append(rock((wx + math.cos(a) * rr, rng.uniform(-2.5, -0.5), wz + math.sin(a) * rr), rng.uniform(1.5, 5), 100 + k, 0.5, C(84, 96, 90)))
props['wreck_reef'] = {'pos': [wx, 0, wz], 'cam': open_cam(wx, wz, 110, 22), 'note': 'skiff-only shallows; galleon reef collider ring r=95 m'}; save('arch_wreck_reef', merge(wp_))
# Saltwatch Keep with the dive bell gantry
kx, kz = nearest_shore(-560, 420); ksd = shore_dir(kx, kz); kyaw = yaw_of(ksd); ky = 0
cx_, cz_ = kx - ksd[0] * 14, kz - ksd[1] * 14; base = sample(cx_, cz_)
kp = [cyl(7, 18, STONE, (cx_, base + 8, cz_), sec=12), cyl(7.8, 1.5, DST, (cx_, base + 17.5, cz_), sec=12)]
for k in range(12): a = k * math.tau / 12; kp.append(box((1.6, 1.6, 1.2), DST, (cx_ + math.cos(a) * 7.2, base + 19, cz_ + math.sin(a) * 7.2), (0, -a, 0)))
kp += [cyl(4.5, 7, STONE, (cx_ + 9, base + 3.5, cz_ + 4), sec=10), cyl(5, 4, ROOF2, (cx_ + 9, base + 9, cz_ + 4), sec=10, r2=0), box((16, 7, 9), STONE, (cx_ - 8, base + 3, cz_ - 6), (0, kyaw, 0))]
kp.append(dock((kx, 0, kz), kyaw, 26, 5))
bx, bz = kx + ksd[0] * 24, kz + ksd[1] * 24  # gantry at the pier end
for sx in (-1, 1): kp.append(line((bx + ksd[1] * sx * 3 - ksd[0] * 3, 1.5, bz - ksd[0] * sx * 3 - ksd[1] * 3), (bx, 12, bz), 0.35, DKW))
kp.append(line((bx - ksd[0] * 4, 1.5, bz - ksd[1] * 4), (bx, 12, bz), 0.35, DKW)); kp.append(line((bx, 12, bz), (bx + ksd[0] * 6, 11.5, bz + ksd[1] * 6), 0.3, DKW))
hx_, hz_ = bx + ksd[0] * 6, bz + ksd[1] * 6
kp.append(line((hx_, 11.5, hz_), (hx_, 6.4, hz_), 0.06, IRON))
prof = [(0.0, 0), (1.0, 0.05), (1.45, 0.6), (1.6, 1.0), (1.55, 2.0), (1.25, 2.9), (0.6, 3.3), (0.0, 3.35)]  # dive bell lathe (brass)
bell = trimesh.creation.revolve(np.array(prof), sections=16); bell.apply_transform(trimesh.transformations.rotation_matrix(-math.pi / 2, (1, 0, 0)))
kp.append(T(paint(bell, BRASS), (hx_, 3.0, hz_)))
for a in range(4): kp.append(ball(0.35, C(140, 220, 230), (hx_ + math.cos(a * 1.57) * 1.55, 4.5, hz_ + math.sin(a * 1.57) * 1.55)))
props['saltwatch_keep'] = {'cam': open_cam(hx_, hz_, 40, 12), 'pos': [cx_, base, cz_], 'dive_bell': [hx_, 3.0, hz_], 'dive_buoy': [-1300, 0, 300]}; save('arch_saltwatch_keep', merge(kp))
# rocks / sea stacks scatter around every shore (1 mesh) + buoys
dist = D['dist_m']; cand = np.argwhere((dist[j0:j1, i0:i1] > 4) & (dist[j0:j1, i0:i1] < 30)); rp = []
for k in rng.choice(len(cand), 160, replace=False):
    jj, ii = cand[k]; x = (ii + i0 - S / 2) / pm; z = (jj + j0 - S / 2) / pm
    if rng.uniform() < 0.15: rp.append(natural_stack(x, z, rng.uniform(8, 20), rng.uniform(2.5, 4.5), 4000 + int(k)))
    else: rp.append(rock((x, rng.uniform(-1, 0.3), z), rng.uniform(1.2, 4.5), 300 + int(k), 0.6))
save('arch_shore_rocks', merge(rp))
def buoy(col):
    return merge([cyl(0.9, 1.6, col, (0, 0.3, 0), sec=10), cyl(0.12, 2.4, IRON, (0, 2.0, 0), sec=5), ball(0.35, C(255, 230, 140), (0, 3.3, 0)), cyl(1.0, 0.25, C(240, 240, 240), (0, 0.8, 0), sec=10)])
save('buoy_route', buoy(C(220, 170, 40)), ratio=0.5); save('buoy_skiff', buoy(C(235, 235, 235))); save('buoy_dive', buoy(C(70, 220, 190)))
# storm wall + fog bank ribbons around the region A border (shader does the look; UV.x along, UV.y up)
def ribbon(pts, hgt, segs_per=40):
    vv, uu, ff = [], [], []; L = 0; acc = [0]
    P_ = [np.array(p, float) for p in pts]
    dense = []
    for a_, b_ in zip(P_, P_[1:]):
        for t in np.linspace(0, 1, segs_per, endpoint=False): dense.append(a_ + (b_ - a_) * t)
    dense.append(P_[-1])
    for k in range(1, len(dense)): acc.append(acc[-1] + np.linalg.norm(dense[k] - dense[k - 1]))
    for k, p in enumerate(dense):
        for yy in (0.0, 1.0):
            wob = 18 * math.sin(acc[k] / 70.0) * yy
            vv.append((p[0] + wob, -4 + hgt * yy, p[1] + wob * 0.5)); uu.append((acc[k] / hgt, yy))
    for k in range(len(dense) - 1): i = 2 * k; ff += [(i, i + 1, i + 2), (i + 1, i + 3, i + 2)]
    m = trimesh.Trimesh(vv, ff, process=False); m.visual = trimesh.visual.TextureVisuals(uv=np.array(uu)); return m
inset = 40
border = [(X0 + inset, Z0 + inset), (X1 - inset, Z0 + inset), (X1 - inset, Z1 - inset), (X0 + inset, Z1 - inset), (X0 + inset, Z0 + inset)]
ribbon(border, 140).export(os.path.join(OUT, 'arch_storm_wall.glb')); STATS['arch_storm_wall'] = {'tris': 2 * 40 * 4}
ribbon([(X0 + inset + 60, Z0 + inset + 60), (X1 - inset - 60, Z0 + inset + 60), (X1 - inset - 60, Z1 - inset - 60), (X0 + inset + 60, Z1 - inset - 60), (X0 + inset + 60, Z0 + inset + 60)], 45).export(os.path.join(OUT, 'arch_fog_bank.glb')); STATS['arch_fog_bank'] = {'tris': 320}
# ---------------------------------------------------------------- Brinecrown Coil (original sea serpent) + sea-stack arena
SC = C(36, 92, 98); BELLY = C(196, 186, 140); FIN = C(170, 52, 60); CROWN = C(232, 214, 150); EYE = C(255, 200, 60)
def coil_mesh(path_fn, n=140, ring=14):
    """tube along path_fn(t)->(pos, radius), belly colour on the underside; returns tube, plus spine points"""
    pts = np.array([path_fn(t)[0] for t in np.linspace(0, 1, n)]); rad = np.array([path_fn(t)[1] for t in np.linspace(0, 1, n)])
    tang = np.gradient(pts, axis=0); tang /= np.linalg.norm(tang, axis=1, keepdims=True)
    up = np.array([0, 1.0, 0]); vv, cc, ff = [], [], []
    for k in range(n):
        side = np.cross(tang[k], up); side /= np.linalg.norm(side) + 1e-9; nup = np.cross(side, tang[k])
        for r in range(ring):
            a = r * math.tau / ring; dirv = math.cos(a) * side + math.sin(a) * nup
            ridge = 1 + 0.08 * math.cos(6 * a) * (k % 2)  # scale ridges
            vv.append(pts[k] + dirv * rad[k] * ridge * (0.86 if math.sin(a) < 0 else 1.0)); cc.append(BELLY if math.sin(a) < -0.35 else SC)
    for k in range(n - 1):
        for r in range(ring):
            a_ = k * ring + r; b_ = k * ring + (r + 1) % ring; ff += [(a_, b_, a_ + ring), (b_, b_ + ring, a_ + ring)]
    vv.append(pts[-1] + tang[-1] * rad[-1] * 0.5); cc.append(SC)
    for r in range(ring): ff.append(((n - 1) * ring + r, (n - 1) * ring + (r + 1) % ring, len(vv) - 1))
    m = trimesh.Trimesh(vv, ff, process=False); m.visual = trimesh.visual.ColorVisuals(m, vertex_colors=np.array(cc)); return m, pts, rad, tang
def head(pos, fwd, size):
    fwd = np.array(fwd, float); fwd /= np.linalg.norm(fwd); yaw = math.atan2(fwd[0], fwd[2]); pitch = -math.asin(fwd[1])
    hp = [ball(1.0, SC, (0, 0, 0.4), 2, (1.15, 0.85, 1.6)), ball(1.0, SC, (0, -0.25, 1.7), 1, (0.8, 0.45, 1.1)), ball(1.0, BELLY, (0, -0.75, 1.3), 1, (0.75, 0.3, 1.2)),
          ball(0.22, EYE, (0.75, 0.35, 1.1)), ball(0.22, EYE, (-0.75, 0.35, 1.1))]
    for k in range(7):  # the brine crown: 7 coral-bone horns sweeping back
        a = -0.9 + k * 0.3; base = np.array([math.sin(a) * 0.9, 0.7, -0.1 + abs(a) * 0.2])
        hp.append(line(base, base + np.array([math.sin(a) * 0.8, 1.7 - abs(a) * 0.5, -1.2]), 0.16, CROWN, 5)); hp.append(ball(0.2, CROWN, base + np.array([math.sin(a) * 0.8, 1.7 - abs(a) * 0.5, -1.2])))
    for sx in (-1, 1): hp.append(T(box((0.08, 1.2, 1.6), FIN), (sx * 1.1, 0.1, -0.2), (0, sx * 0.5, sx * 0.3)))  # gill frills
    for k in range(6): hp.append(cyl(0.07, 0.4, C(240, 236, 220), (0.35 - k * 0.14, -0.55, 2.2), sec=4, r2=0))  # teeth
    return T(merge(hp), pos, (pitch, yaw, 0), scale=size)
def fins(pts, rad, tang, every=5):
    out = []
    for k in range(6, len(pts) - 4, every):
        h = rad[k] * 1.1; up = np.array([0, 1.0, 0]); side = np.cross(tang[k], up); side /= np.linalg.norm(side) + 1e-9; nup = np.cross(side, tang[k])
        a = pts[k] + nup * rad[k] * 0.9; b = a + nup * h - tang[k] * h * 0.6; c2 = a - tang[k] * h * 0.9
        m = trimesh.Trimesh([a, b, c2, a + side * 0.05, b + side * 0.05, c2 + side * 0.05], [(0, 1, 2), (3, 5, 4), (0, 3, 4), (0, 4, 1), (1, 4, 5), (1, 5, 2), (2, 5, 3), (2, 3, 0)], process=False)
        out.append(paint(m, FIN))
    return out
# (a) rig-ready REST pose: straight along +Z, 96 m, head at +Z, belly down (Lucian rigs this one)
L = 96.0
def rest(t): return (np.array([0.0, 0.0, (t - 1) * L]), 3.4 * (0.35 + 0.65 * math.sin(math.pi * min(1, 0.15 + t * 0.95)) ** 0.6) if t < 0.97 else 2.4)
tube, sp, sr, st_ = coil_mesh(rest)
rig = merge([tube] + fins(sp, sr, st_) + [head(sp[-1] + st_[-1] * 0.5, st_[-1], 3.2)])
save('brinecrown_coil_rest', rig)
joints = [{'name': f'spine_{k:02d}', 'pos': [0, 0, round(float(z), 2)]} for k, z in enumerate(np.linspace(-L, 0, 25))] + [{'name': 'head', 'pos': [0, 0, 1.6]}, {'name': 'jaw', 'pos': [0, -1.0, 3.5]}, {'name': 'crown', 'pos': [0, 2.4, 1.0]}]
json.dump({'units': 'm', 'forward': '+Z', 'up': '+Y', 'length_m': L, 'joints': joints}, open(os.path.join(OUT, 'brinecrown_coil_joints.json'), 'w'), indent=1, default=float)
# (b) hero pose for renders / concept: arches out of the water in 3 humps, head reared up
def pose(t):
    s = t * 1.0; x = 40 * math.sin(s * 3.2) ; z = -60 + s * 100; y = 7 * math.sin(s * math.tau * 1.5) - 3.0
    if t > 0.8: y += (t - 0.8) / 0.2 * 22; z -= (t - 0.8) / 0.2 * 6
    return np.array([x, y, z]), rest(t)[1]
tube2, sp2, sr2, st2 = coil_mesh(pose)
save('brinecrown_coil_hero', merge([tube2] + fins(sp2, sr2, st2) + [head(sp2[-1] + st2[-1] * 0.5, st2[-1] * np.array([1, 0.3, 1]), 3.2)]), lod=False)
# arena: ring of sea stacks + two arches, centred on the Coil mark
ax_, az_ = -150, 700
_bestc = None
for _r in range(0, 400, 10):
    for _a in np.linspace(0, 2 * math.pi, 36, endpoint=False):
        _x = ax_ + math.cos(_a) * _r; _z = az_ + math.sin(_a) * _r; _i, _j = px(_x, _z)
        if D['dist_m'][int(_j), int(_i)] > 110: _bestc = (_x, _z); break
    if _bestc: break
ax_, az_ = _bestc; ap = []
for k in range(11):
    a = k * math.tau / 11 + rng.uniform(-.1, .1); r = rng.uniform(85, 105); h = rng.uniform(22, 48)
    p = (ax_ + math.cos(a) * r, h / 2 - 4, az_ + math.sin(a) * r)
    st = cyl(rng.uniform(6, 10), h, STONE, p, sec=9, r2=rng.uniform(2.5, 5)); st.vertices += np.random.default_rng(k).uniform(-0.8, 0.8, st.vertices.shape); ap.append(st)
    ap.append(ball(rng.uniform(5, 8), C(80, 110, 70), (p[0], h - 4 + 1, p[2]), 1, (1, 0.35, 1), 0.2, k))  # grassy cap
    ap.append(rock((p[0] + rng.uniform(-8, 8), -1, p[2] + rng.uniform(-8, 8)), rng.uniform(3, 6), 50 + k, 0.5))
for a in (0.6, 3.3):
    c0 = np.array([ax_ + math.cos(a) * 95, 0, az_ + math.sin(a) * 95]); tng = np.array([-math.sin(a), 0, math.cos(a)])
    for k in range(14):
        t = k / 13; p = c0 + tng * (t - 0.5) * 34 + np.array([0, 26 * math.sin(math.pi * t) + 4 * (1 - math.sin(math.pi * t)) - 2, 0])
        ap.append(rock(tuple(p), 6.5 - 2.5 * math.sin(math.pi * t), 200 + k, 0.8, STONE))
props['coil_arena'] = {'pos': [ax_, 0, az_], 'radius': 95, 'cam': open_cam(ax_, az_, 70, 18)}; save('arch_coil_arena', merge(ap))
# ---------------------------------------------------------------- ship upgrade add-ons (never edits the user's glbs)
def ship_info(fn):
    m = trimesh.load(os.path.join(SHIPS, fn), force='mesh'); v = m.vertices; return m, v
def gunwale(v, deck_y, n=24):
    zs = np.linspace(v[:, 2].min() + 0.2, v[:, 2].max() - 0.2, n); out = []
    band = v[(v[:, 1] > deck_y - 0.8) & (v[:, 1] < deck_y + 0.6)]
    for z in zs:
        s = band[np.abs(band[:, 2] - z) < (zs[1] - zs[0])]
        if len(s): out.append((np.abs(s[:, 0]).max(), z, s[:, 1].max()))
    out = np.array(out); k = np.ones(5) / 5
    for c in range(3): out[:, c] = np.convolve(np.pad(out[:, c], 2, mode='edge'), k, 'valid')
    out[:, 2] = np.minimum(out[:, 2], deck_y + 0.4); return out
def masts(v, ymin, thr, nmax=3):
    s = v[(v[:, 1] > ymin) & (np.abs(v[:, 0]) < 0.6)]; hst, edges = np.histogram(s[:, 2], bins=60); out = []
    for k in np.argsort(hst)[::-1]:
        z = (edges[k] + edges[k + 1]) / 2
        if hst[k] < thr or any(abs(z - o[0]) < (np.ptp(v[:, 2]) * 0.12) for o in out): continue
        top = s[np.abs(s[:, 2] - z) < 1.0][:, 1].max(); out.append((z, top))
        if len(out) == nmax: break
    return sorted(out)
def sail(w, h, billow, col, trim=None, stripes=None, n=8):
    vv, cc, ff = [], [], []
    for i in range(n + 1):
        for j in range(n + 1):
            u, t = i / n, j / n; x = (u - 0.5) * w * (1 - 0.12 * t); y = t * h; z = billow * math.sin(math.pi * u) * math.sin(math.pi * (0.15 + 0.85 * t))
            vv.append((x, y, z)); c = col
            if stripes is not None and int(u * 6) % 2 == 0: c = stripes
            if trim is not None and (i in (0, n) or j in (0, n)): c = trim
            cc.append(c)
    for i in range(n):
        for j in range(n):
            a = i * (n + 1) + j; ff += [(a, a + n + 1, a + 1), (a + 1, a + n + 1, a + n + 2), (a, a + 1, a + n + 1), (a + 1, a + n + 2, a + n + 1)]
    m = trimesh.Trimesh(vv, ff, process=False); m.visual = trimesh.visual.ColorVisuals(m, vertex_colors=np.array(cc)); return m
TIERS = [  # name, sail colour, stripe, trim, rope, hull-trim colour, sail scale, extra sails, charm glow
    ('T1 Patched Canvas', C(214, 200, 168), None, C(150, 120, 80), C(150, 120, 80), C(170, 96, 60), 1.05, 0, C(150, 200, 210)),
    ('T2 Gullwing Rig', C(240, 236, 226), C(170, 40, 40), C(170, 40, 40), C(190, 160, 110), C(196, 150, 60), 1.15, 1, C(120, 230, 240)),
    ('T3 Stormsilk', C(40, 70, 120), C(220, 190, 90), C(230, 200, 100), C(220, 200, 150), C(230, 200, 100), 1.25, 2, C(120, 255, 250))]
SPEC = {}
for key, fn, deck, scale in [('galleon', 'ship_tidewrack_sailing_ship.glb', 2.78, 1.0), ('skiff', 'ship_boat_sail.glb', 1.61, 0.24)]:
    m, v = ship_info(fn); g = gunwale(v, deck); ms = masts(v, deck + 2.0, 6 if key == 'galleon' else 2, 3 if key == 'galleon' else 1)
    if key == 'galleon':  # polish: explicit mast stations from a vertex histogram (auto-detect missed the main mast)
        ms = []
        for mz in (-7.0, -0.8, 5.3):
            sel = v[(np.abs(v[:, 2] - mz) < 1.2) & (np.abs(v[:, 0]) < 0.6)]; ms.append((mz, float(sel[:, 1].max())))
    if not ms: ms = [(0.0, v[:, 1].max())]
    bow_z = v[:, 2].max(); stern_z = v[:, 2].min(); SPEC[key] = {'masts': [[round(z, 2), round(t, 2)] for z, t in ms], 'bow_z': round(bow_z, 2), 'deck_y': deck}
    for ti, (tn, sc, sp_, tr, rope, hull, ss, extra, glow) in enumerate(TIERS, 1):
        parts = []
        # sails: one main course + topsail per mast, slightly forward of the original sails so they cover them (add-on, see SHIP_UPGRADES.md)
        for mz, top in ms:
            span = (top - deck - 1.0); w = span * (0.85 if key == 'galleon' else 0.95) * ss
            parts.append(T(sail(w, span * 0.48 * ss, 0.9 * scale * ss + 0.15, sc, tr, sp_), (0, deck + span * 0.22, mz + 0.55 * scale + 0.2)))
            if key == 'galleon' or ti >= 2: parts.append(T(sail(w * 0.75, span * 0.3 * ss, 0.6 * scale * ss + 0.1, sc, tr, sp_), (0, deck + span * 0.74, mz + 0.45 * scale + 0.15)))
            parts.append(box((w * 1.05, 0.18 * scale + 0.06, 0.18 * scale + 0.06), C(90, 64, 40), (0, deck + span * 0.71, mz + 0.4 * scale + 0.1)))
        if extra >= 1:  # jib forward of the fore mast
            fz, ftop = ms[-1]; jb = trimesh.Trimesh([(0, deck + 1.0, bow_z - 0.3), (0, ftop * 0.92, fz + 0.3), (0, deck + 1.2, fz + 0.5)], [(0, 1, 2), (0, 2, 1)], process=False); parts.append(paint(jb, sc))
        if extra >= 2:  # spanker / gaff sail aft + bowsprit extension
            az, atop = ms[0]; sp2_ = trimesh.Trimesh([(0, deck + 1.2, az - 0.4), (0, atop * 0.8, az - 0.4), (0, deck + 1.6, stern_z + 1.0)], [(0, 1, 2), (0, 2, 1)], process=False); parts.append(paint(sp2_, sc))
            parts.append(line((0, deck + 0.8, bow_z - 1.0), (0, deck + 2.2 * scale + 0.4, bow_z + 3.5 * scale), 0.12 * scale + 0.04, C(90, 64, 40)))
        # rigging: stays + shrouds, more per tier
        for mz, top in ms:
            parts.append(line((0, top - 0.3, mz), (0, deck + 0.3, bow_z - 0.5 if mz == ms[-1][0] else mz + 6 * scale), 0.04 * scale + 0.015, rope))
            gi = g[np.argmin(np.abs(g[:, 1] - mz))]
            for k in range(1 + ti):
                for sx in (-1, 1): parts.append(line((0, top * (0.95 - 0.12 * k), mz), (sx * gi[0], gi[2] + 0.1, mz - (k - ti / 2) * 0.9 * scale), 0.03 * scale + 0.012, rope))
        # hull trim: gunwale rail strip both sides (+ waterline band from T2)
        for sx in (-1, 1):
            for a_, b_ in zip(g[:-1], g[1:]):
                parts.append(line((sx * (a_[0] + 0.05), a_[2] + 0.05, a_[1]), (sx * (b_[0] + 0.05), b_[2] + 0.05, b_[1]), 0.09 * scale + 0.03, hull, 6))
                if ti >= 2: parts.append(line((sx * (a_[0] * 0.92 + 0.04), 0.35 * scale + 0.05, a_[1]), (sx * (b_[0] * 0.92 + 0.04), 0.35 * scale + 0.05, b_[1]), 0.07 * scale + 0.03, hull, 6))
        # figurehead at the bow (original designs: T1 carved post, T2 gull, T3 tide-warden with a lantern)
        fh = (0, deck + 0.2 * scale, bow_z + 0.15); fs = 1.0 * scale + 0.25
        if ti == 1: f = merge([cyl(0.32, 1.1, C(150, 108, 64), (0, 0.55, 0.45), (0.35, 0, 0), 8, 0.22), ball(0.34, C(150, 108, 64), (0, 1.25, 0.62), 1, (1, 1.15, 1)), T(box((0.9, 0.1, 0.5), C(196, 150, 60)), (0, 0.75, 0.5), (0.3, 0, 0))])  # carved bust + brass collar
        elif ti == 2: f = merge([ball(0.5, C(240, 240, 235), (0, 0.6, 0.8), 1, (0.7, 0.6, 1.3)), T(box((2.6, 0.08, 0.7), C(240, 240, 235)), (0, 0.9, 0.6), (0.3, 0, 0)), cyl(0.12, 0.5, BRASS, (0, 0.6, 1.5), (1.57, 0, 0), 6, 0)])
        else: f = merge([cyl(0.3, 1.6, C(230, 200, 100), (0, 0.6, 0.6), (0.9, 0, 0), 8, 0.18), ball(0.32, C(230, 200, 100), (0, 1.4, 1.2)), T(box((0.12, 1.4, 1.6), C(40, 70, 120)), (0, 0.6, 0.3), (0.5, 0, 0)), ball(0.25, glow, (0, 1.0, 1.75))])
        parts.append(T(f, fh, scale=fs))
        # wind charm: hanging glass totem at the stern rail; glows brighter per tier (emissive hint via colour; shader uses COLOR alpha=charm)
        cz = stern_z + 0.8 * scale + 0.2; cy = deck + 1.8 * scale + 0.5
        parts += [line((0, cy + 0.9, cz), (0, cy, cz), 0.02, rope), ball(0.18 + 0.05 * ti, glow, (0, cy - 0.15, cz), 1), cyl(0.05, 0.5 + 0.2 * ti, BRASS, (0, cy - 0.7, cz), sec=5)]
        for k in range(ti + 1): parts.append(T(box((0.04, 0.25, 0.12), glow), (0.18 * math.cos(k * 2.1), cy - 0.45, cz + 0.18 * math.sin(k * 2.1))))
        save(f'upg_{key}_t{ti}', merge(parts))
json.dump({'stats': STATS, 'props': props, 'ships': SPEC}, open(os.path.join(OUT, 'stage1_manifest.json'), 'w'), indent=1, default=float)
print('DONE')
