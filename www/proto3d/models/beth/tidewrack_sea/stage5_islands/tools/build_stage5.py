#!/usr/bin/env python3
"""Beth: Tidewrack Sea STAGE 5 - island interiors behind the 13 landing points (Lucky test 35).
For every landing in landings_v1.json: an overlay terrain patch inland of the pier head (shaped hills, outcrops, paths from the
pier to each point of interest, region ground: temperate / saltglass / frost / ash) + 2-4 points of interest + scatter.
The patch is sampled from the existing stage 1/2/4 terrain (never edits it), sits +0.08 m above it, is cut out around every
existing prop (ports, keep, lighthouse, arena, harbours, wrecks, arches) and stays at the original height within 14 m of the
pier head, so docks, landing spots and existing colliders are untouched.
Output per landing, in meshes/<region>/ (drop into that region's mesh dir; tw_sea.gd auto-loads by prefix):
  {pre}isl_<id>.glb / _lod1.glb  (terrain + props, vertex colour)   {pre}isl_<id>_glow.glb (lanterns, lava, crystals, pools)
  {pre}isl_<id>_col.glb (walk collider: simplified patch + solid POI parts)
Usage: build_stage5.py [id ...]   (no args = all 13)"""
import os, sys, math, json, glob, zlib
S1 = '/workspace/godot-art/ocean_stage1/tools/build_stage1.py'
_src = open(S1).read().split('\n'); _g = {'__file__': S1, '__name__': 'stage1_helpers'}
def _blk(start, stop):
    a_ = next(i for i, l in enumerate(_src) if l.startswith(start)) if start else 0; b_ = next(i for i, l in enumerate(_src) if i > a_ and l.startswith(stop)); return '\n'.join(_src[a_:b_])
exec(_blk(None, 'step = 2'), _g); exec(_blk('WOOD = C(', 'props = {}'), _g)
globals().update({k: v for k, v in _g.items() if not k.startswith('__')})
import numpy as np, trimesh, fast_simplification
from scipy import ndimage
from scipy.interpolate import LinearNDInterpolator
from scipy.spatial import cKDTree
from skimage import graph
ROOT5 = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); GA = os.path.dirname(ROOT5)
STATS = _g['STATS']; STATS.clear()
L = json.load(open(os.path.join(ROOT5, 'landings_v1.json')))
RDIR = {'A': ('ocean_stage1/meshes', 'arch_'), 'B': ('ocean_stage2/meshes', 'coast_'), 'frost': ('ocean_stage4/meshes', 'frost_'), 'ash': ('ocean_stage4/meshes', 'ash_')}
SKIPFP = ('_fog', '_storm', '_steam', '_ice_floes', '_iceberg', '_col', '_lod1', 'isl_', 'sunken_ward', 'offshore')
STEP = 2.0
# ground palettes (sRGB; save() linearises)
PAL = {
 'temperate': dict(g1=C(92, 140, 62), g2=C(118, 160, 74), g3=C(74, 116, 54), path=C(156, 124, 84), rock=C(124, 120, 112), rock2=C(96, 92, 88), sand=C(206, 190, 150), cliff=C(140, 128, 104)),
 'saltglass': dict(g1=C(146, 160, 108), g2=C(214, 210, 196), g3=C(200, 176, 186), path=C(176, 160, 136), rock=C(152, 142, 152), rock2=C(118, 110, 124), sand=C(222, 214, 196), cliff=C(170, 160, 168)),
 'frost': dict(g1=C(232, 238, 244), g2=C(214, 226, 238), g3=C(176, 204, 224), path=C(170, 182, 198), rock=C(150, 176, 200), rock2=C(118, 136, 156), sand=C(200, 214, 226), cliff=C(150, 188, 214)),
 'ash': dict(g1=C(58, 55, 56), g2=C(78, 74, 73), g3=C(118, 100, 58), path=C(96, 84, 76), rock=C(32, 31, 34), rock2=C(22, 22, 25), sand=C(28, 28, 31), cliff=C(38, 36, 38))}
GROUND = {'A': 'temperate', 'B': 'saltglass', 'frost': 'frost', 'ash': 'ash'}
# per landing: window half-size, hill amplitude, POIs (type, name); first POI goes on the high ground
ISL = {
 'gullhaven':      dict(R=170, amp=11, pois=[('watchtower', 'Gull Watchtower ruin'), ('shrine', 'Gull Shrine'), ('lore', 'Founders\' Stone'), ('chest', 'Harbourmaster\'s Cache')]),
 'saltglass':      dict(R=170, amp=9,  pois=[('crystal_shrine', 'Saltglass Shrine'), ('crystal_grove', 'Singing Shards'), ('chest', 'Glass-diver\'s Chest'), ('lore', 'Salt-crusted Tablet')]),
 'frostreach':     dict(R=170, amp=10, pois=[('ice_cave', 'Rimehollow Ice Cave'), ('frost_shrine', 'Frostreach Cairn'), ('chest', 'Iced Chest'), ('lore', 'Frozen Waystone')]),
 'vent':           dict(R=170, amp=9,  pois=[('lava_vent', 'Ventmouth'), ('hot_pool', 'Steam Pools'), ('obsidian_shrine', 'Ember Shrine'), ('chest', 'Ash-buried Chest')]),
 'lantern_rock':   dict(R=120, amp=9,  pois=[('lighthouse', 'Old Lantern ruin'), ('hut_ruin', 'Keeper\'s Hut'), ('chest', 'Keeper\'s Strongbox'), ('lore', 'Lamp-oil Logbook')]),
 'saltwatch_keep': dict(R=150, amp=10, pois=[('keep_ruin', 'Outer Wall ruin'), ('shrine', 'Watch Shrine'), ('chest', 'Garrison Chest')]),
 'coil_isle':      dict(R=150, amp=9,  pois=[('bones', 'Coil Bones'), ('shrine', 'Serpent Shrine'), ('chest', 'Drowned Offering')]),
 'beached_wreck':  dict(R=140, amp=8,  pois=[('wreck_camp', 'Castaway Camp'), ('chest', 'Salvage Chest'), ('lore', 'Captain\'s Last Log')]),
 'frozen_wreck':   dict(R=130, amp=8,  pois=[('wreck_camp', 'Frozen Camp'), ('ice_cave', 'Bergcleft Cave'), ('chest', 'Frostbitten Chest')]),
 'aurora_arch':    dict(R=120, amp=8,  pois=[('frost_shrine', 'Aurora Shrine'), ('ice_cave', 'Skyglass Hollow'), ('lore', 'Starwatcher\'s Stone')]),
 'ember_wreck':    dict(R=120, amp=7,  pois=[('wreck_camp', 'Cinder Camp'), ('lava_vent', 'Ember Vent'), ('chest', 'Scorched Chest')]),
 'hot_spring':     dict(R=120, amp=7,  pois=[('hot_pool', 'Upper Spring'), ('hot_pool', 'Lower Spring'), ('shrine', 'Bathers\' Shrine'), ('chest', 'Bather\'s Bundle')]),
 'obsidian_arch':  dict(R=120, amp=8,  pois=[('obsidian_shrine', 'Glassfire Shrine'), ('lava_vent', 'Arch Vent'), ('lore', 'Obsidian Mirror')]),
}
PAD = {'watchtower': 8, 'lighthouse': 9, 'keep_ruin': 12, 'hut_ruin': 7, 'shrine': 5, 'crystal_shrine': 6, 'frost_shrine': 6, 'obsidian_shrine': 6, 'crystal_grove': 9,
       'ice_cave': 9, 'lava_vent': 7, 'hot_pool': 8, 'wreck_camp': 10, 'bones': 11, 'chest': 3, 'lore': 3}
