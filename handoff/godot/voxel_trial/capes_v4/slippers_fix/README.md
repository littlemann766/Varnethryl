Owner slippers fix (test 30). Cause: the slipper cubes (foot_L/R, toe_L/R bones) sampled the source texture per cube and got 13 palette colours,
incl. 1,856 skin-tan faces (239,165,115) scattered among ~10 near-identical dark browns -> random tan/brown speckle. Not z-fighting (sealed mesh, opaque, backface cull) and not missing faces.
Fix: those 6,184 faces now use 2 existing palette cells: slipper brown (99,58,25), sole (82,41,16) on the bottom 2 cm. Nothing else changed (face, suit, hood plain, capes, clips).
Batch seal paths: /workspace/godot-art/voxel_cast/batch{1,2,3}/glb_sealed/ (too big for git, ~610 MB).
