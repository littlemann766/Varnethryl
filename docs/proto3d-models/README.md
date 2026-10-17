# VARNETHRYL 3D hero prototypes (Beth)
11 procedural low-poly heroes built from the boss's character sheets (Orin Ashlance and Lady Elira intentionally skipped).
- Models: `www/proto3d/models/<id>.glb` (370-530 KB each): aldric, darius, selene, seraphine, talia, finn, brynn, mirelle, nyx, vesper, thorne.
- Rig: named Bone node hierarchy (root > hips > spine > chest > neck > head; shoulder/upperArm/foreArm/hand _L/_R; thigh/shin/foot _L/_R; `cape`). Parts are RIGID (parented to bones), not skinned. Baked clips: `idle`, `walk`.
- Hand sockets: weapons/shields/books are children of `hand_R`, `hand_L`, `foreArm_L` or `hips`.
- Viewer: `www/proto3d/viewer.html` (serve `www/`; buttons for each hero, idle/walk, spin).
- Rebuild: `python3 tools/export_proto3d_models.py [id...]`; render + contact sheets: `python3 tools/render_proto3d.py`; walk strip: `tools/walk_strip.py out.png ids...`.
- Source: `www/proto3d/chars_core.js` (kit) and `chars.js` (the 11 builds). three r186 + GLTFExporter/Loader vendored in `www/proto3d/vendor/`.
- Contact sheets: `contact_1..4.png` (sheet front vs 3D front, 3/4, back).
Caveats: prototype blockiness, no faces/textures (flat colour materials), robes are rigid cylinders so legs clip in walk, lion/fleur emblems are crude geometry, arms with held weapons barely swing.

## v2 (Lucky) - branch lucky-3d-v2
13 heroes (Lady Elira added from sheet x5; x4 is a second Orin sheet). Changes: smooth-shaded higher-segment geometry; procedural cloth/leather/brushed-steel/hair/fur textures (www/proto3d/texgen.js, JPEG in GLB); painted faces (eyes, brows, lips, per-hero eye colour, scar, beard, elf ears) and a hair system with a real hairline and tapered locks; heraldry as decals - the Aldric lion and fleur-de-lis are derived from the Sir Aldric sheet (tools/derive_emblems.py -> www/proto3d/tex/emb_*.png), others (sun, snow, gear, spiral, cross, ornate, sprig) drawn on canvas; capes carry conforming decals; skirts/robes are front+back panels on bones (skirtF*/skirtB*) that swing with the legs so legs no longer cut through; plate armour got fauld bands, ridge, gorget, knee/ankle trim, sabatons, finger plates; new bow and quiver props. Still rigid bones (not skinned). Compare sheets: docs/proto3d-models/v2/compare_*.png. Rebuild: python3 tools/export_proto3d_models.py (textures are generated in-browser, then embedded).
