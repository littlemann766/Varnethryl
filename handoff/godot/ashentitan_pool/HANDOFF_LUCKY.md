# Ashen Titan pool intro v3 (test 13) - staggered, no elbow flips
Files: ashentitan_volcano_glow.glb, ashentitan_volcano_glow_lod1.glb (same path, same scale; node scale 1.3362 in Godot = 28 m). All 12 original clips kept.
## v3 changes
- Plants solved onto the LOCAL lava surface per key, assuming your rise is LINEAR y=10+16.8*t/3.5 over 0-3.5 s (node scale 1.3362, lava y 38). Palms down, shoulder shrugs as the weight loads. Palm height error <0.05 m at 2.0/2.3/2.8/3.05/3.3/3.55 s, <0.7 m at 4.1/4.6. If your rise is eased, send the curve and I re-solve.
- Right arm already up through the surface from t=0 (fingertips ~5 m above the lava over 0-0.75 s).
- Overhead -> reach -> plant now 1.2 -> 1.6 -> 2.0 s (no 0.25 s pop).
## `intro` 9.233 s, 30 fps, IN PLACE (game drives y10->26.8 over 0-3.5 s)
0-1.4 right arm reaches up out of the lava (shoulder/torso lead, weight shifts left) -> 2.0 right hand plants forward-right;
2.0-2.8 left arm rises and reaches over -> 3.3 left plants; 3.3-5.6 torso-led haul with R->L->centre weight shifts, elbows bend then lock;
6.1 right arm flings out first, left follows -> roar 6.6-8.0 (jaw open) -> settle 8.7-9.2.
Arms never move in sync. FK only (no IK poles), elbow one-way hinge 5-120 deg, quaternion continuity on every key; per-frame check: arm-vs-arm min gap 0.26 H (~7 m at 28 m), 0 elbow folds/inversions.
## `death_pool` 3.03 s, IN PLACE (new; use while he is in the lava instead of `death`)
Shudder + roar 0-0.7, sag 1.2, collapses forward 1.8-2.45 with arms flopped out ahead over the surface; hips stay put so chest/head stay above the lava (stage 1-2); final pose holds at 3.0.

## v8 (2026-10-25 2:00 PM ET)
- intro (9.233 s): planted hands pinned per frame to the lava surface (linear rise y 10->26.8 over 0-3.5 s, scale 1.3362, lava y 38): R 2.0-5.1 s, L 3.3-5.1 s, max height error 0.028 m, slow slide <=1.15 m over the haul. Note: the hands are sculpted fists in the mesh (finger weights only on the tips), so finger keys cannot fully open them.
- New attack clips (hit time; fist position in game metres, x, z-out, y height above the plate):
  eruption_slam 3.0 s, impact 1.288 s, both fists at (+-6.1, 16.7 out, plate 12.2) -> spawn the wave here
  magma_sweep 2.733 s, hit 0.976 s; boulder_hurl 3.6 s, rip 1.224 s, release 2.383 s
  attack1 2.2 s hit 1.2 (R fist -6.0, 17.1 out, 12.1); attack2 2.0 s hit 1.1 (L 6.7, 17.1, 12.4); attack3 2.4 s hit 1.3
- death_pool and the 12 original clips unchanged.
