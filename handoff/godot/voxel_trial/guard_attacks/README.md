# Town guard melee set (Lucian) — base: voxel_trial/armfix35/town_guard_voxel{,_lod1,_lod2}.glb
Drop-in replacements for res://voxel/town_guard_voxel*.glb. Existing attack/idle/walk/run are carried over from armfix35 unedited (lengths match: walk 1.333 s, run 0.9 s). Loaded at 30 fps.

New clips (30 fps; hit frames in guard_attacks.events.json):
| clip | s | source (Quaternius CC0) | hit frame |
|---|---|---|---|
| attack_slash | 1.70 | UAL2 Sword_Regular_A + A_Rec | 15 |
| attack_backhand | 1.83 | UAL2 Sword_Regular_B + B_Rec | 13 |
| attack_overhead | 2.03 | UAL1 Sword_Attack | 22 |
| attack_shield_bash | 1.10 | UAL1 Punch_Jab (shield arm) | 12 |
| block | 0.83 | UAL2 Shield_OneShot | - |
| guard_stance (loop) | 2.50 | UAL2 Idle_Shield_Loop | - |
| combat_idle (loop) | 1.67 | UAL1 Sword_Idle | - |
| hit | 0.67 | UAL1 Hit_Chest | - |
Wind-up/strike slowed (x0.35-0.75) so the wind-up reads; lower body damped (hips drop <= 7 cm), feet locked flat; mace attacks keep the shield up in front.

Checks (checks/): Godot 4.7.2 headless import 0 errors, 1 skeleton, 12 clips, all LODs. No single-frame snaps in the new clips. Arms out <= 30.2 deg. Wrist twist <= 60 deg (the old bug was 110-130). Cape in body 0 everywhere.
Arms in legs (frames over 24 voxels): LOD2 0. LOD1: overhead 3, backhand 1, hit 1. LOD0: overhead 9 (up to 825 voxels; the mace passes the thigh at the end of the swing), hit 6, slash 4, backhand 2. The game uses LOD1.
Not checked: whether the mace actually connects with targets in game.

## For Lucky (npc/town_guards.gd, not edited)
- It calls play_attack("attack",1.3) and applies _strike() at once. Rotate through attack_slash/backhand/overhead/shield_bash and apply damage at events hit_frame/30/speed. Set SWING to at least duration/speed.
- Use combat_idle while in reach and waiting, guard_stance/block when a monster attacks, and hit when g.hp drops.
- Base-model issues not touched: armfix35 run has an 83 deg RightForeArm snap at frame 5 (LOD2: frames 7 and 16), and run arms reach 36 deg, walk arms 34.6 deg.

## Cleanup pass (2026-11-01, Lucian)
Fixed only the frames that clipped; key timing, clip lengths, and hit frames are unchanged. Capes untouched.
- Arm/mace in legs (frames over 24 voxels): LOD1 overhead 3->0, backhand 1->0, hit 1->0; LOD0 overhead 9 (825 voxels)->0, hit 6->0, slash 4->0, backhand 2->0; LOD2 stays 0. Run and walk 0 on all LODs.
- Run frame-5 RightForeArm flip (83 deg) is fixed. LOD2 run flips at frames 7 and 16 are also fixed.
- Arm swing out: run 36.1->30.1, walk 34.6->30.3 (LOD0/1/2).
- Method: swingcap_guard.py -> armfix_guard.py -> fixsnap2.py -> handclear2.py (wrist re-aim of the mace on clipping frames).
- Residual: overhead right arm out reaches 39 deg (LOD0) / 43 deg (LOD1) at the end of the swing to clear the thigh. The LOD1 run has wrist steps of 42-56 deg at frames 2 and 19, and the LOD2 backhand has a 37 deg wrist step at frame 39.

## Shield fix (2026-11-01)
- Cause: the shield's voxels are bound to LeftHandThumb3. In the rest pose the shield is upright (long axis 4.7 deg from vertical) and faces forward, so the bind and rest pose are fine. The clips roll it, because the retargeted Quaternius hand and thumb rotations don't account for a shield. Even armfix35 had the shield tilted: attack 53 deg, run 63 deg. Our new clips were worse: combat_idle 78, guard_stance 82, block 109, slash 82, backhand 78 and bash 123 deg (long axis off vertical, median).
- Fix: shieldfix.py re-keys LeftHandThumb3 every frame so the shield stands upright with its face forward (relative to the hips). Only on frames where an upright forward shield would go into the legs (idle, walk, run, hit, the end of the overhead) does it turn the face out to the side or tilt the bottom out. The change is spread over neighbouring frames and wraps around on loops. On LOD0 the left arm was also moved on overhead frame 23. Shield frame-to-frame steps are 35 deg or less.
- After: the long axis is 0 deg from vertical in guard_stance, combat_idle, block, bash, slash and backhand, and the face is within 0-8 deg of forward. Arm/shield-in-leg is 0 on every LOD; capes are unchanged; timing is unchanged. See checks/shield_before_after.png.
