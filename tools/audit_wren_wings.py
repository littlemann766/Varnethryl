#!/usr/bin/env python3
"""Diagnose actual Wren GLB wing joints and animation channels, no mesh changes."""
import json,struct
from pathlib import Path
p=Path('www/proto3d/models-new/wren_cl_arms.glb')
raw=p.read_bytes();assert raw[:4]==b'glTF'
length,kind=struct.unpack_from('<II',raw,12); d=json.loads(raw[20:20+length])
nodes=d.get('nodes',[]); acc=d.get('accessors',[]); skins=d.get('skins',[])
names={i:n.get('name','') for i,n in enumerate(nodes)}
wing={i:name for i,name in names.items() if 'wing' in name.lower() or 'feather' in name.lower()}
print('WREN',len(raw),'bytes; meshes',len(d.get('meshes',[])),'skins',len(skins),'wing-related nodes',len(wing))
print('WING NODES',sorted(wing.items()))
joint_ids={x for skin in skins for x in skin.get('joints',[])}
print('WING JOINTS', [(i,n,i in joint_ids) for i,n in wing.items()])
print('WING HIERARCHY', [(i,next((k for k,node in enumerate(nodes) if i in node.get('children',[])),None)) for i in wing])
for clip in d.get('animations',[]):
    channels=[(names.get(ch.get('target',{}).get('node'),''),ch.get('target',{}).get('path')) for ch in clip.get('channels',[])]
    w=[(n,pp) for n,pp in channels if 'wing' in n.lower() or 'feather' in n.lower()]
    print('CLIP',clip.get('name'),'duration',clip.get('samplers',[]) and 'present','wing tracks',len(w),w[:35],'total tracks',len(channels))
assert wing,'Wren has no wings (wrong GLB)'
print('PASS: inspected real Wren wing rig and authored clip channels')
