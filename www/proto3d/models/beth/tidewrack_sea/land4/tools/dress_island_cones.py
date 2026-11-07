"""Lift closed decorative cone canopies out of island meshes.

A cone is removed only when the whole connected component is a small closed
pine tier: 6 to 16 vertices, taller than 1 m, green or snow-dusted, and one
level ring around an apex. Ground faces stay byte for byte. A component that
shares the terrain mesh is reported and left alone.

Replacement crowns are a separate *_canopy.glb (and _lod1). They use the
existing needle atlas through vc_scatter. They are not named _isl_, so the
terrain shader does not pick them up. No collider is written.
"""
import json
import os
import struct
import sys
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from common import write_glb
from dress_foliage import Mesh, PINE_A, PINE_B, _norm, _place

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def load_glb(path):
    with open(path, "rb") as f:
        struct.unpack("<III", f.read(12))
        clen, _ = struct.unpack("<II", f.read(8))
        js = json.loads(f.read(clen))
        blen, _ = struct.unpack("<II", f.read(8))
        blob = f.read(blen)
    prim = js["meshes"][0]["primitives"][0]
    attrs = prim["attributes"]

    def acc(idx):
        a = js["accessors"][idx]
        bv = js["bufferViews"][a["bufferView"]]
        off = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
        n = a["count"]
        comps = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}[a["type"]]
        dt = {5126: np.float32, 5121: np.uint8, 5123: np.uint16, 5125: np.uint32}[a["componentType"]]
        return np.frombuffer(blob, dtype=dt, count=n * comps, offset=off).reshape(n, comps).copy()

    V = acc(attrs["POSITION"])
    N = acc(attrs["NORMAL"])
    C = acc(attrs["COLOR_0"])
    F = acc(prim["indices"]).reshape(-1, 3).astype(np.int64)
    return V, N, C, F


def write_exact(path, V, N, C, F, name):
    """Write POSITION/NORMAL/COLOR bytes unchanged. F is remapped uint32."""
    V = np.asarray(V, np.float32)
    N = np.asarray(N, np.float32)
    C = np.asarray(C, np.uint8)
    F = np.asarray(F, np.uint32).reshape(-1)
    bufs = []
    views = []
    acc = []
    off = 0

    def add(arr, target, comp, typ, count, mm=False):
        nonlocal off
        b = arr.tobytes()
        pad = (-len(b)) % 4
        views.append(dict(buffer=0, byteOffset=off, byteLength=len(b), target=target))
        bufs.append(b + b"\0" * pad)
        off += len(b) + pad
        a = dict(bufferView=len(views) - 1, componentType=comp, count=count, type=typ)
        if mm:
            a["min"] = arr.reshape(count, -1).min(0).astype(float).tolist()
            a["max"] = arr.reshape(count, -1).max(0).astype(float).tolist()
        acc.append(a)
        return len(acc) - 1

    attrs = {
        "POSITION": add(V, 34962, 5126, "VEC3", len(V), True),
        "NORMAL": add(N, 34962, 5126, "VEC3", len(V)),
        "COLOR_0": add(C, 34962, 5121, "VEC4", len(V)),
    }
    acc[-1]["normalized"] = True
    ind = add(F, 34963, 5125, "SCALAR", len(F))
    j = dict(
        asset=dict(version="2.0", generator="beth land4"),
        scene=0,
        scenes=[dict(nodes=[0])],
        nodes=[dict(mesh=0, name=name)],
        meshes=[dict(name=name, primitives=[dict(attributes=attrs, indices=ind, mode=4)])],
        accessors=acc,
        bufferViews=views,
        buffers=[dict(byteLength=off)],
    )
    js = json.dumps(j, separators=(",", ":")).encode()
    js += b" " * ((-len(js)) % 4)
    bin_ = b"".join(bufs)
    with open(path, "wb") as f:
        f.write(struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(bin_)))
        f.write(struct.pack("<II", len(js), 0x4E4F534A))
        f.write(js)
        f.write(struct.pack("<II", len(bin_), 0x004E4942))
        f.write(bin_)


def components(F, n):
    parent = np.arange(n)

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for f in F:
        union(int(f[0]), int(f[1]))
        union(int(f[1]), int(f[2]))
    return np.fromiter((find(i) for i in range(n)), np.int64, n)


