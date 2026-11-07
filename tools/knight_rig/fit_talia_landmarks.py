"""Place the female knight on Talia using surface landmarks.

The hand joint is not the fist. The gauntlet is lined up with the fist
the outfit split kept, and the arm plates move as one assembly. Hero
vertices are not moved. Review only. Does not build the other heroes.
"""
import json
import os

import numpy as np

from fit_heroes import (
    ARMOR,
    PILOTS,
    chain_of,
    dominant,
    joint_maps,
    load_glb,
    quat_mat,
    read_acc,
    rot_between,
    save_glb,
)

OUT = "/workspace/www/proto3d/models/beth/equipment/knight_rig/fitted_heroes/talia/talia_armor_fit.glb"


def _gauntlet_mask(bone, side):
    mask = np.zeros(len(bone), bool)
    for name in set(bone.tolist()):
        if not name.endswith(side):
            continue
        if any(k in name for k in ("hand", "thumb", "index", "middle", "ring", "pinky", "finger")):
            mask |= bone == name
    return mask


def _arm_mask(bone, side):
    mask = np.zeros(len(bone), bool)
    for name in set(bone.tolist()):
        # Pauldrons stay on the cuirass. The arm below the shoulder is one assembly.
        if chain_of(name) == "arm" + side or name in (f"elbow{side}",):
            mask |= bone == name
    return mask


def _arm_joint_names(names, side):
    return [n for n in names if chain_of(n) == "arm" + side or n in (f"elbow{side}",)]


def _fist_center(pos, bone, side):
    hv = pos[bone == "hand" + side]
    if len(hv) < 8:
        return None
    return hv.mean(0)


def _write_joints_and_ibm(js, blob, pos, nrm, desired):
    names, _, node_of, _, parent = joint_maps(js)
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
            if nm in desired:
                pw = world[parent[i]]
                t = np.linalg.lstsq(pw[:3, :3], desired[nm] - pw[:3, 3], rcond=None)[0]
                node["translation"] = [float(x) for x in t]
                mat = local_matrix(node)
            world[i] = world[parent[i]] @ mat
        else:
            world[i] = mat

    prim = js["meshes"][0]["primitives"][0]
    acc = js["accessors"][prim["attributes"]["POSITION"]]
    bv = js["bufferViews"][acc["bufferView"]]
    start = bv.get("byteOffset", 0) + acc.get("byteOffset", 0)
    raw = np.ascontiguousarray(pos.astype(np.float32)).tobytes()
    blob[start:start + len(raw)] = raw
    nacc = js["accessors"][prim["attributes"]["NORMAL"]]
    nbv = js["bufferViews"][nacc["bufferView"]]
    nstart = nbv.get("byteOffset", 0) + nacc.get("byteOffset", 0)
    blob[nstart:nstart + len(np.ascontiguousarray(nrm.astype(np.float32)).tobytes())] = np.ascontiguousarray(nrm.astype(np.float32)).tobytes()
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
    return world


