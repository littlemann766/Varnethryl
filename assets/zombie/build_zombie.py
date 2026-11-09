#!/usr/bin/env python3
"""Original Varnethryl zombie meshes.

Skins a 21-joint humanoid whose rest pose and clip curves come from the
game's kael voxel rig (same joint names and rest as characters/kael_lod1.glb).
Mesh and textures are procedural and original. Owner concept sheets are style
reference only and are not sampled into the maps.
"""
from __future__ import annotations

import json
import math
import struct
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
SRC = ROOT / "voxel" / "kael_voxel.glb"
TEX = OUT / "textures"

CORE = [
    "root", "hips", "spine", "chest", "cape", "neck", "head",
    "shoulder_L", "upperArm_L", "foreArm_L", "hand_L",
    "shoulder_R", "upperArm_R", "foreArm_R", "hand_R",
    "thigh_L", "shin_L", "foot_L", "thigh_R", "shin_R", "foot_R",
]
PARENT = {
    "hips": "root", "spine": "hips", "chest": "spine", "cape": "chest",
    "neck": "chest", "head": "neck",
    "shoulder_L": "chest", "upperArm_L": "shoulder_L", "foreArm_L": "upperArm_L", "hand_L": "foreArm_L",
    "shoulder_R": "chest", "upperArm_R": "shoulder_R", "foreArm_R": "upperArm_R", "hand_R": "foreArm_R",
    "thigh_L": "hips", "shin_L": "thigh_L", "foot_L": "shin_L",
    "thigh_R": "hips", "shin_R": "thigh_R", "foot_R": "shin_R",
}
CHILD = {p: c for c, p in PARENT.items()}
CLIPS = ["idle", "walk", "run", "attack1", "attack2", "attack3", "hit", "death"]

# UV islands in 0..1, v up. Mesh UVs stay inside; paint covers the whole island.
RECT = {
    "face": (0.015, 0.610, 0.400, 0.985),
    "scalp": (0.410, 0.780, 0.600, 0.985),
    "body": (0.610, 0.560, 0.985, 0.985),
    "eye": (0.410, 0.620, 0.500, 0.760),
    "tooth": (0.510, 0.620, 0.600, 0.760),
    "blood": (0.860, 0.500, 0.985, 0.555),
    "dress": (0.015, 0.300, 0.340, 0.545),
    "tunic": (0.350, 0.300, 0.590, 0.545),
    "cloak": (0.600, 0.300, 0.985, 0.545),
    "sailor": (0.015, 0.020, 0.250, 0.270),
    "leather": (0.260, 0.020, 0.480, 0.270),
    "metal": (0.490, 0.020, 0.720, 0.270),
    "hair": (0.730, 0.020, 0.985, 0.270),
}

HEAD_LAT, HEAD_LON = 44, 56
S = 2048


def load_glb(path):
    data = Path(path).read_bytes()
    off = 12
    js = blob = None
    while off < len(data):
        ln, typ = struct.unpack_from("<I4s", data, off)
        off += 8
        chunk = data[off:off + ln]
        off += ln
        if typ == b"JSON":
            js = json.loads(chunk)
        elif typ == b"BIN\x00":
            blob = chunk
    return js, blob


def read_acc(js, blob, i):
    a = js["accessors"][i]
    bv = js["bufferViews"][a["bufferView"]]
    start = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
    ctype = {5120: "b", 5121: "B", 5122: "h", 5123: "H", 5125: "I", 5126: "f"}[a["componentType"]]
    ncomp = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}[a["type"]]
    count = a["count"]
    el = np.dtype({"b": "i1", "B": "u1", "h": "<i2", "H": "<u2", "I": "<u4", "f": "<f4"}[ctype])
    stride = bv.get("byteStride", el.itemsize * ncomp)
    if stride == el.itemsize * ncomp:
        arr = np.frombuffer(blob, dtype=el, count=count * ncomp, offset=start)
        return arr.reshape(count, ncomp) if ncomp > 1 else arr
    arr = np.empty((count, ncomp), dtype=el)
    for k in range(count):
        arr[k] = np.frombuffer(blob, dtype=el, count=ncomp, offset=start + k * stride)
    return arr


def qmat(q):
    x, y, z, w = q
    return np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
    ], np.float64)


def trs(t, r, s):
    M = np.eye(4)
    M[:3, :3] = qmat(r) @ np.diag(s)
    M[:3, 3] = t
    return M


def nrm(v):
    L = np.linalg.norm(v)
    return v / L if L > 1e-8 else v * 0


def frame(direction, hint=None):
    t = nrm(np.asarray(direction, np.float64))
    h = np.array([0.0, 0.0, 1.0] if hint is None else hint, np.float64)
    s = np.cross(t, h)
    if np.linalg.norm(s) < 1e-4:
        h = np.array([0.0, 1.0, 0.0] if abs(t[1]) < 0.9 else [1.0, 0.0, 0.0])
        s = np.cross(t, h)
    s = nrm(s)
    f = nrm(np.cross(s, t))
    return s, t, f


def slerp(a, b, u):
    d = float(np.dot(a, b))
    if d < 0:
        b = -b
        d = -d
    if d > 0.9995:
        return nrm(a * (1 - u) + b * u)
    th = math.acos(max(-1.0, min(1.0, d)))
    s = math.sin(th)
    return (math.sin((1 - u) * th) * a + math.sin(u * th) * b) / s


class Rig:
    def __init__(self, path):
        js, blob = load_glb(path)
        self.js, self.blob = js, blob
        self.nodes = js["nodes"]
        self.by = {n["name"]: i for i, n in enumerate(self.nodes)}
        self.parent = {}
        for i, n in enumerate(self.nodes):
            for c in n.get("children", []):
                self.parent[c] = i
        self.rest = {}
        for nm in CORE:
            n = self.nodes[self.by[nm]]
            self.rest[nm] = (
                np.array(n.get("translation", [0, 0, 0]), np.float64),
                np.array(n.get("rotation", [0, 0, 0, 1]), np.float64),
                np.array(n.get("scale", [1, 1, 1]), np.float64),
            )
        self.clips = {}
        for anim in js["animations"]:
            if anim["name"] not in CLIPS:
                continue
            chans = {}
            tmax = 0.0
            for ch in anim["channels"]:
                nm = self.nodes[ch["target"]["node"]]["name"]
                if nm not in CORE:
                    continue
                samp = anim["samplers"][ch["sampler"]]
                times = read_acc(js, blob, samp["input"]).astype(np.float64)
                vals = read_acc(js, blob, samp["output"]).astype(np.float64)
                tmax = max(tmax, float(times[-1]))
                chans.setdefault(nm, {})[ch["target"]["path"]] = (
                    times, vals, samp.get("interpolation", "LINEAR")
                )
            self.clips[anim["name"]] = {"length": tmax, "channels": chans}
        self.bind = self.pose(None, 0.0)

    def _sample(self, ch, t):
        times, vals, interp = ch
        if t <= times[0]:
            return vals[0]
        if t >= times[-1]:
            return vals[-1]
        i = int(np.searchsorted(times, t) - 1)
        i = max(0, min(i, len(times) - 2))
        if interp == "STEP":
            return vals[i]
        u = (t - times[i]) / (times[i + 1] - times[i] + 1e-12)
        a, b = vals[i], vals[i + 1]
        if a.shape[0] == 4:
            return slerp(a, b, float(u))
        return a * (1 - u) + b * u

    def locals_at(self, clip, t):
        loc = {k: (v[0].copy(), v[1].copy(), v[2].copy()) for k, v in self.rest.items()}
        if clip and clip in self.clips:
            for nm, paths in self.clips[clip]["channels"].items():
                t0, r0, s0 = loc[nm]
                if "translation" in paths:
                    t0 = np.array(self._sample(paths["translation"], t), np.float64)
                if "rotation" in paths:
                    r0 = np.array(self._sample(paths["rotation"], t), np.float64)
                if "scale" in paths:
                    s0 = np.array(self._sample(paths["scale"], t), np.float64)
                loc[nm] = (t0, r0, s0)
        return loc

    def pose(self, clip, t):
        loc = self.locals_at(clip, t)
        world = {}

        def walk(nm, parent_m):
            M = parent_m @ trs(*loc[nm])
            world[nm] = M
            for child, par in PARENT.items():
                if par == nm:
                    walk(child, M)

        walk("root", np.eye(4))
        return world

    def origins(self, world):
        return {k: world[k][:3, 3].copy() for k in world}

    def length_error(self, clip, samples=12):
        L = self.clips[clip]["length"]
        bind_o = self.origins(self.bind)
        worst = 0.0
        worst_name = ""
        scale_max = 1.0
        for s in range(samples):
            t = L * s / max(samples - 1, 1)
            loc = self.locals_at(clip, t)
            W = self.pose(clip, t)
            O = self.origins(W)
            for nm, sc in loc.items():
                scale_max = max(scale_max, float(np.max(np.abs(sc[2] - 1.0)) + 1.0))
            for child, par in PARENT.items():
                if par not in bind_o or child not in ("spine", "chest", "neck", "head",
                    "upperArm_L", "foreArm_L", "hand_L", "thigh_L", "shin_L", "foot_L",
                    "upperArm_R", "foreArm_R", "hand_R", "thigh_R", "shin_R", "foot_R",
                    "shoulder_L", "shoulder_R"):
                    continue
                b = np.linalg.norm(bind_o[child] - bind_o[par])
                p = np.linalg.norm(O[child] - O[par])
                if b < 1e-4:
                    continue
                err = abs(p - b)
                if err > worst:
                    worst = err
                    worst_name = f"{par}->{child}"
        return {"max_bone_stretch_m": round(worst, 4), "bone": worst_name, "max_scale": round(scale_max, 4)}


BONE_INDEX = {nm: i for i, nm in enumerate(CORE)}


