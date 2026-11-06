"""Separate baked clothing and size the shared knight armor. Review assets only.

Source GLBs are read and never modified. Derived files land in
www/proto3d/models/beth/equipment/knight_rig/fitted_heroes/<id>/.

Unequipped look = body keep vertices + outfit vertices, which is a partition
of the source mesh (same positions, normals, UVs, weights). The underlayer
is extra geometry used only while the outfit is off, so covered regions are
not a hole. Equipped look = keep (head, hair, face, hands) + underlayer +
a sized copy of the shared male or female knight. The shared knight GLB is
not edited. Plate vertices stay rigid on one bone; the size change is baked
into the rest pose and is not animated.
"""
import json
import os
import struct
import subprocess

import numpy as np
from PIL import Image
import io

ROOT = "/workspace/www/proto3d/models/beth/equipment/knight_rig/fitted_heroes"
ARMOR = {
    "male": "/workspace/www/proto3d/models/beth/equipment/knight_rig/knight_male.glb",
    "female": "/workspace/www/proto3d/models/beth/equipment/knight_rig/knight_female.glb",
}
PILOTS = {
    "darius": {
        "path": "/tmp/heroes/darius_voxel_noweapon.glb",
        "source": "origin/weaponless-rigs:voxel/darius_voxel_noweapon.glb",
        "blob": "d3746fc89957989499f5b854b28d189c78a9ed4a",
        "armor": "male",
        "why": "Male the sculpt was built on. Weaponless rig, so the baked sword is not in the source.",
    },
    "talia": {
        "path": "/tmp/heroes/talia_voxel_main.glb",
        "source": "origin/main:voxel/talia_voxel.glb",
        "blob": "a1155620d822c23bfe77afc0561623e60c22bcf8",
        "armor": "female",
        "why": "Female build. Shorter arms than the female armor, robe is the torso.",
    },
    "rook": {
        "path": "/tmp/heroes/rook_voxel.glb",
        "source": "origin/main:voxel/rook_voxel.glb",
        "blob": "ceef6379dd3c8ef5e0b0aea75d8fe40c7acd60d4",
        "armor": "male",
        "why": "Taller male. The wide silhouette is the robe, not a second skeleton.",
    },
}
PLAYABLE = [
    "aldric", "asha", "brynn", "cedric", "darius", "elira", "finn", "garruk",
    "kael", "mirelle", "morwen", "nyx", "orin", "owner", "rook", "rowan",
    "selene", "seraphine", "talia", "thorne", "vesper", "wren",
]
KEEP_PREFIX = (
    "head", "jaw", "eye", "hair", "hand_", "thumb", "index", "middle",
    "ring", "pinky", "finger",
)


def load_glb(path):
    data = open(path, "rb").read()
    off = 12
    js = blob = None
    while off < len(data):
        clen, ctype = struct.unpack_from("<II", data, off)
        off += 8
        chunk = data[off:off + clen]
        off += clen
        if ctype == 0x4E4F534A:
            js = json.loads(chunk)
        elif ctype == 0x004E4942:
            blob = bytearray(chunk)
    return js, blob


def save_glb(js, blob, path):
    blob = bytes(blob)
    if len(blob) % 4:
        blob += b"\x00" * (4 - len(blob) % 4)
    js["buffers"][0]["byteLength"] = len(blob)
    jb = json.dumps(js, separators=(",", ":")).encode()
    jb += b" " * ((4 - len(jb) % 4) % 4)
    out = struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(jb) + 8 + len(blob))
    out += struct.pack("<II", len(jb), 0x4E4F534A) + jb
    out += struct.pack("<II", len(blob), 0x004E4942) + blob
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "wb").write(out)


COMP = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
NCOMP = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}


def read_acc(js, blob, idx):
    a = js["accessors"][idx]
    bv = js["bufferViews"][a["bufferView"]]
    start = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
    count = a["count"]
    nc = NCOMP[a["type"]]
    dt = np.dtype(COMP[a["componentType"]])
    stride = bv.get("byteStride", dt.itemsize * nc)
    if stride == dt.itemsize * nc:
        return np.frombuffer(blob, dtype=dt, count=count * nc, offset=start).reshape(count, nc).copy()
    raw = np.empty((count, nc), dtype=dt)
    for k in range(count):
        raw[k] = np.frombuffer(blob, dtype=dt, count=nc, offset=start + k * stride)
    return raw


def quat_mat(r):
    x, y, z, w = [float(v) for v in r]
    return np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
    ], float)


def node_worlds(js):
    nodes = js["nodes"]
    parent = {}
    for i, n in enumerate(nodes):
        for c in n.get("children", []):
            parent[c] = i
    world = {}

    def W(i):
        if i in world:
            return world[i]
        n = nodes[i]
        t = np.array(n.get("translation", [0, 0, 0]), float)
        r = np.array(n.get("rotation", [0, 0, 0, 1]), float)
        s = np.array(n.get("scale", [1, 1, 1]), float)
        M = np.eye(4)
        M[:3, :3] = quat_mat(r) @ np.diag(s)
        M[:3, 3] = t
        world[i] = (W(parent[i]) @ M) if i in parent else M
        return world[i]

    return W, parent


def joint_maps(js):
    W, parent = node_worlds(js)
    skin = js["skins"][0]
    names = []
    pos = {}
    node_of = {}
    for ji, node_i in enumerate(skin["joints"]):
        name = js["nodes"][node_i].get("name")
        names.append(name)
        pos[name] = W(node_i)[:3, 3].copy()
        node_of[name] = node_i
    return names, pos, node_of, W, parent


def dominant(joints, weights):
    return joints[np.arange(len(joints)), weights.argmax(1)]


def is_keep(name):
    return name.startswith(KEEP_PREFIX)


def srgb_to_linear(c):
    c = np.asarray(c, float) / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def face_color(js, blob, pos, uv, bone_name):
    names, _, _, _, _ = joint_maps(js)
    # caller passes already-sliced head arrays
    if len(pos) < 20:
        return [0.45, 0.30, 0.24, 1.0]
    c = pos.mean(0)
    r = np.linalg.norm(pos - c, axis=1)
    core = r < np.percentile(r, 45)
    # front of the head: larger Z in this asset set is the face side for some,
    # smaller Z for others. Take the band nearest the centroid in X and mid Y.
    band = core & (np.abs(pos[:, 0] - c[0]) < 0.05)
    if band.sum() < 30:
        band = core
    im = js["images"][0]
    bv = js["bufferViews"][im["bufferView"]]
    start = bv.get("byteOffset", 0)
    png = bytes(blob[start:start + bv["byteLength"]])
    img = np.asarray(Image.open(io.BytesIO(png)).convert("RGB"))
    h, w = img.shape[:2]
    u = np.clip(uv[band, 0], 0, 0.999)
    v = np.clip(uv[band, 1], 0, 0.999)
    xs = np.clip((u * w).astype(int), 0, w - 1)
    ys = np.clip(((1 - v) * h).astype(int), 0, h - 1)
    cols = img[ys, xs].astype(np.float64)
    lum = cols.mean(1)
    ok = (lum > 40) & (lum < 200)
    if ok.sum() < 15:
        return [0.52, 0.36, 0.28, 1.0]
    med = np.median(cols[ok], axis=0)
    lin = srgb_to_linear(med)
    if float(lin.mean()) > 0.72:
        return [0.52, 0.36, 0.28, 1.0]
    return [float(lin[0]), float(lin[1]), float(lin[2]), 1.0]


def append_view(js, blob, arr, component, atype, target=None):
    arr = np.ascontiguousarray(arr)
    raw = arr.tobytes()
    pad = (4 - (len(blob) % 4)) % 4
    blob.extend(b"\x00" * pad)
    off = len(blob)
    blob.extend(raw)
    bv = {"buffer": 0, "byteOffset": off, "byteLength": len(raw)}
    if target:
        bv["target"] = target
    js["bufferViews"].append(bv)
    acc = {
        "bufferView": len(js["bufferViews"]) - 1,
        "componentType": component,
        "count": int(arr.shape[0]),
        "type": atype,
    }
    if atype == "VEC3" and component == 5126:
        acc["min"] = arr.min(0).tolist()
        acc["max"] = arr.max(0).tolist()
    js["accessors"].append(acc)
    return len(js["accessors"]) - 1


