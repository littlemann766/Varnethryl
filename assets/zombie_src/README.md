# Zombie source meshes (image-to-3D, unrigged)

These are raw meshes generated from the concept art on free, anonymous Hugging Face Spaces (no account, no token) on Nov 9, 2026. They are source material for rigging to the kael 21-joint skeleton and are not game-ready yet.

All files are a single textured mesh: Y-up, about 1.0 unit tall, facing +Z, with a 2048² base-colour texture and no normal map. The pose is baked in (hunched, arms slightly forward), not a T-pose or A-pose.

| File | Concept | Space | Tris | Notes |
|---|---|---|---|---|
| hooded_male/trellis2_raw.glb | ref_2 hooded male | microsoft/TRELLIS.2 (res 1024, seed 0, decimation 100k = space minimum, tex 2048) | 96,615 | Best result. Layered tattered cloak and tunic, hood, diagonal strap, belt, wrapped shins and boots. Has a metallic-roughness texture. The face is a gaunt sunken face, not a crisp skull, with no white eyes. |
| hooded_male/hooded_male_light.glb | ref_2 hooded male | trellis-community/TRELLIS (seed 0, simplify 0.95, tex 2048) | 13,887 | Same character, but blobbier, with a muddy texture and almost no face detail. Fallback or LOD reference. |
| ex_soldier/trellis2_raw.glb | ref_3 ex-soldier | microsoft/TRELLIS.2 (same settings) | 97,850 | Pauldron, arm plates, kneepad, red-stained tunic, long ragged cape. The chainmail is only painted into the texture. The face is blurry. |
| female_blue/trellis_raw.glb | ref_7 female, blue dress | trellis-community/TRELLIS | 14,225 | Blue dress with a jagged hem, sash belt, long dark hair, boots. Softer and blurrier than the concept, with a weak face. |

Each folder also has crop.png (the background-removed concept used as input) and *_preview_compare.png, which shows the concept followed by front, 3/4, side, back and face renders.

Known issues to fix while rigging:
- The TRELLIS.2 meshes are about 97k triangles and need reducing to the 15–20k full-body budget.
- Faces and hands are weak.
- The baked pose needs cleanup.
- There is no normal map, so one would need baking if wanted.
