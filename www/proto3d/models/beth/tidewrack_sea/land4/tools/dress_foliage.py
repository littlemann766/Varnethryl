"""Replace cone canopies, block bushes and spike flowers. Trunks and rocks stay.

Each scatter glb is many separate pieces. Brown trunks, limbs and stone are
copied vertex for vertex, so the collider boxes still meet the same wood and
rock. Green cones, bushes, tufts and flower spikes are rebuilt as clusters
that occupy the same patch of air. Collider glbs are not opened.
"""
import os, sys
import numpy as np
import trimesh
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components

sys.path.insert(0, os.path.dirname(__file__))
from common import write_glb, vnormals

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def components(F, n):
    rows = np.concatenate([F[:, 0], F[:, 1], F[:, 2]])
    cols = np.concatenate([F[:, 1], F[:, 2], F[:, 0]])
    g = csr_matrix((np.ones(len(rows), np.float32), (rows, cols)), shape=(n, n))
    return connected_components(g, directed=False)


def ico(sub):
    s = trimesh.creation.icosphere(subdivisions=sub)
    return np.asarray(s.vertices, np.float64), np.asarray(s.faces, np.int64)


ICO_HI = ico(1)
ICO_LO = ico(0)


def shade(V, base):
    y = V[:, 1]
    t = (y - y.min()) / (np.ptp(y) + 1e-6)
    col = np.array(base, np.float64) * (0.62 + 0.55 * t)[:, None]
    # underside a little darker and bluer so a clump is not one flat green
    col[:, 2] += (1 - t) * 0.03
    return np.clip(col, 0, 1)


def cluster(center, size, base_col, n_blobs, flower_col=None, ico=None):
    ico = ICO_HI if ico is None else ico
    rng = np.random.default_rng(int(abs(center[0] * 10 + center[2] * 3)) % (2**31 - 1) or 1)
    parts_v, parts_f, parts_c = [], [], []
    for i in range(n_blobs):
        v = ico[0] * np.array([
            size[0] * rng.uniform(0.28, 0.48),
            size[1] * rng.uniform(0.22, 0.42),
            size[2] * rng.uniform(0.28, 0.48),
        ])
        off = np.array([
            rng.uniform(-0.22, 0.22) * size[0],
            rng.uniform(-0.05, 0.18) * size[1],
            rng.uniform(-0.22, 0.22) * size[2],
        ])
        parts_v.append(v + off)
        parts_f.append(ico[1])
        parts_c.append(shade(v + off, base_col * rng.uniform(0.85, 1.08)))
    if flower_col is not None:
        v = ICO_LO[0] * (max(size) * 0.16)
        v[:, 1] += size[1] * 0.42
        parts_v.append(v)
        parts_f.append(ICO_LO[1])
        parts_c.append(np.tile(np.clip(flower_col, 0, 1), (len(v), 1)))
    return _fit(parts_v, parts_f, parts_c, center, size)


def blades(center, size, base_col, n, flower_col=None):
    rng = np.random.default_rng(int(abs(center[0] * 7 + center[2] * 11)) % (2**31 - 1) or 1)
    h = max(float(size[1]), 0.25)
    r = max(float(max(size[0], size[2])) * 0.55, 0.12)
    V, F, C = [], [], []
    for i in range(n):
        a = i / n * 6.283 + rng.random() * 0.4
        lean = rng.uniform(0.15, 0.55)
        w = r * rng.uniform(0.08, 0.16)
        x, z = np.cos(a), np.sin(a)
        px, pz = -z, x
        b0 = np.array([x * r * 0.15, 0, z * r * 0.15])
        tip = np.array([x * r * lean, h * rng.uniform(0.75, 1.05), z * r * lean])
        p1 = b0 + np.array([px, 0, pz]) * w
        p2 = b0 - np.array([px, 0, pz]) * w
        o = len(V)
        V += [p1, p2, tip]
        F += [[o, o + 1, o + 2]]
        col = base_col * rng.uniform(0.8, 1.15)
        C += [col * 0.75, col * 0.75, np.clip(col * 1.25, 0, 1)]
    if flower_col is not None:
        v = ICO_LO[0] * (r * 0.22)
        v[:, 1] += h * 0.92
        o = len(V)
        V += list(v)
        F += list(ICO_LO[1] + o)
        C += list(np.tile(np.clip(flower_col, 0, 1), (len(v), 1)))
    V = np.array(V, np.float64)
    # sit the clump on the old bottom, centered in xz
    V[:, 0] += center[0]
    V[:, 2] += center[2]
    V[:, 1] += center[1] - size[1] * 0.5
    return V, np.array(F, np.int64), np.array(C, np.float64)


def _fit(parts_v, parts_f, parts_c, center, size):
    V = np.concatenate(parts_v)
    F = []
    o = 0
    for v, f in zip(parts_v, parts_f):
        F.append(f + o)
        o += len(v)
    F = np.concatenate(F)
    C = np.concatenate(parts_c)
    # map the generated cloud onto the old box so it stays in that plant's patch
    mn, mx = V.min(0), V.max(0)
    ext = np.maximum(mx - mn, 1e-4)
    V = (V - (mn + mx) * 0.5) / ext * size + center
    return V, F, C


