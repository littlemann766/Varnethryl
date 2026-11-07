"""Cutout foliage on the original trunks. Colliders are not opened.

Brown trunks, limbs and stone keep their vertices. Trunks get a cylindrical
UV into the bark photo. Green cones, bushes, grass and flowers become small
crossed cards into the foliage atlas, sitting in the same patch of air.
A tall piece is a pine: needle fans on a cone. A wide piece is a broadleaf
sprig cluster. Bushes sit on the old ground contact. trunk_bounds.json is
not rewritten.

Run this on the cone meshes (the geometry before the sphere and shell
passes). Running it twice rebuilds cards from cards and drifts.
"""
import os
import sys
import numpy as np
import trimesh
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components

sys.path.insert(0, os.path.dirname(__file__))
from common import write_glb

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Atlas is 4 columns by 2 rows. v=0 is the bottom of the image.
PINE_A, PINE_B, LEAF, BUSH, GRASS, FLOWER_Y, FLOWER_W, FLOWER_P = range(8)
KIND_FLAT, KIND_ROCK, KIND_BARK, KIND_LEAF = 0.05, 0.22, 0.45, 1.0


def components(F, n):
    rows = np.concatenate([F[:, 0], F[:, 1], F[:, 2]])
    cols = np.concatenate([F[:, 1], F[:, 2], F[:, 0]])
    g = csr_matrix((np.ones(len(rows), np.float32), (rows, cols)), shape=(n, n))
    return connected_components(g, directed=False)


def _rng(center, salt):
    return np.random.default_rng(int(abs(center[0] * 10 + center[2] * 3 + salt * 17)) % (2**31 - 1) or 1)


def cell_uvs(idx):
    """glTF stores v=0 at the top. Godot flips it on import."""
    c, r = idx % 4, idx // 4
    pad = 0.03
    u0, u1 = c / 4 + pad, (c + 1) / 4 - pad
    top = r / 2 + pad
    bot = (r + 1) / 2 - pad
    # origin, +right, +right+up, +up. Up points at the top of the cell.
    return [(u0, bot), (u1, bot), (u1, top), (u0, top)]


def classify(v, c):
    size = np.maximum(v.max(0) - v.min(0), 1e-4)
    mean = c.mean(0)
    green = mean[1] > mean[0] + 0.025 and mean[1] >= mean[2] - 0.03
    warm = (c[:, 0] > 0.4).mean() > 0.12 and mean[1] > 0.25 and mean[0] > mean[2]
    snow = mean.mean() > 0.62 and mean[2] + 0.02 >= mean[0] and size[1] < 6 and max(size[0], size[2]) < 5
    bark = mean[0] > mean[1] + 0.02 and mean[0] > 0.12 and size[1] > max(size[0], size[2]) * 0.85
    if bark or (not green and not warm and not snow):
        return "keep", size, mean
    if warm and size[1] < 1.6 and max(size[0], size[2]) < 1.4:
        return "flower", size, mean
    if size[1] < 1.15 and max(size[0], size[2]) < 1.15:
        return "grass", size, mean
    if size[1] < 2.4 and max(size[0], size[2]) < 3.2 and (green or snow):
        return "bush", size, mean
    return "canopy", size, mean


def _norm(v):
    n = np.linalg.norm(v)
    return v / n if n > 1e-8 else np.array([0.0, 1.0, 0.0])


def _rot(v, axis, ang):
    axis = _norm(axis)
    c, s = np.cos(ang), np.sin(ang)
    return v * c + np.cross(axis, v) * s + axis * np.dot(axis, v) * (1 - c)


