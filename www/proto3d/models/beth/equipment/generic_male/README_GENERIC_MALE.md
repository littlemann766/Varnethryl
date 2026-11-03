# Generic shared MALE armour set (plate, v1)
One set of meshes for every male hero. It replaces the per-hero fitted (puffy) shells. Awaiting the boss's review, so it is not wired into the game yet.

Pieces (`generic_male_plate_<piece>.glb` + `_lod1.glb`): helm, chest, shoulder_L/R, glove_L/R, leg_L/R, boot_L/R.
- helm: great helm with a sugarloaf face keel, a recessed eye slit with a nasal bar, breaths, a brow band, a crest ridge and a riveted rim.
- chest: breastplate with keel and pecs, backplate, plackart, belt, 3 faulds, mail skirt and a 2-lame gorget.
- shoulder: flared domed pauldron with 3 tight lames and a rerebrace with a strap.
- glove: couter, vambrace with straps, flared cuff and lamed mitten gauntlet.
- leg: cuisse over mail with straps, poleyn and side wing.
- boot: ridged greave with straps and a lamed pointed sabaton.

Skinning: built in Darius' rest space (male reference, `darius_voxel_noweapon.glb`, read only). Weights are interpolated along each bone chain, so a piece stretches between any male rig's joints. Every core bone on the hero rigs has identity rest rotation.

Godot (`tools/generic_armor/gen_dress.gd`):
- `attach()` rebinds by bone NAME. It strips Godot's `_2` rename and substitutes missing bones (upperChest -> chest, spine2 -> spine, ...) using the reference bind of the substitute.
- `group_stats()` computes one depth shift per hero, plus a head shift for the helm, because Rook's and Orin's skeletons sit 7–13 cm behind their modelled bodies.
- `hide_body()` hides body triangles by dominant bone, per equipped piece. Capes stay.

Colour is COLOR_0 vertex colour, so keep `vertex_color_use_as_albedo` and `vertex_color_is_srgb = true`. Tri counts are in `generic_male_plate_tris.json`: every High piece is 4.0–6.4k and every lod1 is 45%.
