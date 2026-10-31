# Town guard melee set (Lucian) — base: voxel_trial/armfix35/town_guard_voxel{,_lod1,_lod2}.glb
Drop-in replacements for res://voxel/town_guard_voxel*.glb. Existing attack/idle/walk/run are byte-for-byte the armfix35 clips (same lengths: walk 1.333 s, run 0.9 s). Loaded at 30 fps.

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
