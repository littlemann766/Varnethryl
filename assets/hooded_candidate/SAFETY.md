# Hooded candidate — safety pass

One hooded mesh. Looked at the pictures from a fresh Godot 4.7 import, not only at the numbers. The soldier and the female are not in this pass. `MODEL_HOOK` is still empty. This was not sent onward.

## How it was run

Godot 4.7-stable, hash `5b4e0cb0fd279832bbdd69fed5354d4e5ad26f88`. Renderer `mobile`. Display server X11. Adapter string: Vulkan 1.4.318, Forward Mobile, device #0 **llvmpipe (LLVM 20.1.2, 256 bits)**. That is a software rasterizer. A phone was not used, and no phone number was measured.

The packaged files (mobile glb, full glb, atlas, card, presenter, billboard shader, this harness) were copied into an empty project at a new path, with no `.godot` cache and no game autoloads. Godot imported that tree, then `validation/hooded_male/hooded_safety.gd` rendered 70 frames. `report.json` from that run: mobile 47,583 tris, full 96,615 tris, albedo present on both, 20 bones, clips `attack2`, `death`, `hit`, `idle`, `run`, `walk`, face dot with −Z = 0.984. The same harness had already been run inside the game project; the frames below are the fresh-import set.

Lighting is a neutral key, fill, and rim. The model colors were not brightened and nothing was made emissive. An orange sphere sits in front of the nose and is only a marker.

## Checklist

| Check | Result |
|---|---|
| Idle, face and side, feet on the ground, one body | Pass. Face, strap, belt, and wraps read. Not a missing texture. |
| Idle / walk / run looped for three cycles | Pass. Walk start, walk end, and walk at cycle 3 are the same stride. Run at cycle 3 is the same crouch, one foot up, face toward the marker. |
| Attack2 first, wind-up, peak, last | Pass, with the wind-up called out below. At 0.8 s the leading hand reaches the marker. The other arm stays back. The last frame has the hand coming back in. |
| Hit first / mid / last | Pass. Arms come out and stay on the body. Feet stay down. |
| Death first / mid / last, then held 1.5 s | Pass. The last frame and the hold are the same body on the ground. It does not stand back up. |
| Walk into attack, 0.08 s and 0.30 s | Pass. At 0.08 s it is still the walk. At 0.30 s it is the wind-up, not a T. |
| Walk into hit and walk into death | Pass. Death at 0.30 s is a crouch into the fall, not a rest pose. |
| Attack interrupted into hit, then into death | Pass. Hit keeps a reach toward the marker. Death is a crouch, not a snap to idle. |
| 16 near bodies + 72 cards, three phases | Pass. Near bodies change pose (one is on the ground by the third phase). Cards stay upright, mixed yaw, feet on the floor. |
| Orbit 0 / 45 / 90 / 135 / 180 / 225 / 270 / 315 | Pass. Front shows two faces. Back shows two cloaks. 45° and 135° show the same quarter on both. At 90° and 270° the two stand in a line, so one hides the other; the one you see is a full profile, not a line. |
| Near to far at 4, 8, 11, 14, 18 m, then back the same steps | Pass. 4 m is the solid mesh. 11 m is a stippled standing figure. 18 m is the small card, still facing, feet on the floor. Back at 4 m is the solid mesh again. |
| Fresh zip import, empty cache | Pass. Albedo is the character, not pink or white. Tris and bone count match the game-project import. |

## What is still wrong, and was left

- The mobile cloak throws bright torn edges under the key light. The full mesh is darker and smoother in the face shot. That is the shell, not a dropped texture.
- The card's silhouette is sparkly next to the mesh (alpha cut). In the 8–14 m band the crossfade dithers, so the figure looks stippled while you cross it. Height and feet stay put. It is not a color pop and not a floor jump, and it is noisier than the body.
- Attack2 is asymmetric. Around 0.3 s the leading hand is behind the body, away from the marker. The bite is the later reach, about 0.8 s. Shambler damage is still 0.45 s and runner damage is still 0.28 s, both before that peak. The timers were not changed.
- On the fallen body the cloak sheets lie across the torso, with some bright interior planes. The body stays one piece.
- The card is one idle bake. It does not walk.
- `hooded_male_far.glb` (783 tris) was not used as the crowd. It is thinner and block-headed. Do not treat it as approved.
- No phone. The pictures are llvmpipe. Do not read them as a frame-time budget.
- Production horde is unchanged. The other two characters are not in this package.
