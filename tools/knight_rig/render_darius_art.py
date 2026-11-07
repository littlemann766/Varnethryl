"""Render the exported Darius armor. Review only.

Imports the fitted GLBs and plays the clips stored in those files.
Nothing here aims bones or drops keys.
"""
import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(__file__))
import render_fitted as R

OUT = os.environ.get(
    "KNIGHT_FIT_OUT",
    "/workspace/www/proto3d/models/beth/equipment/knight_rig/fitted_heroes/stills",
)
BODY = "/workspace/www/proto3d/models/beth/equipment/knight_rig/fitted_heroes/darius/darius_body_equipped.glb"
ARMOR = "/workspace/www/proto3d/models/beth/equipment/knight_rig/fitted_heroes/darius/darius_armor_fit.glb"
SOURCE = "/tmp/heroes/darius_voxel_noweapon.glb"
os.makedirs(OUT, exist_ok=True)


def clip_name(action):
    key = action.name.split("|")[-1]
    key = key.replace("_Darius_Rig", "").replace("_knight_rig", "")
    return key.split(".")[0]


def import_with_actions(path):
    before_obj = set(bpy.data.objects)
    before_act = set(bpy.data.actions)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before_obj]
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
    acts = {}
    for a in bpy.data.actions:
        if a in before_act:
            continue
        acts.setdefault(clip_name(a), a)
    if arm and arm.animation_data:
        arm.animation_data.action = None
        for tr in arm.animation_data.nla_tracks:
            tr.mute = True
    return arm, meshes, acts


def play(arm, action, frac):
    R.zero(arm)
    arm.animation_data_create()
    arm.animation_data.action = action
    f0, f1 = [int(round(x)) for x in action.frame_range]
    f = int(round(f0 + (f1 - f0) * frac))
    bpy.context.scene.frame_set(f)
    bpy.context.view_layer.update()
    return f


def main():
    sc, cam = R.setup()
    hero, hm, hacts = import_with_actions(BODY)
    arm, am, aacts = import_with_actions(ARMOR)
    for m in hm:
        if len(m.data.vertices) < 800 or "under" in m.name.lower():
            m.hide_render = True
    print("body", [m.name for m in hm], "armor", [m.name for m in am], flush=True)
    print("hero clips", sorted(hacts), "armor clips", sorted(aacts), flush=True)
    missing = [k for k in ("idle", "run", "attack") if k not in hacts or k not in aacts]
    if missing:
        raise RuntimeError("missing clips " + " ".join(missing))

    def shot(name, clip, frac, yaw, ortho, bone):
        play(hero, hacts[clip], frac)
        f = play(arm, aacts[clip], frac)
        # Both share one scene frame. Set the frame once after both actions
        # are assigned, or the second play resets the first armature's eval
        # only if we update. Re-assign and set frame together.
        hero.animation_data.action = hacts[clip]
        arm.animation_data.action = aacts[clip]
        bpy.context.scene.frame_set(f)
        bpy.context.view_layer.update()
        if bone and bone in arm.pose.bones:
            t = R.world_head(arm, arm.pose.bones[bone])
        else:
            t = R.world_head(hero, hero.pose.bones["hips"])
            t = Vector((t.x, t.y, t.z + 0.28))
        R.shot(sc, cam, os.path.join(OUT, name), t, yaw, ortho, 900, 1200)
        print("shot", name, "frame", f, flush=True)

    quick = os.environ.get("KNIGHT_QUICK") == "1"
    shots = [
        ("darius_art_idle_front.png", "idle", 0.0, 18, 2.15, None),
        ("darius_art_helm.png", "idle", 0.0, 24, 0.62, "head"),
        ("darius_art_attack_f1.png", "attack", 0.35, 28, 2.25, None),
        ("darius_art_run_f1.png", "run", 0.40, 24, 2.2, None),
        ("darius_art_elbow.png", "attack", 0.40, 70, 0.85, "foreArm_R"),
        ("darius_art_knee.png", "run", 0.45, 80, 0.85, "shin_L"),
        ("darius_art_wrist.png", "idle", 0.0, 30, 0.48, "hand_L"),
    ]
    if not quick:
        shots = [
            ("darius_art_idle_front.png", "idle", 0.0, 18, 2.15, None),
            ("darius_art_idle_side.png", "idle", 0.5, 100, 2.15, None),
            ("darius_art_idle_back.png", "idle", 0.0, 198, 2.15, None),
            ("darius_art_run_f0.png", "run", 0.0, 18, 2.2, None),
            ("darius_art_run_f1.png", "run", 0.33, 24, 2.2, None),
            ("darius_art_run_f2.png", "run", 0.66, 70, 2.2, None),
            ("darius_art_attack_f0.png", "attack", 0.0, 18, 2.2, None),
            ("darius_art_attack_f1.png", "attack", 0.35, 28, 2.25, None),
            ("darius_art_attack_f2.png", "attack", 0.70, 80, 2.25, None),
            ("darius_art_helm.png", "idle", 0.0, 24, 0.62, "head"),
            ("darius_art_shoulder.png", "idle", 0.0, 40, 0.7, "shoulder_L"),
            ("darius_art_elbow.png", "attack", 0.40, 70, 0.85, "foreArm_R"),
            ("darius_art_knee.png", "run", 0.45, 80, 0.85, "shin_L"),
            ("darius_art_wrist.png", "idle", 0.0, 30, 0.48, "hand_L"),
        ]
    for name, clip, frac, yaw, ortho, bone in shots:
        shot(name, clip, frac, yaw, ortho, bone)

    # Before: the source hero, untouched, at rest. After: the exported pair.
    src, sm = R.import_glb(SOURCE)
    R.zero(src)
    bpy.context.view_layer.update()
    R.show(hm, False)
    R.show(am, False)
    R.show(sm, True)
    t = R.world_head(src, src.pose.bones["hips"])
    t = Vector((t.x, t.y, t.z + 0.28))
    R.shot(sc, cam, os.path.join(OUT, "darius_art_before.png"), t, 18, 2.15, 900, 1200)
    R.show(sm, False)
    R.show(hm, True)
    R.show(am, True)
    for m in hm:
        if len(m.data.vertices) < 1000 or "under" in m.name.lower():
            m.hide_render = True
    hero.animation_data.action = hacts["idle"]
    arm.animation_data.action = aacts["idle"]
    bpy.context.scene.frame_set(0)
    bpy.context.view_layer.update()
    R.shot(sc, cam, os.path.join(OUT, "darius_art_after.png"), t, 18, 2.15, 900, 1200)
    print("DONE", flush=True)


if __name__ == "__main__":
    main()
