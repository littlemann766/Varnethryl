# Boss reference armour (Tripo "fantasy knight"), split into male and female, then slotted and skinned
**Source:** one static mesh, 102,940 tris, holding two figures side by side. It has no rig or skin. It came with base colour (jpg), roughness/metal (png, 19 MB) and normal map (png) textures.

**Split by loose part** (3,757 parts, split by x):
- male: 61,734 tris
- female: 41,206 tris

The full-res splits are in `/workspace/uploads/ref_{male,female}.glb` on the box and are not committed.

**Fit** (`tools/ref_armor/fit.py`):
- **Reference rigs:** male on Darius (`darius_voxel_noweapon`), female on Talia (`talia_voxel`, symmetric rest pose). Both rigs were only read.
- **Scaling:** each figure is scaled to head + 20 cm and centred on the torso.
- **Arms:** each vertex goes to the nearest bone segment. The arms are re-aimed from the ref's own shoulder-to-hand line onto the rig's arm bones.
- **Weights:** one bone per segment, with a 20% blend at the joints.
- **Slots:** each face goes to the majority slot of its vertices. Small loose plates (under 1,500 faces) move as a whole.
  - helm = head and neck
  - shoulder = upperArm
  - glove = forearm and hand
  - leg = thigh
  - boot = shin and foot
  - chest = everything else: torso, wings, tabard, tassets
- **Budget:** each piece is decimated to at most 7.6–7.9k (helm and chest) or 6.5k (others).
  - Pieces under 3.6k were split once with simple subdivision to reach the 3.5k minimum. That adds triangles but no new shape.
  - lod1 = 45%.

**Material:**
- Kept the base-colour texture, downscaled to 1024 and embedded per piece as JPEG.
- Dropped the roughness/metal and normal maps. Mobile uses constant metallic 0.6 and roughness 0.4.
- No COLOR_0, so the vertex colour is white. The material keeps `vertex_color_use_as_albedo` and `vertex_color_is_srgb = true`, and `gen_dress.gd` copies `albedo_texture`.

**Godot:**
- The same `tools/generic_armor/gen_dress.gd` path is used (bone-name rebind and bone-based body hide).
- Each job has a `prefix` of `ref_male_` or `ref_female_`.
- `ref_reset` restarts the per-hero depth reference: Darius for males, Talia for females.
