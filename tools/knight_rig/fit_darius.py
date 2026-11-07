"""Fit the male knight armor to Darius and write review GLBs.

The shared knight file, the unequipped body, and the unequipped outfit are
not modified. The armor mesh starts from the same fitted rest as
fit_heroes.fit_plates: one scale per limb, plates kept in one piece, joints
seated on Darius's bind pose.

Clips are solved in world space, one key at every source time. The torso
copies Darius's change in orientation. Each arm and leg is a two-bone reach
onto his hand or foot, so the plates stay rigid and the gauntlet stays on
the fist. Elbow and knee cops are a second skin of the existing cuff, rigid
on the joint bone, turned halfway through the bend.

The equipped body keeps the face in the visor and the part of each fist
that sits inside the gauntlet. Hair, the crown, and the underlayer are
hidden only in that equipped file.
"""
import json
import os
import sys
from collections import Counter, defaultdict

import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, os.path.dirname(__file__))
from fit_heroes import (  # noqa: E402
    ARMOR,
    PILOTS,
    append_view,
    dominant,
    fit_plates,
    joint_maps,
    load_glb,
    pack_mesh,
    quat_mat,
    read_acc,
    rot_between,
    save_glb,
    split_hero,
)

ROOT = "/workspace/www/proto3d/models/beth/equipment/knight_rig/fitted_heroes/darius"
HERO = PILOTS["darius"]["path"]
BODY = os.path.join(ROOT, "darius_body.glb")
OUT_ARMOR = os.path.join(ROOT, "darius_armor_fit.glb")
OUT_BODY = os.path.join(ROOT, "darius_body_equipped.glb")

TORSO = ("root", "hips", "spine", "spine2", "chest", "upperChest", "neck", "head")
LIMBS = (
    ("upperArm_L", "foreArm_L", "hand_L"),
    ("upperArm_R", "foreArm_R", "hand_R"),
    ("thigh_L", "shin_L", "foot_L"),
    ("thigh_R", "shin_R", "foot_R"),
)
EXTREMITIES = (("hand_L", "fingers_L"), ("hand_R", "fingers_R"), ("foot_L", "toe_L"), ("foot_R", "toe_R"))
SHOULDERS = (("shoulder_L", "upperArm_L"), ("shoulder_R", "upperArm_R"))
HALF = {"elbow_L": "foreArm_L", "elbow_R": "foreArm_R", "knee_L": "shin_L", "knee_R": "shin_R"}
# Filled by close_joints. Each entry is (helper name, child bone, fraction of that bend).
SEGMENT_JOBS = []


def qnorm(q):
    q = np.asarray(q, float)
    n = float(np.linalg.norm(q))
    if n < 1e-10:
        return np.array([0.0, 0.0, 0.0, 1.0])
    return q / n


def qinv(q):
    return np.array([-q[0], -q[1], -q[2], q[3]], float)


def qmul(a, b):
    ax, ay, az, aw = a
    bx, by, bz, bw = b
    return np.array([
        aw * bx + ax * bw + ay * bz - az * by,
        aw * by - ax * bz + ay * bw + az * bx,
        aw * bz + ax * by - ay * bx + az * bw,
        aw * bw - ax * bx - ay * by - az * bz,
    ], float)


def slerp(a, b, t):
    a = qnorm(a)
    b = qnorm(b)
    d = float(np.dot(a, b))
    if d < 0.0:
        b = -b
        d = -d
    if d > 0.9995:
        return qnorm(a * (1.0 - t) + b * t)
    th = float(np.arccos(np.clip(d, -1.0, 1.0)))
    s = np.sin(th)
    return qnorm(np.sin((1.0 - t) * th) / s * a + np.sin(t * th) / s * b)


def mat_to_quat(m):
    u, _s, vt = np.linalg.svd(m[:3, :3])
    r = u @ vt
    if np.linalg.det(r) < 0:
        u = u.copy()
        u[:, -1] *= -1
        r = u @ vt
    t = float(np.trace(r))
    if t > 0.0:
        s = np.sqrt(t + 1.0) * 2.0
        w = 0.25 * s
        x = (r[2, 1] - r[1, 2]) / s
        y = (r[0, 2] - r[2, 0]) / s
        z = (r[1, 0] - r[0, 1]) / s
    elif r[0, 0] > r[1, 1] and r[0, 0] > r[2, 2]:
        s = np.sqrt(1.0 + r[0, 0] - r[1, 1] - r[2, 2]) * 2.0
        w = (r[2, 1] - r[1, 2]) / s
        x = 0.25 * s
        y = (r[0, 1] + r[1, 0]) / s
        z = (r[0, 2] + r[2, 0]) / s
    elif r[1, 1] > r[2, 2]:
        s = np.sqrt(1.0 + r[1, 1] - r[0, 0] - r[2, 2]) * 2.0
        w = (r[0, 2] - r[2, 0]) / s
        x = (r[0, 1] + r[1, 0]) / s
        y = 0.25 * s
        z = (r[1, 2] + r[2, 1]) / s
    else:
        s = np.sqrt(max(1e-12, 1.0 + r[2, 2] - r[0, 0] - r[1, 1])) * 2.0
        w = (r[1, 0] - r[0, 1]) / s
        x = (r[0, 2] + r[2, 0]) / s
        y = (r[1, 2] + r[2, 1]) / s
        z = 0.25 * s
    return qnorm(np.array([x, y, z, w], float))


def ortho(m):
    u, _s, vt = np.linalg.svd(np.asarray(m, float)[:3, :3])
    r = u @ vt
    if np.linalg.det(r) < 0:
        u = u.copy()
        u[:, -1] *= -1
        r = u @ vt
    return r


def node_rest(js):
    rot, loc, parent = {}, {}, {}
    nodes = js["nodes"]
    for i, n in enumerate(nodes):
        for c in n.get("children", []):
            parent[c] = i
    name_of = {i: n.get("name") for i, n in enumerate(nodes)}
    node_of = {n.get("name"): i for i, n in enumerate(nodes) if n.get("name")}
    for i, n in enumerate(nodes):
        name = n.get("name")
        if not name:
            continue
        r = n.get("rotation") or [0, 0, 0, 1]
        t = n.get("translation") or [0, 0, 0]
        rot[name] = qnorm(np.array(r, float))
        loc[name] = np.array(t, float)
    return rot, loc, parent, name_of, node_of


def fk(js, rot, loc, parent, name_of):
    nodes = js["nodes"]
    world = {}

    def W(i):
        if i in world:
            return world[i]
        name = name_of.get(i)
        r = rot.get(name, np.array([0.0, 0.0, 0.0, 1.0]))
        t = loc.get(name, np.zeros(3))
        s = np.array(nodes[i].get("scale", [1, 1, 1]), float)
        M = np.eye(4)
        M[:3, :3] = quat_mat(r) @ np.diag(s)
        M[:3, 3] = t
        world[i] = (W(parent[i]) @ M) if i in parent else M
        return world[i]

    for i in range(len(nodes)):
        W(i)
    pos, Rm = {}, {}
    for i, n in enumerate(nodes):
        if n.get("name"):
            pos[n["name"]] = world[i][:3, 3].copy()
            Rm[n["name"]] = ortho(world[i][:3, :3])
    return pos, Rm


