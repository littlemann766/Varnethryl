"""Land4 scatter. Varied trees, shrubs, rocks and shore wrack on every landmass, including small islets.
Seated on the land4 terrain. Routes, piers, POIs, the Saltglass harbour and props stay clear.
Collider kinds (trees, boulders, landmarks) keep a wide berth; tufts may sit nearer a path but not on it.
"""
import os, sys, json, zlib
import numpy as np
import trimesh
from scipy.spatial import cKDTree
from scipy import ndimage
sys.path.insert(0, os.path.dirname(__file__))
from common import write_glb, fbm
from smooth_land import ROOT, LAND3, REG, build_pins, is_terrain, gidx, CELL

OUT = ROOT
MAN = json.load(open(os.path.join(os.path.dirname(ROOT), "stage5_islands", "stage5_manifest.json")))

def ring(rng, r, y, n, jit=0.0):
    a = np.linspace(0, 2 * np.pi, n, endpoint=False) + rng.random() * 6
    rr = r * (1 + jit * (rng.random(n) - 0.5))
    return np.stack([np.cos(a) * rr, np.full(n, y), np.sin(a) * rr], 1)

def loft(rings, cols, cap=True):
    n = len(rings[0])
    V = np.concatenate(rings)
    C = np.concatenate([np.tile(c, (n, 1)) for c in cols])
    F = []
    for k in range(len(rings) - 1):
        for i in range(n):
            a = k * n + i; b = k * n + (i + 1) % n; c = a + n; d = b + n
            F += [[a, c, b], [b, c, d]]
    if cap:
        top = rings[-1]
        V = np.vstack([V, [[top[:, 0].mean(), top[0, 1], top[:, 2].mean()]]])
        C = np.vstack([C, cols[-1]])
        t = len(V) - 1; o = (len(rings) - 1) * n
        F += [[o + i, t, o + (i + 1) % n] for i in range(n)]
    return V, np.array(F, np.int64), C

def cone(rng, r, y0, h, n, col, tip=None):
    V = np.vstack([ring(rng, r, y0, n, 0.28), [[0, y0 + h, 0]]])
    C = np.vstack([np.tile(col, (n, 1)), tip if tip is not None else col])
    F = [[i, n, (i + 1) % n] for i in range(n)]
    return V, np.array(F, np.int64), C

def blob(rng, r, sub, col, sq=(1, 1, 1), jit=0.3):
    s = trimesh.creation.icosphere(subdivisions=sub)
    V = np.array(s.vertices, np.float64)
    V *= (1 + jit * (rng.random(len(V)) - 0.5))[:, None]
    V *= np.array(sq) * r
    sh = np.clip(V[:, 1] / (r * sq[1] + 1e-6) * 0.5 + 0.5, 0, 1)[:, None]
    C = np.array(col) * (0.62 + 0.38 * sh)
    return V, np.array(s.faces), C

def merge(parts):
    V, F, C, o = [], [], [], 0
    for v, f, c in parts:
        V.append(v); F.append(f + o); C.append(c); o += len(v)
    return np.concatenate(V), np.concatenate(F), np.concatenate(C)

def place(p, s=1.0, yaw=0.0, dy=0.0, shear=(0, 0)):
    v, f, c = p
    ca, sa = np.cos(yaw), np.sin(yaw)
    R = np.array([[ca, 0, -sa], [0, 1, 0], [sa, 0, ca]])
    v = v @ R.T * s
    v[:, 0] += v[:, 1] * shear[0]; v[:, 2] += v[:, 1] * shear[1]
    v = v + [0, dy, 0]
    return v, f, c

BARK = np.array([0.28, 0.18, 0.11])
def pine(hi, rng, snow=False, tone=1.0, style=0):
    n = 7 if hi else 5
    h = rng.uniform(6.5, 13 if style == 0 else 9)
    parts = [loft([ring(rng, 0.26, -0.3, n), ring(rng, 0.11, h * 0.55, n, 0.1)], [BARK * 0.85, BARK], False)]
    lv = (4 if hi else 2) if style != 2 else (3 if hi else 2)
    col = np.array([0.10, 0.24, 0.13]) * tone * rng.uniform(0.82, 1.18)
    shear = (rng.normal(0, 0.18), rng.normal(0, 0.18)) if style == 1 else (0, 0)
    built = []
    for k in range(lv):
        t = k / lv
        rad = (1 - t) * (h * (0.22 if style == 0 else 0.30)) + 0.45
        y = h * (0.18 + 0.72 * t)
        tip = np.array([0.86, 0.90, 0.95]) if snow else col * 1.15
        built.append(cone(rng, rad, y, h * (0.40 if hi else 0.5) * (1 - t * 0.25), n, col * (0.8 + 0.25 * t), tip))
        if snow:
            v, f, c = built[-1]
            c = np.where((v[:, 1] > y + h * 0.12)[:, None], np.array([0.84, 0.89, 0.94]), c)
            built[-1] = (v, f, c)
    parts += built
    v, f, c = merge(parts)
    return place((v, f, c), 1, 0, 0, shear), h