class Prim:
    def __init__(self):
        self.pos = []
        self.uv = []
        self.j = []
        self.w = []
        self.idx = []

    def add(self, p, uv, bone, bone2=None, w2=0.0):
        self.pos.append(np.asarray(p, np.float64))
        self.uv.append((float(min(0.995, max(0.005, uv[0]))), float(min(0.995, max(0.005, uv[1])))))
        j0 = BONE_INDEX[bone]
        w2 = float(max(0.0, min(1.0, w2)))
        if bone2 and w2 > 0.001:
            self.j.append((j0, BONE_INDEX[bone2], 0, 0))
            self.w.append((1.0 - w2, w2, 0.0, 0.0))
        else:
            self.j.append((j0, 0, 0, 0))
            self.w.append((1.0, 0.0, 0.0, 0.0))
        return len(self.pos) - 1

    def tri(self, i, j, k, center):
        P = self.pos
        n = np.cross(P[j] - P[i], P[k] - P[i])
        mid = (P[i] + P[j] + P[k]) / 3.0
        if np.dot(n, mid - center) < 0:
            j, k = k, j
        self.idx.extend((int(i), int(j), int(k)))

    def finish(self):
        if not self.idx:
            self.P = np.zeros((0, 3), np.float32)
            self.N = np.zeros((0, 3), np.float32)
            self.UV = np.zeros((0, 2), np.float32)
            self.J = np.zeros((0, 4), np.uint16)
            self.W = np.zeros((0, 4), np.float32)
            self.I = np.zeros((0, 3), np.int32)
            return self
        P = np.asarray(self.pos, np.float64)
        I = np.asarray(self.idx, np.int32).reshape(-1, 3)
        n = np.zeros_like(P)
        fn = np.cross(P[I[:, 1]] - P[I[:, 0]], P[I[:, 2]] - P[I[:, 0]])
        for k in range(3):
            np.add.at(n, I[:, k], fn)
        ln = np.linalg.norm(n, axis=1, keepdims=True)
        ln[ln < 1e-12] = 1.0
        self.P = P.astype(np.float32)
        self.N = (n / ln).astype(np.float32)
        self.UV = np.asarray(self.uv, np.float32)
        self.J = np.asarray(self.j, np.uint16)
        self.W = np.asarray(self.w, np.float32)
        self.I = I
        return self

    @property
    def tris(self):
        return len(self.idx) // 3


def add_limb(prim, p0, p1, r0, r1, rect, bone, parent=None, sides=12, rings=6, bulge=0.08, overlap=0.0):
    p0 = np.asarray(p0, np.float64)
    p1 = np.asarray(p1, np.float64)
    d = p1 - p0
    if np.linalg.norm(d) < 1e-4:
        return
    if overlap > 0:
        p0 = p0 - nrm(d) * overlap
        d = p1 - p0
    right, tang, fwd = frame(d)
    cols = sides + 1
    ids = []
    span = np.linalg.norm(d)
    blend = min(0.22, (overlap + 0.02) / max(span, 1e-3)) if parent else 0.0
    for i in range(rings + 1):
        t = i / rings
        c = p0 + d * t
        r = r0 + (r1 - r0) * t
        r *= 1.0 + bulge * math.sin(t * math.pi)
        w2 = 0.0
        b2 = None
        if parent and t < blend:
            b2 = parent
            w2 = 1.0 - t / blend
        row = []
        for s in range(cols):
            ang = math.tau * s / sides
            p = c + right * math.cos(ang) * r + fwd * math.sin(ang) * r
            u = rect[0] + (s / sides) * (rect[2] - rect[0])
            v = rect[1] + (1.0 - t) * (rect[3] - rect[1])
            row.append(prim.add(p, (u, v), bone, b2, w2))
        ids.append(row)
    for i in range(rings):
        c = p0 + d * ((i + 0.5) / rings)
        for s in range(sides):
            a, b = ids[i][s], ids[i][s + 1]
            c3, d3 = ids[i + 1][s + 1], ids[i + 1][s]
            prim.tri(a, b, c3, c)
            prim.tri(a, c3, d3, c)


def add_loft(prim, stations, rect, sides=18, closed=True, ang0=0.0, ang1=None):
    if ang1 is None:
        ang1 = math.tau if closed else 0.0
    rings = len(stations)
    cols = sides + 1
    ids = []
    for i, st in enumerate(stations):
        row = []
        v = rect[1] + (i / max(rings - 1, 1)) * (rect[3] - rect[1])
        bone = st["bone"]
        b2 = st.get("bone2")
        w2 = st.get("w2", 0.0)
        for s in range(cols):
            ang = ang0 + (ang1 - ang0) * (s / sides)
            p = st["pos"] + np.array([math.sin(ang) * st["rx"], 0.0, math.cos(ang) * st["rz"]])
            if "nudge" in st:
                p = p + st["nudge"] * (0.35 + 0.65 * abs(math.sin(ang)))
            u = rect[0] + (s / sides) * (rect[2] - rect[0])
            row.append(prim.add(p, (u, v), bone, b2, w2))
        ids.append(row)
    for i in range(rings - 1):
        c = (stations[i]["pos"] + stations[i + 1]["pos"]) * 0.5
        for s in range(sides if closed or True else cols - 1):
            if s >= cols - 1:
                continue
            a, b = ids[i][s], ids[i][s + 1]
            c3, d3 = ids[i + 1][s + 1], ids[i + 1][s]
            prim.tri(a, b, c3, c)
            prim.tri(a, c3, d3, c)


def add_sphere(prim, center, radius, rect, bone, lat, lon, disp):
    center = np.asarray(center, np.float64)
    ids = []
    for iy in range(lat + 1):
        theta = math.pi * iy / lat
        row = []
        for ix in range(lon + 1):
            ang = math.tau * ix / lon
            st, ct = math.sin(theta), math.cos(theta)
            # Seam (ang 0 / full turn) sits on the back of the head, not down the nose.
            x = st * math.sin(ang)
            y = ct
            z = -st * math.cos(ang)
            r = radius * disp(x, y, z)
            p = center + np.array([x, y, z]) * r
            # front gets the face island, back the scalp
            if z > -0.05:
                u = rect[0] + (x * 0.5 + 0.5) * (rect[2] - rect[0])
                v = rect[1] + (y * 0.5 + 0.5) * (rect[3] - rect[1])
            else:
                sc = RECT["scalp"]
                u = sc[0] + (x * 0.5 + 0.5) * (sc[2] - sc[0])
                v = sc[1] + (y * 0.5 + 0.5) * (sc[3] - sc[1])
            row.append(prim.add(p, (u, v), bone))
        ids.append(row)
    for iy in range(lat):
        for ix in range(lon):
            a, b = ids[iy][ix], ids[iy][ix + 1]
            c3, d3 = ids[iy + 1][ix + 1], ids[iy + 1][ix]
            prim.tri(a, b, c3, center)
            prim.tri(a, c3, d3, center)


def add_box(prim, center, ax, ay, az, size, rect, bone):
    center = np.asarray(center, np.float64)
    ax, ay, az = nrm(ax), nrm(ay), nrm(az)
    sx, sy, sz = size
    signs = [(-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1),
             (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)]
    ids = []
    for i, (a, b, c) in enumerate(signs):
        p = center + ax * (a * sx) + ay * (b * sy) + az * (c * sz)
        u = rect[0] + (0.2 + 0.6 * (a > 0)) 
        v = rect[1] + (0.2 + 0.6 * (b > 0))
        ids.append(prim.add(p, (u, v), bone))
    faces = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (2, 6, 7, 3), (0, 3, 7, 4), (1, 5, 6, 2)]
    for f in faces:
        prim.tri(ids[f[0]], ids[f[1]], ids[f[2]], center)
        prim.tri(ids[f[0]], ids[f[2]], ids[f[3]], center)


def add_ribbon(prim, pts, width, rect, bone, up=None):
    pts = [np.asarray(p, np.float64) for p in pts]
    if len(pts) < 2:
        return
    cols = []
    for i, p in enumerate(pts):
        d = pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]
        side = np.cross(nrm(d), np.array([0.0, 1.0, 0.0]) if up is None else up)
        if np.linalg.norm(side) < 1e-4:
            side = np.array([1.0, 0.0, 0.0])
        side = nrm(side) * width * (1.0 - 0.25 * i / max(len(pts) - 1, 1))
        v = rect[3] - (i / max(len(pts) - 1, 1)) * (rect[3] - rect[1])
        cols.append((
            prim.add(p + side, (rect[0], v), bone),
            prim.add(p - side, (rect[2], v), bone),
        ))
    for i in range(len(pts) - 1):
        a, b = cols[i]
        c, d = cols[i + 1]
        mid = (pts[i] + pts[i + 1]) * 0.5
        prim.tri(a, c, b, mid - np.array([0, 0, 0.2]))
        prim.tri(b, c, d, mid - np.array([0, 0, 0.2]))


def add_torus(prim, center, axis, radius, tube, rect, bone, n=12, m=5):
    center = np.asarray(center, np.float64)
    axis = nrm(np.asarray(axis, np.float64))
    right, _, fwd = frame(axis, [1.0, 0.0, 0.0])
    ids = []
    for i in range(n + 1):
        a = math.tau * i / n
        spine = center + (right * math.cos(a) + fwd * math.sin(a)) * radius
        row = []
        radial = nrm(spine - center)
        side = nrm(np.cross(axis, radial))
        for j in range(m + 1):
            b = math.tau * j / m
            p = spine + (radial * math.cos(b) + axis * math.sin(b)) * tube
            u = rect[0] + (i / n) * (rect[2] - rect[0])
            v = rect[1] + (j / m) * (rect[3] - rect[1])
            row.append(prim.add(p, (u, v), bone))
        ids.append(row)
    for i in range(n):
        for j in range(m):
            c = center
            prim.tri(ids[i][j], ids[i + 1][j], ids[i + 1][j + 1], c)
            prim.tri(ids[i][j], ids[i + 1][j + 1], ids[i][j + 1], c)


def head_disp(x, y, z):
    r = 1.0
    # narrower jaw, fuller cranium
    if y < 0.05:
        r *= 1.0 - 0.28 * ((0.05 - y) ** 1.15)
    if y > 0.15:
        r *= 1.04
    # cheeks
    cheek = math.exp(-((abs(x) - 0.42) ** 2) / 0.05 - ((y + 0.02) ** 2) / 0.04)
    if z > 0:
        r -= 0.16 * cheek * max(z, 0)
    # nose
    nose = math.exp(-(x ** 2) / 0.014 - ((y - 0.02) ** 2) / 0.02)
    if z > 0:
        r += 0.20 * nose * max(z, 0.0)
    # sockets
    for sx in (-0.30, 0.32):
        eye = math.exp(-((x - sx) ** 2) / 0.012 - ((y - 0.14) ** 2) / 0.007)
        if z > 0:
            r -= 0.42 * eye * max(z, 0)
    # brow ridge
    brow = math.exp(-(x ** 2) / 0.20 - ((y - 0.30) ** 2) / 0.012)
    if z > 0:
        r += 0.14 * brow * max(z, 0)
    # chin
    chin = math.exp(-(x ** 2) / 0.02 - ((y + 0.62) ** 2) / 0.03)
    if z > 0 and y < -0.35:
        r += 0.10 * chin
    # one temple eaten away
    if x > 0.2 and -0.05 < y < 0.35 and z > 0:
        r -= 0.06 * max(z, 0) * min(x, 0.5)
    # mouth recess, kept shallow so the jaw stays attached to the neck
    mouth = math.exp(-(x ** 2) / 0.025 - ((y + 0.36) ** 2) / 0.016)
    if z > 0:
        r -= 0.12 * mouth * max(z, 0)
    return max(0.62, r)


