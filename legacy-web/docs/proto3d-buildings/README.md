# Varnethryl 3D buildings (branch `buildings-3d`)

26 low-poly, walk-in buildings built in code from the boss's building sheets and beauty renders. They replace the blocky village in
`proto3d.html` (add `?oldvillage` to the URL to get the old one). The village grew from 64x64 to 120x120 (`WORLD = 60`) to hold them.

| file | what |
|---|---|
| `www/proto3d/bldtex.js` | procedural canvas textures: stone blocks + mortar + moss, pale limestone, half-timber, dark wood, blue slate shingles, floors, carpet, sigil, stained glass, banner (lion crest cut from the Aldric sheet, `tex/emb_lion.png`) |
| `www/proto3d/bldkit.js` | `Builder`: world-scaled UVs, hollow walls with a real door gap, gable/hip/cone roofs, round shells, furniture kit, props, **merge pass** (every group collapses to one mesh per material), cutaway (roof hides + walls go see-through when the hero is inside), local->world collider transform, interiors only drawn near the hero |
| `www/proto3d/buildings.js` | the 26 building definitions, village layout (`BUILDING_DEFS`), walls + watchtowers |
| `www/proto3d/bldview.html/js` | standalone viewer used by the render tools (`?b=inn`) |
| `tools/render_buildings.py`, `compare_buildings.py`, `montage_buildings.py` | exterior / side / back / interior renders and sheet-vs-3D comparison images |
| `tools/buildings_test.py` | Playwright test: walks into every building through its door and checks the walls are solid |

Buildings: Guild Hall, Grand Library, Town Hall, Mage Academy*, Treasury, Castle Keep*, Observatory, Crypt (links to the Dusk Hollow / Veyra quest:
`builder.quest = 'veyra'`, the page fires a `p3d-enter` event with the building id), Market Provisioner, Apothecary, Bakery, Inn, Blacksmith, Temple,
Training Hall, Colosseum, Thieves' Den, Farmhouse, Barn, Stables, Windmill (spinning sails), Village Houses x4, Lighthouse, Port (pond, pier, boats, tavern),
Gatehouse (walkable tunnel gate), Fountain Monument (blue lion), Town Walls + 4 enterable corner Watchtowers + 11 plain towers.  (*simplified)

Notes / limits: upper floors and galleries are visual (stairs and mezzanines are not climbable); the colosseum seating is solid and the
pit is reached through the gate tunnel; GLB export of buildings was not done because they are generated procedurally at load (cheaper than shipping GLBs).
Collision: each building adds box/circle colliders (wall segments, furniture) in world space, so the existing hero collision works unchanged.
