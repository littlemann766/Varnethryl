"""Review-only bind-aware fit. Not used by the game.

The previous review copied local joint quaternions. That is not a retarget
when rest poses differ: every bone node in these GLBs shares one orientation,
and the limb direction is the child offset. The same quaternion therefore
swings two different rest offsets to two different places.

This script aims each armor bone so its child offset (armor length kept)
points along the hero bone's posed child offset, then reapplies the hero's
twist around that limb. Plate helpers stay constraints on this review
armature only. The armor mesh is not scaled and its vertices are not moved
except by those rigid bone transforms.

Cape and coat-bone vertices are hidden on a review copy of the hero mesh.
They are not removed from the GLB. Shoulder, arm, hand, leg, and head
weights stay visible. If the bulky coat or robe is weighted to chest/hips,
it cannot be hidden without deleting the torso; that is reported, not faked.
"""
import math
import os
import sys

import bpy
import bmesh
from mathutils import Matrix, Quaternion, Vector

OUT = os.environ.get("KNIGHT_BIND_OUT", "/tmp/krender/bindfit")
os.makedirs(OUT, exist_ok=True)

# Armor bone -> child used as the limb axis. Hero uses the same pair when
# both bones exist; otherwise the fallback child on the hero.
CHAIN = [
    ("hips", "spine", "spine"),
    ("spine", "spine2", "chest"),
    ("spine2", "chest", "chest"),
    ("chest", "upperChest", "neck"),
    ("upperChest", "neck", "neck"),
    ("neck", "head", None),
    ("shoulder_L", "upperArm_L", "upperArm_L"),
    ("upperArm_L", "foreArm_L", "foreArm_L"),
    ("foreArm_L", "hand_L", "hand_L"),
    ("hand_L", "middle1_L", "fingers_L"),
    ("shoulder_R", "upperArm_R", "upperArm_R"),
    ("upperArm_R", "foreArm_R", "foreArm_R"),
    ("foreArm_R", "hand_R", "hand_R"),
    ("hand_R", "middle1_R", "fingers_R"),
    ("thigh_L", "shin_L", "shin_L"),
    ("shin_L", "foot_L", "foot_L"),
    ("foot_L", "toe_L", "toe_L"),
    ("thigh_R", "shin_R", "shin_R"),
    ("shin_R", "foot_R", "foot_R"),
    ("foot_R", "toe_R", "toe_R"),
]


def setup_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE"
    sc.eevee.taa_render_samples = 16
    sc.view_settings.view_transform = "Standard"
    sc.render.resolution_x = 1600
    sc.render.resolution_y = 1600
    sc.render.fps = 30
    w = bpy.data.worlds.new("w")
    sc.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.62, 0.63, 0.65, 1)
    bg.inputs[1].default_value = 0.7
    sun = bpy.data.objects.new("key", bpy.data.lights.new("key", "SUN"))
    sc.collection.objects.link(sun)
    sun.rotation_euler = (math.radians(54), math.radians(8), math.radians(-36))
    sun.data.energy = 3.4
    fill = bpy.data.objects.new("fill", bpy.data.lights.new("fill", "SUN"))
    sc.collection.objects.link(fill)
    fill.rotation_euler = (math.radians(68), 0, math.radians(148))
    fill.data.energy = 1.4
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam.data.type = "ORTHO"
    return sc, cam


def import_glb(path, prefix):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    arm = next(o for o in new if o.type == "ARMATURE")
    meshes = [o for o in new if o.type == "MESH" and "Icosphere" not in o.name]
    arm["src_name"] = arm.name
    arm.name = prefix + "_rig"
    for i, m in enumerate(meshes):
        m.name = prefix + ("_body" if i == 0 else f"_m{i}")
    if arm.animation_data:
        arm.animation_data.action = None
        for tr in arm.animation_data.nla_tracks:
            tr.mute = True
    return arm, meshes


def action_map(hero):
    src = hero.get("src_name", "")
    out = {}
    for a in bpy.data.actions:
        name = a.name
        if src and name.endswith("_" + src):
            name = name[: -(len(src) + 1)]
        out[name.split(".")[0]] = a
    return out


def zero(arm):
    arm.data.pose_position = "POSE"
    if arm.animation_data:
        arm.animation_data.action = None
    for pb in arm.pose.bones:
        pb.rotation_mode = "QUATERNION"
        pb.rotation_quaternion = (1, 0, 0, 0)
        pb.location = (0, 0, 0)
        pb.scale = (1, 1, 1)


def has(arm, name):
    return name in arm.pose.bones


def hero_child(hero, primary, fallback):
    if primary and has(hero, primary):
        return primary
    if fallback and has(hero, fallback):
        return fallback
    return None