def fit():
    hero_js, hero_blob = load_glb(PILOTS["talia"]["path"])
    h_names, h_pos, _, _, _ = joint_maps(hero_js)
    hprim = hero_js["meshes"][0]["primitives"][0]
    # Fist landmark from the separated body, which already dropped the sleeve flare.
    body_js, body_blob = load_glb(
        "/workspace/www/proto3d/models/beth/equipment/knight_rig/fitted_heroes/talia/talia_body.glb"
    )
    b_names, _, _, _, _ = joint_maps(body_js)
    bprim = body_js["meshes"][0]["primitives"][0]
    bpos = read_acc(body_js, body_blob, bprim["attributes"]["POSITION"]).astype(np.float64)
    bj = read_acc(body_js, body_blob, bprim["attributes"]["JOINTS_0"]).astype(np.int32)
    bw = read_acc(body_js, body_blob, bprim["attributes"]["WEIGHTS_0"]).astype(np.float32)
    bb = np.array(b_names)[dominant(bj, bw)]
    hprim_pos = read_acc(hero_js, hero_blob, hprim["attributes"]["POSITION"]).astype(np.float64)
    hj = read_acc(hero_js, hero_blob, hprim["attributes"]["JOINTS_0"]).astype(np.int32)
    hw = read_acc(hero_js, hero_blob, hprim["attributes"]["WEIGHTS_0"]).astype(np.float32)
    hb = np.array(h_names)[dominant(hj, hw)]
    head = hprim_pos[hb == "head"]

    armor_js, armor_blob = load_glb(ARMOR["female"])
    names, apos, _, _, _ = joint_maps(armor_js)
    prim = armor_js["meshes"][0]["primitives"][0]
    pos = read_acc(armor_js, armor_blob, prim["attributes"]["POSITION"]).astype(np.float64)
    nrm = read_acc(armor_js, armor_blob, prim["attributes"]["NORMAL"]).astype(np.float64)
    joints = read_acc(armor_js, armor_blob, prim["attributes"]["JOINTS_0"]).astype(np.int32)
    weights = read_acc(armor_js, armor_blob, prim["attributes"]["WEIGHTS_0"]).astype(np.float32)
    bone = np.array(names)[dominant(joints, weights)]

    moved = {n: apos[n].copy() for n in names}
    report = {}

    # Torso: one scale about the hips so the cuirass height matches. Not an arm scale.
    s = float(np.linalg.norm(h_pos["head"] - h_pos["hips"]) / np.linalg.norm(apos["head"] - apos["hips"]))
    hip_a = apos["hips"].copy()
    hip_h = h_pos["hips"].copy()
    pos[:] = hip_h + (pos - hip_a) * s
    nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-12
    for n in moved:
        moved[n] = hip_h + (moved[n] - hip_a) * s
    report["torso_height_scale"] = round(s, 3)

    for side in ("_L", "_R"):
        fist = _fist_center(bpos, bb, side)
        gmask = _gauntlet_mask(bone, side)
        amask = _arm_mask(bone, side)
        if fist is None or gmask.sum() < 20 or amask.sum() < 20:
            report["arm" + side] = "missing"
            continue
        shoulder_a = moved["upperArm" + side].copy()
        gaunt = pos[gmask].mean(0)
        shoulder_h = h_pos["upperArm" + side]
        src = gaunt - shoulder_a
        dst = fist - shoulder_h
        scale = float(np.linalg.norm(dst) / np.linalg.norm(src))
        rot = rot_between(src, dst)
        before = {n: moved[n].copy() for n in _arm_joint_names(names, side) if n in moved}
        pos[amask] = shoulder_h + ((pos[amask] - shoulder_a) * scale) @ rot.T
        nrm[amask] = nrm[amask] @ rot.T
        for n, p0 in before.items():
            moved[n] = shoulder_h + rot @ ((p0 - shoulder_a) * scale)
        # Animation pivots stay on Talia's joints. The gauntlet mesh stays on the fist,
        # so its rest offset from the hand joint is the fist's offset, not zero.
        for joint in ("upperArm" + side, "foreArm" + side, "hand" + side):
            if joint in h_pos and joint in moved:
                moved[joint] = h_pos[joint].copy()
        placed = pos[gmask].mean(0)
        report["arm" + side] = {
            "landmark_scale": round(scale, 3),
            "fist": [round(float(x), 3) for x in fist],
            "gauntlet_after": [round(float(x), 3) for x in placed],
            "gauntlet_to_fist_cm": round(float(np.linalg.norm(placed - fist)) * 100, 2),
            "fist_to_hand_joint_cm": round(float(np.linalg.norm(fist - h_pos["hand" + side])) * 100, 1),
        }

    # Helm: slide the head shell toward the head cloud. Do not scale it and do not touch hair.
    hmask = bone == "head"
    if hmask.any() and len(head):
        delta = head.mean(0) - pos[hmask].mean(0)
        dist = float(np.linalg.norm(delta))
        cap = 0.04
        if dist > cap:
            delta = delta / dist * cap
        pos[hmask] += delta
        if "head" in moved:
            moved["head"] = moved["head"] + delta
        report["helm_shift_cm"] = round(float(np.linalg.norm(delta)) * 100, 2)

    nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-12
    js = json.loads(json.dumps(armor_js))
    blob = bytearray(armor_blob)
    _write_joints_and_ibm(js, blob, pos, nrm, moved)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    save_glb(js, blob, OUT)
    json.dump(report, open(OUT.replace(".glb", "_landmarks.json"), "w"), indent=2)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    fit()