def pack_mesh(js, blob, pos, nrm, uv, joints, weights, indices):
    ipos = append_view(js, blob, pos.astype(np.float32), 5126, "VEC3", 34962)
    inrm = append_view(js, blob, nrm.astype(np.float32), 5126, "VEC3", 34962)
    iuv = append_view(js, blob, uv.astype(np.float32), 5126, "VEC2", 34962)
    ij = append_view(js, blob, joints.astype(np.uint8), 5121, "VEC4", 34962)
    iw = append_view(js, blob, weights.astype(np.float32), 5126, "VEC4", 34962)
    ii = append_view(js, blob, indices.astype(np.uint32).reshape(-1), 5125, "SCALAR", 34963)
    return {
        "attributes": {
            "POSITION": ipos, "NORMAL": inrm, "TEXCOORD_0": iuv,
            "JOINTS_0": ij, "WEIGHTS_0": iw,
        },
        "indices": ii,
    }


def rot_between(a, b):
    a = a / (np.linalg.norm(a) + 1e-12)
    b = b / (np.linalg.norm(b) + 1e-12)
    c = np.cross(a, b)
    d = float(np.dot(a, b))
    if np.linalg.norm(c) < 1e-8:
        if d > 0:
            return np.eye(3)
        # 180 degree: pick an axis
        axis = np.array([1.0, 0.0, 0.0])
        if abs(a[0]) > 0.9:
            axis = np.array([0.0, 1.0, 0.0])
        axis = axis - a * np.dot(axis, a)
        axis /= np.linalg.norm(axis)
        # Rodrigues 180
        K = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])
        return np.eye(3) + 2 * K @ K
    s = np.linalg.norm(c)
    K = np.array([[0, -c[2], c[1]], [c[2], 0, -c[0]], [-c[1], c[0], 0]])
    return np.eye(3) + K + K @ K * ((1 - d) / (s * s))


def side_of(name):
    if name.endswith("_L"):
        return "_L"
    if name.endswith("_R"):
        return "_R"
    return ""


def chain_of(name):
    base = name
    while base.startswith("mid_"):
        base = base[4:]
    side = side_of(base)
    core = base[:-2] if side else base
    if core in ("head",):
        return "head"
    if core in ("pauldron",):
        return "torso"
    if core in ("upperArm", "foreArm", "hand", "elbow", "foreArm_twist",
                "fingers", "thumb", "index", "middle", "ring", "pinky") or core[:-1] in (
            "thumb", "index", "middle", "ring", "pinky"):
        return "arm" + side
    # finger bones like index1_L already caught
    if any(core.startswith(p) for p in ("thumb", "index", "middle", "ring", "pinky", "finger")):
        return "arm" + side
    if core in ("thigh", "shin", "foot", "toe", "knee", "tasset"):
        return "leg" + side
    return "torso"


def anatomical_pair(name, have):
    """Parent and child anatomical bones a helper sits between."""
    base = name
    while base.startswith("mid_"):
        base = base[4:]
    pairs = {
        "upperArm": "foreArm", "foreArm": "hand", "thigh": "shin", "shin": "foot",
        "pauldron": None, "elbow": None, "knee": None, "tasset": None,
    }
    side = side_of(base)
    core = base[:-2] if side else base
    child_core = {
        "upperArm": "foreArm", "foreArm": "hand", "hand": None,
        "thigh": "shin", "shin": "foot", "foot": None,
        "spine": "spine2", "spine2": "chest", "chest": "upperChest",
        "upperChest": "neck", "neck": "head", "hips": "spine",
        "shoulder": "upperArm",
    }.get(core)
    parent_core = {
        "foreArm": "upperArm", "hand": "foreArm", "shin": "thigh", "foot": "shin",
        "spine2": "spine", "chest": "spine2", "upperChest": "chest", "neck": "upperChest",
        "head": "neck", "upperArm": "shoulder", "pauldron": "shoulder",
        "elbow": "upperArm", "knee": "thigh", "tasset": "hips",
    }.get(core)
    def pick(core_name):
        if core_name is None:
            return None
        n = core_name + side
        if n in have:
            return n
        # fallbacks when the rig skips a bone
        alt = {"spine2": "chest", "upperChest": "neck", "neck": "head", "shoulder": "upperArm"}.get(core_name)
        if alt and alt + side in have:
            return alt + side
        if core_name + side == n and core_name in have:
            return core_name
        return None
    return pick(parent_core if parent_core else core), pick(child_core)


def tube(p0, p1, r0, r1, n=8):
    d = p1 - p0
    L = np.linalg.norm(d)
    if L < 1e-4:
        return np.zeros((0, 3)), np.zeros((0, 3)), np.zeros((0, 3), int)
    z = d / L
    up = np.array([0.0, 0.0, 1.0]) if abs(z[1]) < 0.9 else np.array([1.0, 0.0, 0.0])
    x = np.cross(up, z); x /= np.linalg.norm(x)
    y = np.cross(z, x)
    ang = np.linspace(0, 2 * np.pi, n, endpoint=False)
    circ = np.stack([np.cos(ang), np.sin(ang)], 1)
    rings = []
    for t, r in ((0.0, r0), (1.0, r1)):
        c = p0 + d * t
        rings.append(c + (circ[:, 0:1] * x + circ[:, 1:2] * y) * r)
    verts = np.vstack(rings)
    faces = []
    for i in range(n):
        j = (i + 1) % n
        faces.append([i, j, n + j])
        faces.append([i, n + j, n + i])
    faces = np.array(faces, int)
    # normals from face, flat
    nrm = np.zeros_like(verts)
    for f in faces:
        fn = np.cross(verts[f[1]] - verts[f[0]], verts[f[2]] - verts[f[0]])
        nrm[f] += fn
    nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-12
    return verts, nrm, faces


def ball(center, radius, n=8):
    verts = []
    for t in (0.35, 1.0, 0.35):
        pass
    rings_y = [-0.55, 0.0, 0.55]
    radii = [0.75, 1.0, 0.75]
    ang = np.linspace(0, 2 * np.pi, n, endpoint=False)
    up = np.array([0.0, 1.0, 0.0])
    x = np.array([1.0, 0.0, 0.0])
    z = np.array([0.0, 0.0, 1.0])
    for yy, rr in zip(rings_y, radii):
        c = center + up * (yy * radius)
        circ = np.stack([np.cos(ang), np.sin(ang)], 1)
        verts.append(c + (circ[:, 0:1] * x + circ[:, 1:2] * z) * (radius * rr))
    verts.append(center + up * radius)
    verts.append(center - up * radius)
    verts = np.vstack(verts)
    faces = []
    for i in range(n):
        j = (i + 1) % n
        faces.append([i, j, n + j])
        faces.append([i, n + j, n + i])
        faces.append([n + i, n + j, 2 * n + j])
        faces.append([n + i, 2 * n + j, 2 * n + i])
        faces.append([2 * n + i, 2 * n + j, 3 * n])
        faces.append([i, 3 * n + 1, j])
    faces = np.array(faces, int)
    nrm = verts - center
    nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-12
    return verts, nrm, faces


def _mail_span(p0, p1, radius, n_side=10, n_ring=4):
    """Tube from p0 to p1. Returns verts, normals, faces, param t in 0..1."""
    d = np.asarray(p1, float) - np.asarray(p0, float)
    length = float(np.linalg.norm(d))
    if length < 0.02:
        empty = np.zeros((0, 3))
        return empty, empty, np.zeros((0, 3), int), np.zeros(0)
    z = d / length
    up = np.array([0.0, 0.0, 1.0]) if abs(z[1]) < 0.85 else np.array([1.0, 0.0, 0.0])
    x = np.cross(up, z)
    x /= np.linalg.norm(x)
    y = np.cross(z, x)
    ang = np.linspace(0, 2 * np.pi, n_side, endpoint=False)
    rings = []
    ts = []
    for t in np.linspace(0.0, 1.0, n_ring):
        c = np.asarray(p0, float) + d * t
        ring = c + (np.cos(ang)[:, None] * x + np.sin(ang)[:, None] * y) * radius
        rings.append(ring)
        ts.append(np.full(n_side, t))
    verts = np.vstack(rings)
    ts = np.concatenate(ts)
    faces = []
    for r in range(n_ring - 1):
        for i in range(n_side):
            j = (i + 1) % n_side
            a = r * n_side + i
            b = r * n_side + j
            c = (r + 1) * n_side + j
            e = (r + 1) * n_side + i
            faces.append([a, b, c])
            faces.append([a, c, e])
    faces = np.array(faces, int)
    nrm = np.zeros_like(verts)
    for f in faces:
        fn = np.cross(verts[f[1]] - verts[f[0]], verts[f[2]] - verts[f[0]])
        nrm[f] += fn
    nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-12
    return verts, nrm, faces, ts


