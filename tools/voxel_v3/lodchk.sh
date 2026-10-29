B=/workspace/tools/blender-4.2.3-linux-x64/blender
for f in town_guard_voxel_lod1 town_guard_voxel_lod2 holyknight_villain_voxel_lod1 holyknight_villain_voxel_lod2; do
 case $f in town*) CL=attack,idle,run,walk;; *) CL=attack,death,hit,idle,run,walk;; esac
 $B -b -P check1.py -- glb/$f.glb.blend $CL glb/$f.cape_checks.json > /dev/null 2>&1 &
done; wait; echo DONE
