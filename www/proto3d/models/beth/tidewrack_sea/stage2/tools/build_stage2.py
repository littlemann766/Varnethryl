#!/usr/bin/env python3
"""Beth: Tidewrack Sea STAGE 2 art builder: region B Saltglass Coast + the Sunken Ward dive spot.
Reuses Stage 1 helpers (exec of build_stage1.py's helper blocks). Same conventions: Godot coords, map metres, 1 surface per mesh, _lod1 <=50%."""
import os, math, json
S1 = '/workspace/godot-art/ocean_stage1/tools/build_stage1.py'
_src = open(S1).read().split('\n')
_g = {'__file__': S1, '__name__': 'stage1_helpers'}
def _blk(start, stop):
    a_ = next(i for i, l in enumerate(_src) if l.startswith(start)) if start else 0; b_ = next(i for i, l in enumerate(_src) if i > a_ and l.startswith(stop)); return '\n'.join(_src[a_:b_])
exec(_blk(None, 'step = 2'), _g)                  # helpers + v4 land mask (with islets) + height_field/sample/nearest_shore
exec(_blk('WOOD = C(', 'props = {}'), _g)         # prop helpers (house, dock, rock, find_water, open_cam, colours)
exec(_blk('def hulk', 'wx, wz'), _g)              # hulk()
exec(_blk('def ribbon', 'inset = 40'), _g)        # ribbon()
globals().update({k: v for k, v in _g.items() if not k.startswith('__')})
ROOT2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT = os.path.join(ROOT2, 'meshes'); os.makedirs(OUT, exist_ok=True)
_g['OUT'] = OUT; STATS = _g['STATS']; STATS.clear()
save = _g['save']
import numpy as np, trimesh
from scipy import ndimage
from scipy.spatial import cKDTree
import fast_simplification
from PIL import Image
rng = np.random.default_rng(42)
X0, Z0, X1, Z1 = -3000, -1500, -1200, 1700
SALT = C(176, 236, 242); SALT2 = C(120, 210, 230); DARK = C(14, 14, 18); CLIFF = C(122, 110, 98); CLIFF2 = C(92, 84, 78)
# ---------------------------------------------------------------- coast terrain: cliffs on the exposed coast, beaches in coves
def hf_coast(lf, n, x):
    mainland = x < -2150
    cliffy = mainland & (n > -0.35)
    beach = np.where(lf < 18, lf * 0.09, 1.6 + (lf - 18) * (0.11 + 0.05 * n) + np.clip(n, 0, None) * 9)
    cliff = np.clip(lf, 0, 9) * (2.4 + 0.8 * n) + np.clip(lf - 9, 0, None) * (0.10 + 0.04 * n) + np.clip(n, 0, None) * 12
    land = np.where(cliffy, cliff, beach)
    land = np.where(mainland, land + np.clip((lf - 120) * 0.05, 0, 40), land)   # uplands
    sea = np.where(cliffy, np.maximum(lf * 0.35, -14.0), np.maximum(lf * 0.16, -12.0))  # cliffs drop into deeper water
    return np.where(lf > 0, np.minimum(land, 120), sea), cliffy
