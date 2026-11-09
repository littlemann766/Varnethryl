# Zombie characters v3

Built from the image-to-3D meshes in `assets/zombie_src/` (TRELLIS / TRELLIS.2, commit `9c26ce3`). The silhouette, tattered cloth, strap, pauldron, and source texture are kept. These are not a redesign of v1 or v2.

## Files

| File | What it is |
|---|---|
| `hooded_male.glb` | Skinned full body, 16,999 tris |
| `ex_soldier.glb` | Skinned full body, 17,000 tris |
| `female_blue.glb` | Skinned full body, 14,225 tris (source count, not decimated) |
| `*_far.glb` | Unskinned crowd mesh. Hood 809 tris, soldier 862, female 400 |
| `previews/*_impostor.png` | RGBA card of the bind pose, for a camera-facing quad |
| `previews/` | Front, three-quarter, face, walk, bite, death, concept comparison, Godot group |

Each full GLB is one mesh, one material, and the 21-joint humanoid (`root`, `hips`, `spine`, `chest`, `cape`, `neck`, `head`, `shoulder_*`, `upperArm_*`, `foreArm_*`, `hand_*`, `thigh_*`, `shin_*`, `foot_*`). Clips are the kael set: `idle`, `walk`, `run`, `attack2` (bite), `hit`, `death`, plus the other kael clips that were on the same armature.

Scale is 1.72 m, feet on the ground, Y-up. The female was yawed 180° after the first export so her face points the same way as the hooded male.

## How to instance

```gdscript
var body := load("res://assets/zombie_v3/hooded_male.glb").instantiate()
var anim := body.find_child("AnimationPlayer", true, false) as AnimationPlayer
anim.play("walk")
```

Far crowd: take the mesh inside `*_far.glb` and put it on a `MultiMeshInstance3D`. The impostor PNGs are a single bind-pose card with a transparent background.

## Godot 4.7 Forward Mobile, software Vulkan

Measured with Godot 4.7 stable, `--rendering-method mobile`, `--rendering-driver vulkan`, on lavapipe (`llvmpipe`, not a phone):

- 16 skinned bodies (6 hooded, 5 soldier, 5 female) playing `walk`, `attack2`, `death`, `idle`, and `hit`
- 72 far instances (24 of each character)
- About **52 ms per frame** (roughly 19 fps) on this CPU rasterizer
- Full-body triangles in that shot: about 258,000. Far triangles: about 50,000

The clips are present and the bodies deform. See `previews/group16.png`.

## Honest limits

The source meshes are open shells. Almost every tatter edge is a boundary, so they will not collapse to a clean 15–20k the way a closed body does, and a heat-map skin fails on them.

- Decimation kept the source UVs and the 2048 albedo. The two males landed at 17k after a texture-preserving collapse plus a second pass. Their far meshes stop around 800 tris; pushing lower deletes the tatters. The female stayed at 14,225.
- There is no baked normal map. TRELLIS.2 supplied albedo and a metallic-roughness map (hood and soldier). The female source has albedo only. A small pale-eye paint was applied on the hood and soldier atlases; it does not turn the generated face into the concept skull.
- The face read is the generated face. The hood is the closest. The soldier face is soft and breaks into facets up close. The female face is pale and readable at game distance, not a sharp skull.
- The baked pose has the arms slightly forward. The skeleton rest was posed into that hang, then the kael clips were retargeted as deltas from the kael T-pose. Driving the arms, shoulders, and cape with the full clip still tears the open cloth, so those bones stay on the bind hang. Legs, spine, neck, and head play `walk`, `attack2`, and `death`. A walk frame shows a step. A death frame drops the body, and the tatter shell shreds while it does.
- The soldier pauldron region is weighted only to `shoulder_L`, and a knee region only to `shin_R`. The regions are boxes on the mesh, so some nearby cloth is rigid with them.
- Hands are the generated hands. They were not resculpted.

`hooded_male_light.glb` was not used. The TRELLIS.2 hood is the one in `hooded_male.glb`.
