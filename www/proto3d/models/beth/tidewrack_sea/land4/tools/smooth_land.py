"""Land4 mesh pass. Reads land3 terrain (read-only) and writes rounded silhouettes + soft sea aprons.

Walkable ground, tile seams, overhangs, routes, POIs, piers, bridges and the Saltglass harbour stay put.
Collision meshes are not written. COLOR_0 stays uint8 normalized.
"""
import os, sys, json
import numpy as np
import trimesh
from scipy import ndimage
sys.path.insert(0, os.path.dirname(__file__))
from common import write_glb, fbm, face_normals, vnormals, slope_deg, unique_edges, subdivide

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LAND3 = os.path.abspath(os.path.join(ROOT, "..", "land3"))
SEA = os.path.abspath(os.path.join(ROOT, ".."))
MAN = json.load(open(os.path.join(SEA, "stage5_islands", "stage5_manifest.json")))
CELL = 2.0
X0, Z0, NX = -3400.0, -3400.0, 3400
REG = {
    "A": ("stage1/meshes/", "arch_"),
    "B": ("stage2/meshes/", "coast_"),
    "frost": ("stage4/meshes/", "frost_"),
    "ash": ("stage4/meshes/", "ash_"),
}
WET = {
    "A": np.array([0.40, 0.38, 0.30]),
    "B": np.array([0.58, 0.54, 0.46]),
    "frost": np.array([0.50, 0.58, 0.66]),
    "ash": np.array([0.09, 0.08, 0.075]),
}
SKIRT = {
    "A": np.array([0.46, 0.43, 0.34]),
    "B": np.array([0.64, 0.60, 0.52]),
    "frost": np.array([0.58, 0.66, 0.72]),
    "ash": np.array([0.11, 0.10, 0.09]),
}

def gidx(xz):
    return np.clip(((np.asarray(xz) - [X0, Z0]) / CELL).astype(int), 0, NX - 1)

def stamp(grid, xz, r):
    xz = np.asarray(xz, np.float64).reshape(-1, 2)
    if len(xz) == 0:
        return
    k = int(np.ceil(r / CELL))
    ij = gidx(xz)
    for dx in range(-k, k + 1):
        for dz in range(-k, k + 1):
            if dx * dx + dz * dz <= (k + 0.25) ** 2:
                grid[np.clip(ij[:, 0] + dx, 0, NX - 1), np.clip(ij[:, 1] + dz, 0, NX - 1)] = True

def is_terrain(b):
    return "_tile_" in b or b == "arch_islands" or ("_isl_" in b and not b.endswith("_glow") and not b.endswith("_port"))

def terrain_files(region):
    d, pre = REG[region]
    src = os.path.join(LAND3, d)
    out = []
    for f in sorted(os.listdir(src)):
        if not f.endswith(".glb") or not f.startswith(pre):
            continue
        b = f[:-4]
        if b.endswith("_lod1") or b.endswith("_col"):
            continue
        if is_terrain(b):
            out.append((b, os.path.join(src, f)))
    return out