_cache = {}
def region_meshes(reg):
    if reg in _cache: return _cache[reg]
    d, pre = RDIR[reg]; base, fp = [], []
    for f in sorted(glob.glob(os.path.join(GA, d, pre + '*.glb'))):
        b = os.path.basename(f)[:-4]
        if any(s in b for s in SKIPFP): continue
        m = trimesh.load(f, force='mesh')
        (base if ('_tile_' in b or b == 'arch_islands') else fp).append((b, m))
    bv = np.concatenate([m.vertices for _, m in base]); fv = np.concatenate([m.vertices for _, m in fp]) if fp else np.zeros((0, 3))
    _cache[reg] = (bv, fv, base); return _cache[reg]
def smooth01(a, b, x): t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra
def walk_graph(H, okc, sj, sii, ny, nx, hard=None):
    okc = okc.copy(); okc[sj, sii] = True; nid = -np.ones(okc.shape, int); nid[okc] = np.arange(okc.sum()); rr_, cc_, ww_ = [], [], []
    for dj, di in [(0, 1), (1, 0), (1, 1), (1, -1), (0, 2), (2, 0), (1, 2), (2, 1), (2, -1), (1, -2)]:
        if di < 0: A_ = nid[:ny - dj, -di:]; B_ = nid[dj:, :nx + di]; HA = H[:ny - dj, -di:]; HB = H[dj:, :nx + di]
        else: A_ = nid[:ny - dj, :nx - di]; B_ = nid[dj:, di:]; HA = H[:ny - dj, :nx - di]; HB = H[dj:, di:]
        m_ = (A_ >= 0) & (B_ >= 0); L_ = math.hypot(dj, di) * STEP; gr = np.abs(HA - HB)[m_] / L_
        w_ = L_ * (1 + 30 * (gr / 0.5) ** 4) + np.where(gr > 0.75, 5000, 0)
        if hard is not None: keep_ = gr <= hard; w_ = w_[keep_]; a_ = A_[m_][keep_]; b_ = B_[m_][keep_]
        else: a_ = A_[m_]; b_ = B_[m_]
        rr_ += [a_, b_]; cc_ += [b_, a_]; ww_ += [w_, w_]
    G = coo_matrix((np.concatenate(ww_), (np.concatenate(rr_), np.concatenate(cc_))), shape=(okc.sum(), okc.sum())).tocsr()
    return G, okc, nid
