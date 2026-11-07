"""Reseat rigid mid-joint islands onto the plate they already touch.

v6 binds every former seam piece to a mid_* helper that takes half of the
child joint's rotation. At the larger v6 swings that half-turn leaves the
piece floating between the two plates. This pass does not move vertices,
UVs, normals, materials, or clip tracks. An island currently on a limb
mid_* bone is moved fully onto the parent plate or the child plate when
its vertices are clearly closer to that plate at rest (median gap at least
4 mm). Wings, tabard, and mid_chest stay as Beth rigged them. Rest shape
is unchanged because every vertex is still rigid to one bone and every
bone's bind pose is identity.
"""
import json, struct, sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

ROOT = Path("/workspace/www/proto3d/models/beth/equipment/knight_rig")
# mid bone -> (parent plate, child plate). Child may be a set of bones.
LIMB = {
    "mid_upperArm_L": ("shoulder_L", ("upperArm_L",)),
    "mid_upperArm_R": ("shoulder_R", ("upperArm_R",)),
    "mid_foreArm_L": ("upperArm_L", ("foreArm_L",)),
    "mid_foreArm_R": ("upperArm_R", ("foreArm_R",)),
    "mid_hand_L": ("foreArm_L", ("hand_L", "fingers_L", "thumb1_L", "thumb2_L", "thumb3_L",
                                 "index1_L", "index2_L", "index3_L", "middle1_L", "middle2_L", "middle3_L",
                                 "ring1_L", "ring2_L", "ring3_L", "pinky1_L", "pinky2_L", "pinky3_L")),
    "mid_hand_R": ("foreArm_R", ("hand_R", "fingers_R", "thumb1_R", "thumb2_R", "thumb3_R",
                                 "index1_R", "index2_R", "index3_R", "middle1_R", "middle2_R", "middle3_R",
                                 "ring1_R", "ring2_R", "ring3_R", "pinky1_R", "pinky2_R", "pinky3_R")),
    "mid_shin_L": ("thigh_L", ("shin_L",)),
    "mid_shin_R": ("thigh_R", ("shin_R",)),
    "mid_thigh_L": ("hips", ("thigh_L",)),
    "mid_thigh_R": ("hips", ("thigh_R",)),
    "mid_foot_L": ("shin_L", ("foot_L", "toe_L")),
    "mid_foot_R": ("shin_R", ("foot_R", "toe_R")),
}
MARGIN = 0.004  # metres; closer plate must win by at least this
MIN_ISLAND = 8
# Some plates were never weighted to the anatomical bone (pauldron took the shoulder).
PARENT_FALLBACK = {
    "shoulder_L": ("pauldron_L",),
    "shoulder_R": ("pauldron_R",),
    "hand_L": ("fingers_L",),
    "hand_R": ("fingers_R",),
}


def load_glb(path):
    data = Path(path).read_bytes()
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


def save_glb(path, js, blob):
    # JSON chunk must match the original padding style well enough to stay valid.
    jbytes = json.dumps(js, separators=(",", ":")).encode("utf-8")
    jbytes += b" " * ((4 - len(jbytes) % 4) % 4)
    blob = bytes(blob)
    blob += b"\x00" * ((4 - len(blob) % 4) % 4)
    out = bytearray()
    out += struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(jbytes) + 8 + len(blob))
    out += struct.pack("<II", len(jbytes), 0x4E4F534A)
    out += jbytes
    out += struct.pack("<II", len(blob), 0x004E4942)
    out += blob
    Path(path).write_bytes(out)


COMP = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
NCOMP = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}


def acc(js, blob, i):
    a = js["accessors"][i]
    bv = js["bufferViews"][a["bufferView"]]
    start = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
    count = a["count"]
    nc = NCOMP[a["type"]]
    dt = COMP[a["componentType"]]
    item = np.dtype(dt).itemsize
    stride = bv.get("byteStride", item * nc)
    if stride == item * nc:
        return np.frombuffer(blob, dtype=dt, count=count * nc, offset=start).reshape(count, nc).copy()
    raw = np.empty((count, nc), dtype=dt)
    for k in range(count):
        raw[k] = np.frombuffer(blob, dtype=dt, count=nc, offset=start + k * stride)
    return raw


class UF:
    def __init__(self, n):
        self.p = np.arange(n)

    def find(self, a):
        p = self.p
        while p[a] != a:
            p[a] = p[p[a]]
            a = p[a]
        return a

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[rb] = ra


def main():
    files = sys.argv[1:] or [
        str(ROOT / "knight_male.glb"),
        str(ROOT / "knight_female.glb"),
        str(ROOT / "knight_male_lod1.glb"),
        str(ROOT / "knight_female_lod1.glb"),
    ]
    allr = []
    for f in files:
        rep = reseat_into(f)
        allr.append(rep)
        print(json.dumps({k: rep[k] for k in ("file", "verts_moved", "unique_islands")}, default=str))
    out = ROOT / "reseat_mid_report.json"
    out.write_text(json.dumps(allr, indent=1))
    print("WROTE", out)


