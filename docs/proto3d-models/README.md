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