def build_head(opaque, cloth, center, sex):
    center = np.asarray(center, np.float64)
    add_sphere(opaque, center, 0.122 if sex == "m" else 0.114, RECT["face"], "head", HEAD_LAT, HEAD_LON, head_disp)
    # eyes sit in the sockets, milky and slightly proud of the surface
    for sx, alive in ((-0.032, True), (0.034, sex == "f")):
        eye_c = center + np.array([sx, 0.012, 0.100])
        if alive:
            add_sphere(opaque, eye_c, 0.015, RECT["eye"], "head", 8, 10, lambda x, y, z: 1.0)
        else:
            add_sphere(opaque, eye_c + np.array([0, -0.006, -0.015]), 0.011, RECT["blood"], "head", 6, 8, lambda x, y, z: 0.65)
    # teeth, a little forward of the mouth recess so they read at arm's length
    for upper, yoff in ((True, 0.010), (False, -0.014)):
        count = 7 if upper else 6
        for i in range(count):
            if upper and i in (2, 5):
                continue
            x = -0.028 + (0.056 * i / max(count - 1, 1))
            p = center + np.array([x, -0.042 + yoff, 0.078])
            add_box(opaque, p, np.array([1, 0, 0]), np.array([0, 1, 0]), np.array([0, 0, 1]),
                    (0.0042, 0.007 if upper else 0.006, 0.004), RECT["tooth"], "head")
    # ears
    for sx in (-1.0, 1.0):
        e = center + np.array([sx * 0.10, -0.005, 0.0])
        add_sphere(opaque, e, 0.022, RECT["body"], "head", 6, 8, lambda x, y, z: 0.55 + 0.2 * max(z, 0))


def build_hand(opaque, wrist, elbow, bone, side):
    wrist = np.asarray(wrist, np.float64)
    d = nrm(wrist - np.asarray(elbow, np.float64))
    fwd = np.array([0.0, 0.0, 1.0])
    up = np.array([0.0, 1.0, 0.0])
    palm_r = 0.034 if side > 0 else 0.032
    add_limb(opaque, wrist, wrist + d * 0.045, palm_r, palm_r * 0.86, RECT["body"], bone, sides=8, rings=3, bulge=0.02)
    spreads = [-0.020, -0.007, 0.006, 0.018]
    for i, off in enumerate(spreads):
        root = wrist + d * 0.04 + fwd * off + up * (-0.004)
        curl = d
        rad = 0.011 - i * 0.0004
        p = root
        for seg in range(3):
            curl = nrm(curl * 0.62 + np.array([0.0, -1.0, 0.0]) * 0.55 + fwd * (0.04 if i != 2 else -0.02))
            step = 0.038 - seg * 0.008
            nxt = p + curl * step
            rect = RECT["blood"] if seg == 2 else RECT["body"]
            add_limb(opaque, p, nxt, rad, rad * 0.72, rect, bone, sides=5, rings=2, bulge=0.0)
            p = nxt
            rad *= 0.78
    # thumb
    troot = wrist + d * 0.02 + fwd * 0.012 + up * 0.01
    td = nrm(d * 0.35 + fwd * 0.85 + up * 0.15)
    p = troot
    rad = 0.012
    for seg in range(2):
        td = nrm(td * 0.7 + np.array([0.0, -0.6, 0.4]))
        nxt = p + td * (0.032 - seg * 0.008)
        add_limb(opaque, p, nxt, rad, rad * 0.7, RECT["blood"] if seg else RECT["body"], bone, sides=5, rings=2, bulge=0.0)
        p = nxt
        rad *= 0.75


def build_foot(opaque, cloth, ankle, side, boot):
    ankle = np.asarray(ankle, np.float64)
    s = 1.0 if side > 0 else -1.0
    heel = ankle + np.array([s * 0.01, -0.062, -0.04])
    ball = ankle + np.array([s * 0.012, -0.055, 0.085])
    toe = ankle + np.array([s * 0.01, -0.050, 0.155])
    bone = "foot_L" if side > 0 else "foot_R"
    if boot:
        add_limb(opaque, ankle + np.array([0, 0.02, 0]), heel, 0.048, 0.052, RECT["leather"], bone, sides=10, rings=3, bulge=0.04)
        add_limb(opaque, heel, ball, 0.052, 0.046, RECT["leather"], bone, sides=10, rings=3, bulge=0.02)
        add_limb(opaque, ball, toe, 0.046, 0.030, RECT["leather"], bone, sides=8, rings=2, bulge=0.0)
        # cuff
        add_torus(opaque, ankle + np.array([0, 0.01, 0.01]), np.array([0, 1, 0]), 0.055, 0.012, RECT["leather"], bone, n=10, m=4)
    else:
        add_limb(opaque, ankle, heel, 0.040, 0.046, RECT["body"], bone, sides=8, rings=3, bulge=0.05)
        add_limb(opaque, heel, ball, 0.046, 0.036, RECT["body"], bone, sides=8, rings=3, bulge=0.0)
        add_limb(opaque, ball, toe, 0.034, 0.022, RECT["body"], bone, sides=7, rings=2, bulge=0.0)
        for i in range(5):
            xoff = -0.02 + i * 0.01
            a = toe + np.array([s * xoff, 0.004, 0.01])
            b = a + np.array([s * 0.002, -0.004, 0.028])
            add_limb(opaque, a, b, 0.010, 0.006, RECT["blood"] if i == 0 else RECT["body"], bone, sides=4, rings=1, bulge=0.0)


def sex_dims(sex):
    if sex == "f":
        return dict(hipx=0.132, hipz=0.100, waistx=0.108, waistz=0.084, chestx=0.128, chestz=0.098,
                    thigh=0.078, knee=0.050, calf=0.046, ankle=0.036, arm=0.042, elbow=0.034, wrist=0.026, neck=0.046)
    return dict(hipx=0.128, hipz=0.102, waistx=0.122, waistz=0.096, chestx=0.158, chestz=0.118,
                thigh=0.086, knee=0.055, calf=0.050, ankle=0.040, arm=0.050, elbow=0.040, wrist=0.030, neck=0.050)


def build_body(opaque, J, sex):
    D = sex_dims(sex)
    hips, spine, chest = J["hips"], J["spine"], J["chest"]
    neck, head = J["neck"], J["head"]
    shoulder = J["shoulder_L"]
    back = np.array([0.0, 0.0, -1.0])
    # Mild hunch: the upper back bows back a few centimetres. The shoulder line stays wide
    # so the deltoids meet the chest instead of floating.
    stations = [
        dict(pos=hips + np.array([0, -0.05, 0.0]), rx=D["hipx"], rz=D["hipz"], bone="hips"),
        dict(pos=hips * 0.4 + spine * 0.6 + back * 0.015, rx=D["waistx"], rz=D["waistz"], bone="hips", bone2="spine", w2=0.4),
        dict(pos=spine + back * 0.025, rx=D["waistx"] + 0.01, rz=D["waistz"] + 0.008, bone="spine"),
        dict(pos=spine * 0.35 + chest * 0.65 + back * 0.03, rx=D["chestx"] * 0.94, rz=D["chestz"], bone="spine", bone2="chest", w2=0.5),
        dict(pos=chest + back * 0.032, rx=D["chestx"], rz=D["chestz"], bone="chest"),
        dict(pos=np.array([0.0, shoulder[1] - 0.02, chest[2] - 0.02]), rx=abs(shoulder[0]) + 0.06, rz=0.11, bone="chest"),
        dict(pos=neck + np.array([0, -0.02, 0.0]), rx=D["neck"] + 0.01, rz=D["neck"], bone="neck", bone2="chest", w2=0.4),
    ]
    add_loft(opaque, stations, RECT["body"], sides=22)
    head_c = head + np.array([0.0, 0.072, 0.018])
    add_limb(opaque, neck + np.array([0, -0.04, 0]), head_c + np.array([0, -0.06, -0.01]), D["neck"] + 0.012, D["neck"] + 0.006, RECT["body"], "neck", "chest", sides=12, rings=4, bulge=0.05, overlap=0.03)
    build_head(opaque, None, head_c, sex)
    for side, tag in ((1, "L"), (-1, "R")):
        sh, ua, fa, ha = J[f"shoulder_{tag}"], J[f"upperArm_{tag}"], J[f"foreArm_{tag}"], J[f"hand_{tag}"]
        add_limb(opaque, sh, ua, 0.058 if sex == "m" else 0.050, D["arm"] + 0.004, RECT["body"], f"shoulder_{tag}", "chest", sides=12, rings=5, bulge=0.06, overlap=0.05)
        add_limb(opaque, ua, fa, D["arm"], D["elbow"], RECT["body"], f"upperArm_{tag}", f"shoulder_{tag}", sides=12, rings=6, bulge=0.10, overlap=0.035)
        add_limb(opaque, fa, ha, D["elbow"], D["wrist"], RECT["body"], f"foreArm_{tag}", f"upperArm_{tag}", sides=12, rings=6, bulge=0.06, overlap=0.025)
        build_hand(opaque, ha, fa, f"hand_{tag}", side)
        th, shn, ft = J[f"thigh_{tag}"], J[f"shin_{tag}"], J[f"foot_{tag}"]
        add_limb(opaque, th, shn, D["thigh"], D["knee"], RECT["body"], f"thigh_{tag}", "hips", sides=12, rings=7, bulge=0.08, overlap=0.03)
        add_limb(opaque, shn, ft, D["knee"] * 1.05, D["ankle"], RECT["body"], f"shin_{tag}", f"thigh_{tag}", sides=12, rings=7, bulge=0.12, overlap=0.025)
    # chest wound dent via a few ribs on males is added by the caller
    return head_c


def add_ribs(opaque, chest):
    for i, y in enumerate((0.02, -0.02, -0.06)):
        c = chest + np.array([0.0, y, 0.02])
        add_torus(opaque, c, np.array([1.0, 0.15, 0.0]), 0.09 - i * 0.008, 0.006, RECT["tooth"], "chest", n=14, m=4)


