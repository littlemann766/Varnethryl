# Beth World — Godot 4 Ultra showcase

Files: `showcase.tscn` + `showcase.gd` (builds the scene from R4 hi assets + hero/boss GLBs, renders 8 shots),
`showcase_water.gdshader` (dual scrolling normals, depth colour, shoreline foam, fresnel; SSR does reflections),
`showcase_env.tres` (base Ultra Environment), `project_ultra.godot.txt` (render settings used).

## Ultra settings
- Forward+; MSAA 2x + TAA; directional + positional shadow atlas 8192, soft filter quality 5 (Ultra)
- Sun: PSSM 4 splits, max distance 420 m, shadow_blur 1.5, angular distance 0.8, volumetric fog energy 2
- Environment: PhysicalSky, ACES (white 6), SDFGI 6 cascades / 0.4 m cell + occlusion, SSAO r1.6 i2.2, SSIL r6,
  SSR 96 steps, glow softlight thr 1.1 bloom 0.06, volumetric fog (anisotropy 0.7 = god rays), sat 1.08 / contrast 1.05
- DoF (CameraAttributesPractical) on hero shots only, near+far blur, amount 0.11
- Night: sun 0.12 blue moonlight, sky 0.02, emissive windows + real OmniLights (shadowed on lamps near camera)
- Per time-of-day overrides (sun angle/colour, fog density/albedo, exposure) live in `set_tod()` in showcase.gd.
- Particles: GPUParticles3D for fireflies, chimney smoke, embers, lava sparks, ash, snow.

## Software render vs phone GPU
Renders were made on Xvfb/llvmpipe (software Vulkan). On a real GPU: TAA converges properly (here few frames → shimmer),
SDFGI cascades settle (here GI is under-converged, some flat/blotchy indirect), volumetric fog is less noisy,
SSR/SSIL full quality. On a phone, Forward+ Ultra is NOT realistic: use Mobile renderer, drop SDFGI/SSIL/volumetric fog,
shadow 2048, keep glow + ACES + water shader; bake GI (LightmapGI) for the town.

## Known flaws
- Some sun-into-camera shots are overexposed (town golden, night horizon glow).
- Boss lineup framed too tight (titan cropped); colosseum/temple wide shot reads flat at distance.
- Volcano titan silhouettes against lava with little detail; terrain heightfields are visibly faceted far away.
- Character albedo partly vertex-colour based; some armor reads washed out.
