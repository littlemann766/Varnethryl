# VARNETHRYL v1.5.33 (a8aa181) — town & between-zone profile

Measured by Beth, 2026-10-24, headless Chromium (SwiftShader), 960×540, after *Play Solo*, hero teleported to each spot, game camera.
`renderer.info.render.calls/triangles` include the shadow pass. Totals wobble ±50 calls between runs (NPC crowd, heroes, Balthrix), so
the landscape column was measured by toggling only the landscape meshes off in the same frame (`audit/lscost.py`).

| spot (x,z in `spots.json`) | total calls | total tris | landscape calls before → after kit | landscape tris before → after kit |
|---|---|---|---|---|
| town_start | 419 | 369,190 | 6 → 2 | 23,920 → 28,824 |
| town_center | 383 | 367,798 | 6 → 3 | 23,920 → 28,860 |
| town_east | 327 | 368,960 | 6 → 3 | 23,920 → 28,856 |
| outskirts_east | 416 | 358,282 | 21 → 15 | 34,723 → 39,626 |
| outskirts_north | 185 | 325,262 | 20 → 13 | 36,027 → 36,480 |
| outskirts_sw | 395 | 346,541 | 22 → 15 | 29,465 → 26,540 |
| port_edge | 245 | 316,353 | 18 → 8 | 22,921 → 16,118 |
| volcano_edge | 179 | 181,976 | 15 → 11 | 8,182 → 2,812 |

## Where the draw calls actually go (town_start, 419 calls)
| source | owner | meshes in scene | real calls (toggle test) | notes |
|---|---|---|---|---|
| Building merged chunks (`mergeStatic` / bldkit, Lambert + map) | Lucky | ~550 meshes, 138k tris total | ~180 visible in town (≈158k tris) | **the #1 cost.** One mesh per zone×material class; many tiny materials per building. |
| Ladders (`ladders.js`, 3 InstancedMesh **per ladder** × 59) | Lucky | 177 | **21 in town, 61 at outskirts_east** | One shared InstancedMesh per part type (3 total, all 59 ladders) would save ~20–60 calls. |
| Landscape chunks (`townlands.js`, 64 m chunks × cast/plain) | art | 518 | 6 in town, 15–22 outside | Already well batched; heaviest content is 740 trees (≈200–500 tris each, procedural) + 890 flower patches (78–214 tris each). |
| Town cone trees (`main.js`, 3 InstancedMesh, 230 trees) | art/Lucky | 3 | 3 | 52-tri cones, the ugliest thing on screen. |
| Terrain `walkable-hills-mountains-valleys` | Lucky | 1 | 1 | 41k tris, always drawn. |
| `BALTHRIX_RAISED_PERIMETER_TRAIL` | Lucky | 1 | 1 | 25k tris, always drawn. |
| Heroes / NPC skinned meshes, HUD previews | Lucian/Lucky | many | not measured (estimate: the rest of the ~419) | Each hero is 6–12 materials (steel/gold/hair/m3…). |
| Ships (`port-ships.js`, 28-part galleons) | Lucky | 28–70 | near port only | Not merged: 28 meshes per galleon. |

## Heavy / ugly props (procedural, `scenery.js`)
Per-variant triangles (full / LOD): oak 504/222, birch 491/344, apple 478/244, dead 259/234, pine 199/142, cypress 276/114, daisy 214, mushrooms 236,
crate 296, logs 296, well 342, lamp 244 (+ emissive glow strip). Flowers are the worst value: 214 tris for a 0.5 m patch, 890 of them in the outskirts.
Ugly: main.js cone trees (single-colour cones), flat empty land between zones (only scatter), emissive ice shards / ember slabs (break the no-emissive rule).

## Conclusion
The **300-call phone target cannot be hit by art alone**: art (landscape + trees) is only 6 calls in town. The big levers are code:
building chunk material count (~180), per-ladder instancing (~20–60), hero material counts (not measured). Art can cut its own share and lower
triangles while filling the empty land for free, which is what the kit does.