def add_hood(cloth, head_c):
    # partial shell, open at the face and under the chin
    center = head_c + np.array([0.0, 0.02, -0.02])
    radius = 0.155
    lat, lon = 14, 18
    ids = {}
    for iy in range(lat + 1):
        theta = math.pi * iy / lat
        for ix in range(lon + 1):
            ang = math.tau * ix / lon - math.pi
            st, ct = math.sin(theta), math.cos(theta)
            x = st * math.sin(ang)
            y = ct
            z = st * math.cos(ang)
            # Face and throat stay open. The hood is the back and the crown only.
            if z > -0.05 and y < 0.62:
                continue
            if y < -0.25:
                continue
            r = radius * (1.0 + 0.04 * math.sin(ang * 5 + iy))
            p = center + np.array([x, y, z]) * r
            u = RECT["cloak"][0] + (ix / lon) * (RECT["cloak"][2] - RECT["cloak"][0]) * 0.5 + 0.02
            v = RECT["cloak"][1] + 0.55 + (1 - iy / lat) * 0.4 * (RECT["cloak"][3] - RECT["cloak"][1])
            v = min(RECT["cloak"][3] - 0.01, max(RECT["cloak"][1] + 0.25, v))
            ids[(iy, ix)] = cloth.add(p, (u, v), "head")
    for iy in range(lat):
        for ix in range(lon):
            quad = [(iy, ix), (iy, ix + 1), (iy + 1, ix + 1), (iy + 1, ix)]
            if not all(q in ids for q in quad):
                continue
            a, b, c, d = (ids[q] for q in quad)
            cloth.tri(a, b, c, center)
            cloth.tri(a, c, d, center)


def add_hair(cloth, head_c, kind):
    scalp = head_c + np.array([0.0, 0.07, -0.02])
    n = {"long": 18, "medium": 12, "short": 8}[kind]
    length = {"long": 0.42, "medium": 0.22, "short": 0.08}[kind]
    rng = np.random.default_rng(7 if kind == "long" else 3)
    for i in range(n):
        ang = rng.uniform(-2.4, 2.4)
        side = math.sin(ang)
        back = -abs(math.cos(ang))
        if kind == "long" and i < 4:
            back = 0.35  # a few locks over the face
            side = -0.7 + i * 0.45
        p0 = scalp + np.array([side * 0.07, 0.02, back * 0.04])
        pts = [p0]
        p = p0
        segs = 5 if kind != "short" else 2
        for s in range(segs):
            fall = np.array([
                side * 0.012 + rng.normal(0, 0.006),
                -length / segs,
                (0.03 if back > 0 else -0.02) + rng.normal(0, 0.008),
            ])
            p = p + fall
            pts.append(p)
        width = 0.010 if kind == "short" else 0.014
        add_ribbon(cloth, pts, width, RECT["hair"], "head")


def add_skirt(cloth, hips, rect, length, r0, r1, bone="hips", sides=18, front_open=0.0):
    hips = np.asarray(hips, np.float64)
    rings = 8
    stations = []
    for i in range(rings):
        t = i / (rings - 1)
        y = -0.02 - length * t
        # flare
        rx = r0 + (r1 - r0) * (t ** 0.85)
        rz = rx * 0.82
        stations.append(dict(pos=hips + np.array([0, y, -0.01 - 0.02 * t]), rx=rx, rz=rz, bone=bone))
    ang0 = front_open
    ang1 = math.tau - front_open
    add_loft(cloth, stations, rect, sides=sides, closed=front_open < 0.05, ang0=ang0, ang1=ang1)


def add_cloak(cloth, chest, hips, length=0.85):
    chest = np.asarray(chest, np.float64)
    hips = np.asarray(hips, np.float64)
    # upper shell on the chest, open at the front
    top = chest + np.array([0, 0.12, -0.04])
    mid = chest + np.array([0, -0.05, -0.06])
    stations = []
    for i, (p, r) in enumerate((
        (top, 0.16),
        (top * 0.5 + mid * 0.5, 0.20),
        (mid, 0.22),
    )):
        stations.append(dict(pos=p, rx=r, rz=r * 0.55, bone="chest"))
    add_loft(cloth, stations, RECT["cloak"], sides=16, closed=False, ang0=0.9, ang1=math.tau - 0.9)
    # lower tails on the hips, two side panels so the split does not bridge the groin
    for sign, ang_a, ang_b in ((1, 1.2, 2.6), (-1, math.tau - 2.6, math.tau - 1.2)):
        stations = []
        for i in range(6):
            t = i / 5
            p = hips + np.array([sign * 0.02, -0.02 - length * t, -0.06 - 0.03 * t])
            stations.append(dict(pos=p, rx=0.16 + 0.06 * t, rz=0.10, bone="hips"))
        add_loft(cloth, stations, RECT["cloak"], sides=8, closed=False, ang0=ang_a, ang1=ang_b)


def add_tunic(cloth, chest, hips):
    chest = np.asarray(chest, np.float64)
    stations = []
    for i, y in enumerate((0.08, -0.02, -0.12)):
        stations.append(dict(pos=chest + np.array([0, y, 0.01]), rx=0.15 - i * 0.005, rz=0.11, bone="chest"))
    # open down the front
    add_loft(cloth, stations, RECT["tunic"], sides=18, closed=False, ang0=0.40, ang1=math.tau - 0.40)
    add_skirt(cloth, hips, RECT["tunic"], 0.46, 0.16, 0.26, bone="hips", sides=18, front_open=0.28)


def add_sailor_shirt(cloth, chest):
    chest = np.asarray(chest, np.float64)
    stations = []
    for i, y in enumerate((0.10, 0.0, -0.10, -0.18)):
        stations.append(dict(pos=chest + np.array([0, y, 0.0]), rx=0.16, rz=0.11, bone="chest"))
    add_loft(cloth, stations, RECT["sailor"], sides=16, closed=False, ang0=0.7, ang1=math.tau - 0.7)


def add_dress(cloth, chest, hips):
    # three layers, each its own vertical band of the dress island so blue / brown / green share one map
    chest = np.asarray(chest, np.float64)
    hips = np.asarray(hips, np.float64)
    bands = [
        (0.70, 0.98, 0.34, "over"),
        (0.40, 0.72, 0.55, "mid"),
        (0.02, 0.42, 0.78, "under"),
    ]
    base = RECT["dress"]
    for v0, v1, length, _name in bands:
        rect = (base[0], base[1] + v0 * (base[3] - base[1]), base[2], base[1] + v1 * (base[3] - base[1]))
        # bodice, almost closed, with a narrow tear down the sternum
        stations = [
            dict(pos=chest + np.array([0, 0.06, 0.02]), rx=0.145, rz=0.105, bone="chest"),
            dict(pos=chest + np.array([0, -0.06, 0.015]), rx=0.132, rz=0.098, bone="chest"),
            dict(pos=hips + np.array([0, 0.08, 0.01]), rx=0.138, rz=0.10, bone="chest"),
        ]
        add_loft(cloth, stations, (rect[0], (rect[1] + rect[3]) * 0.5, rect[2], rect[3]), sides=18, closed=False, ang0=0.18, ang1=math.tau - 0.18)
        # Skirt starts up over the bodice hem so the waist is not a bare tube.
        add_skirt(cloth, hips + np.array([0.0, 0.10, 0.0]), rect, length + 0.10, 0.145, 0.22 + length * 0.10, sides=18)


def add_belt(opaque, hips, with_pouch=True):
    hips = np.asarray(hips, np.float64)
    c = hips + np.array([0, 0.02, 0.0])
    add_torus(opaque, c, np.array([0, 1, 0]), 0.145, 0.014, RECT["leather"], "hips", n=16, m=5)
    add_box(opaque, c + np.array([0, 0, 0.145]), np.array([1, 0, 0]), np.array([0, 1, 0]), np.array([0, 0, 1]),
            (0.028, 0.02, 0.012), RECT["metal"], "hips")
    if with_pouch:
        add_box(opaque, c + np.array([-0.10, -0.06, 0.06]), np.array([1, 0, 0]), np.array([0, 1, 0]), np.array([0, 0, 1]),
                (0.035, 0.05, 0.02), RECT["leather"], "hips")


def add_wraps(opaque, a, b, bone, n=3, radius=0.06):
    a = np.asarray(a, np.float64)
    b = np.asarray(b, np.float64)
    for i in range(n):
        t = 0.2 + 0.65 * i / max(n - 1, 1)
        c = a * (1 - t) + b * t
        add_torus(opaque, c, b - a, radius, 0.008, RECT["leather"], bone, n=8, m=3)


def add_pauldron(opaque, shoulder):
    shoulder = np.asarray(shoulder, np.float64)
    center = shoulder + np.array([0.02, 0.03, 0.0])
    ids = []
    for iy in range(7):
        row = []
        for ix in range(10):
            u = ix / 9
            v = iy / 6
            ang = -0.8 + u * 1.6
            th = 0.35 + v * 1.0
            p = center + np.array([
                math.sin(th) * math.sin(ang),
                math.cos(th),
                math.sin(th) * math.cos(ang),
            ]) * 0.095
            uu = RECT["metal"][0] + u * (RECT["metal"][2] - RECT["metal"][0])
            vv = RECT["metal"][1] + v * (RECT["metal"][3] - RECT["metal"][1])
            row.append(opaque.add(p, (uu, vv), "shoulder_L"))
        ids.append(row)
    for iy in range(6):
        for ix in range(9):
            a, b = ids[iy][ix], ids[iy][ix + 1]
            c, d = ids[iy + 1][ix + 1], ids[iy + 1][ix]
            opaque.tri(a, b, c, center)
            opaque.tri(a, c, d, center)


def add_kneepad(opaque, knee):
    knee = np.asarray(knee, np.float64)
    center = knee + np.array([0.0, 0.0, 0.04])
    add_sphere(opaque, center, 0.055, RECT["metal"], "shin_R", 8, 10, lambda x, y, z: 0.55 + 0.5 * max(z, 0))


