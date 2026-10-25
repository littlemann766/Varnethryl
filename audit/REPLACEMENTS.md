# REPLACEMENTS — old asset → Beth kit asset

All kit assets share ONE material (`beth_kit_atlas`: MeshStandard, metalness 0, roughness 0.85, 1024² atlas webp+png, vertex colours, alphaTest 0.5, double-sided, `fx('wild')` wind).
Because the material is shared, every kit piece in a 64 m chunk merges into the **same** chunk mesh, so swapping art never adds a draw call.

## Per-prop (scenery.js variants → kit) — triangles per instance
`new` column = full / lod1 / billboard. "Saving" compares with the LOD variant the outskirts actually place today (makeVariant(..., lod=true)); a **negative** number means the kit piece is heavier.
| old | new | new tris | saving per instance |
|---|---|---|---|
| `trees/oak` (504 full / 222 LOD) | `tree_oak_a / _b / _autumn / _yellow / _red` | 290 / 176 / 4 | -68 vs the LOD the outskirts use |
| `trees/apple` (478 full / 244 LOD) | `tree_apple_blossom, tree_oak_a, tree_oak_red` | 290 / 176 / 4 | -46 vs the LOD the outskirts use |
| `trees/birch` (491 full / 344 LOD) | `tree_birch_a` | 278 / 110 / 4 | +66 vs the LOD the outskirts use |
| `trees/pine` (199 full / 142 LOD) | `tree_pine_a / _b` | 100 / 36 / 4 | +42 vs the LOD the outskirts use |
| `trees/cypress` (276 full / 114 LOD) | `tree_pine_b` | 100 / 36 / 4 | +14 vs the LOD the outskirts use |
| `trees/dead` (259 full / 234 LOD) | `tree_dead_a` | 52 / 28 / — | +182 vs the LOD the outskirts use |
| `bushes/round` (224 full / 164 LOD) | `bush_a` | 88 / — / — | +76 vs the LOD the outskirts use |
| `bushes/hedge` (212 full / 152 LOD) | `bush_a / bush_b` | 88 / — / — | +64 vs the LOD the outskirts use |
| `bushes/spiky` (64 full / 64 LOD) | `bush_a` | 88 / — / — | -24 vs the LOD the outskirts use |
| `flowers/daisy` (214 full / 214 LOD) | `flowers_white` | 8 / — / — | +206 vs the LOD the outskirts use |
| `flowers/tulip` (78 full / 78 LOD) | `flowers_red / _yellow` | 8 / — / — | +70 vs the LOD the outskirts use |
| `flowers/lavender` (102 full / 102 LOD) | `flowers_purple` | 8 / — / — | +94 vs the LOD the outskirts use |
| `flowers/bellflower` (98 full / 98 LOD) | `flowers_blue` | 8 / — / — | +90 vs the LOD the outskirts use |
| `flowers/grass` (15 full / 15 LOD) | `grass_a / grass_dry` | 6 / — / — | +9 vs the LOD the outskirts use |
| `rocks/boulder` (172 full / 112 LOD) | `boulder` | 320 / — / — | -208 vs the LOD the outskirts use |
| `rocks/stone` (172 full / 112 LOD) | `rock_small / rock_mossy` | 80 / — / — | +32 vs the LOD the outskirts use |
| `rocks/cluster` (240 full / 60 LOD) | `rock_small` | 80 / — / — | -20 vs the LOD the outskirts use |
| `rocks/slab` (64 full / 64 LOD) | `rock_slab` | 80 / — / — | -16 vs the LOD the outskirts use |
| `rocks/standing` (108 full / 108 LOD) | `standing_stone` | 80 / — / — | +28 vs the LOD the outskirts use |
| `props/barrel` (232 full / 232 LOD) | `barrel` | 132 / — / — | +100 vs the LOD the outskirts use |
| `props/crate` (296 full / 296 LOD) | `crate` | 60 / — / — | +236 vs the LOD the outskirts use |
| `props/lamp` (244 full / 244 LOD) | `lamp_post` | 60 / — / — | +184 vs the LOD the outskirts use |
| `props/fence` (64 full / 64 LOD) | `fence_2m` | 48 / — / — | +16 vs the LOD the outskirts use |

