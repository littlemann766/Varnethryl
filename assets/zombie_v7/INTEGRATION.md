# Zombie characters v7

The body is the same MakeHuman mesh as v6, on the kael skeleton. The clothes are new meshes, not a decimated TRELLIS shell. The stretch numbers pass. The pictures do not match the concepts.

## Body

Arms were swung into the kael T-pose and the torso was narrowed. The female has wider hips. Two eyeballs stay, weighted to `head`.

Skinning is one bone per face. A face whose vertices sat nearest two different bones was deleted, so no edge is pulled by two bones. That is why every clip below is 1.0. The gaps that deletion opens at the neck, shoulders, elbows, hips, and knees are visible. Clothing was supposed to hide them. It does not.

The skin map is 2048². The face is mapped into the upper part of that image, which is more than a 1024² region. The painted colour is a dark grey-green, with pale bone and a redder sinew tone on the jaw and cheeks, darker hands, and milky eyeballs. A tangent-space normal map is in the material at low strength. In the face renders the head still reads as a dark low-poly sculpt with pale blocks on the jaw, not as the concept's rotted skin.

## Clothing

Each piece is a quad grid, double sided, with no second shell. Tattered hems and a few holes are in the cloth alpha (alpha clip / scissor), not cut into the mesh.

| Piece | Weight |
|---|---|
| Hood, cloak | chest, spine, and a small blend toward the upper arms where the cloth is near them |
| Tunic | 0.62 chest, 0.38 spine, the same on every vertex |
| Sleeves | the matching upper arm or forearm, 100% |
| Belt, strap, pouches | hips |
| Skirt | transferred from the body, then collapsed to one shared blend if an edge went over 1.8× |
| Shin wraps | that shin |
| Boots | that foot |
| Hair | head |
| Pauldron | that shoulder, 100% |
| Kneepad | that shin, 100% |

Weights were transferred from the body with nearest-face interpolation, then smoothed and limited to four influences. Pieces that still stretched were then given one shared weight. A shared weight cannot stretch the piece. It also cannot bend, which is why a sleeve is a rigid tube on its bone.

The soldier tunic has a chain pattern painted into the chest of the cloth map. It does not read as mail in the preview.

## Stretch

Measured on the exported meshes, every piece, every frame of `idle`, `walk`, `run`, `attack2`, `hit`, and `death`. The number is the longest posed edge divided by its rest length. Edges shorter than 3 mm are ignored.

| Clip | Hooded male | Ex-soldier | Female |
|---|---|---|---|
| idle | 1.0 | 1.0 | 1.0 |
| walk | 1.0 | 1.0 | 1.0 |
| run | 1.0 | 1.0 | 1.0 |
| attack2 | 1.0 | 1.0 | 1.0 |
| hit | 1.0 | 1.0 | 1.0 |
| death | 1.0 | 1.0 | 1.0 |

On the kael walk, the left hand sits about 60 degrees below horizontal (around z = 0.97 against a shoulder near z = 1.4). The hands are not stuck in the T-pose. They are also not tucked against the ribs the way the concept sheets show them. The walk clip is a swing from the T-pose.

## What the pictures show

This does not match the concept art.

- The head is a real head, and the eyes are pale. The skin does not look rotted. The jaw patches are pale blocks. The scalp shows the polygon flow.
- The tunic, sleeves, cloak, and skirt are clean tubes and panels, which is the point of this pass, and they look like tubes and panels. The hood is a slab behind the skull. The cloak is a flat back sheet. The sleeves do follow the arms.
- The boots are rings that do not sit on the feet. The shin wraps are short tubes. Joints in the body show through as gaps, and some cloth panels float off the limb.
- The soldier's pauldrons are small plates that do not wrap the shoulder. The female dress is two long panels and a back sheet, not the blue gown in the crop.
- Death stays in one piece. It does not spike. It still looks like tubes lying down.

## Files

| File | Tris | Notes |
|---|---|---|
| `hooded_male.glb` | 25,376 | Inside 25–40k. |
| `ex_soldier.glb` | 25,350 | Inside 25–40k. The v6 soldier was over. |
| `female_blue.glb` | 25,642 | Inside 25–40k. |
| `*_far.glb` | 700 / 700 / 699 | Inside 400–900. |
| `*_impostor.glb` | two cards | Front render, crossed. |
| `textures/` | 2048² | Skin and cloth albedo, plus a normal map. Metallic is 0. Skin roughness is 0.62, cloth is 0.86. |
| `previews/` | | Front, three-quarter, face beside the concept, walk, bite, death, walk GIF, group of 16. |

The group is 16 copies, each on its own armature at a different walk frame, then rendered. They are not one skeleton.

`attack2` is the bite. There is no separate bite clip.

Godot 4.7 Mobile, lavapipe, 16 skinned characters playing walk: see the timing line at the bottom of this file. That number is a software renderer, not a phone.

```gdscript
var body := load("res://assets/zombie_v7/hooded_male.glb").instantiate()
var anim := body.find_child("AnimationPlayer", true, false) as AnimationPlayer
anim.play("walk")
```

Do not put these in the crowd. The budget and the stretch pass. The mesh does not look like the concepts.

## Godot timing

Godot 4.7.stable, Mobile renderer, lavapipe. 16 skinned characters playing `walk`.

`FRAME_MS 6.90` over 90 frames. Same class of number as v6 on this machine. It is not a phone.