def build(k):
    Ld = L[k]; cfg = ISL[k]; reg = Ld['region']; pre = RDIR[reg][1]; P = PAL[GROUND[reg]]; rng = np.random.default_rng(zlib.crc32(k.encode()))
    OUT = os.path.join(ROOT5, 'meshes', reg); os.makedirs(OUT, exist_ok=True); _g['OUT'] = OUT
    sh = np.array([Ld['shore'][0], Ld['shore'][2]]); inl = np.array(Ld['inland']) / np.linalg.norm(Ld['inland']); R = cfg['R']
    cen = sh + inl * R * 0.7
    xs = np.arange(cen[0] - R, cen[0] + R + 1e-3, STEP); zs = np.arange(cen[1] - R, cen[1] + R + 1e-3, STEP); X, Z = np.meshgrid(xs, zs); ny, nx = X.shape
    bv, fv, _ = region_meshes(reg)
    sel = (np.abs(bv[:, 0] - cen[0]) < R + 30) & (np.abs(bv[:, 2] - cen[1]) < R + 30); v = bv[sel]
    # top surface: keep the highest vertex per 0.5 m bin (caves/overhangs would otherwise fold the patch)
    key = np.round(v[:, [0, 2]] * 2).astype(np.int64); o = np.lexsort((-v[:, 1], key[:, 1], key[:, 0])); kk = key[o]; first = np.r_[True, np.any(kk[1:] != kk[:-1], 1)]; v = v[o][first]
    base = LinearNDInterpolator(v[:, [0, 2]], v[:, 1], fill_value=-10.0)(X, Z)
    land = base > 0.2
    si = (int(round((sh[1] + inl[1] * 8 - zs[0]) / STEP)), int(round((sh[0] + inl[0] * 8 - xs[0]) / STEP)))
    lab, nl = ndimage.label(land); comp = lab == lab[si] if lab[si] else land
    BR = np.zeros_like(comp); bridges = []
    if comp.sum() * STEP ** 2 < 9000 and nl > 1:   # landing sits on a small islet / shelf: join it to the nearest big land with a causeway
        sizes = ndimage.sum(np.ones_like(lab), lab, range(1, nl + 1)); ce = np.argwhere(comp & ~ndimage.binary_erosion(comp)); tc = cKDTree(ce); best = None
        for li in range(1, nl + 1):
            if li == lab[si] or sizes[li - 1] * STEP ** 2 < 9000: continue
            oe = np.argwhere((lab == li) & ~ndimage.binary_erosion(lab == li)); dd, ii = tc.query(oe); dh = np.abs(base[oe[:, 0], oe[:, 1]] - base[ce[ii, 0], ce[ii, 1]])
            sc = dd * STEP + dh * 3; kk = int(np.argmin(sc))
            if dd[kk] * STEP <= 70 and (best is None or sc[kk] < best[0]): best = (sc[kk], tuple(ce[ii[kk]]), tuple(oe[kk]), li)
        if best:
            _, a_, b_, li = best; n_ = int(max(abs(a_[0] - b_[0]), abs(a_[1] - b_[1]))) * 2 + 2
            for t in np.linspace(0, 1, n_):
                jj, ii_ = a_[0] + (b_[0] - a_[0]) * t, a_[1] + (b_[1] - a_[1]) * t; BR[int(round(jj)), int(round(ii_))] = True
            BR = ndimage.binary_dilation(BR, iterations=1) & ~land
            ya, yb = base[a_] + 0.3, base[b_] + 0.3
            bridges.append({'a': [float(X[a_]), float(ya), float(Z[a_])], 'b': [float(X[b_]), float(yb), float(Z[b_])], 'len_m': round(float(np.hypot(X[a_] - X[b_], Z[a_] - Z[b_])), 1)})
            comp = comp | (lab == li)
    walk = comp | BR
    cd = ndimage.distance_transform_edt(comp) * STEP
    # existing props: footprint (cut out of the patch) and keep-out falloff
    fsel = (np.abs(fv[:, 0] - cen[0]) < R + 20) & (np.abs(fv[:, 2] - cen[1]) < R + 20) if len(fv) else np.zeros(0, bool)
    FP = np.zeros_like(comp)
    if fsel.any():
        q = fv[fsel]; ii = np.round((q[:, 0] - xs[0]) / STEP).astype(int); jj = np.round((q[:, 2] - zs[0]) / STEP).astype(int); ok = (ii >= 0) & (ii < nx) & (jj >= 0) & (jj < ny)
        hb = base[jj[ok], ii[ok]]; up = q[ok, 1] > hb - 3   # only parts standing on this land
        FP[jj[ok][up], ii[ok][up]] = True; FP = ndimage.binary_closing(ndimage.binary_dilation(FP, iterations=1), iterations=2)
    fpd = ndimage.distance_transform_edt(~FP) * STEP if FP.any() else np.full(FP.shape, 999.0)
    dsh = np.hypot(X - sh[0], Z - sh[1])
    # hills: smooth random field + ridges, rising inland
    n1 = ndimage.gaussian_filter(rng.standard_normal(X.shape), 26 / STEP); n1 /= n1.std() + 1e-9
    n2 = ndimage.gaussian_filter(rng.standard_normal(X.shape), 7 / STEP); n2 /= n2.std() + 1e-9
    ridge = 1 - np.abs(np.tanh(n1 * 0.9))
    A = cfg['amp']; bump = A * (0.45 * np.clip(n1 * 0.6 + 0.6, 0, 1.6) + 0.35 * ridge * smooth01(0, 1, n1 + 0.5) + 0.05 * n2) + np.clip(cd, 0, 90) / 90 * A * 0.7
    edge = np.minimum(np.minimum(X - xs[0], xs[-1] - X), np.minimum(Z - zs[0], zs[-1] - Z))
    mask = smooth01(4, 45, edge) * smooth01(3, 34, cd) * smooth01(4, 30, fpd) * smooth01(14, 75, dsh)
    H = base + np.maximum(bump, 0) * mask
    def slope_of(h): gz, gx = np.gradient(h, STEP); return np.hypot(gx, gz)
    for _ in range(25):   # soften anything steeper than ~32 deg that the hills added (cliffs of the original terrain stay)
        st = (slope_of(H) > 0.62) & (mask > 0.05) & (slope_of(base) < 0.6)
        if not st.any(): break
        Hb = ndimage.gaussian_filter(H, 1.5); H = np.where(ndimage.binary_dilation(st), Hb, H); H = np.maximum(H, base)
    # POI sites
    def slope_of(h): gz, gx = np.gradient(h, STEP); return np.hypot(gx, gz)
    pois = []; taken = []
    edge = np.minimum(np.minimum(X - xs[0], xs[-1] - X), np.minimum(Z - zs[0], zs[-1] - Z))
    Gr, okr, nidr = walk_graph(H, walk & ~(FP & (dsh > 12)), si[0], si[1], ny, nx, hard=0.7)   # walkable (<=35 deg steps) from the pier head
    dr = dijkstra(Gr, indices=nidr[si], limit=np.inf); reach = np.zeros_like(comp); reach[okr] = np.isfinite(dr)
    reach = ndimage.binary_erosion(reach, iterations=1) | (dsh < 6)
    cand = reach & comp & (cd > 12) & (fpd > 18) & (dsh > 30) & (dsh < R * 1.35) & (edge > 26)
    for t_i, (typ, name) in enumerate(cfg['pois']):
        r = PAD[typ]; c2 = cand & (cd > r + 4) & (fpd > r + 10)
        for tk in taken: c2 &= np.hypot(X - tk[0], Z - tk[1]) > max(34, r + tk[2] + 14)
        if not c2.any():
            c2 = reach & comp & (cd > r + 2) & (fpd > r + 4) & (dsh > 20) & (edge > r + 8)
            for tk in taken: c2 &= np.hypot(X - tk[0], Z - tk[1]) > r + tk[2] + 6
        if not c2.any(): print('  no site for', typ); continue
        if t_i == 0 and typ not in ('ice_cave', 'hot_pool', 'wreck_camp', 'bones'): sc = H + rng.uniform(0, 0.5, H.shape)
        elif typ in ('wreck_camp', 'hot_pool', 'bones'): sc = -np.abs(cd - (r + 10)) * 0.5 - dsh * 0.05 + (np.min([np.hypot(X - tk[0], Z - tk[1]) for tk in taken], 0) * 0.3 if taken else 0)
        else: sc = (np.min([np.hypot(X - tk[0], Z - tk[1]) for tk in taken], 0) if taken else dsh) + rng.uniform(0, 4, H.shape) - 0.25 * dsh * (dsh > R)
        sc = sc - 1.5 * (ndimage.maximum_filter(H, size=int(24 / STEP)) - H)   # no pits / ravines
        sc = np.where(c2, sc, -1e9); j, i = np.unravel_index(np.argmax(sc), sc.shape)
        taken.append((X[j, i], Z[j, i], r)); pois.append({'type': typ, 'name': name, 'ij': (j, i), 'r': r})
    # flatten pads
    for p in pois:
        j, i = p['ij']; r = p['r']; dd = np.hypot(X - X[j, i], Z - Z[j, i]); inner = dd < r
        h0 = float(np.median(H[inner])); w = 1 - smooth01(r, r + 7, dd); H = H * (1 - w) + h0 * w; p['pos'] = [float(X[j, i]), h0, float(Z[j, i])]
    # paths: pier head -> each POI (least-cost over slope), widened + smoothed so they stay walkable
    sj, sii = si; path = np.zeros_like(comp)
    if bridges:   # bridge deck heights into H so the router sees the crossing
        b0 = bridges[0]; ab = np.array([b0['b'][0] - b0['a'][0], b0['b'][2] - b0['a'][2]]); t_ = np.clip(((X - b0['a'][0]) * ab[0] + (Z - b0['a'][2]) * ab[1]) / (ab @ ab), 0, 1)
        H = np.where(BR, b0['a'][1] + (b0['b'][1] - b0['a'][1]) * t_, H)
    G, okc, nid = walk_graph(H, walk & ~(FP & (dsh > 12)), sj, sii, ny, nx)
    dist_, pred = dijkstra(G, indices=nid[sj, sii], return_predecessors=True)
    cells_ = np.argwhere(okc)
    for p in pois:
        t = nid[p['ij']]
        if t < 0 or not np.isfinite(dist_[t]): continue
        route = []
        while t >= 0 and t != nid[sj, sii]: route.append(tuple(cells_[t])); t = pred[t]
        route = route[::-1]
        for (a, b) in route: path[a, b] = True
        p['route'] = route
    # bench fill: the path is a level shelf at its own height (fills only; the original slope stays above it on the uphill side)
    pband, pidx = ndimage.distance_transform_edt(~path, return_indices=True); pband = pband * STEP
    Hp = ndimage.gaussian_filter(H, 1.0)[pidx[0], pidx[1]]
    band = (pband < 3.2) & walk & ~BR & (cd > 4)
    H = np.where(band, np.clip(H * smooth01(1.6, 3.2, pband) + Hp * (1 - smooth01(1.6, 3.2, pband)), base, base + 2.5), H)
    H = np.where(dsh < 14, base, H * smooth01(14, 22, dsh) + base * (1 - smooth01(14, 22, dsh)))   # pier head stays as built
    sl = slope_of(H)
    grade = []
    for p in pois:
        r_ = p.get('route', [])
        for (a0, b0), (a1, b1) in zip(r_[:-1], r_[1:]):
            if BR[a0, b0] or BR[a1, b1]: continue
            grade.append(float(np.degrees(np.arctan(abs(H[a1, b1] - H[a0, b0]) / (math.hypot(a1 - a0, b1 - b0) * STEP)))))
    STATS[k] = {'reach_m2': int(reach.sum() * STEP ** 2), 'path_max_deg': round(max(grade) if grade else 0, 1), 'path_p95_deg': round(float(np.percentile(grade, 95)) if grade else 0, 1)}
    # ---------------- terrain mesh
    keep = comp & ~ndimage.binary_dilation(FP, iterations=0 if not FP.any() else 1) & (base > 0.15)
    keep &= ~((dsh < 6))   # leave the pier-head boards alone
    keep &= ~((slope_of(base) > 0.85) & (H - base < 0.5) & (pband > 3))   # original sea cliffs stay as built (their own colours / shape)
    keep = ndimage.binary_opening(keep, iterations=1) | (keep & (pband < 3))
    idx = -np.ones(keep.shape, int); idx[keep] = np.arange(keep.sum())
    rim = keep & ~ndimage.binary_erosion(keep)   # patch rim tucks 0.25 m under the original ground: no visible step / seam
    V = np.stack([X[keep], np.where(rim, base - 0.25, H + 0.08)[keep], Z[keep]], 1)
    q = keep[:-1, :-1] & keep[1:, :-1] & keep[:-1, 1:] & keep[1:, 1:]
    a = idx[:-1, :-1][q]; b = idx[:-1, 1:][q]; c_ = idx[1:, :-1][q]; d = idx[1:, 1:][q]
    Fc = np.concatenate([np.stack([a, c_, b], 1), np.stack([b, c_, d], 1)])
    nn = n2[keep]; s_ = sl[keep]; hh = (H - base)[keep]; cdk = cd[keep]; pb = pband[keep]
    col = np.tile(P['g1'], (len(V), 1)); col[nn > 0.5] = P['g2']; col[nn < (-1.5 if reg == 'ash' else -0.8)] = P['g3']
    col[cdk < 6] = P['sand']; col[s_ > 0.65] = P['rock']; col[(s_ > 0.65) & (nn > 0.3)] = P['rock2']; col[s_ > 1.0] = P['cliff']
    col[pb < 2.0] = P['path']
    for p in pois:
        dd = np.hypot(V[:, 0] - p['pos'][0], V[:, 2] - p['pos'][2]); col[dd < p['r'] * 0.8] = P['path']
    tm = trimesh.Trimesh(V, Fc, process=False)
    budget = 36000
    v2, f2 = fast_simplification.simplify(V.astype(np.float32), Fc.astype(np.int64), target_reduction=max(0.0, 1 - budget / max(1, len(Fc))))
    terr = trimesh.Trimesh(v2, f2, process=False); terr.visual = trimesh.visual.ColorVisuals(terr, vertex_colors=col[cKDTree(V).query(v2)[1]])
    def Hat(x, z):
        i = (x - xs[0]) / STEP; j = (z - zs[0]) / STEP; return float(ndimage.map_coordinates(H, [[j], [i]], order=1)[0]) + 0.08
    solid, glow, colp = [terr], [], []
    # ---------------- POIs
    pm_ = P
    for p in pois:
        x, _, z = p['pos']; y = Hat(x, z); yaw = math.atan2(sh[0] - x, sh[1] - z); s, g, c = poi(p['type'], (x, y, z), yaw, pm_, reg, rng); solid += s; glow += g; colp += c; p['pos'][1] = y
    # ---------------- scatter (rocks, vegetation / crystals / ice / basalt)
    ok = comp & ~FP & (pband > 3.5) & (cd > 3) & (dsh > 16)
    for p in pois: ok &= np.hypot(X - p['pos'][0], Z - p['pos'][2]) > p['r'] + 3
    cells = np.argwhere(ok); rng.shuffle(cells)
    nrock = int(min(70, len(cells) * 0.004 + 18)); nveg = int(min(110, len(cells) * 0.008 + 20))
    for (j, i) in cells[:nrock]:
        r = float(rng.uniform(0.6, 2.6) if sl[j, i] < 0.5 else rng.uniform(1.2, 3.6)); x, z = X[j, i] + rng.uniform(-1, 1), Z[j, i] + rng.uniform(-1, 1)
        rk = rock((x, Hat(x, z) + r * 0.2, z), r, int(rng.integers(1e6)), 0.6, P['rock'] if rng.random() < 0.6 else P['rock2']); solid.append(rk)
        if r > 1.4: colp.append(rk)
    for (j, i) in cells[nrock:nrock + nveg]:
        x, z = X[j, i] + rng.uniform(-1, 1), Z[j, i] + rng.uniform(-1, 1); y = Hat(x, z)
        s, g, c = veg(GROUND[reg], (x, y, z), rng); solid += s; glow += g; colp += c
    for b0 in bridges:
        s_, c_ = bridge(b0, GROUND[reg]); solid += s_; colp += c_
    name = f'{pre}isl_{k}'
    allm = merge(solid); save(name, allm)
    if glow: save(name + '_glow', merge(glow), lod=False)
    cv, cf = fast_simplification.simplify(np.asarray(terr.vertices, np.float32), np.asarray(terr.faces, np.int64), target_reduction=0.6)
    colm = merge([trimesh.Trimesh(cv, cf, process=False)] + [trimesh.Trimesh(c.vertices, c.faces, process=False) for c in colp])
    colm.export(os.path.join(OUT, name + '_col.glb')); STATS[name]['col_tris'] = int(len(colm.faces))
    STATS[name]['terrain_tris'] = int(len(f2))
    lights = [l for p in pois for l in p.get('lights', [])]
    return {'id': k, 'name': Ld['name'], 'region': reg, 'ground': GROUND[reg], 'files': {'mesh': name, 'lod1': name + '_lod1', 'glow': name + '_glow' if glow else None, 'col': name + '_col'},
            'pier_head': Ld['shore'], 'window': [float(xs[0]), float(zs[0]), float(xs[-1]), float(zs[-1])],
            'pois': [{'type': p['type'], 'name': p['name'], 'pos': [round(c, 2) for c in p['pos']], 'radius': p['r']} for p in pois],
            'lights': lights, 'bridges': bridges, 'path': {'max_deg': STATS[k]['path_max_deg'], 'p95_deg': STATS[k]['path_p95_deg']},
            'cams': {'inland': [Ld['shore'][0] - inl[0] * 6, Ld['shore'][1] + 4.5, Ld['shore'][2] - inl[1] * 6], 'inland_look': [sh[0] + inl[0] * 40, Hat(*(sh + inl * 40)) + 1.5, sh[1] + inl[1] * 40],
                     'over': [sh[0] - inl[0] * 60 + inl[1] * 50, max(H.max(), 0) + 55, sh[1] - inl[1] * 60 - inl[0] * 50], 'over_look': [cen[0], float(np.median(H[comp])) if comp.any() else 0, cen[1]]}}