_sol0 = D['solid'] > 0; _edge0 = _sol0 & ndimage.binary_dilation(~_sol0); _ej0, _ei0 = np.nonzero(_edge0); _et0 = cKDTree(np.stack([_ei0, _ej0], 1))
CAVES = {'coast_echo_grotto': ((-2330, -300), 18, 15, 'echo', 1), 'coast_glasswyrm_cavern': ((-2330, 360), 24, 18, 'wyrm', 2), 'coast_smugglers_throat': ((-2330, 1100), 14, 16, 'smug', 3)}
CAVE_GEO = {}
_yy, _xx = np.mgrid[0:S, 0:S]
for _n, ((x, z), w, hgt, kind, sd_) in CAVES.items():
    i, j = px(x, z); _, k = _et0.query([i, j]); si, sj = _ei0[k], _ej0[k]; sx_, sz_ = (si - S / 2) / pm, (sj - S / 2) / pm
    w_ = LF[sj - 8:sj + 9, si - 8:si + 9]; gzz, gxx = np.gradient(ndimage.gaussian_filter(w_, 2)); dv = -np.array([gxx[8, 8], gzz[8, 8]]); dv /= np.linalg.norm(dv) + 1e-9
    # cleft: from 12 m out to sea to 40 m inland, half-width w/2 (metres in LF units ~ metres)
    ax_, az_ = sx_ + dv[0] * 12, sz_ + dv[1] * 12; bx_, bz_ = sx_ - dv[0] * 40, sz_ - dv[1] * 40
    sl = (slice(max(0, int(sj - 40)), int(sj + 40)), slice(max(0, int(si - 40)), int(si + 40)))
    MXs = (_xx[sl] - S / 2) / pm; MZs = (_yy[sl] - S / 2) / pm; abx, abz = bx_ - ax_, bz_ - az_; L2 = abx * abx + abz * abz
    t = np.clip(((MXs - ax_) * abx + (MZs - az_) * abz) / L2, 0, 1); dd = np.hypot(MXs - (ax_ + abx * t), MZs - (az_ + abz * t))
    LF[sl] = np.minimum(LF[sl], (dd - w / 2 * (1 - 0.4 * t)) * 1.0)
    CAVE_GEO[_n] = (sx_, sz_, dv, w, hgt, kind, sd_)
step = 2
i0, j0 = map(int, px(X0, Z0)); i1, j1 = map(int, px(X1, Z1)); i0 = max(i0, 0)
lf = LF[j0:j1:step, i0:i1:step]; n = N1[j0:j1:step, i0:i1:step]
gz, gx = np.mgrid[j0:j1:step, i0:i1:step]; WXg = (gx - S / 2) / pm; WZg = (gz - S / 2) / pm
H, CL = hf_coast(lf, n, WXg)
# Stage 3 fix: the map's small scattered islets came out as pale sandy pyramids. Make them low, rounded, dark weathered rock.
_orig = D['land_f'][j0:j1:step, i0:i1:step]; ISLET = (lf > 0) & (_orig <= 0)
_ins = np.clip(lf, 0, None) / 1.4
H = np.where(ISLET, 7.0 * (1 - np.exp(-_ins / 7.0)) * (0.8 + 0.4 * np.clip(n + 0.5, 0, 1)) - 0.6, H)
keep = lf > -50
idx = -np.ones(lf.shape, int); idx[keep] = np.arange(keep.sum())
V = np.stack([WXg[keep], H[keep], WZg[keep]], 1)
q = keep[:-1, :-1] & keep[1:, :-1] & keep[:-1, 1:] & keep[1:, 1:]
a = idx[:-1, :-1][q]; b = idx[:-1, 1:][q]; c_ = idx[1:, :-1][q]; d = idx[1:, 1:][q]
Fc = np.concatenate([np.stack([a, c_, b], 1), np.stack([b, c_, d], 1)])
coast = trimesh.Trimesh(V, Fc, process=False)
nrm = coast.vertex_normals; slope = 1 - np.abs(nrm[:, 1]); h = V[:, 1]; clf = CL[keep]
col = np.tile(C(88, 126, 62), (len(V), 1)); col[h > 40] = C(74, 104, 56); col[h > 75] = C(118, 116, 102)
col[(h < 2.2) & ~clf] = C(216, 198, 142); col[h < 0] = C(170, 160, 120); col[h < -5] = C(104, 116, 104)
rk = (slope > 0.4) & (h > 0.3); col[rk] = CLIFF; col[(slope > 0.6) & (h > 0)] = CLIFF2
band = (slope > 0.5) & (h > 3) & (h < 30) & (np.sin(h * 1.3) > 0.6); col[band] = C(150, 136, 118)   # strata bands
col[clf & (h < 1.5) & (h > -2)] = C(64, 60, 58)   # dark wet rock at the cliff foot
isl_k = ISLET[keep]; col[isl_k] = C(78, 74, 70); col[isl_k & (h < 1.2)] = C(42, 42, 44); col[isl_k & (h > 4.5)] = C(96, 104, 80)
coast.visual = trimesh.visual.ColorVisuals(coast, vertex_colors=col)
v2, f2 = fast_simplification.simplify(coast.vertices.astype(np.float32), coast.faces.astype(np.int64), target_reduction=max(0, 1 - 180000 / len(coast.faces)))
c2 = trimesh.Trimesh(v2, f2, process=False); c2.visual = trimesh.visual.ColorVisuals(c2, vertex_colors=col[cKDTree(V).query(v2)[1]])
save('coast_terrain', c2)   # full mesh kept for reference/collision bake
def split_tiles(mesh, name, nx=3, nz=4, suf=''):
    cen = mesh.triangles_center; out = []
    for ix in range(nx):
        for iz in range(nz):
            xa = X0 + (X1 - X0) * ix / nx; xb = X0 + (X1 - X0) * (ix + 1) / nx; za = Z0 + (Z1 - Z0) * iz / nz; zb = Z0 + (Z1 - Z0) * (iz + 1) / nz
            sel = (cen[:, 0] >= xa) & (cen[:, 0] < xb + (ix == nx - 1)) & (cen[:, 2] >= za) & (cen[:, 2] < zb + (iz == nz - 1))
            if sel.sum() == 0: continue
            sub = mesh.submesh([np.nonzero(sel)[0]], append=True); sub.export(os.path.join(OUT, f'{name}_x{ix}z{iz}{suf}.glb')); out.append((f'{name}_x{ix}z{iz}{suf}', int(sel.sum())))
    return out
