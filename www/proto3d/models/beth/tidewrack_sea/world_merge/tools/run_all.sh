# Stage 10/11 island + straight-line pipeline (Beth). Usage: bash run_all.sh <tidewrack_sea dir> <work dir>
# TW env = the game tidewrack dir (landings.json + stage manifests); default /tmp/gv2/tidewrack
# Every step starts from the meshes_v2_backup originals, so the whole thing can be re-run.
set -e; T=$(dirname "$0"); R=$1; W=$2; mkdir -p $W; export LAND3M=$W/world_land3m.npy
find $R -name "*_prewobble.glb" -delete; rm -f $R/world_merge/wobble_runs.json
python3 $T/restore.py $R
python3 $T/island_carve.py H $T/world_h_before.f32 $W/H_after.f32
python3 $T/resample_frost.py $R
python3 $T/carve_meshes.py $R
python3 $T/reseat_props.py $R $T/world_h_before.f32 $W/H_after.f32
python3 $T/build_floes.py $R $W/H_after.f32
python3 $T/floe_trim.py $R $W/H_after.f32
python3 $T/isl_blend.py $R
python3 $T/shore_maps.py $R
for i in 1 2 3 4; do
  python3 $T/straight_scan.py $LAND3M -3200 -3200 3 $W/scan_$i.json world
  python3 $T/wobble_runs.py $R $W/scan_$i.json $W/exempt_$i.json
  python3 $T/shore_maps.py $R
done
python3 $T/straight_scan.py $LAND3M -3200 -3200 3 $W/scan_final.json world
