# Ashen Titan voxel - sealed (2026-10-29), from ashentitan_wb_voxel @ c7ad026 (review only)
- tools/voxel_v3/seal.py: faces between cubes on different bones are kept (no see-through joints); 153 / 75 isolated stray cubes removed.
- Tris: LOD0 151,232 (was 128,964); LOD1 43,348 (was 32,976).
- Rig, materials (palette + emissive lava) and all 42 clips unchanged.
- Ground contacts unchanged: measure.py lowest points per clip/frame match the c7ad026 GLB within 0.001 (43,569 values).
- Arm-leg (check1.py, every frame, S=0.21): 0 frames on all 42 clips, LOD0 and LOD1.
- Godot 4.7.2 headless import: 0 errors.