def world_head(arm, pb):
    return arm.matrix_world @ pb.head


def limb_dir(arm, bone, child):
    a = world_head(arm, arm.pose.bones[bone])
    b = world_head(arm, arm.pose.bones[child])
    v = b - a
    if v.length < 1e-6:
        return None
    return v.normalized()


# Long limbs only. Shoulder and spine offsets are short; aiming them swings
# the arm origin off the body. Those bones keep the copied local rotation.
AIM_BONES = {
    "upperArm_L", "foreArm_L", "hand_L",
    "upperArm_R", "foreArm_R", "hand_R",
    "thigh_L", "shin_L", "foot_L",
    "thigh_R", "shin_R", "foot_R",
}


def add_helpers(arm):
    pb = arm.pose.bones

    def cr(dst, src, inf, axes=(True, True, True)):
        if dst not in pb or src not in pb:
            return
        c = pb[dst].constraints.new("COPY_ROTATION")
        c.target = arm
        c.subtarget = src
        c.target_space = "LOCAL"
        c.owner_space = "LOCAL"
        c.mix_mode = "ADD"
        c.influence = inf
        c.use_x, c.use_y, c.use_z = axes

    for side in ("_L", "_R"):
        cr("pauldron" + side, "upperArm" + side, 0.45)
        cr("elbow" + side, "foreArm" + side, 0.50)
        cr("knee" + side, "shin" + side, 0.50)
        cr("tasset" + side, "thigh" + side, 0.85)
        cr("foreArm_twist" + side, "hand" + side, 0.50)
        for src in ("upperArm", "foreArm", "hand", "shin", "thigh", "foot"):
            cr("mid_" + src + side, src + side, 0.50)
    for i, inf in ((1, 0.35), (2, 0.15)):
        for prefix in ("tabard_F_", "tabard_B_"):
            name = f"{prefix}{i:02d}"
            cr(name, "thigh_L", inf, (True, False, False))
            cr(name, "thigh_R", inf, (True, False, False))


def hide_clothing(obj):
    """Review copy only. Cape and coat bones. Not limbs, not the GLB."""
    obj.data = obj.data.copy()
    names = [g.name for g in obj.vertex_groups]
    doomed = []
    for v in obj.data.vertices:
        if not v.groups:
            continue
        g = max(v.groups, key=lambda x: x.weight)
        n = names[g.group]
        if n.startswith(("coat", "cape")):
            doomed.append(v.index)
    if not doomed:
        return 0
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.verts.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[bm.verts[i] for i in doomed], context="VERTS")
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()
    return len(doomed)


def copy_locals(hero, armor):
    """Same local axes on both rigs, so the clip's local rotation is the motion."""
    for name in hero.pose.bones.keys():
        if not has(armor, name):
            continue
        if name.startswith("mid_") or name.startswith(("pauldron", "elbow", "knee", "tasset", "tabard")):
            continue
        src = hero.pose.bones[name]
        dst = armor.pose.bones[name]
        dst.rotation_mode = "QUATERNION"
        dst.rotation_quaternion = src.rotation_quaternion.copy()
    bpy.context.view_layer.update()


def aim_armor(hero, armor):
    """After the copied pose, aim long bones along the hero limb. Lengths stay."""
    errors = []
    for bone, child, fallback in CHAIN:
        if bone not in AIM_BONES or not has(armor, bone) or not has(armor, child):
            continue
        h_child = hero_child(hero, child, fallback)
        if h_child is None or not has(hero, bone):
            continue
        d_h = limb_dir(hero, bone, h_child)
        if d_h is None:
            continue
        ap = armor.pose.bones[bone]
        ap.rotation_quaternion = (1, 0, 0, 0)
        bpy.context.view_layer.update()
        d_a = limb_dir(armor, bone, child)
        if d_a is None:
            continue
        q_aim = d_a.rotation_difference(d_h)
        current = armor.matrix_world @ ap.matrix
        head = current.to_translation()
        # Rotate around the joint. A bare quaternion spins the bone about the world origin.
        spin = Matrix.Translation(head) @ q_aim.to_matrix().to_4x4() @ Matrix.Translation(-head)
        target = spin @ current
        ap.matrix = armor.matrix_world.inverted() @ target
        bpy.context.view_layer.update()
        if os.environ.get("KNIGHT_AIM_DEBUG"):
            gap = (world_head(armor, ap) - world_head(hero, hero.pose.bones[bone])).length
            print(
                "  aim", bone,
                "swing", round(math.degrees(q_aim.angle), 1),
                "joint gap m", round(gap, 3),
                flush=True,
            )
        d_after = limb_dir(armor, bone, child)
        if d_after is not None:
            err = math.degrees(math.acos(max(-1.0, min(1.0, d_after.dot(d_h)))))
            errors.append((bone, err))
    return errors


