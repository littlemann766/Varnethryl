"""Review-only fit check. Not used by the game.

Puts the shared knight armor on the real Godot voxel heroes and plays their
clips. Sources (read from git, not merged into this branch):

  origin/weaponless-rigs:voxel/darius_voxel_noweapon.glb
  origin/main:voxel/talia_voxel.glb
  origin/main:voxel/rook_voxel.glb   (different male build; same armor, no scale)

Anatomical rotations are copied from the hero clip. Arm/leg bones whose rest
direction differs from the hero get the same correction as
tools/knight_rig/retarget_fix.py. Helper plates (pauldron 0.45, elbow/knee
0.5, tasset 0.85, tabard X, twists) are constraints on this review armature
only. Hero joint angles are not soft-limited.

Jump is not in these GLBs. The empty jump_* tracks inside the knight GLB are
not used.
"""
import math
import os
import sys

import bpy
from mathutils import Quaternion, Vector

OUT = os.environ.get("KNIGHT_REVIEW_OUT", "/tmp/krender/onhero")
os.makedirs(OUT, exist_ok=True)

# (parent bone, child bone) pairs whose rest direction is corrected.
PAIRS = [
    ("upperArm_L", "foreArm_L"), ("foreArm_L", "hand_L"),
    ("upperArm_R", "foreArm_R"), ("foreArm_R", "hand_R"),
    ("thigh_L", "shin_L"), ("shin_L", "foot_L"),
    ("thigh_R", "shin_R"), ("shin_R", "foot_R"),
]


def setup_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE"
    sc.eevee.taa_render_samples = 16
    sc.view_settings.view_transform = "Standard"
    sc.render.resolution_x = 1400
    sc.render.resolution_y = 1860
    sc.eevee.taa_render_samples = 12
    sc.render.film_transparent = False
    sc.render.fps = 30
    w = bpy.data.worlds.new("w")
    sc.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.55, 0.56, 0.58, 1)
    bg.inputs[1].default_value = 0.55
    sun = bpy.data.objects.new("key", bpy.data.lights.new("key", "SUN"))
    sc.collection.objects.link(sun)
    sun.rotation_euler = (math.radians(58), math.radians(6), math.radians(-38))
    sun.data.energy = 3.2
    fill = bpy.data.objects.new("fill", bpy.data.lights.new("fill", "SUN"))
    sc.collection.objects.link(fill)
    fill.rotation_euler = (math.radians(72), 0, math.radians(145))
    fill.data.energy = 1.2
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
    meshes = [o for o in new if o.type == "MESH" and o.name != "Icosphere"]
    arm["src_name"] = arm.name
    arm.name = prefix + "_rig"
    for i, m in enumerate(meshes):
        m.name = prefix + ("_body" if i == 0 else f"_mesh{i}")
    if arm.animation_data:
        arm.animation_data.action = None
        for t in list(arm.animation_data.nla_tracks):
            t.mute = True
    return arm, meshes


def bone_dir(arm, bone, child):
    b = arm.data.bones[bone]
    c = arm.data.bones[child]
    v = c.head_local - b.head_local
    if v.length < 1e-6:
        return Vector((0, 1, 0))
    return v.normalized()


def build_correction(hero, knight):
    """Same correction as retarget_fix.py: q' = Cp^-1 * q * Cb."""
    ch = {}
    parent = {}
    for b in knight.data.bones:
        parent[b.name] = b.parent.name if b.parent else None
    for bone, child in PAIRS:
        if bone not in hero.data.bones or child not in hero.data.bones:
            continue
        if bone not in knight.data.bones or child not in knight.data.bones:
            continue
        do = bone_dir(knight, bone, child)
        dd = bone_dir(hero, bone, child)
        ch[bone] = do.rotation_difference(dd)
    corr = {}
    for bone in ch:
        cp = ch.get(parent.get(bone), Quaternion())
        corr[bone] = (cp, ch[bone])
    for side in ("_L", "_R"):
        for bone in ("hand" + side, "foot" + side):
            p = parent.get(bone)
            if bone in knight.data.bones and p in ch:
                corr[bone] = (ch[p], Quaternion())
    return corr


def add_helpers(arm):
    """Plate helpers for this review armature only. Does not limit the clip."""
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


def zero(arm):
    arm.data.pose_position = "POSE"
    if arm.animation_data:
        arm.animation_data.action = None
    for pb in arm.pose.bones:
        pb.rotation_mode = "QUATERNION"
        pb.rotation_quaternion = (1, 0, 0, 0)
        pb.location = (0, 0, 0)
        pb.scale = (1, 1, 1)


def apply_clip(hero, knight, corr, action, frame):
    zero(hero)
    zero(knight)
    hero.animation_data_create()
    hero.animation_data.action = action
    bpy.context.scene.frame_set(int(frame))
    bpy.context.view_layer.update()
    for pb in hero.pose.bones:
        name = pb.name
        if name not in knight.pose.bones:
            continue
        q = pb.rotation_quaternion.copy()
        if name in corr:
            cp, cb = corr[name]
            q = cp.inverted() @ q @ cb
        knight.pose.bones[name].rotation_quaternion = q
        # README: location only on hips/root. The body clip uses it; armor must follow.
        if name in ("hips", "root"):
            knight.pose.bones[name].location = pb.location.copy()
    bpy.context.view_layer.update()


def world_bounds(objs):
    pts = []
    for o in objs:
        for c in o.bound_box:
            pts.append(o.matrix_world @ Vector(c))
    mn = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    mx = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return mn, mx