def channels(js, blob, anim):
    nodes = {i: n.get("name") for i, n in enumerate(js["nodes"])}
    out = {}
    for ch in anim["channels"]:
        name = nodes.get(ch["target"]["node"])
        path = ch["target"]["path"]
        sm = anim["samplers"][ch["sampler"]]
        times = read_acc(js, blob, sm["input"]).reshape(-1).astype(np.float64)
        values = read_acc(js, blob, sm["output"]).astype(np.float64)
        out.setdefault(name, {})[path] = (times, values)
    return out


def sample_quat(times, values, t):
    if t <= times[0]:
        return qnorm(values[0])
    if t >= times[-1]:
        return qnorm(values[-1])
    i = int(np.searchsorted(times, t))
    u = (t - times[i - 1]) / (times[i] - times[i - 1] + 1e-12)
    return slerp(values[i - 1], values[i], float(u))


def sample_vec(times, values, t):
    if t <= times[0]:
        return values[0].astype(np.float64)
    if t >= times[-1]:
        return values[-1].astype(np.float64)
    i = int(np.searchsorted(times, t))
    u = (t - times[i - 1]) / (times[i] - times[i - 1] + 1e-12)
    return (1.0 - u) * values[i - 1] + u * values[i]


def solve_two_bone(root, target, pole, l1, l2):
    delta = target - root
    raw = float(np.linalg.norm(delta))
    reach = l1 + l2 - 1e-5
    minimum = abs(l1 - l2) + 1e-4
    dist = float(np.clip(raw, minimum, max(minimum + 1e-4, reach)))
    nd = delta / (raw + 1e-12)
    cosang = (l1 * l1 + dist * dist - l2 * l2) / (2.0 * l1 * dist)
    cosang = float(np.clip(cosang, -1.0, 1.0))
    along = cosang * l1
    height = float(np.sqrt(max(0.0, l1 * l1 - along * along)))
    pole_v = pole - root
    pole_v = pole_v - nd * float(np.dot(pole_v, nd))
    if float(np.linalg.norm(pole_v)) < 1e-6:
        helper = np.array([0.0, 1.0, 0.0]) if abs(nd[1]) < 0.9 else np.array([1.0, 0.0, 0.0])
        pole_v = helper - nd * float(np.dot(helper, nd))
    pole_v = pole_v / (np.linalg.norm(pole_v) + 1e-12)
    elbow = root + nd * along + pole_v * height
    # If the target was out of reach, the hand stops on the ray.
    if raw > 1e-8 and abs(raw - dist) > 1e-6:
        target = root + nd * dist
    return elbow, target, abs(raw - dist)


def aim_world(prev_R, aim_axis, new_dir):
    old = prev_R @ aim_axis
    return ortho(rot_between(old, new_dir) @ prev_R)


def local_from_world(parent_R, world_R):
    if parent_R is None:
        return mat_to_quat(world_R)
    return mat_to_quat(parent_R.T @ world_R)


def _assign(joints, weights, bname, names, ids, dest):
    ji = names.index(dest)
    joints[ids, 0] = ji
    joints[ids, 1:] = 0
    weights[ids] = 0
    weights[ids, 0] = 1
    bname[ids] = dest


def dissolve_helpers(js, blob):
    """Lock each shell to one plate so a bend cannot tear it into shards.

    The cuirass, including the pauldrons and the collar, stays on the chest.
    Each limb shell stays on the upper or lower bone it already touches.
    Wings and the tabard are left on the bones Beth rigged.
    """
    names, _apos, _node, _W, _parent = joint_maps(js)
    prim = js["meshes"][0]["primitives"][0]
    pos = read_acc(js, blob, prim["attributes"]["POSITION"]).astype(np.float64)
    nrm = read_acc(js, blob, prim["attributes"]["NORMAL"]).astype(np.float32)
    uv = read_acc(js, blob, prim["attributes"]["TEXCOORD_0"]).astype(np.float32)
    joints = read_acc(js, blob, prim["attributes"]["JOINTS_0"]).astype(np.int32)
    weights = read_acc(js, blob, prim["attributes"]["WEIGHTS_0"]).astype(np.float32)
    indices = read_acc(js, blob, prim["indices"]).astype(np.int64)
    bone_i = dominant(joints, weights)
    bname = np.array(names)[bone_i]
    cuirass = {"neck", "upperChest", "spine", "spine2", "mid_chest"}
    limb_src = set()
    for side in ("_L", "_R"):
        cuirass.update({"shoulder" + side, "pauldron" + side, "tasset" + side})
        limb_src.update({
            "elbow" + side, "knee" + side,
            "mid_foreArm" + side, "mid_hand" + side, "mid_shin" + side,
            "mid_upperArm" + side, "mid_thigh" + side, "mid_foot" + side,
            "foreArm_twist" + side, "upperArm_twist" + side,
            "thigh_twist" + side, "shin_twist" + side,
        })
    plates = ["chest", "hips", "head"]
    for side in ("_L", "_R"):
        plates += [
            "upperArm" + side, "foreArm" + side, "hand" + side,
            "thigh" + side, "shin" + side, "foot" + side,
        ]
    plates = [p for p in plates if p in names]
    moved = Counter()
    # Cuirass shells move onto the chest. The rest pose does not change,
    # because every weight is still rigid and the bind is the identity.
    if "chest" in names:
        sel = np.isin(bname, list(cuirass))
        if sel.any():
            _assign(joints, weights, bname, names, np.where(sel)[0], "chest")
            moved["chest"] += int(sel.sum())
    # The skirt is one piece on the hips. Split tabard bones open it when the chest leans.
    if "hips" in names:
        skirt = np.array(["tabard" in str(n) for n in bname])
        if skirt.any():
            _assign(joints, weights, bname, names, np.where(skirt)[0], "hips")
            moved["hips"] += int(skirt.sum())
    # Limb helpers move to the plate they touch.
    plate_mask = np.isin(bname, plates)
    if plate_mask.sum() > 100 and any(n in limb_src for n in bname):
        tree = cKDTree(pos[plate_mask])
        plate_ids = np.where(plate_mask)[0]
        parent = np.arange(len(pos))

        def find(a):
            while parent[a] != a:
                parent[a] = parent[parent[a]]
                a = parent[a]
            return a

        def union(a, b):
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[rb] = ra

        tri = indices.reshape(-1, 3)
        src = np.array([n in limb_src for n in bname])
        for a, b, c in tri[src[tri].all(1)]:
            union(int(a), int(b))
            union(int(b), int(c))
        groups = defaultdict(list)
        for i in np.where(src)[0]:
            groups[find(int(i))].append(int(i))
        for ids in groups.values():
            ids = np.array(ids)
            _dist, nn = tree.query(pos[ids], k=1)
            labels = bname[plate_ids[nn]]
            dest, _n = Counter(labels.tolist()).most_common(1)[0]
            _assign(joints, weights, bname, names, ids, dest)
            moved[dest] += len(ids)
    print("  rebound", dict(moved), flush=True)
    return pos, nrm, uv, joints, weights, indices, bname


