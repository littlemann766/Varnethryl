# Ashen Titan pool intro v2 (test 13) - staggered, no elbow flips
Files: ashentitan_volcano_glow.glb, ashentitan_volcano_glow_lod1.glb (same path, same scale; node scale 1.3362 in Godot = 28 m). All 12 original clips kept.
## `intro` 9.233 s, 30 fps, IN PLACE (game drives y10->26.8 over 0-3.5 s)
0-1.4 right arm reaches up out of the lava (shoulder/torso lead, weight shifts left) -> 2.0 right hand plants forward-right;
2.0-2.8 left arm rises and reaches over -> 3.3 left plants; 3.3-5.6 torso-led haul with R->L->centre weight shifts, elbows bend then lock;
6.1 right arm flings out first, left follows -> roar 6.6-8.0 (jaw open) -> settle 8.7-9.2.
Arms never move in sync. FK only (no IK poles), elbow one-way hinge 5-120 deg, quaternion continuity on every key; per-frame check: arm-vs-arm min gap 0.26 H (~7 m at 28 m), 0 elbow folds/inversions.
## `death_pool` 3.03 s, IN PLACE (new; use while he is in the lava instead of `death`)
Shudder + roar 0-0.7, sag 1.2, collapses forward 1.8-2.45 with arms flopped out ahead over the surface; hips stay put so chest/head stay above the lava (stage 1-2); final pose holds at 3.0.
