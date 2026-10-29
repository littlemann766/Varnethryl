cd /workspace/capes; B=/workspace/tools/blender-4.2.3-linux-x64/blender
for a in "owner 10 5" "selene 10 5" "darius 10 5" "holyknight_villain 10 5" "town_guard 6 3"; do set -- $a; rm -f out/$1.done.json out/$1.blend; $B -b -P capes.py -- $1 $2 $3 2>&1 | grep -E "Error|line [0-9]"
CL=$($B -b out/$1.blend --python-expr "import bpy;print('CL',','.join(a.name for a in bpy.data.actions))" 2>/dev/null | grep ^CL | cut -c4-)
$B -b -P check.py -- out/$1.blend $CL /tmp/c_$1.json 2>&1 | grep CHECK | python3 -c "
import sys,json;d=json.loads(sys.stdin.read()[6:]);print('$1',{k:(v.get('cape_in_body_verts_max'),v.get('cape_frames_over24')) for k,v in d.items() if k!='rest_baseline'})"; done
