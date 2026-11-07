"""Review renders of the separated body and the fitted knight armor.

Not used by the game. Shows the untouched source, the reversible
keep+outfit composite, and the equipped body (keep + underlayer + armor).
"""
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

OUT = os.environ.get("KNIGHT_FIT_OUT", "/tmp/krender/fitted")
os.makedirs(OUT, exist_ok=True)

CHAIN = [
    ("upperArm_L", "foreArm_L", "foreArm_L"),
    ("foreArm_L", "hand_L", "hand_L"),
    ("hand_L", "middle1_L", "fingers_L"),
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
AIM = {a for a, _, _ in CHAIN}


def setup():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE"
    sc.eevee.taa_render_samples = 16
    sc.view_settings.view_transform = "Standard"
    sc.render.resolution_x = 1200
    sc.render.resolution_y = 1600
    sc.render.fps = 30
    w = bpy.data.worlds.new("w")
    sc.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.62, 0.63, 0.65, 1)
    bg.inputs[1].default_value = 0.75
    sun = bpy.data.objects.new("key", bpy.data.lights.new("key", "SUN"))
    sc.collection.objects.link(sun)
    sun.rotation_euler = (math.radians(54), math.radians(8), math.radians(-36))
    sun.data.energy = 3.6
    fill = bpy.data.objects.new("fill", bpy.data.lights.new("fill", "SUN"))
    sc.collection.objects.link(fill)
    fill.rotation_euler = (math.radians(70), 0, math.radians(150))
    fill.data.energy = 1.5
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam.data.type = "ORTHO"
    return sc, cam


