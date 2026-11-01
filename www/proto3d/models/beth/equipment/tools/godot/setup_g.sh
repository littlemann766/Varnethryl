G=/tmp/l3g; mkdir -p $G/heroes $G/equipment $G/loot/gear
cp /workspace/vmain/voxel/*_voxel.glb $G/heroes/ 2>/dev/null
rm -rf $G/equipment/meshes $G/equipment/fit; cp -r /tmp/l3/www/proto3d/models/beth/equipment/{meshes,fit} $G/equipment/
cp -r /tmp/l3/www/proto3d/models/beth/loot/gear/{meshes,gear_attach.json} $G/loot/gear/
cp /workspace/godot-art/loot3_tools/godot/dress.gd $G/
printf 'config_version=5\n[application]\nconfig/name="beth_dress"\nrun/main_scene="res://main.tscn"\n[display]\nwindow/size/viewport_width=420\nwindow/size/viewport_height=560\n' > $G/project.godot
printf '[gd_scene load_steps=2 format=3]\n[ext_resource type="Script" path="res://dress.gd" id="1"]\n[node name="main" type="Node3D"]\nscript = ExtResource("1")\n' > $G/main.tscn
cd $G && timeout 770 godot --headless --path . --import > /tmp/l3w/imp.log 2>&1
