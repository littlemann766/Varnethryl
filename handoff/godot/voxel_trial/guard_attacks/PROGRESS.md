# guard_attacks progress (Lucian)
- Base: test 34 guard as shipped in /workspace/godot-voxel/voxel/town_guard_voxel{,_lod1,_lod2}.glb (capes_v4 / test 26 model, untouched since; test 34 did not change the guard). Existing clips attack/idle/run/walk kept as-is.
- Existing attack: one 25-frame mace chop, no wind-up hold, shield arm swings out wide (L arm 35°), no hit frame data.
- Pipeline: tools/guard_attacks/run_all.sh (retarget_attacks.py from mocap/retarget.py + foot lock; despike.py; handclear.py; armfix_guard.py from tools/capes/armfix34.py; motion_checks.py; voxel_v3/check1.py).
- Scratch: /workspace/ga_tmp (delete when done).
- 15:16 EDT: base switched to voxel_trial/armfix35/town_guard_voxel{,_lod1,_lod2}.glb (walk/run arm clipping fixed). retarget now sets scene fps=30 BEFORE the glb import (24 fps load bug). Clip set: attack_slash, attack_backhand, attack_overhead, attack_shield_bash (UAL1 Punch_Jab with shield arm), block, guard_stance, combat_idle, hit.
- 16:20 EDT: done; outputs, checks, events, preview mp4 committed. Scratch /workspace/ga_tmp deleted.
- 2026-11-01 00:40 EDT cleanup pass (scratch /workspace/ga2/v5): swingcap_guard.py (run/walk arm-out 30) -> armfix_guard (PASS2, ABMAX16, GRAB0) -> fixsnap2.py (frame-evaluated snap slerp; fixes run fr5 forearm flip) -> handclear2.py (wrist re-aim of mace, iterate + exact pass). Interim: LOD0 overhead 0, run 1 frame; LOD1 overhead 1, run 0; walk/run arm-out 30.
- 01:10 EDT: cleanup outputs installed + committed (360d289); Godot 0 err. Preview re-render running.