_hi = trimesh.load(os.path.join(OUT, 'coast_terrain.glb'), force='mesh'); _lo = trimesh.load(os.path.join(OUT, 'coast_terrain_lod1.glb'), force='mesh')
TILES = {'high': split_tiles(_hi, 'coast_tile'), 'lod1': split_tiles(_lo, 'coast_tile', suf='_lod1')}
for _f in ('coast_terrain.glb', 'coast_terrain_lod1.glb'): os.remove(os.path.join(OUT, _f))   # tiles replace the single mesh
STATS['coast_terrain_tiles'] = {'count': len(TILES['high']), 'note': '3x4 tiles, 600 x 800 m; frustum + shadow culled per tile'}
v3, f3 = fast_simplification.simplify(v2, f2, target_reduction=0.93); trimesh.Trimesh(v3, f3).export(os.path.join(OUT, 'coast_terrain_col.glb'))
dm = np.clip(D['dist_m'][j0:j1, i0:i1], 0, 255).astype(np.uint8); Image.fromarray(dm).save(os.path.join(ROOT2, 'shaders', 'coast_shore_dist.png'))
json.dump({'x0': X0, 'z0': Z0, 'x1': X1, 'z1': Z1, 'px_m': 1 / pm, 'shore_rect': [X0, Z0, X1 - X0, Z1 - Z0], 'note': 'R = metres to nearest land (0..255)'}, open(os.path.join(ROOT2, 'shaders', 'coast_shore_dist.json'), 'w'), indent=1)
def H_at(x, z):
    i, j = px(x, z); l_ = ndimage.map_coordinates(LF, [[j], [i]], order=1); n_ = ndimage.map_coordinates(N1, [[j], [i]], order=1)
    return float(hf_coast(l_, n_, np.array([x]))[0][0])
def shore_dir2(x, z):
    i, j = px(x, z); i, j = int(i), int(j); w = LF[j - 6:j + 7, i - 6:i + 7]; gzz, gxx = np.gradient(ndimage.gaussian_filter(w, 2)); v = -np.array([gxx[6, 6], gzz[6, 6]]); return v / (np.linalg.norm(v) + 1e-9)
props = {}
_sol = D['solid'] > 0; _edge = _sol & ndimage.binary_dilation(~_sol); _ej, _ei = np.nonzero(_edge); _etree = cKDTree(np.stack([_ei, _ej], 1))
def nearest_shore(x, z, want_land=True):  # exact: nearest coastline pixel of the v4 mask
    i, j = px(x, z); _, k = _etree.query([i, j]); return (float((_ei[k] - S / 2) / pm), float((_ej[k] - S / 2) / pm))
