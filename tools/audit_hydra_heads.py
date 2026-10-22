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


def find_connected_surfaces(doc, blob, json_length):
    """Count connected triangle components without changing the original mesh."""
    views = doc.get('bufferViews', [])
    accessors = doc.get('accessors', [])
    bin_header = 20 + json_length
    if bin_header + 8 > len(blob):
        return {'note': 'No binary GLB chunk'}
    bin_length, bin_kind = struct.unpack_from('<II', blob, bin_header)
    if bin_kind != 0x004e4942:
        return {'note': 'Unexpected GLB binary chunk type'}
    bin_start = bin_header + 8
    if bin_start + bin_length > len(blob):
        raise ValueError('Corrupted binary geometry length')
    reports = []
    for mesh_index, mesh in enumerate(doc.get('meshes', [])):
        for prim_index, prim in enumerate(mesh.get('primitives', [])):
            attributes = prim.get('attributes', {})
            pos_idx = attributes.get('POSITION')
            if pos_idx is None:
                continue
            pos = accessors[pos_idx]
            count = pos['count']
            if pos.get('componentType') != 5126 or pos.get('type') != 'VEC3':
                reports.append({'mesh': mesh_index, 'primitive': prim_index,
                                'note': 'Position buffer is not FLOAT VEC3'})
                continue
            pv = views[pos['bufferView']]
            poff = bin_start + pv.get('byteOffset', 0) + pos.get('byteOffset', 0)
            pstride = pv.get('byteStride', 12)
            parent = list(range(count))
            def find(v):
                while parent[v] != v:
                    parent[v] = parent[parent[v]]
                    v = parent[v]
                return v
            def unite(a, b):
                a, b = find(a), find(b)
                if a != b:
                    parent[b] = a
            index_acc = accessors[prim['indices']] if 'indices' in prim else None
            if index_acc:
                fmt = {5121: 'B', 5123: 'H', 5125: 'I'}.get(index_acc['componentType'])
                if not fmt:
                    reports.append({'mesh': mesh_index, 'primitive': prim_index,
                                    'note': 'Unsupported triangle-index component type'})
                    continue
                iv = views[index_acc['bufferView']]
                ioff = bin_start + iv.get('byteOffset', 0) + index_acc.get('byteOffset', 0)
                isize = struct.calcsize('<' + fmt)
                istride = iv.get('byteStride', isize)
                indices = [struct.unpack_from('<' + fmt, blob, ioff + j * istride)[0]
                           for j in range(index_acc['count'])]
            else:
                indices = list(range(count))
            if prim.get('mode', 4) != 4:
                reports.append({'mesh': mesh_index, 'primitive': prim_index,
                                'note': 'Primitive is not TRIANGLES'})
                continue
            if len(indices) % 3:
                raise ValueError('Malformed triangle index buffer')
            for j in range(0, len(indices), 3):
                a, b, d = indices[j:j + 3]
                if max(a, b, d) >= count:
                    raise ValueError('Triangle index out of position accessor bounds')
                unite(a, b)
                unite(b, d)
            components = {}
            for i in range(count):
                root = find(i)
                if root not in components:
                    components[root] = {'vertices': 0,
                        'min': [float('inf')] * 3, 'max': [float('-inf')] * 3}
                entry = components[root]
                x, y, z = struct.unpack_from('<3f', blob, poff + i * pstride)
                entry['vertices'] += 1
                for dim, val in enumerate((x, y, z)):
                    entry['min'][dim] = min(entry['min'][dim], val)
                    entry['max'][dim] = max(entry['max'][dim], val)
            sorted_components = sorted(components.values(),
                                       key=lambda component: component['vertices'],
                                       reverse=True)
            reports.append({
                'mesh': mesh_index, 'primitive': prim_index,
                'position_vertices': count, 'triangles': len(indices) // 3,
                'connected_surfaces': len(sorted_components),
                'largest_surfaces': [
                    {'vertices': v['vertices'],
                     'min_xyz': [round(n, 4) for n in v['min']],
                     'max_xyz': [round(n, 4) for n in v['max']]}
                    for v in sorted_components[:12]
                ],
                'note': 'Triangle connectivity does not prove which surface is a head.'
            })
    return reports

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
        'mesh_surface_analysis': find_connected_surfaces(doc, blob, json_length),
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
    print('CONNECTED SURFACES:', json.dumps(r['mesh_surface_analysis']))
    print('FIVE ANIMATED HEAD JOINTS:', r['independent_head_rig_verified'])
    if not r['independent_head_rig_verified']:
        print('ACTION NEEDED: five independently controlled heads are NOT verified; '
              'do not distort the approved chest or replace the model with a primitive rig.')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
