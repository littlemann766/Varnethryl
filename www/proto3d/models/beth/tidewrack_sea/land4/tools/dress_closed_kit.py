"""Replace closed green foliage kits that the cone pass left behind.

The kit is one mesh: 80 triangles, every edge shared by two faces, no vertex
shared with the ground, and a green mean. Ice (blue heavier than green) and
the orange ember spike are not this kit. A piece whose top sits under the
surrounding surface is buried, so it stays.

Cards land in the existing *_canopy.glb. A short piece becomes a grounded
bush. A tall piece becomes a needle crown. Small gaps under the kit, up to
0.45 m, are closed. Ground vertices are not moved.
"""
import json
import os
import sys
from collections import Counter, defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from common import write_glb
from dress_foliage import broad_cards
from dress_island_cones import ROOT, canopy_name, components, load_glb, pine_crown, write_exact


def load_canopy(path):
    if not os.path.exists(path):
        return None
    import struct
    with open(path, "rb") as f:
        struct.unpack("<III", f.read(12))
        clen, _ = struct.unpack("<II", f.read(8))
        js = json.loads(f.read(clen))
        blen, _ = struct.unpack("<II", f.read(8))
        blob = f.read(blen)
    prim = js["meshes"][0]["primitives"][0]
    attrs = prim["attributes"]

    def acc(name):
        if name not in attrs:
            return None
        a = js["accessors"][attrs[name]]
        bv = js["bufferViews"][a["bufferView"]]
        off = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
        n = a["count"]
        comps = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}[a["type"]]
        dt = {5126: np.float32, 5121: np.uint8, 5123: np.uint16, 5125: np.uint32}[a["componentType"]]
        return np.frombuffer(blob, dtype=dt, count=n * comps, offset=off).reshape(n, comps).copy()

    V = acc("POSITION").astype(np.float64)
    N = acc("NORMAL").astype(np.float64)
    C = acc("COLOR_0").astype(np.float64)
    if C.max() > 1.5:
        C = C / 255.0
    UV = acc("TEXCOORD_0")
    T = acc("TANGENT")
    F = acc("INDICES") if False else None
    ind = js["accessors"][prim["indices"]]
    bv = js["bufferViews"][ind["bufferView"]]
    off = bv.get("byteOffset", 0) + ind.get("byteOffset", 0)
    n = ind["count"]
    dt = {5123: np.uint16, 5125: np.uint32}[ind["componentType"]]
    F = np.frombuffer(blob, dtype=dt, count=n, offset=off).reshape(-1, 3).astype(np.int64)
    if UV is None:
        UV = np.zeros((len(V), 2))
    if T is None:
        T = np.tile([1.0, 0.0, 0.0, 1.0], (len(V), 1))
    return V, F, C, UV, N, T


def kit_parts(V, F, C, lod=False):
    roots = components(F, len(V))
    by = defaultdict(list)
    for i, r in enumerate(roots):
        by[int(r)].append(i)
    found = []
    skipped = []
    for r, sel0 in by.items():
        sel = np.array(sel0, np.int64)
        n = len(sel)
        if not (20 <= n <= 64):
            continue
        col = C[sel].mean(0)
        if not (col[1] > col[0] + 0.04 and col[1] + 0.02 >= col[2]):
            continue
        bb = V[sel].max(0) - V[sel].min(0)
        height = float(bb[1])
        horiz = float(max(bb[0], bb[2]))
        if height < 1.0 or height > 6.5 or horiz > 4.2:
            continue
        ins = set(int(i) for i in sel)
        faces = []
        mixed = 0
        for fi, f in enumerate(F):
            flags = [int(k) in ins for k in f]
            if all(flags):
                faces.append(fi)
            elif any(flags):
                mixed += 1
        # High meshes use one 80-face kit. Lod keeps the same object with fewer faces.
        if mixed or len(faces) < 20 or len(faces) > 80:
            continue
        if not lod and len(faces) != 80:
            continue
        edges = Counter()
        for fi in faces:
            a, b, c = (int(k) for k in F[fi])
            for e in ((min(a, b), max(a, b)), (min(b, c), max(b, c)), (min(c, a), max(c, a))):
                edges[e] += 1
        if any(v != 2 for v in edges.values()):
            continue
        y0 = float(V[sel, 1].min())
        y1 = float(V[sel, 1].max())
        cen = V[sel].mean(0)
        d = np.hypot(V[:, 0] - cen[0], V[:, 2] - cen[2])
        other = np.nonzero((d < 2.2) & (roots != r))[0]
        above = int(np.sum(V[other, 1] > y1 + 0.25)) if len(other) else 0
        below = int(np.sum(V[other, 1] < y0 + 0.15)) if len(other) else 0
        if above >= 1 and below == 0:
            skipped.append(dict(why="buried under the surface", at=[round(float(x), 2) for x in cen]))
            continue
        ground = None
        if len(other):
            under = other[V[other, 1] < y0 + 0.05]
            if len(under):
                ground = float(V[under, 1].max())
        gap = 0.0 if ground is None else max(0.0, y0 - ground)
        drop = float(min(gap, 0.45))
        found.append(dict(sel=sel, col=col, y0=y0, y1=y1, cen=cen, horiz=horiz, height=height, drop=drop))
    found.sort(key=lambda t: (round(t["cen"][0], 2), round(t["cen"][2], 2)))
    return found, skipped


