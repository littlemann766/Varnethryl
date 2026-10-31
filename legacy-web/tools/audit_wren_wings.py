#!/usr/bin/env python3
"""Verify real Wren wing skeleton and measure baked motion, no binary modifications."""
import json,struct,math
from pathlib import Path
p=Path('www/proto3d/models-new/wren_cl_arms.glb')
raw=p.read_bytes();assert raw[:4]==b'glTF'
length,kind=struct.unpack_from('<II',raw,12); d=json.loads(raw[20:20+length]); blob=20+length+8
nodes=d.get('nodes',[]);acc=d.get('accessors',[]);views=d.get('bufferViews',[])
names={i:n.get('name','') for i,n in enumerate(nodes)}
wing={i:name for i,name in names.items() if name in {
 'wing_L','wing2_L','wing3_L','wing4_L','wing_R','wing2_R','wing3_R','wing4_R'}}
assert len(wing)==8, f'Expected 8 Wren wing joints, found {len(wing)}: {wing}'
joint_ids={x for skin in d.get('skins',[]) for x in skin.get('joints',[])}
assert set(wing)<=joint_ids, 'Wren wing bones are not skinned mesh joints'
print('WREN',len(raw),'bytes; skins',len(d.get('skins',[])),'WING BONES',list(wing.values()))
def quats(accessor):
    a=acc[accessor]; assert a['type']=='VEC4' and a['componentType']==5126
    v=views[a['bufferView']]
    offset=blob+v.get('byteOffset',0)+a.get('byteOffset',0)
    stride=v.get('byteStride',16)
    return [struct.unpack_from('<4f',raw,offset+i*stride) for i in range(a['count'])]
for clip in d.get('animations',[]):
    wingtracks={}
    for ch in clip.get('channels',[]):
        target=ch.get('target',{});idx=target.get('node')
        if idx in wing and target.get('path')=='rotation':
            a=clip['samplers'][ch['sampler']]['output']
            qs=quats(a);q0=qs[0]
            angles=[]
            for q in qs:
                dot=sum(x*y for x,y in zip(q,q0))
                dot=min(1,max(-1,abs(dot)))
                angles.append(math.degrees(2*math.acos(dot)))
            wingtracks[wing[idx]]=round(max(angles),2)
    print('CLIP',clip.get('name'),'wing bone amplitudes (degrees from first key)',wingtracks)
    if clip.get('name') in ('idle','walk','run','attack'):
        assert set(wingtracks)==set(wing.values()), 'Wren must have all eight wing joint tracks'
assert len(d.get('animations',[]))>=7,'Wren must preserve all seven authored clips'
print('PASS: Wren eight connected wing joints have complete authored rotation tracks')
