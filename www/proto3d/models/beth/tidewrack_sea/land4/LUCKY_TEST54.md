# Test 54 art drop — blocked on the godot-voxel branch ref

`godot-voxel` is a branch of `https://github.com/littlemann766/Varnethryl`. It is not a separate repository. Checked from this clone:

```
git fetch origin refs/heads/godot-voxel:refs/remotes/origin/godot-voxel
fatal: couldn't find remote ref refs/heads/godot-voxel
```

`git ls-remote --heads origin` has no `refs/heads/godot-voxel` and no other head whose name contains `voxel`. Compatibility of the 15 bindings against that branch was not validated. The `_mat_for` paste further down is the land1/land3 note from test 49. It is not a verified test 54 call site. Do not apply it until `refs/heads/godot-voxel` exists and someone reads `_mat_for` on that SHA.

A tag named `godot-test-54` does exist. It is not the branch. It was not used as a substitute, and its tree was not read for this check. For the record only: `refs/tags/godot-test-54` is `33ec05515fa2907c1d6958e39e884eed92955776`, the same SHA as `refs/heads/main` at the time of this fetch.

Art files named below are still `4f8c97f8` on `beth-world-art`. This note does not change a mesh or the shader. Nothing was pushed to `godot-voxel`, `main`, or a release.

Do not merge this branch. Do not copy armor, PR27, `equipment/`, mainland `main.gd`, or any collision mesh.

## Copy

From `www/proto3d/models/beth/tidewrack_sea/land4/` at `4f8c97f8`.

Terrain visuals only. A file is in scope when the name contains `_tile_` or `_isl_` or is exactly `arch_islands`, and the name does not contain `_col`, `land_scatter`, `_glow`, or `_port`. Copy those glbs, including `_lod1`, over `res://tidewrack/stageN/meshes/` of the same name. Copying the whole `meshes/` folder will overwrite scatter colliders. Do not.

| From | To |
|---|---|
| `shaders/vc_terrain.gdshader` | `res://tidewrack/stage1/shaders/vc_terrain.gdshader` |
| `textures/*.jpg` (15 files, listed below) | `res://tidewrack/land4/textures/` |

The shader replaces the procedural land1/land3 ground. It draws black or empty on any sampler that is not set.

## Fifteen bindings

CC0 1.0 ambientCG, recorded in `textures/TEXTURES.md`. No purchase. The shader names are the uniforms.

| Uniform | File | Source |
|---|---|---|
| `grass_col` | `grass_albedo.jpg` | Grass004 albedo |
| `grass_nrm` | `grass_normal.jpg` | Grass004 normal, OpenGL +Y |
| `grass_rgh` | `grass_rough.jpg` | Grass004 roughness |
| `earth_col` | `earth_albedo.jpg` | Ground048 albedo |
| `earth_nrm` | `earth_normal.jpg` | Ground048 normal |
| `earth_rgh` | `earth_rough.jpg` | Ground048 roughness |
| `sand_col` | `sand_albedo.jpg` | Ground054 albedo |
| `sand_nrm` | `sand_normal.jpg` | Ground054 normal |
| `sand_rgh` | `sand_rough.jpg` | Ground054 roughness |
| `rock_col` | `rock_albedo.jpg` | Rock023 albedo |
| `rock_nrm` | `rock_normal.jpg` | Rock023 normal |
| `rock_rgh` | `rock_rough.jpg` | Rock023 roughness |
| `snow_col` | `snow_albedo.jpg` | Snow001 albedo |
| `snow_nrm` | `snow_normal.jpg` | Snow001 normal |
| `snow_rgh` | `snow_rough.jpg` | Snow001 roughness |

`preview/render.gd` `bind_terrain()` is the loader the stills used: `Image.load_from_file`, then `generate_mipmaps()`, then `ImageTexture`. Use that, not the editor importer. An importer that marks the normal or the roughness as sRGB will not match the stills.

## Code

