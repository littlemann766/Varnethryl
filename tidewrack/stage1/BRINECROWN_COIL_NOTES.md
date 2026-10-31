# Brinecrown Coil: mesh notes for Lucian (rigging)
This is an original sea serpent, designed for VARNETHRYL: teal scale tube, pale belly, red dorsal fins and gill frills, and a "brine crown" of 7 coral-bone horns sweeping back.

- Rig this one: meshes/brinecrown_coil_rest.glb (5,526 tris, single surface, vertex colours), plus _lod1 (2,486 tris, 45%).
  - Rest pose is straight along +Z, with the head at z 0 to +4 and the tail at z -96. +Y is up and the belly is down. Units are metres. Length is about 100 m, max body radius 3.4 m.
  - The body is a 14-sided tube with 140 evenly spaced rings (about 0.7 m apart), so there's plenty of loops for bending.
- Suggested joints: meshes/brinecrown_coil_joints.json lists 25 spine joints every 4 m (spine_00 at the tail to spine_24 at z 0), plus head, jaw and crown.
  - The jaw is not split from the head yet. The lower snout is a separate shape: cut it, or weight it to jaw.
  - Fins and frills are separate strips. Weight each one to its nearest spine joint.
  - The crown horns are rigid to head, or to crown for a flare animation.
- Hero pose: meshes/brinecrown_coil_hero.glb is for the renders only (three humps, head reared about 25 m up). Don't rig it.
- Arena: meshes/arch_coil_arena.glb has 11 sea stacks on a ring of radius ~95 m, with grassy caps and two rock arches. Its centre is in stage1_manifest.json under props.coil_arena.
  It is in open water about 110 m offshore, moved from the map mark so the fight isn't on the beach.
- Not done: UVs or textures (vertex colour only), skinning, blendshapes, and colliders (use capsules along the spine joints).