def build_underlayer(hero_pos, joint_index, factor):
    """Dark mail liner. Tight radii, weights blended along each span.

    This is not a flesh mannequin. It stays under the plates and shows at
    the neck, elbow, and knee when those plates open. `factor` is unused;
    a fatter body is what made the slabs cut through the armor.
    """
    del factor
    spans = [
        ("hips", "chest", "hips", "chest", 0.042),
        ("chest", "head", "chest", "head", 0.038),
    ]
    for side in ("_L", "_R"):
        spans += [
            (f"upperArm{side}", f"foreArm{side}", f"upperArm{side}", f"foreArm{side}", 0.024),
            (f"foreArm{side}", f"hand{side}", f"foreArm{side}", f"hand{side}", 0.020),
            (f"thigh{side}", f"shin{side}", f"thigh{side}", f"shin{side}", 0.030),
            (f"shin{side}", f"foot{side}", f"shin{side}", f"foot{side}", 0.024),
        ]
    vs, ns, fs, js, ws = [], [], [], [], []
    counts = {}

    def add(v, n, f, t, bone_a, bone_b):
        if len(v) == 0 or bone_a not in joint_index:
            return
        base = sum(len(x) for x in vs)
        vs.append(v.astype(np.float32))
        ns.append(n.astype(np.float32))
        fs.append(f + base)
        jj = np.zeros((len(v), 4), np.uint8)
        ww = np.zeros((len(v), 4), np.float32)
        ia = joint_index[bone_a]
        ib = joint_index.get(bone_b, ia)
        jj[:, 0] = ia
        jj[:, 1] = ib
        ww[:, 0] = 1.0 - t
        ww[:, 1] = t
        # keep a fully rigid span when both ends are the same bone
        if ia == ib:
            ww[:, 0] = 1.0
            ww[:, 1] = 0.0
        js.append(jj)
        ws.append(ww)
        counts[bone_a] = counts.get(bone_a, 0) + len(v)

    for a, b, ba, bb, radius in spans:
        if a not in hero_pos or b not in hero_pos:
            continue
        # Neck span starts at the chest and reaches into the head so the
        # collar follows the skull instead of leaving a hole under the helm.
        p0 = hero_pos[a]
        p1 = hero_pos[b]
        if b == "head":
            p1 = p1 + np.array([0.0, 0.045, 0.0])
        v, n, f, t = _mail_span(p0, p1, radius)
        add(v, n, f, t, ba if ba in joint_index else a, bb if bb in joint_index else ba)
    if not vs:
        raise RuntimeError("underlayer empty")
    pos = np.vstack(vs)
    nrm = np.vstack(ns)
    faces = np.vstack(fs).astype(np.uint32)
    joints = np.vstack(js)
    weights = np.vstack(ws)
    uv = np.zeros((len(pos), 2), np.float32)
    return pos, nrm, uv, joints, weights, faces, counts


def _retired_build_underlayer(hero_pos, joint_index, factor):
    """Previous flesh cylinders. Kept out of the build path."""
    R = {
        "torso": 0.100 * factor,
        "neck": 0.064 * factor,
        "shoulder": 0.042 * factor,
        "arm": 0.032 * factor,
        "fore": 0.026 * factor,
        "thigh": 0.072 * factor,
        "shin": 0.048 * factor,
        "foot": 0.038 * factor,
    }
    segs = [
        ("hips", "spine", "torso", "hips"),
        ("spine", "chest", "torso", "spine"),
        ("chest", "neck", "torso", "chest"),
        ("chest", "head", "neck", "chest"),
        ("neck", "head", "neck", "neck"),
        ("shoulder_L", "upperArm_L", "shoulder", "shoulder_L"),
        ("shoulder_R", "upperArm_R", "shoulder", "shoulder_R"),
        ("upperArm_L", "foreArm_L", "arm", "upperArm_L"),
        ("upperArm_R", "foreArm_R", "arm", "upperArm_R"),
        ("foreArm_L", "hand_L", "fore", "foreArm_L"),
        ("foreArm_R", "hand_R", "fore", "foreArm_R"),
        ("thigh_L", "shin_L", "thigh", "thigh_L"),
        ("thigh_R", "shin_R", "thigh", "thigh_R"),
        ("shin_L", "foot_L", "shin", "shin_L"),
        ("shin_R", "foot_R", "shin", "shin_R"),
    ]
    balls = [
        ("foreArm_L", "fore", "upperArm_L"),
        ("foreArm_R", "fore", "upperArm_R"),
        ("shin_L", "shin", "thigh_L"),
        ("shin_R", "shin", "thigh_R"),
        ("upperArm_L", "arm", "upperArm_L"),
        ("upperArm_R", "arm", "upperArm_R"),
    ]
    vs, ns, fs, js = [], [], [], []
    counts = {}

    def add(v, n, f, bone):
        if len(v) == 0 or bone not in joint_index:
            return
        base = sum(len(x) for x in vs)
        vs.append(v)
        ns.append(n)
        fs.append(f + base)
        j = np.zeros((len(v), 4), np.uint8)
        j[:, 0] = joint_index[bone]
        js.append(j)
        counts[bone] = counts.get(bone, 0) + len(v)

    for a, b, kind, bone in segs:
        if a not in hero_pos or b not in hero_pos:
            continue
        if a == "chest" and b == "head" and "neck" in hero_pos:
            continue
        if a == "neck" and "neck" not in hero_pos:
            continue
        p0, p1 = hero_pos[a].copy(), hero_pos[b].copy()
        # Push the neck tube up into the head so the collar is not a hole.
        if b == "head":
            p1 = p1 + np.array([0.0, 0.06, 0.0])
        if a.startswith("foreArm"):
            fist = hero_pos.get("fist" + a[-2:])
            if fist is not None:
                p1 = fist
        v, n, f = tube(p0, p1, R[kind], R[kind] * 0.92)
        add(v, n, f, bone if bone in joint_index else a)
    for bone, kind, weight_bone in balls:
        if bone not in hero_pos:
            continue
        v, n, f = ball(hero_pos[bone], R[kind] * 1.15)
        add(v, n, f, weight_bone if weight_bone in joint_index else bone)
    # feet: short sole so the boot is not empty
    for side in ("_L", "_R"):
        foot = "foot" + side
        shin = "shin" + side
        if foot not in hero_pos or shin not in hero_pos:
            continue
        d = hero_pos[foot] - hero_pos[shin]
        d = d / (np.linalg.norm(d) + 1e-8)
        v, n, f = tube(hero_pos[foot], hero_pos[foot] + d * 0.07, R["foot"], R["foot"] * 0.8)
        add(v, n, f, foot)
    if not vs:
        raise RuntimeError("underlayer empty")
    pos = np.vstack(vs).astype(np.float32)
    nrm = np.vstack(ns).astype(np.float32)
    faces = np.vstack(fs).astype(np.uint32)
    joints = np.vstack(js)
    weights = np.zeros_like(joints, np.float32)
    weights[:, 0] = 1.0
    uv = np.zeros((len(pos), 2), np.float32)
    return pos, nrm, uv, joints, weights, faces, counts