# ---------------------------------------------------------------- kits
STONE2 = C(138, 132, 122); MOSS = C(96, 120, 70); EMB = C(255, 120, 40); LAMP = C(255, 196, 110); ICE1 = C(176, 214, 236); ICE2 = C(120, 170, 206); OBS = C(20, 18, 26); TEAL = C(90, 200, 200); GOLD = C(220, 180, 70); CRYS = C(170, 230, 245); CRYP = C(236, 170, 210)
def R_(pos, yaw, m): return T(m, pos, (0, yaw, 0))
def _ring(n, r, f):
    return [f(i, math.cos(2 * math.pi * i / n) * r, math.sin(2 * math.pi * i / n) * r) for i in range(n)]
def bridge(b0, ground):
    a = np.array(b0['a']); b = np.array(b0['b']); d = b - a; Lh = math.hypot(d[0], d[2]); yaw = math.atan2(d[0], d[2]); n = max(2, int(Lh / 2.0)); S_, C_ = [], []
    deck = {'temperate': WOOD, 'saltglass': WOOD, 'frost': ICE1, 'ash': C(44, 42, 44)}[ground]; post = {'temperate': DKW, 'saltglass': DKW, 'frost': ICE2, 'ash': OBS}[ground]
    for i in range(n):
        t0, t1 = i / n, (i + 1) / n; p0 = a + d * t0; p1 = a + d * t1; mid = (p0 + p1) / 2; pitch = math.atan2(p1[1] - p0[1], Lh / n)
        sl_ = T(box((3.0, 0.3, Lh / n + 0.05), deck if i % 2 else (deck * np.array([0.9, 0.9, 0.9, 1])).astype(np.uint8)), (0, 0, 0), (-pitch, 0, 0)); sl_ = T(sl_, mid, (0, yaw, 0)); S_.append(sl_); C_.append(sl_)
        for sd in (-1.4, 1.4):
            off = np.array([math.cos(yaw) * sd, 0, -math.sin(yaw) * sd])
            if i % 2 == 0: S_.append(line(p0 + off + (0, -3.0, 0), p0 + off + (0, 1.1, 0), 0.14, post))
            rl = line(p0 + off + (0, 1.0, 0), p1 + off + (0, 1.0, 0), 0.07, post); S_.append(rl); C_.append(T(box((0.2, 1.0, Lh / n), post, (0, 0, 0), (-pitch, 0, 0)), mid + off + (0, 0.6, 0), (0, yaw, 0)))
    return S_, C_
