"""Give existing flowers thickness, and make low-tier crowns one shape.

High tree cards are not rewritten. Flowers stay on the cards that are
already there: one head becomes three crossed faces so the side is not a
disk. Low-tier leaf cards are replaced, inside the same crown box, by fewer
larger fans that overlap. Grass, trunks, ground, and colliders stay.
"""
import json
import os
import struct
import sys
from collections import defaultdict

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

sys.path.insert(0, os.path.dirname(__file__))
from common import write_glb
from dress_foliage import (
    BUSH, FLOWER_P, FLOWER_W, FLOWER_Y, LEAF, Mesh, PINE_A, PINE_B, _norm, _rot,
)

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ATLAS = os.path.join(ROOT, "textures", "foliage_atlas.png")
CELL = 512


def _soft_petal(layer, cx, cy, n, length, width, color, center, turn=0.0):
    """Petals with a shaded base and no stroke, so the head is not an outline."""
    for i in range(n):
        ang = turn + i / n * 360.0
        pet = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
        d = ImageDraw.Draw(pet)
        d.ellipse([cx - width, cy - length, cx + width, cy - width * 0.2], fill=color)
        arr = np.asarray(pet).astype(np.float32)
        y, x = np.mgrid[0:CELL, 0:CELL]
        along = np.clip((cy - y) / max(length, 1), 0, 1)
        shade = 0.78 + 0.28 * along
        arr[:, :, :3] *= shade[:, :, None]
        edge = np.clip((arr[:, :, 3] - 18) / 40.0, 0, 1)
        arr[:, :, 3] *= edge
        pet = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")
        pet = pet.rotate(ang, center=(cx, cy), resample=Image.Resampling.BICUBIC)
        layer.alpha_composite(pet)
    d = ImageDraw.Draw(layer)
    r = max(11, int(width * 0.36))
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=center)
    hi = tuple(min(255, c + 36) if k < 3 else c for k, c in enumerate(center))
    d.ellipse([cx - r // 3, cy - r // 3, cx + r // 3, cy + r // 4], fill=hi)


def paint_flowers():
    im = Image.open(ATLAS).convert("RGBA")
    arr = np.asarray(im).copy()
    for c in (1, 2, 3):
        arr[CELL:CELL * 2, c * CELL:(c + 1) * CELL] = 0
    base = Image.fromarray(arr, "RGBA")
    cup = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
    _soft_petal(cup, 256, 268, 5, 132, 48, (232, 176, 46, 255), (98, 58, 18, 255), -12)
    daisy = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
    _soft_petal(daisy, 256, 250, 6, 168, 26, (244, 240, 228, 255), (214, 164, 42, 255), 8)
    sprig = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
    _soft_petal(sprig, 210, 150, 5, 72, 26, (196, 78, 104, 255), (110, 32, 52, 255))
    _soft_petal(sprig, 320, 210, 5, 52, 18, (176, 64, 92, 255), (100, 28, 46, 255), 18)
    _soft_petal(sprig, 250, 300, 5, 44, 15, (214, 118, 136, 255), (124, 44, 60, 255), 6)
    for col, layer in enumerate((cup, daisy, sprig), start=1):
        a = np.asarray(layer)
        opaque = a[:, :, 3] > 8
        if opaque.any():
            _, idx = ndimage.distance_transform_edt(~opaque, return_indices=True)
            a = a.copy()
            a[:, :, :3] = a[:, :, :3][idx[0], idx[1]]
            a[:6, :, 3] = 0
            a[-6:, :, 3] = 0
            a[:, :6, 3] = 0
            a[:, -6:, 3] = 0
            layer = Image.fromarray(a, "RGBA")
        base.paste(layer, (col * CELL, CELL), layer)
    base.save(ATLAS)


def load_full(path):
    with open(path, "rb") as f:
        struct.unpack("<III", f.read(12))
        clen, _ = struct.unpack("<II", f.read(8))
        js = json.loads(f.read(clen))
        blen, _ = struct.unpack("<II", f.read(8))
        blob = f.read(blen)
    prim = js["meshes"][0]["primitives"][0]
    attrs = prim["attributes"]

    def acc(name):
        a = js["accessors"][attrs[name]]
        bv = js["bufferViews"][a["bufferView"]]
        off = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
        n = a["count"]
        comps = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}[a["type"]]
        dt = {5126: np.float32, 5121: np.uint8, 5123: np.uint16, 5125: np.uint32}[a["componentType"]]
        return np.frombuffer(blob, dtype=dt, count=n * comps, offset=off).reshape(n, comps).copy()

    ind = js["accessors"][prim["indices"]]
    bv = js["bufferViews"][ind["bufferView"]]
    off = bv.get("byteOffset", 0) + ind.get("byteOffset", 0)
    dt = {5123: np.uint16, 5125: np.uint32}[ind["componentType"]]
    faces = np.frombuffer(blob, dtype=dt, count=ind["count"], offset=off).reshape(-1, 3).astype(np.int64)
    return (acc("POSITION"), acc("NORMAL"), acc("COLOR_0"), acc("TEXCOORD_0"), acc("TANGENT"), faces)


def _leaf_mask(UV, C):
    u, v = UV[:, 0], UV[:, 1]
    alpha = C[:, 3].astype(np.float64)
    if alpha.max() > 1.5:
        alpha = alpha / 255.0
    return (alpha > 0.75) & (u >= 0.0) & (u <= 1.0) & (v > 0.0) & (v < 0.50)


def _flower_mask(UV, C):
    u, v = UV[:, 0], UV[:, 1]
    alpha = C[:, 3].astype(np.float64)
    if alpha.max() > 1.5:
        alpha = alpha / 255.0
    return (alpha > 0.75) & (u > 0.27) & (u <= 1.0) & (v > 0.52) & (v < 1.02)


def _faces_of(mask, F):
    return np.array([i for i, f in enumerate(F) if mask[f].all()], np.int64)


def _cell(u):
    if u < 0.52:
        return FLOWER_Y
    if u < 0.76:
        return FLOWER_W
    return FLOWER_P


def _quads(F, faces):
    """Two triangles that share vertices are one card."""
    parent = {int(v): int(v) for v in np.unique(F[faces])}

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    groups = defaultdict(list)
    for fi in faces:
        verts = [int(v) for v in F[fi]]
        root = find(verts[0])
        for v in verts[1:]:
            rv = find(v)
            if rv != root:
                parent[rv] = root
        groups[find(verts[0])].append(int(fi))
    # re-find after unions
    out = defaultdict(list)
    for fi in faces:
        out[find(int(F[fi][0]))].append(int(fi))
    return out.values()


def deepen_flowers(V, C, UV, F, faces):
    """One flat head becomes crossed faces of the same size and place."""
    m = Mesh()
    n = 0
    for fis in _quads(F, faces):
        verts = np.unique(F[fis])
        p = V[verts].astype(np.float64)
        if len(p) < 3:
            continue
        p0 = p[0]
        d = np.linalg.norm(p[1:] - p0, axis=1)
        order = np.argsort(d)
        right = p[1:][order[0]] - p0
        up = p[1:][order[1]] - p0 if len(order) > 1 else np.array([0.0, 0.2, 0.0])
        if abs(right[1]) > abs(up[1]):
            right, up = up, right
        if np.linalg.norm(right) < 1e-4 or np.linalg.norm(up) < 1e-4:
            continue
        center = p.mean(0)
        col = C[verts].mean(0)[:3]
        if col.max() > 1.5:
            col = col / 255.0
        cell = _cell(float(UV[verts, 0].mean()))
        # Pitch the head so it reads as a bloom, not a vertical sign.
        axis = _norm(np.cross(up, right))
        up = _rot(up, axis, 0.85)
        right = _rot(right, axis, 0.85)
        turns = 2 if cell == FLOWER_P else 3
        spin = _norm(up)
        for k in range(turns):
            ang = k * (np.pi / turns)
            rgt = _rot(right, spin, ang) * (1.0 - 0.05 * k)
            u = up * (1.0 - 0.04 * k)
            m.card(center - rgt * 0.5 - u * 0.5, rgt, u, col, cell)
        n += 1
    arr = m.arrays()
    return n, arr


def _cluster_cards(cents, link, vlink):
    parent = np.arange(len(cents))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    grid = defaultdict(list)
    for i, p in enumerate(cents):
        grid[(int(np.floor(p[0] / link)), int(np.floor(p[2] / link)))].append(i)
    for i, p in enumerate(cents):
        ix, iz = int(np.floor(p[0] / link)), int(np.floor(p[2] / link))
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                for j in grid[(ix + dx, iz + dz)]:
                    if j <= i:
                        continue
                    d = p - cents[j]
                    if d[0] * d[0] + d[2] * d[2] < link * link and abs(d[1]) < vlink:
                        ra, rb = find(i), find(j)
                        if ra != rb:
                            parent[rb] = ra
    groups = defaultdict(list)
    for i in range(len(cents)):
        groups[find(i)].append(i)
    return groups


def fill_crowns(V, C, UV, F, faces):
    """Fewer, larger fans inside each low-tier crown box."""
    if len(faces) == 0:
        return 0, None
    cards = []
    for fi in faces:
        f = F[fi]
        p = V[f].astype(np.float64)
        cards.append(dict(cen=p.mean(0), col=C[f].mean(0)[:3], u=float(UV[f, 0].mean()),
                          vmin=p.min(0), vmax=p.max(0)))
    if cards and cards[0]["col"].max() > 1.5:
        for c in cards:
            c["col"] = c["col"] / 255.0
    cents = np.array([c["cen"] for c in cards])
    groups = _cluster_cards(cents, 1.35, 1.7)
    m = Mesh()
    crowns = 0
    for idxs in groups.values():
        sel = [cards[i] for i in idxs]
        vmin = np.min([c["vmin"] for c in sel], axis=0)
        vmax = np.max([c["vmax"] for c in sel], axis=0)
        h = float(vmax[1] - vmin[1])
        r = float(max(vmax[0] - vmin[0], vmax[2] - vmin[2])) * 0.5
        if h < 0.25 and r < 0.15:
            continue
        col = np.mean([c["col"] for c in sel], axis=0)
        u = float(np.mean([c["u"] for c in sel]))
        cx = float(np.mean([c["cen"][0] for c in sel]))
        cz = float(np.mean([c["cen"][2] for c in sel]))
        pine = u < 0.50 and h > max(r, 0.4) * 1.05 and h > 1.3
        if pine:
            # Dense leaf photos, not the sparse needle fan. The fan's empty
            # texels are what broke the low crown into whiskers. The taper
            # still reads as a pine. High meshes keep the needle cards.
            shells = 6
            # Start a little under the old leaves so the crown meets the trunk.
            y0 = vmin[1] - min(0.3, h * 0.06)
            for i in range(shells):
                t = (i + 0.5) / shells
                rad = max(r * (1.08 - 0.82 * t), 0.35)
                card_h = float(np.clip(h / shells * 1.9, 0.5, h * 0.4))
                card_w = float(np.clip(rad * 1.55, 0.45, r * 1.2 + 0.1))
                y = y0 + (vmax[1] - y0) * t
                y = float(np.clip(y, y0 + card_h * 0.45, vmax[1] - card_h * 0.35))
                up = np.array([0.0, card_h, 0.0])
                a0 = i * 0.7
                right = np.array([np.cos(a0), 0.0, np.sin(a0)]) * card_w
                m.cluster(np.array([cx, y, cz]), right, up, col, BUSH if i < 3 else LEAF)
        else:
            cell = BUSH if u > 0.75 else (LEAF if u > 0.5 else PINE_A)
            card = float(np.clip(max(r * 1.15, h * 0.85), 0.4, max(h, r) * 1.15 + 0.2))
            ctr = np.array([cx, float(vmin[1] + h * 0.48), cz])
            up = np.array([0.05, card, 0.0])
            right = np.array([card, 0.0, 0.08])
            m.cluster(ctr, right, up, col, cell)
            if r > 0.6:
                ctr2 = ctr + np.array([r * 0.15, h * 0.08, 0.0])
                m.cluster(ctr2, _rot(right, _norm(up), 0.8) * 0.8, up * 0.75, col, cell)
        crowns += 1
    return crowns, m.arrays()


def process(path, lod):
    P, N, C, UV, T, F = load_full(path)
    Cc = C.astype(np.float64)
    flower_f = _faces_of(_flower_mask(UV, Cc), F)
    leaf_f = _faces_of(_leaf_mask(UV, Cc), F) if lod else np.zeros(0, np.int64)
    drop_f = np.zeros(len(F), np.bool_)
    if len(flower_f):
        drop_f[flower_f] = True
    if len(leaf_f):
        drop_f[leaf_f] = True
    if not drop_f.any():
        return 0, 0
    drop_v = np.zeros(len(P), np.bool_)
    drop_v[F[drop_f].ravel()] = True
    used = np.zeros(len(P), np.bool_)
    used[F[~drop_f].ravel()] = True
    drop_v &= ~used
    keep = ~drop_v
    blocks = []
    nf = nc = 0
    if len(flower_f):
        nf, arr = deepen_flowers(P, Cc, UV, F, flower_f)
        if arr is not None:
            blocks.append(arr)
    if lod and len(leaf_f):
        nc, arr = fill_crowns(P, Cc, UV, F, leaf_f)
        if arr is not None:
            blocks.append(arr)
    remap = -np.ones(len(P), np.int64)
    nkeep = int(keep.sum())
    remap[keep] = np.arange(nkeep)
    scale = 255.0 if C.max() > 1.5 else 1.0
    parts_v = [P[keep].astype(np.float64)] if nkeep else []
    parts_n = [N[keep].astype(np.float64)] if nkeep else []
    parts_c = [C[keep].astype(np.float64) / scale] if nkeep else []
    parts_uv = [UV[keep].astype(np.float64)] if nkeep else []
    parts_t = [T[keep].astype(np.float64)] if nkeep else []
    parts_f = [remap[F[~drop_f]]] if nkeep else []
    base = nkeep
    for V, Ff, Cc2, Uv, Nn, Tt in blocks:
        parts_v.append(V)
        parts_n.append(Nn)
        parts_c.append(Cc2)
        parts_uv.append(Uv)
        parts_t.append(Tt)
        parts_f.append(Ff + base)
        base += len(V)
    write_glb(path, np.concatenate(parts_v), np.concatenate(parts_f).astype(np.uint32),
              np.concatenate(parts_c), np.concatenate(parts_n), np.concatenate(parts_uv),
              np.concatenate(parts_t), os.path.basename(path)[:-4])
    P2, N2, C2, _, _, _ = load_full(path)
    if nkeep and P2[:nkeep].tobytes() != P[keep].tobytes():
        raise SystemExit("positions moved " + path)
    if nkeep and N2[:nkeep].tobytes() != N[keep].tobytes():
        raise SystemExit("normals moved " + path)
    if nkeep and C2[:nkeep].tobytes() != C[keep].tobytes():
        raise SystemExit("colors moved " + path)
    return nf, nc


def kind_of(fn):
    if not fn.endswith(".glb") or "_col" in fn:
        return None
    lod = fn.endswith("_lod1.glb")
    if "land_scatter" in fn:
        return "lod" if lod else "high"
    if lod and "canopy" in fn:
        return "lod"
    return None


def main():
    paint_flowers()
    flowers = crowns = files = 0
    for dp, _, fs in os.walk(ROOT):
        for fn in sorted(fs):
            kind = kind_of(fn)
            if kind is None:
                continue
            path = os.path.join(dp, fn)
            nf, nc = process(path, kind == "lod")
            if nf or nc:
                files += 1
                flowers += nf
                crowns += nc
    print("files", files, "flowers", flowers, "crowns", crowns)


if __name__ == "__main__":
    main()