def split_hero(js, blob):
    prim = js["meshes"][0]["primitives"][0]
    pos = read_acc(js, blob, prim["attributes"]["POSITION"]).astype(np.float32)
    nrm = read_acc(js, blob, prim["attributes"]["NORMAL"]).astype(np.float32)
    uv = read_acc(js, blob, prim["attributes"]["TEXCOORD_0"]).astype(np.float32)
    joints = read_acc(js, blob, prim["attributes"]["JOINTS_0"]).astype(np.uint8)
    weights = read_acc(js, blob, prim["attributes"]["WEIGHTS_0"]).astype(np.float32)
    indices = read_acc(js, blob, prim["indices"]).astype(np.int64).reshape(-1)
    names, jpos, _, _, _ = joint_maps(js)
    bone_i = dominant(joints, weights)
    bone_names = np.array(names)[bone_i]
    keep = np.array([is_keep(n) for n in bone_names])
    # Sleeves and props weighted to the hand bone are not the fist.
    for side in ("_L", "_R"):
        hn = "hand" + side
        if hn not in jpos:
            continue
        m = bone_names == hn
        if not np.any(m):
            continue
        sel = np.where(m)[0]
        dist = np.linalg.norm(pos[sel] - jpos[hn], axis=1)
        core = pos[sel][np.argsort(dist)[:max(8, int(0.35 * len(sel)))]]
        center = np.median(core, axis=0)
        d2 = np.linalg.norm(pos[sel] - center, axis=1)
        keep[sel[d2 > 0.10]] = False
    # small neck skin (not a collar): keep if the neck cloud is tighter than 4 cm
    neck = bone_names == "neck"
    if neck.sum() > 0:
        rad = np.linalg.norm(pos[neck] - pos[neck].mean(0), axis=1)
        if np.percentile(rad, 90) < 0.04:
            keep[neck] = True
    tri = indices.reshape(-1, 3)
    keep_tri = keep[tri].all(1)
    # Outfit keeps every non-keep triangle, including ones that touch a fist or the head,
    # so those faces are not left with a dangling index.
    out_tri = ~keep_tri
    outfit_verts = np.zeros(len(pos), bool)
    outfit_verts[~keep] = True
    if out_tri.any():
        outfit_verts[np.unique(tri[out_tri])] = True

    def take(mask_v, tri_mask):
        remap = -np.ones(len(pos), np.int64)
        sel = np.where(mask_v)[0]
        remap[sel] = np.arange(len(sel))
        faces = remap[tri[tri_mask]]
        if faces.size and (faces < 0).any():
            raise RuntimeError("triangle referenced a vertex outside its mesh")
        return (pos[sel], nrm[sel], uv[sel], joints[sel], weights[sel], faces.astype(np.uint32))

    kept = take(keep, keep_tri)
    outfit = take(outfit_verts, out_tri)
    # coverage notes: which regions had no source skin
    region = {
        "head_hair_face": int(np.isin(bone_names, [n for n in names if n.startswith(("head", "jaw", "eye", "hair"))]).sum()) if False else int(sum(1 for n in bone_names if n.startswith(("head", "jaw", "eye", "hair")))),
        "hands": int(sum(1 for n in bone_names if n.startswith(("hand_", "thumb", "index", "middle", "ring", "pinky", "finger")))),
        "outfit_verts": int((~keep).sum()),
        "keep_verts": int(keep.sum()),
        "source_verts": int(len(pos)),
    }
    head_m = np.array([n.startswith("head") for n in bone_names])
    color = face_color(js, blob, pos[head_m], uv[head_m], "head") if head_m.any() else [0.45, 0.30, 0.24, 1.0]
    # shoulder width for the underlayer girth
    sw = 0.38
    if "upperArm_L" in jpos and "upperArm_R" in jpos:
        sw = float(np.linalg.norm(jpos["upperArm_L"] - jpos["upperArm_R"]))
    factor = float(np.clip(sw / 0.38, 0.90, 1.05))
    fists = {}
    for side in ("_L", "_R"):
        hn = "hand" + side
        m = (bone_names == hn) & keep
        if m.sum() < 8 or hn not in jpos:
            continue
        sel = pos[m]
        dist = np.linalg.norm(sel - jpos[hn], axis=1)
        core = sel[np.argsort(dist)[:max(8, int(0.5 * len(sel)))]]
        fists["fist" + side] = np.median(core, axis=0)
    jpos = dict(jpos)
    jpos.update(fists)
    jindex = {n: i for i, n in enumerate(names)}
    under = build_underlayer(jpos, jindex, factor)
    return kept, outfit, under, region, color, factor, jpos, names


def write_partition(src_js, src_blob, kept, outfit, under, color, body_path, outfit_path):
    def fresh():
        js = json.loads(json.dumps(src_js))
        blob = bytearray(src_blob)
        return js, blob

    def add_node(js, mesh_i, name):
        node = {"mesh": mesh_i, "name": name, "skin": 0}
        js["nodes"].append(node)
        # parent is the scene root that already holds the original mesh
        root = js["scenes"][0]["nodes"][0]
        js["nodes"][root].setdefault("children", []).append(len(js["nodes"]) - 1)

    # body: replace the original primitive with keep, add underlayer mesh node
    js, blob = fresh()
    kp, kn, ku, kj, kw, kf = kept
    prim = pack_mesh(js, blob, kp, kn, ku, kj, kw, kf)
    prim["material"] = js["meshes"][0]["primitives"][0].get("material", 0)
    js["meshes"][0]["primitives"] = [prim]
    js["meshes"][0]["name"] = "body_keep"
    up, un, uu, uj, uw, uf, _counts = under
    uprim = pack_mesh(js, blob, up, un, uu, uj, uw, uf)
    js["materials"].append({
        "name": "underlayer_mail",
        "pbrMetallicRoughness": {
            "baseColorFactor": color,
            "metallicFactor": 0.72,
            "roughnessFactor": 0.40,
        },
        "doubleSided": False,
    })
    uprim["material"] = len(js["materials"]) - 1
    js["meshes"].append({"name": "underlayer", "primitives": [uprim]})
    add_node(js, len(js["meshes"]) - 1, "underlayer")
    save_glb(js, blob, body_path)

    js, blob = fresh()
    op, on, ou, oj, ow, of = outfit
    prim = pack_mesh(js, blob, op, on, ou, oj, ow, of)
    prim["material"] = js["meshes"][0]["primitives"][0].get("material", 0)
    js["meshes"][0]["primitives"] = [prim]
    js["meshes"][0]["name"] = "outfit"
    # rename mesh node
    for n in js["nodes"]:
        if "mesh" in n:
            n["name"] = "outfit"
    save_glb(js, blob, outfit_path)
    return _counts


def length(pos, a, b):
    if a not in pos or b not in pos:
        return None
    return float(np.linalg.norm(pos[a] - pos[b]))


