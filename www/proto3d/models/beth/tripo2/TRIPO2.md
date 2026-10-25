# Tripo batch 2 (user uploads user_1025.glb farmstead 48,385 tris; user_1025b.glb lighthouse 50,853 tris; one 4096 basecolor each)
Same pipeline as tripo/: centered X/Z, base y=0; `<name>.glb` source units, `_game` metres, `_lod1` ~50%/1024, `_lod2` ~20%/512, max 2048.
Farmstead x40 (barn doors ~3.5 m, house door ~2.2 m): farmhouse, barn_stable (welded mesh cut by plane x=-0.095, slice keeps UVs;
cut faces are open, place the two pieces together or hide the cut side), fence_paddock, yard_path (5-tri ground quad), farmstead_full.
Lighthouse x36 (tower ~31.6 m): lighthouse_tower, lighthouse_rock_island (rock, stairs, railings), lighthouse_full.
Manifest: tripo2_manifest.json. Renders: audit/tripo2/.

user_1025c.glb (untextured concept sheet): castle 2 of 4 cut out. backdrop_castle (70 m tall, 71.6x70x67.6 m, 8k/4k/1.6k tris, own 1024/512/256 texture built from card2 atlas crops: cream brick with warm emissive windows, grey stone, blue slate). prop_castle_model (0.6 m tabletop model, 4k/2k/800 tris, embedded varn_interiors atlas 2048/1024/512: stone walls, blue cones, gold tops). Contact: audit/tripo2/castle_contact_sheet.png

2026-10-25 FIX (v1.5.33 "farmhouse cut in half"): the farmhouse and barn are one welded building on the card, and the plane split left a slice of the house
on the barn piece (that slice is what the game showed). farmhouse_game* is now the WHOLE farmhouse+barn (34.3 x 14.6 x 24.4 m, from farmstead_full_game
minus fence_paddock and 2 stray rail faces, centred X/Z, base y=0, +Z front), 47,678 / 23,112 / 9,245 tris, with _col (house door 1.4x2.3 at (-1.9,0.9,10.9),
barn opening 4x5 at (5.2,0,10.2)). barn_stable_game* is a deprecated duplicate of the same building: place only one. Script: audit/cardstyle/tools/v2/prep_farmstead.py
