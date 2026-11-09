# Zombie characters v5

Built from the same image-to-3D shells as v4 (`assets/zombie_src/`). v4 is unchanged. This version does not pass the animation test. The numbers are below, and the last section says what to do instead.

## What was done

The source meshes split vertices, so a connectivity test before a weld treats every triangle as its own island and deletes the body. The shells were welded by distance (1.5 mm) first, normals were made consistent, and then every disconnected island under 2% of the faces was deleted.

| Character | Faces removed | Faces kept |
|---|---|---|
| hooded_male | 933 | 94,808 |
| ex_soldier | 422 | 92,392 |
| female_blue | 17 | 14,208 |

Weights come from `characters/kael_lod1.glb`, not from a hand-painted map. The kael body was posed into the baked hunch until each hand bone sat within 3 cm of the shell. Blender's Data Transfer modifier copied vertex groups with nearest-face interpolation. Arm weights fade out past the sleeve, so the cloak back is left on the spine and chest. Cloth below the belt is half `hips` and half the nearer thigh. Weights were smoothed for 10 iterations, normalized, and limited to 4 influences. Nothing is weighted to `cape`. That fitted pose was applied as the rest, the mesh was deformed back onto the standard kael rest, and the export uses a fresh `voxel/kael_voxel.glb` armature so the clip curves stay intact.

A second pass that copied neighbour weights onto stretched vertices made the ratios worse (walk climbed past 60×), so it was thrown out. Faces were not deleted to hide the stretch.

## The pass condition is not met

No frame of `idle`, `walk`, `run`, `attack2`, `hit`, or `death` was allowed to stretch a triangle past 1.8× its rest edge length. Measured on the exported meshes, every clip fails. Edges shorter than 3 mm are weld slivers; both columns are listed.

| Clip | hooded_male (any / over 3 mm) | ex_soldier | female_blue |
|---|---|---|---|
| idle | 28.6 / 4.1 | 9.8 / 4.3 | 4.7 / 4.7 |
| walk | 33.6 / 7.9 | 9.7 / 9.0 | 7.5 / 7.5 |
| run | 32.4 / 12.6 | 24.8 / 14.3 | 11.2 / 11.2 |
| attack2 | 35.8 / 5.4 | 13.0 / 5.0 | 4.6 / 4.6 |
| hit | 24.5 / 3.8 | 5.0 / 2.7 | 2.8 / 2.8 |
| death | 30.8 / 6.7 | 7.3 / 7.3 | 8.0 / 8.0 |

Thousands of edges over 3 mm are past 1.8× on walk, run, and death. The open shell is one connected surface, so triangles run from the sleeve into the cloak and from the thigh into the boot. Those faces cannot follow one bone without stretching, and smoothing them only spreads the stretch. The bind pose itself shows it: the hooded male's cloak has a panel pulled out to the side where a strip took the arm bone on the way back to the kael rest.

Some single frames still look like one body. `previews/*_walk.png` is an early walk frame. `previews/*_walk_worst.png` is the frame with the highest ratio on edges over 3 mm. The body does not explode into separate chunks the way v4 did, and the floating shoulder shards are gone, but the 1.8× rule is not met and the cloak still spikes.

## Colour

The v4 white look was the TRELLIS.2 metallic channel. On the hooded male that channel sits near 0.7, so the cloth rendered as metal under the old lights. The source preview is matte dark grey-brown, so v5 does not use it. Metallic is 0, roughness is 0.78, and the albedo is the sRGB base-color image (saved under `textures/`). The female chest is still brighter than the concept. That brightness is in the albedo, plus a specular highlight, not a metallic map.

## Files

| File | Tris | Notes |
|---|---|---|
| `hooded_male.glb` | 94,808 | Skinned. sRGB albedo embedded. Metallic 0. |
| `ex_soldier.glb` | 92,392 | Same. |
| `female_blue.glb` | 14,208 | Same. Source was already near this density. |
| `textures/*_albedo.png` | 2048² | sRGB albedo only. |
| `previews/` | | Front, three-quarter, face, concept comparison, walk, the worst walk frame, bite, death, and a 12-frame walk turntable GIF. |

Scale is about 1.72 m, feet on the ground, Y-up. Clips are the kael set. `attack2` is the bite. There is no separate bite clip.

```gdscript
var body := load("res://assets/zombie_v5/hooded_male.glb").instantiate()
var anim := body.find_child("AnimationPlayer", true, false) as AnimationPlayer
anim.play("walk")
```

These files are not ready to replace the crowd. The stretch above will show up as spikes in play.

## Godot 4.7 mobile, headless

Godot 4.7 stable, project rendering method `mobile`, `--headless`. 16 skinned bodies, mixed across the three, playing `walk`, 90 frames after a short warmup:

- **6.90 ms per frame**

Same clock reading as the v4 bench on this machine. It is a software-renderer number, not a phone, and it is only the bodies. `surface_get_array_len() / 3` reported 33,409 / 39,344 / 3,909. That is the vertex buffer, not the triangle count. The triangle counts are in the table above.

## What to do instead

The single open shell cannot be skinned to this skeleton and stay under 1.8×. Another weight pass on the same surface will not get there: a triangle that joins the sleeve to the cloak has to stretch when the arm swings, and deleting those faces was ruled out.

The workable split is a clean rigged body plus the generated clothing as separate pieces:

- A closed body, either the kael body or a retopologised body, skinned with the kael weights it already has.
- Sleeves, cloak, skirt, and boots cut off the generated shell into their own meshes.
- Each clothing piece skinned to one bone, or to a small blend that every vertex of that piece shares (cloak on `chest` and `spine` only, skirt half `hips` and half the thighs, sleeves on the arm chain).
- No triangle shared between a sleeve and the cloak, so the arm can move without tearing the back.

That keeps the TRELLIS cloth and the kael clips, and it is the first layout that can actually meet the 1.8× rule.
