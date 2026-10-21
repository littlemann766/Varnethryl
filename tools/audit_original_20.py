#!/usr/bin/env python3
"""Audit the original 20 hero GLB files without overwriting art or reordering saves.

Produces machine-readable and human-readable reports for a character-by-character
visual/rig cleanup. Structural readiness is NOT visual/portrait approval.
"""
import json
import re
import struct
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MAIN=(ROOT/'www/proto3d/main.js').read_text()
IDS=re.findall(r"'([^']+)'", re.search(r"const GLB_IDS = \[([^;]+)\];",MAIN).group(1))
NAMES=re.findall(r"'([^']+)'", re.search(r"const GLB_NAMES = \[([^;]+)\];",MAIN).group(1))
if len(IDS)!=20 or len(NAMES)!=20:
    raise SystemExit(f'FAIL: original hero array was reordered/modified: IDs={len(IDS)}, names={len(NAMES)}')
rows=[]
for i,(key,name) in enumerate(zip(IDS,NAMES),start=1):
    path=ROOT/'www/proto3d/models'/f'{key}.glb'
    record=dict(slot=i,id=key,character=name,source=str(path.relative_to(ROOT)),
        file_exists=path.exists(),bytes=path.stat().st_size if path.exists() else 0,
        skin_joints=0,skinned_primitives=0,clips=[],animated_joints=0,
        status='missing',visually_approved=False)
    if not path.exists():
        rows.append(record);continue
    try:
        raw=path.read_bytes()
        if len(raw)<20 or raw[:4]!=b'glTF':
            raise ValueError('invalid GLB header')
        total=struct.unpack_from('<I',raw,8)[0]
        if total!=len(raw):
            raise ValueError(f'invalid byte count: {total} != {len(raw)}')
        length,chunk=struct.unpack_from('<II',raw,12)
        if chunk!=0x4e4f534a:
            raise ValueError('missing JSON')
        g=json.loads(raw[20:20+length])
        record['skin_joints']=max([len(s.get('joints',[])) for s in g.get('skins',[])] or [0])
        record['skinned_primitives']=sum(int('JOINTS_0' in p.get('attributes',{}) and 'WEIGHTS_0' in p.get('attributes',{}))
          for m in g.get('meshes',[]) for p in m.get('primitives',[]))
        joint_ids={j for s in g.get('skins',[]) for j in s.get('joints',[])}
        animated=set()
        for a in g.get('animations',[]):
            target={c.get('target',{}).get('node') for c in a.get('channels',[])}
            animated.update(joint_ids & target)
            record['clips'].append(dict(name=a.get('name','unnamed'),tracks=len(a.get('channels',[])),
                joint_tracks=len(joint_ids & target)))
        record['animated_joints']=len(animated)
        record['status']='skinned_animated' if record['skinned_primitives'] and record['animated_joints'] else (
            'skinned_static' if record['skinned_primitives'] else ('node_animated' if record['clips'] else 'static'))
    except Exception as e:
        record['status']='invalid'; record['error']=str(e)
    rows.append(record)
OUT=ROOT/'model-original-20-audit.json'
OUT.write_text(json.dumps({'source':'Varnethryl original playable 20','note':'Structural status only; no visual/portrait approval',
    'original_id_order':IDS,'models':rows},indent=2)+'\n')
md=['# Original 20 character GLB audit','', 'Every character requires visual review against its approved 2D portrait, weapon and class. The columns below only test file/rig data.',
    '', '| Slot | Character | ID | Bones | Animated joints | Clips | Rig status | Visual approval |',
    '| ---: | --- | --- | ---: | ---: | ---: | --- | --- |']
for r in rows:
    md.append(f"| {r['slot']} | {r['character']} | `{r['id']}` | {r['skin_joints']} | {r['animated_joints']} | {len(r['clips'])} | {r['status']} | **Pending** |")
(ROOT/'model-original-20-audit.md').write_text('\n'.join(md)+'\n')
for r in rows:
    print(f"{r['slot']:02d}. {r['character']:<24} {r['id']:<12} bones={r['skin_joints']:3} animated={r['animated_joints']:3} clips={len(r['clips']):2} status={r['status']}")
if any(r['status'] in ('invalid','missing') for r in rows):
    raise SystemExit('FAIL: missing/invalid original character GLBs')
print('PASS: all 20 original GLBs present; individual rig report generated (visual identities remain unapproved).')