def oak(hi, rng, tone=1.0, style=0):
    n = 6 if hi else 5
    h = rng.uniform(4.5, 8.5)
    parts = [loft([ring(rng, 0.32, -0.3, n, 0.15), ring(rng, 0.16, h * 0.55, n)], [BARK, BARK * 0.9], False)]
    col = np.array([0.22, 0.38, 0.14]) * tone * rng.uniform(0.75, 1.2)
    if style == 1:
        col = col * np.array([1.15, 0.9, 0.75])  # early autumn
    blobs = 3 if hi else 1
    sub = 1 if hi else 0
    for k in range(blobs):
        off = rng.normal(0, 0.8, 3) * [1, 0.35, 1] if k else np.zeros(3)
        v, f, c = blob(rng, rng.uniform(1.5, 2.5), sub, col, (1.0, 0.72, rng.uniform(0.8, 1.15)), 0.35)
        parts.append((v + [off[0], h * 0.72 + off[1], off[2]], f, c))
    return merge(parts), h

def dead(hi, rng):
    n = 5 if hi else 4
    h = rng.uniform(3.5, 7)
    B = np.array([0.16, 0.12, 0.10]) * rng.uniform(0.8, 1.2)
    parts = [loft([ring(rng, 0.22, -0.2, n, 0.2), ring(rng, 0.05, h, n)], [B, B * 1.3])]
    for k in range(3 if hi else 1):
        a = rng.random() * 6.28; y = h * rng.uniform(0.45, 0.85); L = rng.uniform(0.8, 2.0)
        v, f, c = loft([ring(rng, 0.06, 0, 4), ring(rng, 0.02, L, 4)], [B, B * 0.8], False)
        v = v.copy(); d = np.array([np.cos(a), rng.uniform(0.2, 0.8), np.sin(a)])
        v[:, 0] += v[:, 1] * d[0]; v[:, 2] += v[:, 1] * d[2]; v[:, 1] *= d[1]
        parts.append((v + [0, y, 0], f, c))
    return merge(parts), h

def rock(hi, rng, col, big=False, slab=False):
    r = rng.uniform(1.1, 2.8) if big else rng.uniform(0.28, 0.85)
    sq = (rng.uniform(0.9, 1.5), rng.uniform(0.28, 0.45), rng.uniform(0.7, 1.2)) if slab else (1, rng.uniform(0.45, 0.85), rng.uniform(0.75, 1.25))
    v, f, c = blob(rng, r, 1 if (hi and big) else 0, col * rng.uniform(0.82, 1.15), sq, 0.4)
    return (v - [0, r * sq[1] * 0.35, 0], f, c), r

def crystal(hi, rng, col, glint):
    parts = []
    for k in range(int(rng.integers(3, 6) if hi else 2)):
        v, f, c = cone(rng, rng.uniform(0.12, 0.32), -0.15, rng.uniform(0.7, 2.4), 5 if hi else 4, col, glint)
        parts.append(place((v, f, c), 1, rng.random() * 6, 0, (rng.normal(0, 0.28), rng.normal(0, 0.28))))
    return merge(parts), 2.0

def bush(hi, rng, col):
    v, f, c = blob(rng, rng.uniform(0.55, 1.25), 1 if hi else 0, col * rng.uniform(0.8, 1.2), (rng.uniform(0.8, 1.3), 0.65, 1), 0.4)
    return (v + [0, 0.25, 0], f, c), 1.0

def tuft(hi, rng, col, flower=None):
    parts = []
    for k in range(5 if hi else 2):
        tip = flower if (flower is not None and rng.random() > 0.4) else col * 1.35
        v, f, c = cone(rng, 0.1, -0.02, rng.uniform(0.35, 0.85), 3, col * rng.uniform(0.75, 1.2), tip)
        parts.append(place((v, f, c), 1, rng.random() * 6, 0, (rng.normal(0, 0.25), rng.normal(0, 0.25))))
        parts[-1] = (parts[-1][0] + [rng.normal(0, 0.22), 0, rng.normal(0, 0.22)], parts[-1][1], parts[-1][2])
    return merge(parts), 0.4

