"""Replace existing grass and flower cards. Trees, trunks, and ground stay.

Each old tuft keeps its footprint. Blades vary in height and lean. A flower
is one head plus a short stem, with a smaller side bloom only on the high
mesh, instead of three copies of the same daisy. The low-tier tuft keeps the
tallest blade and the same head, so the graphics-tier swap does not erase it.

The three flower cells are repainted in place. Pine, leaf, bush, and grass
cells are not touched.
"""
import json
import os
import struct
import sys
from collections import defaultdict

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(__file__))
from common import write_glb
from dress_foliage import FLOWER_P, FLOWER_W, FLOWER_Y, GRASS, Mesh, _norm, _rng

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ATLAS = os.path.join(ROOT, "textures", "foliage_atlas.png")
CELL = 512


def _petal_flower(layer, cx, cy, n, length, width, color, center, turn=0.0):
    """Separate petals around one centre, so the head is not one lumpy disk."""
    for i in range(n):
        ang = turn + i / n * 360.0
        pet = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
        d = ImageDraw.Draw(pet)
        d.ellipse([cx - width, cy - length, cx + width, cy - width], fill=color)
        vein = tuple(max(0, c - 36) if k < 3 else c for k, c in enumerate(color))
        d.line([(cx, cy - width), (cx, cy - length + 16)], fill=vein, width=3)
        pet = pet.rotate(ang, center=(cx, cy), resample=Image.Resampling.BICUBIC)
        layer.alpha_composite(pet)
    d = ImageDraw.Draw(layer)
    r = max(18, width // 2)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=center)
    hi = tuple(min(255, c + 40) if k < 3 else c for k, c in enumerate(center))
    d.ellipse([cx - r // 2, cy - r // 2, cx + r // 3, cy + r // 3], fill=hi)


def paint_flowers():
    im = Image.open(ATLAS).convert("RGBA")
    arr = np.asarray(im).copy()
    for c in (1, 2, 3):
        arr[CELL:CELL * 2, c * CELL:(c + 1) * CELL] = 0
    base = Image.fromarray(arr, "RGBA")
    # Three different heads. The old atlas used the same seven-petal stamp in every cell.
    kinds = []
    cup = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
    _petal_flower(cup, 256, 250, 5, 150, 42, (236, 186, 48, 255), (96, 58, 18, 255), -18)
    kinds.append(cup)
    bell = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
    _petal_flower(bell, 256, 230, 6, 170, 28, (242, 238, 226, 255), (214, 164, 42, 255), 12)
    kinds.append(bell)
    sprig = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
    _petal_flower(sprig, 190, 170, 5, 78, 24, (206, 86, 112, 255), (120, 36, 58, 255))
    _petal_flower(sprig, 330, 210, 5, 58, 18, (186, 70, 100, 255), (110, 32, 52, 255), 20)
    _petal_flower(sprig, 250, 310, 5, 50, 16, (214, 120, 138, 255), (130, 48, 64, 255), 8)
    kinds.append(sprig)
    from scipy import ndimage
    for col, layer in enumerate(kinds, start=1):
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
    print("painted flowers", ATLAS)


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
    F = np.frombuffer(blob, dtype=dt, count=ind["count"], offset=off).reshape(-1, 3).astype(np.int64)
    return (acc("POSITION"), acc("NORMAL"), acc("COLOR_0"), acc("TEXCOORD_0"),
            acc("TANGENT"), F)


def tuft_faces(UV, C, F):
    u = UV[:, 0]
    v = UV[:, 1]
    alpha = C[:, 3]
    if alpha.max() > 1.5:
        alpha = alpha / 255.0
    leaf = (alpha > 0.75) & (u >= 0.0) & (u <= 1.0) & (v > 0.52) & (v < 1.02)
    return np.array([i for i, f in enumerate(F) if leaf[f].all()], np.int64)


def clusters(V, UV, C, F, faces):
    quads = []
    for fi in faces:
        f = F[fi]
        cen = V[f].mean(0)
        flower = float(UV[f, 0].mean()) > 0.27
        bb = V[f].max(0) - V[f].min(0)
        quads.append(dict(fi=int(fi), cen=cen, flower=flower, col=C[f].mean(0),
                          verts=f, tall=float(bb[1]), wide=float(max(bb[0], bb[2]))))
    parent = np.arange(len(quads))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    grid = defaultdict(list)
    for i, q in enumerate(quads):
        key = (int(np.floor(q["cen"][0] / 0.16)), int(np.floor(q["cen"][2] / 0.16)))
        grid[key].append(i)
    for i, q in enumerate(quads):
        ix, iz = int(np.floor(q["cen"][0] / 0.16)), int(np.floor(q["cen"][2] / 0.16))
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                for j in grid[(ix + dx, iz + dz)]:
                    if j <= i:
                        continue
                    d = q["cen"] - quads[j]["cen"]
                    if d[0] * d[0] + d[2] * d[2] < 0.16 ** 2 and abs(d[1]) < 0.45:
                        ra, rb = find(i), find(j)
                        if ra != rb:
                            parent[rb] = ra
    groups = defaultdict(list)
    for i in range(len(quads)):
        groups[find(i)].append(quads[i])
    # Grass stays a tuft. Each flower group keeps its own head so a neighbour
    # does not swallow it, and the low tier still has a bloom.
    grass = {k: v for k, v in groups.items() if not all(q["flower"] for q in v)}
    flowers = {k: v for k, v in groups.items() if all(q["flower"] for q in v)}
    plants = []
    for qs in grass.values():
        plants.append(qs)  # blades, and a head when the group already holds one
    for fqs in flowers.values():
        fc = np.mean([q["cen"] for q in fqs], axis=0)
        best = None
        best_d = 0.4 ** 2
        for qs in grass.values():
            gc = np.mean([q["cen"] for q in qs], axis=0)
            d = (fc[0] - gc[0]) ** 2 + (fc[2] - gc[2]) ** 2
            if d < best_d and fc[1] >= gc[1] - 0.2:
                best, best_d = qs, d
        # Head only. The tuft under it is the grass plant, so it is not drawn twice.
        borrowed = [dict(q, flower=False, _base=True) for q in (best or [])]
        plants.append(borrowed + fqs)
    return plants


def build(plant, lod):
    verts = np.concatenate([p["verts"] for p in plant])
    pts = np.vstack([p["cen"] for p in plant])
    # world AABB of the old cards
    # recover from the actual vertices via the face indices later; cens are enough for a loose box
    flowers = [p for p in plant if p["flower"]]
    grasses = [p for p in plant if not p["flower"]]
    col = np.mean([p["col"][:3] for p in (grasses or plant)], axis=0)
    fcol = np.mean([p["col"][:3] for p in flowers], axis=0) if flowers else None
    # Blade length follows the old grass cards, not the flower heads above them.
    gh = max((p["tall"] for p in grasses), default=0.34)
    gh = float(np.clip(gh, 0.22, 0.55))
    gw = max((p["wide"] for p in grasses), default=0.12)
    gw = float(np.clip(max(gw, 0.16), 0.16, 0.26))
    fh = max((p["wide"] for p in flowers), default=0.28)
    fh = float(np.clip(fh, 0.18, 0.42))
    bottom = float(min(p["cen"][1] - p["tall"] * 0.5 for p in (grasses or plant)))
    # Sit the bloom in the top of the tuft. The old cards stacked three heads
    # half a metre up, which left a floating disk once there was only one.
    xz = np.mean([p["cen"][[0, 2]] for p in plant], axis=0)
    origin = np.array([xz[0], bottom, xz[1]])
    rng = _rng(origin, 11 if lod else 9)
    m = Mesh()
    borrowed = any(p.get("_base") for p in plant)
    n = 0 if borrowed else (3 if lod else 5)
    for i in range(n):
        ang = float(rng.uniform(0, np.pi))
        tall = 1.0 if i == 0 else float(rng.uniform(0.55, 0.9))
        lean = float(rng.uniform(-0.22, 0.22))
        width = gw * float(rng.uniform(0.85, 1.15))
        right = np.array([np.cos(ang), 0.0, np.sin(ang)]) * width
        up = np.array([lean * 0.08, gh * tall, lean * 0.06])
        off = np.array([float(rng.uniform(-0.04, 0.04)), 0.0, float(rng.uniform(-0.04, 0.04))])
        m.card(off - right * 0.5, right, up, col, GRASS)
    if fcol is not None:
        stem = gh * 0.72
        m.card(np.array([-0.018, 0.0, 0.0]), np.array([0.04, 0.0, 0.01]),
               np.array([0.012, stem, 0.0]), col, GRASS)
        # 0.5 m buckets, so a low-tier card that shifted a few centimetres
        # keeps the same head as the high mesh.
        kind = int(abs(round(origin[0] * 2) * 3 + round(origin[2] * 2) * 7)) % 3
        cells = (FLOWER_Y, FLOWER_W, FLOWER_P)
        tilt = float(rng.uniform(-0.15, 0.15))
        right = np.array([1.0, 0.0, tilt]) * fh
        up = np.array([tilt * 0.1, fh * 0.85, 0.02])
        m.card(np.array([0.0, stem, 0.0]) - right * 0.5 - up * 0.2, right, up, fcol, cells[kind])
    arr = m.arrays()
    if arr is None:
        return None
    V, F, C, UV, N, T = arr
    V = V.copy()
    V[:, 0] += origin[0]
    V[:, 1] += origin[1]
    V[:, 2] += origin[2]
    return V, F, C, UV, N, T


def process(path, lod):
    P, N, C, UV, T, F = load_full(path)
    faces = tuft_faces(UV, C, F)
    if len(faces) == 0:
        return 0
    plants = clusters(P.astype(np.float64), UV.astype(np.float64), C.astype(np.float64) / 255.0, F, faces)
    drop = np.zeros(len(P), np.bool_)
    for fi in faces:
        drop[F[fi]] = True
    # a vertex used by a kept face stays
    kept_face = np.ones(len(F), np.bool_)
    kept_face[faces] = False
    used = np.zeros(len(P), np.bool_)
    used[F[kept_face].ravel()] = True
    drop &= ~used
    keep = ~drop
    blocks = []
    for plant in plants:
        built = build(plant, lod)
        if built is not None:
            blocks.append(built)
    remap = -np.ones(len(P), np.int64)
    remap[keep] = np.arange(int(keep.sum()))
    F2 = remap[F[kept_face]]
    parts_v = [P[keep].astype(np.float64)]
    parts_n = [N[keep].astype(np.float64)]
    parts_c = [C[keep].astype(np.float64) / 255.0]
    parts_uv = [UV[keep].astype(np.float64)]
    parts_t = [T[keep].astype(np.float64)]
    parts_f = [F2]
    base = int(keep.sum())
    before = P[keep].tobytes() + N[keep].tobytes() + C[keep].tobytes()
    for V, Ff, Cc, Uv, Nn, Tt in blocks:
        parts_v.append(V)
        parts_n.append(Nn)
        parts_c.append(Cc)
        parts_uv.append(Uv)
        parts_t.append(Tt)
        parts_f.append(Ff + base)
        base += len(V)
    write_glb(path, np.concatenate(parts_v), np.concatenate(parts_f).astype(np.uint32),
              np.concatenate(parts_c), np.concatenate(parts_n), np.concatenate(parts_uv),
              np.concatenate(parts_t), os.path.basename(path)[:-4])
    # verify kept bytes
    P2, N2, C2, UV2, T2, F2b = load_full(path)
    # kept verts are a prefix only if we wrote them first. Compare the subsequence.
    if P2[:int(keep.sum())].tobytes() != P[keep].tobytes():
        raise SystemExit("positions moved " + path)
    if N2[:int(keep.sum())].tobytes() != N[keep].tobytes():
        raise SystemExit("normals moved " + path)
    if C2[:int(keep.sum())].tobytes() != C[keep].tobytes():
        raise SystemExit("colors moved " + path)
    return len(plants)


def main():
    paint_flowers()
    nfiles = nplants = 0
    for dp, _, fs in os.walk(ROOT):
        for fn in sorted(fs):
            if "land_scatter" not in fn or not fn.endswith(".glb") or "_col" in fn:
                continue
            path = os.path.join(dp, fn)
            k = process(path, fn.endswith("_lod1.glb"))
            if k:
                nfiles += 1
                nplants += k
                print(fn, "plants", k)
    print("files", nfiles, "plants", nplants)


if __name__ == "__main__":
    main()