def fit_armor(hero_pos, armor_js, armor_blob, out_path):
    names, apos, node_of, W, parent = joint_maps(armor_js)
    # ratios from bone lengths. One scale per chain so plates on that chain keep their overlaps.
    def ratio(ha, hb, aa, ab, lo, hi):
        h = length(hero_pos, ha, hb)
        ar = length(apos, aa, ab)
        if not h or not ar or ar < 1e-4:
            return 1.0
        return float(np.clip(h / ar, lo, hi))

    # Do not shrink the cuirass. A shorter torso keeps the authored plate size.
    torso = ratio("hips", "head", "hips", "head", 1.0, 1.15)
    ratios = {"torso": torso, "head": 1.0}
    for side in ("_L", "_R"):
        # Floor keeps the plate wide enough to read as the same sculpt on a shorter arm.
        ratios["arm" + side] = ratio("upperArm" + side, "hand" + side, "upperArm" + side, "hand" + side, 0.90, 1.20)
        ratios["leg" + side] = ratio("thigh" + side, "foot" + side, "thigh" + side, "foot" + side, 0.75, 1.25)
    # helm sized to the head cloud, placed in the vertex pass
    ratios["head"] = 1.0

    desired = {}
    for name in names:
        if name in ("hand_L", "hand_R") and ("fist" + name[-2:]) in hero_pos:
            desired[name] = hero_pos["fist" + name[-2:]].copy()
            continue
        if name in hero_pos and chain_of(name) != "head":
            desired[name] = hero_pos[name].copy()
        elif name == "head" and "head" in hero_pos:
            desired[name] = hero_pos["head"].copy()
    # intermediates the hero rig skips, then helpers, by fraction along an anatomical span
    def span_ends(name):
        side = side_of(name)
        core = name[4:] if name.startswith("mid_") else name
        core = core[:-2] if side and core.endswith(side) else core
        table = {
            "spine2": ("spine", "chest"),
            "upperChest": ("chest", "neck"),
            "mid_upperArm": ("upperArm", "foreArm"),
            "mid_foreArm": ("foreArm", "hand"),
            "mid_hand": ("foreArm", "hand"),
            "mid_thigh": ("thigh", "shin"),
            "mid_shin": ("shin", "foot"),
            "mid_foot": ("shin", "foot"),
            "pauldron": ("shoulder", "upperArm"),
            "elbow": ("upperArm", "foreArm"),
            "knee": ("thigh", "shin"),
            "tasset": ("hips", "thigh"),
        }
        key = "mid_" + core if name.startswith("mid_") else core
        if name.startswith("mid_"):
            key = "mid_" + core
        pair = table.get(key) or table.get(core)
        if not pair:
            return None
        a, b = pair
        a = a + side if side and a not in ("hips", "spine", "chest", "neck") else a
        b = b + side if side and b not in ("hips", "spine", "chest", "neck", "head") else b
        if side and a in ("shoulder", "upperArm", "foreArm", "thigh", "shin", "foot", "hand"):
            a = a if a.endswith(side) else a + side
        return a, b

    # fix span_ends more carefully
    def ends(name):
        side = side_of(name)
        raw = name[:-2] if side else name
        table = {
            "spine2": ("spine", "chest"),
            "upperChest": ("chest", "neck"),
            "mid_spine": ("spine", "chest"),
            "mid_spine2": ("spine", "chest"),
            "mid_chest": ("chest", "neck"),
            "mid_upperChest": ("chest", "neck"),
            "mid_upperArm": ("upperArm", "foreArm"),
            "mid_foreArm": ("foreArm", "hand"),
            "mid_hand": ("hand", "hand"),
            "mid_thigh": ("thigh", "shin"),
            "mid_shin": ("shin", "foot"),
            "mid_foot": ("shin", "foot"),
            "pauldron": ("shoulder", "upperArm"),
            "elbow": ("upperArm", "foreArm"),
            "knee": ("thigh", "shin"),
            "tasset": ("hips", "thigh"),
            "foreArm_twist": ("foreArm", "hand"),
            "tabard_F_01": ("hips", "chest"),
            "tabard_B_01": ("hips", "chest"),
            "tabard_F_02": ("hips", "chest"),
            "tabard_B_02": ("hips", "chest"),
            "mid_tabard_F_02": ("hips", "chest"),
            "mid_tabard_B_02": ("hips", "chest"),
            "mid_tabard_F_03": ("hips", "chest"),
            "mid_tabard_B_03": ("hips", "chest"),
        }
        pair = table.get(raw)
        if not pair:
            return None
        a, b = pair
        def sided(n):
            if n in ("hips", "spine", "chest", "neck", "head"):
                return n
            return n + side if side else n
        return sided(a), sided(b)

    for _ in range(4):
        for name in names:
            if name in desired:
                continue
            pair = ends(name)
            if not pair:
                continue
            a, b = pair
            if a not in desired or b not in desired or a not in apos or b not in apos or name not in apos:
                continue
            span = apos[b] - apos[a]
            denom = float(np.dot(span, span)) + 1e-12
            rel = apos[name] - apos[a]
            frac = float(np.dot(rel, span) / denom)
            closest = apos[a] + span * frac
            # Decorative pieces (tabard, wings) do not lie on the bone. Leave them for the offset pass.
            if frac < -0.05 or frac > 1.05 or np.linalg.norm(apos[name] - closest) > 0.06:
                continue
            desired[name] = desired[a] + (desired[b] - desired[a]) * frac
    for _ in range(6):
        for name in names:
            if name in desired:
                continue
            ni = node_of[name]
            if ni not in parent:
                desired[name] = apos[name].copy()
                continue
            pname = armor_js["nodes"][parent[ni]].get("name")
            if pname not in desired:
                continue
            r = ratios.get(chain_of(name), torso)
            desired[name] = desired[pname] + (apos[name] - apos[pname]) * r
    # Visual fists sit off the hand bone on some rigs. Move the gauntlet onto the fist.
    children = {}
    for nm, ni in node_of.items():
        if ni in parent:
            pn = armor_js["nodes"][parent[ni]].get("name")
            children.setdefault(pn, []).append(nm)

    def subtree(nm):
        out = [nm]
        for c in children.get(nm, []):
            out.extend(subtree(c))
        return out

    for side in ("_L", "_R"):
        fist = hero_pos.get("fist" + side)
        bone = hero_pos.get("hand" + side)
        if fist is None or bone is None:
            continue
        delta = fist - bone
        for nm in subtree("hand" + side):
            if nm == "hand" + side:
                continue
            if nm in hero_pos:
                desired[nm] = hero_pos[nm] + delta
        desired["hand" + side] = fist
    missing = [n for n in names if n not in desired]
    if missing:
        print("  joints with no target", missing, flush=True)

    # helm scale from head-cloud radii is applied to head-weighted verts only
    prim = armor_js["meshes"][0]["primitives"][0]
    pos = read_acc(armor_js, armor_blob, prim["attributes"]["POSITION"]).astype(np.float64)
    nrm = read_acc(armor_js, armor_blob, prim["attributes"]["NORMAL"]).astype(np.float64)
    joints = read_acc(armor_js, armor_blob, prim["attributes"]["JOINTS_0"]).astype(np.int32)
    weights = read_acc(armor_js, armor_blob, prim["attributes"]["WEIGHTS_0"]).astype(np.float32)
    bone_i = dominant(joints, weights)
    bname = np.array(names)[bone_i]

    anatom_child = {
        "hips": "spine", "spine": "spine2", "spine2": "chest", "chest": "upperChest",
        "upperChest": "neck", "neck": "head",
        "shoulder_L": "upperArm_L", "shoulder_R": "upperArm_R",
        "upperArm_L": "foreArm_L", "upperArm_R": "foreArm_R",
        "foreArm_L": "hand_L", "foreArm_R": "hand_R",
        "thigh_L": "shin_L", "thigh_R": "shin_R",
        "shin_L": "foot_L", "shin_R": "foot_R",
    }

    def bone_dir(table, bone):
        # Only an anatomical child. Wings, tabard, and plates must not spin
        # toward a decorative child.
        child = anatom_child.get(bone)
        if child == "spine2" and child not in table and "chest" in table:
            child = "chest"
        if child == "upperChest" and child not in table and "neck" in table:
            child = "neck"
        if child == "neck" and child not in table and "head" in table:
            child = "head"
        if child and child in table and bone in table:
            d = table[child] - table[bone]
            if np.linalg.norm(d) > 1e-4:
                return d
        return None

    new_pos = pos.copy()
    new_nrm = nrm.copy()
    for name in names:
        m = bname == name
        if not np.any(m) or name not in desired or name not in apos:
            continue
        r = ratios.get(chain_of(name), torso)
        old_d = bone_dir(apos, name)
        new_d = bone_dir(desired, name)
        if old_d is None or new_d is None:
            R = np.eye(3)
        else:
            R = rot_between(old_d, new_d)
        if name == "head":
            # size the helm to the hero head cloud, then this pass only places it
            R = np.eye(3)
            r = ratios["head"]
        off = (pos[m] - apos[name]) * r
        new_pos[m] = desired[name] + off @ R.T
        new_nrm[m] = nrm[m] @ R.T

    # helm: rescale head verts about the hero head so the shell covers the head
    # (the loop above used r=1). Done below if both heads exist.
    # Write positions back into a copy and update joint translations.
    blob = bytearray(armor_blob)
    acc = armor_js["accessors"][prim["attributes"]["POSITION"]]
    bv = armor_js["bufferViews"][acc["bufferView"]]
    start = bv.get("byteOffset", 0) + acc.get("byteOffset", 0)
    raw = np.ascontiguousarray(new_pos.astype(np.float32)).tobytes()
    blob[start:start + len(raw)] = raw
    nacc = armor_js["accessors"][prim["attributes"]["NORMAL"]]
    nbv = armor_js["bufferViews"][nacc["bufferView"]]
    nstart = nbv.get("byteOffset", 0) + nacc.get("byteOffset", 0)
    nraw = np.ascontiguousarray(new_nrm.astype(np.float32)).tobytes()
    blob[nstart:nstart + len(nraw)] = nraw

    # translations parent-first
    js = json.loads(json.dumps(armor_js))
    # clear cached worlds by recomputing as we go
    order = []
    seen = set()

    def walk(i):
        if i in seen:
            return
        seen.add(i)
        if i in parent:
            walk(parent[i])
        order.append(i)

    for n in node_of.values():
        walk(n)
    world = {}

    def local_matrix(node):
        t = np.array(node.get("translation", [0, 0, 0]), float)
        r = np.array(node.get("rotation", [0, 0, 0, 1]), float)
        s = np.array(node.get("scale", [1, 1, 1]), float)
        M = np.eye(4)
        M[:3, :3] = quat_mat(r) @ np.diag(s)
        M[:3, 3] = t
        return M

    name_by_node = {node_of[n]: n for n in node_of}
    for i in order:
        node = js["nodes"][i]
        M = local_matrix(node)
        if i in parent and parent[i] in world:
            # if this joint has a desired position, replace local translation
            nm = name_by_node.get(i)
            if nm in desired:
                pw = world[parent[i]]
                R = pw[:3, :3]
                # parent scale is 1, R may include scale
                # solve R @ t = desired - parent_pos
                t = np.linalg.lstsq(R, desired[nm] - pw[:3, 3], rcond=None)[0]
                node["translation"] = [float(x) for x in t]
                M = local_matrix(node)
            world[i] = world[parent[i]] @ M
        else:
            world[i] = M

    # IBM
    skin = js["skins"][0]
    ibm = np.zeros((len(skin["joints"]), 4, 4), np.float32)
    for ji, node_i in enumerate(skin["joints"]):
        inv = np.linalg.inv(world[node_i])
        ibm[ji] = inv.T.astype(np.float32)  # store column-major as raw rows of transpose? 
        # file matched transposed inverse, meaning memory layout is column-major of inv.
        # np stores row-major. Column-major of inv is inv.T in row-major memory.
    a = js["accessors"][skin["inverseBindMatrices"]]
    bv = js["bufferViews"][a["bufferView"]]
    start = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
    raw = np.ascontiguousarray(ibm).tobytes()
    blob[start:start + len(raw)] = raw
    # refresh position min/max
    acc["min"] = new_pos.min(0).astype(float).tolist()
    acc["max"] = new_pos.max(0).astype(float).tolist()
    save_glb(js, blob, out_path)
    return ratios, {k: int(np.sum(bname == k)) for k in ("head", "upperArm_L", "chest", "thigh_L")}


