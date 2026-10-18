#!/bin/sh
# usage: tools/swap_owner.sh /workspace/rigged/owner_new4   (path without extension)
set -e
cp "$1.glb" "$(dirname "$0")/../www/proto3d/models-new/owner.glb"
cp "$1.cloth.json" "$(dirname "$0")/../www/proto3d/models-new/owner.cloth.json"
echo "Owner swapped from $1"