def line_(a_, b_, r, c): return line(a_, b_, r, c)
# ---------------------------------------------------------------- Saltglass Landing: cliff port (pier, switchback stair, lift, clifftop town)
lx, lz = nearest_shore(-2080, -130); sd = shore_dir2(lx, lz); yw = math.atan2(sd[0], sd[1]); side = np.array([sd[1], -sd[0]])
P_ = [dock((lx, 0, lz), yw, 55, 6), dock((lx + side[0] * 26, 0, lz + side[1] * 26), yw, 34, 4)]
top_d = 22; tx_, tz_ = lx - sd[0] * top_d, lz - sd[1] * top_d; topy = max(H_at(tx_, tz_), 6)
for k in range(int(topy / 1.2)):   # switchback stair carved up the cliff face
    t = k / max(1, int(topy / 1.2)); zig = (k // 6) % 2; s_ = (k % 6) / 6.0 * (1 if zig == 0 else -1) + (0 if zig == 0 else 1)
    p = np.array([lx, 0, lz]) - np.array([sd[0], 0, sd[1]]) * (2 + t * (top_d - 4)) + np.array([side[0], 0, side[1]]) * (s_ * 10 - 5)
    P_.append(box((3.0, 0.6, 2.0), STONE, (p[0], 1.6 + k * 1.2, p[2]), (0, yw, 0)))
lift = np.array([lx, 0, lz]) + np.array([side[0], 0, side[1]]) * 12
P_ += [cyl(0.4, topy + 6, DKW, (lift[0], (topy + 6) / 2, lift[2]), sec=6), cyl(0.4, topy + 6, DKW, (lift[0] + side[0] * 4, (topy + 6) / 2, lift[2] + side[1] * 4), sec=6),
       box((5, 0.6, 1.0), DKW, (lift[0] + side[0] * 2, topy + 6, lift[2] + side[1] * 2), (0, yw + math.pi / 2, 0)), box((3, 2, 3), WOOD, (lift[0] + side[0] * 2, topy * 0.55, lift[2] + side[1] * 2))]
for k in range(14):
    back = 26 + (k // 5) * 13 + rng.uniform(-2, 2); sv = (k % 5 - 2) * 13 + rng.uniform(-3, 3)
    hx = lx - sd[0] * back + side[0] * sv; hz = lz - sd[1] * back + side[1] * sv
    P_.append(house((hx, H_at(hx, hz) - 0.4, hz), yw + rng.uniform(-.25, .25), rng.uniform(6, 9), rng.uniform(6, 10), rng.uniform(4, 8), ROOF2 if k % 3 else ROOF))
wh = np.array([tx_, topy, tz_]); P_.append(T(merge([box((18, 8, 11), STONE, (0, 4, 0)), box((19, 1, 12), ROOF2, (0, 8.5, 0))]), (wh[0], wh[1] - 0.5, wh[2]), (0, yw, 0)))
bk = np.array([lx, 0, lz]) + np.array([sd[0], 0, sd[1]]) * 56   # beacon on the pier head
P_ += [cyl(1.2, 7, STONE, (bk[0], 4.5, bk[2]), sec=8), cyl(1.0, 1.6, C(255, 220, 130), (bk[0], 8.8, bk[2]), sec=8), cyl(1.4, 1.6, IRON, (bk[0], 10.4, bk[2]), sec=8, r2=0)]
props['saltglass_landing'] = {'pos': [lx, 0, lz], 'yaw': yw, 'anchor': list(map(float, (bk + np.array([sd[0], 0, sd[1]]) * 40))), 'cam': open_cam(lx, lz, 120, 30)}
save('coast_saltglass_landing', merge(P_))
# ---------------------------------------------------------------- sea caves (skiff-only): mouths set into the cliff, facing the sea
def cave_mouth(x, z, w, hgt, depth, seed, kind):
    sx_, sz_ = nearest_shore(x, z); sdv = shore_dir2(sx_, sz_); yaw = math.atan2(sdv[0], sdv[1]); r = np.random.default_rng(seed); parts = []
    # arch ring of jagged boulders + dark throat that recedes into the cliff
    for k in range(18):
        t = k / 17; a = math.pi * t; px_ = math.cos(a) * w / 2; py_ = math.sin(a) * hgt
        parts.append(rock((px_, py_ - 1.5, r.uniform(-1, 1.5)), r.uniform(2.5, 4.5) * (1.3 if k in (0, 17) else 1), seed * 50 + k, 0.8, CLIFF2 if k % 2 else CLIFF))
    for k in range(5):
        parts.append(rock((r.uniform(-w / 2, w / 2), hgt + r.uniform(1, 6), r.uniform(-4, 1)), r.uniform(4, 7), seed * 70 + k, 0.7, CLIFF))
    throat = trimesh.creation.cylinder(1.0, depth, sections=12); throat.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, (1, 0, 0)))  # along z? cylinder z->y? keep along z
    throat = trimesh.creation.cylinder(1.0, depth, sections=12); throat.apply_scale((w * 0.42, hgt * 0.9, 1)); throat.apply_translation((0, hgt * 0.3, -depth / 2 + 1)); parts.append(paint(throat, DARK))
    if kind == 'echo':   # hanging saltglass + drip stones
        for k in range(10): parts.append(cyl(0.35, r.uniform(1.5, 3.5), SALT, (r.uniform(-w / 3, w / 3), hgt - 1, r.uniform(-2, 1)), (math.pi, 0, 0), 5, 0))
    if kind == 'wyrm':   # jagged glowing saltglass teeth + ribs of an old kill
        for k in range(14): a = math.pi * k / 13; parts.append(cyl(0.6, r.uniform(2.5, 5), SALT2 if k % 2 else SALT, (math.cos(a) * w * 0.45, math.sin(a) * hgt * 0.95 - 0.5, 1.5), (0, 0, a - math.pi / 2 + math.pi), 5, 0))
        for k in range(6): parts.append(line((-3, 0.5, -2 - k * 2.2), (-1.5, 4.0 + k * 0.1, -2.5 - k * 2.2), 0.25, C(230, 224, 200)))
    if kind == 'smug':   # rope bridge over the cleft, lanterns, a hidden jetty
        parts.append(line((-w / 2 - 1, hgt + 2, 0), (w / 2 + 1, hgt + 2, 0), 0.08, C(150, 120, 80)))
        for k in range(12): parts.append(box((0.6, 0.12, 1.6), WOOD, (-w / 2 + k * w / 11, hgt + 1.8 - 0.6 * math.sin(math.pi * k / 11), 0)))
        for k in range(3): parts.append(ball(0.35, C(255, 200, 110), (-w / 4 + k * w / 4, 2.6, -3)))
        parts.append(T(dock((0, 0, 0), math.pi, 10, 2.5), (w * 0.2, 0, -2)))
    m = merge(parts); return T(m, (sx_, 0, sz_), (0, yaw, 0)), [sx_, 0, sz_], yaw