def helm_fit(hero_js, hero_blob, armor_path):
    """Second pass: scale head-weighted armor verts so the helm covers the head cloud."""
    hjs, hblob = hero_js, hero_blob
    hnames, _, _, _, _ = joint_maps(hjs)
    prim = hjs["meshes"][0]["primitives"][0]
    hpos = read_acc(hjs, hblob, prim["attributes"]["POSITION"]).astype(np.float64)
    hj = read_acc(hjs, hblob, prim["attributes"]["JOINTS_0"]).astype(np.int32)
    hw = read_acc(hjs, hblob, prim["attributes"]["WEIGHTS_0"]).astype(np.float32)
    hb = np.array(hnames)[dominant(hj, hw)]
    head = hpos[hb == "head"]
    hc = head.mean(0)
    hr = np.linalg.norm(head - hc, axis=1)
    hero_r = float(np.percentile(hr, 92))

    js, blob = load_glb(armor_path)
    names, apos, _, _, _ = joint_maps(js)
    prim = js["meshes"][0]["primitives"][0]
    pos = read_acc(js, blob, prim["attributes"]["POSITION"]).astype(np.float64)
    joints = read_acc(js, blob, prim["attributes"]["JOINTS_0"]).astype(np.int32)
    weights = read_acc(js, blob, prim["attributes"]["WEIGHTS_0"]).astype(np.float32)
    bname = np.array(names)[dominant(joints, weights)]
    m = bname == "head"
    if m.sum() < 10:
        return 1.0
    ac = pos[m].mean(0)
    ar = float(np.percentile(np.linalg.norm(pos[m] - ac, axis=1), 92))
    # Do not shrink the helm off the face. Grow it only when the head is larger.
    scale = float(np.clip(hero_r / max(ar, 1e-4), 1.0, 1.30))
    pos[m] = hc + (pos[m] - ac) * scale
    acc = js["accessors"][prim["attributes"]["POSITION"]]
    bv = js["bufferViews"][acc["bufferView"]]
    start = bv.get("byteOffset", 0)
    raw = np.ascontiguousarray(pos.astype(np.float32)).tobytes()
    blob[start:start + len(raw)] = raw
    acc["min"] = pos.min(0).astype(float).tolist()
    acc["max"] = pos.max(0).astype(float).tolist()
    save_glb(js, blob, armor_path)
    return scale


def _arm_names(names, side):
    out = []
    for name in names:
        if chain_of(name) == "arm" + side:
            out.append(name)
            continue
        # Pauldrons stay with the cuirass. Scaling them with a short arm
        # pulls the shoulder armor off the chest.
        if name in (f"elbow{side}",):
            out.append(name)
    return out


def _leg_names(names, side):
    return [n for n in names if chain_of(n) == "leg" + side]


def _apply_similarity(pos, mask, pivot_from, pivot_to, direction_from, direction_to):
    """One rotation and one uniform scale. Every selected vertex moves together."""
    span = np.asarray(direction_from, float)
    target = np.asarray(direction_to, float)
    ls = float(np.linalg.norm(span))
    lt = float(np.linalg.norm(target))
    if ls < 1e-5 or lt < 1e-5:
        return 1.0
    scale = lt / ls
    rot = rot_between(span, target)
    src = pos[mask] - np.asarray(pivot_from, float)
    pos[mask] = np.asarray(pivot_to, float) + (src * scale) @ rot.T
    return float(scale)


def _move_joints(desired, names, selected, pivot_from, pivot_to, direction_from, direction_to, old_pos):
    span = np.asarray(direction_from, float)
    target = np.asarray(direction_to, float)
    ls = float(np.linalg.norm(span))
    lt = float(np.linalg.norm(target))
    if ls < 1e-5 or lt < 1e-5:
        return
    scale = lt / ls
    rot = rot_between(span, target)
    for name in selected:
        if name not in old_pos:
            continue
        src = old_pos[name] - np.asarray(pivot_from, float)
        desired[name] = np.asarray(pivot_to, float) + rot @ (src * scale)


