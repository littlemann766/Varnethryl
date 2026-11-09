# Zombie villager v2

This replaces the procedural v1 body. v1 in `assets/zombie/` is unchanged.

## Base mesh

The body is the MakeHuman 1.x base mesh (`base.obj`, 13,380 vertices, quads), which the MakeHuman project released as CC0. The file header says so, and the project license says the bundled assets (base mesh, targets, textures, clothes, poses) are CC0 1.0.

- Source: https://github.com/makehumancommunity/makehuman/blob/master/makehuman/data/3dobjs/base.obj
- License: https://github.com/makehumancommunity/makehuman/blob/master/LICENSE.md (section C, assets are CC0)
- No MakeHuman application code is included. Only the mesh was used, then edited.

Blender Studio's Human Base Meshes bundle is also CC0 and would have been a better sculpt base, but `download.blender.org` answered with a Cloudflare challenge from this machine, so the file never arrived.

There is no GPU on this machine (no `nvidia-smi`, 4 cores, about 15 GB RAM). TRELLIS, Hunyuan3D-2, and TripoSR were not run. A CPU image-to-3D pass was not going to beat a real human mesh under that limit.

## What was done to the base

- Dropped the helper geometry and the separate eyeballs. The face, ears, teeth volume, and fingers are the MakeHuman surface.
- Arms were rotated from the resting pose into a T so they line up with the kael rest pose. The rotation is one rigid swing per arm, from the hand inward, stopping at the shoulder.
- Decimated the body with the head protected. The face is still the MakeHuman face, not a new sculpt. Local vertex pulls on the cheeks and jaw were tried and they split the surface, so they were removed.
- A tunic shell is the torso surface offset along the outward normal, with jagged alpha at the hem. It is joined into the body mesh before skinning so it cannot detach when the skeleton translates.
- A few hair cards hang down the back of the head and are weighted only to `head`.
- The mesh is skinned with Blender's automatic weights onto the kael skeleton imported from `voxel/kael_voxel.glb`. Vertex groups outside the 21 humanoid joints are removed. The bone rest transforms are the kael ones, which is why the existing clips play.

## Textures

2048×2048 albedo, normal, and ORM for skin and for the tunic. They are painted in UV space from vertex position (dead olive skin, bruised sockets, dark mouth, blood spots, brown cloth, hem alpha). The normal is a detail map derived from the albedo, not a baked high-poly sculpt. Both sets are embedded in the glb.

## Budget

| Mesh | Triangles |
| --- | --- |
| Villager (body + tunic + hair) | 13,596 |
| Far crowd, idle pose, decimated | 402 |

One material pair (skin, cloth) at 2048². Godot 4.7 imported the villager at 13,596 triangles.

## Skeleton and clips

The glb carries the kael rig (71 bones in the file, including the unused fly bones). Weights use the 21 humanoid joints: `root`, `hips`, `spine`, `chest`, `cape`, `neck`, `head`, `shoulder_L/R`, `upperArm_L/R`, `foreArm_L/R`, `hand_L/R`, `thigh_L/R`, `shin_L/R`, `foot_L/R`.

Clips copied with that rig: `idle`, `walk`, `run`, `attack1`, `attack2`, `attack3`, `hit`, `death`, plus the fly and skill clips that were already on the rig. In Godot 4.7 mobile (lavapipe software Vulkan, not a phone GPU), bone lengths stayed constant across attack, hit, death, and walk:

- upper arm 0.203 m
- forearm 0.194 m
- thigh 0.418 m (0.417 on the walk frame)
- shin 0.397 m
- neck 0.091 m

The kael `idle` already leans the spine and drops the arms. A custom hunched pose that re-aimed the bones stretched the mesh, so it was not shipped. There is still no `bite` or `bite_windup` clip in the project.

## Honest limits

- One villager, not separate female, knight, and sailor meshes. The base is the neutral MakeHuman body. A second sex or a pauldron was not a stable extra shell.
- The face is a real human face with bruised sockets and a dark mouth. It is not a sculpted skull, the eyes are not deep recessed whites, and the jaw is not open with a row of teeth. Those edits tore the surface when they were tried as vertex moves.
- Hair is a handful of cards down the back, not a full mane.
- The tunic is one offset shell with alpha cuts, not layered cloth with thickness, a belt buckle, or armor.
- The normal map is detail-from-albedo, not a high-to-low bake.
- Far crowd is a 402-tri static mesh in the idle pose. There is no separate billboard impostor.

## Validation

Godot 4.7, `renderer/rendering_method="mobile"`, software Vulkan:

`VK_ICD_FILENAMES=/usr/share/vulkan/icd.d/lvp_icd.json xvfb-run -a Godot --path . -s res://assets/zombie_v2/preview_render.gd`

Stills are in `artifacts/zombie_model_v2/`. `11_compare.png` puts the idle and the face next to two of the owner's concept sheets.
