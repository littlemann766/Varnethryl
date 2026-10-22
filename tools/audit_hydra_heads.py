#!/usr/bin/env python3
"""Read-only audit of the actual compressed five-head Hydra GLB.

A combat pattern per head does not mean the head has independently movable
geometry. Inspect the glTF node hierarchy, skins and clip channels before
attempting to rig or reposition any part of the approved model.
"""
import argparse
import gzip
import json
import re
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSET = ROOT / 'www/proto3d/models-new/hydra_restored_mobile.glb.gz'

def inspect():
    blob = gzip.decompress(ASSET.read_bytes())
    if len(blob) < 20:
        raise ValueError('Hydra GLB is truncated')
    magic, version, length = struct.unpack_from('<4sII', blob)
    if (magic, version, length) != (b'glTF', 2, len(blob)):
        raise ValueError('Hydra GLB header or length mismatch')
    json_length, kind = struct.unpack_from('<II', blob, 12)
    if kind != 0x4e4f534a or 20 + json_length > len(blob):
        raise ValueError('Hydra GLB has a corrupt JSON chunk')
    doc = json.loads(blob[20:20 + json_length].decode('utf-8'))
    nodes = doc.get('nodes', [])
    meshes = doc.get('meshes', [])
    skins = doc.get('skins', [])
    animations = doc.get('animations', [])
    head_names = re.compile(r'(head|neck|jaw|tongue)', re.I)
    candidates = [
        {'index': i, 'name': n.get('name', ''), 'mesh': n.get('mesh'),
         'child_count': len(n.get('children', []))}
        for i, n in enumerate(nodes) if head_names.search(n.get('name', ''))
    ]
    skinned_joints = {joint for skin in skins for joint in skin.get('joints', [])}
    animated_targets = {
        ch.get('target', {}).get('node')
        for clip in animations for ch in clip.get('channels', [])
    }
    distinct_head_joints = [
        x['index'] for x in candidates
        if x['index'] in skinned_joints and x['index'] in animated_targets
    ]
    report = {
        'asset': str(ASSET.relative_to(ROOT)),
        'decoded_bytes': len(blob),
        'nodes': len(nodes), 'meshes': len(meshes),
        'mesh_nodes': [
            {'index': i, 'name': node.get('name', ''), 'mesh': node['mesh']}
            for i, node in enumerate(nodes) if 'mesh' in node
        ][:70],
        'skins': len(skins), 'animations': len(animations),
        'clip_names': [a.get('name', '') for a in animations],
        'head_named_nodes': candidates[:70],
        'head_animated_skin_joints': distinct_head_joints,
        'independent_head_rig_verified': len(distinct_head_joints) >= 5,
        'limitation': (
            'Names alone do not prove five correctly weighted independent necks; '
            'a visual/animation review is still needed.'
        )
    }
    return report

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--report', default='hydra-rig-audit.json')
    args = ap.parse_args()
    r = inspect()
    Path(args.report).write_text(json.dumps(r, indent=2) + '\n')
    print('HYDRA MODEL:', r['nodes'], 'nodes;', r['meshes'], 'meshes;',
          r['skins'], 'skins;', r['animations'], 'animation clips')
    print('MESH NODES:', json.dumps(r['mesh_nodes']))
    print('HEAD / NECK NODES:', json.dumps(r['head_named_nodes']))
    print('FIVE ANIMATED HEAD JOINTS:', r['independent_head_rig_verified'])
    if not r['independent_head_rig_verified']:
        print('ACTION NEEDED: five independently controlled heads are NOT verified; '
              'do not distort the approved chest or replace the model with a primitive rig.')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