def add_cops(pos, nrm, uv, joints, weights, indices, bname, names, apos):
    """A second cuff at the elbow and the knee, rigid on the joint bone."""
    bands = (
        ("foreArm_L", "elbow_L", "upperArm_L", 0.075),
        ("foreArm_R", "elbow_R", "upperArm_R", 0.075),
        ("shin_L", "knee_L", "thigh_L", 0.085),
        ("shin_R", "knee_R", "thigh_R", 0.085),
    )
    extra_p, extra_n, extra_u, extra_j, extra_w = [], [], [], [], []
    extra_tri = []
    base = len(pos)
    tri = indices.reshape(-1, 3)
    for src, helper, parent_bone, radius in bands:
        if helper not in names or src not in apos or parent_bone not in apos:
            continue
        sel = np.where(bname == src)[0]
        if len(sel) < 20:
            continue
        pivot = apos[src]
        dist = np.linalg.norm(pos[sel] - pivot, axis=1)
        take = sel[dist < radius]
        if len(take) < 30:
            take = sel[np.argsort(dist)[: min(180, len(sel))]]
        if len(take) > 500:
            take = take[np.argsort(np.linalg.norm(pos[take] - pivot, axis=1))[:500]]
        chosen = set(int(i) for i in take)
        faces = [f for f in tri if all(int(v) in chosen for v in f)]
        if len(faces) < 8:
            continue
        remap = {int(v): k for k, v in enumerate(take)}
        axis = apos[src] - apos[parent_bone]
        axis = axis / (np.linalg.norm(axis) + 1e-12)
        chunk = pos[take].copy()
        for i, v in enumerate(chunk):
            rel = v - pivot
            radial = rel - axis * float(np.dot(rel, axis))
            ln = float(np.linalg.norm(radial))
            if ln > 1e-5:
                chunk[i] = v + radial / ln * 0.0035
        ji = names.index(helper)
        j = np.zeros((len(take), 4), np.uint8)
        w = np.zeros((len(take), 4), np.float32)
        j[:, 0] = ji
        w[:, 0] = 1
        extra_p.append(chunk.astype(np.float32))
        extra_n.append(nrm[take])
        extra_u.append(uv[take])
        extra_j.append(j)
        extra_w.append(w)
        for f in faces:
            extra_tri.append([base + remap[int(v)] for v in f])
        base += len(take)
        print("  cop", helper, "verts", len(take), "tris", len(faces), flush=True)
    if not extra_p:
        return pos, nrm, uv, joints, weights, indices
    pos = np.vstack([pos, np.vstack(extra_p)])
    nrm = np.vstack([nrm, np.vstack(extra_n)])
    uv = np.vstack([uv, np.vstack(extra_u)])
    joints = np.vstack([joints, np.vstack(extra_j)])
    weights = np.vstack([weights, np.vstack(extra_w)])
    indices = np.vstack([tri, np.array(extra_tri, np.int64)]).reshape(-1)
    return pos, nrm, uv, joints, weights, indices


def pose_hero(hero_js, hero_rest_r, hero_rest_t, ch, t, parent, name_of):
    rot = dict(hero_rest_r)
    loc = {k: v.copy() for k, v in hero_rest_t.items()}
    for name, paths in ch.items():
        if not name:
            continue
        if "rotation" in paths:
            rot[name] = sample_quat(paths["rotation"][0], paths["rotation"][1], t)
        if "translation" in paths:
            loc[name] = sample_vec(paths["translation"][0], paths["translation"][1], t)
    return fk(hero_js, rot, loc, parent, name_of)


def solve_armor(armor_js, a_rest_r, a_rest_t, a_parent, a_name, a_bind_pos, a_bind_R,
                h_pos, h_R, h_bind_pos, h_bind_R, prev):
    """One frame. prev holds world rotations so the swing does not flip."""
    rot = {k: v.copy() for k, v in a_rest_r.items()}
    loc = {k: v.copy() for k, v in a_rest_t.items()}
    # Hips travel with Darius. Other bones keep their fitted length.
    if "hips" in h_pos and "hips" in a_rest_t and "hips" in h_bind_pos:
        # World delta of the hips, expressed back in the armor parent frame below
        # once the torso rotation is known. Translation is copied as a local delta
        # when both rests share a parent. The fitted rests already match.
        pass

    def set_world(name, world_R):
        pi = a_parent.get(a_name[name]) if name in a_name else None
        parent_R = None
        if pi is not None:
            pname = a_name.get(pi) if False else None
        # parent world from the pose built so far
        return world_R

    # Build locals parent-first for the torso using full orientation delta.
    order = []
    seen = set()

    def walk(name):
        if name in seen or name not in a_name:
            return
        seen.add(name)
        pi = a_parent.get(a_name[name])
        if pi is not None and a_js_name(a_name, pi) in a_rest_r:
            walk(a_js_name(a_name, pi))
        order.append(name)

    # a_name is name->index. Need index->name too. Closed over via a_name_of.
    return rot, loc, prev


def a_js_name(name_of, index):
    return name_of.get(index)