def chest(p, yaw):
    s = [box((1.2, 0.7, 0.8), WOOD, (0, 0.35, 0)), box((1.24, 0.12, 0.84), BRASS, (0, 0.72, 0)), box((0.2, 0.25, 0.06), BRASS, (0, 0.5, 0.43)), box((1.25, 0.08, 0.1), IRON, (0, 0.3, 0.38))]
    return [R_(p, yaw, merge(s))], [R_(p, yaw, ball(0.12, LAMP, (0, 0.85, 0)))], [R_(p, yaw, box((1.2, 0.8, 0.8), WOOD, (0, 0.4, 0)))]
def lore(p, yaw, col):
    s = [T(paint(trimesh.creation.box((1.3, 2.6, 0.45)), col), (0, 1.2, 0), (0.06, 0, 0.04)), box((1.8, 0.3, 1.0), STONE2, (0, 0.1, 0))]
    return [R_(p, yaw, merge(s))], [R_(p, yaw, box((0.8, 1.2, 0.05), TEAL, (0, 1.4, 0.25)))], [R_(p, yaw, box((1.4, 2.6, 0.6), col, (0, 1.3, 0)))]
def poi(typ, p, yaw, P, reg, rng):
    S_, G_, C_ = [], [], []
    x, y, z = p
    if typ == 'chest': return chest(p, yaw)
    if typ == 'lore': return lore(p, yaw, P['rock'] if reg != 'frost' else C(110, 120, 134))
    if typ in ('watchtower', 'lighthouse'):
        r0 = 3.6 if typ == 'lighthouse' else 3.0; h = 15 if typ == 'lighthouse' else 11
        for k in range(10):   # broken ring of stone courses, taller on the lee side
            a0 = k / 10 * 2 * math.pi; hh = h * (0.35 + 0.65 * abs(math.sin(a0 * 0.5 + 0.6))); seg = cyl(r0, hh, STONE2, (0, hh / 2, 0), sec=10)
            for t in range(int(math.ceil(hh / 1.0))):
                bx = box((2.45, 1.02, 1.0), STONE2 if (t + k) % 2 else STONE, (math.cos(a0) * r0, 0.5 + t * 1.0, math.sin(a0) * r0), (0, -a0 + math.pi / 2, 0)); S_.append(R_(p, yaw, bx)); C_.append(R_(p, yaw, bx))
        S_.append(R_(p, yaw, cyl(r0 + 1.2, 0.6, STONE, (0, 0.3, 0), sec=12)))
        for k in range(7): S_.append(R_(p, yaw, rock((rng.uniform(-7, 7), 0.4, rng.uniform(-7, 7)), rng.uniform(0.5, 1.1), int(rng.integers(1e6)), 0.6, STONE2)))
        if typ == 'lighthouse':
            S_.append(R_(p, yaw, box((2.2, 0.3, 2.2), IRON, (0, 0.8, 0)))); G_.append(R_(p, yaw, ball(0.6, LAMP, (0, 1.4, 0)))); S_.append(R_(p, yaw, line((0, 0.9, 0), (0, 2.2, 0), 0.15, IRON)))
            S_.append(R_(p, yaw, merge([box((1.2, 0.2, 4), WOOD, (5.5 + i * 0.3, 0.12, i * 1.3 - 2)) for i in range(3)])))   # fallen lantern-room beams
        else: G_.append(R_(p, yaw, ball(0.35, EMB, (1.0, 0.9, 1.0))))
        return S_, G_, C_
    if typ == 'keep_ruin':
        for s in range(4):
            a0 = s * math.pi / 2; L_ = 18
            for k in range(7):
                if rng.random() < 0.25: continue
                hh = rng.uniform(1.5, 5.5); bx = box((L_ / 7 - 0.2, hh, 1.6), STONE2, (math.cos(a0) * 9 + math.sin(a0) * (k - 3) * L_ / 7, hh / 2, math.sin(a0) * 9 - math.cos(a0) * (k - 3) * L_ / 7), (0, -a0, 0))
                S_.append(R_(p, yaw, bx)); C_.append(R_(p, yaw, bx))
        for c in [(-9, -9), (9, -9), (9, 9), (-9, 9)]:
            t = cyl(2.0, rng.uniform(5, 8), STONE, (c[0], 3, c[1]), sec=8); S_.append(R_(p, yaw, t)); C_.append(R_(p, yaw, t))
        S_.append(R_(p, yaw, box((5, 0.2, 5), MOSS, (0, 0.1, 0)))); G_.append(R_(p, yaw, ball(0.4, EMB, (0, 0.6, 0)))); S_.append(R_(p, yaw, cyl(0.8, 0.5, STONE, (0, 0.25, 0), sec=8)))
        return S_, G_, C_
    if typ == 'hut_ruin':
        for (sx, sz, w, d) in [(0, -2.5, 6, 0.5), (-3, 0, 0.5, 5), (3, 0.5, 0.5, 4)]:
            bx = box((w, 2.2, d), STONE2, (sx, 1.1, sz)); S_.append(R_(p, yaw, bx)); C_.append(R_(p, yaw, bx))
        S_.append(R_(p, yaw, T(box((6.6, 0.25, 3.5), DKW), (0, 2.3, -1.2), (0.4, 0, 0)))); S_.append(R_(p, yaw, box((1.0, 1.2, 1.0), STONE, (-2, 0.6, -1.6))))
        G_.append(R_(p, yaw, ball(0.25, LAMP, (-2, 1.4, -1.6))))
        return S_, G_, C_
    if typ in ('shrine', 'frost_shrine', 'obsidian_shrine', 'crystal_shrine'):
        stc = {'shrine': STONE2, 'frost_shrine': ICE1, 'obsidian_shrine': OBS, 'crystal_shrine': C(200, 196, 206)}[typ]
        S_.append(R_(p, yaw, cyl(4.0, 0.5, stc, (0, 0.25, 0), sec=12))); S_.append(R_(p, yaw, cyl(3.2, 0.4, stc, (0, 0.7, 0), sec=12)))
        for i, cx, cz in _ring(4, 2.6, lambda i, a, b: (i, a, b)):
            pl = cyl(0.35, 3.6, stc, (cx, 2.6, cz), sec=6); S_.append(R_(p, yaw, pl)); C_.append(R_(p, yaw, pl))
        S_.append(R_(p, yaw, cyl(3.4, 0.4, stc, (0, 4.6, 0), sec=4, r2=1.6)))
        S_.append(R_(p, yaw, box((1.2, 1.0, 0.8), stc, (0, 1.4, 0))))
        gc = {'shrine': LAMP, 'frost_shrine': CRYS, 'obsidian_shrine': EMB, 'crystal_shrine': CRYP}[typ]
        G_.append(R_(p, yaw, T(paint(trimesh.creation.icosphere(0, 0.55), gc), (0, 2.3, 0), scale=(1, 1.6, 1))))
        for i, cx, cz in _ring(6, 3.8, lambda i, a, b: (i, a, b)): G_.append(R_(p, yaw, ball(0.12, gc, (cx, 0.62, cz))))
        return S_, G_, C_
    if typ == 'crystal_grove':
        for k in range(14):
            a0 = rng.uniform(0, 2 * math.pi); rr = rng.uniform(1, 8); h = rng.uniform(1.5, 5.5)
            cr = T(paint(trimesh.creation.cone(rng.uniform(0.35, 0.9), h, sections=5), CRYS if k % 2 else CRYP), (math.cos(a0) * rr, 0, math.sin(a0) * rr), (-math.pi / 2 + rng.uniform(-0.3, 0.3), 0, rng.uniform(-0.3, 0.3)))
            G_.append(R_(p, yaw, cr))
        return S_, G_, C_
    if typ == 'ice_cave':   # walk-in hollow under an ice dome (open front facing the pier)
        for k in range(9):
            a0 = math.pi * 0.25 + k / 8 * math.pi * 1.5
            ch = T(paint(trimesh.creation.icosphere(1, 3.0), ICE1 if k % 2 else ICE2), (math.cos(a0) * 6.5, 2.6, math.sin(a0) * 6.5), scale=(1.1, 1.6, 0.9)); S_.append(R_(p, yaw + math.pi / 2, ch)); C_.append(R_(p, yaw + math.pi / 2, ch))
        roof = T(paint(trimesh.creation.icosphere(1, 6.8), ICE2), (0, 7.2, 0), scale=(1, 0.35, 1)); S_.append(R_(p, yaw + math.pi / 2, roof)); C_.append(R_(p, yaw + math.pi / 2, roof))
        for k in range(9):
            ic = T(paint(trimesh.creation.cone(0.3, rng.uniform(1, 2.4), sections=5), CRYS), (rng.uniform(-4, 4), 5.6, rng.uniform(-4, 4)), (math.pi, 0, 0)); G_.append(R_(p, yaw, ic))
        G_.append(R_(p, yaw, ball(0.5, CRYS, (0, 0.6, 0))))
        return S_, G_, C_
    if typ == 'lava_vent':
        S_.append(R_(p, yaw, cyl(5.5, 2.2, C(34, 30, 32), (0, 1.1, 0), sec=10, r2=2.4)));
        for k in range(8): S_.append(R_(p, yaw, rock((math.cos(k) * 6.5, 0.4, math.sin(k) * 6.5), rng.uniform(0.7, 1.4), int(rng.integers(1e6)), 0.5, OBS)))
        G_.append(R_(p, yaw, cyl(2.2, 0.3, EMB, (0, 2.1, 0), sec=10)))
        for k in range(5):
            a0 = k * 1.25; G_.append(R_(p, yaw, line((math.cos(a0) * 2.4, 2.0, math.sin(a0) * 2.4), (math.cos(a0) * 5.6, 0.15, math.sin(a0) * 5.6), 0.22, EMB, 4)))
        C_.append(R_(p, yaw, cyl(5.5, 2.2, OBS, (0, 1.1, 0), sec=10, r2=2.4)))
        return S_, G_, C_
    if typ == 'hot_pool':
        S_.append(R_(p, yaw, cyl(6.2, 0.5, C(120, 110, 96) if reg != 'ash' else C(60, 56, 54), (0, 0.15, 0), sec=14)));
        for k in range(12): S_.append(R_(p, yaw, rock((math.cos(k / 12 * 6.283) * 6.0, 0.45, math.sin(k / 12 * 6.283) * 6.0), rng.uniform(0.7, 1.2), int(rng.integers(1e6)), 0.55, C(110, 100, 92) if reg != 'ash' else C(54, 50, 50))))
        G_.append(R_(p, yaw, cyl(5.3, 0.1, C(60, 170, 180), (0, 0.45, 0), sec=14)))
        for k in range(3): G_.append(R_(p, yaw, T(paint(trimesh.creation.icosphere(1, 1.6), C(200, 210, 214)), (rng.uniform(-2.5, 2.5), 2.2 + k * 1.4, rng.uniform(-2.5, 2.5)), scale=(1.4, 0.6, 1.4))))
        S_.append(R_(p, yaw, box((1.4, 0.2, 3.0), WOOD, (6.5, 0.4, 0))))
        return S_, G_, C_
    if typ == 'wreck_camp':
        hull = T(paint(trimesh.creation.icosphere(1, 1.0), DKW), (0, 1.4, -5), scale=(3.2, 2.2, 8.0), rot=(0, 0, 0.5)); S_.append(R_(p, yaw, hull)); C_.append(R_(p, yaw, hull))
        for k in range(6): S_.append(R_(p, yaw, line((-2.6 + k * 1.0, 0.0, -9 + k * 1.6), (-3.6 + k * 1.0, 4.2, -7 + k * 1.6), 0.18, WOOD)))
        tent = T(paint(trimesh.creation.cone(2.4, 2.6, sections=4), C(196, 180, 150) if reg != 'ash' else C(120, 96, 80)), (4, 0, 2), (-math.pi / 2, 0, 0)); S_.append(R_(p, yaw, tent)); C_.append(R_(p, yaw, tent))
        for k in range(7): S_.append(R_(p, yaw, rock((math.cos(k) * 1.2, 0.15, math.sin(k) * 1.2 + 3), 0.3, k, 0.6, STONE2)))
        G_.append(R_(p, yaw, T(paint(trimesh.creation.cone(0.6, 1.0, sections=6), EMB), (0, 0, 3), (-math.pi / 2, 0, 0))))
        for k in range(3): S_.append(R_(p, yaw, box((0.9, 0.9, 0.9), WOOD, (-3 + k * 1.1, 0.45, 4.5), (0, k * 0.4, 0))))
        S_.append(R_(p, yaw, line((2.0, 0.0, 6.0), (2.0, 3.2, 6.0), 0.1, WOOD))); G_.append(R_(p, yaw, ball(0.22, LAMP, (2.0, 3.3, 6.0))))
        return S_, G_, C_
    if typ == 'bones':   # Brinecrown-coil serpent ribs half buried
        BONE = C(222, 214, 190)
        for k in range(9):
            zz = -12 + k * 3; rr = 4.5 - abs(k - 4) * 0.35
            for sgn in (-1, 1):
                rb = line((sgn * 0.6, 0.2, zz), (sgn * rr, rr * 1.1, zz + 0.8), 0.35, BONE, 6); S_.append(R_(p, yaw, rb))
            S_.append(R_(p, yaw, ball(0.8, BONE, (0, 0.4, zz))))
        sk = T(paint(trimesh.creation.icosphere(1, 1.0), BONE), (0, 1.2, 15), scale=(2.2, 1.4, 3.4)); S_.append(R_(p, yaw, sk)); C_.append(R_(p, yaw, sk))
        G_.append(R_(p, yaw, ball(0.3, TEAL, (0.9, 1.8, 16.5)))); G_.append(R_(p, yaw, ball(0.3, TEAL, (-0.9, 1.8, 16.5))))
        return S_, G_, C_
    raise ValueError(typ)