def apply_clip(hero, armor, action, frame):
    zero(hero)
    zero(armor)
    hero.animation_data_create()
    hero.animation_data.action = action
    bpy.context.scene.frame_set(int(frame))
    bpy.context.view_layer.update()
    # Shared root motion. Armor keeps its own bone lengths.
    for name in ("root", "hips"):
        if has(hero, name) and has(armor, name):
            armor.pose.bones[name].location = hero.pose.bones[name].location.copy()
    bpy.context.view_layer.update()
    copy_locals(hero, armor)
    if os.environ.get("KNIGHT_AIM_DEBUG"):
        for name in ("hips", "spine", "chest", "upperChest", "shoulder_L", "upperArm_L", "thigh_L"):
            if has(hero, name) and has(armor, name):
                gap = (world_head(armor, armor.pose.bones[name]) - world_head(hero, hero.pose.bones[name])).length
                print("  copy gap", name, round(gap, 3), flush=True)
    errors = aim_armor(hero, armor)
    # Place the armor hips on the hero hips. No scale.
    if has(hero, "hips") and has(armor, "hips"):
        delta = world_head(hero, hero.pose.bones["hips"]) - world_head(armor, armor.pose.bones["hips"])
        armor.location = armor.location + delta
        bpy.context.view_layer.update()
    return errors