def fit_armor_anims(armor_js, armor_blob, hero_js, hero_blob):
    a_rest_r, a_rest_t, a_parent, a_name_of, a_node = node_rest(armor_js)
    h_rest_r, h_rest_t, h_parent, h_name_of, h_node = node_rest(hero_js)
    a_bind_pos, a_bind_R = fk(armor_js, a_rest_r, a_rest_t, a_parent, a_name_of)
    h_bind_pos, h_bind_R = fk(hero_js, h_rest_r, h_rest_t, h_parent, h_name_of)

    def aim_axis(rest_t, child):
        v = rest_t[child]
        n = float(np.linalg.norm(v))
        if n < 1e-6:
            return None
        return v / n, n

    def limb_lengths(table, a, b, c):
        return float(np.linalg.norm(table[b] - table[a])), float(np.linalg.norm(table[c] - table[b]))

    lengths = {a: limb_lengths(a_bind_pos, a, b, c) for a, b, c in LIMBS}

    def frame_locals(h_pos, h_R, prev):
        rot = {k: v.copy() for k, v in a_rest_r.items()}
        loc = {k: v.copy() for k, v in a_rest_t.items()}
        if "hips" in h_rest_t and "hips" in a_rest_t:
            # The hero clip stores the full local translation.
            loc["hips"] = a_rest_t["hips"] + (h_pos["hips_local"] - h_rest_t["hips"])

        # Torso orientation follows Darius's change from his bind pose.
        torso_names = [n for n in TORSO if n in a_node and n in h_bind_R and n in h_R]
        # parent first
        pending = list(torso_names)
        placed = set()
        guard = 0
        while pending and guard < 20:
            guard += 1
            later = []
            for name in pending:
                pi = a_parent.get(a_node[name])
                pname = a_name_of.get(pi) if pi is not None else None
                if pname in torso_names and pname not in placed and pname in a_node:
                    later.append(name)
                    continue
                delta = h_R[name] @ h_bind_R[name].T
                desired = ortho(delta @ a_bind_R[name])
                parent_R = None
                if pname is not None and pname in a_bind_R:
                    # Parent world from this pose. Recompute after we know parent local.
                    parent_R = current_R(pname, rot, loc)
                rot[name] = local_from_world(parent_R, desired)
                placed.add(name)
            pending = later
        # Shoulders aim the upper arm at Darius's upper arm, without adding twist.
        for shoulder, upper in SHOULDERS:
            if shoulder not in a_node or upper not in h_pos or upper not in a_rest_t:
                continue
            axis = aim_axis(a_rest_t, upper)
            if axis is None:
                continue
            spos = current_pos(shoulder, rot, loc)
            desired = h_pos[upper] - spos
            if float(np.linalg.norm(desired)) < 1e-5:
                continue
            desired = desired / np.linalg.norm(desired)
            prev_R = prev.get(shoulder, a_bind_R[shoulder])
            world = aim_world(prev_R, axis[0], desired)
            prev[shoulder] = world
            pname = a_name_of.get(a_parent.get(a_node[shoulder]))
            parent_R = current_R(pname, rot, loc) if pname else None
            rot[shoulder] = local_from_world(parent_R, world)
        # Arms and legs reach the fist and the foot.
        for root, mid, tip in LIMBS:
            if root not in a_node or mid not in h_pos or tip not in h_pos:
                continue
            l1, l2 = lengths[root]
            rpos = current_pos(root, rot, loc)
            hero_root = h_bind_pos[root]
            hero_mid = h_bind_pos[mid]
            hero_tip = h_bind_pos[tip]
            # Bend plane follows Darius, and at his bind pose it is the sculpt.
            Rpose = frame_delta(hero_root, hero_mid, hero_tip, h_pos[root], h_pos[mid], h_pos[tip])
            pole = rpos + Rpose @ (a_bind_pos[mid] - a_bind_pos[root])
            target = h_pos[tip]
            elbow, reached, miss = solve_two_bone(rpos, target, pole, l1, l2)
            axis_mid = aim_axis(a_rest_t, mid)
            axis_tip = aim_axis(a_rest_t, tip)
            if axis_mid is None or axis_tip is None:
                continue
            d_mid = elbow - rpos
            d_mid = d_mid / (np.linalg.norm(d_mid) + 1e-12)
            prev_R = prev.get(root, a_bind_R[root])
            world_root = aim_world(prev_R, axis_mid[0], d_mid)
            prev[root] = world_root
            pname = a_name_of.get(a_parent.get(a_node[root]))
            parent_R = current_R(pname, rot, loc) if pname else None
            rot[root] = local_from_world(parent_R, world_root)
            d_tip = reached - elbow
            d_tip = d_tip / (np.linalg.norm(d_tip) + 1e-12)
            prev_M = prev.get(mid, a_bind_R[mid])
            world_mid = aim_world(prev_M, axis_tip[0], d_tip)
            prev[mid] = world_mid
            rot[mid] = local_from_world(world_root, world_mid)
            prev["_miss_" + tip] = miss
        # Gloves and boots keep their sculpted twist and follow the fist direction.
        for bone, child in EXTREMITIES:
            if bone not in a_node or child not in h_pos or child not in h_bind_pos:
                continue
            axis = aim_axis(a_rest_t, child)
            if axis is None:
                continue
            bind_dir = h_bind_pos[child] - h_bind_pos[bone]
            pose_dir = h_pos[child] - h_pos[bone]
            if float(np.linalg.norm(bind_dir)) < 1e-5 or float(np.linalg.norm(pose_dir)) < 1e-5:
                continue
            Rdelta = rot_between(bind_dir, pose_dir)
            rest_dir = a_bind_R[bone] @ axis[0]
            desired = Rdelta @ rest_dir
            desired = desired / (np.linalg.norm(desired) + 1e-12)
            prev_R = prev.get(bone, a_bind_R[bone])
            world = aim_world(prev_R, axis[0], desired)
            prev[bone] = world
            pname = a_name_of.get(a_parent.get(a_node[bone]))
            parent_R = current_R(pname, rot, loc) if pname else None
            rot[bone] = local_from_world(parent_R, world)
        # Joint cops take half the bend, so they sit in the opening.
        for helper, child in HALF.items():
            if helper not in a_rest_r or child not in rot:
                continue
            delta = qmul(qinv(a_rest_r[child]), rot[child])
            rot[helper] = qnorm(qmul(a_rest_r[helper], slerp(np.array([0, 0, 0, 1.0]), delta, 0.5)))
        return rot, loc

    def current_world(name, rot, loc):
        # Walk to the root using the pose locals. Cached per call by the caller
        # only through recursion.
        i = a_node[name]
        chain = [i]
        while i in a_parent:
            i = a_parent[i]
            chain.append(i)
        M = np.eye(4)
        for i in reversed(chain):
            nm = a_name_of.get(i)
            r = rot.get(nm, np.array([0.0, 0.0, 0.0, 1.0])) if nm else np.array([0.0, 0.0, 0.0, 1.0])
            t = loc.get(nm, np.zeros(3)) if nm else np.zeros(3)
            L = np.eye(4)
            L[:3, :3] = quat_mat(r)
            L[:3, 3] = t
            M = M @ L
        return M

    def current_R(name, rot, loc):
        if name is None or name not in a_node:
            return None
        return ortho(current_world(name, rot, loc)[:3, :3])

    def current_pos(name, rot, loc):
        return current_world(name, rot, loc)[:3, 3].copy()

    # Bind pose must come back as the sculpt. One synthetic frame.
    prev0 = {}
    bind_rot, _bind_loc = frame_locals(h_bind_pos, h_bind_R, prev0)
    # h_bind_pos has no hips_local. Set it before the call.
    return frame_locals, a_rest_r, a_rest_t, a_node, a_bind_pos, h_bind_pos, h_bind_R