def classify(v, c):
    size = np.maximum(v.max(0) - v.min(0), 1e-4)
    mean = c.mean(0)
    green = mean[1] > mean[0] + 0.025 and mean[1] >= mean[2] - 0.03
    warm = (c[:, 0] > 0.45).mean() > 0.15 and mean[1] > 0.25
    snow = mean.mean() > 0.62 and mean[2] + 0.02 >= mean[0] and size[1] < 5 and max(size[0], size[2]) < 4
    bark = mean[0] > mean[1] + 0.02 and mean[0] > 0.12 and size[1] > max(size[0], size[2])
    if bark or (not green and not warm and not snow):
        return "keep", size, mean
    if warm and size[1] < 1.6:
        return "flower", size, mean
    if size[1] < 1.15 and max(size[0], size[2]) < 1.1:
        return "grass", size, mean
    if size[1] < 2.4 and max(size[0], size[2]) < 3.2 and green:
        return "bush", size, mean
    return "canopy", size, mean


def rebuild(V, F, C, lod=False):
    nlab, labels = components(F, len(V))
    pieces = []
    trunks = []
    for lab in range(nlab):
        sel = np.nonzero(labels == lab)[0]
        faces = F[np.isin(F, sel).all(1)]
        if len(faces) == 0:
            continue
        remap = -np.ones(len(V), np.int64)
        remap[sel] = np.arange(len(sel))
        v, c = V[sel], C[sel, :3]
        ff = remap[faces]
        kind, size, mean = classify(v, c)
        center = (v.min(0) + v.max(0)) * 0.5
        pieces.append((kind, size, mean, center, v, c, ff))
        if kind == "keep" and size[1] > 2.0:
            trunks.append((center, v.min(0), v.max(0), mean))
    # A small green piece sitting up in a trunk is a branch tuft, not ground grass.
    wood = [(t[0], t[1][1]) for t in trunks]
    out_v, out_f, out_c = [], [], []
    o = 0
    for kind, size, mean, center, v, c, ff in pieces:
        if kind in ("grass", "flower"):
            for wc, ymin in wood:
                if abs(center[0] - wc[0]) < 2.4 and abs(center[2] - wc[2]) < 2.4 and center[1] > ymin + 1.2:
                    kind = "canopy"
                    break
        if kind == "keep":
            out_v.append(v)
            out_f.append(ff + o)
            out_c.append(c)
            o += len(v)
            continue
        flower = None
        if kind == "flower":
            tips = c[c[:, 0] > 0.4]
            flower = tips.mean(0) if len(tips) else np.array([0.85, 0.72, 0.28])
        nblob = 2 if lod else (4 if kind == "bush" else 3)
        # Canopies are numerous, so they stay the coarser sphere. Bushes are few and read at eye height.
        ico = ICO_LO if lod or kind == "canopy" else ICO_HI
        if kind in ("grass", "flower"):
            nv, nf, nc = blades(center, size, mean, 5 if lod else 9, flower)
        else:
            # cones are flat; give the clump some body or it stays a slab
            horiz = max(float(size[0]), float(size[2]), 0.35)
            tall = max(float(size[1]), horiz * (0.5 if kind == "bush" else 0.62))
            box = np.array([horiz, tall, horiz])
            nv, nf, nc = cluster(center, box, mean, nblob, None, ico)
            nv = nv.copy()
            nv[:, 1] += float(v[:, 1].min() - nv[:, 1].min())
        out_v.append(nv)
        out_f.append(nf + o)
        out_c.append(nc)
        o += len(nv)
    if not out_v:
        return V, F, C[:, :3], []
    return np.concatenate(out_v), np.concatenate(out_f), np.concatenate(out_c), trunks


def main():
    records = []
    nfiles = 0
    for dp, _, fs in os.walk(ROOT):
        for f in sorted(fs):
            if "land_scatter" not in f or not f.endswith(".glb") or f.endswith("_col.glb"):
                continue
            path = os.path.join(dp, f)
            m = trimesh.load(path, force="mesh", process=False)
            V = np.asarray(m.vertices, np.float64)
            F = np.asarray(m.faces, np.int64)
            C = np.asarray(m.visual.vertex_colors, np.float64) / 255.0
            lod = f.endswith("_lod1.glb")
            V2, F2, C2, trunks = rebuild(V, F, C, lod=lod)
            Ca = np.concatenate([np.clip(C2, 0, 1), np.zeros((len(C2), 1))], 1)
            N = vnormals(V2, F2)
            write_glb(path, V2.astype(np.float32), F2.astype(np.uint32), Ca.astype(np.float32), N.astype(np.float32), f[:-4])
            nfiles += 1
            if not lod:
                rel = os.path.relpath(path, ROOT)
                for center, mn, mx, mean in trunks:
                    records.append(dict(
                        file=rel,
                        centroid=[round(float(x), 3) for x in center],
                        aabb_min=[round(float(x), 3) for x in mn],
                        aabb_max=[round(float(x), 3) for x in mx],
                        mean_rgb=[round(float(x), 3) for x in mean],
                    ))
    import json
    json.dump(records, open(os.path.join(ROOT, "trunk_bounds.json"), "w"))
    print("files", nfiles, "trunk records", len(records))


if __name__ == "__main__":
    main()
