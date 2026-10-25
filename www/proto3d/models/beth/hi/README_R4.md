# Beth round 4: High/Ultra hero art for Godot (notes for Lucky)
Everything is in `www/proto3d/models/beth/hi/`: standard glTF PBR (base colour, normal, ORM = R occlusion / G roughness / B metal, emissive), Y-up, in metres. The GLBs carry **no vertex colours**: every tint is baked into the atlas slots, so they drop straight into Godot without `vertex_color_use_as_albedo`. Metal is 1 only on iron. Glass and window panes and the lava are emissive.

## Tiers
| tier | file suffix | textures |
|---|---|---|
| Ultra/High | none | `tex/2048/` |
| Medium | `_lod1` | `tex/1024/` |
| Low | `_lod2` | `tex/512/` |

Use the files as LOD steps or a per-quality swap. Each family (buildings / terrain / trees) has ONE shared slot atlas (8×8 slots of 256 px) holding albedo.png, normal.png, orm.png and emissive.png. That is one material per family, so Godot can batch.

## Buildings: `hi/buildings/bld_<id>{,_lod1,_lod2}.glb`
- **Coverage:** 27 exteriors: house1–4, farmhouse, barn, stables, windmill, lighthouse, gate_tower, thieves, guildhall, library, townhall, mage, treasury, crypt, market, apothecary, bakery, inn, smithy, training, keep, temple, observatory, colosseum.
- **Nodes:** `walls` and `roof` (the roof hides when inside); the windmill also has `blades`, which rotate about local Z. Footprints and doors match the round-2/3 measurements: door on +z at x=0, ≥3.7×3.3 m.
- **High detail:**
  - Individual roof tiles or shingles.
  - Proud ashlar stone blocks on the stone ground storeys and around round towers.
  - Window frames with mullions, sills, lintels and keystones.
  - Voussoir door arches.
- **Character pieces (from the old models and sheets):**
  - Mage academy: 5 towers with blue conical roofs and banners.
  - Temple: twin spired front towers with pinnacles, a rose window, and a drum and dome.
  - Colosseum: 6 seating tiers, an upper column ring and the arcade.
  - Keep: machicolation corbels, arrow slits and a raised portcullis.
  - Guildhall: clock tower.
  - Smithy: forge arch, anvil, quench barrel and big chimney.
  - Inn: hanging sign, banners and chimneys.
  - Library: buttresses.
  - Townhall: belfry.
  - Lighthouse: gallery corbels.
- **Tris:** High 2.8k–47.6k. Only mage (47.6k) and temple (42.2k) exceed the ~40k target; the rest are under 40k. Full table in NUMBERS.md.

## Terrain: `hi/terrain/`
| piece | High tris | notes |
|---|---|---|
| peak_snow_hi | 57.8k | sculpted ridged-noise heightfield, snowpack cap above a noisy snowline, strata on steep faces |
| peak_bare_hi | 24k | |
| volcano_flank_hi | 54k | 6 carved lava channels plus a crater; lava slots are emissive (emissiveFactor 2) |
| cliff_strata_hi | 27.5k | banded ledges with a grass top |
| shore_edge_hi | 16k | grass→sand→foam line→wet sand→wet rock, with rocks; put the waterline at y=0 |
| boulder_strata_hi | 6.4k | |

Each piece has lod1 and lod2. They use a new extra tile set: strata, lava, sand, wet sand, wet rock, moss rock, snowpack, scree, ash, foam, cliff grass, obsidian.

## Trees and foliage: `hi/trees/`
- **Species:** oak, oak_autumn, oak_deep, birch, blossom, pine, pine_snow, bush, bush_autumn, grass_clump.
- **Construction:** branching trunks with 1.1k alpha-cut leaf cards that use canopy-spherical normals (soft, volumetric shading). Material is alpha MASK 0.5, double-sided.
- **Tris:** High 2.5k–6.2k. lod1 is 0.2k–1k, and lod2 is a 6-tri crossed impostor (trees only).

## Godot check (copy at /tmp/gp4; /workspace/godot-proto untouched)
- The harness is audit/r4/godot/show.gd/.tscn (`-- _lod1` / `-- _lod2` picks the tier).
- All 27 buildings, 6 terrain pieces and 10 foliage types imported and instanced with 0 errors, in both Mobile and Forward+.
- Shots: audit/r4/godot/shot_{forward_plus,mobile,lod1_mobile,lod2_mobile}_*.png (day and night). Contact sheets: audit/r4/contact_r4_*.png.
- Stats are in NUMBERS.md. The full showcase view is about 100 draw calls / 1.48M primitives on High Mobile, against 100 / 0.40M on Medium and 100 / 0.23M on Low.
- The frame ms are from llvmpipe (CPU software) and are not representative.

## Honest flaws
- The detail is procedural and parametric, not hand-sculpted. The buildings read richer up close, but the character pieces are simplified compared with the beauty sheets: there is no statuary, no stained-glass imagery and no ivy. The temple's large white surfaces look flat.
- Normal maps are derived from albedo luminance, so they are subtle and generic, not authored.
- The slot atlas has 256 px per slot; a "2048" atlas means 64 tinted slots, not higher texel density per surface. Close-ups of walls are still soft.
- Tri counts: mage (47.6k) and temple (42.2k) are over the ~40k target. The round buildings (windmill, observatory, gate tower) are light at 3–5k.
- Terrain is generic, not fitted to the real game heightmap or zone layout. The peaks read small at distance in my test framing. The cliff piece reads like a stacked slab from the side. In the test, the shore piece sits mostly under the water plane, so place it with the waterline at y=0.
- Tree LOD1 is a big visual step down from High, and LOD2 reuses the old impostor tiles.
- I didn't measure on a real phone. The asset size is about 100 MB of GLBs (positions are float32, indices uint32); Godot import compresses textures but not the source repo size.