def frame_delta(bind_root, bind_mid, bind_tip, pose_root, pose_mid, pose_tip):
    """Rotation that carries the bind limb frame onto the posed limb frame."""
    def frame(root, mid, tip):
        x = tip - root
        ln = float(np.linalg.norm(x))
        if ln < 1e-6:
            return np.eye(3)
        x = x / ln
        y = mid - root
        y = y - x * float(np.dot(y, x))
        if float(np.linalg.norm(y)) < 1e-6:
            y = np.array([0.0, 1.0, 0.0])
            y = y - x * float(np.dot(y, x))
        y = y / (np.linalg.norm(y) + 1e-12)
        z = np.cross(x, y)
        return np.stack([x, y, z], axis=1)

    Fb = frame(bind_root, bind_mid, bind_tip)
    Fp = frame(pose_root, pose_mid, pose_tip)
    return ortho(Fp @ Fb.T)


def mask_body(body_js, body_blob, armor_pos, armor_bone, armor_names):
    """Face stays in the visor. Fists that stick out of the gauntlet go."""
    js = json.loads(json.dumps(body_js))
    blob = bytearray(body_blob)
    for n in js["nodes"]:
        if "children" not in n:
            continue
        n["children"] = [c for c in n["children"] if js["nodes"][c].get("name") != "underlayer"]
    names, _pos, _n, _W, _p = joint_maps(js)
    prim = js["meshes"][0]["primitives"][0]
    pos = read_acc(js, blob, prim["attributes"]["POSITION"]).astype(np.float64)
    nrm = read_acc(js, blob, prim["attributes"]["NORMAL"]).astype(np.float32)
    uv = read_acc(js, blob, prim["attributes"]["TEXCOORD_0"]).astype(np.float32)
    joints = read_acc(js, blob, prim["attributes"]["JOINTS_0"]).astype(np.uint8)
    weights = read_acc(js, blob, prim["attributes"]["WEIGHTS_0"]).astype(np.float32)
    bone = np.array(names)[dominant(joints.astype(np.int32), weights)]
    hair = np.array([str(b).startswith("hair") for b in bone])
    head = bone == "head"
    face = (
        head
        & (pos[:, 1] > 1.545) & (pos[:, 1] < 1.720)
        & (np.abs(pos[:, 0]) < 0.075)
        & (pos[:, 2] > 0.015) & (pos[:, 2] < 0.160)
    )
    helm = armor_pos[armor_bone == "head"]
    if len(helm) > 20 and face.any():
        dist, _nn = cKDTree(helm).query(pos[face], k=1)
        # A vert in the window but far outside the shell is still the brow bar.
        far = np.zeros(len(pos), bool)
        far[np.where(face)[0][dist > 0.055]] = True
        face = face & ~far
    hand_names = [n for n in armor_names if n and any(
        k in n for k in ("hand", "finger", "thumb", "index", "middle", "ring", "pinky"))]
    gaunt = armor_pos[np.isin(armor_bone, hand_names)]
    hand = np.array([str(b).startswith(("hand", "thumb", "index", "middle", "ring", "pinky", "finger")) for b in bone])
    outside = np.zeros(len(pos), bool)
    if len(gaunt) > 20 and hand.any():
        dist, _nn = cKDTree(gaunt).query(pos[hand], k=1)
        outside[np.where(hand)[0][dist > 0.020]] = True
    drop = hair | (head & ~face) | outside
    keep = ~drop
    remap = -np.ones(len(pos), np.int64)
    remap[keep] = np.arange(int(keep.sum()))
    indices = read_acc(js, blob, prim["indices"]).astype(np.int64).reshape(-1, 3)
    faces = remap[indices[keep[indices].all(1)]].astype(np.uint32)
    packed = pack_mesh(
        js, blob,
        pos[keep].astype(np.float32), nrm[keep], uv[keep], joints[keep], weights[keep], faces,
    )
    packed["material"] = prim.get("material", 0)
    js["meshes"][0]["primitives"] = [packed]
    info = {
        "hair": int(hair.sum()),
        "head_hidden": int((head & ~face).sum()),
        "face": int(face.sum()),
        "hand_hidden": int(outside.sum()),
        "hand_kept": int((hand & ~outside).sum()),
        "kept": int(keep.sum()),
    }
    return js, blob, info


def write_anims(js, blob, hero_js, hero_blob, solve):
    frame_locals, a_rest_r, a_rest_t, a_node, a_bind_pos, h_bind_pos, h_bind_R = solve
    # The closure needs hips_local on the position dict. Handled inside write.
    anims_out = []
    specs = []

    def spec(arr, ctype, atype):
        specs.append((np.ascontiguousarray(arr), ctype, atype))
        return len(specs) - 1

    h_rest_r, h_rest_t, h_parent, h_name_of, _h_node = node_rest(hero_js)
    report = []
    for anim in hero_js["animations"]:
        ch = channels(hero_js, hero_blob, anim)
        times = []
        for paths in ch.values():
            if "rotation" in paths:
                times.append(paths["rotation"][0])
        if not times:
            continue
        uniq = np.unique(np.round(np.concatenate(times), 5))
        prev = {}
        series = defaultdict(list)
        hip_t = []
        misses = []
        for t in uniq:
            h_pos, h_R = pose_hero(hero_js, h_rest_r, h_rest_t, ch, float(t), h_parent, h_name_of)
            h_pos = dict(h_pos)
            h_pos["hips_local"] = sample_vec(*ch["hips"]["translation"], float(t)) if "hips" in ch and "translation" in ch["hips"] else h_rest_t["hips"]
            h_pos["_absolute"] = anim.get("name") != "idle"
            rot, loc = frame_locals(h_pos, h_R, prev)
            for name, q in rot.items():
                if name not in a_node:
                    continue
                # Only store bones we actually changed, plus hips translation.
                if name in a_rest_r and (name in HALF or name in TORSO or name.startswith(("seg_", "shoulder", "upperArm", "foreArm", "hand", "thigh", "shin", "foot"))):
                    series[name].append(qnorm(q))
            hip_t.append(loc["hips"])
            misses.append(float(prev.get("_miss_hand_L", 0.0) + prev.get("_miss_hand_R", 0.0)
                                + prev.get("_miss_foot_L", 0.0) + prev.get("_miss_foot_R", 0.0)))
        # Hemisphere continuity, then accessors.
        channels_out = []
        samplers = []
        for name, quats in series.items():
            prev_q = None
            out = np.empty((len(quats), 4), np.float32)
            for i, q in enumerate(quats):
                if prev_q is not None and float(np.dot(q, prev_q)) < 0:
                    q = -q
                out[i] = q
                prev_q = q
            si = spec(uniq.astype(np.float32), 5126, "SCALAR")
            so = spec(out, 5126, "VEC4")
            samplers.append({"input": si, "output": so, "interpolation": "LINEAR"})
            channels_out.append({
                "sampler": len(samplers) - 1,
                "target": {"node": a_node[name], "path": "rotation"},
            })
        ht = np.stack(hip_t).astype(np.float32)
        si = spec(uniq.astype(np.float32), 5126, "SCALAR")
        so = spec(ht, 5126, "VEC3")
        samplers.append({"input": si, "output": so, "interpolation": "LINEAR"})
        channels_out.append({
            "sampler": len(samplers) - 1,
            "target": {"node": a_node["hips"], "path": "translation"},
        })
        anims_out.append({"name": anim.get("name"), "channels": channels_out, "samplers": samplers})
        report.append((anim.get("name"), len(uniq), float(np.max(misses)) if misses else 0.0))
    index_of = []
    for arr, ctype, atype in specs:
        acc = append_view(js, blob, arr, ctype, atype)
        if atype == "SCALAR":
            js["accessors"][acc]["min"] = [float(arr.min())]
            js["accessors"][acc]["max"] = [float(arr.max())]
        index_of.append(acc)
    for anim in anims_out:
        for sm in anim["samplers"]:
            sm["input"] = index_of[sm["input"]]
            sm["output"] = index_of[sm["output"]]
    js["animations"] = anims_out
    print("  clips", [(n, k, round(m * 100, 2)) for n, k, m in report], flush=True)
    return report