def veg(ground, p, rng):
    x, y, z = p; S_, G_, C_ = [], [], []
    if ground == 'temperate':
        if rng.random() < 0.55:
            h = rng.uniform(5, 9); S_.append(cyl(0.22, h * 0.35, DKW, (x, y + h * 0.17, z), sec=5))
            for t in range(3): S_.append(T(paint(trimesh.creation.cone(h * (0.28 - t * 0.06), h * 0.42, sections=7), C(52, 96, 52) if t % 2 else C(64, 110, 58)), (x, y + h * (0.25 + t * 0.2), z), (-math.pi / 2, 0, 0)))
            C_.append(cyl(0.3, 3, DKW, (x, y + 1.5, z), sec=5))
        else: S_.append(ball(rng.uniform(0.8, 1.6), C(78, 122, 60), (x, y + 0.4, z), 1, (1, 0.7, 1), 0.2, int(rng.integers(1e6))))
    elif ground == 'saltglass':
        if rng.random() < 0.5:
            for k in range(3): G_.append(T(paint(trimesh.creation.cone(rng.uniform(0.2, 0.45), rng.uniform(0.8, 2.4), sections=5), CRYS if rng.random() < 0.5 else CRYP), (x + rng.uniform(-0.8, 0.8), y - 0.1, z + rng.uniform(-0.8, 0.8)), (-math.pi / 2 + rng.uniform(-0.4, 0.4), 0, rng.uniform(-0.4, 0.4))))
        else: S_.append(ball(rng.uniform(0.6, 1.2), C(150, 166, 110), (x, y + 0.3, z), 1, (1, 0.6, 1), 0.2, int(rng.integers(1e6))))
    elif ground == 'frost':
        if rng.random() < 0.5:
            h = rng.uniform(1.5, 4.5); S_.append(T(paint(trimesh.creation.cone(h * 0.25, h, sections=5), ICE1 if rng.random() < 0.5 else ICE2), (x, y - 0.1, z), (-math.pi / 2 + rng.uniform(-0.2, 0.2), 0, rng.uniform(-0.2, 0.2))))
        else:
            h = rng.uniform(3, 6); S_.append(cyl(0.18, h * 0.3, C(70, 56, 44), (x, y + h * 0.15, z), sec=5))
            for t in range(3): S_.append(T(paint(trimesh.creation.cone(h * (0.24 - t * 0.05), h * 0.4, sections=6), C(214, 226, 234) if t == 2 else C(60, 92, 80)), (x, y + h * (0.25 + t * 0.2), z), (-math.pi / 2, 0, 0)))
    else:
        if rng.random() < 0.6:
            for k in range(int(rng.integers(2, 5))):
                h = rng.uniform(1.2, 4.5); col_ = cyl(rng.uniform(0.45, 0.8), h, C(30, 29, 32), (x + rng.uniform(-1.2, 1.2), y + h / 2 - 0.2, z + rng.uniform(-1.2, 1.2)), sec=6); S_.append(col_)
                if h > 2.5: C_.append(col_)
        else:
            S_.append(ball(0.9, SULF if 'SULF' in globals() else C(176, 150, 64), (x, y, z), 1, (1, 0.3, 1), 0.2, int(rng.integers(1e6))))
            G_.append(ball(0.18, C(255, 120, 40), (x, y + 0.25, z)))
    return S_, G_, C_
SULF = C(176, 150, 64)
if __name__ == '__main__':
    ids = sys.argv[1:] or list(ISL)
    manp = os.path.join(ROOT5, 'stage5_manifest.json'); man = json.load(open(manp)) if os.path.exists(manp) else {'islands': {}}
    for k in ids:
        print('==', k); man['islands'][k] = build(k)
    man['stats'] = {**man.get('stats', {}), **STATS}
    man['note'] = 'Stage 5 island interiors. Files per island live in meshes/<region>/ with the region prefix; copy them into that region mesh dir.'
    json.dump(man, open(manp, 'w'), indent=1, default=float); print('DONE')
