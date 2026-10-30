#!/usr/bin/env python3
"""Beth: Tidewrack Sea STAGE 4 art builder: region C, the Straits.
  C-N Frost Strait (rect x -2400..1500, z -3000..-1500): ice shelf, frozen cliffs, floes, drifting bergs, Frostreach Ice Dock,
      Rimefang Narrows (channel round Frostreach isle), hidden: Rimefang Maw, Frozen Wreck, Aurora Arch.
  C-S Ash Strait (rect x -1800..1500, z 1700..3000): black basalt, steam vents, lava seams, Cinderreach volcano, Vent Harbour,
      Cinder Gate (110 m channel), hidden: Obsidian Arch, Ember Wreck, Hot-spring Grotto.
Same conventions as Stage 1-3: Godot coords (+Y up, metres, map origin), one vertex-colour surface per mesh, _lod1 <= 50 %."""
import os, math, json, sys
S1 = '/workspace/godot-art/ocean_stage1/tools/build_stage1.py'
_src = open(S1).read().split('\n'); _g = {'__file__': S1, '__name__': 'stage1_helpers'}
def _blk(start, stop):
    a_ = next(i for i, l in enumerate(_src) if l.startswith(start)) if start else 0; b_ = next(i for i, l in enumerate(_src) if i > a_ and l.startswith(stop)); return '\n'.join(_src[a_:b_])
exec(_blk(None, 'step = 2'), _g); exec(_blk('WOOD = C(', 'props = {}'), _g); exec(_blk('def hulk', 'wx, wz'), _g)
globals().update({k: v for k, v in _g.items() if not k.startswith('__')})
ROOT4 = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT = os.path.join(ROOT4, 'meshes'); os.makedirs(OUT, exist_ok=True)
_g['OUT'] = OUT; STATS = _g['STATS']; STATS.clear(); save = _g['save']
import numpy as np, trimesh, fast_simplification
from scipy import ndimage
from scipy.spatial import cKDTree
from PIL import Image
from skimage import measure, graph
F = np.load(os.path.join(ROOT4, 'map', 'straits_fields.npz')); ICE = F['ice_f']; ASH = F['ash_f']; SOL = F['solid'] > 0; DM = F['dist_m']; N1 = F['N1']
S = ICE.shape[0]; pm = S / 6000.0
def px(x, z): return S / 2 + x * pm, S / 2 + z * pm
def at(A, x, z):
    i, j = px(x, z); return float(ndimage.map_coordinates(A, [[j], [i]], order=1)[0])
rng = np.random.default_rng(404)
REG = {'frost': (-2400, -3000, 1500, -1500), 'ash': (-1800, 1450, 1500, 3000)}
ICEW = C(236, 242, 248); ICEB = C(150, 192, 218); ICED = C(96, 140, 170); ROCKD = C(70, 76, 86); BAS = C(38, 36, 38); BAS2 = C(26, 25, 28); ASHG = C(62, 60, 62)
SULF = C(176, 150, 64); LAVA = C(255, 110, 30); WARM = C(255, 196, 110); SNOWR = C(228, 234, 240); RUST = C(120, 64, 40)
_sol_edge = SOL & ndimage.binary_dilation(~SOL); _ej, _ei = np.nonzero(_sol_edge); _et = cKDTree(np.stack([_ei, _ej], 1))
def nearest_shore(x, z):
    i, j = px(x, z); _, k = _et.query([i, j]); return float((_ei[k] - S / 2) / pm), float((_ej[k] - S / 2) / pm)
def sea_dir(x, z):   # unit vector land -> sea at a shore point
    i, j = px(x, z); i, j = int(i), int(j); w = DM[j - 8:j + 9, i - 8:i + 9].astype(float); gzz, gxx = np.gradient(ndimage.gaussian_filter(w, 2)); v = np.array([gxx[8, 8], gzz[8, 8]]); return v / (np.linalg.norm(v) + 1e-9)
REG = {'frost': (-2400, -3000, 1500, -1500), 'ash': (-1800, 1450, 1500, 3000)}
def open_cam2(x, z, dist_, up):
    best = None
    for _a in np.linspace(0, 2 * math.pi, 48, endpoint=False):
        _x = x + math.cos(_a) * dist_; _z = z + math.sin(_a) * dist_; d_ = at(DM, _x, _z)
        if not any(r[0] + 180 < _x < r[2] - 180 and r[1] + 180 < _z < r[3] - 180 for r in REG.values()): continue
        if best is None or d_ > best[0]: best = (d_, _x, _z)
    return [best[1], up, best[2]]
# ---------------------------------------------------------------- terrain
SDF = (np.where(SOL, ndimage.distance_transform_edt(SOL), -ndimage.distance_transform_edt(~SOL)) / pm).astype(np.float32)
def _carve_slot(x, z, w, inland=34, out=10):
    sx, sz = nearest_shore(x, z); sd = sea_dir(sx, sz); ax_, az_ = sx + sd[0] * out, sz + sd[1] * out; bx_, bz_ = sx - sd[0] * inland, sz - sd[1] * inland
    i, j = map(int, px(sx, sz)); r = int(60 * pm); sl = (slice(j - r, j + r), slice(i - r, i + r)); yy, xx = np.mgrid[sl]; MX_ = (xx - S / 2) / pm; MZ_ = (yy - S / 2) / pm
    abx, abz = bx_ - ax_, bz_ - az_; t = np.clip(((MX_ - ax_) * abx + (MZ_ - az_) * abz) / (abx * abx + abz * abz), 0, 1); dd = np.hypot(MX_ - (ax_ + abx * t), MZ_ - (az_ + abz * t))
    SDF[sl] = np.minimum(SDF[sl], dd - w / 2 * (1 - 0.45 * t))
