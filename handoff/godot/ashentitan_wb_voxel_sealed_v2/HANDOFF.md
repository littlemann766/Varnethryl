# Ashen Titan voxel, sealed v2 (test 32, 2026-10-30): single-frame hand snaps removed
- Source: ashentitan_wb_voxel_sealed (same files as godot-voxel 54e17f1). Mesh, rig, materials and all 42 clips are the same except the hand_L/hand_R rotation curves in 3 clips.
- Fix (tools/voxel_v3/t32/cfix.py, CYC=0 BONES=hand_L,hand_R LIM=40): smoothing on the hand bone only, edges clamped (not looped), applied only until the largest frame-to-frame change is 40° or less.
  - wb_ritual_fissure_release: hand_L 112°→34°, hand_R 92°→32°
  - wb_swat_forearm_L: hand_L 88°→39°
  - wb_swat_forearm_R: hand_R 99°→29°
- Hand bone heads (wrists) don't move, so foot and wrist ground contact and the worldboss_events.json timing are unchanged. The fist tip moves at most 6 cm at the contact frames (the titan is about 15 m tall), and its tip height changes by 4 cm or less.
- Arm-leg (check1): 0 on all 4 checked clips (including wb_stomp), LOD0 and LOD1. LOD1 got the same actions copied from LOD0 (tools/lodcopy.py).