def build_variant(J, spec):
    opaque, cloth = Prim(), Prim()
    build_body(opaque, J, spec["sex"])
    if spec.get("ribs"):
        add_ribs(opaque, J["chest"])
    if spec.get("dress"):
        add_dress(cloth, J["chest"], J["hips"])
    if spec.get("tunic"):
        add_tunic(cloth, J["chest"], J["hips"])
    if spec.get("sailor"):
        add_sailor_shirt(cloth, J["chest"])
    if spec.get("cloak"):
        add_cloak(cloth, J["chest"], J["hips"], 0.78 if spec["sex"] == "m" else 0.62)
    if spec.get("hood"):
        head_c = J["head"] + np.array([0.0, 0.09, 0.02])
        add_hood(cloth, head_c)
    if spec.get("hair"):
        head_c = J["head"] + np.array([0.0, 0.09, 0.02])
        add_hair(cloth, head_c, spec["hair"])
    add_belt(opaque, J["hips"], spec.get("pouch", False))
    if spec.get("straps"):
        c = J["chest"]
        add_ribbon(opaque, [c + np.array([-0.08, 0.08, 0.10]), c + np.array([0.10, -0.08, 0.10])], 0.018, RECT["leather"], "chest")
        add_ribbon(opaque, [c + np.array([0.08, 0.08, 0.10]), c + np.array([-0.10, -0.08, 0.10])], 0.016, RECT["leather"], "chest")
    for side, tag in ((1, "L"), (-1, "R")):
        if spec.get("bracers") == "cloth" or (spec.get("bracers") == "metal" and tag == "R"):
            rect = RECT["metal"] if spec.get("bracers") == "metal" and tag == "R" else RECT["leather"]
            fa, ha = J[f"foreArm_{tag}"], J[f"hand_{tag}"]
            add_limb(opaque, fa * 0.35 + ha * 0.65, ha * 0.92 + fa * 0.08, 0.046, 0.040, rect, f"foreArm_{tag}", sides=10, rings=3, bulge=0.0)
        if spec.get("boots"):
            build_foot(opaque, cloth, J[f"foot_{tag}"], side, True)
            add_wraps(opaque, J[f"shin_{tag}"], J[f"foot_{tag}"], f"shin_{tag}", n=4, radius=0.055 if spec["sex"] == "m" else 0.050)
        else:
            build_foot(opaque, cloth, J[f"foot_{tag}"], side, False)
            add_wraps(opaque, J[f"shin_{tag}"], J[f"foot_{tag}"], f"shin_{tag}", n=3, radius=0.052)
    if spec.get("pauldron"):
        add_pauldron(opaque, J["shoulder_L"])
    if spec.get("kneepad"):
        add_kneepad(opaque, J["shin_R"])
    if spec.get("chain"):
        c = J["chest"] + np.array([0.0, -0.08, 0.06])
        add_box(opaque, c, np.array([1, 0, 0]), np.array([0, 1, 0]), np.array([0, 0, 1]),
                (0.08, 0.07, 0.01), RECT["metal"], "chest")
    opaque.finish()
    cloth.finish()
    return opaque, cloth


def fbm(shape, seed):
    rng = np.random.default_rng(seed)
    acc = np.zeros(shape, np.float32)
    amp = 1.0
    total = 0.0
    h, w = shape
    for octv in (4, 8, 16, 32, 64, 128, 256):
        n = rng.random((octv, octv), np.float32)
        img = Image.fromarray((n * 255).astype(np.uint8), "L").resize((w, h), Image.BILINEAR)
        acc += amp * (np.asarray(img, np.float32) / 255.0)
        total += amp
        amp *= 0.55
    return acc / total


def rect_slices(rect, S):
    u0, v0, u1, v1 = rect
    x0, x1 = int(u0 * S), int(u1 * S)
    # glTF v=0 is the top of the image.
    y0, y1 = int(v0 * S), int(v1 * S)
    return x0, x1, y0, y1


def stamp(dst, u, v, ru, rv, value, add=False):
    H = dst.shape[0]
    x = int(u * H)
    y = int(v * H)
    rx = max(int(ru * H), 1)
    ry = max(int(rv * H), 1)
    x0, x1 = max(0, x - rx), min(H, x + rx + 1)
    y0, y1 = max(0, y - ry), min(H, y + ry + 1)
    if x0 >= x1 or y0 >= y1:
        return
    yy, xx = np.mgrid[y0:y1, x0:x1]
    m = ((xx - x) / rx) ** 2 + ((yy - y) / ry) ** 2 <= 1.0
    if dst.ndim == 3:
        if add:
            dst[y0:y1, x0:x1][m] = np.clip(dst[y0:y1, x0:x1][m] * 0.45 + np.array(value) * 0.55, 0, 255)
        else:
            dst[y0:y1, x0:x1][m] = value
    else:
        if add:
            dst[y0:y1, x0:x1][m] += value
        else:
            dst[y0:y1, x0:x1][m] = value


def paint():
    noise = fbm((S, S), 11)
    noise2 = fbm((S, S), 29)
    rgb = np.zeros((S, S, 3), np.float32)
    height = np.zeros((S, S), np.float32)
    rough = np.full((S, S), 0.82, np.float32)
    metal = np.zeros((S, S), np.float32)
    ao = np.full((S, S), 1.0, np.float32)
    alpha = np.full((S, S), 255, np.uint8)

    def fill(rect, base, rough_v, metal_v, ao_v, height_amp=0.0):
        x0, x1, y0, y1 = rect_slices(rect, S)
        n = noise[y0:y1, x0:x1]
        col = np.array(base, np.float32) * (0.78 + 0.44 * n)[..., None]
        # rot mottling
        m = noise2[y0:y1, x0:x1]
        col[m < 0.28] *= np.array([0.72, 0.85, 0.68])
        col[m > 0.82] *= np.array([0.85, 0.55, 0.5])
        rgb[y0:y1, x0:x1] = np.clip(col, 0, 255)
        rough[y0:y1, x0:x1] = rough_v + (n - 0.5) * 0.08
        metal[y0:y1, x0:x1] = metal_v
        ao[y0:y1, x0:x1] = ao_v
        height[y0:y1, x0:x1] = (n - 0.5) * height_amp

    fill(RECT["body"], (126, 118, 104), 0.78, 0.0, 0.85, 0.12)
    fill(RECT["face"], (132, 122, 108), 0.70, 0.0, 0.9, 0.18)
    fill(RECT["scalp"], (92, 84, 74), 0.8, 0.0, 0.8, 0.2)
    fill(RECT["eye"], (214, 208, 196), 0.22, 0.0, 1.0, 0.05)
    fill(RECT["tooth"], (186, 170, 138), 0.45, 0.0, 0.95, 0.15)
    fill(RECT["blood"], (120, 28, 24), 0.32, 0.0, 0.7, 0.1)
    fill(RECT["leather"], (78, 60, 44), 0.72, 0.0, 0.75, 0.25)
    fill(RECT["metal"], (128, 124, 116), 0.42, 0.82, 0.8, 0.45)
    fill(RECT["hair"], (48, 40, 34), 0.9, 0.0, 0.7, 0.3)
    # cloth bases, then per-band colors
    fill(RECT["tunic"], (96, 84, 70), 0.88, 0.0, 0.78, 0.3)
    fill(RECT["cloak"], (70, 66, 60), 0.9, 0.0, 0.72, 0.35)
    fill(RECT["sailor"], (74, 86, 92), 0.86, 0.0, 0.78, 0.28)
    # dress bands: blue over, brown mid, green under
    x0, x1, y0, y1 = rect_slices(RECT["dress"], S)
    rows, cols = y1 - y0, x1 - x0
    # image y grows downward, so the top of the rect (high v, overdress) is small y
    t = np.linspace(0.0, 1.0, rows)
    palette = np.array([[78, 90, 96], [110, 90, 70], [78, 86, 68]], np.float32)
    choice = np.where(t < 0.34, 0, np.where(t < 0.66, 1, 2))
    col = np.broadcast_to(palette[choice][:, None, :], (rows, cols, 3)).copy()
    n = noise[y0:y1, x0:x1][..., None]
    col = col * (0.75 + 0.5 * n)
    rgb[y0:y1, x0:x1] = np.clip(col, 0, 255)
    rough[y0:y1, x0:x1] = 0.88
    height[y0:y1, x0:x1] = (noise[y0:y1, x0:x1] - 0.5) * 0.3

    # face features in the face rect. UV maps x,y of the unit sphere through (x*0.5+0.5)
    fr = RECT["face"]
    def fuv(lx, ly):
        return (fr[0] + (lx * 0.5 + 0.5) * (fr[2] - fr[0]),
                fr[1] + (ly * 0.5 + 0.5) * (fr[3] - fr[1]))
    # sockets
    for sx in (-0.30, 0.32):
        u, v = fuv(sx, 0.14)
        stamp(rgb, u, v, 0.028, 0.018, (28, 22, 20))
        stamp(ao, u, v, 0.03, 0.02, 0.35)
        stamp(height, u, v, 0.028, 0.018, -0.8)
    # nose highlight
    u, v = fuv(0.0, 0.02)
    stamp(rgb, u, v, 0.012, 0.028, (150, 138, 122), add=True)
    stamp(height, u, v, 0.01, 0.03, 0.7, add=True)
    # nasal hole
    u, v = fuv(0.0, -0.08)
    stamp(rgb, u, v, 0.012, 0.012, (20, 12, 12))
    stamp(height, u, v, 0.012, 0.01, -0.5, add=True)
    # mouth blood
    u, v = fuv(0.0, -0.38)
    stamp(rgb, u, v, 0.045, 0.028, (90, 18, 16))
    stamp(rough, u, v, 0.05, 0.03, 0.3)
    stamp(height, u, v, 0.04, 0.02, -0.4, add=True)
    # cheek rot
    u, v = fuv(0.42, -0.05)
    stamp(rgb, u, v, 0.04, 0.03, (70, 48, 42), add=True)
    # brow grime
    u, v = fuv(0.0, 0.32)
    stamp(rgb, u, v, 0.08, 0.02, (90, 82, 72), add=True)
    # blood drip
    u, v = fuv(0.08, -0.15)
    stamp(rgb, u, v, 0.012, 0.05, (110, 20, 18), add=True)

    # chain rings in the metal island
    mx0, mx1, my0, my1 = rect_slices(RECT["metal"], S)
    yy, xx = np.mgrid[my0:my1, mx0:mx1]
    rings = (np.sin((xx - mx0) * 0.45) ** 2) * (np.sin((yy - my0) * 0.45) ** 2)
    height[my0:my1, mx0:mx1] += rings * 0.35

    # cloth alpha: ragged hem + holes. Low glTF v (bottom of island) is the hem.
    def ragged(rect, hem=0.28, holes=0.18):
        x0, x1, y0, y1 = rect_slices(rect, S)
        rows, cols = y1 - y0, x1 - x0
        if rows < 2 or cols < 2:
            return
        # local 1 at the top of the island (high glTF v), 0 at the hem
        local = np.linspace(1.0, 0.0, rows)[:, None]
        local = np.broadcast_to(local, (rows, cols)).copy()
        rng = np.random.default_rng(abs(x0 * 17 + y0))
        # high-frequency tears: each column ends at a different height
        tear = hem * (0.25 + 1.15 * rng.random(cols))
        col_noise = rng.random((8, cols))
        hf = np.asarray(Image.fromarray((col_noise * 255).astype(np.uint8), "L").resize((cols, rows), Image.NEAREST), np.float32) / 255.0
        a = np.full((rows, cols), 255.0, np.float32)
        a[local < tear[None, :]] = 0.0
        # a few holes above the hem, not a smooth band
        a[(hf < holes) & (local < 0.72) & (local > 0.18)] = 0.0
        alpha[y0:y1, x0:x1] = a.astype(np.uint8)

    for key, hem, holes in (
        ("dress", 0.22, 0.16),
        ("tunic", 0.30, 0.20),
        ("cloak", 0.34, 0.14),
        ("sailor", 0.26, 0.18),
        ("hair", 0.55, 0.42),
    ):
        ragged(RECT[key], hem, holes)
    # hair is mostly streaks
    x0, x1, y0, y1 = rect_slices(RECT["hair"], S)
    xs = np.linspace(0, 1, x1 - x0)
    streak = (np.sin(xs * 48) > -0.15).astype(np.float32)
    alpha[y0:y1, x0:x1] = (alpha[y0:y1, x0:x1] * streak[None, :]).astype(np.uint8)

    # normal from height
    gy, gx = np.gradient(height.astype(np.float32))
    strength = 1.15
    nx, ny, nz = -gx * strength, -gy * strength, np.ones_like(height)
    ln = np.sqrt(nx * nx + ny * ny + nz * nz) + 1e-8
    normal = np.stack((nx / ln * 0.5 + 0.5, ny / ln * 0.5 + 0.5, nz / ln * 0.5 + 0.5), axis=-1)
    normal = np.clip(normal * 255, 0, 255).astype(np.uint8)

    rgb_u = np.clip(rgb, 0, 255).astype(np.uint8)
    albedo = np.dstack((rgb_u, alpha))
    # ORM: R ao, G rough, B metal
    orm = np.stack((
        np.clip(ao, 0, 1) * 255,
        np.clip(rough, 0, 1) * 255,
        np.clip(metal, 0, 1) * 255,
    ), axis=-1).astype(np.uint8)

    Image.fromarray(albedo, "RGBA").save(TEX / "zombie_albedo.png", optimize=True)
    Image.fromarray(normal, "RGB").save(TEX / "zombie_normal.png", optimize=True)
    Image.fromarray(orm, "RGB").save(TEX / "zombie_orm.png", optimize=True)
    # far texture: flat zones
    far = np.zeros((256, 256, 3), np.uint8)
    far[:] = (120, 112, 98)
    far[:, 128:] = (72, 66, 58)
    far[128:, :128] = (80, 62, 46)
    Image.fromarray(far, "RGB").save(TEX / "zombie_far_albedo.png", optimize=True)
    return albedo