def apex_of(vi, faces, V):
    if not (5 <= len(faces) <= 12):
        return None
    apex = V[vi]
    others = []
    for fi in faces:
        for k in (int(x) for x in fi):
            if k != vi:
                others.append(k)
    others = np.unique(others)
    if len(others) < 5:
        return None
    ov = V[others]
    dy = float(apex[1] - np.median(ov[:, 1]))
    if dy < 0.8 or float(np.std(ov[:, 1])) > 0.05:
        return None
    rad = np.linalg.norm(ov[:, [0, 2]] - apex[[0, 2]], axis=1)
    if float(rad.mean()) < 0.4 or float(rad.std()) > 0.35:
        return None
    return float(rad.max())


def cone_components(V, F, C):
    """Return (keep_components, skipped notes). V is float64."""
    roots = components(F, len(V))
    vf = defaultdict(list)
    for i, f in enumerate(F):
        vf[int(f[0])].append(f)
        vf[int(f[1])].append(f)
        vf[int(f[2])].append(f)
    # apex vertex -> ring radius, if the star around it is a cone
    apex_rad = {}
    for vi, faces in vf.items():
        rad = apex_of(vi, faces, V)
        if rad is not None:
            apex_rad[vi] = rad
    by = defaultdict(list)
    for vi in apex_rad:
        by[int(roots[vi])].append(vi)
    keep = []
    skipped = []
    seen = set()
    for r, apices in by.items():
        if r in seen:
            continue
        seen.add(r)
        sel = np.nonzero(roots == r)[0]
        n = len(sel)
        bb = V[sel].max(0) - V[sel].min(0)
        horiz = float(max(bb[0], bb[2]))
        height = float(bb[1])
        mean = C[sel, :3].mean(0)
        reason = None
        if n > 16 or n < 6:
            reason = "component size %d shares more than a closed tier" % n
        elif height < 1.0:
            reason = "too flat to be a crown (%.2f m)" % height
        elif horiz > 6.0:
            reason = "wider than a pine tier (%.2f m)" % horiz
        elif not (mean[1] > mean[0] + 0.015):
            reason = "not green (rgb %s)" % np.round(mean, 3).tolist()
        else:
            rad = max(apex_rad[i] for i in apices)
            ctr = V[apices[0], [0, 2]]
            spread = np.hypot(V[sel, 0] - ctr[0], V[sel, 2] - ctr[1]).max()
            if spread > rad * 1.4 + 0.35:
                reason = "vertices sprawl outside the ring"
        if reason:
            skipped.append(dict(
                verts=int(n), height=round(height, 2), horiz=round(horiz, 2),
                at=[round(float(x), 2) for x in V[sel].mean(0)],
                why=reason,
            ))
            continue
        keep.append(sel)
    return keep, skipped


def trees_from(parts, V, C):
    """Group stacked tiers that share a trunk axis."""
    items = []
    for sel in parts:
        at = V[sel].mean(0)
        items.append(dict(sel=sel, at=at, y0=float(V[sel, 1].min()), y1=float(V[sel, 1].max()),
                          r=float(np.hypot(V[sel, 0] - at[0], V[sel, 2] - at[2]).max()),
                          col=C[sel, :3].mean(0)))
    used = [False] * len(items)
    groups = []
    for i, it in enumerate(items):
        if used[i]:
            continue
        g = [it]
        used[i] = True
        for j in range(i + 1, len(items)):
            if used[j]:
                continue
            if abs(items[j]["at"][0] - it["at"][0]) < 0.8 and abs(items[j]["at"][2] - it["at"][2]) < 0.8:
                g.append(items[j])
                used[j] = True
        groups.append(g)
    return groups


def pine_crown(center, size, col, lod):
    """Needle fans filling the old cone. No bare pole, no broadleaf ball."""
    h = max(float(size[1]), 0.8)
    r = max(float(max(size[0], size[2])) * 0.5, 0.45)
    m = Mesh()
    rings = int(np.clip(h / (0.62 if lod else 0.36), 3 if lod else 6, 6 if lod else 12))
    boughs = 5 if lod else 9
    for ring in range(rings):
        t = (ring + 0.4) / rings
        y = h * (0.05 + 0.9 * t)
        rad = r * (1.05 - 0.92 * t)
        for k in range(boughs):
            a = (k / boughs) * np.pi * 2.0 + ring * 0.5
            ca, sa = np.cos(a), np.sin(a)
            shells = (0.82,) if lod else (0.42, 0.82)
            for frac in shells:
                up = _norm(np.array([ca * 0.72, 0.48, sa * 0.72]))
                card = float(np.clip(0.34 + rad * 0.42, 0.38, 0.9))
                upv = up * card
                right = _norm(np.cross(up, np.array([ca, 0.0, sa]))) * card
                ctr = np.array([ca * rad * frac, y, sa * rad * frac])
                m.cluster(ctr, right, upv, col, PINE_A if (k + ring) % 2 == 0 else PINE_B)
    return _place(m, center, size)