Note on sign: the last column is old − new, so negative = kit is heavier. Kit oaks, apples, bushes-spiky and the boulder are heavier up close than the procedural LODs; flowers, pines, dead trees, barrels and crates are much lighter, but they now get a
4-tri billboard past 55–90 m (old trees drew full geometry to 140 m), so visible totals still drop (below).

## Scene-level swaps (measured, same frame toggle, `audit/landscape_cost.json`)
| old | new | draw calls | visible triangles |
|---|---|---|---|
| main.js town cone trees: 3 InstancedMesh (trunk, leaf, leaf2), 230 trees, 12.0k tris | ONE merged mesh `beth-town-trees` (pine lod1 ×3 : oak/birch lod1 ×1), 14.4k tris | **3 → 1 (−2)** | +2.4k (+4.9k incl. shadow pass) |
| townlands chunks (518 meshes, procedural variants, cast+plain per 64 m) | kit chunks (cast+plain per 64 m, + tree-billboard layer per 128 m), +70 landscape clusters | outskirts **20–22 → 13–15 (−6/−7)**; port 18 → 8 (−10); volcano 15 → 11 (−4); town 6 → 2–3 | outskirts ≈ equal (−3k … +5k) **while adding 70 clusters**; port −6.8k; volcano −5.4k |
| townlands ice shards (MeshPhong, emissive 0x10283e) | `frost/ice_rock`, `cluster_frost` | proposed, not wired | — |
| townlands volcano ember slabs / basalt (emissive) | `volcano/lavacrust_rock` (cracks painted in albedo, no emissive), `basalt_columns`, `cluster_volcano` | proposed, not wired | — |
| harbor box piers | `port/dock_10m`, `cluster_port_dock` | proposed, not wired | — |
| port-ships galleon (28 meshes) | `port/ship_cog` (1 mesh, 142 tris) | 28 → 1 if accepted | — (far simpler look; your call) |
| hobcamps.js tents/palisade | `hobcamp/hob_tent`, `hob_palisade`, `hob_firepit`, `cluster_hobcamp` | proposed, not wired | — |

## Estimated totals (town_start / outskirts average)
Draw calls: town 419 → ~415 (art share 6 → 2–3); outskirts ~200–400 → −6 to −10 each. **Art alone cannot reach 300.**
With Lucky's code levers (one InstancedMesh set for all ladders: −20…−60; fewer building material classes: up to −100 of ~180) town could reach ≈250–300.

## Round 3 (Beth): Godot-targeted
| old (buildings.js / scene) | new asset | status |
|---|---|---|
| guildhall, library, townhall, mage, treasury, crypt, market, apothecary, bakery, inn, smithy, training, keep, temple, observatory, colosseum: the textured ext + roof meshes | `buildings/bld_<id>.glb` (walls + roof nodes, one atlas, emissive window mask) | built, Godot import verified, not wired |
| fountain, port, gatehouse body, town walls | none yet | not done |
| plain cobble street edges and plaza rim | `dressing/cobble_edge_2m`, `curb_2m` via PLACEMENT_dressing_town | placed (JSON), not wired |
| (new) street lanterns, wells, market stalls, benches, planters, banner poles, signposts, milestones, wall lanterns, rubble | `dressing/*` | placed (JSON), not wired |
| (new) moss, crack, dirt, grime, soot, leaves and puddle decals | `decals/*` on decals/atlas (alpha cut) | placed (JSON), not wired |
| mountain/cliff scenery (scenery.js rocks and boulders at large scale) | `terrain/mountain_peak_*`, `volcano_cone_flank`, `cliff_ridge_60m`, `scree_slope`, `grass_mound`, `rock_arch` (+LODs) | built, no placement |
