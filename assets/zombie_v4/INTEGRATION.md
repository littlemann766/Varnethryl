# Zombie characters v4

Built from the image-to-3D meshes in `assets/zombie_src/` (TRELLIS.2 for the two males, TRELLIS for the female). v3 is unchanged.

The mesh is moved onto the kael rest before it is skinned. A copy of the kael armature is posed into the baked hunch, heat-weighted through a voxel, and applied so the shell sits on the kael bind pose. The exported rig is a fresh `voxel/kael_voxel.glb` armature. `characters/kael_lod1.glb` also contains clips, and applying a rest pose corrupts those curves, so the export uses the voxel actions (the ones with the full curve set).

## Files

| File | Tris | Notes |
|---|---|---|
| `hooded_male.glb` | 38,854 | Skinned. Albedo, tangent normal, ORM at 2048. |
| `ex_soldier.glb` | 38,791 | Skinned. Albedo, tangent normal, ORM at 2048. |
| `female_blue.glb` | 12,729 | Skinned. Source is 14,225 tris, not a TRELLIS.2 mesh, so it was not raised to the 35–45k budget. Albedo and a tangent normal. No ORM on the source. |
| `*_far.glb` | 939 / 872 / 850 | Unskinned crowd mesh, same textures embedded. |
| `textures/` | 2048² | Albedo, tangent-space normal, and ORM (males). |
| `previews/` | | Front, three-quarter, face, walk, bite, death, concept comparison, group of 16. |

Each full GLB is one mesh, one double-sided material, and the kael skeleton. The skin can carry the extra kael cape joints; the shell is not weighted to the cape bone (that bone whips cloth on death). Influences are normalized and limited to 4. Clips are the kael set: `idle`, `walk`, `run`, `attack1`, `attack2`, `attack3`, `hit`, `death`, plus the fly and skill clips that ship on the same armature.

Scale is about 1.72 m, feet on the ground, Y-up, facing the same way as kael.

## How to instance

```gdscript
var body := load("res://assets/zombie_v4/hooded_male.glb").instantiate()
var anim := body.find_child("AnimationPlayer", true, false) as AnimationPlayer
anim.play("walk")
```

`attack2` is the bite clip. There is no separate bite or bite-windup clip on this skeleton. Far crowd: use the mesh inside `*_far.glb` on a `MultiMeshInstance3D`.

## Godot 4.7 Forward Mobile, software Vulkan

Measured with Godot 4.7 stable, `--headless --rendering-method mobile --rendering-driver vulkan`, on lavapipe (not a phone). 16 skinned bodies, mixed across the three characters, playing `walk`:

- **6.90 ms per frame** over 90 frames after a short warmup

That scene is only the bodies. It is not the town, and it does not include the far meshes. The importer's vertex-array length divided by 3 is not the triangle count (it reported 25,561 / 27,904 / 3,618). The triangle counts in the table above are from the mesh that was exported.

## Honest limits

- Decimation is a texture-preserving quadric collapse from the unposed high mesh (about 84k after cleanup), then a Blender collapse to 40k. The open tatter shell will not collapse cleanly below that without eating the cloak, which is why the second stage is a plain collapse rather than another boundary-locked pass. The female stays near her source count.
- The tangent normal is baked from the pre-decimation surface onto the low UVs (a headless Cycles bake in this Blender writes an empty image, so the bake is a closest-face normal transfer). It is a real normal map, and it is subtle: at ~39k tris most of the shape is already in the mesh. The face still reads faceted up close. It is the generated face, not the concept skull.
- The albedo is the generated texture. It is dark (channel means around 30–45 / 255). The males also embed the TRELLIS.2 metallic-roughness map. The female source has no ORM; roughness is 0.72 and metallic is 0.
- A few small shells from the source float beside the shoulders. They are disconnected tatters, not a second character.
- Hands do move. On `attack2` frame 16 the hand-weighted vertices travel about 0.62 m (hood), 0.68 m (soldier), and 0.74 m (female). The sleeve is only partly on the arm bones, because a wider arm tube drags the cloak out into horizontal wings. Walk shows a step and a small arm change. It is not a full swing of the whole cloak-covered arm, and the bite still does not read as a hand at the mouth.
- Edge-length ratio versus rest is not under 1.6 everywhere. After the weight pass and after deleting faces that still exceeded 2.2, the worst remaining ratios are about 3.4 on an early walk frame and about 2.2 on `attack2`, death, and idle. Hit stays under 1.6. Death keeps the legs and the torso together. The hood and the loose shoulder tatters still separate into fragments when the spine and head fold. It is not the v3 cape-to-spikes failure, and it is not a clean collapse either.
- `hooded_male_light.glb` was not used.