def cave_mouth2(sx_, sz_, dv, w, hgt, kind, seed):
    yaw = math.atan2(dv[0], dv[1]); r = np.random.default_rng(seed); parts = []
    for k in range(20):   # arch over the cleft mouth, legs anchored on the cliff either side
        t = k / 19; a = math.pi * t; _rs = 1.0 if kind == 'wyrm' else 0.55; parts.append(rock((math.cos(a) * (w / 2 + 2 * _rs), math.sin(a) * hgt + 1, r.uniform(-1, 1) * _rs - (0 if kind == 'wyrm' else 1.5)), r.uniform(2.8, 4.8) * _rs * (1.4 if k in (0, 19) else 1), seed * 50 + k, 0.8, CLIFF2 if k % 2 else CLIFF))
    for k in range(12):   # roof: lumpy boulders bridging the cleft going inland (Stage 4 polish: was flat box slabs)
        zz = -3 - k * 3.2
        for j in range(4): parts.append(rock(((j - 1.5) * (w + 8) / 4 + r.uniform(-1, 1), hgt + 3.5 + k * 0.9 + r.uniform(-0.6, 0.6), zz + r.uniform(-1, 1)), (w + 8) / 5.2 + r.uniform(0, 1.2), seed * 130 + k * 4 + j, 0.62, CLIFF2 if (k + j) % 2 else CLIFF))
    for k in range(3):  # dark void walls deep in the cleft
        parts.append(box((w * (0.9 - 0.2 * k), hgt * (1.1 - 0.2 * k), 0.4), DARK, (0, hgt * 0.45 - 1, -14 - k * 9)))
    parts.append(box((w + 2, 1.0, 38), DARK, (0, hgt + 1.0, -20)))   # ceiling underside (dark)
    _hv = [(0, -1.5, -0.8)] + [(math.cos(math.pi * t) * (w / 2 + 0.5), max(-1.5, math.sin(math.pi * t) * (hgt + 0.5)), 0.6) for t in np.linspace(0, 1, 17)]
    parts.append(paint(trimesh.Trimesh(_hv, [(0, k + 1, k + 2) for k in range(16)] + [(0, k + 2, k + 1) for k in range(16)], process=False), DARK))   # black opening fills the arch
    if kind in ('echo', 'smug'):   # Stage 3: deep dark overhang so the mouth reads as a cave from a distance
        oh = hgt * 0.55
        for k in range(7):   # brow of the cliff pushed out over the water
            a = math.pi * (0.08 + 0.84 * k / 8); parts.append(rock((math.cos(a) * (w / 2 + 3), hgt + oh * 0.4 + math.sin(a) * oh * 0.5, 3.5 + r.uniform(-1, 1)), r.uniform(4.5, 7), seed * 90 + k, 0.7, CLIFF2))
        for j in range(9):   # overhang brow: overlapping squashed boulders, sagging at the middle (Stage 4 polish: was one box slab)
            u = (j - 4) / 4.0; parts.append(rock((u * (w + 12) / 2 + r.uniform(-0.8, 0.8), hgt + oh * 0.55 - 0.9 * (1 - u * u) + r.uniform(-0.5, 0.5), 2.0 + r.uniform(-1.5, 1.5) + 1.2 * (1 - u * u)), (w + 14) / 9 + oh * 0.35 + r.uniform(0, 1.0), seed * 170 + j, 0.55, CLIFF2 if j % 2 else C(78, 72, 68)))
        parts.append(box((w + 6, 0.6, 12), DARK, (0, hgt - 0.2, 1.5)))                        # its dark underside
        for k in range(3): parts.append(box((w * (1.05 - 0.15 * k), hgt * (1.0 - 0.15 * k), 0.4), DARK, (0, hgt * 0.5 - 1.2, -2.5 - k * 3.0)))   # near-mouth black voids
        for k in range(10): parts.append(cyl(0.5, r.uniform(1.5, 4.0), CLIFF2, (r.uniform(-w / 2, w / 2), hgt - 0.6, r.uniform(-1, 5)), (math.pi, 0, 0), 5, 0))   # dripstone fringe
    if kind == 'echo':
        for k in range(14): parts.append(cyl(0.35, r.uniform(1.5, 3.8), SALT, (r.uniform(-w / 2.5, w / 2.5), hgt - 0.5, r.uniform(-12, 1)), (math.pi, 0, 0), 5, 0))
    if kind == 'wyrm':
        for k in range(16): a = math.pi * k / 15; parts.append(T(cyl(0.7, r.uniform(3, 6), SALT2 if k % 2 else SALT, (0, 0, 0), sec=5, r2=0), (math.cos(a) * (w / 2), math.sin(a) * hgt * 0.95, 1.5), (0, 0, a + math.pi / 2)))
        for k in range(7): parts.append(line((-w / 3, 0.4, -4 - k * 2.4), (-w / 3 + 3, 5.0, -4.5 - k * 2.4), 0.3, C(230, 224, 200)))
    if kind == 'smug':
        for k in range(12): parts.append(box((0.6, 0.12, 1.6), WOOD, (-w / 2 + k * w / 11, hgt + 6 - 0.8 * math.sin(math.pi * k / 11), 4)))
        parts.append(line((-w / 2 - 2, hgt + 6.5, 4), (w / 2 + 2, hgt + 6.5, 4), 0.08, C(150, 120, 80)))
        for k in range(3): parts.append(ball(0.4, C(255, 200, 110), (-w / 3 + k * w / 3, 2.6, -6)))
        parts.append(T(dock((0, 0, 0), math.pi, 12, 2.5), (w * 0.25, 0, -2)))
    return T(merge(parts), (sx_, 0, sz_), (0, yaw, 0)), [sx_, 0, sz_], yaw