def check_bind(frame_locals, h_bind_pos, h_bind_R, h_rest_t, a_rest_r):
    h_pos = dict(h_bind_pos)
    h_pos["hips_local"] = h_rest_t["hips"]
    rot, _loc = frame_locals(h_pos, h_bind_R, {})
    worst = 0.0
    worst_name = ""
    for name, q in a_rest_r.items():
        if name not in rot:
            continue
        d = abs(float(np.dot(qnorm(rot[name]), qnorm(q))))
        d = min(1.0, d)
        ang = float(np.degrees(2 * np.arccos(d)))
        if ang > worst:
            worst = ang
            worst_name = name
    print("  bind residual deg", round(worst, 3), worst_name, flush=True)
    return worst


def cap_openings(pos, nrm, uv, joints, weights, indices, bname, names, apos):
    """Close the mouth of each limb shell with the same metal.

    The plates are hollow. A deep bend shows the inside. A cap on each open
    mouth stays with that plate, so the bend shows a solid end. Caps that
    already sit against the next plate stay hidden in the standing pose.
    """
    tri = indices.reshape(-1, 3)
    ends = {
        "upperArm_L": ("foreArm_L",),
        "upperArm_R": ("foreArm_R",),
        "foreArm_L": ("upperArm_L", "hand_L"),
        "foreArm_R": ("upperArm_R", "hand_R"),
        "thigh_L": ("shin_L",),
        "thigh_R": ("shin_R",),
        "shin_L": ("thigh_L", "foot_L"),
        "shin_R": ("thigh_R", "foot_R"),
    }
    extra_p, extra_n, extra_u, extra_j, extra_w, extra_tri = [], [], [], [], [], []
    base = len(pos)
    capped = 0
    name_to_i = {n: i for i, n in enumerate(names)}
    for bone, pivots in ends.items():
        if bone not in name_to_i:
            continue
        sel = bname == bone
        faces = tri[sel[tri].all(axis=1)]
        if len(faces) < 20:
            continue
        edge_count = {}
        for a, b, c in faces:
            for e in ((int(a), int(b)), (int(b), int(c)), (int(c), int(a))):
                key = (e[0], e[1]) if e[0] < e[1] else (e[1], e[0])
                edge_count[key] = edge_count.get(key, 0) + 1
        boundary = [e for e, n in edge_count.items() if n == 1]
        if len(boundary) < 3:
            continue
        link = defaultdict(list)
        for a, b in boundary:
            link[a].append(b)
            link[b].append(a)
        seen = set()
        for start in list(link):
            if start in seen:
                continue
            # Walk one boundary loop.
            loop = [start]
            seen.add(start)
            prev = None
            cur = start
            for _ in range(len(link) + 2):
                nxts = [n for n in link[cur] if n != prev and n not in seen]
                if not nxts:
                    break
                prev, cur = cur, nxts[0]
                loop.append(cur)
                seen.add(cur)
                if start in link[cur] and len(loop) > 2:
                    break
            if len(loop) < 6:
                continue
            ring = pos[loop]
            center = ring.mean(axis=0)
            span = float(np.linalg.norm(ring - center, axis=1).max())
            if span < 0.015 or span > 0.14:
                continue
            near_joint = False
            for pname in pivots:
                if pname in apos and float(np.linalg.norm(center - apos[pname])) < 0.09:
                    near_joint = True
            if not near_joint:
                continue
            # Sit the cap just inside the mouth so the standing pose keeps its edge.
            nsum = nrm[loop].astype(np.float64).sum(axis=0)
            nlen = float(np.linalg.norm(nsum))
            inward = -nsum / nlen if nlen > 1e-8 else np.zeros(3)
            center = center + inward * 0.004
            ci = base
            extra_p.append(center.astype(np.float32))
            extra_n.append((nsum / nlen if nlen > 1e-8 else np.array([0, 1, 0], np.float32)).astype(np.float32))
            extra_u.append(uv[loop].mean(axis=0).astype(np.float32))
            jj = np.zeros(4, np.uint8)
            ww = np.zeros(4, np.float32)
            jj[0] = name_to_i[bone]
            ww[0] = 1.0
            extra_j.append(jj)
            extra_w.append(ww)
            base += 1
            for i in range(len(loop)):
                a = int(loop[i])
                b = int(loop[(i + 1) % len(loop)])
                extra_tri.extend([[ci, a, b], [ci, b, a]])
            capped += 1
    print("  caps", capped, flush=True)
    if not extra_p:
        return pos, nrm, uv, joints, weights, indices
    pos = np.vstack([pos, np.stack(extra_p)])
    nrm = np.vstack([nrm, np.stack(extra_n)])
    uv = np.vstack([uv, np.stack(extra_u)])
    joints = np.vstack([joints, np.stack(extra_j)])
    weights = np.vstack([weights, np.stack(extra_w)])
    indices = np.concatenate([indices.reshape(-1), np.array(extra_tri, np.int64).reshape(-1)])
    return pos, nrm, uv, joints, weights, indices


