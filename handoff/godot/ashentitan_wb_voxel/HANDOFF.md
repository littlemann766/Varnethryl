# Ashen Titan world boss - voxel v1 (2026-10-29, review only - not for the build until the boss approves)
Source: handoff/godot/ashentitan_worldboss/ashentitan_worldboss.glb at HEAD (fists, knee fixes, arm clearance). The rig and all 42 clips are unchanged, including wb_emerge.
Cubes: 0.21 body / 0.094 head in model units, the same size relative to the body as the heroes' 1.8 cm / 0.8 cm cubes. Each cube is 100% on one bone.
Lava glow: kept as an emissive palette texture (*_vox_emis, Nearest filtering) on the Emission input.
Scale: the model is ~21.1 units tall; a node scale of ~5.4 gives ~114 m (same as the existing worldboss handoff).
Triangles: LOD0 128,964; LOD1 32,976 (0.42 / 0.19 cubes).
Godot 4.7.2 headless: 0 errors, 42 animations in both.

## v2 (2026-10-29, review only — not for the build until the boss approves)
- wb_walk: Quaternius UAL1 Walk_Loop (CC0) retargeted, 0.444x playback, 3.0 s cycle (footsteps L 0.3, R 1.733), heavier dip/sway/lean, ball-locked feet (0 slide). Root motion 30.2 m/s at 114 m (was 2.96 m/s) — node speed must change if root motion is stripped.
- Ground contact (IK, held 4 frames, lowest point -0.01 m): wb_stomp/wb_swat_knee R foot 2.4 s; wb_ritual_fissure_release both fists 0.9 s; wb_ritual_lavawave_release both fists 1.3 s; wb_swat_forearm_L/R forearm 1.6 s. Event times unchanged. Same in ashentitan_worldboss(.glb/_lod1).
- Scripts: tools/titan_voxel/v2/.