for name, (sx_, sz_, dv, w, hgt, kind, sd_) in CAVE_GEO.items():
    m, p, yw_ = cave_mouth2(sx_, sz_, dv, w, hgt, kind, sd_); save(name, m)
    props[name] = {'pos': p, 'yaw': yw_, 'skiff_only': True, 'interior_cell': name.replace('coast_', '') + '_interior (Stage 3 sub-cell)', 'cam': open_cam(p[0], p[2], 45 + w, 10 + hgt * 0.6)}
# ---------------------------------------------------------------- Sunken Ward dive spot: drowned district breaking the surface
sw = []; cx_, cz_ = -1300, 400
for k in range(16):   # broken column clusters
    a = rng.uniform(0, math.tau); r = rng.uniform(15, 110); bx, bz = cx_ + math.cos(a) * r * 1.2, cz_ + math.sin(a) * r
    for j in range(rng.integers(2, 5)):
        hh = rng.uniform(4, 13); sw.append(T(cyl(1.1, hh, C(196, 190, 176), (0, hh / 2 - 6, 0), sec=10), (bx + j * 3.5, 0, bz + rng.uniform(-1, 1)), (rng.uniform(-0.15, 0.15), 0, rng.uniform(-0.2, 0.2))))
        sw.append(box((2.8, 0.8, 2.8), C(176, 170, 156), (bx + j * 3.5, -6.4, bz)))
