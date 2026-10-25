# Tripo diorama split (source: user upload user_1024.glb, 53,356 tris, one 4096 basecolor)
Split method: topology + 6 mm vertex-proximity clustering, region boxes for mountain/volcano/great tree,
topological components for the 11 houses on the village island. 0 faces unassigned.
Each piece: centered on X/Z, base at y=0. `<name>.glb` = source units (1 unit = diorama), `<name>_game.glb` = metres,
`_lod1` (~50% tris, 1024 tex) and `_lod2` (~20% tris, 512 tex). Pieces under 200 tris keep their full mesh in the LODs.
Textures: crop of the original atlas (UVs remapped), JPEG q88, unlit-looking PBR (metal 0, rough 0.9, double-sided).

Scales (Owner = 1.905 m): mountain x1100 (~407 x 254 x 416 m backdrop peak); volcano x940 (~275 x 80 x 291 m,
crater rim r~55 m at 80 m, floor ~39 m, titan leash r122 sits on the outer slopes); great_tree x300 (~79 x 67 x 83 m landmark);
houses / village / trees x150 (houses 5-12 m wide, 7-10 m tall; pines ~16 m); boats x80; rocks x60; fences, bushes, barrels,
crates, wagon, signpost, pole x40 (fence 1.45 m, barrels 1.3 m).
volcano_lava_pool_game.glb: emissive disc r34 m sitting on the crater floor (optional).
Manifest with tri counts and sizes: tripo_manifest.json