_carve_slot(-1100, -2280, 16)
HARB_F = nearest_shore(-900, -1950)
CONES = {'ash': [(300, 2250, 270, 135, 'Cinderreach'), (-600, 2050, 150, 46, 'Vent isle hill'), (1100, 2000, 110, 28, 'Hot-spring isle')]}
def hf(kind, lf, n, X, Z):
    if kind == 'frost':
        shelf = (n < -0.45) | (np.hypot(X - HARB_F[0], Z - HARB_F[1]) < 150)      # low shelf-ice coves (landable, harbour), else frozen cliffs
        rib = np.sin(X * 0.21 + Z * 0.17 + n * 4) * 0.5 + np.sin(X * 0.07 - Z * 0.11) * 0.5             # buttresses / gullies along the cliff
        cliff = np.clip(lf, 0, 5) * (2.5 + 0.8 * n + 0.5 * rib) + np.clip(lf - 5, 0, None) * (0.05 + 0.03 * n) + np.clip(n, 0, None) * 9 + np.clip(lf - 5, 0, 30) * 0.12 * rib
        low = np.clip(lf, 0, None) * 0.14 + np.clip(lf - 30, 0, None) * 0.08
        land = np.minimum(np.where(shelf, low, cliff), 60)
        sea = np.where(shelf, np.maximum(lf * 0.12, -10), np.maximum(lf * 0.4, -18))
        return np.where(lf > 0, land, sea), ~shelf
    land = np.clip(lf, 0, 5) * (2.0 + 0.8 * n) + np.clip(lf - 5, 0, None) * (0.07 + 0.03 * n) + np.clip(n, 0, None) * 5
    for (cx, cz, r, hh, _) in CONES['ash']:
        d = np.hypot(X - cx, Z - cz); ang = np.arctan2(Z - cz, X - cx); cone = hh * np.clip(1 - d / r, 0, 1) ** 1.25 * (1 + 0.07 * np.sin(ang * 11 + n * 3) + 0.04 * np.sin(ang * 23))
        if hh > 100: cone = cone - np.clip(1 - d / 42, 0, 1) * 34     # crater
        land = np.maximum(land, np.where(lf > 0, cone + np.clip(lf, 0, 3), land))
    sea = np.maximum(lf * 0.3, -16)
    return np.where(lf > 0, land, sea), np.ones_like(lf, bool)
def H_at(x, z):
    kind = 'frost' if z < 0 else 'ash'; l_ = at(SDF, x, z); n_ = at(N1, x, z)
    return float(hf(kind, np.array([l_]), np.array([n_]), np.array([x]), np.array([z]))[0][0])
def split_tiles(mesh, name, rect, nx, nz, suf=''):
    X0, Z0, X1, Z1 = rect; cen = mesh.triangles_center; out = []
    for ix in range(nx):
        for iz in range(nz):
            xa = X0 + (X1 - X0) * ix / nx; xb = X0 + (X1 - X0) * (ix + 1) / nx; za = Z0 + (Z1 - Z0) * iz / nz; zb = Z0 + (Z1 - Z0) * (iz + 1) / nz
            sel = (cen[:, 0] >= xa) & (cen[:, 0] < xb + (ix == nx - 1)) & (cen[:, 2] >= za) & (cen[:, 2] < zb + (iz == nz - 1))
            if sel.sum() == 0: continue
            sub = mesh.submesh([np.nonzero(sel)[0]], append=True); sub.export(os.path.join(OUT, f'{name}_x{ix}z{iz}{suf}.glb')); out.append((f'{name}_x{ix}z{iz}{suf}', int(sel.sum())))
    return out
TILES = {}
def terrain(kind, rect, budget=170000):
    X0, Z0, X1, Z1 = rect; step = 2
    i0, j0 = map(int, px(X0, Z0)); i1, j1 = map(int, px(X1, Z1))
    lf = SDF[j0:j1:step, i0:i1:step]; n = N1[j0:j1:step, i0:i1:step]
    gz, gx = np.mgrid[j0:j1:step, i0:i1:step]; X = (gx - S / 2) / pm; Z = (gz - S / 2) / pm
    H, CL = hf(kind, lf, n, X, Z); keep = lf > -60
    idx = -np.ones(lf.shape, int); idx[keep] = np.arange(keep.sum()); V = np.stack([X[keep], H[keep], Z[keep]], 1)
    q = keep[:-1, :-1] & keep[1:, :-1] & keep[:-1, 1:] & keep[1:, 1:]
    a = idx[:-1, :-1][q]; b = idx[:-1, 1:][q]; c_ = idx[1:, :-1][q]; d = idx[1:, 1:][q]
    m = trimesh.Trimesh(V, np.concatenate([np.stack([a, c_, b], 1), np.stack([b, c_, d], 1)]), process=False)
    nrm = m.vertex_normals; slope = 1 - np.abs(nrm[:, 1]); h = V[:, 1]; nn = n[keep]; ll = lf[keep]
    if kind == 'frost':
        col = np.tile(ICEW, (len(V), 1)); col[nn > 0.6] = SNOWR
        strx = np.sin(V[:, 0] * 0.9 + V[:, 2] * 0.7 + nn * 5)
        col[(slope > 0.35) & (h > 0.5)] = ICEB; col[(slope > 0.55) & (h > 0.5)] = ICED; col[(slope > 0.5) & (h > 0.5) & (strx > 0.55)] = C(196, 222, 236)
        col[(slope > 0.5) & (h > 0.5) & (strx < -0.7)] = C(70, 110, 140)                 # crevasse shadows
        col[(slope > 0.5) & (h > 3) & (np.sin(h * 0.9 + nn * 3) > 0.72)] = ROCKD        # dark rock strata in the ice cliffs
        col[(h < 1.4) & (h > -1.5)] = C(120, 172, 204)                                  # blue waterline ice
        col[h < -1.5] = C(70, 102, 118); col[h < -8] = C(46, 70, 86)
    else:
        col = np.tile(BAS, (len(V), 1)); col[(slope < 0.25) & (h > 4)] = C(34, 32, 34); col[(slope < 0.25) & (h > 4) & (nn > 1.0)] = C(48, 46, 48)
        col[(h > 40) & (np.sin(np.arctan2(V[:, 2] - 2250, V[:, 0] - 300) * 17) > 0.6)] = C(58, 50, 48)   # ash streaks down the cone; col[(slope > 0.45)] = BAS2
        col[(h > 4) & (nn > 1.9)] = C(150, 128, 70)                                     # sulphur crust patches
        col[(slope > 0.4) & (np.sin(h * 1.1 + nn * 2) > 0.8)] = C(58, 48, 46)             # reddish basalt bands
        col[(h < 1.2) & (h > -1.5)] = C(22, 22, 25)                                     # black sand / wet rock
        col[h < -1.5] = C(40, 46, 50); col[h < -8] = C(28, 34, 40)
    m.visual = trimesh.visual.ColorVisuals(m, vertex_colors=col)
    v2, f2 = fast_simplification.simplify(m.vertices.astype(np.float32), m.faces.astype(np.int64), target_reduction=max(0, 1 - budget / len(m.faces)))
    c2 = trimesh.Trimesh(v2, f2, process=False); c2.visual = trimesh.visual.ColorVisuals(c2, vertex_colors=col[cKDTree(V).query(v2)[1]])
    name = f'{kind}_terrain'; save(name, c2)
    hi = trimesh.load(os.path.join(OUT, name + '.glb'), force='mesh'); lo = trimesh.load(os.path.join(OUT, name + '_lod1.glb'), force='mesh')
    nx, nz = (4, 2) if kind == 'frost' else (3, 2)
    TILES[kind] = {'high': split_tiles(hi, f'{kind}_tile', rect, nx, nz), 'lod1': split_tiles(lo, f'{kind}_tile', rect, nx, nz, '_lod1')}
    for f_ in (name + '.glb', name + '_lod1.glb'): os.remove(os.path.join(OUT, f_))
    v3, f3 = fast_simplification.simplify(v2, f2, target_reduction=0.93); trimesh.Trimesh(v3, f3).export(os.path.join(OUT, f'{kind}_terrain_col.glb'))
    land = np.repeat(np.repeat(H > 0.2, step, 0), step, 1)[:j1 - j0, :i1 - i0]   # shore distance from the real terrain (the SOL mask had submerged land -> white foam fields)
    dm = np.clip(ndimage.distance_transform_edt(~land) / pm, 0, 255).astype(np.uint8); Image.fromarray(dm).save(os.path.join(ROOT4, 'shaders', f'{kind}_shore_dist.png'))
    STATS[f'{kind}_tiles'] = {'count': len(TILES[kind]['high']), 'tris': int(len(f2)), 'lod1_tris': int(sum(t[1] for t in TILES[kind]['lod1']))}
    return CL
