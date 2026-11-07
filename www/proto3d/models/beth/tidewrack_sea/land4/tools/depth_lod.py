"""Break the even whorl on low-tier pines. Flowers and high cards stay.

A low-tier pine keeps its crown box. The fans are the same needle cells, but
the boughs no longer share a height or a six-sided turn. Grass, flowers,
trunks, ground, and colliders stay.
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
    # Wider, shorter petals. The thin ones read as a star once the head has any thickness.
    _soft_petal(daisy, 256, 256, 8, 128, 34, (244, 240, 228, 255), (214, 164, 42, 255), 6)
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


def _one_card(V, C, UV, F, fis):
    verts = np.unique(F[fis])
    p = V[verts].astype(np.float64)
    if len(p) < 3:
        return None
    p0 = p[0]
    dist = np.linalg.norm(p[1:] - p0, axis=1)
    order = np.argsort(dist)
    right = p[1:][order[0]] - p0
    up = p[1:][order[1]] - p0 if len(order) > 1 else np.array([0.0, 0.2, 0.0])
    if abs(right[1]) > abs(up[1]):
        right, up = up, right
    if np.linalg.norm(right) < 1e-4 or np.linalg.norm(up) < 1e-4:
        return None
    col = C[verts].mean(0)[:3]
    if col.max() > 1.5:
        col = col / 255.0
    return dict(center=p.mean(0), right=right, up=up, col=col,
                cell=_cell(float(UV[verts, 0].mean())))


def _bloom(right, up):
    """Tip the head so it is readable from the side and from above."""
    width = float(np.linalg.norm(right))
    height = float(np.linalg.norm(up))
    normal = np.cross(right, up)
    face = np.array([normal[0], 0.0, normal[2]])
    if np.linalg.norm(face) < 1e-4:
        face = np.array([right[0], 0.0, right[2]])
    if np.linalg.norm(face) < 1e-4:
        face = np.array([1.0, 0.0, 0.0])
    face = _norm(face)
    tilt = 1.05
    new_up = _norm(np.array([face[0] * np.sin(tilt), np.cos(tilt), face[2] * np.sin(tilt)])) * height
    new_right = np.cross(new_up, np.array([0.0, 1.0, 0.0]))
    if np.linalg.norm(new_right) < 1e-4:
        new_right = np.array([width, 0.0, 0.0])
    new_right = _norm(new_right) * width
    if np.dot(new_right, right) < 0:
        new_right = -new_right
    return new_right, new_up


def deepen_flowers(V, C, UV, F, faces):
    """Two nearly aligned faces. A wide spin turns a daisy into a pinwheel."""
    cards = []
    for fis in _quads(F, faces):
        card = _one_card(V, C, UV, F, fis)
        if card is not None:
            cards.append(card)
    if not cards:
        return 0, None
    cents = np.array([c["center"] for c in cards])
    groups = _cluster_cards(cents, 0.22, 0.35)
    m = Mesh()
    n = 0
    for idxs in groups.values():
        sel = [cards[i] for i in idxs]
        # The largest face is the bloom. The others were the old crossing.
        q = max(sel, key=lambda c: float(np.linalg.norm(c["right"]) * np.linalg.norm(c["up"])))
        center, col, cell = q["center"], q["col"], q["cell"]
        right, up = _bloom(q["right"], q["up"])
        # A few degrees, so the side has thickness and the petals still line up.
        yaw = 0.14 if cell == FLOWER_P else (0.18 if cell == FLOWER_W else 0.22)
        m.card(center - right * 0.5 - up * 0.5, right, up, col, cell)
        r2 = _rot(right, np.array([0.0, 1.0, 0.0]), yaw) * 0.96
        u2 = _rot(up, np.array([0.0, 1.0, 0.0]), yaw) * 0.96
        m.card(center - r2 * 0.5 - u2 * 0.5 + np.array([0.0, 0.012, 0.0]), r2, u2, col, cell)
        n += 1
    return n, m.arrays()


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
        return 0, None, []
    cards = []
    for fi in faces:
        f = F[fi]
        p = V[f].astype(np.float64)
        cards.append(dict(cen=p.mean(0), col=C[f].mean(0)[:3], u=float(UV[f, 0].mean()),
                          vmin=p.min(0), vmax=p.max(0), fi=int(fi)))
    if cards and cards[0]["col"].max() > 1.5:
        for c in cards:
            c["col"] = c["col"] / 255.0
    cents = np.array([c["cen"] for c in cards])
    groups = _cluster_cards(cents, 1.8, 2.8)
    m = Mesh()
    crowns = 0
    consumed = []
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
        # Shape, not the current cell. An earlier pass painted these with broad leaves.
        pine = h > max(r, 0.35) * 1.15 and h > 1.4
        if pine:
            # Same number of fans as the even whorl, but not on a shared ring.
            # Height is stratified so the cone stays filled. Reach and lean
            # wander, so the outline is not a sawtooth.
            y0 = float(vmin[1])
            bands = int(np.clip(round(h / 0.4), 6, 11))
            seed = int(abs(cx * 13.7 + cz * 7.1 + y0) * 1000) % (2**31 - 1) or 1
            rng = np.random.default_rng(seed)
            phase = float(rng.uniform(0, 6.283))
            for b in range(bands):
                t = (b + 0.45) / bands
                ymid = h * (0.04 + 0.9 * t)
                cone = max(r * (1.04 - 0.9 * t), 0.24)
                # A slow bulge, so the outline is not a straight sawtooth taper.
                cone *= 0.94 + 0.08 * np.sin(t * 6.283 * 2.15 + phase)
                arms = int(rng.integers(5, 8))
                spin = float(rng.uniform(0, 6.283))
                step = 6.283 / arms
                for k in range(arms):
                    a = spin + k * step + float(rng.uniform(-0.28, 0.28))
                    ca, sa = np.cos(a), np.sin(a)
                    y = ymid + float(rng.uniform(-0.4, 0.4)) * (h / bands)
                    reach = cone * float(rng.uniform(0.88, 1.06))
                    lean = float(rng.uniform(0.32, 0.55))
                    rise = float(rng.uniform(0.72, 0.92))
                    up = _norm(np.array([ca * lean, rise, sa * lean]))
                    card = float(np.clip(0.48 + reach * 0.3, 0.54, 0.86))
                    upv = up * card
                    right = _norm(np.cross(up, np.array([0.0, 1.0, 0.0]))) * card * float(rng.uniform(0.78, 0.94))
                    ctr = np.array([cx + ca * reach * 0.68, y0 + y, cz + sa * reach * 0.68])
                    cell = PINE_A if (b + k) % 2 == 0 else PINE_B
                    m.card(ctr - right * 0.5 - upv * 0.5, right, upv, col, cell)
                    r2 = _rot(right, _norm(up), float(rng.uniform(0.5, 0.95)))
                    m.card(ctr - r2 * 0.5 - upv * 0.5, r2, upv, col, cell)
            # Two short twigs inside the fat part of the cone.
            a0 = float(rng.uniform(0, 6.283))
            for i in range(2):
                th = 0.28 + 0.14 * i
                local = max(r * (1.04 - 0.9 * th) * 0.42, 0.15)
                a = a0 + (1.9 + i * float(rng.uniform(0.7, 1.3)))
                trunk = np.array([cx, y0 + h * 0.14, cz])
                tip = np.array([cx + np.cos(a) * local, y0 + h * th, cz + np.sin(a) * local])
                m.twig(trunk, tip, col)
            consumed.extend(int(cards[i]["fi"]) for i in idxs)
            crowns += 1
    return crowns, m.arrays(), consumed


def process(path, lod, crowns_only=False):
    P, N, C, UV, T, F = load_full(path)
    Cc = C.astype(np.float64)
    flower_f = np.zeros(0, np.int64) if crowns_only else _faces_of(_flower_mask(UV, Cc), F)
    leaf_f = _faces_of(_leaf_mask(UV, Cc), F) if lod else np.zeros(0, np.int64)
    pine_faces = []
    if crowns_only:
        if len(leaf_f) == 0:
            return 0, 0
        nc, arr, pine_faces = fill_crowns(P, Cc, UV, F, leaf_f)
        if not pine_faces:
            return 0, 0
        leaf_f = np.asarray(pine_faces, np.int64)
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
    nf = 0
    if crowns_only:
        if arr is not None:
            blocks.append(arr)
    else:
        nc = 0
        if len(flower_f):
            nf, arr = deepen_flowers(P, Cc, UV, F, flower_f)
            if arr is not None:
                blocks.append(arr)
        if lod and len(leaf_f):
            nc, arr, _pine = fill_crowns(P, Cc, UV, F, leaf_f)
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


def thicken_needles():
    """Close holes in the pine fans. The strokes stay needles, not a leaf blob.

    High and low share this atlas, so the change is a fuller fan of the same
    needles. Running again is a no-op once the fan is already filled.
    """
    im = Image.open(ATLAS).convert("RGBA")
    probe = np.asarray(im.crop((0, 0, CELL, CELL)))
    if float((probe[:, :, 3] > 80).mean()) > 0.28:
        return
    for col in (0, 1):
        src = im.crop((col * CELL, 0, (col + 1) * CELL, CELL))
        layer = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
        for ang, dx, dy in ((0, 0, 0), (8, 18, 10), (-11, -16, 8), (5, 10, -20), (-7, -12, -14)):
            spun = src.rotate(ang, resample=Image.Resampling.BICUBIC)
            layer.alpha_composite(spun, (dx, dy))
        arr = np.asarray(layer).astype(np.float32)
        # Keep the fan's pointed outline. Tips stay thin.
        y, x = np.mgrid[0:CELL, 0:CELL]
        ny = y / (CELL - 1)
        nx = np.abs((x / (CELL - 1)) * 2 - 1)
        half = 0.22 + 0.74 * ny
        fall = np.clip((half - nx) / 0.16, 0, 1)
        arr[:, :, 3] *= fall
        im.paste(Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA"), (col * CELL, 0))
    im.save(ATLAS)


def main():
    # Flowers and the atlas stay. Only the low-tier pine fans are rewritten.
    crowns = files = 0
    for dp, _, fs in os.walk(ROOT):
        for fn in sorted(fs):
            if kind_of(fn) != "lod":
                continue
            path = os.path.join(dp, fn)
            _nf, nc = process(path, True, crowns_only=True)
            if nc:
                files += 1
                crowns += nc
    print("files", files, "crowns", crowns)


if __name__ == "__main__":
    main()