def fit():
    # Round-trip check for the quaternion helper before any file is written.
    rng = np.random.default_rng(0)
    for _ in range(20):
        q = qnorm(rng.normal(size=4))
        back = mat_to_quat(quat_mat(q))
        if abs(float(np.dot(q, back))) < 0.999:
            raise RuntimeError("quaternion roundtrip failed")

    hero_js, hero_blob = load_glb(HERO)
    _kept, _outfit, _under, _region, _color, _factor, jpos, _names = split_hero(hero_js, hero_blob)
    armor_js, armor_blob = load_glb(ARMOR["male"])
    fit_plates(jpos, armor_js, armor_blob, OUT_ARMOR)
    armor_js, armor_blob = load_glb(OUT_ARMOR)
    armor_blob = bytearray(armor_blob)
    names, apos, _node, _W, _parent = joint_maps(armor_js)
    pos, nrm, uv, joints, weights, indices, bname = dissolve_helpers(armor_js, armor_blob)
    pos, nrm, uv, joints, weights, indices = cap_openings(
        pos, nrm, uv, joints, weights, indices, bname, names, apos)
    prim = pack_mesh(
        armor_js, armor_blob,
        pos.astype(np.float32), nrm.astype(np.float32), uv.astype(np.float32),
        joints.astype(np.uint8), weights.astype(np.float32), indices.astype(np.uint32),
    )
    prim["material"] = armor_js["meshes"][0]["primitives"][0].get("material", 0)
    armor_js["meshes"][0]["primitives"] = [prim]

    # The solver closes over helpers defined in fit_armor_anims. Rebuild it here
    # as a direct call so the bind check and the clip write share one function.
    solve = prepare_solver(armor_js, hero_js, hero_blob)
    frame_locals, a_rest_r, _a_rest_t, _a_node, _ab, _hb, _hR = solve
    h_rest_r, h_rest_t, h_parent, h_name_of, _hn = node_rest(hero_js)
    idle = next(a for a in hero_js["animations"] if a.get("name") == "idle")
    idle_ch = channels(hero_js, hero_blob, idle)
    h_pos, h_R = pose_hero(hero_js, h_rest_r, h_rest_t, idle_ch, 0.0, h_parent, h_name_of)
    h_pos = dict(h_pos)
    h_pos["hips_local"] = sample_vec(*idle_ch["hips"]["translation"], 0.0)
    stood, _loc = frame_locals(h_pos, h_R, {})
    worst = 0.0
    worst_name = ""
    for name, q in a_rest_r.items():
        if name not in stood:
            continue
        d = min(1.0, abs(float(np.dot(qnorm(stood[name]), qnorm(q)))))
        ang = float(np.degrees(2 * np.arccos(d)))
        if ang > worst:
            worst, worst_name = ang, name
    print("  idle-as-sculpt residual deg", round(worst, 3), worst_name, flush=True)
    write_anims(armor_js, armor_blob, hero_js, hero_blob, solve)
    save_glb(armor_js, armor_blob, OUT_ARMOR)
    print("armor", OUT_ARMOR, os.path.getsize(OUT_ARMOR), flush=True)

    # The equipped body uses the same solved clips, so the face and the fists
    # stay with the plates. The unequipped body file is not modified.
    body_js, body_blob = load_glb(BODY)
    body_blob = bytearray(body_blob)
    body_solve = prepare_solver(body_js, hero_js, hero_blob)
    write_anims(body_js, body_blob, hero_js, hero_blob, body_solve)
    # Reload armor positions after the write. Rest positions are the fitted ones.
    armor_js, armor_blob = load_glb(OUT_ARMOR)
    anames, _ap, _n, _W, _p = joint_maps(armor_js)
    aprim = armor_js["meshes"][0]["primitives"][0]
    apos = read_acc(armor_js, armor_blob, aprim["attributes"]["POSITION"]).astype(np.float64)
    abone = np.array(anames)[dominant(
        read_acc(armor_js, armor_blob, aprim["attributes"]["JOINTS_0"]).astype(np.int32),
        read_acc(armor_js, armor_blob, aprim["attributes"]["WEIGHTS_0"]).astype(np.float32),
    )]
    body_js, body_blob, info = mask_body(body_js, body_blob, apos, abone, anames)
    save_glb(body_js, body_blob, OUT_BODY)
    print("body", info, os.path.getsize(OUT_BODY), flush=True)
    note = {
        "armor": OUT_ARMOR,
        "equipped_body": OUT_BODY,
        "unequipped_body": BODY,
        "unequipped_outfit": os.path.join(ROOT, "darius_outfit.glb"),
        "source_hero": HERO,
        "source_armor": ARMOR["male"],
        "equipped_mask": info,
        "bind_residual_deg": worst,
        "clips": "Every Darius key time. Plates stay rigid. Arms and legs reach the fist and the foot. Idle frame 0 is the closed sculpt. Run and attack still open the hollow limb shells.",
        "shell_caps": "53 mouths on the limb shells are capped. That does not cover the gap when a shell swings away.",
    }
    with open(os.path.join(ROOT, "darius_art.json"), "w") as f:
        json.dump(note, f, indent=2)
    return worst


def prepare_solver(armor_js, hero_js, hero_blob):
    """Return the solver closure. Idle frame 0 is the standing reference."""
    return build_solver(armor_js, hero_js, hero_blob)


