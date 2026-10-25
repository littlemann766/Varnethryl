# Roads (Beth) - replaces main.gd _roads()
Bug (boss screenshot): old _roads() lays flat 8.8 m quads every 4 m with heights from height(), but the rendered
terrain is a 10 m-grid triangle mesh. 1811 of 7839 probe samples (23%) had terrain ABOVE the road (worst 0.58 m at
(-534,-12), (556,-11), (72,-442)) -> green triangle spikes; quads also don't join at bends (gaps/void, jagged edges).
Fix: road_builder.gd builds Catmull-Rom smoothed ribbons with shared cross-sections, every vertex on the rendered
terrain triangle surface (+6 cm), 1.8 m alpha grass skirt with noisy edge, dirt outside walls / cobble inside r<215.
LODs: per 64 m chunk, High (1 m x 13 verts, 0-140 m), lod1 (2.5 m x 7, 140-380 m), lod2 (6 m x 5, 380 m+), visibility ranges.
Build ~0.8 s, 168 chunks, 102k tris across all LODs (only nearby chunks draw High).
Files: road_builder.gd, road.gdshader, textures/{dirt,cobble}_{albedo,normal,rough}.png, edge_noise.png, make_tex.py.
## Lucky
1. Copy this folder to res://assets/roads/ (road_builder.gd, road.gdshader, textures/).
2. In scripts/main.gd replace the body of `func _roads()` with:
       add_child(load("res://assets/roads/road_builder.gd").new().build(self, ROADS))
   (must run after _terrain(); it already does). ROADS / _road_dist / height() unchanged, no collision change (hero walks on the heightmap).
3. If you ever change _terrain() N=140 / S=1400, update N/S at the top of road_builder.gd (it mirrors that triangulation).
Before/after: beth-world/audit/roads/road_before_after.jpg
