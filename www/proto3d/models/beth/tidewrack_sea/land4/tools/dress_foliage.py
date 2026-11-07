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
        col = np.array(color, np.float64)
        for p, uv in zip(corners, uvs):
            self.V.append(np.array(p, np.float64))
            self.C.append(col.copy())
            self.UV.append(uv)
            self.N.append(nrm.copy())
            self.T.append([tang[0], tang[1], tang[2], 1.0])
        self.F += [[base, base + 1, base + 2], [base, base + 2, base + 3]]

    def crossed(self, origin, right, up, color, cell, twist=1.15):
        center = origin + right * 0.5 + up * 0.5
        self.card(center - right * 0.5 - up * 0.5, right, up, color, cell)
        r2 = _rot(right, _norm(up), twist)
        self.card(center - r2 * 0.5 - up * 0.5, r2, up, color, cell)

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
        lo, hi = (7, 12) if lod else (16, 28)
        div = 0.48 if lod else 0.22
    elif kind == "bush":
        lo, hi = (6, 9) if lod else (12, 18)
        div = 0.32 if lod else 0.14
    else:
        lo, hi = (6, 10) if lod else (16, 26)
        div = 0.42 if lod else 0.18
    return int(np.clip(cover / div, lo, hi)), h, r


def pine_cards(center, size, col, lod):
    n, h, r = _count(size, lod, "pine")
    rng = _rng(center, 1)
    m = Mesh()
    for i in range(n):
        t = (i + 0.35) / n
        y = h * (0.08 + 0.86 * t)
        rad = r * (1.02 - 0.86 * t) * (0.55 if i % 3 == 0 else 0.92)
        a = rng.uniform(0, 6.283)
        ca, sa = np.cos(a), np.sin(a)
        radial = np.array([ca, 0.0, sa])
        # droop outward so the tier reads as a bough, not a vertical plane
        up = _norm(np.array([ca * 0.55, 0.72, sa * 0.55]))
        card = float(np.clip(max(rad, 0.45) * 1.25, 0.5, 1.7))
        upv = up * card * 0.85
        right = _norm(np.cross(up, radial)) * card
        origin = radial * rad + np.array([0.0, y, 0.0]) - right * 0.5 - upv * 0.45
        cell = PINE_A if i % 2 == 0 else PINE_B
        m.crossed(origin, right, upv, col, cell, twist=rng.uniform(0.9, 1.4))
    return _place(m, center, size)


def broad_cards(center, size, col, lod, grounded):
    n, h, r = _count(size, lod, "bush" if grounded else "broad")
    rng = _rng(center, 2)
    m = Mesh()
    cell = BUSH if grounded else LEAF
    for i in range(n):
        a = rng.uniform(0, 6.283)
        ca, sa = np.cos(a), np.sin(a)
        dist = r * rng.uniform(0.15, 0.88)
        y = h * (rng.uniform(0.02, 0.25) if grounded else rng.uniform(0.2, 0.85))
        up = _norm(np.array([ca * 0.25, 1.0, sa * 0.25]))
        card = float(np.clip(max(r, 0.4) * rng.uniform(0.72, 1.05), 0.42, 1.15 if grounded else 1.75))
        upv = up * card * (0.7 if grounded else 0.62)
        right = _norm(np.array([-sa, 0.0, ca])) * card
        origin = np.array([ca * dist, y, sa * dist]) - right * 0.5
        if grounded:
            origin[1] = max(origin[1], 0.0)
        m.crossed(origin, right, upv, col, cell, twist=rng.uniform(0.8, 1.3))
    return _place(m, center, size)


def grass_cards(center, size, col, lod, flower):
    h = max(float(size[1]), 0.22)
    r = max(float(max(size[0], size[2])) * 0.45, 0.12)
    rng = _rng(center, 3)
    m = Mesh()
    n = 2 if lod else 3
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
        for i in range(2):
            a = i * 1.2 + 0.4
            right = np.array([np.cos(a), 0.0, np.sin(a)]) * fw
            up = np.array([0.05, fh, 0.0])
            origin = np.array([0.0, h * 0.72, 0.0]) - right * 0.5 - up * 0.15
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
    repeats = float(np.clip(2 * np.pi * max(rad, 0.08) / 0.9, 1.0, 5.0))
    u = ang / (2 * np.pi) * repeats
    vv = along / 0.85
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
        rgba = np.concatenate([nc, np.ones((len(nv), 1))], 1)
        out.C += list(rgba)
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