class Blob:
    def __init__(self):
        self.data = bytearray()
        self.views = []
        self.accessors = []

    def align(self, n=4):
        while len(self.data) % n:
            self.data.append(0)

    def view(self, raw, target=None):
        self.align(4)
        off = len(self.data)
        self.data += raw
        bv = {"buffer": 0, "byteOffset": off, "byteLength": len(raw)}
        if target:
            bv["target"] = target
        self.views.append(bv)
        return len(self.views) - 1

    def acc(self, arr, typ, comp, target=None):
        arr = np.ascontiguousarray(arr)
        vi = self.view(arr.tobytes(), target)
        a = {"bufferView": vi, "byteOffset": 0, "componentType": comp, "count": int(arr.shape[0]), "type": typ}
        if arr.ndim == 1:
            a["min"] = [float(arr.min())]
            a["max"] = [float(arr.max())]
        elif typ != "SCALAR":
            a["min"] = [float(x) for x in arr.reshape(-1, arr.shape[-1]).min(0)]
            a["max"] = [float(x) for x in arr.reshape(-1, arr.shape[-1]).max(0)]
        self.accessors.append(a)
        return len(self.accessors) - 1


def prim_acc(blob, prim):
    pos = blob.acc(prim.P, "VEC3", 5126, 34962)
    nrm_ = blob.acc(prim.N, "VEC3", 5126, 34962)
    uv = blob.acc(prim.UV, "VEC2", 5126, 34962)
    joints = blob.acc(prim.J, "VEC4", 5123, 34962)
    weights = blob.acc(prim.W, "VEC4", 5126, 34962)
    idx = prim.I.reshape(-1)
    if len(prim.P) > 65535:
        ind = blob.acc(idx.astype(np.uint32), "SCALAR", 5125, 34963)
    else:
        ind = blob.acc(idx.astype(np.uint16), "SCALAR", 5123, 34963)
    return pos, nrm_, uv, joints, weights, ind


def write_glb(path, rig: Rig, opaque: Prim, cloth: Prim, skinned=True):
    blob = Blob()
    # images external
    mats = [
        {
            "name": "ZombieBody",
            "pbrMetallicRoughness": {
                "baseColorTexture": {"index": 0},
                "metallicRoughnessTexture": {"index": 2},
                "metallicFactor": 1.0,
                "roughnessFactor": 1.0,
            },
            "normalTexture": {"index": 1},
            "occlusionTexture": {"index": 2},
            "doubleSided": False,
            "alphaMode": "OPAQUE",
        },
        {
            "name": "ZombieCloth",
            "pbrMetallicRoughness": {
                "baseColorTexture": {"index": 0},
                "metallicRoughnessTexture": {"index": 2},
                "metallicFactor": 1.0,
                "roughnessFactor": 1.0,
            },
            "normalTexture": {"index": 1},
            "occlusionTexture": {"index": 2},
            "doubleSided": True,
            "alphaMode": "MASK",
            "alphaCutoff": 0.5,
        },
    ]
    primitives = []
    if opaque.tris:
        pos, nn, uv, j, w, ind = prim_acc(blob, opaque)
        attr = {"POSITION": pos, "NORMAL": nn, "TEXCOORD_0": uv}
        if skinned:
            attr["JOINTS_0"] = j
            attr["WEIGHTS_0"] = w
        primitives.append({"attributes": attr, "indices": ind, "material": 0})
    if cloth.tris:
        pos, nn, uv, j, w, ind = prim_acc(blob, cloth)
        attr = {"POSITION": pos, "NORMAL": nn, "TEXCOORD_0": uv}
        if skinned:
            attr["JOINTS_0"] = j
            attr["WEIGHTS_0"] = w
        primitives.append({"attributes": attr, "indices": ind, "material": 1})

    nodes = []
    def add_node(name, **extra):
        n = {"name": name}
        n.update(extra)
        nodes.append(n)
        return len(nodes) - 1

    mesh_i = add_node("Zombie", mesh=0)
    bone_ids = {}
    # create bones in CORE order so joint index matches BONE_INDEX, then link parents
    for nm in CORE:
        t, r, s = rig.rest[nm]
        extra = {"translation": [float(x) for x in t], "rotation": [float(x) for x in r]}
        if not np.allclose(s, 1.0):
            extra["scale"] = [float(x) for x in s]
        bone_ids[nm] = add_node(nm, **extra)
    rig_i = add_node("ZombieRig")
    # children
    for n in nodes:
        n.setdefault("children", [])
    nodes[rig_i]["children"] = [mesh_i, bone_ids["root"]]
    for child, par in PARENT.items():
        nodes[bone_ids[par]]["children"].append(bone_ids[child])
    for n in nodes:
        if not n["children"]:
            del n["children"]

    if skinned:
        ibm = []
        bind = rig.bind
        for nm in CORE:
            ibm.append(np.linalg.inv(bind[nm]).astype(np.float32).reshape(-1, order="F"))
        ibm_arr = np.stack(ibm, 0)
        ibm_acc = blob.acc(ibm_arr, "MAT4", 5126)
        skin = {"joints": [bone_ids[nm] for nm in CORE], "inverseBindMatrices": ibm_acc, "name": "Humanoid"}
        nodes[mesh_i]["skin"] = 0
        skins = [skin]
    else:
        skins = []

    animations = []
    # build animations from rig clips, plus attack alias
    wanted = list(CLIPS) + ["attack"]
    for name in wanted:
        src = "attack1" if name == "attack" else name
        clip = rig.clips[src]
        samplers = []
        channels = []
        for nm, paths in clip["channels"].items():
            node_i = bone_ids[nm]
            for path_name, (times, vals, interp) in paths.items():
                ta = blob.acc(times.astype(np.float32), "SCALAR", 5126)
                va = blob.acc(vals.astype(np.float32), "VEC4" if vals.shape[-1] == 4 else "VEC3", 5126)
                samplers.append({"input": ta, "output": va, "interpolation": interp})
                channels.append({"sampler": len(samplers) - 1, "target": {"node": node_i, "path": path_name}})
        animations.append({"name": name, "samplers": samplers, "channels": channels})

    images = [
        {"uri": "textures/zombie_albedo.png", "mimeType": "image/png"},
        {"uri": "textures/zombie_normal.png", "mimeType": "image/png"},
        {"uri": "textures/zombie_orm.png", "mimeType": "image/png"},
    ]
    sampler = {"magFilter": 9729, "minFilter": 9986, "wrapS": 33071, "wrapT": 33071}
    textures = [{"sampler": 0, "source": i} for i in range(3)]
    gltf = {
        "asset": {"version": "2.0", "generator": "varnethryl-zombie-original"},
        "scene": 0,
        "scenes": [{"nodes": [rig_i], "name": "Zombie"}],
        "nodes": nodes,
        "meshes": [{"name": path.stem, "primitives": primitives}],
        "skins": skins,
        "animations": animations if skinned else [],
        "materials": mats,
        "textures": textures,
        "images": images,
        "samplers": [sampler],
        "accessors": blob.accessors,
        "bufferViews": blob.views,
        "buffers": [{"byteLength": len(blob.data)}],
    }
    if not skins:
        del gltf["skins"]
    if not animations or not skinned:
        gltf.pop("animations", None)
    js = json.dumps(gltf, separators=(",", ":")).encode("utf-8")
    while len(js) % 4:
        js += b" "
    bin_ = bytes(blob.data)
    while len(bin_) % 4:
        bin_ += b"\x00"
    total = 12 + 8 + len(js) + 8 + len(bin_)
    out = bytearray()
    out += struct.pack("<4sII", b"glTF", 2, total)
    out += struct.pack("<I4s", len(js), b"JSON")
    out += js
    out += struct.pack("<I4s", len(bin_), b"BIN\x00")
    out += bin_
    Path(path).write_bytes(out)