for k_, r_ in REG.items(): terrain(k_, r_)
# ---------------------------------------------------------------- the two narrow sailing channels (max-clearance route through the water)
def channel(pts):
    cost = 1.0 / (np.clip(DM, 0, None) + 0.5) ** 2 + np.where(DM <= 2, 1e3, 0); path = []
    for a_, b_ in zip(pts, pts[1:]):
        ia, ja = px(*a_); ib, jb = px(*b_); p, _ = graph.route_through_array(cost, (int(ja), int(ia)), (int(jb), int(ib)), fully_connected=True, geometric=True); path += p
    P = np.array([((i - S / 2) / pm, (j - S / 2) / pm) for j, i in path])[::6]
    w = [2 * at(DM, x, z) for x, z in P]; return P, w
CHAN = {}
for name_, pts_ in {'rimefang_narrows': [(-560, -1560), (-605, -2050), (-410, -2250), (-300, -2420), (200, -2400), (520, -2280), (300, -2110), (262, -1990), (330, -1560)],
                    'cinder_gate': [(-160, 1760), (-165, 2070), (-60, 2420)]}.items():
    P_, w_ = channel(pts_); CHAN[name_] = {'path': P_.round(1).tolist(), 'min_width_m': round(float(min(w_)), 1), 'mean_width_m': round(float(np.mean(w_)), 1)}
    print(name_, CHAN[name_]['min_width_m'], CHAN[name_]['mean_width_m'], len(P_))
def far_from_chan(x, z, d=40):
    return all(np.min(np.hypot(np.array(c['path'])[:, 0] - x, np.array(c['path'])[:, 1] - z)) > d for c in CHAN.values())
props = {}
def cands(rect, dmin, dmax, kind_land=None, lmin=None, lmax=None):
    X0, Z0, X1, Z1 = rect; i0, j0 = map(int, px(X0, Z0)); i1, j1 = map(int, px(X1, Z1)); sl = (slice(j0, j1), slice(i0, i1))
    m = (DM[sl] > dmin) & (DM[sl] < dmax) if lmin is None else (SDF[sl] > lmin) & (SDF[sl] < lmax)
    jj, ii = np.nonzero(m); return np.stack([(ii + i0 - S / 2) / pm, (jj + j0 - S / 2) / pm], 1)
# ================================================================ FROST props
FR = REG['frost']
def floe(r, seed, thick=0.9):
    rr = np.random.default_rng(seed); n = rr.integers(6, 10); a = np.sort(rr.uniform(0, math.tau, n)); rad = r * rr.uniform(0.6, 1.0, n)
    top = np.stack([np.cos(a) * rad, np.full(n, 0.35), np.sin(a) * rad], 1); bot = top * (0.92, 1, 0.92); bot[:, 1] = 0.35 - thick
    V = np.concatenate([top, bot, [(0, 0.35, 0), (0, 0.35 - thick, 0)]]); Fs = []
    for i in range(n):
        j = (i + 1) % n; Fs += [(2 * n, j, i), (2 * n + 1, n + i, n + j), (i, j, n + j), (i, n + j, n + i)]
    m = trimesh.Trimesh(V, Fs, process=False)
    col = np.tile(ICEW, (len(m.vertices), 1)); col[m.vertices[:, 1] < 0.2] = C(140, 196, 224); m.visual = trimesh.visual.ColorVisuals(m, vertex_colors=col); return m
def berg(r, h, seed):
    rr = np.random.default_rng(seed); m = trimesh.creation.icosphere(2, 1.0)
    v = m.vertices; v *= (1 + rr.uniform(-0.28, 0.28, (len(v), 1))); v[:, 1] = np.where(v[:, 1] > 0, v[:, 1] * h, v[:, 1] * h * 0.6)
    v[:, 0] *= r; v[:, 2] *= r * rr.uniform(0.7, 1.1); v[:, 1] += rr.uniform(-0.1, 0.1, len(v)) * h
    top = v[:, 1] > h * 0.55; v[top, 1] = np.minimum(v[top, 1], h * (0.7 + 0.3 * np.sin(v[top, 0] * 0.3 + seed)))   # tabular / broken tops
    m = trimesh.Trimesh(v, m.faces, process=False); fn = m.face_normals; m = m.subdivide() if False else m
    m = trimesh.Trimesh(m.vertices[m.faces].reshape(-1, 3), np.arange(len(m.faces) * 3).reshape(-1, 3), process=False)   # flat faceted
    y = m.vertices[:, 1]; fny = np.repeat(fn[:, 1], 3)
    col = np.tile(ICEW, (len(y), 1)); col[fny < 0.3] = C(176, 214, 236); col[fny < -0.2] = C(120, 176, 210)
    col[np.repeat(rr.uniform(size=len(fn)) > 0.82, 3)] = C(150, 204, 232); col[y < 0.6] = C(96, 168, 196); col[y < -1.0] = C(60, 130, 160)
    m.visual = trimesh.visual.ColorVisuals(m, vertex_colors=col); return m