class Mesh:
    def __init__(self):
        self.V, self.F, self.C, self.UV, self.N, self.T = [], [], [], [], [], []

    def card(self, origin, right, up, color, cell):
        nrm = np.cross(right, up)
        ln = np.linalg.norm(nrm)
        if ln < 1e-8:
            return
        nrm = nrm / ln
        uvs = cell_uvs(cell)
        corners = [origin, origin + right, origin + right + up, origin + up]
        base = len(self.V)
        tang = _norm(right)
        col = np.array(color, np.float64).reshape(-1)
        if col.shape[0] == 3:
            col = np.concatenate([col, [1.0]])
        for p, uv in zip(corners, uvs):
            self.V.append(np.array(p, np.float64))
            self.C.append(col.copy())
            self.UV.append(uv)
            self.N.append(nrm.copy())
            self.T.append([tang[0], tang[1], tang[2], 1.0])
        self.F += [[base, base + 1, base + 2], [base, base + 2, base + 3]]

    def cluster(self, center, right, up, color, cell):
        """Three cards around one centre so the clump has depth from the side."""
        axis = _norm(up)
        for ang in (0.0, 1.05, 2.15):
            r = right if ang == 0.0 else _rot(right, axis, ang)
            self.card(center - r * 0.5 - up * 0.5, r, up, color, cell)

    def twig(self, a, b, color):
        """A thin soft twig. Not a trunk: a few centimetres wide, no collider."""
        d = b - a
        ln = np.linalg.norm(d)
        if ln < 0.15:
            return
        up = d
        side = np.cross(d, np.array([0.0, 1.0, 0.0]))
        if np.linalg.norm(side) < 1e-4:
            side = np.cross(d, np.array([1.0, 0.0, 0.0]))
        side = _norm(side) * 0.045
        # Flat colour, a few centimetres wide. Not a bark-mapped trunk and not a collider.
        flat = np.array([0.34, 0.2, 0.09, KIND_FLAT])
        axis = _norm(d)
        self.card(a - side * 0.5, side, up, flat, 0)
        side2 = _rot(side, axis, 1.57)
        self.card(a - side2 * 0.5, side2, up, flat, 0)

    def arrays(self):
        if not self.V:
            return None
        return (np.asarray(self.V, np.float64), np.asarray(self.F, np.int64),
                np.asarray(self.C, np.float64), np.asarray(self.UV, np.float64),
                np.asarray(self.N, np.float64), np.asarray(self.T, np.float64))


def _count(size, lod, kind):
    h = max(float(size[1]), 0.3)
    r = max(float(size[0]), float(size[2]), 0.3) * 0.5
    # cover the old patch with overlapping sprigs, not a handful of cards
    cover = r * max(h, r * 0.8)
    if kind == "pine":
        lo, hi = (8, 14) if lod else (18, 34)
        div = 0.42 if lod else 0.16
    elif kind == "bush":
        lo, hi = (6, 10) if lod else (14, 22)
        div = 0.28 if lod else 0.11
    else:
        lo, hi = (7, 12) if lod else (18, 32)
        div = 0.36 if lod else 0.14
    return int(np.clip(cover / div, lo, hi)), h, r


def _twig_color(col):
    return np.array([0.32, 0.2, 0.1], np.float64)


