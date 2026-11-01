"""Stage 10 (Beth): the Frost tiles were heavily decimated (edges up to 165 m, col up to 800 m), so pulling the land back
would stretch slivers across the island. Resample each tile (and the collision) onto a regular grid from the original
pre-island mesh (exact triangle interpolation of height and vertex colour), then the island carve is applied by carve_meshes.py.
Tiles 7.5 m grid, lod1 15 m (25%), terrain_col 20 m. Sources: meshes_v2_backup/ (originals). Output -> meshes/."""
import sys, numpy as np, trimesh
import matplotlib.tri as mtri
R = sys.argv[1] + '/stage4'
def interp(src, xs, zs):
    s = trimesh.load(src, force='scene'); n = s.graph.nodes_geometry[0]; xf, gn = s.graph[n]; g = s.geometry[gn]
    P = trimesh.transform_points(g.vertices, xf)
    X, Z = np.meshgrid(xs, zs); H = np.full(X.shape, -np.inf); vc = getattr(g.visual, 'vertex_colors', None)
    hasc = vc is not None and len(vc) == len(P); C = np.zeros(X.shape + (3,))
    x0, z0, st = xs[0], zs[0], xs[1] - xs[0]
    for f in g.faces:   # top-surface rasterisation (max y), barycentric height + colour
        A = P[f]; i0 = max(int(np.ceil((A[:, 0].min() - x0) / st)), 0); i1 = min(int(np.floor((A[:, 0].max() - x0) / st)), len(xs) - 1)
        j0 = max(int(np.ceil((A[:, 2].min() - z0) / st)), 0); j1 = min(int(np.floor((A[:, 2].max() - z0) / st)), len(zs) - 1)
        if i1 < i0 or j1 < j0: continue
        gx, gz = np.meshgrid(xs[i0:i1 + 1], zs[j0:j1 + 1])
        d = (A[1, 2] - A[2, 2]) * (A[0, 0] - A[2, 0]) + (A[2, 0] - A[1, 0]) * (A[0, 2] - A[2, 2])
        if abs(d) < 1e-9: continue
        l0 = ((A[1, 2] - A[2, 2]) * (gx - A[2, 0]) + (A[2, 0] - A[1, 0]) * (gz - A[2, 2])) / d
        l1 = ((A[2, 2] - A[0, 2]) * (gx - A[2, 0]) + (A[0, 0] - A[2, 0]) * (gz - A[2, 2])) / d; l2 = 1 - l0 - l1
        ins = (l0 >= -1e-6) & (l1 >= -1e-6) & (l2 >= -1e-6)
        if not ins.any(): continue
        y = l0 * A[0, 1] + l1 * A[1, 1] + l2 * A[2, 1]; sub = H[j0:j1 + 1, i0:i1 + 1]; up = ins & (y > sub)
        sub[up] = y[up]
        if hasc:
            cc = vc[f, :3].astype(float); cs = C[j0:j1 + 1, i0:i1 + 1]
            cs[up] = (l0[up, None] * cc[0] + l1[up, None] * cc[1] + l2[up, None] * cc[2])
    H[np.isinf(H)] = np.nan
    return X, Z, [H] + ([C[..., k] for k in range(3)] if hasc else [])
def grid_mesh(X, Z, Y, C):
    ok = ~np.isnan(Y); h, w = Y.shape; idx = np.arange(h * w).reshape(h, w)
    a, b, c, d = idx[:-1, :-1], idx[:-1, 1:], idx[1:, :-1], idx[1:, 1:]
    q = ok[:-1, :-1] & ok[:-1, 1:] & ok[1:, :-1] & ok[1:, 1:]
    F = np.r_[np.c_[a[q], c[q], b[q]], np.c_[b[q], c[q], d[q]]]
    V = np.c_[X.ravel(), np.nan_to_num(Y).ravel(), Z.ravel()]
    m = trimesh.Trimesh(V, F, process=False)
    if C is not None:
        col = np.c_[np.stack([np.nan_to_num(c, nan=200).ravel() for c in C], 1).clip(0, 255).astype(np.uint8), np.full(len(V), 255, np.uint8)]
        m.visual.vertex_colors = col
    m.remove_unreferenced_vertices(); return m