def write_static_glb(path, prim, material_uri, double=False, alpha=False):
    blob = Blob()
    prim.finish() if prim.N is None or not hasattr(prim, "P") else None
    if not hasattr(prim, "P"):
        prim.finish()
    pos = blob.acc(prim.P, "VEC3", 5126, 34962)
    nn = blob.acc(prim.N, "VEC3", 5126, 34962)
    uv = blob.acc(prim.UV, "VEC2", 5126, 34962)
    idx = prim.I.reshape(-1)
    ind = blob.acc(idx.astype(np.uint16 if len(prim.P) <= 65535 else np.uint32), "SCALAR",
                   5123 if len(prim.P) <= 65535 else 5125, 34963)
    mat = {
        "name": "Far",
        "pbrMetallicRoughness": {"baseColorTexture": {"index": 0}, "metallicFactor": 0.0, "roughnessFactor": 0.9},
        "doubleSided": double,
        "alphaMode": "MASK" if alpha else "OPAQUE",
    }
    if alpha:
        mat["alphaCutoff"] = 0.4
    node = {"name": "FarZombie", "mesh": 0}
    gltf = {
        "asset": {"version": "2.0", "generator": "varnethryl-zombie-original"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [node],
        "meshes": [{"primitives": [{"attributes": {"POSITION": pos, "NORMAL": nn, "TEXCOORD_0": uv}, "indices": ind, "material": 0}]}],
        "materials": [mat],
        "textures": [{"sampler": 0, "source": 0}],
        "images": [{"uri": material_uri, "mimeType": "image/png"}],
        "samplers": [{"magFilter": 9729, "minFilter": 9986, "wrapS": 33071, "wrapT": 33071}],
        "accessors": blob.accessors,
        "bufferViews": blob.views,
        "buffers": [{"byteLength": len(blob.data)}],
    }
    js = json.dumps(gltf, separators=(",", ":")).encode("utf-8")
    while len(js) % 4:
        js += b" "
    bin_ = bytes(blob.data)
    while len(bin_) % 4:
        bin_ += b"\x00"
    total = 12 + 8 + len(js) + 8 + len(bin_)
    out = bytearray()
    out += struct.pack("<4sII", b"glTF", 2, total)
    out += struct.pack("<I4s", len(js), b"JSON") + js
    out += struct.pack("<I4s", len(bin_), b"BIN\x00") + bin_
    Path(path).write_bytes(out)


def skin_arrays(prim, rig, clip, t):
    if prim.tris == 0:
        return np.zeros((0, 3), np.float32), np.zeros((0, 3), np.float32)
    bind = rig.bind
    posed = rig.pose(clip, t)
    ibm = [np.linalg.inv(bind[nm]) for nm in CORE]
    M = [(posed[nm] @ ibm[i])[:3, :3] for i, nm in enumerate(CORE)]
    T = [(posed[nm] @ ibm[i])[:3, 3] for i, nm in enumerate(CORE)]
    P = prim.P.astype(np.float64)
    N = prim.N.astype(np.float64)
    out = np.zeros_like(P)
    nout = np.zeros_like(N)
    J = prim.J
    W = prim.W.astype(np.float64)
    for b in range(len(CORE)):
        for k in range(4):
            m = J[:, k] == b
            if not np.any(m):
                continue
            w = W[m, k][:, None]
            out[m] += (P[m] @ M[b].T + T[b]) * w
            nout[m] += (N[m] @ M[b].T) * w
    ln = np.linalg.norm(nout, axis=1, keepdims=True)
    ln[ln < 1e-8] = 1
    return out.astype(np.float32), (nout / ln).astype(np.float32)


def build_far(Jpose):
    prim = Prim()
    # chunky posed shambler, horizontal rings, one material, simple UVs
    skin_uv = (0.02, 0.52, 0.48, 0.98)
    cloth_uv = (0.52, 0.52, 0.98, 0.98)
    leather_uv = (0.02, 0.02, 0.48, 0.48)
    def tube(a, b, r0, r1, uv, n=5):
        add_limb(prim, a, b, r0, r1, uv, "hips", sides=n, rings=1, bulge=0.0)
    H = Jpose
    head = H["head"] + np.array([0, 0.09, 0.03])
    add_sphere(prim, head, 0.11, skin_uv, "hips", 6, 8, lambda x, y, z: 0.9 + 0.2 * max(z, 0))
    tube(H["hips"], H["chest"], 0.14, 0.16, cloth_uv, 6)
    tube(H["chest"], H["head"], 0.07, 0.05, skin_uv, 5)
    for tag in ("L", "R"):
        tube(H[f"shoulder_{tag}"], H[f"foreArm_{tag}"], 0.05, 0.04, skin_uv, 5)
        tube(H[f"foreArm_{tag}"], H[f"hand_{tag}"], 0.04, 0.03, skin_uv, 4)
        tube(H[f"thigh_{tag}"], H[f"shin_{tag}"], 0.07, 0.05, skin_uv, 5)
        tube(H[f"shin_{tag}"], H[f"foot_{tag}"], 0.05, 0.035, leather_uv, 4)
        foot = H[f"foot_{tag}"]
        tube(foot, foot + np.array([0, -0.04, 0.1]), 0.04, 0.03, leather_uv, 4)
    # cloak slab
    c = H["chest"] + np.array([0, -0.05, -0.08])
    h = H["hips"] + np.array([0, -0.35, -0.1])
    add_ribbon(prim, [c + np.array([-0.12, 0.1, 0]), c + np.array([0.12, 0.1, 0]), h + np.array([0.16, 0, 0]), h + np.array([-0.16, 0, 0])],
               0.02, cloth_uv, "hips")
    prim.finish()
    P = prim.P.copy()
    if len(P):
        P[:, 1] -= P[:, 1].min()
        prim.P = P
    return prim


def raster(path, P, N, UV, I, albedo, eye, target, fov=32, w=480, h=640):
    if len(P) == 0:
        return
    fwd = nrm(target - eye)
    right = nrm(np.cross(fwd, np.array([0.0, 1.0, 0.0])))
    up = np.cross(right, fwd)
    # camera rays
    aspect = w / h
    tany = math.tan(math.radians(fov) * 0.5)
    tanx = tany * aspect
    zbuf = np.full((h, w), 1e9, np.float32)
    img = np.zeros((h, w, 3), np.uint8)
    img[:] = (28, 28, 32)
    light = nrm(np.array([0.35, 0.75, 0.45]))
    alb = albedo
    AH, AW = alb.shape[:2]
    tris = I.reshape(-1, 3)
    for tri in tris:
        p = P[tri]
        cam = np.stack((
            (p - eye) @ right,
            (p - eye) @ up,
            (p - eye) @ fwd,
        ), axis=1)
        if np.any(cam[:, 2] < 0.05):
            continue
        sx = (cam[:, 0] / cam[:, 2] / tanx * 0.5 + 0.5) * w
        sy = (0.5 - cam[:, 1] / cam[:, 2] / tany * 0.5) * h
        if sx.max() < 0 or sx.min() >= w or sy.max() < 0 or sy.min() >= h:
            continue
        area = (sx[1] - sx[0]) * (sy[2] - sy[0]) - (sx[2] - sx[0]) * (sy[1] - sy[0])
        if area <= 0:
            continue
        x0, x1 = max(int(sx.min()), 0), min(int(sx.max()) + 1, w)
        y0, y1 = max(int(sy.min()), 0), min(int(sy.max()) + 1, h)
        if x0 >= x1 or y0 >= y1:
            continue
        xs = np.arange(x0, x1) + 0.5
        ys = np.arange(y0, y1) + 0.5
        X, Y = np.meshgrid(xs, ys)
        den = area
        w0 = ((sx[1] - X) * (sy[2] - Y) - (sx[2] - X) * (sy[1] - Y)) / den
        w1 = ((sx[2] - X) * (sy[0] - Y) - (sx[0] - X) * (sy[2] - Y)) / den
        w2 = 1 - w0 - w1
        m = (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
        if not np.any(m):
            continue
        z = w0 * cam[0, 2] + w1 * cam[1, 2] + w2 * cam[2, 2]
        closer = m & (z < zbuf[y0:y1, x0:x1])
        if not np.any(closer):
            continue
        zbuf[y0:y1, x0:x1][closer] = z[closer]
        uv = (UV[tri[0]] * w0[..., None] + UV[tri[1]] * w1[..., None] + UV[tri[2]] * w2[..., None])
        nn = N[tri].mean(0)
        nd = float(np.clip(np.dot(nn, light), 0, 1))
        shade = 0.38 + 0.62 * nd
        ui = np.clip((uv[..., 0] * (AW - 1)).astype(np.int32), 0, AW - 1)
        vi = np.clip((uv[..., 1] * (AH - 1)).astype(np.int32), 0, AH - 1)
        col = alb[vi, ui, :3].astype(np.float32) * shade
        if alb.shape[-1] == 4:
            a = alb[vi, ui, 3]
            closer = closer & (a > 128)
        img[y0:y1, x0:x1][closer] = np.clip(col[closer], 0, 255).astype(np.uint8)
    Image.fromarray(img, "RGB").save(path)


def raster_ortho(P, N, UV, I, albedo, axis, res=256):
    """axis 'front' looks along -Z, 'side' along -X. Returns RGBA."""
    img = np.zeros((res, res, 4), np.uint8)
    if len(P) == 0:
        return img
    light = nrm(np.array([0.3, 0.8, 0.4]))
    AH, AW = albedo.shape[:2]
    # map x or z and y into the frame. character ~ x -0.6..0.6, y 0..1.9, z -0.4..0.5
    def project(p):
        if axis == "front":
            u = (p[:, 0] + 0.65) / 1.30
        else:
            u = (p[:, 2] + 0.55) / 1.10
        v = p[:, 1] / 1.95
        return u, v
    tris = I.reshape(-1, 3)
    zbuf = np.full((res, res), 1e9, np.float32)
    for tri in tris:
        p = P[tri]
        u, v = project(p)
        if axis == "front":
            depth = -p[:, 2]
            if np.dot(N[tri].mean(0), np.array([0, 0, 1.0])) < 0:
                continue
        else:
            depth = -p[:, 0]
            if np.dot(N[tri].mean(0), np.array([1.0, 0, 0])) < 0:
                continue
        sx = u * res
        sy = (1 - v) * res
        area = (sx[1] - sx[0]) * (sy[2] - sy[0]) - (sx[2] - sx[0]) * (sy[1] - sy[0])
        if abs(area) < 1e-6:
            continue
        x0, x1 = max(int(sx.min()), 0), min(int(sx.max()) + 1, res)
        y0, y1 = max(int(sy.min()), 0), min(int(sy.max()) + 1, res)
        if x0 >= x1 or y0 >= y1:
            continue
        xs = np.arange(x0, x1) + 0.5
        ys = np.arange(y0, y1) + 0.5
        X, Y = np.meshgrid(xs, ys)
        w0 = ((sx[1] - X) * (sy[2] - Y) - (sx[2] - X) * (sy[1] - Y)) / area
        w1 = ((sx[2] - X) * (sy[0] - Y) - (sx[0] - X) * (sy[2] - Y)) / area
        w2 = 1 - w0 - w1
        m = (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
        if not np.any(m):
            continue
        z = -(w0 * depth[0] + w1 * depth[1] + w2 * depth[2])
        # smaller z (more negative depth stored) — use positive depth, keep nearer (larger if front is +)
        z = w0 * depth[0] + w1 * depth[1] + w2 * depth[2]
        closer = m & (z > zbuf[y0:y1, x0:x1] * -1 + 1e9) if False else m & (z < zbuf[y0:y1, x0:x1])
        # depth is -z for front, nearer is larger -z? I set depth = -p.z so the front (high +z, low -z) has smaller depth.
        # nearer to camera on +Z side is larger z, which is smaller depth (-z). Yes zbuf keeps smaller depth.
        if not np.any(closer):
            continue
        zbuf[y0:y1, x0:x1][closer] = z[closer]
        uv = UV[tri[0]] * w0[..., None] + UV[tri[1]] * w1[..., None] + UV[tri[2]] * w2[..., None]
        nn = N[tri].mean(0)
        shade = 0.4 + 0.6 * float(np.clip(abs(np.dot(nn, light)), 0, 1))
        ui = np.clip((uv[..., 0] * (AW - 1)).astype(np.int32), 0, AW - 1)
        vi = np.clip((uv[..., 1] * (AH - 1)).astype(np.int32), 0, AH - 1)
        col = albedo[vi, ui, :3].astype(np.float32) * shade
        a = albedo[vi, ui, 3] if albedo.shape[-1] == 4 else np.full(col.shape[:2], 255)
        take = closer & (a > 120)
        img[y0:y1, x0:x1, :3][take] = np.clip(col, 0, 255).astype(np.uint8)[take]
        img[y0:y1, x0:x1, 3][take] = 255
    return img


def build_impostor(front, side):
    img = np.zeros((256, 512, 4), np.uint8)
    img[:, 0:256] = front
    img[:, 256:512] = side
    Image.fromarray(img, "RGBA").save(TEX / "zombie_impostor.png")
    prim = Prim()
    # two crossed cards, feet at y=0, height 1.95, matching the ortho frame
    def card(dx, dz, u0, u1):
        y0, y1 = 0.0, 1.95
        p = [
            np.array([-dx, y0, -dz]),
            np.array([dx, y0, dz]),
            np.array([dx, y1, dz]),
            np.array([-dx, y1, -dz]),
        ]
        ids = []
        # glTF v=0 is the top of the image, so the head (y1) gets v=0 and the feet get v=1.
        uvs = [(u0, 1.0), (u1, 1.0), (u1, 0.0), (u0, 0.0)]
        for i in range(4):
            ids.append(prim.add(p[i], uvs[i], "hips"))
        mid = np.array([0, 1, 0.2])
        prim.tri(ids[0], ids[1], ids[2], mid)
        prim.tri(ids[0], ids[2], ids[3], mid)
    # front card faces ±Z, covers x -0.65..0.65 (half-width 0.65) so dx=0.65, dz=0
    card(0.65, 0.0, 0.0, 0.5)
    # side card faces ±X, covers z. The ortho side used z -0.55..0.55 mapped across the right half.
    # Rebuild as a card in the Z direction: width 0.55
    # card() uses dx along x and dz along z of the first/second point. For a side card, points should vary in Z, x=0.
    y0, y1 = 0.0, 1.95
    pts = [
        np.array([0.0, y0, -0.55]),
        np.array([0.0, y0, 0.55]),
        np.array([0.0, y1, 0.55]),
        np.array([0.0, y1, -0.55]),
    ]
    ids = []
    for i, uv in enumerate(((0.5, 1.0), (1.0, 1.0), (1.0, 0.0), (0.5, 0.0))):
        ids.append(prim.add(pts[i], uv, "hips"))
    mid = np.array([0.2, 1, 0])
    prim.tri(ids[0], ids[1], ids[2], mid)
    prim.tri(ids[0], ids[2], ids[3], mid)
    prim.finish()
    return prim


SPECS = [
    dict(name="female_villager", sex="f", dress=True, cloak=True, hood=True, hair="long", boots=True, pouch=True, bracers="cloth", straps=False, ribs=False),
    dict(name="male_villager", sex="m", tunic=True, cloak=True, hood=True, hair="short", boots=True, pouch=True, bracers="cloth", straps=True, ribs=True),
    dict(name="male_sailor", sex="m", sailor=True, cloak=False, hood=False, hair="medium", boots=False, pouch=False, bracers="none", straps=False, ribs=True),
    dict(name="male_knight", sex="m", tunic=True, cloak=True, hood=True, hair="short", boots=True, pouch=True, bracers="metal", straps=True, ribs=True, pauldron=True, kneepad=True, chain=True),
]


def main():
    TEX.mkdir(parents=True, exist_ok=True)
    print("loading rig", SRC)
    rig = Rig(SRC)
    J = rig.origins(rig.bind)
    print("bind head", J["head"].round(3), "handL", J["hand_L"].round(3))
    pose_times = {}
    stretch = {}
    for name in CLIPS:
        stretch[name] = rig.length_error(name)
        L = rig.clips[name]["length"]
        if name == "death":
            best_t, best_y = 0.0, 1e9
            for s in range(16):
                t = L * s / 15
                y = rig.origins(rig.pose(name, t))["head"][1]
                if y < best_y:
                    best_y, best_t = y, t
            pose_times[name] = round(best_t, 3)
        elif name in ("walk", "run"):
            best_t, best = 0.35 * L, -1.0
            for s in range(2, 14):
                t = L * s / 15
                O = rig.origins(rig.pose(name, t))
                sep = abs(O["foot_L"][2] - O["foot_R"][2])
                if sep > best:
                    best, best_t = sep, t
            pose_times[name] = round(best_t, 3)
        elif name.startswith("attack") or name == "hit":
            pose_times[name] = round(L * 0.45, 3)
        else:
            pose_times[name] = round(L * 0.5, 3)
    print("pose times", pose_times)
    print("stretch", json.dumps(stretch, indent=2))
    # hand to head during attacks
    reach = {}
    for name in ("attack1", "attack2", "attack3"):
        L = rig.clips[name]["length"]
        best = 1e9
        for s in range(12):
            O = rig.origins(rig.pose(name, L * s / 11))
            best = min(best, float(np.linalg.norm(O["hand_L"] - O["head"])), float(np.linalg.norm(O["hand_R"] - O["head"])))
        reach[name] = round(best, 3)
    print("closest hand-head m", reach)

    print("painting")
    albedo = paint()
    counts = {}
    built = {}
    for spec in SPECS:
        print("mesh", spec["name"])
        opaque, cloth = build_variant(J, spec)
        counts[spec["name"]] = {"opaque_tris": opaque.tris, "cloth_tris": cloth.tris, "total": opaque.tris + cloth.tris}
        print(" ", counts[spec["name"]])
        write_glb(OUT / f"zombie_{spec['name']}.glb", rig, opaque, cloth, skinned=True)
        built[spec["name"]] = (opaque, cloth)

    # bind skinning error on the female
    op, cl = built["female_villager"]
    Ps, Ns = skin_arrays(op, rig, None, 0.0)
    err = float(np.max(np.abs(Ps - op.P))) if len(Ps) else 0
    print("bind skin error m", round(err, 5))

    idle_t = pose_times["idle"]
    print("far lod from idle", idle_t)
    Jp = rig.origins(rig.pose("idle", idle_t))
    far = build_far(Jp)
    print("far tris", far.tris)
    write_static_glb(OUT / "zombie_far_lod.glb", far, "textures/zombie_far_albedo.png")

    # impostor from the female, skinned to idle, both surfaces
    print("impostor bake")
    chunks = []
    for prim in built["female_villager"]:
        if prim.tris == 0:
            continue
        P, N = skin_arrays(prim, rig, "idle", idle_t)
        chunks.append((P, N, prim.UV, prim.I))
    P = np.concatenate([c[0] for c in chunks])
    N = np.concatenate([c[1] for c in chunks])
    UV = np.concatenate([c[2] for c in chunks])
    # reindex
    I = []
    base = 0
    for c in chunks:
        I.append(c[3] + base)
        base += len(c[0])
    I = np.concatenate(I)
    front = raster_ortho(P, N, UV, I, albedo, "front")
    side = raster_ortho(P, N, UV, I, albedo, "side")
    imp = build_impostor(front, side)
    print("impostor tris", imp.tris)
    write_static_glb(OUT / "zombie_far_impostor.glb", imp, "textures/zombie_impostor.png", double=True, alpha=True)

    stats = {
        "triangles": counts,
        "far_lod_tris": far.tris,
        "impostor_tris": imp.tris,
        "pose_times": pose_times,
        "clip_lengths": {k: rig.clips[k]["length"] for k in CLIPS},
        "bone_stretch": stretch,
        "attack_hand_to_head_m": reach,
        "bind_skin_error_m": err,
        "missing_clips": ["bite", "bite_windup"],
        "skeleton": CORE,
        "texture": "2048 albedo RGBA, 2048 normal, 2048 ORM",
    }
    (OUT / "STATS.json").write_text(json.dumps(stats, indent=2))
    print("wrote", OUT)
    # one debug render of the idle female, full shading is slow so keep it modest
    dbg = Path("/tmp/zombie_debug")
    dbg.mkdir(exist_ok=True)
    target = np.array([0.0, 0.95, 0.08])
    print("debug raster")
    raster(dbg / "female_idle_front.png", P, N, UV, I, albedo, target + np.array([0.15, 0.05, 2.6]), target, fov=30, w=520, h=720)
    raster(dbg / "female_idle_side.png", P, N, UV, I, albedo, target + np.array([2.5, 0.1, 0.35]), target, fov=30, w=520, h=720)
    print("debug done")


if __name__ == "__main__":
    main()
