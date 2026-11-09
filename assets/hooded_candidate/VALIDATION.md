# Hooded candidate — Godot 4.7 validation

One character. The soldier and the female are not in this pass. This is not a drop-in for the horde, and it was not handed to anyone.

Engine: Godot 4.7-stable (official), hash `5b4e0cb0fd279832bbdd69fed5354d4e5ad26f88`. Project renderer `mobile`. Window on display server **X11**. Device string from the run: Vulkan 1.4.318, Forward Mobile, device #0 **llvmpipe (LLVM 20.1.2, 256 bits)**. That is a software rasterizer, not a phone.

Harness: `validation/hooded_male/hooded_validate.gd`, driven with `--display-driver x11`. Stills are grabbed from the window texture after the main menu is hidden. Pixels between two walk frames differ (15,794 sampled pixels). Pixels between two crowd frames differ (9,236). The earlier headless 6.90 ms figure is still not a draw cost.

## Result

**Pass** for import, rest appearance, and the embedded clips on this machine.

**Not a pass** for production wiring, for a finished LOD, or for a phone cost.

## What imported

| File | Tris in Godot | Bones | Clips |
|---|---|---|---|
| `hooded_male_full_game.glb` | 96,615 | 20 | the six below |
| `hooded_male_mobile.glb` | 47,583 | 20 | same lengths |
| `far_impostor/hooded_male_far.glb` | 783 | 20, same clips | skinned, vertex color |
| `far_impostor/impostor_card.glb` | 2 | none | no AnimationPlayer |

Clip lengths match the handoff: attack2 1.0417 s, death 1.5833 s, hit 0.375 s, idle 2.5 s, run 0.9167 s, walk 1.3333 s. Idle, walk, and run loop. Hand position at the end of those three is within 0.5 mm of the start. Attack2, hit, and death do not loop. Attack2's hand moves from about (0.69, 1.21, 0.10) at t = 0 to (0.68, 1.42, 0.16) at t = 0.45. Death's hips and feet travel to the ground by t = 1.5.

Mesh bounds of the full file: height 1.72 m, feet on y = 0. Materials on the two game meshes, as imported, with no override: StandardMaterial3D, metallic 0, roughness 1, cull disabled (double-sided), albedo PNG, no normal map, transparency opaque. The card is alpha-scissor, untextured metallic 0, and uses its front PNG.

Skeleton order and parents match the handoff. `shoulder_L`, `shoulder_R`, `thigh_L`, `thigh_R`, and `hips` are all parentless. `cloak_back` is a child of `chest`.

## Adjustments that were required

- Godot's scene import was generating mesh LODs. That is off for these four glbs (`meshes/generate_lods=false`) so the triangle counts stay the authored ones.
- `animation/remove_immutable_tracks` is still the importer default. Each clip arrives with 25 tracks, not the 60 channels in the file. Constant tracks, including identity keys on `cloak_back` in the clips that do not move it, are dropped. The rest pose keeps those bones. The moving tracks are the ones that play.
- Import resamples at 30 fps. The durations above still match 24 fps source times.
- The glTF faces +Z. `HoodedPresenter` turns the model 180° so it faces the game's −Z. Shots whose names end in `_front` are taken from +Z and therefore show the cloak. Shots whose names end in `_back` show the face. The side shots are from +X.
- Idle, walk, and run are set to loop in the presenter. The file's one-shots stay non-looping.
- The far mesh imported with vertex colors and no albedo. Godot was ignoring the colors, so the crowd rendered as pale ghosts. The presenter turns on `vertex_color_use_as_albedo` for a material with no albedo texture. After that the far mesh is dark, which matches the handoff's "darker than the full model," and it is still a crude low poly.

No axis scale fix was needed. No metallic override was needed on the game meshes.

## What the pictures show

Rest, face-on, is the hooded body: strap, belt, hanging hands, wrapped legs. Full and mobile match at this distance. The mobile cloak, from behind, is more jagged and throws brighter edge highlights under the same directional light. They are not the same picture.

Walk is a step. Run is a stride with a lifted foot. Attack2 at 0.45 s is a reach with the hands open and the cloak still on the body. Death at 1.5 s is on the ground, face up, one piece. Hit and attack2 and death at t = 0 are the arms-out pose. Those frames are in `mobile_attack2_arms_out.png` and `mobile_hit_000_front.png`. A 0.30 s blend from walk does not show that pose at 0.05 s. At 0.30 s one arm is out and the other is still coming across. There is no one-frame snap to a T.

The 16 mobile bodies are independent poses (idle, walk, run, attack2, hit, death, phase-shifted). The 72 far copies are one MultiMesh of the far mesh in its bind pose, not 72 skeletons.

## LOD

Hard swap. There is no crossfade. At one camera the impostor card reads as the character, the mobile cloak reads as the character, and the far mesh reads as a thin dark low poly with a block head. Lowest vertex: mobile rest 0.6 mm, far 4.5 mm. That is not a few centimetres. The card was not rebuilt. It does not turn to face the camera. Edge-on it becomes a line. A real switch has to yaw the card, and the far mesh will pop darker and thinner than the mobile body.

## Clock

`process_frame` sat around 19–23 ms. `RenderingServer.force_draw` after the meshes were hidden sat around 19 ms. Those two match, so that 19 ms is the frame slot, not the cost of the characters.

While the 16 skinned bodies and 72 far instances were visible, the same `force_draw` returned 219 ms, 250 ms, and 560 ms. The spread is too wide to call a cost, and the device is llvmpipe. A phone number is not available.

## Evidence

Godot PNGs, `report.json`, and `contact_sheet.png` are in the run artifacts under `hooded_validate/`. The harness prints `VALIDATE_DONE` when it finishes.