for k, (ox, oz, hh) in enumerate([(-60, -40, 16), (70, 90, 12)]):   # drowned watch towers, tops awash
    sw.append(cyl(5.5, hh, C(160, 156, 146), (cx_ + ox, hh / 2 - 9, cz_ + oz), sec=12))
    for j in range(10): a = j * math.tau / 10; sw.append(box((1.6, 1.4 + (j % 3) * 0.8, 1.1), C(140, 136, 128), (cx_ + ox + math.cos(a) * 5.4, hh - 8.5, cz_ + oz + math.sin(a) * 5.4), (0, -a, 0)))
for k in range(12):   # a long arcade (arches) marking the old high street
    x = cx_ - 120 + k * 9; sw += [box((1.4, 9, 1.4), C(190, 184, 170), (x, -3.5, cz_ + 150)), box((9.2, 1.2, 1.6), C(176, 170, 156), (x + 4.5, 1.0 - (k % 4 == 3) * 2.2, cz_ + 150))]
dome = trimesh.creation.icosphere(2, 14); dome.vertices[:, 1] = np.abs(dome.vertices[:, 1]); sw.append(T(paint(dome, C(120, 150, 140)), (cx_ + 10, -10.5, cz_ - 20), scale=(1, 0.8, 1)))   # green-copper dome cap just under
db = (-1300, 300); sw += [T(merge([box((10, 0.6, 10), WOOD, (0, 0.6, 0))] + [cyl(0.5, 1.4, C(220, 170, 40), (sx * 4.5, 0.2, sz * 4.5), sec=8) for sx in (-1, 1) for sz in (-1, 1)] + [line((-4.5, 1, -4.5), (0, 6, 0), 0.12, DKW), line((4.5, 1, 4.5), (0, 6, 0), 0.12, DKW), line((0, 6, 0), (0, 0.8, 0), 0.04, IRON)]), (db[0] + 14, 0, db[1]))]
props['sunken_ward'] = {'box': [-1520, 150, -1080, 650], 'dive_buoy': [db[0], 0, db[1]], 'dive_raft': [db[0] + 14, 0, db[1]], 'ring_radius': 30, 'cam': [db[0] - 110, 24, db[1] + 150]}
save('coast_sunken_ward_surface', merge(sw))
# ---------------------------------------------------------------- saltglass crystal clusters on clifftops + offshore rocks/stacks + driftwood + a beached wreck
lfB = LF[j0:j1, i0:i1]; dB = D['dist_m'][j0:j1, i0:i1]; xs = lambda ii: (ii + i0 - S / 2) / pm; zs = lambda jj: (jj + j0 - S / 2) / pm
cand = np.argwhere((lfB > 8) & (lfB < 70)); cr = []
for k in rng.choice(len(cand), 170, replace=False):
    jj, ii = cand[k]; x, z = xs(ii), zs(jj)
    if x > -2150 and rng.uniform() < 0.7: continue
    y = H_at(x, z) - 0.3
    for j in range(rng.integers(3, 7)):
        hh = rng.uniform(1.0, 4.5); cr.append(T(cyl(rng.uniform(0.25, 0.6), hh, SALT if j % 2 else SALT2, (0, hh / 2, 0), sec=6, r2=0.05), (x + rng.uniform(-1.5, 1.5), y, z + rng.uniform(-1.5, 1.5)), (rng.uniform(-0.5, 0.5), rng.uniform(0, 3), rng.uniform(-0.5, 0.5))))