def drift(hi, rng):
    B = np.array([0.32, 0.24, 0.16]) * rng.uniform(0.8, 1.1)
    v, f, c = loft([ring(rng, 0.12, 0, 5, 0.3), ring(rng, 0.08, rng.uniform(1.2, 2.4), 5, 0.3)], [B, B * 0.7])
    return place((v, f, c), 1, rng.random() * 6, 0.05, (0.7, rng.normal(0, 0.1))), 1.5

def column(hi, rng):
    parts = []; B = np.array([0.07, 0.065, 0.07])
    for k in range(int(rng.integers(3, 6) if hi else 2)):
        h = rng.uniform(1.4, 4.2); n = 6 if hi else 5
        v, f, c = loft([ring(rng, rng.uniform(0.28, 0.5), -0.2, n), ring(rng, rng.uniform(0.25, 0.48), h, n)], [B, B * 1.3])
        parts.append((v + [rng.normal(0, 0.6), 0, rng.normal(0, 0.6)], f, c))
    return merge(parts), 2.0

def lava_spire(hi, rng):
    parts = []; B = np.array([0.06, 0.045, 0.04]); E = np.array([0.62, 0.16, 0.03])
    for k in range(int(rng.integers(2, 5) if hi else 2)):
        h = rng.uniform(5, 13) * (1 if k == 0 else rng.uniform(0.45, 0.75))
        n = 6 if hi else 4
        v, f, c = loft([ring(rng, rng.uniform(0.7, 1.4), -0.4, n, 0.35), ring(rng, 0.35, h * 0.5, n, 0.3), ring(rng, 0.08, h, n)], [B, B * 1.2, E])
        parts.append(place((v, f, c), 1, rng.random() * 6, 0, (rng.normal(0, 0.06), rng.normal(0, 0.06))))
        parts[-1] = (parts[-1][0] + [rng.normal(0, 1.4) if k else 0, 0, rng.normal(0, 1.4) if k else 0], parts[-1][1], parts[-1][2])
    return merge(parts), 3.0

def boulder_cluster(hi, rng, col):
    parts = []
    for k in range(int(rng.integers(3, 6) if hi else 2)):
        r = rng.uniform(1.6, 3.6) * (1 if k == 0 else 0.55)
        v, f, c = blob(rng, r, 1 if hi else 0, col * rng.uniform(0.8, 1.15), (1, rng.uniform(0.5, 0.8), rng.uniform(0.8, 1.2)), 0.45)
        o = [rng.normal(0, 2.2), 0, rng.normal(0, 2.2)] if k else [0, 0, 0]
        parts.append((v + o - [0, r * 0.25, 0], f, c))
    return merge(parts), 3.5

