# Ashen Titan minions — progress (ET)
- 14:35 found minions: wb_ash_fiend (2.45 m humanoid, static, no rig) + wb_ember_wisp (1.3 m floater, static, no rig). Spawned by godot-voxel/scripts/world_boss.gd _spawn_adds (crystal break + every 45 s, max 12, 3 fiend + 2 wisp, freed after 90 s). No AI/movement: fiends stand still, wisps bob/spin.
- workdir /workspace/minions (own temp). plan: rig_fiend.py -> rt_fiend.py (UAL1+UAL2) -> check -> export; wisp: rig_wisp.py keyframed clips.
- 14:30 fiend rig (heat weights + nearest-bone for 258 loose verts), rt_fiend.py (UAL1+UAL2, timewarp strikes <=30deg/frame), post.py (despike, ground, claw-ground lift, events). checks: steps<=37deg, arm-leg min gap 19cm. preview rendering work/pv_fiend
- 14:38 wisp rig_wisp.py (7 rigid shard bones + soft body/tail/crown weights, keyframed clips) ok; checks steps<=20deg, death lands at -2.0 (hover)
- 14:42 exported 4 GLBs to varn-core/handoff/godot/ashentitan_minions; Godot 4.7.2 headless import 0 errors/warnings (minions/gtest). previews rendering work/pv_fiend, work/pv_wisp
