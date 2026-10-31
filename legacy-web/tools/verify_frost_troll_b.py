#!/usr/bin/env python3
"""Regression guard for Frost Troll B's approved replacement GLB.
Pure stdlib: runs on GitHub Actions before Android packaging or web publishing.
Confirms the snake was replaced by an actual bipedal skinned animated troll.
"""
import json
import math
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / 'www/proto3d/models-new/frosttroll_b.glb'
if not MODEL.is_file():
    sys.exit('FAIL: Troll B is missing from the shipped game.')
raw = MODEL.read_bytes()
if len(raw) > 12 * 1024 * 1024 or len(raw) < 100_000:
    sys.exit(f'FAIL: implausible mobile GLB size ({len(raw)} bytes).')
magic, version, total = struct.unpack_from('<4sII', raw)
assert magic == b'glTF' and version == 2 and total == len(raw), 'GLB header/length invalid'
size, typ = struct.unpack_from('<II', raw, 12)
assert typ == 0x4E4F534A and size % 4 == 0, 'GLB JSON chunk invalid'
gltf = json.loads(raw[20:20 + size])
bin_offset = 20 + size
bin_size, bin_type = struct.unpack_from('<II', raw, bin_offset)
assert bin_type == 0x004E4942, 'Missing GLB binary chunk'
assert bin_offset + 8 + bin_size == len(raw), 'GLB binary payload truncated'
blob_off = bin_offset + 8
assert len(gltf.get('skins', [])) > 0, 'Mesh must have a real skeletal rig'
assert max(len(s.get('joints', [])) for s in gltf['skins']) >= 60, 'Troll B is not the approved 71-bone rig'
nodes = gltf['nodes']
names = {n.get('name') for n in nodes}
needed = {'mixamorig:Head', 'mixamorig:Neck', 'mixamorig:Spine', 'mixamorig:Hips',
          'mixamorig:LeftFoot', 'mixamorig:RightFoot'}
assert needed <= names, 'Bipedal troll anatomy missing (possible serpent model)'
head = next(n for n in nodes if n.get('name') == 'mixamorig:Head')
neck = next(n for n in nodes if n.get('name') == 'mixamorig:Neck')
assert head.get('translation', [0, 0, 0])[1] > 0.12, 'Refined head correction lost'
assert neck.get('translation', [0, 0, 0])[1] > 0.34, 'Refined neck correction lost'
assert any(m.get('primitives') for m in gltf.get('meshes', [])), 'No visible geometry'
mesh = gltf['meshes'][0]['primitives'][0]
pos = gltf['accessors'][mesh['attributes']['POSITION']]
extents = [hi - lo for lo, hi in zip(pos['min'], pos['max'])]
assert extents[1] > extents[2] * 1.25, 'Troll mesh is suspiciously low/long'
clips = {a['name'].lower(): a for a in gltf.get('animations', [])}
assert {'walking', 'running'} <= clips.keys(), 'Walking and Running clips are required'
def duration(clip):
    sampler = clip['samplers'][0]
    a = gltf['accessors'][sampler['input']]
    view = gltf['bufferViews'][a['bufferView']]
    assert a['componentType'] == 5126, 'Animation time track is not float32'
    offset = blob_off + view.get('byteOffset', 0) + a.get('byteOffset', 0)
    stride = view.get('byteStride', 4)
    value = struct.unpack_from('<f', raw, offset + (a['count'] - 1) * stride)[0]
    assert math.isfinite(value), 'Nonfinite animation duration'
    return value
run_time = duration(clips['running'])
assert 0.80 <= run_time <= 1.05, f'The refined 0.85s run gait was lost: {run_time}'
for a in clips.values():
    assert len(a['channels']) > 100, 'Whole-body bone animation missing'
source = (ROOT / 'www/proto3d/main.js').read_text()
assert '["n:frosttroll_b", "Frost Troll (B)", "proto3d/models-new/frosttroll_b.glb"]' in source
assert "'n:frosttroll_b': { walk: 0.52, run: 1.10 }" in source
host = (ROOT / 'www/proto3d/fight.js').read_text()
assert "if (e.key === 'frosttroll_b') lean =" in host
print(f'PASS: Frost Troll B is a distinct {len(raw):,} byte animated biped with {len(gltf["skins"][0]["joints"])} bones, '
      f'{extents[1]:.2f}m native height and {run_time:.2f}s refined running loop.')