def build_pins():
    pin = np.zeros((NX, NX), bool)
    routes = []
    for k, I in MAN["islands"].items():
        extra = 10.0 if k == "saltglass" else (9.0 if (I.get("path") or {}).get("max_deg", 0) > 20 else 7.0)
        pts = []
        for po in I.get("pois", []):
            pos = po["pos"]
            stamp(pin, [[pos[0], pos[2]]], po.get("radius", 6) + 8)
            rt = po.get("route") or []
            if rt:
                arr = np.array(rt, np.float64).reshape(-1, 3)
                stamp(pin, arr[:, [0, 2]], extra)
                pts.append(arr[:, [0, 2]])
        if I.get("pier_head"):
            p = I["pier_head"]
            stamp(pin, [[p[0], p[2]]], 28)
        for br in I.get("bridges") or []:
            stamp(pin, [[br["a"][0], br["a"][2]], [br["b"][0], br["b"][2]]], 14)
        if pts:
            routes.append((k, I["region"], np.concatenate(pts)))
    for k, L in MAN["landings"].items():
        stamp(pin, [[L["shore"][0], L["shore"][2]]], 22)
        stamp(pin, [[L["moor"][0], L["moor"][2]]], 16)
    # harbour, glow decals, and placed landmark meshes: footprints stay clear of reshape and of later scatter
    extra_glbs = []
    s5 = os.path.join(SEA, "stage5_islands", "meshes")
    for dirpath, _, files in os.walk(s5):
        for f in files:
            if f.endswith("_port.glb") or f.endswith("_glow.glb"):
                extra_glbs.append(os.path.join(dirpath, f))
    for region, (d, pre) in REG.items():
        src = os.path.join(SEA, d.replace("land3/", ""))
        # stage meshes live in tidewrack_sea/stageN, not land3
        src = os.path.join(SEA, d)
        if not os.path.isdir(src):
            continue
        for f in os.listdir(src):
            if not f.endswith(".glb") or f.endswith("_lod1.glb") or f.endswith("_col.glb"):
                continue
            b = f[:-4]
            if is_terrain(b):
                continue
            if any(s in b for s in ("storm", "fog", "ocean", "buoy", "upg_", "hero", "floe", "iceberg", "hidden", "sunken")):
                continue
            extra_glbs.append(os.path.join(src, f))
    for p in extra_glbs:
        try:
            s = trimesh.load(p, force="mesh", process=False)
        except Exception:
            continue
        V = np.asarray(s.vertices)
        if len(V) == 0:
            continue
        rad = 5.0 if p.endswith("_port.glb") else 3.0
        step = max(1, len(V) // 4000)
        stamp(pin, V[::step][:, [0, 2]], rad)
    return pin, routes

def height_grid(region, files):
    pts = []
    for b, p in files:
        s = trimesh.load(p, force="mesh", process=False)
        V = np.asarray(s.vertices, np.float64)
        C = np.asarray(s.visual.vertex_colors)
        m = C[:, 3] > 127
        pts.append(V[m][:, [0, 1, 2]])
    P = np.concatenate(pts)
    origin = np.floor(P[:, [0, 2]].min(0)) - 16
    cell = 4.0
    ij = np.floor((P[:, [0, 2]] - origin) / cell).astype(int)
    shape = ij.max(0) + 2
    H = np.full(shape, -999.0, np.float32)
    np.maximum.at(H, (ij[:, 0], ij[:, 1]), P[:, 1])
    # fill single-cell holes so a narrow gap isn't treated as open sea
    known = H > -100
    H2 = H.copy()
    dil = ndimage.binary_dilation(known, iterations=1)
    fill = dil & ~known
    # leave true sea empty; only fill if a neighbour is land above 0.5 (inland holes)
    acc = ndimage.uniform_filter(np.where(known, H, 0), size=3)
    cnt = ndimage.uniform_filter(known.astype(np.float32), size=3)
    avg = acc / np.maximum(cnt, 1e-6)
    take = fill & (avg > 0.8)
    H2[take] = avg[take]
    return origin, cell, H2

def sample_h(origin, cell, H, xz):
    ij = np.floor((np.asarray(xz, np.float64).reshape(-1, 2) - origin) / cell).astype(int)
    ok = (ij[:, 0] >= 0) & (ij[:, 1] >= 0) & (ij[:, 0] < H.shape[0]) & (ij[:, 1] < H.shape[1])
    out = np.full(len(ij), -999.0)
    out[ok] = H[ij[ok, 0], ij[ok, 1]]
    return out

def blur_color(V, C, terrain, pin_at, island):
    cell = 4.0
    origin = V[:, [0, 2]].min(0) - cell
    ij = np.floor((V[:, [0, 2]] - origin) / cell).astype(int)
    shape = tuple(ij.max(0) + 2)
    sumC = np.zeros(shape + (3,), np.float64)
    cnt = np.zeros(shape, np.float64)
    t = np.nonzero(terrain)[0]
    np.add.at(sumC, (ij[t, 0], ij[t, 1]), C[t, :3])
    np.add.at(cnt, (ij[t, 0], ij[t, 1]), 1)
    sig = 2.1 if island else 3.3
    sumB = ndimage.gaussian_filter(sumC, sigma=(sig, sig, 0))
    cntB = ndimage.gaussian_filter(cnt, sigma=sig)
    blur = sumB[ij[:, 0], ij[:, 1]] / np.maximum(cntB[ij[:, 0], ij[:, 1], None], 1e-6)
    mix = np.full(len(V), 0.40 if island else 0.56)
    mix[pin_at] = 0.10
    C2 = C.copy()
    C2[t, :3] = C[t, :3] * (1 - mix[t, None]) + blur[t] * mix[t, None]
    return np.clip(C2, 0, 1)

def weights(V, F, C, pin, island):
    N = vnormals(V, F)
    sd = slope_deg(N)
    u, c = unique_edges(F)
    boundary = np.zeros(len(V), bool)
    boundary[np.unique(u[c == 1])] = True
    el = np.linalg.norm(V[u[:, 0]] - V[u[:, 1]], axis=1)
    long = np.zeros(len(V), bool)
    long[np.unique(u[el > 18.0])] = True   # pillars / rails, not ordinary coarse terrain edges
    on_pin = pin[tuple(gidx(V[:, [0, 2]]).T)]
    fn = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
    Nraw = np.zeros_like(V)
    for i in range(3):
        np.add.at(Nraw, F[:, i], fn)
    overhang = Nraw[:, 1] < 0   # true undersides (arches). Vertical cliffs stay free so the silhouette can round.
    hard = (C[:, 3] < 0.5) | boundary | on_pin | long | overhang | (V[:, 1] < -3.0)
    w = np.clip((sd - 22.0) / 12.0, 0, 1)
    shore = (V[:, 1] > -0.5) & (V[:, 1] < 3.6) & (sd > 16) & (~hard)
    w = np.where(shore, np.maximum(w, 0.82), w)
    w[hard] = 0
    return w, N, sd, boundary

def taubin(V, F, w, pairs, lim):
    u, _ = unique_edges(F)
    orig = V.copy()
    for _it in range(pairs):
        for coef in (0.42, -0.45):
            acc = np.zeros_like(V)
            cnt = np.zeros(len(V))
            np.add.at(acc, u[:, 0], V[u[:, 1]])
            np.add.at(acc, u[:, 1], V[u[:, 0]])
            np.add.at(cnt, u[:, 0], 1)
            np.add.at(cnt, u[:, 1], 1)
            mean = acc / (cnt[:, None] + 1e-9)
            V = V + coef * (mean - V) * w[:, None]
            V[w == 0] = orig[w == 0]
    d = V - orig
    L = np.linalg.norm(d, axis=1)
    sc = np.minimum(1.0, lim / (L + 1e-9))
    V = orig + d * sc[:, None]
    V[w == 0] = orig[w == 0]
    return V

def mark_faces(V, F, w, loose):
    fn = face_normals(V, F)
    sd = slope_deg(fn)
    y = V[F][:, :, 1]
    e01 = np.linalg.norm(V[F[:, 1]] - V[F[:, 0]], axis=1)
    e12 = np.linalg.norm(V[F[:, 2]] - V[F[:, 1]], axis=1)
    e20 = np.linalg.norm(V[F[:, 0]] - V[F[:, 2]], axis=1)
    mx = np.maximum(np.maximum(e01, e12), e20)
    wf = w[F].mean(1)
    free = w[F].min(1) > 0
    steep = (sd > 27) & (mx > (3.0 if loose else 5.2)) & (mx < 14) & (wf > 0.32) & (y.max(1) > 3.2)
    water = (y.min(1) < 0.8) & (y.max(1) > 2.0) & (mx > 2.6) & (mx < 16) & free & (wf > 0.15)
    mark = steep | water
    frac = 0.42 if loose else 0.20
    budget = int(frac * len(F)) + int(water.sum())
    if mark.sum() > budget:
        score = np.where(water, 100.0, 0.0) + mx + sd * 0.02
        score[~mark] = -1
        # keep the highest scores
        idx = np.argpartition(score, -budget)[-budget:]
        mark = np.zeros(len(F), bool)
        mark[idx] = True
    return mark

def add_apron(V, F, C, boundary, pin_at, name, region, origin, cell, H):
    if boundary.sum() < 4 or np.percentile(V[:, 1], 90) < 0.4:
        return V, F, C, 0
    u, c = unique_edges(F)
    bnd = u[c == 1]
    # tile rectangle edges are seams, not coast
    if "_tile_" in name:
        bb0 = V[:, [0, 2]].min(0); bb1 = V[:, [0, 2]].max(0)
        def near_bb(idx):
            d = np.minimum(np.minimum(V[idx, 0] - bb0[0], bb1[0] - V[idx, 0]),
                           np.minimum(V[idx, 2] - bb0[1], bb1[1] - V[idx, 2]))
            return d < 3.0
        keep = ~(near_bb(bnd[:, 0]) & near_bb(bnd[:, 1]))
        bnd = bnd[keep]
    if len(bnd) == 0:
        return V, F, C, 0
    # outward horizontal normal, away from the incident face
    # map edge -> a third vertex via faces (first match)
    face_of = {}
    for fi, f in enumerate(F):
        for a, b in ((f[0], f[1]), (f[1], f[2]), (f[2], f[0])):
            face_of.setdefault((int(min(a, b)), int(max(a, b))), int(fi))
    mids = (V[bnd[:, 0]] + V[bnd[:, 1]]) * 0.5
    low = (mids[:, 1] > -0.15) & (mids[:, 1] < 2.6) & (np.linalg.norm(V[bnd[:, 0]] - V[bnd[:, 1]], axis=1) < 14)
    low &= ~pin_at[bnd[:, 0]] & ~pin_at[bnd[:, 1]]
    low &= (C[bnd[:, 0], 3] > 0.5) & (C[bnd[:, 1], 3] > 0.5)
    bnd = bnd[low]
    if len(bnd) == 0:
        return V, F, C, 0
    outs = []
    use = []
    for a, b in bnd:
        key = (int(min(a, b)), int(max(a, b)))
        fi = face_of.get(key)
        if fi is None:
            continue
        f = F[fi]
        third = int(f[0] + f[1] + f[2] - a - b)
        edge = V[b] - V[a]
        perp = np.array([edge[2], 0.0, -edge[0]])
        ln = np.linalg.norm(perp) + 1e-9
        perp /= ln
        mid = (V[a] + V[b]) * 0.5
        if np.dot(perp, V[third] - mid) > 0:
            perp = -perp
        probe = mid[[0, 2]] + perp[[0, 2]] * 7.0
        h = sample_h(origin, cell, H, probe)[0]
        if h > 0.45:
            continue  # outward is still land (tuck rim or a neighbouring shore)
        outs.append(perp)
        use.append((int(a), int(b)))
    if not use:
        return V, F, C, 0
    # one skirt vertex pair per unique boundary vertex
    acc = {}
    cnt = {}
    for (a, b), perp in zip(use, outs):
        for i in (a, b):
            acc[i] = acc.get(i, np.zeros(3)) + perp
            cnt[i] = cnt.get(i, 0) + 1
    q1 = {}; q2 = {}
    base_n = len(V)
    Vlist = [V]
    Clist = [C]
    cursor = base_n
    for i, s in acc.items():
        d = s / (np.linalg.norm(s) + 1e-9)
        p = V[i].copy()
        a = p + d * 4.2; a[1] = min(p[1] * 0.35, 0.55) - 0.05
        b = p + d * 8.6; b[1] = -0.65
        q1[i] = cursor; cursor += 1
        q2[i] = cursor; cursor += 1
        Vlist.append(np.stack([a, b]))
        col = C[i].copy()
        c1 = col.copy(); c1[:3] = col[:3] * 0.45 + SKIRT[region] * 0.55; c1[3] = 1
        c2 = col.copy(); c2[:3] = SKIRT[region] * 0.72; c2[3] = 1
        Clist.append(np.stack([c1, c2]))
    Vn = np.concatenate(Vlist)
    Cn = np.concatenate(Clist)
    faces = []
    for a, b in use:
        if a not in q1 or b not in q1:
            continue
        faces.append([a, b, q1[b]])
        faces.append([a, q1[b], q1[a]])
        faces.append([q1[a], q1[b], q2[b]])
        faces.append([q1[a], q2[b], q2[a]])
    if not faces:
        return V, F, C, 0
    Fn = np.concatenate([F, np.array(faces, np.int64)])
    return Vn, Fn, Cn, len(faces)

def lod1(V, F, C, target_faces):
    m = trimesh.Trimesh(vertices=V, faces=F, process=False)
    target = int(np.clip(target_faces, 300, max(300, int(len(F) * 0.48))))
    try:
        s = m.simplify_quadric_decimation(face_count=target)
        if len(s.faces) < 50 or len(s.faces) > len(F) * 0.72:
            raise RuntimeError("bad decimation %d" % len(s.faces))
        sv = np.asarray(s.vertices, np.float64)
        sf = np.asarray(s.faces, np.int64)
    except Exception:
        step = 1
        while len(F[::step]) > target and step < 8:
            step += 1
        # vertex clustering fallback
        q = np.round(V / 2.2).astype(np.int64)
        # unique rows
        _, inv = np.unique(q, axis=0, return_inverse=True)
        sv = np.zeros((inv.max() + 1, 3))
        cnt = np.zeros(len(sv))
        np.add.at(sv, inv, V)
        np.add.at(cnt, inv, 1)
        sv /= cnt[:, None]
        sf = inv[F]
        ok = (sf[:, 0] != sf[:, 1]) & (sf[:, 1] != sf[:, 2]) & (sf[:, 2] != sf[:, 0])
        sf = sf[ok]
    from scipy.spatial import cKDTree
    _, ii = cKDTree(V).query(sv)
    return sv, sf, C[ii]

def process(region, name, path, pin, routes, origin, cell, H):
    s = trimesh.load(path, force="mesh", process=False)
    V = np.asarray(s.vertices, np.float64)
    F = np.asarray(s.faces, np.int64)
    C = np.asarray(s.visual.vertex_colors, np.float64) / 255.0
    if C.ndim != 2 or C.shape[1] != 4:
        C = np.concatenate([np.ones((len(V), 3)), np.ones((len(V), 1))], 1)
    island = "_isl_" in name
    loose = island or name == "arch_islands" or len(F) < 45000
    V0 = V.copy()
    nf0 = len(F)
    w, N, sd, boundary = weights(V, F, C, pin, island)
    # high-frequency energy before (mean |laplacian y| on steep verts)
    u, _ = unique_edges(F)
    acc = np.zeros(len(V)); cnt = np.zeros(len(V))
    np.add.at(acc, u[:, 0], V[u[:, 1], 1]); np.add.at(acc, u[:, 1], V[u[:, 0], 1])
    np.add.at(cnt, u[:, 0], 1); np.add.at(cnt, u[:, 1], 1)
    ydev0 = np.abs(V[:, 1] - acc / (cnt + 1e-9))
    steep0 = sd > 30
    dev_before = float(np.percentile(ydev0[steep0], 90)) if steep0.any() else 0.0
    peak0 = float(V[:, 1].max())
    mark = mark_faces(V, F, w, loose)
    V, F, C, w = subdivide(V, F, C, w, mark)
    if loose and len(F) < 90000:
        mark2 = mark_faces(V, F, w, True)
        # second pass only on still-long steep faces, small budget
        if mark2.sum() > 80:
            mark2_score_cap = min(int(mark2.sum()), int(0.12 * len(F)))
            fn = face_normals(V, F)
            mx = np.maximum(np.linalg.norm(V[F[:, 1]] - V[F[:, 0]], axis=1),
                            np.maximum(np.linalg.norm(V[F[:, 2]] - V[F[:, 1]], axis=1),
                                       np.linalg.norm(V[F[:, 0]] - V[F[:, 2]], axis=1)))
            score = np.where(mark2, mx, -1)
            if mark2.sum() > mark2_score_cap:
                idx = np.argpartition(score, -mark2_score_cap)[-mark2_score_cap:]
                m3 = np.zeros(len(F), bool); m3[idx] = True
                mark2 = m3
            V, F, C, w = subdivide(V, F, C, w, mark2)
    # refresh shore boost on new midpoints that inherited a free weight
    N = vnormals(V, F); sd = slope_deg(N)
    shore = (V[:, 1] > -0.5) & (V[:, 1] < 3.6) & (sd > 16) & (w > 0)
    w = np.where(shore, np.maximum(w, 0.82), w)
    pairs = 8 if region == "frost" and not island else (5 if not island else 4)
    lim = np.where(V0.shape[0] == len(V), 1.0, 1.0)  # placeholder, real lim per vert below
    # per-vertex clamp: shores stay close to the old waterline; ridges may round a few metres
    birth = V.copy()
    limv = np.where(birth[:, 1] < 6.0, 1.15, 4.0 if region == "frost" else 3.0)
    # taubin clamp uses birth positions; pass lim as array via a small wrapper
    u, _ = unique_edges(F)
    orig = birth
    for _it in range(pairs):
        for coef in (0.42, -0.45):
            acc = np.zeros_like(V); cnt = np.zeros(len(V))
            np.add.at(acc, u[:, 0], V[u[:, 1]]); np.add.at(acc, u[:, 1], V[u[:, 0]])
            np.add.at(cnt, u[:, 0], 1); np.add.at(cnt, u[:, 1], 1)
            mean = acc / (cnt[:, None] + 1e-9)
            V = V + coef * (mean - V) * w[:, None]
            V[w == 0] = orig[w == 0]
    dlt = V - orig
    L = np.linalg.norm(dlt, axis=1)
    sc = np.minimum(1.0, limv / (L + 1e-9))
    V = orig + dlt * sc[:, None]
    V[w == 0] = orig[w == 0]
    # gentle low-frequency shoulders on Archipelago and Ash island patches only (they were flat facets).
    # Frost and Saltglass get smoothing only: extra noise there is what read as corrugation / lumpiness.
    if island and region in ("A", "ash"):
        N = vnormals(V, F)
        disp = fbm(np.stack([V[:, 0] / 52.0, V[:, 1] / 20.0, V[:, 2] / 52.0], 1), 3, 11 if region == "A" else 23)
        amp = 0.75 if region == "A" else 0.6
        hn = N.copy(); hn[:, 1] = 0
        hn /= np.linalg.norm(hn, axis=1, keepdims=True) + 1e-9
        gate = (w > 0.55) & (V[:, 1] > 5.0)
        move = hn * (disp * amp)[:, None] + np.array([0, 1.0, 0]) * (np.clip(disp, 0, None) * 0.22 * amp)[:, None]
        move[~gate] = 0
        mv = np.linalg.norm(move, axis=1)
        move *= np.minimum(1.0, 1.0 / (mv + 1e-9))[:, None]
        V = V + move
        V[w == 0] = orig[w == 0]
    pin_at = pin[tuple(gidx(V[:, [0, 2]]).T)]
    # apron from the pinned coastline
    _, _, _, boundary = weights(V, F, C, pin, island) if False else (None, None, None, None)
    u, c = unique_edges(F)
    boundary = np.zeros(len(V), bool)
    boundary[np.unique(u[c == 1])] = True
    V, F, C, nskirt = add_apron(V, F, C, boundary, pin_at, name, region, origin, cell, H)
    terrain = C[:, 3] > 0.5
    pin_at = np.zeros(len(V), bool)
    pin_at[:min(len(pin_at), len(gidx(V[:, [0, 2]])))] = pin[tuple(gidx(V[:, [0, 2]]).T)]
    C = blur_color(V, C, terrain, pin_at, island)
    # shore tint on natural ground, not on routes / props
    y = V[:, 1]
    macro = fbm(np.stack([V[:, 0] / 40.0, np.zeros(len(V)), V[:, 2] / 40.0], 1), 2, 5)
    shore = np.clip((3.4 + macro * 1.3 - y) / 3.2, 0, 1) * terrain * (~pin_at)
    C[:, :3] = C[:, :3] * (1 - 0.42 * shore[:, None]) + WET[region] * (0.42 * shore[:, None])
    C = np.clip(C, 0, 1)
    N = vnormals(V, F)
    # stats versus the original vertex set (first len(V0) rows are the old verts, unmoved where w was 0)
    moved = np.linalg.norm(V[:len(V0)] - V0, axis=1)
    # route height check: grid before vs mesh after, sampled at route xz
    dh = 0.0
    nroute = 0
    for k, reg, pts in routes:
        if reg != region:
            continue
        # only routes that actually sit on this mesh's xz span
        bb0 = V0[:, [0, 2]].min(0) - 2; bb1 = V0[:, [0, 2]].max(0) + 2
        m = (pts[:, 0] >= bb0[0]) & (pts[:, 0] <= bb1[0]) & (pts[:, 1] >= bb0[1]) & (pts[:, 1] <= bb1[1])
        if not m.any():
            continue
        h0 = sample_h(origin, cell, H, pts[m])
        # after: nearest original-index vert in xz among pinned-ish
        from scipy.spatial import cKDTree
        tree = cKDTree(V[:len(V0)][:, [0, 2]])
        dd, ii = tree.query(pts[m])
        close = dd < 8
        if close.any():
            dh = max(dh, float(np.max(np.abs(V[ii[close], 1] - V0[ii[close], 1]))))
            nroute += int(close.sum())
    u, _ = unique_edges(F)
    acc = np.zeros(len(V)); cnt = np.zeros(len(V))
    np.add.at(acc, u[:, 0], V[u[:, 1], 1]); np.add.at(acc, u[:, 1], V[u[:, 0], 1])
    np.add.at(cnt, u[:, 0], 1); np.add.at(cnt, u[:, 1], 1)
    ydev = np.abs(V[:, 1] - acc / (cnt + 1e-9))
    N2 = vnormals(V, F); sd2 = slope_deg(N2)
    steep = sd2 > 30
    dev_after = float(np.percentile(ydev[steep], 90)) if steep.any() else 0.0
    peak1 = float(V[:, 1].max())
    od = os.path.join(ROOT, REG[region][0])
    os.makedirs(od, exist_ok=True)
    write_glb(os.path.join(od, name + ".glb"), V, F, C, N, name)
    # lod1 ~40% and never over half, colours transferred. Old land3 lod1 is the sawtooth shape, so it is not reused.
    sv, sf, sc = lod1(V, F, C, int(len(F) * 0.40))
    write_glb(os.path.join(od, name + "_lod1.glb"), sv, sf, sc, vnormals(sv, sf), name + "_lod1")
    st = dict(region=region, island=island, tris_before=nf0, tris_high=int(len(F)), tris_lod1=int(len(sf)),
              lod1_pct=round(100 * len(sf) / max(len(F), 1), 1),
              skirt_tris=int(nskirt), moved_verts=int((moved > 0.02).sum()),
              max_move_m=round(float(moved.max()), 3), route_max_dy_m=round(float(dh), 4),
              route_samples=nroute, ydev90_before=round(dev_before, 3), ydev90_after=round(dev_after, 3),
              peak_before=round(peak0, 2), peak_after=round(peak1, 2))
    print(f"{region} {name} {nf0}->{len(F)} lod1 {len(sf)} ({st['lod1_pct']}%) skirt {nskirt} "
          f"move {st['max_move_m']} routeDy {st['route_max_dy_m']} ydev {dev_before:.2f}->{dev_after:.2f} peak {peak0:.1f}->{peak1:.1f}",
          flush=True)
    return st

def main():
    only = sys.argv[1:]
    pin, routes = build_pins()
    stats = {}
    for region in REG:
        if only and region not in only and not any(a in region for a in only):
            # allow a mesh-name filter too
            pass
        files = terrain_files(region)
        if only and region not in only:
            files = [(b, p) for b, p in files if any(a in b for a in only)]
            if not files:
                continue
        elif only and region in only:
            pass
        print(f"== {region} {len(files)} meshes", flush=True)
        origin, cell, H = height_grid(region, terrain_files(region))
        for b, p in files:
            stats[b] = process(region, b, p, pin, routes, origin, cell, H)
    json.dump(stats, open(os.path.join(ROOT, "terrain_stats.json"), "w"), indent=1)
    # route safety summary
    bad = {k: v for k, v in stats.items() if v["route_max_dy_m"] > 0.2}
    print("ROUTE DY > 0.2m", bad or "none", flush=True)

if __name__ == "__main__":
    main()
