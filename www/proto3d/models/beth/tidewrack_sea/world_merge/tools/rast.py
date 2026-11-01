"""Top-down max-height rasteriser for terrain GLBs (shared by shore_maps.py and isl_blend.py)."""
import numpy as np, trimesh
def raster(files, r, px):
    w, h = int(round(r[2] / px)), int(round(r[3] / px)); xs = r[0] + (np.arange(w) + 0.5) * px; zs = r[1] + (np.arange(h) + 0.5) * px
    Hm = np.full((h, w), -99.0)
    for f in files:
        s = trimesh.load(f, force='scene')
        for node in s.graph.nodes_geometry:
            xf, gn = s.graph[node]; g = s.geometry[gn]; P = trimesh.transform_points(g.vertices, xf); A = P[g.faces]
            i0 = np.ceil((A[:, :, 0].min(1) - xs[0]) / px).astype(int); i1 = np.floor((A[:, :, 0].max(1) - xs[0]) / px).astype(int)
            j0 = np.ceil((A[:, :, 2].min(1) - zs[0]) / px).astype(int); j1 = np.floor((A[:, :, 2].max(1) - zs[0]) / px).astype(int)
            for t in np.where((i1 >= np.maximum(i0, 0)) & (j1 >= np.maximum(j0, 0)) & (i0 < w) & (j0 < h) & (A[:, :, 1].max(1) > -0.5))[0]:
                a = A[t]; ia, ib, ja, jb = max(i0[t], 0), min(i1[t], w - 1), max(j0[t], 0), min(j1[t], h - 1)
                gx, gz = np.meshgrid(xs[ia:ib + 1], zs[ja:jb + 1])
                d = (a[1, 2] - a[2, 2]) * (a[0, 0] - a[2, 0]) + (a[2, 0] - a[1, 0]) * (a[0, 2] - a[2, 2])
                if abs(d) < 1e-9: continue
                l0 = ((a[1, 2] - a[2, 2]) * (gx - a[2, 0]) + (a[2, 0] - a[1, 0]) * (gz - a[2, 2])) / d
                l1 = ((a[2, 2] - a[0, 2]) * (gx - a[2, 0]) + (a[0, 0] - a[2, 0]) * (gz - a[2, 2])) / d; l2 = 1 - l0 - l1
                ins = (l0 >= -1e-6) & (l1 >= -1e-6) & (l2 >= -1e-6); y = l0 * a[0, 1] + l1 * a[1, 1] + l2 * a[2, 1]
                sub = Hm[ja:jb + 1, ib - (ib - ia):ib + 1]; np.maximum(sub, np.where(ins, y, -99.0), out=sub)
    return Hm
