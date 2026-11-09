# Zombie characters v6

The body and the clothes are separate meshes. v5 is unchanged. The stretch numbers pass. The pictures do not.

## Body

The body is the MakeHuman 1.x base mesh, CC0. Provenance is in `PROVENANCE.md`. Kael's own mesh was not used: it is the clothed hero, and the cape on that mesh is what stretches.

Arms were swung into the kael T-pose. The torso was narrowed. The female has wider hips and narrower shoulders. The head, ears, and fingers are the MakeHuman surface. Two eyeballs are kept and weighted to `head`.

Skinning is one bone per face. Any face whose vertices wanted two bones was deleted, and the new boundary vertices are not shared, so an edge cannot be pulled by two bones. That is why the stretch table below is 1.0. The gaps that deletion opens at the joints are supposed to sit under the clothing.

## Clothing

Sleeves, tunic, cloak, skirt (front and two sides), hood, hair, belt, boots, pauldrons, and kneepads are cut off the TRELLIS shell by which posed bone they sit nearest. Each piece is welded, islands under 2% were already gone on the shell, and the piece is decimated toward a budget. Faces larger than about 12 cm² are dropped. Every vertex of a piece shares one weight:

| Piece | Weight |
|---|---|
| Hood | 0.75 head, 0.25 neck |
| Hair | head |
| Cloak | 0.65 chest, 0.35 spine |
| Tunic | 0.70 chest, 0.30 spine |
| Belt, skirt centre | hips |
| Skirt side | 0.55 that thigh, 0.45 hips |
| Upper sleeve | that upper arm |
| Lower sleeve | that forearm |
| Boot | 0.55 shin, 0.45 foot |
| Pauldron | that shoulder |
| Kneepad | that shin |

A shared weight cannot stretch the piece internally. The piece is then moved from the hunched shell back onto the kael rest by the inverse of that same skin matrix.

## Stretch

Measured on the exported meshes, every piece, every frame of `idle`, `walk`, `run`, `attack2`, `hit`, and `death`. The number is the longest posed edge divided by its rest length. Edges shorter than 3 mm are included in the first pass of the tool and did not change the result.

| Clip | Hooded male | Ex-soldier | Female |
|---|---|---|---|
| idle | 1.0 | 1.0 | 1.0 |
| walk | 1.0 | 1.0 | 1.0 |
| run | 1.0 | 1.0 | 1.0 |
| attack2 | 1.0 | 1.0 | 1.0 |
| hit | 1.0 | 1.0 | 1.0 |
| death | 1.0 | 1.0 | 1.0 |

The 1.8× rule on edge length is met. It is met because the faces that would have stretched were split onto one bone, not because the clothing moves like cloth.

## What the pictures show

This does not meet the visual rule.

- The rest pose is the kael T, so the sleeves stick straight out. In the walk frames some sleeves stay out or come off the arm. The female walk has hands floating beside the dress.
- The garments are still shards. Cutting the open shell by nearest bone, then decimating, does not produce a fitted tunic or cloak. A large flat facet sits on the chest of several of the group figures. Holes in the torso show through.
- The head is a real head. The face close-ups show the MakeHuman eyes, nose, ears, and mouth. The skin texture on that head is pale and pixelated. It is not the dark rotted skin in the concept. The cube-projected atlas sampled the shell poorly, and the result is a light grey wash, not the TRELLIS preview.
- The hood behind the head is a pile of facets, not a hood.

## Files

| File | Tris | Notes |
|---|---|---|
| `hooded_male.glb` | 36,964 | Under the 40k budget. |
| `ex_soldier.glb` | 58,463 | Over the budget. The cloak did not collapse. |
| `female_blue.glb` | 22,196 | Under the budget. |
| `*_far.glb` | 2,423 / 6,286 / 797 | Collapse would not go lower on the two male shells. The female far mesh is the one that fits a crowd budget. |
| `*_impostor.glb` | two cards | Front render, crossed. |
| `textures/` | 2048² | Albedo, a weak normal, ORM. Metallic is 0. Roughness is about 0.84. |
| `previews/` | | Front, three-quarter, face, concept strip, walk, bite, death, walk GIF, impostor, group of 16. |

The group is 16 copies. Each copy was posed by its own armature at a different walk frame and then frozen for the still. They are not one skeleton scaled up.

`attack2` is the bite. There is no separate bite clip.

```gdscript
var body := load("res://assets/zombie_v6/hooded_male.glb").instantiate()
var anim := body.find_child("AnimationPlayer", true, false) as AnimationPlayer
anim.play("walk")
```

Do not put these in the crowd. The stretch number is fine and the mesh is not.

## Godot 4.7 mobile, headless

Godot 4.7 stable, project renderer `mobile`, `--headless`. 16 skinned bodies, mixed across the three, playing `walk`, 90 frames after a short warmup:

- **6.90 ms per frame**

That is the same clock reading as the v4 and v5 benches on this machine, including a 58k soldier in the mix. Treat it as a software-renderer number that did not move with the triangle count, not as a phone measurement. Triangle counts above are from the mesh index buffers.

## What is still required

The split layout is the right structure, and the 1.0 stretch shows the weighting rule works. The garments have to be rebuilt as real pieces: a tunic, a cloak, and boots modelled or retopologised to the body, with the TRELLIS used as a colour and a silhouette reference. Decimating the open shell does not produce those pieces.