# name, weight, builder(hi,rng)->((V,F,C),size), collider class (0 none, 1 tree, 2 boulder, 3 landmark), min_y, max_slope
def spec_for(region):
    A = [
        ("pine", 16, lambda hi, rng: pine(hi, rng, style=0), 1, 2.2, 26),
        ("pine_bent", 8, lambda hi, rng: pine(hi, rng, style=1), 1, 2.2, 24),
        ("oak", 12, lambda hi, rng: oak(hi, rng, style=0), 1, 2.2, 22),
        ("oak_warm", 6, lambda hi, rng: oak(hi, rng, style=1), 1, 2.2, 22),
        ("bush", 14, lambda hi, rng: bush(hi, rng, np.array([0.16, 0.30, 0.12])), 0, 1.2, 32),
        ("flower", 10, lambda hi, rng: tuft(hi, rng, np.array([0.22, 0.36, 0.12]), np.array([0.75, 0.62, 0.18])), 0, 0.8, 28),
        ("tuft", 14, lambda hi, rng: tuft(hi, rng, np.array([0.20, 0.36, 0.13])), 0, 0.8, 32),
        ("boulder", 5, lambda hi, rng: rock(hi, rng, np.array([0.40, 0.38, 0.34]), True), 2, 1.0, 40),
        ("slab", 4, lambda hi, rng: rock(hi, rng, np.array([0.42, 0.40, 0.36]), True, True), 2, 1.0, 36),
        ("stones", 8, lambda hi, rng: rock(hi, rng, np.array([0.45, 0.42, 0.38])), 0, 0.4, 42),
        ("driftwood", 4, lambda hi, rng: drift(hi, rng), 0, 0.35, 30),
    ]
    B = [
        ("shore_pine", 12, lambda hi, rng: pine(hi, rng, tone=0.85, style=int(rng.integers(0, 3))), 1, 3.0, 24),
        ("scrub", 14, lambda hi, rng: bush(hi, rng, np.array([0.34, 0.36, 0.18])), 0, 1.2, 32),
        ("salt_bush", 8, lambda hi, rng: bush(hi, rng, np.array([0.42, 0.40, 0.28])), 0, 1.0, 30),
        ("dune_grass", 14, lambda hi, rng: tuft(hi, rng, np.array([0.48, 0.46, 0.26])), 0, 0.5, 32),
        ("salt_flower", 6, lambda hi, rng: tuft(hi, rng, np.array([0.50, 0.48, 0.36]), np.array([0.85, 0.82, 0.78])), 0, 0.5, 28),
        ("salt_crystal", 8, lambda hi, rng: crystal(hi, rng, np.array([0.72, 0.84, 0.88]), np.array([0.95, 0.98, 1])), 0, 1.0, 36),
        ("boulder", 6, lambda hi, rng: rock(hi, rng, np.array([0.62, 0.56, 0.48]), True), 2, 1.0, 40),
        ("slab", 5, lambda hi, rng: rock(hi, rng, np.array([0.66, 0.60, 0.50]), True, True), 2, 1.0, 34),
        ("stones", 10, lambda hi, rng: rock(hi, rng, np.array([0.68, 0.64, 0.56])), 0, 0.3, 42),
        ("driftwood", 5, lambda hi, rng: drift(hi, rng), 0, 0.3, 28),
    ]
    F = [
        ("snow_pine", 18, lambda hi, rng: pine(hi, rng, snow=True, tone=0.8, style=0), 1, 2.4, 26),
        ("snow_bent", 8, lambda hi, rng: pine(hi, rng, snow=True, tone=0.75, style=1), 1, 2.4, 24),
        ("snow_bush", 8, lambda hi, rng: bush(hi, rng, np.array([0.45, 0.52, 0.48])), 0, 1.2, 30),
        ("ice_shard", 8, lambda hi, rng: crystal(hi, rng, np.array([0.55, 0.72, 0.86]), np.array([0.9, 0.96, 1])), 0, 0.8, 40),
        ("boulder", 8, lambda hi, rng: rock(hi, rng, np.array([0.55, 0.60, 0.66]), True), 2, 1.0, 40),
        ("slab", 4, lambda hi, rng: rock(hi, rng, np.array([0.60, 0.64, 0.70]), True, True), 2, 1.0, 36),
        ("stones", 10, lambda hi, rng: rock(hi, rng, np.array([0.62, 0.66, 0.72])), 0, 0.4, 42),
        ("dead_tree", 6, lambda hi, rng: dead(hi, rng), 1, 2.2, 26),
    ]
    H = [
        ("dead_tree", 10, lambda hi, rng: dead(hi, rng), 1, 2.2, 26),
        ("dead_bent", 5, lambda hi, rng: dead(hi, rng), 1, 2.2, 24),
        ("basalt", 8, lambda hi, rng: column(hi, rng), 2, 1.0, 40),
        ("lava_rocks", 8, lambda hi, rng: rock(hi, rng, np.array([0.22, 0.08, 0.04]), True), 2, 1.0, 42),
        ("boulder", 6, lambda hi, rng: rock(hi, rng, np.array([0.08, 0.07, 0.07]), True), 2, 1.0, 40),
        ("stones", 7, lambda hi, rng: rock(hi, rng, np.array([0.10, 0.08, 0.07])), 0, 0.4, 44),
        ("cinders", 6, lambda hi, rng: rock(hi, rng, np.array([0.04, 0.035, 0.035])), 0, 0.3, 44),
        ("sulfur", 5, lambda hi, rng: crystal(hi, rng, np.array([0.72, 0.58, 0.12]), np.array([0.95, 0.85, 0.3])), 0, 0.8, 38),
        ("obsidian", 5, lambda hi, rng: crystal(hi, rng, np.array([0.07, 0.06, 0.09]), np.array([0.28, 0.22, 0.32])), 0, 0.8, 40),
        ("ash_grass", 8, lambda hi, rng: tuft(hi, rng, np.array([0.16, 0.14, 0.10])), 0, 0.8, 32),
    ]
    return {"A": A, "B": B, "frost": F, "ash": H}[region]

DENS = {"A": 1 / 240.0, "B": 1 / 420.0, "frost": 1 / 640.0, "ash": 1 / 200.0}
CAP = {"A": 2600, "B": 3200, "frost": 4000, "ash": 3600}