Region index is part of the look. Frost is `2`. Archipelago `0`, Saltglass `1`, Ash `3`. A different order paints frost with grass or ash.

`hero_cut` is a `global uniform vec4` already used by the land1 shader. Leave it.

In `_mat_for`, for terrain names only:

```gdscript
if n.contains("_tile_") or n == "arch_islands" or (n.contains("_isl_") and not n.ends_with("_glow") and not n.ends_with("_port")):
    var t := _sh("stage1/shaders/vc_terrain.gdshader")
    t.set_shader_parameter("region", ["arch_", "coast_", "frost_", "ash_"].find(n.substr(0, n.find("_") + 1)))
    _bind_land4(t)
    if n.begins_with("ash_"):
        t.set_shader_parameter("lift", 0.06)
        t.set_shader_parameter("ambient", 0.45)
        t.set_shader_parameter("spec", 0.12)
    if not high():
        t.set_shader_parameter("detail", 0.55)
    return t
```

Ash `0.06 / 0.45 / 0.12` is what the approved stills used. The older land3 line `0.1 / 1.25 / 0.075` is not this pass.

```gdscript
var _land4_tex := {}
func _bind_land4(mat: ShaderMaterial) -> void:
    var root := "res://tidewrack/land4/textures/"
    for key in ["grass", "earth", "sand", "rock", "snow"]:
        mat.set_shader_parameter(key + "_col", _land4_jpg(root + key + "_albedo.jpg"))
        mat.set_shader_parameter(key + "_nrm", _land4_jpg(root + key + "_normal.jpg"))
        mat.set_shader_parameter(key + "_rgh", _land4_jpg(root + key + "_rough.jpg"))

func _land4_jpg(res_path: String) -> Texture2D:
    if _land4_tex.has(res_path):
        return _land4_tex[res_path]
    var img := Image.load_from_file(ProjectSettings.globalize_path(res_path))
    if img == null:
        push_error("land4 texture missing: " + res_path)
        return null
    img.generate_mipmaps()
    var tex := ImageTexture.create_from_image(img)
    _land4_tex[res_path] = tex
    return tex
```

`detail` only scales normal strength. Low does not drop samples. The fragment shader takes 26 texture reads. It was not timed on a phone.

Warm the shader the same way the other terrain shaders are warmed, or the first frame hitch is the compile.

## What this does not change

- Collision glbs, route vertices, Saltglass stair, harbour, lift, toll.
- Mainland height. The gully term is still not applied.
- Armor and PR27. Nothing under `equipment/`.
- `vertex_color_is_srgb`. COLOR_0 is still uint8 normalized, same as land1–3.
- Frost cliff outlines. They are the mesh. A slide of new vertices along normals opened dark cuts in the gullies and was thrown out. Do not run a rounder. The shader does not change the silhouette.

## Check on test 54

- Gullhaven at eye height: photographed grass, matte, not the old neon blades.
- Frost slope: cold white and blue-grey snow, no yellow-green bands. Steep faces are darker blue-grey rock and still faceted.
- Ash ground: dark. If it looks like the old bright basalt, the lift/ambient lines were the land3 ones.
- A Saltglass route still meets the ground. If the feet float or sink, a collision file was replaced. Put the old col glbs back.
- Armor is the test 54 armor. If it changed, the wrong tree was copied.

## If it fails

- Magenta or missing ground: the shader compiled without a sampler, or one jpg path is wrong. The `push_error` names the file. Put the previous `vc_terrain.gdshader` back if you need the build playable in the next minute.
- Shader fails to link on the phone: 15 samplers plus the engine can pass a GLES limit. Same rollback. The Compatibility preview on this machine linked. That is llvmpipe, not the S26.
- Stills of this art are Godot 4.4.1 GL Compatibility, not a Vulkan phone capture. Brightness on the S26 will not match the jpg.

The Capacitor workflow `.github/workflows/build-android.yml` builds the web game, not Godot test 54. This machine has no Android SDK and no Godot Android export templates, so no terrain APK was made here. Test 54 is the playable check.