def cards_for(part, lod):
    h = max(part["height"], 0.8)
    r = max(part["horiz"] * 0.5, 0.4)
    cen = part["cen"].copy()
    cen[1] -= part["drop"]
    size = np.array([part["horiz"], h, part["horiz"]])
    # center y is the middle of the (possibly lowered) box
    cen[1] = (part["y0"] - part["drop"] + part["y1"]) * 0.5
    # Source kits store alpha 0. The scatter shader reads alpha as the material kind.
    col = np.array(part["col"][:3], np.float64)
    tall = h >= part["horiz"] * 0.9
    if tall:
        return pine_crown(cen, size, col, lod)
    return broad_cards(cen, size, col, lod, True)


def main():
    report = {"dressed": [], "buried": []}
    for dp, _, fs in os.walk(ROOT):
        for fn in sorted(fs):
            if not fn.endswith(".glb"):
                continue
            if "isl" not in fn and "island" not in fn:
                continue
            if any(s in fn for s in ("_glow", "_col", "canopy")):
                continue
            path = os.path.join(dp, fn)
            V, N, C, F = load_glb(path)
            Vc = V.astype(np.float64)
            Cc = C.astype(np.float64) / 255.0
            lod = fn.endswith("_lod1.glb")
            parts, buried = kit_parts(Vc, F, Cc, lod)
            report["buried"] += [dict(file=os.path.relpath(path, ROOT), **b) for b in buried]
            if not parts:
                continue
            keep = np.ones(len(V), np.bool_)
            for p in parts:
                keep[p["sel"]] = False
            face_keep = keep[F].all(1)
            remap = -np.ones(len(V), np.int64)
            remap[keep] = np.arange(int(keep.sum()))
            F2 = remap[F[face_keep]]
            before = V[keep].tobytes() + N[keep].tobytes() + C[keep].tobytes()
            write_exact(path, V[keep], N[keep], C[keep], F2, fn[:-4])
            Vr, Nr, Cr, Fr = load_glb(path)
            if before != Vr.tobytes() + Nr.tobytes() + Cr.tobytes():
                raise SystemExit("kept bytes changed " + fn)
            blocks = []
            for p in parts:
                built = cards_for(p, lod)
                if built is not None:
                    blocks.append(built)
            out = os.path.join(dp, canopy_name(fn))
            old = load_canopy(out)
            chunks = []
            if old is not None:
                chunks.append(old)
            base_b = 0
            if blocks:
                bv, bf, bc, bu, bn, bt = [], [], [], [], [], []
                for b in blocks:
                    bv.append(b[0])
                    bf.append(b[1] + base_b)
                    bc.append(b[2])
                    bu.append(b[3])
                    bn.append(b[4])
                    bt.append(b[5])
                    base_b += len(b[0])
                chunks.append((
                    np.concatenate(bv), np.concatenate(bf), np.concatenate(bc),
                    np.concatenate(bu), np.concatenate(bn), np.concatenate(bt),
                ))
            if not chunks:
                continue
            base = 0
            Vs, Fs, Cs, UVs, Ns, Ts = [], [], [], [], [], []
            for Vv, Ff, Cc_, Uv, Nn, Tt in chunks:
                Vs.append(Vv)
                Fs.append(Ff + base)
                Cs.append(Cc_)
                UVs.append(Uv)
                Ns.append(Nn)
                Ts.append(Tt)
                base += len(Vv)
            write_glb(out, np.concatenate(Vs), np.concatenate(Fs).astype(np.uint32),
                      np.concatenate(Cs), np.concatenate(Ns), np.concatenate(UVs),
                      np.concatenate(Ts), canopy_name(fn)[:-4])
            faces = sum(len(b[1]) for b in blocks)
            report["dressed"].append(dict(
                file=os.path.relpath(path, ROOT),
                canopy=os.path.relpath(out, ROOT),
                kits=len(parts),
                pines=sum(1 for p in parts if p["height"] >= p["horiz"] * 0.9),
                bushes=sum(1 for p in parts if p["height"] < p["horiz"] * 0.9),
                dropped=round(float(np.mean([p["drop"] for p in parts])), 3),
                canopy_faces=int(faces),
                kept_verts=int(keep.sum()),
            ))
            print(fn, "kits", len(parts), "faces", faces, "buried_skip", len(buried))
    rep = os.path.join(ROOT, "closed_kit_report.json")
    with open(rep, "w") as f:
        json.dump(report, f, indent=1)
    print("files", len(report["dressed"]), "buried", len(report["buried"]))


if __name__ == "__main__":
    main()