# floes: thick near the ice coast, thin out to sea; the channel centre-lines are kept clear for the galleon
cf = cands(FR, 4, 260); fl = []
for k in rng.choice(len(cf), 2600, replace=False):
    x, z = cf[k]; d = at(DM, x, z)
    if rng.uniform() > math.exp(-d / 70) or not far_from_chan(x, z, 22): continue
    fl.append(T(floe(rng.uniform(2.5, 11) * (1.4 if d < 25 else 1), 700 + int(k)), (x, 0, z), (0, rng.uniform(0, 3), 0)))
    if len(fl) >= 520: break
save('frost_ice_floes', merge(fl)); print('floes', len(fl))
BERGS = []
for v_, (r_, h_) in enumerate([(22, 26), (15, 34), (30, 18)]): save(f'frost_iceberg_{"abc"[v_]}', berg(r_, h_, 31 + v_))
cb = cands(FR, 110, 1e9)
for k in rng.permutation(len(cb)):
    x, z = cb[k]
    if not far_from_chan(x, z, 120) or any(math.hypot(x - b['pos'][0], z - b['pos'][2]) < 260 for b in BERGS): continue
    a = rng.uniform(0, math.tau); BERGS.append({'mesh': f'frost_iceberg_{"abc"[len(BERGS) % 3]}', 'pos': [float(x), 0.0, float(z)], 'yaw': float(rng.uniform(0, math.tau)),
                  'scale': float(rng.uniform(0.7, 1.3)), 'drift_dir': [math.cos(a), 0, math.sin(a)], 'drift_mps': float(rng.uniform(0.15, 0.4)), 'spin_rad_s': float(rng.uniform(-0.004, 0.004)), 'col_radius_m': 0})
    BERGS[-1]['col_radius_m'] = [22, 15, 30]["abc".index(BERGS[-1]['mesh'][-1])] * BERGS[-1]['scale']
    if len(BERGS) >= 12: break
print('bergs', len(BERGS))
# frozen cliffs: icicle fringes on cliff lips + frozen waterfalls
ci = cands(FR, 0, 0, lmin=2, lmax=9); ic = []; falls = []
for k in rng.choice(len(ci), 4000, replace=False):
    x, z = ci[k]; hh = H_at(x, z)
    if hh < 12: continue
    sd = sea_dir(x, z); n_ = rng.integers(3, 7)
    for j in range(n_):
        o = rng.uniform(-3, 3); px_, pz_ = x + sd[1] * o + sd[0] * 1.2, z - sd[0] * o + sd[1] * 1.2; L = rng.uniform(1.2, 5.5)
        ic.append(cyl(rng.uniform(0.18, 0.45), L, ICEB if j % 2 else C(200, 228, 244), (px_, hh - 0.6, pz_), (math.pi, 0, 0), 5, 0))
    if len(falls) < 9 and hh > 22 and rng.uniform() < 0.05:
        falls.append((x, z, hh, sd))
    if len(ic) > 2600: break
for (x, z, hh, sd) in falls:   # frozen waterfall: stacked tapering lumpy columns from lip to sea
    for j in range(7):
        t = j / 6; ic.append(T(ball(4.5 - 2.2 * t, C(180, 222, 242) if j % 2 else C(206, 236, 250), (0, 0, 0), 1, (1, hh / 6.5 / (4.5 - 2.2 * t) * 0.6, 0.7), 0.3, j),
                              (x + sd[0] * (1.5 + t * 2), hh * (1 - t) - 1, z + sd[1] * (1.5 + t * 2))))
save('frost_icicles', merge(ic)); print('icicles', len(ic), 'falls', len(falls))
GL = {'frost': [], 'ash': []}    # glow pieces (lanterns, runes, embers) -> <region>_glow.glb with glow_vc
def frame(x, z):   # shore point, sea dir, yaw, side vector
    sx, sz = nearest_shore(x, z); sd = sea_dir(sx, sz); return sx, sz, sd, math.atan2(sd[0], sd[1]), np.array([sd[1], -sd[0]])
def lantern(p, glow, region, post=True):
    out = [cyl(0.12, 3.2, DKW, (p[0], p[1] + 1.6, p[2]), sec=6)] if post else []
    out += [box((0.7, 0.9, 0.7), IRON, (p[0], p[1] + 3.5, p[2]))]; GL[region].append(ball(0.32, glow, (p[0], p[1] + 3.5, p[2]), 1)); return out
# ---------------------------------------------------------------- Frostreach Ice Dock (frost harbour): timber piers on the ice, snow-roofed huts, ice breakwater, beacon
hx, hz, sd, yw, side = frame(-900, -1950); P_ = []
P_ += [dock((hx, 0, hz), yw, 44, 6), dock((hx + side[0] * 24, 0, hz + side[1] * 24), yw, 30, 4), dock((hx - side[0] * 22, 0, hz - side[1] * 22), yw, 24, 4)]
for k in range(22):   # ice-block breakwater arcing round the piers
    t = k / 21; a = (t - 0.5) * 2.2; r_ = 70; bx_ = hx + sd[0] * (math.cos(a) * r_ * 0.75 + 8) + side[0] * math.sin(a) * r_; bz_ = hz + sd[1] * (math.cos(a) * r_ * 0.75 + 8) + side[1] * math.sin(a) * r_
    if abs(a) < 0.28: continue   # harbour mouth
    P_.append(T(box((7, 4 + rng.uniform(0, 2), 5), C(190, 226, 244) if k % 2 else ICEW, (0, 0.8, 0)), (bx_, 0, bz_), (rng.uniform(-.1, .1), yw + a + rng.uniform(-.2, .2), rng.uniform(-.1, .1))))