def pick_frame(action, bone_name, arm):
    arm.animation_data_create()
    arm.animation_data.action = action
    f0, f1 = [int(round(x)) for x in action.frame_range]
    if bone_name not in arm.pose.bones:
        return int(round((f0 + f1) * 0.5))
    best_f, best = f0, -1.0
    step = max(1, (f1 - f0) // 16)
    for f in range(f0, f1 + 1, step):
        bpy.context.scene.frame_set(f)
        bpy.context.view_layer.update()
        ang = arm.pose.bones[bone_name].rotation_quaternion.angle
        if ang > best:
            best, best_f = ang, f
    arm.animation_data.action = None
    return best_f


def look(cam, target, yaw_deg, ortho):
    yaw = math.radians(yaw_deg)
    t = Vector(target)
    cam.location = t + Vector((math.sin(yaw) * 7, -math.cos(yaw) * 7, 0.15))
    cam.rotation_euler = (t - cam.location).to_track_quat("-Z", "Y").to_euler()
    cam.data.ortho_scale = ortho


def shot(sc, cam, path, target, yaw, ortho, rx, ry):
    look(cam, target, yaw, ortho)
    sc.render.resolution_x = rx
    sc.render.resolution_y = ry
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print("SHOT", path, flush=True)


def set_visible(objs, on):
    for o in objs:
        o.hide_render = not on
        o.hide_set(not on)


def coverage(hero_mesh, armor_mesh, limit=0.04):
    """Share of body verts farther than limit from any armor vert. Review metric only."""
    from mathutils.kdtree import KDTree

    def co(obj):
        dg = bpy.context.evaluated_depsgraph_get()
        ev = obj.evaluated_get(dg)
        m = ev.to_mesh()
        mw = obj.matrix_world
        pts = [mw @ v.co for v in m.vertices]
        ev.to_mesh_clear()
        return pts

    body = co(hero_mesh)
    arm = co(armor_mesh)
    if len(arm) < 10 or len(body) < 10:
        return None
    tree = KDTree(len(arm))
    for i, p in enumerate(arm):
        tree.insert(p, i)
    tree.balance()
    def stats(pts):
        step = max(1, len(pts) // 4000)
        ds = []
        for p in pts[::step]:
            _, _, dist = tree.find(p)
            ds.append(dist)
        ds.sort()
        n = len(ds)
        if n == 0:
            return None
        return {
            "sample": n,
            "p50_m": round(ds[n // 2], 3),
            "p90_m": round(ds[min(n - 1, int(n * 0.9))], 3),
            "frac_gt_4cm": round(sum(1 for d in ds if d > limit) / n, 3),
        }

    limb_names = {
        "upperArm_L", "upperArm_R", "foreArm_L", "foreArm_R",
        "thigh_L", "thigh_R", "shin_L", "shin_R",
    }
    names = [g.name for g in hero_mesh.vertex_groups]
    limb_idx = []
    for v in hero_mesh.data.vertices:
        if not v.groups:
            continue
        g = max(v.groups, key=lambda x: x.weight)
        if names[g.group] in limb_names:
            limb_idx.append(v.index)
    if len(body) != len(hero_mesh.data.vertices):
        limb_pts = []
    else:
        limb_pts = [body[i] for i in limb_idx]
    return {"all": stats(body), "limbs": stats(limb_pts)}


def render_job(tag, hero_path, armor_path, clips, closeups):
    sc, cam = setup_scene()
    hero, hero_meshes = import_glb(hero_path, "hero")
    actions = action_map(hero)
    armor, armor_meshes = import_glb(armor_path, "armor")
    n_hide = hide_clothing(hero_meshes[0])
    print(tag, "clothing verts hidden in review copy", n_hide, flush=True)
    add_helpers(armor)
    # rest hip delta before any clip, for the report
    zero(hero)
    zero(armor)
    bpy.context.view_layer.update()
    if has(hero, "hips") and has(armor, "hips"):
        d = world_head(hero, hero.pose.bones["hips"]) - world_head(armor, armor.pose.bones["hips"])
        print(tag, "rest hip delta m", tuple(round(x, 3) for x in d), flush=True)

    for clip, bone in clips:
        act = actions.get(clip)
        if act is None:
            print("MISSING", tag, clip, sorted(actions), flush=True)
            continue
        frame = pick_frame(act, bone, hero)
        errors = apply_clip(hero, armor, act, frame)
        mean = sum(e for _, e in errors) / max(len(errors), 1)
        worst = max(errors, key=lambda t: t[1]) if errors else ("none", 0)
        print(tag, clip, "f", frame, "aim err mean deg", round(mean, 2), "worst", worst[0], round(worst[1], 2), flush=True)
        cov = coverage(hero_meshes[0], armor_meshes[0])
        print(tag, clip, "body-to-armor", cov, flush=True)
        # full equipped
        set_visible(armor_meshes, True)
        set_visible(hero_meshes, True)
        tgt = world_head(armor, armor.pose.bones["hips"])
        tgt = Vector((tgt.x, tgt.y, tgt.z + 0.15))
        if os.environ.get("KNIGHT_SKIP_RENDER"):
            continue
        shot(sc, cam, f"{OUT}/{tag}_{clip}_f{frame}_full.png", tgt, 20, 2.15, 1100, 1400)
        for cname, bone_name, yaw, size in closeups.get(clip, []):
            if not has(armor, bone_name):
                continue
            loc = world_head(armor, armor.pose.bones[bone_name])
            shot(sc, cam, f"{OUT}/{tag}_{clip}_f{frame}_{cname}.png", loc, yaw, size, 1600, 1400)
        # bare body, same framing as the equipped full shot
        set_visible(armor_meshes, False)
        shot(sc, cam, f"{OUT}/{tag}_{clip}_f{frame}_bare.png", tgt, 20, 2.15, 1100, 1400)
        set_visible(armor_meshes, True)


def main():
    which = "probe"
    if "--" in sys.argv:
        which = sys.argv[sys.argv.index("--") + 1]
    hero_m = "/tmp/heroes/darius_voxel_noweapon.glb"
    hero_f = "/tmp/heroes/talia_voxel_main.glb"
    hero_r = "/tmp/heroes/rook_voxel.glb"
    armor_m = "/workspace/www/proto3d/models/beth/equipment/knight_rig/knight_male.glb"
    armor_f = "/workspace/www/proto3d/models/beth/equipment/knight_rig/knight_female.glb"
    male_close = {
        "idle": [("torso", "chest", 28, 1.15), ("shoulder", "upperArm_L", 40, 0.85)],
        "run": [("knee", "shin_L", 80, 0.95)],
        "attack": [("elbow", "foreArm_R", 55, 0.9)],
    }
    female_close = {
        "idle": [("arm", "foreArm_L", 70, 1.05)],
        "run": [("knee", "shin_L", 80, 0.95)],
        "attack1": [("elbow", "foreArm_R", 50, 0.95)],
    }
    rook_close = {
        "run": [("torso", "chest", 25, 1.3)],
        "attack1": [("shoulder", "upperArm_R", 40, 1.05)],
    }
    jobs = {
        "darius": (hero_m, armor_m, [("idle", "hips"), ("run", "shin_L"), ("attack", "upperArm_R")], male_close),
        "talia": (hero_f, armor_f, [("idle", "hips"), ("run", "shin_L"), ("attack1", "upperArm_R")], female_close),
        "rook": (hero_r, armor_m, [("idle", "hips"), ("run", "shin_L"), ("attack1", "upperArm_R")], rook_close),
    }
    if which == "probe":
        render_job("darius", hero_m, armor_m, [("idle", "hips")], {"idle": [("torso", "chest", 28, 1.15)]})
        render_job("talia", hero_f, armor_f, [("idle", "hips")], {"idle": [("arm", "foreArm_L", 70, 1.05)]})
    elif which in jobs:
        render_job(which, *jobs[which])
    else:
        for name, args in jobs.items():
            render_job(name, *args)
    print("DONE")


if __name__ == "__main__":
    main()
