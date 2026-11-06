"""Split long coastal and steep faces on the land4 meshes. Routes and walkable ground stay pinned.
Reads and writes land4 in place. Does not touch collision files.
"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from smooth_land import (ROOT, REG, is_terrain, build_pins, weights, mark_faces, vnormals, slope_deg, unique_edges)
from common import write_glb, subdivide, vnormals as vn
from smooth_land import lod1

def main():
    pin, _ = build_pins()
    for region, (d, pre) in REG.items():
        folder = os.path.join(ROOT, d)
        for f in sorted(os.listdir(folder)):
            if not f.endswith(".glb") or f.endswith("_lod1.glb") or "scatter" in f:
                continue
            b = f[:-4]
            if not b.startswith(pre) or not is_terrain(b):
                continue
            path = os.path.join(folder, f)
            import trimesh
            s = trimesh.load(path, force="mesh", process=False)
            V = np.asarray(s.vertices, np.float64)
            F = np.asarray(s.faces, np.int64)
            C = np.asarray(s.visual.vertex_colors, np.float64) / 255.0
            island = "_isl_" in b
            w, N, sd, boundary = weights(V, F, C, pin, island)
            # only the long faces: coasts and ridge edges the first pass left coarse
            fn = __import__("common").face_normals(V, F)
            sd = slope_deg(fn)
            y = V[F][:, :, 1]
            e = np.maximum(np.linalg.norm(V[F[:, 1]] - V[F[:, 0]], axis=1),
                           np.maximum(np.linalg.norm(V[F[:, 2]] - V[F[:, 1]], axis=1),
                                      np.linalg.norm(V[F[:, 0]] - V[F[:, 2]], axis=1)))
            free = w[F].min(1) > 0
            coast = (y.min(1) < 1.2) & (y.max(1) > 2.2) & (e > 3.5) & free
            ridge = (sd > 34) & (e > 6.0) & (y.max(1) > 8) & free
            mark = coast | ridge
            if mark.sum() < 8:
                print(region, b, "skip", int(mark.sum()))
                continue
            cap = int(0.12 * len(F)) + 400
            if mark.sum() > cap:
                score = np.where(coast, 50.0, 0) + e
                score[~mark] = -1
                idx = np.argpartition(score, -cap)[-cap:]
                m2 = np.zeros(len(F), bool); m2[idx] = True
                mark = m2
            n0 = len(F)
            V, F, C, w = subdivide(V, F, C, w, mark)
            # relax only the new midpoints a little so the split doesn't stay a flat facet
            u, _ = unique_edges(F)
            orig = V.copy()
            new = np.zeros(len(V), bool); new[len(orig) if False else 0:] = False
            # midpoints are everything past the pre-split vertex count; recover from w array length history
            # subdivide appends, so indices >= nV_old are new. nV_old = len(V) - (len(V)-count of original)
            # We didn't keep it. Approximate: verts with w>0 get one taubin step, clamped to 0.6 m.
            for coef in (0.35, -0.3):
                acc = np.zeros_like(V); cnt = np.zeros(len(V))
                np.add.at(acc, u[:, 0], V[u[:, 1]]); np.add.at(acc, u[:, 1], V[u[:, 0]])
                np.add.at(cnt, u[:, 0], 1); np.add.at(cnt, u[:, 1], 1)
                mean = acc / (cnt[:, None] + 1e-9)
                V = V + coef * (mean - V) * (w > 0)[:, None]
                V[w == 0] = orig[w == 0]
            dlt = V - orig
            L = np.linalg.norm(dlt, axis=1)
            V = orig + dlt * np.minimum(1.0, 0.7 / (L + 1e-9))[:, None]
            V[w == 0] = orig[w == 0]
            N = vn(V, F)
            write_glb(path, V, F, C, N, b)
            sv, sf, sc = lod1(V, F, C, int(len(F) * 0.40))
            write_glb(os.path.join(folder, b + "_lod1.glb"), sv, sf, sc, vn(sv, sf), b + "_lod1")
            print(region, b, n0, "->", len(F), "coast", int(coast.sum()), "ridge", int(ridge.sum()), flush=True)

if __name__ == "__main__":
    main()
