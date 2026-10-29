# Ashen Titan world boss - voxel v1 (2026-10-29, review only - not for the build until the boss approves)
Source: handoff/godot/ashentitan_worldboss/ashentitan_worldboss.glb at HEAD (fists, knee fixes, arm clearance). The rig and all 42 clips are unchanged, including wb_emerge.
Cubes: 0.21 body / 0.094 head in model units, the same size relative to the body as the heroes' 1.8 cm / 0.8 cm cubes. Each cube is 100% on one bone.
Lava glow: kept as an emissive palette texture (*_vox_emis, Nearest filtering) on the Emission input.
Scale: the model is ~21.1 units tall; a node scale of ~5.4 gives ~114 m (same as the existing worldboss handoff).
Triangles: LOD0 128,964; LOD1 32,976 (0.42 / 0.19 cubes).
Godot 4.7.2 headless: 0 errors, 42 animations in both.
