#!/bin/bash
B=/workspace/beth-world/www/proto3d/models/beth/hi/buildings; T=/workspace/beth-world/www/proto3d/models/beth/tripo; P=/workspace/beth-world/audit/cardstyle/tools/bake.py
for n in house1 house2 house3 house4 inn smithy bakery apothecary guildhall market townhall temple gate_tower keep farmhouse barn lighthouse library thieves windmill crypt observatory treasury stables training mage colosseum; do
  python3 $P $B/bld_$n.glb $B/bld_${n}_card.glb 2048 && python3 $P $B/bld_${n}_lod1.glb $B/bld_${n}_card_lod1.glb 1024 && python3 $P $B/bld_${n}_lod2.glb $B/bld_${n}_card_lod2.glb 512 && echo "DONE $n"
done
for f in $T/house_*_game.glb; do b=${f%_game.glb}; python3 $P $f ${b}_card.glb 1024 && python3 $P ${b}_game_lod1.glb ${b}_card_lod1.glb 512 && python3 $P ${b}_game_lod2.glb ${b}_card_lod2.glb 256 && echo "DONE $(basename $b)"; done
echo ALLDONE