save('coast_saltglass_crystals', merge(cr))
cand = np.argwhere((dB > 3) & (dB < 45)); rp = []
for k in rng.choice(len(cand), 300, replace=False):
    jj, ii = cand[k]; x, z = xs(ii), zs(jj)
    if rng.uniform() < 0.2 and x < -2150: rp.append(natural_stack(x, z, rng.uniform(12, 34), rng.uniform(3.5, 6.5), 5000 + int(k)))
    else: rp.append(rock((x, rng.uniform(-1.2, 0.3), z), rng.uniform(1.2, 5.5), 900 + int(k), 0.6, CLIFF2 if k % 3 else DST))
save('coast_offshore_rocks', merge(rp))
cand = np.argwhere((lfB > 1) & (lfB < 10)); dw = []
for k in rng.choice(len(cand), 90, replace=False):
    jj, ii = cand[k]; x, z = xs(ii), zs(jj); y = H_at(x, z)
    if y > 2.5: continue
    dw.append(T(cyl(0.22, rng.uniform(2, 5), C(170, 150, 120), (0, 0, 0), sec=5), (x, y + 0.2, z), (math.pi / 2, rng.uniform(0, 3), 0)))
wx_, wz_ = nearest_shore(-2250, 900); dw.append(T(hulk(77, 22), (wx_, max(H_at(wx_, wz_), 0) + 0.8, wz_), (0, 1.1, 0.3)))
props['beached_wreck'] = {'pos': [wx_, 0, wz_]}
save('coast_beach_dressing', merge(dw))
# ---------------------------------------------------------------- region border: storm wall + fog bank (B is locked until the Coil falls)
ins = 40
pass  # v1 slab wall retired (storm border v2: tools/build_stormfog.py)
if False: ribbon([(X0 + ins, Z0 + ins), (X1 - ins, Z0 + ins), (X1 - ins, Z1 - ins), (X0 + ins, Z1 - ins), (X0 + ins, Z0 + ins)], 140).export(os.path.join(OUT, 'coast_storm_wall.glb'))
if False: ribbon([(X0 + 100, Z0 + 100), (X1 - 100, Z0 + 100), (X1 - 100, Z1 - 100), (X0 + 100, Z1 - 100), (X0 + 100, Z0 + 100)], 45).export(os.path.join(OUT, 'coast_fog_bank.glb'))
STATS['coast_storm_wall'] = {'tris': 320}; STATS['coast_fog_bank'] = {'tris': 320}
json.dump({'tiles': TILES, 'region': 'B Saltglass Coast', 'rect': [X0, Z0, X1, Z1], 'stats': STATS, 'props': props}, open(os.path.join(OUT, 'stage2_manifest.json'), 'w'), indent=1, default=float)
print('DONE')