def import_glb(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    arm = next((o for o in new if o.type == "ARMATURE"), None)
    meshes = []
    for o in new:
        if o.type != "MESH":
            continue
        if "Icosphere" in o.name:
            o.hide_render = True
            o.hide_set(True)
            continue
        meshes.append(o)
    if arm and arm.animation_data:
        arm.animation_data.action = None
        for tr in arm.animation_data.nla_tracks:
            tr.mute = True
    return arm, meshes


def actions_of(arm):
    src = arm.name if arm else ""
    # gltf import names the armature from the node. Actions may carry a suffix.
    out = {}
    for a in bpy.data.actions:
        name = a.name.split("|")[-1]
        out[name.split(".")[0]] = a
    return out


def zero(arm):
    if arm.animation_data:
        arm.animation_data.action = None
    for pb in arm.pose.bones:
        pb.rotation_mode = "QUATERNION"
        pb.rotation_quaternion = (1, 0, 0, 0)
        pb.location = (0, 0, 0)
        pb.scale = (1, 1, 1)


def has(arm, name):
    return name in arm.pose.bones


def world_head(arm, pb):
    return arm.matrix_world @ pb.head


def limb_dir(arm, bone, child):
    a = world_head(arm, arm.pose.bones[bone])
    b = world_head(arm, arm.pose.bones[child])
    v = b - a
    if v.length < 1e-6:
        return None
    return v.normalized()


def hero_child(hero, primary, fallback):
    if primary and has(hero, primary):
        return primary
    if fallback and has(hero, fallback):
        return fallback
    return None


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


def copy_and_aim(hero, armor):
    for name in hero.pose.bones.keys():
        if not has(armor, name):
            continue
        if name.startswith(("mid_", "pauldron", "elbow", "knee", "tasset", "tabard")):
            continue
        armor.pose.bones[name].rotation_mode = "QUATERNION"
        armor.pose.bones[name].rotation_quaternion = hero.pose.bones[name].rotation_quaternion.copy()
    for name in ("root", "hips"):
        if has(hero, name) and has(armor, name):
            armor.pose.bones[name].location = hero.pose.bones[name].location.copy()
    bpy.context.view_layer.update()
    worst = 0.0
    for bone, child, fallback in CHAIN:
        if bone not in AIM or not has(armor, bone) or not has(armor, child):
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
        q = d_a.rotation_difference(d_h)
        current = armor.matrix_world @ ap.matrix
        head = current.to_translation()
        spin = Matrix.Translation(head) @ q.to_matrix().to_4x4() @ Matrix.Translation(-head)
        ap.matrix = armor.matrix_world.inverted() @ (spin @ current)
        bpy.context.view_layer.update()
        d_after = limb_dir(armor, bone, child)
        if d_after is not None:
            err = math.degrees(math.acos(max(-1.0, min(1.0, d_after.dot(d_h)))))
            worst = max(worst, err)
    if has(hero, "hips") and has(armor, "hips"):
        delta = world_head(hero, hero.pose.bones["hips"]) - world_head(armor, armor.pose.bones["hips"])
        armor.location = armor.location + delta
        bpy.context.view_layer.update()
    return worst


def look(cam, target, yaw_deg, ortho):
    yaw = math.radians(yaw_deg)
    t = Vector(target)
    cam.location = t + Vector((math.sin(yaw) * 8, -math.cos(yaw) * 8, 0.2))
    cam.rotation_euler = (t - cam.location).to_track_quat("-Z", "Y").to_euler()
    cam.data.ortho_scale = ortho


def shot(sc, cam, path, target, yaw, ortho, rx, ry):
    look(cam, target, yaw, ortho)
    sc.render.resolution_x = rx
    sc.render.resolution_y = ry
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print("SHOT", path, flush=True)


def show(objs, on):
    for o in objs:
        o.hide_render = not on
        o.hide_set(not on)


def pick(arm, action, bone):
    arm.animation_data_create()
    arm.animation_data.action = action
    f0, f1 = [int(round(x)) for x in action.frame_range]
    if bone not in arm.pose.bones:
        return int(round((f0 + f1) * 0.5))
    best_f, best = f0, -1.0
    step = max(1, (f1 - f0) // 18)
    for f in range(f0, f1 + 1, step):
        bpy.context.scene.frame_set(f)
        bpy.context.view_layer.update()
        ang = arm.pose.bones[bone].rotation_quaternion.angle
        if ang > best:
            best, best_f = ang, f
    arm.animation_data.action = None
    return best_f


def pose(hero, armor, action, frame):
    zero(hero)
    zero(armor)
    hero.animation_data_create()
    hero.animation_data.action = action
    bpy.context.scene.frame_set(int(frame))
    bpy.context.view_layer.update()
    err = copy_and_aim(hero, armor)
    return err


def by_name(meshes, token):
    return [m for m in meshes if token in m.name.lower()]


def render_character(hid, source, body, outfit, armor, equipped_body=None):
    sc, cam = setup()
    # source original, its own file
    src_arm, src_meshes = import_glb(source)
    src_acts = actions_of(src_arm)
    # Unequipped body keeps every hair vertex. Equipped body drops only
    # the hair that intersects the helm.
    plain_arm, plain_meshes = import_glb(body)
    if equipped_body:
        hero, hero_meshes = import_glb(equipped_body)
    else:
        hero, hero_meshes = plain_arm, plain_meshes
    acts = actions_of(hero)
    out_arm, out_meshes = import_glb(outfit)
    arm, arm_meshes = import_glb(armor)
    add_helpers(arm)
    print(hid, "objects",
          "src", [m.name for m in src_meshes],
          "body", [m.name for m in hero_meshes],
          "outfit", [m.name for m in out_meshes],
          "armor", [m.name for m in arm_meshes], flush=True)
    keep = [m for m in hero_meshes if "underlayer" not in m.name.lower()]
    under = [m for m in hero_meshes if "underlayer" in m.name.lower()]
    print(hid, "keep", len(keep), "under", len(under), "actions", sorted(acts)[:8], flush=True)

    def hips_of(a):
        zero(a)
        bpy.context.view_layer.update()
        return world_head(a, a.pose.bones["hips"])

    # rest equipped
    zero(hero)
    zero(arm)
    bpy.context.view_layer.update()
    err = copy_and_aim(hero, arm)
    print(hid, "rest aim deg", round(err, 3), flush=True)
    show(src_meshes, False)
    show(out_meshes, False)
    show(plain_meshes, False)
    show(keep, True)
    show(under, True)
    show(arm_meshes, True)
    tgt = world_head(hero, hero.pose.bones["hips"])
    tgt = Vector((tgt.x, tgt.y, tgt.z + 0.35))
    shot(sc, cam, f"{OUT}/{hid}_rest_equipped_front.png", tgt, 18, 2.05, 1100, 1500)

    # original unequipped, same framing family
    show(hero_meshes, False)
    show(arm_meshes, False)
    show(out_meshes, False)
    show(src_meshes, True)
    zero(src_arm)
    bpy.context.view_layer.update()
    st = world_head(src_arm, src_arm.pose.bones["hips"])
    st = Vector((st.x, st.y, st.z + 0.35))
    shot(sc, cam, f"{OUT}/{hid}_rest_original_front.png", st, 18, 2.05, 1100, 1500)

    # reversible composite: full hair, outfit, no mail, no armor
    show(src_meshes, False)
    show(hero_meshes, False)
    show(plain_meshes, True)
    for m in plain_meshes:
        if "underlayer" in m.name.lower():
            m.hide_render = True
    show(out_meshes, True)
    # outfit has its own armature; pose both at rest. They share the source rest.
    zero(hero)
    zero(out_arm)
    bpy.context.view_layer.update()
    shot(sc, cam, f"{OUT}/{hid}_rest_composite_front.png", tgt, 18, 2.05, 1100, 1500)

    clips = []
    for key, bone in (("idle", "hips"), ("walk", "shin_L"), ("run", "shin_L"), ("attack", "foreArm_R")):
        act = None
        cands = []
        for n, a in acts.items():
            base = n.split("_")[0]
            if base == key or n == key:
                cands.append((len(n), a))
        if not cands and key == "attack":
            for n, a in acts.items():
                if n.split("_")[0].startswith("attack"):
                    cands.append((len(n), a))
        if cands:
            act = min(cands, key=lambda t: t[0])[1]
        if act is None:
            print("MISSING", hid, key, flush=True)
            continue
        frame = pick(hero, act, bone if has(hero, bone) else "hips")
        # re-find the same action name on... hero is the body armature, actions are shared in the file
        err = pose(hero, arm, act, frame)
        # outfit armature is separate; not shown
        show(src_meshes, False)
        show(out_meshes, False)
        show(plain_meshes, False)
        show(keep, True)
        show(under, True)
        show(arm_meshes, True)
        t = world_head(hero, hero.pose.bones["hips"])
        t = Vector((t.x, t.y, t.z + 0.35))
        print(hid, key, "f", frame, "aim", round(err, 3), flush=True)
        if key in ("idle", "run", "attack"):
            shot(sc, cam, f"{OUT}/{hid}_{key}_f{frame}_front.png", t, 18, 2.05, 1100, 1500)
            shot(sc, cam, f"{OUT}/{hid}_{key}_f{frame}_side.png", t, 100, 2.05, 1100, 1500)
            shot(sc, cam, f"{OUT}/{hid}_{key}_f{frame}_back.png", t, 198, 2.05, 1100, 1500)
        if key == "attack" and has(arm, "foreArm_R"):
            loc = world_head(arm, arm.pose.bones["foreArm_R"])
            shot(sc, cam, f"{OUT}/{hid}_attack_elbow.png", loc, 55, 0.85, 1500, 1300)
        if key == "run" and has(arm, "shin_L"):
            loc = world_head(arm, arm.pose.bones["shin_L"])
            shot(sc, cam, f"{OUT}/{hid}_run_knee.png", loc, 80, 0.9, 1500, 1300)
        if key == "idle" and has(arm, "head"):
            loc = world_head(arm, arm.pose.bones["head"])
            shot(sc, cam, f"{OUT}/{hid}_idle_helm.png", loc, 24, 0.85, 1500, 1300)
            if has(hero, "hand_L"):
                loc = world_head(hero, hero.pose.bones["hand_L"])
                shot(sc, cam, f"{OUT}/{hid}_idle_hand.png", loc, 40, 0.7, 1400, 1200)
        clips.append(key)
    return clips


def main():
    which = "darius"
    if "--" in sys.argv:
        which = sys.argv[sys.argv.index("--") + 1]
    base = "/workspace/www/proto3d/models/beth/equipment/knight_rig/fitted_heroes"
    sources = {
        "darius": "/tmp/heroes/darius_voxel_noweapon.glb",
        "talia": "/tmp/heroes/talia_voxel_main.glb",
        "rook": "/tmp/heroes/rook_voxel.glb",
    }
    ids = ["darius", "talia", "rook"] if which == "all" else [which]
    for hid in ids:
        render_character(
            hid,
            sources[hid],
            f"{base}/{hid}/{hid}_body.glb",
            f"{base}/{hid}/{hid}_outfit.glb",
            f"{base}/{hid}/{hid}_armor_fit.glb",
            equipped_body=f"{base}/{hid}/{hid}_body_equipped.glb",
        )
    print("DONE")


if __name__ == "__main__":
    main()