def reseat_into(path):
    js, blob = load_glb(path)
    prim = js["meshes"][0]["primitives"][0]
    pos = acc(js, blob, prim["attributes"]["POSITION"])
    pos_hash = int(pos.astype(np.float32).tobytes().__hash__()) if False else None
    before = acc(js, blob, prim["attributes"]["POSITION"]).tobytes()
    j_acc = prim["attributes"]["JOINTS_0"]
    joints = acc(js, blob, j_acc).astype(np.int32)
    weights = acc(js, blob, prim["attributes"]["WEIGHTS_0"])
    tris = acc(js, blob, prim["indices"]).astype(np.int32).reshape(-1, 3)
    names = [js["nodes"][j].get("name") for j in js["skins"][0]["joints"]]
    name_to = {n: i for i, n in enumerate(names)}
    bone = joints[np.arange(len(joints)), weights.argmax(1)].copy()
    uf = UF(len(pos))
    for a, b, c in tris:
        if bone[a] == bone[b]:
            uf.union(int(a), int(b))
        if bone[b] == bone[c]:
            uf.union(int(b), int(c))
        if bone[a] == bone[c]:
            uf.union(int(a), int(c))
    groups = defaultdict(list)
    for i, b in enumerate(bone):
        groups[(uf.find(i), int(b))].append(i)

    def ids_for(bone_names):
        parts = []
        for n in bone_names:
            if n in name_to:
                parts.append(np.where(bone == name_to[n])[0])
        if not parts:
            return np.zeros(0, np.int32)
        return np.concatenate(parts)

    report = {"file": path, "islands": [], "verts_moved": 0}
    moves = {}
    for mid, (par, childs) in LIMB.items():
        if mid not in name_to:
            continue
        bi = name_to[mid]
        islands = [np.array(v, dtype=np.int32) for (r, b), v in groups.items() if b == bi]
        # Prefer the anatomical parent bone. If it has no plate, measure
        # against the helper that actually holds that plate and bind there.
        par_bone = par
        pids = ids_for((par,))
        if len(pids) < 12:
            for fb in PARENT_FALLBACK.get(par, ()):
                trial = ids_for((fb,))
                if len(trial) >= 12:
                    pids = trial
                    par_bone = fb
                    break
        cids = ids_for(childs)
        if len(pids) < 12 or len(cids) < 12:
            report["islands"].append({"mid": mid, "skipped": True, "parent_verts": int(len(pids)), "child_verts": int(len(cids)), "n_islands": len(islands)})
            continue
        pt = cKDTree(np.asarray(pos)[pids].astype(np.float64))
        ct = cKDTree(np.asarray(pos)[cids].astype(np.float64))
        for ids in islands:
            if len(ids) < MIN_ISLAND:
                continue
            step = 1 if len(ids) <= 800 else max(1, len(ids) // 40)
            sub = ids[::step]
            P = np.asarray(pos)[sub].astype(np.float64)
            dp = float(np.median(pt.query(P)[0]))
            dc = float(np.median(ct.query(P)[0]))
            dest = None
            if dp + MARGIN < dc:
                dest = par_bone
            elif dc + MARGIN < dp:
                dest = childs[0]
            if dest is None:
                continue
            dj = name_to[dest]
            for vi in ids.tolist():
                moves[vi] = dj
            report["islands"].append({
                "mid": mid, "n": int(len(ids)), "to": dest,
                "dist_parent_m": round(dp, 4), "dist_child_m": round(dc, 4),
            })
            report["verts_moved"] += int(len(ids))
    a = js["accessors"][j_acc]
    bv = js["bufferViews"][a["bufferView"]]
    start = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
    raw = np.frombuffer(blob, dtype=np.uint8, count=a["count"] * 4, offset=start).reshape(-1, 4)
    w = np.asarray(weights)
    for vi, dj in moves.items():
        slot = int(w[vi].argmax())
        raw[vi, slot] = np.uint8(dj)
    after = acc(js, blob, prim["attributes"]["POSITION"]).tobytes()
    report["position_bytes_unchanged"] = before == after
    nrm = prim["attributes"].get("NORMAL")
    if nrm is not None:
        # touching joints must not have shifted the normal view; compare length only
        report["normal_count"] = int(js["accessors"][nrm]["count"])
    save_glb(path, js, blob)
    # confirm reload
    js2, blob2 = load_glb(path)
    pos2 = acc(js2, blob2, js2["meshes"][0]["primitives"][0]["attributes"]["POSITION"]).tobytes()
    report["reloaded_positions_match"] = pos2 == before
    report["unique_islands"] = len([i for i in report["islands"] if not i.get("skipped")])
    return report


if __name__ == "__main__":
    main()