def pine_cards(center, size, col, lod):
    n, h, r = _count(size, lod, "pine")
    rng = _rng(center, 1)
    m = Mesh()
    for i in range(n):
        t = ((i % max(n // 3, 1)) + 0.35) / max(n // 3, 1)
        shell = i % 3
        y = h * (0.05 + 0.9 * min(t, 1.0))
        rad = r * (1.08 - 0.9 * min(t, 1.0)) * (0.42 + 0.29 * shell)
        a = (i * 2.399) + rng.uniform(-0.2, 0.2)
        ca, sa = np.cos(a), np.sin(a)
        up = _norm(np.array([ca * 0.62, 0.55, sa * 0.62]))
        card = float(np.clip(0.28 + rad * 0.72, 0.34, 0.92))
        upv = up * card * rng.uniform(0.75, 1.05)
        right = _norm(np.cross(up, np.array([ca, 0.0, sa]))) * card * rng.uniform(0.85, 1.1)
        ctr = np.array([ca, 0.0, sa]) * rad + np.array([0.0, y, 0.0])
        m.cluster(ctr, right, upv, col, PINE_A if i % 2 == 0 else PINE_B)
    if not lod:
        wood = _twig_color(col)
        for i in range(3):
            a = i / 3 * 6.283 + 0.4
            tip = np.array([np.cos(a) * r * 0.55, h * (0.35 + 0.15 * i), np.sin(a) * r * 0.55])
            m.twig(np.array([0.0, h * 0.08, 0.0]), tip, wood)
    return _place(m, center, size)


def broad_cards(center, size, col, lod, grounded):
    n, h, r = _count(size, lod, "bush" if grounded else "broad")
    rng = _rng(center, 2)
    m = Mesh()
    cell = BUSH if grounded else LEAF
    for i in range(n):
        shell = i % 3
        a = (i * 2.399) + rng.uniform(-0.25, 0.25)
        ca, sa = np.cos(a), np.sin(a)
        dist = r * (0.2 + 0.28 * shell) * rng.uniform(0.85, 1.05)
        if grounded:
            y = h * rng.uniform(0.02, 0.55)
        else:
            y = h * (0.15 + 0.75 * rng.random() * (0.55 + 0.2 * shell))
        up = _norm(np.array([ca * 0.15, 1.0, sa * 0.15]))
        card = float(np.clip(0.32 + r * (0.28 if grounded else 0.22), 0.36, 0.85 if grounded else 1.05))
        upv = up * card * rng.uniform(0.8, 1.15)
        right = _norm(np.array([-sa, 0.0, ca])) * card * rng.uniform(0.85, 1.15)
        ctr = np.array([ca * dist, y + card * 0.15, sa * dist])
        if grounded:
            ctr[1] = max(ctr[1], card * 0.25)
        m.cluster(ctr, right, upv, col, cell)
    if not grounded and not lod:
        wood = _twig_color(col)
        for i in range(4):
            a = i / 4 * 6.283
            tip = np.array([np.cos(a) * r * 0.7, h * rng.uniform(0.35, 0.75), np.sin(a) * r * 0.7])
            m.twig(np.array([0.0, h * 0.05, 0.0]), tip, wood)
    return _place(m, center, size)


def grass_cards(center, size, col, lod, flower):
    h = max(float(size[1]), 0.22)
    r = max(float(max(size[0], size[2])) * 0.45, 0.12)
    rng = _rng(center, 3)
    m = Mesh()
    n = 3 if lod else 6
    for i in range(n):
        a = i / n * np.pi + rng.uniform(-0.2, 0.2)
        card_w = r * rng.uniform(0.7, 1.15)
        right = np.array([np.cos(a), 0.0, np.sin(a)]) * card_w
        lean = rng.uniform(-0.15, 0.15)
        up = np.array([lean, h * rng.uniform(0.85, 1.1), lean * 0.5])
        origin = np.array([rng.uniform(-r, r) * 0.3, 0.0, rng.uniform(-r, r) * 0.3]) - right * 0.5
        m.card(origin, right, up, col, GRASS)
    if flower is not None:
        fw = max(h * 0.55, 0.16)
        fh = fw * 0.95
        cell = FLOWER_W if flower.mean() > 0.72 else (FLOWER_P if flower[0] > flower[1] + 0.08 else FLOWER_Y)
        for i in range(3):
            a = i * 1.15 + 0.3
            scale = 0.72 if i == 2 else 1.0
            right = np.array([np.cos(a), 0.0, np.sin(a)]) * fw * scale
            up = np.array([0.04 * i, fh * scale, 0.02])
            origin = np.array([0.0, h * (0.62 + 0.08 * i), 0.0]) - right * 0.5 - up * 0.2
            m.card(origin, right, up, flower, cell)
    return _place(m, center, size)


def _place(m, center, size):
    arr = m.arrays()
    if arr is None:
        return None
    V, F, C, UV, N, T = arr
    V = V.copy()
    V[:, 0] += center[0]
    V[:, 2] += center[2]
    V[:, 1] += center[1] - size[1] * 0.5
    return V, F, C, UV, N, T


def bark_frame(v, nrm):
    """Cylindrical UV along the piece, vertices untouched."""
    c = v.mean(0)
    x = v - c
    cov = (x.T @ x) / max(len(v), 1)
    _, evecs = np.linalg.eigh(cov)
    axis = evecs[:, -1].copy()
    along = x @ axis
    if along[np.argmax(np.abs(along))] < 0 and v[np.argmax(v[:, 1])] @ axis < c @ axis:
        axis = -axis
        along = -along
    tmp = np.array([1.0, 0.0, 0.0]) if abs(axis[0]) < 0.85 else np.array([0.0, 0.0, 1.0])
    b = np.cross(axis, tmp)
    b /= np.linalg.norm(b) + 1e-12
    p = np.cross(axis, b)
    pu, pv = x @ b, x @ p
    ang = np.arctan2(pu, pv)
    rad = float(np.sqrt(pu ** 2 + pv ** 2).mean())
    repeats = float(np.clip(2 * np.pi * max(rad, 0.08) / 0.42, 2.0, 8.0))
    u = ang / (2 * np.pi) * repeats
    vv = along / 0.48
    uv = np.stack([u, vv], 1)
    # tangent follows U (around the trunk) and stays perpendicular to the mesh normal
    tang = np.cross(axis, nrm)
    ln = np.linalg.norm(tang, axis=1, keepdims=True)
    bad = ln[:, 0] < 1e-6
    tang = tang / (ln + 1e-12)
    if bad.any():
        tang[bad] = b
    T = np.concatenate([tang, np.ones((len(v), 1))], 1)
    return uv.astype(np.float64), T.astype(np.float64)


def solid_tag(v, mean):
    size = np.maximum(v.max(0) - v.min(0), 1e-4)
    sat = float(mean.max() - mean.min())
    tall = size[1] > max(size[0], size[2]) * 0.75
    brown = mean[0] > mean[1] + 0.015 and mean[0] > 0.1
    dark_wood = float(mean.mean()) < 0.25 and tall
    if brown or dark_wood:
        return KIND_BARK
    if sat > 0.28 and not tall:
        return KIND_FLAT
    return KIND_ROCK


def rebuild(V, F, C, N, lod=False):
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
        v, c, n = V[sel], C[sel, :3], N[sel]
        ff = remap[faces]
        kind, size, mean = classify(v, c)
        center = (v.min(0) + v.max(0)) * 0.5
        pieces.append((kind, size, mean, center, v, c, n, ff))
        if kind == "keep" and size[1] > 2.0:
            trunks.append((center, v.min(0), v.max(0), mean))
    wood = [(t[0], t[1][1]) for t in trunks]
    out = Mesh()
    for kind, size, mean, center, v, c, n, ff in pieces:
        if kind in ("grass", "flower"):
            for wc, ymin in wood:
                if abs(center[0] - wc[0]) < 18.0 and abs(center[2] - wc[2]) < 18.0 and center[1] > ymin + 1.3:
                    kind = "canopy"
                    break
        if kind == "keep":
            tag = solid_tag(v, mean)
            base = len(out.V)
            out.V += list(v)
            out.C += list(np.concatenate([c, np.full((len(v), 1), tag)], 1))
            out.N += list(n)
            if tag == KIND_BARK:
                uv, T = bark_frame(v, n)
            else:
                uv = np.zeros((len(v), 2))
                T = np.tile([1.0, 0.0, 0.0, 1.0], (len(v), 1))
            out.UV += list(uv)
            out.T += list(T)
            out.F += list(ff + base)
            continue
        flower = None
        if kind == "flower":
            tips = c[c[:, 0] > 0.4]
            flower = tips.mean(0) if len(tips) else np.array([0.85, 0.72, 0.28])
        horiz = max(float(size[0]), float(size[2]))
        if kind in ("grass", "flower"):
            built = grass_cards(center, size, mean, lod, flower)
        elif kind == "bush" or horiz > float(size[1]) * 1.15:
            built = broad_cards(center, size, mean, lod, kind == "bush")
        else:
            built = pine_cards(center, size, mean, lod)
        if built is None:
            continue
        nv, nf, nc, nu, nn, nt = built
        base = len(out.V)
        out.V += list(nv)
        if nc.shape[1] == 3:
            nc = np.concatenate([nc, np.ones((len(nc), 1))], 1)
        out.C += list(nc)
        out.UV += list(nu)
        out.N += list(nn)
        out.T += list(nt)
        out.F += list(nf + base)
    if not out.V:
        return None
    return (np.asarray(out.V, np.float32), np.asarray(out.F, np.int64),
            np.asarray(out.C, np.float32), np.asarray(out.UV, np.float32),
            np.asarray(out.N, np.float32), np.asarray(out.T, np.float32), trunks)


def face_normals(V, F, fallback):
    N = np.array(fallback, np.float64, copy=True)
    if len(F) == 0:
        return N
    fn = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
    acc = np.zeros_like(V)
    for i in range(3):
        np.add.at(acc, F[:, i], fn)
    ln = np.linalg.norm(acc, axis=1)
    good = ln > 1e-8
    # only fill missing; keep the authored trunk normals
    missing = np.linalg.norm(N, axis=1) < 1e-6
    N[missing & good] = acc[missing & good] / ln[missing & good, None]
    still = np.linalg.norm(N, axis=1) < 1e-6
    N[still] = np.array([0.0, 1.0, 0.0])
    return N


def main():
    records = []
    nfiles = 0
    faces = 0
    for dp, _, fs in os.walk(ROOT):
        for f in sorted(fs):
            if "land_scatter" not in f or not f.endswith(".glb") or f.endswith("_col.glb"):
                continue
            path = os.path.join(dp, f)
            m = trimesh.load(path, force="mesh", process=False)
            V = np.asarray(m.vertices, np.float64)
            F = np.asarray(m.faces, np.int64)
            C = np.asarray(m.visual.vertex_colors, np.float64) / 255.0
            if C.shape[1] == 3:
                C = np.concatenate([C, np.ones((len(C), 1))], 1)
            try:
                authored = np.asarray(m.vertex_normals, np.float64)
                if len(authored) != len(V):
                    authored = np.zeros_like(V)
            except Exception:
                authored = np.zeros_like(V)
            N = face_normals(V, F, authored)
            lod = f.endswith("_lod1.glb")
            built = rebuild(V, F, C, N, lod=lod)
            if built is None:
                continue
            V2, F2, C2, UV, N2, T, trunks = built
            write_glb(path, V2, F2.astype(np.uint32), C2, N2, UV, T, f[:-4])
            nfiles += 1
            if not lod:
                faces += len(F2)
                rel = os.path.relpath(path, ROOT)
                for center, mn, mx, mean in trunks:
                    records.append(dict(
                        file=rel,
                        centroid=[round(float(x), 3) for x in center],
                        aabb_min=[round(float(x), 3) for x in mn],
                        aabb_max=[round(float(x), 3) for x in mx],
                        mean_rgb=[round(float(x), 3) for x in mean],
                    ))
    print("files", nfiles, "high faces", faces, "kept tall pieces", len(records))


if __name__ == "__main__":
    main()