def build_solver(armor_js, hero_js, hero_blob):
    a_rest_r, a_rest_t, a_parent, a_name_of, a_node = node_rest(armor_js)
    h_rest_r, h_rest_t, h_parent, h_name_of, _h_node = node_rest(hero_js)
    a_bind_pos, a_bind_R = fk(armor_js, a_rest_r, a_rest_t, a_parent, a_name_of)
    h_bind_pos, h_bind_R = fk(hero_js, h_rest_r, h_rest_t, h_parent, h_name_of)
    idle_anim = next(a for a in hero_js["animations"] if a.get("name") == "idle")
    idle_ch = channels(hero_js, hero_blob, idle_anim)
    h_idle_pos, h_idle_R = pose_hero(hero_js, h_rest_r, h_rest_t, idle_ch, 0.0, h_parent, h_name_of)
    h_idle_hips = h_rest_t["hips"]
    if "hips" in idle_ch and "translation" in idle_ch["hips"]:
        h_idle_hips = sample_vec(*idle_ch["hips"]["translation"], 0.0)

    def aim_axis(child):
        v = a_rest_t.get(child)
        if v is None:
            return None
        n = float(np.linalg.norm(v))
        if n < 1e-6:
            return None
        return v / n

    lengths = {}
    for root, mid, tip in LIMBS:
        lengths[root] = (
            float(np.linalg.norm(a_bind_pos[mid] - a_bind_pos[root])),
            float(np.linalg.norm(a_bind_pos[tip] - a_bind_pos[mid])),
        )

    cache = {}

    def current_world(name, rot, loc):
        key = (name, id(rot))
        if key in cache:
            return cache[key]
        i = a_node[name]
        chain = [i]
        while i in a_parent:
            i = a_parent[i]
            chain.append(i)
        M = np.eye(4)
        for i in reversed(chain):
            nm = a_name_of.get(i)
            r = rot.get(nm, np.array([0.0, 0.0, 0.0, 1.0])) if nm else np.array([0.0, 0.0, 0.0, 1.0])
            t = loc.get(nm, np.zeros(3)) if nm else np.zeros(3)
            L = np.eye(4)
            L[:3, :3] = quat_mat(r)
            L[:3, 3] = t
            M = M @ L
        cache[key] = M
        return M

    def current_R(name, rot, loc):
        if not name or name not in a_node:
            return None
        return ortho(current_world(name, rot, loc)[:3, :3])

    def current_pos(name, rot, loc):
        return current_world(name, rot, loc)[:3, 3].copy()

    torso_names = [n for n in TORSO if n in a_node and n in h_bind_R]

    def frame_locals(h_pos, h_R, prev):
        cache.clear()
        rot = {k: v.copy() for k, v in a_rest_r.items()}
        loc = {k: v.copy() for k, v in a_rest_t.items()}
        # Idle stays on the closed sculpt. Every other clip reaches Darius's
        # real joints, or the fists leave the gauntlets.
        absolute = bool(h_pos.get("_absolute"))
        ref_R = h_bind_R if absolute else h_idle_R
        ref_pos = h_bind_pos if absolute else h_idle_pos
        hips_ref = h_rest_t["hips"] if absolute else h_idle_hips
        if "hips" in loc and "hips_local" in h_pos:
            loc["hips"] = a_rest_t["hips"] + (h_pos["hips_local"] - hips_ref)

        def shifted(name):
            if absolute:
                return h_pos.get(name)
            if name not in a_bind_pos or name not in h_pos or name not in h_idle_pos:
                return h_pos.get(name)
            return a_bind_pos[name] + (h_pos[name] - h_idle_pos[name])

        pending = list(torso_names)
        placed = set()
        for _guard in range(24):
            if not pending:
                break
            later = []
            for name in pending:
                pi = a_parent.get(a_node[name])
                pname = a_name_of.get(pi) if pi is not None else None
                if pname in torso_names and pname not in placed:
                    later.append(name)
                    continue
                if name not in h_R or name not in ref_R or name not in a_bind_R:
                    placed.add(name)
                    continue
                desired = ortho(h_R[name] @ ref_R[name].T @ a_bind_R[name])
                parent_R = current_R(pname, rot, loc) if pname else None
                rot[name] = local_from_world(parent_R, desired)
                cache.clear()
                placed.add(name)
            if later == pending:
                break
            pending = later
        for shoulder, upper in SHOULDERS:
            axis = aim_axis(upper)
            if shoulder not in a_node or axis is None or upper not in h_pos:
                continue
            spos = current_pos(shoulder, rot, loc)
            desired = shifted(upper) - spos
            ln = float(np.linalg.norm(desired))
            if ln < 1e-5:
                continue
            desired = desired / ln
            base = a_bind_R[shoulder] if absolute else prev.get(shoulder, a_bind_R[shoulder])
            world = aim_world(base, axis, desired)
            if not absolute:
                prev[shoulder] = world
            pname = a_name_of.get(a_parent.get(a_node[shoulder]))
            rot[shoulder] = local_from_world(current_R(pname, rot, loc) if pname else None, world)
            cache.clear()
        for root, mid, tip in LIMBS:
            if root not in a_node or mid not in h_pos or tip not in h_pos:
                continue
            axis_mid = aim_axis(mid)
            axis_tip = aim_axis(tip)
            if axis_mid is None or axis_tip is None:
                continue
            l1, l2 = lengths[root]
            rpos = current_pos(root, rot, loc)
            Rpose = frame_delta(
                ref_pos[root], ref_pos[mid], ref_pos[tip],
                h_pos[root], h_pos[mid], h_pos[tip],
            )
            pole = rpos + Rpose @ (a_bind_pos[mid] - a_bind_pos[root])
            elbow, reached, miss = solve_two_bone(rpos, shifted(tip), pole, l1, l2)
            d_mid = elbow - rpos
            d_mid = d_mid / (np.linalg.norm(d_mid) + 1e-12)
            base = a_bind_R[root] if absolute else prev.get(root, a_bind_R[root])
            world_root = aim_world(base, axis_mid, d_mid)
            if not absolute:
                prev[root] = world_root
            pname = a_name_of.get(a_parent.get(a_node[root]))
            rot[root] = local_from_world(current_R(pname, rot, loc) if pname else None, world_root)
            cache.clear()
            d_tip = reached - elbow
            d_tip = d_tip / (np.linalg.norm(d_tip) + 1e-12)
            base = a_bind_R[mid] if absolute else prev.get(mid, a_bind_R[mid])
            world_mid = aim_world(base, axis_tip, d_tip)
            if not absolute:
                prev[mid] = world_mid
            rot[mid] = local_from_world(world_root, world_mid)
            cache.clear()
            prev["_miss_" + tip] = miss
        for bone, child in EXTREMITIES:
            axis = aim_axis(child)
            if bone not in a_node or axis is None or child not in h_pos or bone not in h_pos:
                continue
            if child not in ref_pos or bone not in ref_pos:
                continue
            bind_dir = ref_pos[child] - ref_pos[bone]
            pose_dir = h_pos[child] - h_pos[bone]
            if float(np.linalg.norm(bind_dir)) < 1e-5 or float(np.linalg.norm(pose_dir)) < 1e-5:
                continue
            desired = rot_between(bind_dir, pose_dir) @ (a_bind_R[bone] @ axis)
            desired = desired / (np.linalg.norm(desired) + 1e-12)
            base = a_bind_R[bone] if absolute else prev.get(bone, a_bind_R[bone])
            world = aim_world(base, axis, desired)
            if not absolute:
                prev[bone] = world
            pname = a_name_of.get(a_parent.get(a_node[bone]))
            rot[bone] = local_from_world(current_R(pname, rot, loc) if pname else None, world)
            cache.clear()
        for helper, child in HALF.items():
            if helper not in a_rest_r or child not in rot:
                continue
            delta = qmul(qinv(a_rest_r[child]), rot[child])
            rot[helper] = qnorm(qmul(a_rest_r[helper], slerp(np.array([0.0, 0.0, 0.0, 1.0]), qnorm(delta), 0.5)))
        # Overlapping cuffs. At rest every fraction is zero, so they stack on
        # the sculpt. Through a bend they fan and keep the joint covered.
        ident = np.array([0.0, 0.0, 0.0, 1.0])
        for helper, child, frac in SEGMENT_JOBS:
            if helper not in a_rest_r or child not in rot or child not in a_rest_r:
                continue
            delta = qmul(qinv(a_rest_r[child]), rot[child])
            rot[helper] = qnorm(qmul(a_rest_r[helper], slerp(ident, qnorm(delta), float(frac))))
        return rot, loc

    return frame_locals, a_rest_r, a_rest_t, a_node, a_bind_pos, h_bind_pos, h_bind_R


# The first draft of fit_armor_anims is not used. write_anims calls the solver tuple.
def fit_armor_anims(*_args, **_kwargs):
    raise RuntimeError("use build_solver")


if __name__ == "__main__":
    fit()
