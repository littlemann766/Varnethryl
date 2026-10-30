# Hands fix (palms up / twisted wrists), 2026-10-30 ET
Cause: retarget.py builds the per-bone correction C from bone directions. The 21-bone game rigs (and Darius) have no finger bone,
so the hand's target direction fell back to the bone's local +Y. These glTF rigs have world-aligned (identity) rest bones, so +Y is a world axis, not the hand direction.
Result: in every mocap clip (idle/walk/run) the hand was turned 105-134 deg off the forearm (palm flipped up/out). The authored game clips (attacks, skill, hit, death, fly) were fine: 0 deg.
Measure: hand rotation relative to forearm, relative to the rest relationship, every 2nd frame (palm_measure.py). The bone axes carry no palm info on these rigs (identity rest), so the wrist angle is the reliable signal.
Fix: per clip and side, the constant mean wrist offset is removed from the hand rotation curves (hand_twist_fix.py), keeping the clip's own wrist motion.
Then the upper arms were abducted only where hands now touched the thighs (vx3/autofix.py). The same arm curves were copied to LOD1/LOD2 (export_copy_arms.py). Legs and feet were not touched, so foot locking is unchanged.
Files: capes_v5/ (Darius, Selene, villain LOD0/1/2 fixed; Owner and guard copied unchanged). Batches: /workspace/godot-art/voxel_cast/batch{1,2,3}/glb_sealed_v2/.
Checks: checks/*.json (arm-in-leg / cape-in-body, before vs after). Godot 4.7.2 headless import of all 51 files: 0 errors, 0 warnings.