def components_from(meshes):
    """Label land components on a 20 m grid. Returns records and a (origin, cell, label) grid."""
    cell = 20.0
    samples = []  # xyz, region later
    for b, s in meshes:
        V = np.asarray(s.vertices); F = np.asarray(s.faces); C = np.asarray(s.visual.vertex_colors)
        A = C[:, 3] > 127
        fm = A[F].all(1)
        cen = V[F[fm]].mean(1)
        ok = cen[:, 1] > 0.8
        c = cen[ok]
        if len(c) > 6000:
            c = c[::max(1, len(c) // 6000)]
        if len(c):
            samples.append(c)
    if not samples:
        return [], None
    P = np.concatenate(samples)
    origin = np.floor(P[:, [0, 2]].min(0) / cell) * cell - cell
    ij = np.floor((P[:, [0, 2]] - origin) / cell).astype(int)
    shape = tuple(ij.max(0) + 3)
    grid = np.zeros(shape, bool)
    grid[ij[:, 0], ij[:, 1]] = True
    grid = ndimage.binary_closing(grid, iterations=1)
    lab, n = ndimage.label(grid)
    recs = []
    for i in range(1, n + 1):
        area = float((lab == i).sum() * cell * cell)
        if area < 250:
            continue
        sel = lab[ij[:, 0], ij[:, 1]] == i
        if not sel.any():
            continue
        c = P[sel][:, [0, 2]].mean(0)
        bb0 = P[sel][:, [0, 2]].min(0); bb1 = P[sel][:, [0, 2]].max(0)
        recs.append(dict(lab=i, area_m2=area, centroid=[float(c[0]), float(c[1])],
                         bbox=[float(bb0[0]), float(bb0[1]), float(bb1[0]), float(bb1[1])]))
    return recs, (origin, cell, lab)

def classify(region, recs):
    islands = [(k, I) for k, I in MAN["islands"].items() if I["region"] == region]
    if not recs:
        return []
    biggest = max(recs, key=lambda r: r["area_m2"])["lab"]
    out = []
    for r in recs:
        c = np.array(r["centroid"])
        near, bestd = None, 1e9
        for k, I in islands:
            ph = np.array(I["pier_head"])[[0, 2]]
            d = float(np.hypot(*(c - ph)))
            if d < bestd:
                bestd, near = d, k
        kind = "main" if r["lab"] == biggest else "islet"
        named = near if bestd < 160 else None
        if named and kind != "main":
            kind = "named_land"
        if kind == "main" and named:
            pass
        cid = f"{region}_{kind}_{near if named else 'x'}{int(round(c[0]))}_{int(round(c[1]))}"
        # stable short id
        if kind == "main":
            cid = f"{region}_main"
        elif named and kind == "named_land":
            cid = f"{region}_named_{named}"
        else:
            cid = f"{region}_islet_{int(round(c[0]))}_{int(round(c[1]))}"
        r = dict(r)
        r.update(id=cid, region=region, kind=kind, nearest_named=near, nearest_m=round(bestd, 1),
                 scatter=0, scatter_kinds={})
        out.append(r)
    return out

def lookup_comp(grid, xz):
    origin, cell, lab = grid
    ij = np.floor((np.asarray(xz, np.float64).reshape(-1, 2) - origin) / cell).astype(int)
    ok = (ij[:, 0] >= 0) & (ij[:, 1] >= 0) & (ij[:, 0] < lab.shape[0]) & (ij[:, 1] < lab.shape[1])
    out = np.zeros(len(ij), np.int32)
    out[ok] = lab[ij[ok, 0], ij[ok, 1]]
    return out

def main():
    pin, _routes = build_pins()
    from scipy.ndimage import binary_dilation
    block = binary_dilation(pin, iterations=1)       # ~2 m, nobody stands in a prop
    block_col = binary_dilation(pin, iterations=3)   # ~6 m, trees and boulders
    rng = np.random.default_rng(11)
    all_comp = []
    stats = {}
    for region, (subdir, pre) in REG.items():
        src = os.path.join(ROOT, subdir)
        ms = []
        for f in sorted(os.listdir(src)):
            if not f.endswith(".glb") or f.endswith("_lod1.glb") or f.endswith("_col.glb"):
                continue
            b = f[:-4]
            if not b.startswith(pre) or not is_terrain(b):
                continue
            s = trimesh.load(os.path.join(src, f), force="mesh", process=False)
            ms.append((b, s))
        recs, grid = components_from(ms)
        crecs = classify(region, recs)
        # sample
        pts = []; nrm = []; labs = []
        for b, s in ms:
            V = np.asarray(s.vertices); F = np.asarray(s.faces); C = np.asarray(s.visual.vertex_colors)
            A = C[:, 3] > 127
            fm = A[F].all(1)
            area = s.area_faces * fm
            if area.sum() < 1:
                continue
            n = int(area.sum() * DENS[region] * 3)
            n = min(n, 20000)
            if n < 8:
                continue
            fi = rng.choice(len(area), n, p=area / area.sum())
            u = rng.random((n, 2)); m = u.sum(1) > 1; u[m] = 1 - u[m]
            T = V[F[fi]]
            P = T[:, 0] + (T[:, 1] - T[:, 0]) * u[:, :1] + (T[:, 2] - T[:, 0]) * u[:, 1:]
            N = s.face_normals[fi]
            pts.append(P); nrm.append(N); labs.append(lookup_comp(grid, P[:, [0, 2]]))
        P = np.concatenate(pts); N = np.concatenate(nrm); lab = np.concatenate(labs)
        sl = np.degrees(np.arccos(np.clip(np.abs(N[:, 1]), 0, 1)))
        forest = fbm(np.stack([P[:, 0] / 90, P[:, 2] / 90, np.zeros(len(P))], 1), 3, len(region) * 3)
        sp = spec_for(region)
        W = np.array([s_[1] for s_ in sp], float); W /= W.sum()
        kind = rng.choice(len(sp), len(P), p=W)
        on_block = block[tuple(gidx(P[:, [0, 2]]).T)]
        on_col = block_col[tuple(gidx(P[:, [0, 2]]).T)]
        keep = np.array([
            P[i, 1] >= sp[k][4] and sl[i] <= sp[k][5] and (not on_block[i]) and (sp[k][3] == 0 or not on_col[i])
            for i, k in enumerate(kind)
        ])
        tree = np.array([sp[k][3] == 1 for k in kind])
        keep &= ~(tree & (forest < -0.15))
        # groves: thin the open ground a bit, never strip an islet that has little forest noise
        thin = rng.random(len(P)) < np.clip(0.35 + forest * 0.9, 0.25, 1)
        keep &= thin
        P, kind, sl, lab = P[keep], kind[keep], sl[keep], lab[keep]
        if len(P):
            kd = cKDTree(P[:, [0, 2]]); drop = np.zeros(len(P), bool)
            for i, j in kd.query_pairs(2.4):
                if not drop[i] and not drop[j]:
                    drop[j] = True
            P, kind, lab = P[~drop], kind[~drop], lab[~drop]
        # floors so no listed landmass is left bare
        pools = {r["lab"]: np.nonzero(lab == r["lab"])[0] if len(lab) else np.array([], int) for r in crecs}
        # rebuild candidate pools from the pre-thin sample for floors: use current P only, and if short, we already kept lab>0
        def add_floor(rec, n_tree, n_bush, n_rock, n_detail):
            nonlocal P, kind, lab
            if len(P) == 0:
                return
            ii = np.nonzero(lab == rec["lab"])[0]
            have = {}
            for i in ii:
                have[sp[kind[i]][0]] = have.get(sp[kind[i]][0], 0) + 1
            def is_tree(k): return sp[k][3] == 1
            def is_rock(k): return sp[k][3] == 2
            def is_detail(k): return sp[k][3] == 0 and "crystal" not in sp[k][0] and "shard" not in sp[k][0]
            need = []
            if sum(1 for i in ii if is_tree(kind[i])) < n_tree:
                need += [("tree", n_tree - sum(1 for i in ii if is_tree(kind[i])))]
            if sum(1 for i in ii if "bush" in sp[kind[i]][0] or "scrub" in sp[kind[i]][0]) < n_bush:
                need += [("bush", n_bush - sum(1 for i in ii if "bush" in sp[kind[i]][0] or "scrub" in sp[kind[i]][0]))]
            if sum(1 for i in ii if is_rock(kind[i])) < n_rock:
                need += [("rock", n_rock - sum(1 for i in ii if is_rock(kind[i])))]
            if sum(1 for i in ii if is_detail(kind[i])) < n_detail:
                need += [("detail", n_detail - sum(1 for i in ii if is_detail(kind[i])))]
            if not need or len(ii) == 0:
                return
            # duplicate existing points of the right class, jittered, if we have any; else jitter any in-comp point
            extra_p, extra_k = [], []
            for cls, nneed in need:
                if nneed <= 0:
                    continue
                if cls == "tree":
                    src = [i for i in ii if is_tree(kind[i])] or [i for i in ii if sp[kind[i]][3] == 0]
                    choices = [k for k in range(len(sp)) if sp[k][3] == 1]
                elif cls == "bush":
                    src = [i for i in ii if sp[kind[i]][3] == 0]
                    choices = [k for k in range(len(sp)) if "bush" in sp[k][0] or "scrub" in sp[k][0]] or [k for k in range(len(sp)) if sp[k][3] == 0]
                elif cls == "rock":
                    src = [i for i in ii if is_rock(kind[i])] or list(ii)
                    choices = [k for k in range(len(sp)) if sp[k][3] == 2]
                else:
                    src = list(ii)
                    choices = [k for k in range(len(sp)) if sp[k][3] == 0]
                if not src or not choices:
                    continue
                for t in range(nneed):
                    j = src[int(rng.integers(0, len(src)))]
                    jitter = rng.normal(0, 6.0, 2)
                    q = P[j].copy(); q[0] += jitter[0]; q[2] += jitter[1]
                    ij = gidx(np.array([[q[0], q[2]]]))
                    if block[ij[0, 0], ij[0, 1]]:
                        continue
                    extra_p.append(q); extra_k.append(int(rng.choice(choices)))
            if extra_p:
                P = np.concatenate([P, np.array(extra_p)])
                kind = np.concatenate([kind, np.array(extra_k)])
                lab = np.concatenate([lab, np.full(len(extra_p), rec["lab"], np.int32)])
        for rec in crecs:
            area = rec["area_m2"]
            if rec["kind"] == "named_land" or (rec["nearest_named"] and rec["kind"] == "main"):
                # the playable island's share of a large landmass is handled by the named id below
                pass
            if area < 800:
                add_floor(rec, 0, 1, 1, 3)
            elif area < 4000:
                add_floor(rec, 2, 3, 2, 6)
            elif area < 20000:
                add_floor(rec, 5, 6, 4, 10)
            else:
                add_floor(rec, 10, 10, 6, 16)
        lab_comp = lab.copy()
        n_comp = len(P)
        # named islands specifically, using pier neighbourhood even if the component is the main landmass
        for k, I in MAN["islands"].items():
            if I["region"] != region:
                continue
            ph = np.array(I["pier_head"], float)
            if len(P) == 0:
                continue
            d = np.hypot(P[:, 0] - ph[0], P[:, 2] - ph[2])
            reach = 220.0 if k != "saltwatch_keep" else 90.0
            # synthetic rec over points near the pier
            near = np.nonzero(d < reach)[0]
            if len(near) == 0:
                continue
            # count and top up by temporarily viewing them as one lab
            fake = dict(lab=-1000 - (zlib.crc32(k.encode()) % 50000), area_m2=MAN["stats"].get(k, {}).get("reach_m2", 20000))
            # retag those points
            lab = lab.copy()
            lab[near] = fake["lab"]
            ha = fake["area_m2"]
            if k == "saltwatch_keep":
                add_floor(fake, 4, 6, 3, 8)
            elif ha < 20000:
                add_floor(fake, 8, 10, 5, 14)
            else:
                add_floor(fake, 14, 16, 8, 22)
        # spacing again after floors
        if len(P) > 1:
            kd = cKDTree(P[:, [0, 2]]); drop = np.zeros(len(P), bool)
            for i, j in kd.query_pairs(2.2):
                if not drop[i] and not drop[j]:
                    drop[j] = True
            P, kind, lab = P[~drop], kind[~drop], lab[~drop]
        if len(P) > CAP[region]:
            protect = np.zeros(len(P), bool)
            for k, I in MAN["islands"].items():
                if I["region"] != region:
                    continue
                ph = np.array(I["pier_head"], float)
                protect |= np.hypot(P[:, 0] - ph[0], P[:, 2] - ph[2]) < (90 if k == "saltwatch_keep" else 180)
            islet_labs = [r["lab"] for r in crecs if r["kind"] == "islet"]
            if islet_labs:
                protect |= np.isin(lab, islet_labs)
            idx_p = np.nonzero(protect)[0]
            idx_r = np.nonzero(~protect)[0]
            room = CAP[region] - len(idx_p)
            if room < 0:
                idx_p = idx_p[:CAP[region]]
                idx_r = np.array([], int)
            elif len(idx_r) > room:
                idx_r = rng.choice(idx_r, room, replace=False)
            sel = np.concatenate([idx_p, idx_r]) if len(idx_r) else idx_p
            P, kind, lab = P[sel], kind[sel], lab[sel]
        if region == "ash" and len(P):
            sp = sp + [
                ("lava_spire", 1, lambda hi, rng: lava_spire(hi, rng), 3, 2.0, 32),
                ("boulder_cluster", 1, lambda hi, rng: boulder_cluster(hi, rng, np.array([0.09, 0.08, 0.08])), 3, 1.5, 34),
            ]
            chosen = []
            extra_p, extra_k = [], []
            for i in rng.permutation(len(P)):
                q = P[i]
                if any(np.hypot(q[0] - c[0], q[2] - c[2]) < 32 for c in chosen):
                    continue
                ij = gidx(np.array([[q[0], q[2]]]))
                if block_col[ij[0, 0], ij[0, 1]]:
                    continue
                chosen.append(q)
                extra_p.append(q)
                extra_k.append(len(sp) - 2 + (len(chosen) % 2))
                if len(chosen) >= 110:
                    break
            if extra_p:
                P = np.concatenate([P, extra_p])
                kind = np.concatenate([kind, np.array(extra_k, int)])
                lab = np.concatenate([lab, np.full(len(extra_p), -1, np.int32)])
        # build chunks
        if len(P) == 0:
            stats[region] = dict(instances=0, tris_high=0, tris_lod1=0, chunks=0)
            all_comp.extend(crecs)
            continue
        ch = np.floor(P[:, [0, 2]] / 256).astype(int)
        keys = np.unique(ch, axis=0)
        od = os.path.join(OUT, subdir); os.makedirs(od, exist_ok=True)
        tot = [0, 0, 0]; cnt = {}
        for key in keys:
            ii = np.nonzero((ch == key).all(1))[0]
            Hparts, Lparts, Cparts = [], [], []
            for i in ii:
                knd = int(kind[i]); seed = int(rng.integers(1, 2 ** 31 - 1)); yaw = float(rng.random() * 6.283); sc = float(rng.uniform(0.82, 1.22))
                for hi, dst in ((True, Hparts), (False, Lparts)):
                    (v, f, c), size = sp[knd][2](hi, np.random.default_rng(seed))
                    v, f, c = place((v, f, c), sc, yaw)
                    dst.append((v + P[i] - [0, 0.12, 0], f, c))
                cnt[sp[knd][0]] = cnt.get(sp[knd][0], 0) + 1
                if sp[knd][3] >= 1:
                    w = 0.45 if sp[knd][3] == 1 else (3.2 * sc if sp[knd][3] == 3 else 1.2 * sc)
                    bx = trimesh.creation.box([w, 2.6, w])
                    Cparts.append((np.array(bx.vertices) + P[i] + [0, 1.0, 0], np.array(bx.faces), np.zeros((8, 3))))
            nm = f"{pre}land_scatter_c{key[0] + 20:02d}_{key[1] + 20:02d}"
            for parts, suf in ((Hparts, ""), (Lparts, "_lod1")):
                if not parts:
                    continue
                V, F, C = merge(parts)
                Ca = np.concatenate([C, np.zeros((len(C), 1))], 1)
                write_glb(os.path.join(od, nm + suf + ".glb"), V, F, Ca, None, nm + suf)
                tot[0 if suf == "" else 1] += len(F)
            if Cparts:
                V, F, C = merge(Cparts)
                Ca = np.concatenate([C, np.zeros((len(C), 1))], 1)
                write_glb(os.path.join(od, nm + "_col.glb"), V, F, Ca, None, nm + "_col")
                tot[2] += len(F)
        # per component counts
        for rec in crecs:
            ii = np.nonzero(lab == rec["lab"])[0]
            kk = {}
            for i in ii:
                kk[sp[kind[i]][0]] = kk.get(sp[kind[i]][0], 0) + 1
            rec["scatter"] = int(len(ii))
            rec["scatter_kinds"] = kk
        # named island counts by pier radius
        named_rows = []
        for k, I in MAN["islands"].items():
            if I["region"] != region:
                continue
            ph = np.array(I["pier_head"], float)
            d = np.hypot(P[:, 0] - ph[0], P[:, 2] - ph[2])
            reach = 220.0 if k != "saltwatch_keep" else 90.0
            ii = np.nonzero(d < reach)[0]
            kk = {}
            for i in ii:
                kk[sp[kind[i]][0]] = kk.get(sp[kind[i]][0], 0) + 1
            named_rows.append(dict(id=k, region=region, kind="named_island", name=I["name"],
                                   area_m2=MAN["stats"].get(k, {}).get("reach_m2"),
                                   centroid=[float(ph[0]), float(ph[2])], nearest_named=k, nearest_m=0,
                                   scatter=int(len(ii)), scatter_kinds=kk,
                                   bbox=None, mesh=I["files"]["mesh"]))
        stats[region] = dict(instances=int(len(P)), by_kind=cnt, chunks=int(len(keys)),
                             tris_high=tot[0], tris_lod1=tot[1],
                             lod1_pct=round(100 * tot[1] / max(tot[0], 1), 1), col_tris=tot[2])
        print(region, stats[region]["instances"], "tris", tot[0], "lod1%", stats[region]["lod1_pct"], cnt, flush=True)
        all_comp.extend(crecs)
        all_comp.extend(named_rows)
    json.dump(stats, open(os.path.join(ROOT, "scatter_stats.json"), "w"), indent=1)
    # drop the internal lab key for the checklist
    clean = []
    for r in all_comp:
        r = dict(r)
        r.pop("lab", None)
        clean.append(r)
    json.dump(clean, open(os.path.join(ROOT, "island_inventory.json"), "w"), indent=1)
    print("components listed", len(clean), flush=True)

if __name__ == "__main__":
    main()