def build_canopy(groups, lod):
    Vs, Fs, Cs, UVs, Ns, Ts = [], [], [], [], [], []
    base = 0
    for g in groups:
        y0 = min(t["y0"] for t in g)
        y1 = max(t["y1"] for t in g)
        r = max(t["r"] for t in g)
        col = np.mean([t["col"] for t in g], axis=0)
        xz = np.mean([t["at"][[0, 2]] for t in g], axis=0)
        h = max(y1 - y0, 0.8)
        center = np.array([xz[0], (y0 + y1) * 0.5, xz[1]])
        size = np.array([max(r * 2, 0.8), h, max(r * 2, 0.8)])
        built = pine_crown(center, size, col, lod)
        if built is None:
            continue
        V, F, C, UV, N, T = built
        Vs.append(V)
        Fs.append(F + base)
        Cs.append(C)
        UVs.append(UV)
        Ns.append(N)
        Ts.append(T)
        base += len(V)
    if not Vs:
        return None
    return (np.concatenate(Vs), np.concatenate(Fs), np.concatenate(Cs),
            np.concatenate(UVs), np.concatenate(Ns), np.concatenate(Ts))


def canopy_name(island_name):
    # arch_isl_gullhaven -> arch_canopy_gullhaven. Avoid _isl_ so the terrain shader skips it.
    stem = island_name[:-4]
    lod = stem.endswith("_lod1")
    if lod:
        stem = stem[:-5]
    stem = stem.replace("_isl_", "_canopy_")
    if lod:
        stem += "_lod1"
    return stem + ".glb"


def main():
    report = {"removed": [], "skipped_files": [], "ambiguous": []}
    for dp, _, fs in os.walk(ROOT):
        for fn in sorted(fs):
            if not fn.endswith(".glb"):
                continue
            if "isl" not in fn and "island" not in fn:
                continue
            if "_glow" in fn or "_col" in fn:
                continue
            path = os.path.join(dp, fn)
            V, N, C, F = load_glb(path)
            Vc = V.astype(np.float64)
            Cc = C.astype(np.float64) / 255.0
            parts, skipped = cone_components(Vc, F, Cc)
            if skipped:
                report["ambiguous"].append({"file": os.path.relpath(path, ROOT), "parts": skipped})
            if not parts:
                continue
            keep = np.ones(len(V), np.bool_)
            for sel in parts:
                keep[sel] = False
            # faces that use a removed vertex go with the cone
            face_keep = keep[F].all(1)
            if not face_keep.any():
                report["skipped_files"].append(os.path.relpath(path, ROOT) + " would be empty")
                continue
            remap = -np.ones(len(V), np.int64)
            remap[keep] = np.arange(int(keep.sum()))
            F2 = remap[F[face_keep]]
            V2, N2, C2 = V[keep], N[keep], C[keep]
            before = V[keep].tobytes() + N[keep].tobytes() + C[keep].tobytes()
            write_exact(path, V2, N2, C2, F2, fn[:-4])
            Vr, Nr, Cr, Fr = load_glb(path)
            after = Vr.tobytes() + Nr.tobytes() + Cr.tobytes()
            if before != after or len(Fr) != len(F2):
                raise SystemExit("vertex bytes moved in " + fn)
            groups = trees_from(parts, Vc, Cc)
            built = build_canopy(groups, fn.endswith("_lod1.glb"))
            out_name = canopy_name(fn)
            out_path = os.path.join(dp, out_name)
            faces = 0
            if built is not None:
                write_glb(out_path, built[0], built[1].astype(np.uint32), built[2], built[4], built[3], built[5], out_name[:-4])
                faces = len(built[1])
            report["removed"].append(dict(
                file=os.path.relpath(path, ROOT),
                canopy=os.path.relpath(out_path, ROOT),
                tiers=len(parts),
                trees=len(groups),
                cone_verts=int((~keep).sum()),
                kept_verts=int(keep.sum()),
                kept_faces=int(face_keep.sum()),
                canopy_faces=faces,
                kept_position_sha256=__import__("hashlib").sha256(V[keep].tobytes()).hexdigest(),
            ))
            print(fn, "tiers", len(parts), "trees", len(groups), "kept", int(keep.sum()), "canopy faces", faces)
    rep = os.path.join(ROOT, "island_cone_report.json")
    with open(rep, "w") as f:
        json.dump(report, f, indent=1)
    print("report", rep, "files", len(report["removed"]))


if __name__ == "__main__":
    main()