def look(cam, target, yaw_deg, ortho):
    yaw = math.radians(yaw_deg)
    t = Vector(target)
    cam.location = t + Vector((math.sin(yaw) * 8, -math.cos(yaw) * 8, 0.2))
    cam.rotation_euler = (t - cam.location).to_track_quat("-Z", "Y").to_euler()
    cam.data.ortho_scale = ortho


def hip_world(arm):
    return arm.matrix_world @ arm.pose.bones["hips"].head


def pick_frame(action, bone_name, arm):
    """Frame in the action where this bone's rotation changes the most."""
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = action
    f0, f1 = action.frame_range
    best_f, best = int(f0), -1
    pb = arm.pose.bones.get(bone_name)
    if pb is None:
        return int(round((f0 + f1) * 0.5))
    for f in range(int(f0), int(f1) + 1, max(1, int((f1 - f0) / 12))):
        bpy.context.scene.frame_set(f)
        bpy.context.view_layer.update()
        ang = pb.rotation_quaternion.angle
        if ang > best:
            best, best_f = ang, f
    arm.animation_data.action = None
    return best_f


def render_pair(tag, hero_path, armor_path, clips, align_hips=False):
    sc, cam = setup_scene()
    hero, hero_meshes = import_glb(hero_path, "hero")
    # actions belong to the hero import
    src = hero.get("src_name", "")
    actions = {}
    for a in bpy.data.actions:
        name = a.name
        if src and name.endswith("_" + src):
            name = name[: -(len(src) + 1)]
        actions[name.split(".")[0]] = a
    knight, armor_meshes = import_glb(armor_path, "armor")
    # second import may have renamed actions; keep the first set
    corr = build_correction(hero, knight)
    add_helpers(knight)
    print(tag, "corr deg", {k: round(math.degrees(v[1].angle), 1) for k, v in corr.items() if v[1].angle > 0.01}, flush=True)
    print(tag, "actions", sorted(actions), flush=True)

    # rest both, then optional hip alignment of the HERO only (armor is not scaled or moved)
    zero(hero)
    zero(knight)
    bpy.context.view_layer.update()
    if align_hips:
        delta = hip_world(knight) - hip_world(hero)
        hero.location = hero.location + delta
        bpy.context.view_layer.update()
        print(tag, "hip align delta m", tuple(round(x, 3) for x in delta), flush=True)

    mn, mx = world_bounds(armor_meshes + hero_meshes)
    height = max(mx.z - mn.z, 0.5)
    center = (mn + mx) * 0.5
    ortho = height * 1.15
    tgt = Vector((center.x, center.y, mn.z + height * 0.48))

    for clip, bone in clips:
        act = actions.get(clip)
        if act is None:
            print("MISSING CLIP", clip, flush=True)
            continue
        frame = pick_frame(act, bone, hero)
        apply_clip(hero, knight, corr, act, frame)
        # reframe on the posed armor so a stride is not cropped
        mn, mx = world_bounds(armor_meshes)
        height = max(mx.z - mn.z, 0.5)
        center = (mn + mx) * 0.5
        ortho = max(height, mx.x - mn.x) * 1.2
        tgt = Vector((center.x, center.y, mn.z + height * 0.46))
        for view, yaw in (("front", 18), ("side", 92)):
            look(cam, tgt, yaw, ortho)
            path = f"{OUT}/{tag}_{clip}_f{frame}_{view}.png"
            sc.render.filepath = path
            bpy.ops.render.render(write_still=True)
            print("SHOT", path, flush=True)
        # shoulder / hip close-up on the action view
        if "upperArm_L" in knight.pose.bones:
            loc = knight.matrix_world @ knight.pose.bones["upperArm_L"].head
            look(cam, loc, 30, 0.85)
            path = f"{OUT}/{tag}_{clip}_f{frame}_shoulder.png"
            sc.render.filepath = path
            bpy.ops.render.render(write_still=True)
            print("SHOT", path, flush=True)


def main():
    which = "all"
    if "--" in sys.argv:
        which = sys.argv[sys.argv.index("--") + 1]
    hero_m = "/tmp/heroes/darius_voxel_noweapon.glb"
    hero_f = "/tmp/heroes/talia_voxel_main.glb"
    hero_r = "/tmp/heroes/rook_voxel.glb"
    before_m = "/tmp/krender/before/knight_male.glb"
    before_f = "/tmp/krender/before/knight_female.glb"
    after_m = "/workspace/www/proto3d/models/beth/equipment/knight_rig/knight_male.glb"
    after_f = "/workspace/www/proto3d/models/beth/equipment/knight_rig/knight_female.glb"
    male_clips = [("idle", "hips"), ("walk", "shin_L"), ("run", "shin_L"), ("attack", "upperArm_R")]
    female_clips = [("idle", "hips"), ("walk", "shin_R"), ("run", "shin_L"), ("attack1", "upperArm_R")]
    jobs = {
        "before_male": (hero_m, before_m, male_clips, False),
        "after_male": (hero_m, after_m, male_clips, False),
        "before_female": (hero_f, before_f, female_clips, True),
        "after_female": (hero_f, after_f, female_clips, True),
        "rook_after": (hero_r, after_m, [("run", "shin_L"), ("attack1", "upperArm_R")], True),
    }
    if which in jobs:
        render_pair(which, *jobs[which])
    else:
        for name, args in jobs.items():
            render_pair(name, *args)
    print("DONE")


if __name__ == "__main__":
    main()
