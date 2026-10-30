# Tidewrack Sea - Stage 4: Region C, the Straits (frost + ash)

Same sea as stages 1-3. Two narrow sailing channels between the frost lands (north) and the ash lands (south).
Godot 4.7.2, Mobile renderer, High + Low tiers. Load `meshes/stage4_manifest.json` (tiles, regions, channels, icebergs, vents, fog tints, props, stats).

## Regions
- **frost** rect (-2400,-3000)-(1500,-1500): buttressed ice cliffs (~13 m, max 60), shelf ice, 520 ice floes, 3 iceberg meshes + 12 drifting instances,
  icicle fringes + 9 frozen falls. Harbour: **Frostreach Ice Dock**. Hidden: **Rimefang Maw** (cave cleft), **Frozen Wreck**, **Aurora Arch** (spans the gorge).
- **ash** rect (-1800,1450)-(1500,3000): black basalt, Cinderreach volcano (crater lake, lava rivulets), 34 steam vents, glowing lava seams along shore.
  Harbour: **Vent Harbour**. Hidden: **Obsidian Arch**, **Ember Wreck**, **Hot-spring Grotto**.
- Channels: **Rimefang Narrows** (min 57 m, mean 195 m), **Cinder Gate** (min ~106 m).
- Fog border: same soft fog-bank style (`{frost,ash}_fog_layers`, storm_sky/sea/col).

## Runtime notes
- Water: use stage1 `ocean_water` / `ocean_water_low` with `shaders/{frost,ash}_shore_dist.png`, `shore_rect` = region rect (x0,z0,w,d), `ice` from manifest.
  `ocean_water_low` gained an optional `rough` uniform (default 0.12 = unchanged); ash uses 0.45.
- Shore distance png is now baked from the real terrain height (>0.2 m), not the map solid mask (that left submerged land -> white foam fields).
- Basalt: StandardMaterial vertex colour with **metallic_specular 0.15**, else it mirrors the hazy sky and reads beige.
- Shaders reading data packed in COLOR.r/g must decode with `pow(x, 1.0/2.2)` (save() writes linear vertex colours).
- Icebergs: drift slowly along the manifest headings (a few m/min), bob with the wave sum; no shadows on ships/bergs on mobile.
- Lava seams: `lava_seam.gdshader` (energy 6), steam: `steam_plume.gdshader` (no lod).
- Map field changes (Cinderreach lava spit, Rimefang gorge carve) live in `map/straits_fields.npz` (tools/make_fields.py); the beth-world map file is untouched.
- Budgets: lod1 ~45% of High; Low tier ~75-137k prims, 15-33 draw calls; High ~270-690k prims, <=41 draw calls.

## Known issue
- Stage 2: thin dark spikes appear in the inlet north of Echo Grotto (~(-2290,-230), terrain tile x1z1). Not slivers/fins; root cause unknown.
  The C3 shot camera was moved to the open-water approach; the artefact itself remains.

Renders: `renders/small/` (S4_contact_*.jpg, F*/A* shots, POLISH_before_after_*.jpg).