TX = [-2400, -1425, -450, 525, 1500]; TZ = [-3000, -2250, -1500]
import glob, trimesh as _t
from scipy.ndimage import uniform_filter, binary_closing, distance_transform_edt, gaussian_filter
sys.path.insert(0, __import__('os').path.dirname(__file__)); from island_carve import fbm, ss
def merged(name_glob):   # all original tiles into one mesh so tile seams sample identical heights
    ms = []
    for f in sorted(glob.glob(name_glob)):
        if '_grid' in f: continue
        sc = _t.load(f, force='scene'); n = sc.graph.nodes_geometry[0]; xf, gn = sc.graph[n]; g = sc.geometry[gn].copy(); g.apply_transform(xf); ms.append(g)
    m = _t.util.concatenate(ms); p = f'{R}/meshes_v2_backup/_merged_tmp.glb'; m.export(p); return p
def despeckle(X, Z, o):   # square speckled ice patches -> irregular patch edges
    C = np.stack(o[1:], -1); ok = ~np.isnan(o[0]); Cn = np.nan_to_num(C, nan=0.0)
    var = sum(uniform_filter(Cn[..., k] ** 2, 3) - uniform_filter(Cn[..., k], 3) ** 2 for k in range(3))
    S = binary_closing(var > 300, iterations=3) & ok
    if not S.any(): return o
    din = distance_transform_edt(S) * (X[0, 1] - X[0, 0])
    keep = ss(0, 35, din + 25 * fbm(X * 2.5, Z * 2.5, 1, 5) - 15)
    W = (~S & ok).astype(float); sur = np.stack([gaussian_filter(Cn[..., k] * W, 6) / np.maximum(gaussian_filter(W, 6), 1e-3) for k in range(3)], -1)
    C2 = C * keep[..., None] + sur * (1 - keep[..., None]); return [o[0]] + [C2[..., k] for k in range(3)]
for lod, step in (('', 7.5), ('_lod1', 15.0)):
    src = merged(f'{R}/meshes_v2_backup/frost_tile_x?z?{lod}.glb') if lod else merged(f'{R}/meshes_v2_backup/frost_tile_x?z?.glb')
    xs = np.arange(TX[0], TX[-1] + 0.01, step); zs = np.arange(TZ[0], TZ[-1] + 0.01, step)
    X, Z, o = interp(src, xs, zs)
    _, _, oc = interp(f'{R}/meshes_v2_backup/frost_terrain_col.glb', xs, zs); m_ = np.isnan(o[0]); o[0][m_] = oc[0][m_]
    for k in (1, 2, 3): o[k][m_] = (60, 80, 95)[k - 1]
    o = despeckle(X, Z, o)
    for i in range(4):
        for j in range(2):
            a = int(round((TX[i] - TX[0]) / step)); b_ = int(round((TX[i + 1] - TX[0]) / step)) + 1
            c = int(round((TZ[j] - TZ[0]) / step)); d = int(round((TZ[j + 1] - TZ[0]) / step)) + 1
            m = grid_mesh(X[c:d, a:b_], Z[c:d, a:b_], o[0][c:d, a:b_], [q[c:d, a:b_] for q in o[1:]])
            out = f'{R}/meshes_v2_backup/frost_tile_x{i}z{j}{lod}_grid.glb'; m.export(out); print(out.split('/')[-1], len(m.faces))
__import__('os').remove(f'{R}/meshes_v2_backup/_merged_tmp.glb')
xs = np.arange(-2400, 1500.01, 20.0); zs = np.arange(-3000, -1500 + 0.01, 20.0)
X, Z, o = interp(f'{R}/meshes_v2_backup/frost_terrain_col.glb', xs, zs)
m = grid_mesh(X, Z, o[0], None); m.export(f'{R}/meshes_v2_backup/frost_terrain_col_grid.glb'); print('col', len(m.faces))