SNOWROOF = C(232, 238, 244)
for k in range(11):
    back = 14 + (k // 4) * 12 + rng.uniform(-2, 2); sv = (k % 4 - 1.5) * 13 + rng.uniform(-2, 2); x_ = hx - sd[0] * back + side[0] * sv; z_ = hz - sd[1] * back + side[1] * sv
    hh_ = H_at(x_, z_); P_.append(house((x_, hh_ - 0.3, z_), yw + rng.uniform(-.2, .2), rng.uniform(6, 9), rng.uniform(6, 9), rng.uniform(3.5, 5.5), SNOWROOF))
    P_.append(cyl(0.4, 2.5, STONE, (x_ + 1.5, hh_ + 6.5, z_), sec=6))
    if k % 3 == 0: P_ += lantern((x_ + side[0] * 5, hh_, z_ + side[1] * 5), WARM, 'frost')
for k in range(0, 44, 11): P_ += lantern((hx + sd[0] * k + side[0] * 2.6, 1.6, hz + sd[1] * k + side[1] * 2.6), WARM, 'frost')
bk = np.array([hx, 0, hz]) + np.array([sd[0], 0, sd[1]]) * 47
P_ += [cyl(1.4, 10, STONE, (bk[0], 6, bk[2]), sec=8), cyl(1.6, 1.4, IRON, (bk[0], 12.6, bk[2]), sec=8, r2=0)]; GL['frost'].append(cyl(1.0, 1.6, C(180, 230, 255), (bk[0], 11.6, bk[2]), sec=8))
for k in range(10): P_.append(box((1.2, 1.2, 1.2), WOOD, (hx + sd[0] * rng.uniform(4, 30) + side[0] * rng.uniform(-2, 2), 2.2, hz + sd[1] * rng.uniform(4, 30) + side[1] * rng.uniform(-2, 2)), (0, rng.uniform(0, 1), 0)))
P_.append(hulk(91, 14).apply_translation((0, 0, 0)) if False else T(hulk(91, 12), (hx + side[0] * 12 + sd[0] * 18, 0.6, hz + side[1] * 12 + sd[1] * 18), (0, yw, 0)))   # moored fishing boat (frozen in)
props['frostreach_ice_dock'] = {'pos': [hx, 0, hz], 'yaw': yw, 'anchor': list(map(float, bk + np.array([sd[0], 0, sd[1]]) * 50)), 'cam': open_cam2(hx, hz, 150, 34), 'kind': 'harbour'}
save('frost_harbour', merge(P_))
# ---------------------------------------------------------------- hidden spots (frost)
H_ = []
mx, mz, sd, yw, side = frame(-1100, -2280); w_, h_ = 16, 13; mp = []   # Rimefang Maw: fanged ice-cave mouth (skiff only)
for k in range(22):
    a = math.pi * k / 21; mp.append(rock((math.cos(a) * (w_ / 2 + 2.5), math.sin(a) * h_, rng.uniform(-1, 1)), rng.uniform(3, 5), 300 + k, 0.8, ICED if k % 2 else C(120, 170, 200)))
for k in range(13):
    a = math.pi * (0.1 + 0.8 * k / 12); mp.append(cyl(0.7, rng.uniform(2.5, 5.5), C(214, 238, 250), (math.cos(a) * w_ / 2 * 0.9, math.sin(a) * h_ * 0.95, 1.0), (math.pi, 0, 0), 5, 0))   # fangs
for k in range(6): mp.append(cyl(0.6, rng.uniform(1.5, 3.0), C(214, 238, 250), (-w_ / 2 + 1 + k * (w_ - 2) / 5, -0.2, 1.2), (0, 0, 0), 5, 0))       # lower fangs
_hv = [(0, -1.5, -0.6)] + [(math.cos(math.pi * t) * (w_ / 2 + 0.3), max(-1.5, math.sin(math.pi * t) * (h_ + 0.3)), 0.2) for t in np.linspace(0, 1, 17)]
mp.append(paint(trimesh.Trimesh(_hv, [(0, k + 1, k + 2) for k in range(16)] + [(0, k + 2, k + 1) for k in range(16)], process=False), C(6, 10, 16)))
for k in range(3): mp.append(box((w_ * (1 - 0.18 * k), h_ * (1 - 0.15 * k), 0.4), C(6, 10, 16), (0, h_ * 0.45 - 1, -3 - k * 4)))
GL['frost'].append(T(merge([ball(0.25, C(140, 220, 255), (rng.uniform(-4, 4), rng.uniform(1, 8), -2 - k), 0) for k in range(9)]), (mx, 0, mz), (0, yw, 0)))   # faint glints inside
H_.append(T(merge(mp), (mx, 0, mz), (0, yw, 0))); props['rimefang_maw'] = {'pos': [mx, 0, mz], 'yaw': yw, 'skiff_only': True, 'hidden': True, 'cam': open_cam2(mx, mz, 55, 12), 'note': 'frost cave mouth; interior cell later'}
wx_, wz_ = nearest_shore(-250, -2560); sdw = sea_dir(wx_, wz_)   # Frozen Wreck: an old warship locked in the bay ice, listing, rigging iced
fw = [T(hulk(57, 30), (0, 0.4, 0), (0.0, 0, 0.32)), cyl(0.5, 18, DKW, (0, 9, 2), (0.3, 0, 0.32), sec=6), cyl(0.4, 12, DKW, (0, 6, -8), (0.25, 0, 0.32), sec=6)]
for k in range(30): fw.append(T(floe(rng.uniform(4, 9), 900 + k, 1.2), (rng.uniform(-22, 22), 0.1, rng.uniform(-30, 30))))
for k in range(40): fw.append(cyl(0.12, rng.uniform(0.6, 1.8), C(210, 236, 250), (rng.uniform(-3, 3), rng.uniform(2, 14), rng.uniform(-12, 12)), (math.pi, 0, 0), 4, 0))
fpos = (wx_ + sdw[0] * 34, 0, wz_ + sdw[1] * 34); GL['frost'].append(ball(0.5, C(255, 210, 120), (fpos[0], 2.4, fpos[2]), 1))   # captain's lamp still lit (loot)
H_.append(T(merge(fw), fpos, (0, math.atan2(sdw[1], -sdw[0]), 0))); props['frozen_wreck'] = {'pos': list(map(float, fpos)), 'hidden': True, 'cam': open_cam2(fpos[0], fpos[2], 70, 18), 'note': 'loot: captain chest (glow)'}
ax_, az_ = 60, -2395; ap = []    # Aurora Arch: natural ice bridge over the Rimefang gorge, rune stone + chest on a ledge
for k in range(26):
    t = k / 25; a = math.pi * t; ap.append(rock((math.cos(a) * 56, 8 + math.sin(a) * 24, rng.uniform(-4, 4)), rng.uniform(5, 8), 400 + k, 0.7, C(186, 222, 242) if k % 3 else ICEW))
for k in range(16): ap.append(cyl(0.35, rng.uniform(2, 5), C(214, 238, 250), (rng.uniform(-30, 30), 8 + 24 * 0.85, rng.uniform(-4, 4)), (math.pi, 0, 0), 5, 0))
lx_ = 50; ly_ = max(H_at(ax_ + math.sin(0.15) * 0, az_ - lx_), 3.0)
ap += [box((2.2, 3.6, 1.0), C(90, 96, 110), (lx_, ly_ + 1.8, 6)), box((1.6, 1.0, 1.0), WOOD, (lx_ + 2.5, ly_ + 0.5, 6))]
GL['frost'].append(T(merge([box((1.8, 0.2, 0.3), C(120, 255, 210), (lx_, ly_ + 2.4 + k * 0.6, 6.55)) for k in range(3)] + [box((1.4, 0.15, 0.9), C(255, 220, 120), (lx_ + 2.5, ly_ + 1.05, 6))]), (ax_, 0, az_), (0, 0.15 + math.pi / 2, 0)))
H_.append(T(merge(ap), (ax_, 0, az_), (0, 0.15 + math.pi / 2, 0))); props['aurora_arch'] = {'pos': [ax_, 0, az_], 'hidden': True, 'cam': [ax_ - 160, 22, az_ + 20], 'note': 'ice bridge over the narrows; rune stone + chest on the east ledge'}
save('frost_hidden_spots', merge(H_)); save('frost_glow', merge(GL['frost']))
# ================================================================ ASH props
AR = REG['ash']
def darken(m, f=0.42, tint=(1.0, 0.95, 0.95)):
    c = np.array(m.visual.vertex_colors).astype(float); c[:, :3] = c[:, :3] * f * np.array(tint); m.visual = trimesh.visual.ColorVisuals(m, vertex_colors=c.clip(0, 255).astype(np.uint8)); return m
cs = cands(AR, 6, 90); st = []
for k in rng.choice(len(cs), 900, replace=False):   # basalt stacks + boulders off the black shore
    x, z = cs[k]
    if not far_from_chan(x, z, 30): continue
    if rng.uniform() < 0.12: st.append(darken(natural_stack(x, z, rng.uniform(10, 26), rng.uniform(3, 6), 7000 + int(k))))
    else: st.append(rock((x, rng.uniform(-1.0, 0.4), z), rng.uniform(1.2, 4.5), 1900 + int(k), 0.6, BAS2 if k % 2 else C(44, 40, 40)))
    if len(st) > 260: break
save('ash_offshore_rocks', merge(st))
def ribbon_on(pts, w, inten, lift=0.12):   # ground-hugging strip, COLOR.r = glow intensity (lava_seam shader)
    P = np.array(pts); n = len(P); vv, cc, ff = [], [], []
    for i in range(n):
        d = P[min(i + 1, n - 1)] - P[max(i - 1, 0)]; d = d / (np.linalg.norm(d) + 1e-9); nrm = np.array([-d[1], d[0]]); ww = w * (0.4 + 0.6 * math.sin(math.pi * i / max(1, n - 1)))
        for s_ in (-1, 1):
            q = P[i] + nrm * ww * s_ * 0.5; vv.append((q[0], H_at(q[0], q[1]) + lift, q[1])); cc.append((int(255 * inten), int(rng.uniform(0, 255)), 0, 255))
    for i in range(n - 1): a = 2 * i; ff += [(a, a + 2, a + 1), (a + 1, a + 2, a + 3)]
    m = trimesh.Trimesh(vv, ff, process=False); m.visual = trimesh.visual.ColorVisuals(m, vertex_colors=np.array(cc, np.uint8)); return m
X0a, Z0a, X1a, Z1a = AR; i0, j0 = map(int, px(X0a, Z0a)); i1, j1 = map(int, px(X1a, Z1a)); sub = SDF[j0:j1, i0:i1]; lv = []
for lev in (1.2, 3.5, 8.0):
    for cnt in measure.find_contours(sub, lev):
        P = np.stack([(cnt[:, 1] + i0 - S / 2) / pm, (cnt[:, 0] + j0 - S / 2) / pm], 1)
        if len(P) < 12: continue
        on = np.sin(np.cumsum(np.r_[0, np.hypot(*np.diff(P, axis=0).T)]) / 37.0 + lev) > 0.35    # broken seams, not a continuous line
        run = []
        for p_, o_ in zip(P, on):
            if o_: run.append(p_ + rng.normal(0, 0.6, 2))
            elif len(run) > 6: lv.append(ribbon_on(run[::2], rng.uniform(2.0, 4.5), rng.uniform(0.6, 1.0), 0.45)); run = []
            else: run = []
for k in range(9):   # lava rivulets down the Cinderreach flanks
    a = k * math.tau / 9 + rng.uniform(-.2, .2); pts = []; x, z = 300 + math.cos(a) * 44, 2250 + math.sin(a) * 44
    for j in range(40): pts.append((x, z)); a += rng.normal(0, 0.08); x += math.cos(a) * 5; z += math.sin(a) * 5
    lv.append(ribbon_on(pts, 5.0, 1.0, 1.6))
cr = trimesh.creation.cylinder(30, 0.5, sections=24); cr.apply_transform(trimesh.transformations.rotation_matrix(-math.pi / 2, (1, 0, 0))); cr.apply_translation((300, H_at(300, 2250) + 4, 2250))
cr.visual = trimesh.visual.ColorVisuals(cr, vertex_colors=np.tile((255, 120, 0, 255), (len(cr.vertices), 1)).astype(np.uint8)); lv.append(cr)   # crater lava lake
save('ash_lava_seams', merge(lv)); print('lava pieces', len(lv))
def plume(x, y, z, hgt, w, seed):   # 3 crossed soft cards; COLOR.r = height fraction, COLOR.g = phase, COLOR.b = width scale
    rr = np.random.default_rng(seed); vv, cc, ff = [], [], []; ph = int(rr.uniform(0, 255))
    for c_ in range(3):
        a = c_ * math.pi / 3 + rr.uniform(0, 0.4); ca, sa = math.cos(a), math.sin(a); base = len(vv)
        for r_ in range(6):
            t = r_ / 5; ww = w * (0.35 + 1.4 * t); yy = y + hgt * t
            for s_ in (-1, 1): vv.append((x + ca * ww * s_, yy, z + sa * ww * s_)); cc.append((int(255 * t), ph, int(255 * (0.5 + 0.5 * s_)), 255))
        for r_ in range(5): i = base + r_ * 2; ff += [(i, i + 1, i + 2), (i + 1, i + 3, i + 2)]
    m = trimesh.Trimesh(vv, ff, process=False); m.visual = trimesh.visual.ColorVisuals(m, vertex_colors=np.array(cc, np.uint8)); return m
cv = cands(AR, 0, 0, lmin=3, lmax=60); vents, steam = [], []; VENTS = []
for k in rng.permutation(len(cv)):
    x, z = cv[k]
    if any(math.hypot(x - v[0], z - v[2]) < 70 for v in VENTS): continue
    y = H_at(x, z); VENTS.append([float(x), float(y), float(z)])
    for j in range(7): a = j * math.tau / 7; vents.append(rock((x + math.cos(a) * 2.4, y + 0.3, z + math.sin(a) * 2.4), rng.uniform(0.8, 1.4), 3000 + j + len(VENTS) * 9, 0.6, C(150, 130, 70) if j % 2 else C(90, 80, 52)))
    GL['ash'].append(ball(1.0, C(255, 140, 40), (x, y - 0.3, z), 1, (1, 0.3, 1))); steam.append(plume(x, y, z, rng.uniform(22, 40), rng.uniform(5, 8), len(VENTS)))
    if len(VENTS) >= 34: break
steam.append(plume(300, H_at(300, 2250) + 4, 2250, 140, 30, 99))   # Cinderreach crater column
save('ash_vents', merge(vents)); save('ash_steam', merge(steam), lod=False); print('vents', len(VENTS))
# ---------------------------------------------------------------- Vent Harbour (ash harbour): basalt quay, smithies with steam chimneys, ember lanterns, crane
hx, hz, sd, yw, side = frame(-500, 1900); P_ = []; BLK = C(52, 48, 48)
for k in range(9): P_.append(T(box((6.5, 3.2, 6), BLK if k % 2 else C(62, 56, 54), (0, 0.4, 0)), (hx + side[0] * (k - 4) * 6.4 + sd[0] * 2, 0, hz + side[1] * (k - 4) * 6.4 + sd[1] * 2), (0, yw, 0)))   # quay
P_ += [dock((hx + side[0] * 14, 0, hz + side[1] * 14), yw, 36, 5), dock((hx - side[0] * 16, 0, hz - side[1] * 16), yw, 26, 4)]
for k in range(16):   # basalt-boulder breakwater
    t = k / 15; a = (t - 0.5) * 2.0; bx_ = hx + sd[0] * (math.cos(a) * 52 + 6) + side[0] * math.sin(a) * 64; bz_ = hz + sd[1] * (math.cos(a) * 52 + 6) + side[1] * math.sin(a) * 64
    if abs(a) < 0.3: continue
    P_.append(rock((bx_, 0.2, bz_), rng.uniform(3, 5), 5000 + k, 0.7, BAS2))
for k in range(9):
    back = 12 + (k // 3) * 12 + rng.uniform(-2, 2); sv = (k % 3 - 1) * 15 + rng.uniform(-2, 2); x_ = hx - sd[0] * back + side[0] * sv; z_ = hz - sd[1] * back + side[1] * sv; hh_ = H_at(x_, z_)
    hs = house((x_, hh_ - 0.3, z_), yw + rng.uniform(-.2, .2), rng.uniform(6, 9), rng.uniform(6, 9), rng.uniform(3.5, 6), RUST); P_.append(darken(hs, 0.5, (1.0, 0.92, 0.88)))
    P_.append(cyl(0.7, 6, C(58, 52, 50), (x_ + 2, hh_ + 7, z_), sec=8)); steam.append(plume(x_ + 2, hh_ + 10, z_, 18, 2.5, 600 + k))
    if k % 2 == 0: P_ += lantern((x_ + side[0] * 6, hh_, z_ + side[1] * 6), C(255, 150, 60), 'ash')
for k in range(0, 36, 9): P_ += lantern((hx + side[0] * 16.8 + sd[0] * k, 1.6, hz + side[1] * 16.8 + sd[1] * k), C(255, 150, 60), 'ash')
cp_ = np.array([hx - side[0] * 6, 0, hz - side[1] * 6]); P_ += [cyl(0.5, 14, IRON, (cp_[0], 9, cp_[2]), sec=6), line((cp_[0], 16, cp_[2]), (cp_[0] + sd[0] * 12, 13, cp_[2] + sd[1] * 12), 0.3, IRON), line((cp_[0] + sd[0] * 12, 13, cp_[2] + sd[1] * 12), (cp_[0] + sd[0] * 12, 5, cp_[2] + sd[1] * 12), 0.05, IRON)]
bk = np.array([hx, 0, hz]) + np.array([sd[0], 0, sd[1]]) * 40 + np.array([side[0], 0, side[1]]) * 14
P_ += [cyl(1.6, 9, BLK, (bk[0], 5.5, bk[2]), sec=8), cyl(1.8, 1.2, IRON, (bk[0], 11.5, bk[2]), sec=8, r2=0)]; GL['ash'].append(ball(1.0, C(255, 120, 40), (bk[0], 10.6, bk[2]), 1))
props['vent_harbour'] = {'pos': [hx, 0, hz], 'yaw': yw, 'anchor': list(map(float, bk + np.array([sd[0], 0, sd[1]]) * 45)), 'cam': list(map(float, np.array([hx, 30, hz]) + np.array([sd[0], 0, sd[1]]) * 170 + np.array([side[0], 0, side[1]]) * 60)), 'kind': 'harbour'}
save('ash_harbour', merge(P_)); save('ash_steam', merge(steam), lod=False)
# ---------------------------------------------------------------- hidden spots (ash)
H_ = []
ox_, oz_, sd, yw, side = frame(330, 2620); op = []   # Obsidian Arch: glassy black sea arch off Cinderreach's south cape, chest in the arch
for k in range(24):
    a = math.pi * k / 23; op.append(rock((math.cos(a) * 20, math.sin(a) * 22 - 2, rng.uniform(-3, 3)), rng.uniform(4, 6.5), 600 + k, 0.8, C(20, 18, 24) if k % 2 else C(34, 30, 40)))
for k in range(12): op.append(cyl(0.6, rng.uniform(2, 6), C(30, 26, 44), (rng.uniform(-18, 18), rng.uniform(16, 22), rng.uniform(-2, 2)), (rng.uniform(-.4, .4), 0, rng.uniform(-.4, .4)), 5, 0))   # obsidian shards
op.append(box((1.6, 1.0, 1.0), WOOD, (-15, 1.2, 0))); op.append(rock((-15, -0.5, 0), 3, 690, 0.4, C(30, 28, 34)))
GL['ash'].append(T(merge([box((1.4, 0.15, 0.9), C(255, 200, 90), (-15, 1.75, 0))] + [ball(0.3, C(170, 80, 255), (rng.uniform(-16, 16), rng.uniform(4, 18), rng.uniform(-1, 1)), 0) for k in range(10)]), (ox_ + sd[0] * 40, 0, oz_ + sd[1] * 40), (0, yw + math.pi / 2, 0)))
opos = (ox_ + sd[0] * 40, 0, oz_ + sd[1] * 40); H_.append(T(merge(op), opos, (0, yw + math.pi / 2, 0)))
props['obsidian_arch'] = {'pos': list(map(float, opos)), 'hidden': True, 'skiff_only': True, 'cam': open_cam2(opos[0], opos[2], 80, 14), 'note': 'chest on the ledge under the arch'}
ex_, ez_, sd, yw, side = frame(900, 2450); ew = [T(hulk(63, 28), (0, -1.2, 0), (0.0, 0, -0.4)), cyl(0.5, 14, C(30, 24, 22), (0, 5, 3), (0.5, 0, -0.4), sec=6)]   # Ember Wreck: burnt galley in a lava-lit cove
ew = [darken(m, 0.35) for m in ew]; epos = (ex_ + sd[0] * 14, 0, ez_ + sd[1] * 14)
for k in range(12): lv.append(ribbon_on([(ex_ + rng.uniform(-14, 14) - sd[0] * j * 3, ez_ + rng.uniform(-14, 14) - sd[1] * j * 3) for j in range(6)], 1.4, 0.9))
GL['ash'].append(T(merge([ball(0.35, C(255, 110, 30), (rng.uniform(-3, 3), rng.uniform(-0.5, 2), rng.uniform(-12, 12)), 0) for k in range(14)]), epos, (0, yw, 0)))
H_.append(T(merge(ew), epos, (0, yw, 0))); props['ember_wreck'] = {'pos': list(map(float, epos)), 'hidden': True, 'cam': open_cam2(epos[0], epos[2], 70, 16), 'note': 'smouldering hull, loot in the stern'}
gx_, gz_ = 1100, 2000; gy_ = H_at(gx_, gz_); gp = []   # Hot-spring Grotto: steaming turquoise pool ringed by sulphur rock + ruined shrine
for k in range(20): a = k * math.tau / 20; gp.append(rock((gx_ + math.cos(a) * 11, gy_ - 0.4, gz_ + math.sin(a) * 9), rng.uniform(1.6, 2.8), 800 + k, 0.6, C(160, 140, 80) if k % 3 else C(200, 190, 160)))
pool = trimesh.creation.cylinder(10, 0.3, sections=20); pool.apply_transform(trimesh.transformations.rotation_matrix(-math.pi / 2, (1, 0, 0))); pool.apply_scale((1, 1, 0.82)); pool.apply_translation((gx_, gy_ - 0.2, gz_))
GL['ash'].append(paint(pool, C(80, 220, 210)))
for k in range(4): a = k * math.tau / 4 + 0.4; gp.append(cyl(0.8, rng.uniform(3, 6), C(150, 140, 130), (gx_ + math.cos(a) * 15, gy_ + 1.5, gz_ + math.sin(a) * 13), sec=8))
gp.append(box((3, 1.2, 2), C(140, 130, 120), (gx_ + 15, gy_ + 0.5, gz_ + 4)))
for k in range(4): steam.append(plume(gx_ + rng.uniform(-6, 6), gy_, gz_ + rng.uniform(-5, 5), 16, 6, 700 + k))
H_.append(merge(gp)); props['hot_spring_grotto'] = {'pos': [gx_, gy_, gz_], 'hidden': True, 'cam': open_cam2(gx_, gz_, 90, 30), 'note': 'heals the crew; shrine offering spot'}
save('ash_hidden_spots', merge(H_)); save('ash_glow', merge(GL['ash'])); save('ash_steam', merge(steam), lod=False); save('ash_lava_seams', merge(lv))
# ---------------------------------------------------------------- soft fog-bank border (same v2 style as regions A/B) + invisible blocker
_sf = open('/workspace/godot-art/ocean_stage2/tools/build_stormfog.py').read(); _sf = _sf[:_sf.index('for pre, (x0, z0, x1, z1) in REGIONS.items():')]
_fg = {'__name__': 'sf', 'sys': sys}; sys.argv = sys.argv[:1] + [OUT]; exec(_sf, _fg)
for pre, (x0, z0, x1, z1) in REG.items():
    parts, cols = [], []
    for k, (ins, hgt) in enumerate([(170, 55), (130, 75), (95, 95), (65, 115), (30, 135)]):
        m, c = _fg['ribbon'](_fg['loop'](x0, z0, x1, z1, ins), -6, hgt, k / 4.0, wob=22, seed=k * 1.7 + (3 if pre == 'ash' else 0)); parts.append(m); cols.append(c)
    fog = trimesh.util.concatenate(parts); fog.visual = trimesh.visual.ColorVisuals(fog, vertex_colors=np.concatenate(cols)); fog.export(os.path.join(OUT, f'{pre}_fog_layers.glb'))
    sky, _ = _fg['ribbon'](_fg['loop'](x0, z0, x1, z1, -220), -10, 420, 0, step=80, rows=4); sky.export(os.path.join(OUT, f'{pre}_storm_sky.glb'))
    _fg['band'](x0, z0, x1, z1, 150, -600).export(os.path.join(OUT, f'{pre}_storm_sea.glb'))
    cb = []; L = _fg['loop'](x0, z0, x1, z1, 40)
    for a_, b_ in zip(L, L[1:]):
        a_ = np.array(a_, float); b_ = np.array(b_, float); c = (a_ + b_) / 2; d = b_ - a_; Ln = np.linalg.norm(d)
        bx = trimesh.creation.box((Ln + 4, 60, 4) if abs(d[0]) > abs(d[1]) else (4, 60, Ln + 4)); bx.apply_translation((c[0], 20, c[1])); cb.append(bx)
    trimesh.util.concatenate(cb).export(os.path.join(OUT, f'{pre}_storm_col.glb')); STATS[f'{pre}_fog_layers'] = {'tris': len(fog.faces)}
FOGTINT = {'frost': {'fog_col': [0.78, 0.84, 0.90], 'fog_dark': [0.50, 0.58, 0.68]}, 'ash': {'fog_col': [0.52, 0.48, 0.46], 'fog_dark': [0.26, 0.23, 0.22]}}
json.dump({'tiles': TILES, 'regions': {'frost': {'name': 'C-N Frost Strait', 'rect': REG['frost'], 'wind': 'polar N', 'water': {'ice': 0.3, 'deep': [0.03, 0.12, 0.2], 'shallow': [0.16, 0.42, 0.5]}},
                                       'ash': {'name': 'C-S Ash Strait', 'rect': REG['ash'], 'wind': 'hot S', 'water': {'ice': 0.0, 'deep': [0.03, 0.07, 0.09], 'shallow': [0.10, 0.26, 0.26]}}},
           'channels': CHAN, 'icebergs': BERGS, 'vents': VENTS, 'fog': FOGTINT, 'props': props, 'stats': STATS,
           'notes': 'Channels: max-clearance centre-lines, widths = 2 x distance to shore. Icebergs: instance the 3 variants, move along drift_dir (bounce off DM<40). '
                    'Floes: decorative, no collision. Lava/steam/glow shaders in shaders/.'}, open(os.path.join(OUT, 'stage4_manifest.json'), 'w'), indent=1, default=float)
print('DONE')