def fit_plates(hero_pos, armor_js, armor_blob, out_path):
    """Place the shared sculpt on the hero without tearing plates apart.

    The whole armor gets one scale about the hips so the height matches.
    Each arm, and each leg, then gets one more uniform scale and one aim
    so that assembly stays in one piece. Nothing here changes clip amplitude.
    """
    names, apos, node_of, _, parent = joint_maps(armor_js)
    prim = armor_js["meshes"][0]["primitives"][0]
    pos = read_acc(armor_js, armor_blob, prim["attributes"]["POSITION"]).astype(np.float64)
    nrm = read_acc(armor_js, armor_blob, prim["attributes"]["NORMAL"]).astype(np.float64)
    joints = read_acc(armor_js, armor_blob, prim["attributes"]["JOINTS_0"]).astype(np.int32)
    weights = read_acc(armor_js, armor_blob, prim["attributes"]["WEIGHTS_0"]).astype(np.float32)
    bname = np.array(names)[dominant(joints, weights)]

    def dist(table, a, b):
        if a not in table or b not in table:
            return None
        return float(np.linalg.norm(table[a] - table[b]))

    h_len = dist(hero_pos, "hips", "head")
    a_len = dist(apos, "hips", "head")
    s_torso = 1.0 if not h_len or not a_len else float(np.clip(h_len / a_len, 0.85, 1.15))
    hip_a = apos["hips"]
    hip_h = hero_pos["hips"]
    pos[:] = hip_h + (pos - hip_a) * s_torso
    moved = {n: hip_h + (apos[n] - hip_a) * s_torso for n in names}
    ratios = {"torso": round(s_torso, 3)}

    def assembly(side, names_fn, root, tip):
        selected = names_fn(names, side)
        if root not in moved or tip not in moved or root not in hero_pos or tip not in hero_pos:
            return
        mask = np.isin(bname, selected)
        if not np.any(mask):
            return
        span = moved[tip] - moved[root]
        target = hero_pos[tip] - hero_pos[root]
        scale = _apply_similarity(pos, mask, moved[root], hero_pos[root], span, target)
        _move_joints(moved, names, selected, moved[root], hero_pos[root], span, target, dict(moved))
        # _move_joints read old positions from the dict it also writes. Recompute
        # from the pre-assembly positions captured below.
        ratios["scale" + side + root[:4]] = round(float(scale), 3)

    # Recompute assembly with a snapshot so joints and verts share one transform.
    for side in ("_L", "_R"):
        for names_fn, root, tip, key in (
            (_arm_names, f"upperArm{side}", f"hand{side}", f"arm{side}"),
            (_leg_names, f"thigh{side}", f"foot{side}", f"leg{side}"),
        ):
            selected = names_fn(names, side)
            if root not in moved or tip not in moved or root not in hero_pos or tip not in hero_pos:
                continue
            before = {n: moved[n].copy() for n in selected if n in moved}
            span = before[tip] - before[root] if tip in before and root in before else None
            if span is None:
                continue
            target = hero_pos[tip] - hero_pos[root]
            if float(np.linalg.norm(span)) < 1e-5:
                continue
            scale = float(np.linalg.norm(target) / np.linalg.norm(span))
            # Legs already follow the torso scale on these rigs. A second scale
            # under a few percent only slides the greaves.
            if key.startswith("leg") and 0.96 <= scale <= 1.04:
                ratios[key] = 1.0
                continue
            mask = np.isin(bname, selected)
            rot = rot_between(span, target)
            src = pos[mask] - before[root]
            pos[mask] = hero_pos[root] + (src * scale) @ rot.T
            nrm[mask] = nrm[mask] @ rot.T
            for n in selected:
                if n not in before:
                    continue
                moved[n] = hero_pos[root] + rot @ ((before[n] - before[root]) * scale)
            ratios[key] = round(scale, 3)

    # Helm: slide the head shell toward the head cloud, rigidly, and only a
    # short way so it stays on the gorget. Do not scale it.
    head_m = bname == "head"
    if head_m.any() and "head" in hero_pos:
        helm_c = pos[head_m].mean(0)
        # The hair cloud sits above the skull. Aim the helm at the head bone,
        # not at the hair centroid, or the visor climbs off the face.
        delta = hero_pos["head"] - moved.get("head", helm_c)
        # Prefer a small lift toward the head bone if the helm is low.
        if float(np.linalg.norm(delta)) > 1e-6:
            cap = 0.035
            if float(np.linalg.norm(delta)) > cap:
                delta = delta / np.linalg.norm(delta) * cap
            pos[head_m] += delta
            if "head" in moved:
                moved["head"] = moved["head"] + delta
            neck_m = bname == "neck"
            if neck_m.any():
                pos[neck_m] += delta * 0.45
                if "neck" in moved:
                    moved["neck"] = moved["neck"] + delta * 0.45
        ratios["helm_shift_cm"] = round(float(np.linalg.norm(delta)) * 100, 2)

    # Normals: uniform scale and rotation. Rotate normals by the same arm/leg
    # rotation is approximate; renormalize. Torso scale does not change them.
    nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-12

    blob = bytearray(armor_blob)
    acc = armor_js["accessors"][prim["attributes"]["POSITION"]]
    bv = armor_js["bufferViews"][acc["bufferView"]]
    start = bv.get("byteOffset", 0) + acc.get("byteOffset", 0)
    raw = np.ascontiguousarray(pos.astype(np.float32)).tobytes()
    blob[start:start + len(raw)] = raw
    nacc = armor_js["accessors"][prim["attributes"]["NORMAL"]]
    nbv = armor_js["bufferViews"][nacc["bufferView"]]
    nstart = nbv.get("byteOffset", 0) + nacc.get("byteOffset", 0)
    nraw = np.ascontiguousarray(nrm.astype(np.float32)).tobytes()
    blob[nstart:nstart + len(nraw)] = nraw

    js = json.loads(json.dumps(armor_js))
    order = []
    seen = set()

    def walk(i):
        if i in seen:
            return
        seen.add(i)
        if i in parent:
            walk(parent[i])
        order.append(i)

    for n in node_of.values():
        walk(n)
    world = {}

    def local_matrix(node):
        t = np.array(node.get("translation", [0, 0, 0]), float)
        r = np.array(node.get("rotation", [0, 0, 0, 1]), float)
        s = np.array(node.get("scale", [1, 1, 1]), float)
        m = np.eye(4)
        m[:3, :3] = quat_mat(r) @ np.diag(s)
        m[:3, 3] = t
        return m

    name_by_node = {node_of[n]: n for n in node_of}
    for i in order:
        node = js["nodes"][i]
        mat = local_matrix(node)
        if i in parent and parent[i] in world:
            nm = name_by_node.get(i)
            if nm in moved:
                pw = world[parent[i]]
                t = np.linalg.lstsq(pw[:3, :3], moved[nm] - pw[:3, 3], rcond=None)[0]
                node["translation"] = [float(x) for x in t]
                mat = local_matrix(node)
            world[i] = world[parent[i]] @ mat
        else:
            world[i] = mat

    skin = js["skins"][0]
    ibm = np.zeros((len(skin["joints"]), 4, 4), np.float32)
    for ji, node_i in enumerate(skin["joints"]):
        ibm[ji] = np.linalg.inv(world[node_i]).T.astype(np.float32)
    a = js["accessors"][skin["inverseBindMatrices"]]
    ibv = js["bufferViews"][a["bufferView"]]
    istart = ibv.get("byteOffset", 0) + a.get("byteOffset", 0)
    ibraw = np.ascontiguousarray(ibm).tobytes()
    blob[istart:istart + len(ibraw)] = ibraw
    acc["min"] = pos.min(0).astype(float).tolist()
    acc["max"] = pos.max(0).astype(float).tolist()
    save_glb(js, blob, out_path)
    return ratios


def mask_hair_under_helm(body_path, armor_path, out_path):
    """Drop hair vertices that intersect the helm. The face stays.

    The unequipped body file is not modified. This equipped copy is the only
    place hair is removed, and only where it occupies the same space as the helm.
    """
    bjs, bblob = load_glb(body_path)
    ajs, ablob = load_glb(armor_path)
    bnames, _, _, _, _ = joint_maps(bjs)
    anames, _, _, _, _ = joint_maps(ajs)
    bprim = bjs["meshes"][0]["primitives"][0]
    pos = read_acc(bjs, bblob, bprim["attributes"]["POSITION"]).astype(np.float64)
    uv = read_acc(bjs, bblob, bprim["attributes"]["TEXCOORD_0"]).astype(np.float64)
    joints = read_acc(bjs, bblob, bprim["attributes"]["JOINTS_0"]).astype(np.int32)
    weights = read_acc(bjs, bblob, bprim["attributes"]["WEIGHTS_0"]).astype(np.float32)
    bone = np.array(bnames)[dominant(joints, weights)]
    head = bone == "head"
    aprim = ajs["meshes"][0]["primitives"][0]
    apos = read_acc(ajs, ablob, aprim["attributes"]["POSITION"]).astype(np.float64)
    aj = read_acc(ajs, ablob, aprim["attributes"]["JOINTS_0"]).astype(np.int32)
    aw = read_acc(ajs, ablob, aprim["attributes"]["WEIGHTS_0"]).astype(np.float32)
    abone = np.array(anames)[dominant(aj, aw)]
    helm = apos[abone == "head"]
    if helm.shape[0] < 20 or head.sum() < 20:
        return {"removed": 0}
    # Color sample: dark texels are hair. Lighter texels on the head are the face.
    im = bjs["images"][0]
    bv = bjs["bufferViews"][im["bufferView"]]
    png = bytes(bblob[bv.get("byteOffset", 0):bv.get("byteOffset", 0) + bv["byteLength"]])
    img = np.asarray(Image.open(io.BytesIO(png)).convert("RGB"))
    h, w = img.shape[:2]
    sel = np.where(head)[0]
    u = np.clip(uv[sel, 0], 0, 0.999)
    v = np.clip(uv[sel, 1], 0, 0.999)
    xs = np.clip((u * w).astype(int), 0, w - 1)
    ys = np.clip(((1.0 - v) * h).astype(int), 0, h - 1)
    lum = img[ys, xs].astype(np.float64).mean(1) / 255.0
    # Face is the lighter front of the head. Never delete it.
    face = np.zeros(len(pos), bool)
    face[sel[lum >= 0.28]] = True
    hair = head & ~face
    # Also treat the crown as hair even when a texel is mid-grey.
    crown = head & (pos[:, 1] > np.percentile(pos[head, 1], 72))
    hair = hair | crown
    face = head & ~hair
    try:
        from scipy.spatial import cKDTree
        tree = cKDTree(helm)
        dist, _ = tree.query(pos[hair], k=1)
    except Exception:
        # Fallback: distance to helm centroid compared with the helm's own radius.
        hc = helm.mean(0)
        hr = np.percentile(np.linalg.norm(helm - hc, axis=1), 55)
        dist = np.linalg.norm(pos[hair] - hc, axis=1)
        dist = np.where(dist < hr, 0.0, dist)
    drop_local = dist < 0.016
    drop = np.zeros(len(pos), bool)
    drop[np.where(hair)[0][drop_local]] = True
    # Face is protected even if the distance test would have caught it.
    drop[face] = False
    keep = ~drop
    if drop.sum() == 0:
        keep = np.ones(len(pos), bool)
    remap = -np.ones(len(pos), np.int64)
    remap[keep] = np.arange(keep.sum())
    indices = read_acc(bjs, bblob, bprim["indices"]).astype(np.int64).reshape(-1, 3)
    tri_ok = keep[indices].all(1)
    faces = remap[indices[tri_ok]].astype(np.uint32)
    nrm = read_acc(bjs, bblob, bprim["attributes"]["NORMAL"]).astype(np.float32)
    uv32 = read_acc(bjs, bblob, bprim["attributes"]["TEXCOORD_0"]).astype(np.float32)
    j8 = read_acc(bjs, bblob, bprim["attributes"]["JOINTS_0"]).astype(np.uint8)
    w32 = read_acc(bjs, bblob, bprim["attributes"]["WEIGHTS_0"]).astype(np.float32)
    js = json.loads(json.dumps(bjs))
    blob = bytearray(bblob)
    packed = pack_mesh(
        js, blob,
        pos[keep].astype(np.float32), nrm[keep], uv32[keep], j8[keep], w32[keep], faces,
    )
    packed["material"] = bprim.get("material", 0)
    js["meshes"][0]["primitives"] = [packed]
    save_glb(js, blob, out_path)
    seated = _seat_fists(out_path)
    return {
        "removed": int(drop.sum()),
        "hair": int(hair.sum()),
        "face": int(face.sum()),
        "fists_seated_cm": seated,
    }


