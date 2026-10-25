# Tripo batch 2 (user uploads user_1025.glb farmstead 48,385 tris; user_1025b.glb lighthouse 50,853 tris; one 4096 basecolor each)
Same pipeline as tripo/: centered X/Z, base y=0; `<name>.glb` source units, `_game` metres, `_lod1` ~50%/1024, `_lod2` ~20%/512, max 2048.
Farmstead x40 (barn doors ~3.5 m, house door ~2.2 m): farmhouse, barn_stable (welded mesh cut by plane x=-0.095, slice keeps UVs;
cut faces are open, place the two pieces together or hide the cut side), fence_paddock, yard_path (5-tri ground quad), farmstead_full.
Lighthouse x36 (tower ~31.6 m): lighthouse_tower, lighthouse_rock_island (rock, stairs, railings), lighthouse_full.
Manifest: tripo2_manifest.json. Renders: audit/tripo2/.
