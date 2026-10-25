# Tripo batch 2 (user uploads user_1025.glb farmstead 48,385 tris; user_1025b.glb lighthouse 50,853 tris; one 4096 basecolor each)
Same pipeline as tripo/: centered X/Z, base y=0; `<name>.glb` source units, `_game` metres, `_lod1` ~50%/1024, `_lod2` ~20%/512, max 2048.
Farmstead x40 (barn doors ~3.5 m, house door ~2.2 m): farmhouse, barn_stable (welded mesh cut by plane x=-0.095, slice keeps UVs;
cut faces are open, place the two pieces together or hide the cut side), fence_paddock, yard_path (5-tri ground quad), farmstead_full.
Lighthouse x36 (tower ~31.6 m): lighthouse_tower, lighthouse_rock_island (rock, stairs, railings), lighthouse_full.
Manifest: tripo2_manifest.json. Renders: audit/tripo2/.

user_1025c.glb (untextured concept sheet): castle 2 of 4 cut out. backdrop_castle (70 m tall, 71.6x70x67.6 m, 8k/4k/1.6k tris, own 1024/512/256 texture built from card2 atlas crops: cream brick with warm emissive windows, grey stone, blue slate). prop_castle_model (0.6 m tabletop model, 4k/2k/800 tris, embedded varn_interiors atlas 2048/1024/512: stone walls, blue cones, gold tops). Contact: audit/tripo2/castle_contact_sheet.png