def _seat_fists(path):
    """Move a fist that does not sit on its hand bone onto that bone.

    Some rigs leave the hand voxels well below the wrist. The sleeve used to
    hide the gap. The equipped preview puts the fist on the wrist. The
    unequipped body file is left where the source modeled it.
    """
    js, blob = load_glb(path)
    names, jpos, _, _, _ = joint_maps(js)
    prim = js["meshes"][0]["primitives"][0]
    pos = read_acc(js, blob, prim["attributes"]["POSITION"]).astype(np.float64)
    joints = read_acc(js, blob, prim["attributes"]["JOINTS_0"]).astype(np.int32)
    weights = read_acc(js, blob, prim["attributes"]["WEIGHTS_0"]).astype(np.float32)
    bone = np.array(names)[dominant(joints, weights)]
    shifts = {}
    for side in ("_L", "_R"):
        name = "hand" + side
        if name not in jpos:
            continue
        m = bone == name
        if m.sum() < 8:
            continue
        delta = jpos[name] - pos[m].mean(0)
        dist = float(np.linalg.norm(delta))
        if dist < 0.03:
            shifts[side] = 0.0
            continue
        # Rook's hand voxels sit about 34 cm off the wrist. The sleeve hid that.
        # Cap high enough to actually reach the bone.
        if dist > 0.40:
            delta = delta / dist * 0.40
            dist = 0.40
        pos[m] += delta
        shifts[side] = round(dist * 100, 1)
    if not any(shifts.values()):
        return shifts
    acc = js["accessors"][prim["attributes"]["POSITION"]]
    bv = js["bufferViews"][acc["bufferView"]]
    start = bv.get("byteOffset", 0) + acc.get("byteOffset", 0)
    raw = np.ascontiguousarray(pos.astype(np.float32)).tobytes()
    # The equipped mesh was repacked, so the position view is at the end and
    # this in-place write is only valid when the accessor still points at a
    # tightly packed float view of the same length. Repack if the size differs.
    if len(raw) != bv["byteLength"]:
        nrm = read_acc(js, blob, prim["attributes"]["NORMAL"]).astype(np.float32)
        uv = read_acc(js, blob, prim["attributes"]["TEXCOORD_0"]).astype(np.float32)
        j8 = read_acc(js, blob, prim["attributes"]["JOINTS_0"]).astype(np.uint8)
        w32 = read_acc(js, blob, prim["attributes"]["WEIGHTS_0"]).astype(np.float32)
        faces = read_acc(js, blob, prim["indices"]).astype(np.uint32)
        js2 = json.loads(json.dumps(js))
        blob2 = bytearray(blob)
        packed = pack_mesh(js2, blob2, pos.astype(np.float32), nrm, uv, j8, w32, faces.reshape(-1, 3))
        packed["material"] = prim.get("material", 0)
        js2["meshes"][0]["primitives"] = [packed]
        save_glb(js2, blob2, path)
        return shifts
    blob = bytearray(blob)
    blob[start:start + len(raw)] = raw
    acc["min"] = pos.min(0).astype(float).tolist()
    acc["max"] = pos.max(0).astype(float).tolist()
    save_glb(js, blob, path)
    return shifts


def build_one(hid):
    spec = PILOTS[hid]
    print("BUILD", hid, flush=True)
    js, blob = load_glb(spec["path"])
    kept, outfit, under, region, color, factor, jpos, names = split_hero(js, blob)
    assert region["keep_verts"] + region["outfit_verts"] == region["source_verts"]
    assert len(kept[0]) == region["keep_verts"]
    region["outfit_mesh_verts"] = int(len(outfit[0]))
    region["boundary_copies_in_outfit"] = int(len(outfit[0]) - region["outfit_verts"])
    out_dir = os.path.join(ROOT, hid)
    os.makedirs(out_dir, exist_ok=True)
    mail = [0.055, 0.052, 0.048, 1.0]
    counts = write_partition(
        js, blob, kept, outfit, under, mail,
        os.path.join(out_dir, f"{hid}_body.glb"),
        os.path.join(out_dir, f"{hid}_outfit.glb"),
    )
    armor_js, armor_blob = load_glb(ARMOR[spec["armor"]])
    ratios = fit_plates(jpos, armor_js, armor_blob, os.path.join(out_dir, f"{hid}_armor_fit.glb"))
    # The bind-pose audit showed the source already reconstructs (world @ IBM = I).
    # Moving fists onto the joint, or deleting hair, changes that pose. Do not.
    # clips
    clips = [a["name"] for a in js.get("animations", [])]
    report = {
        "id": hid,
        "source": spec["source"],
        "source_blob": spec["blob"],
        "source_untouched": True,
        "armor_set": spec["armor"],
        "armor_source": ARMOR[spec["armor"]],
        "why": spec["why"],
        "clips": clips,
        "jump_clip": any("jump" in c.lower() for c in clips),
        "partition": region,
        "underlayer_factor": round(factor, 3),
        "underlayer_verts_by_bone": counts,
        "underlayer_color_linear": mail,
        "armor_ratios": ratios,
        "attachment": "Bind-space joint origin. Node world translation matches inv(IBM). Hero vertices are not moved.",
        "animation": "Clips are copied in full. No angle limit and no pose-bone scale.",
        "covered_by_source_skin": ["head", "hair", "face", "hands"],
        "no_source_skin_under": ["torso", "upper_arm", "forearm", "thigh", "shin", "foot"],
        "unequipped": "body keep + outfit (underlayer hidden) restores the source partition",
        "equipped": "body keep + underlayer + fitted armor; outfit and its cape stay off",
        "cape_rule": "Outfit holds every cape/coat bone vertex. Equipping hides that outfit, so the hero cape is off while the armor's own cloak stays. Unequipping shows the outfit again, cape included.",
    }
    json.dump(report, open(os.path.join(out_dir, "fit.json"), "w"), indent=2)
    print(json.dumps({k: report[k] for k in ("partition", "armor_ratios", "attachment", "jump_clip")}, indent=2), flush=True)
    return report


def roster():
    """Clip inventory for the 22 playable heroes. Assets are not all fitted."""
    rows = []
    for hid in PLAYABLE:
        if hid == "darius":
            ref = "origin/weaponless-rigs:voxel/darius_voxel_noweapon.glb"
        else:
            ref = f"origin/main:voxel/{hid}_voxel.glb"
        try:
            raw = subprocess.check_output(["git", "cat-file", "-p", ref], stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError:
            rows.append({"id": hid, "source": ref, "present": False})
            continue
        # JSON chunk
        off = 12
        js = None
        while off < len(raw):
            clen, ctype = struct.unpack_from("<II", raw, off)
            off += 8
            chunk = raw[off:off + clen]
            off += clen
            if ctype == 0x4E4F534A:
                js = json.loads(chunk)
                break
        clips = [a["name"] for a in js.get("animations", [])] if js else []
        rows.append({
            "id": hid,
            "source": ref,
            "present": True,
            "clips": clips,
            "has_idle": "idle" in clips,
            "has_walk": "walk" in clips,
            "has_run": "run" in clips,
            "has_attack": any(c.startswith("attack") for c in clips),
            "has_jump": any("jump" in c.lower() for c in clips),
            "fitted_this_pass": hid in PILOTS,
        })
        print("roster", hid, "jump" if rows[-1]["has_jump"] else "no-jump", "clips", len(clips), flush=True)
    return rows


def main():
    os.makedirs(ROOT, exist_ok=True)
    reports = [build_one(hid) for hid in PILOTS]
    rows = roster()
    json.dump({"playable_22": rows, "pilots": reports}, open(os.path.join(ROOT, "coverage.json"), "w"), indent=2)
    print("DONE", ROOT)


if __name__ == "__main__":
    main()
