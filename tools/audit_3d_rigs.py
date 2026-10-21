#!/usr/bin/env python3
"""Inspect original Varnethryl GLB rigs without modifying the model binaries.

Reports structure and animation-target evidence, not artistic/visual approval.
Works with the standard library in GitHub Actions. An unanimated model is a
warning; corrupted glTF structure is a failure.
"""
import json, struct, re, sys, argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
MODELS=(
 'www/proto3d/models-new/owner.glb',
 'www/proto3d/models-new/owner_pika1.glb',
 'www/proto3d/models-new/vaelthryx_straight_rig.glb',
 'www/proto3d/models-new/vaelthryx_new6.glb',
 'www/proto3d/models-new/frosttroll_a.glb',
 'www/proto3d/models-new/frosttroll_b.glb',
 'www/proto3d/models-new/ashentitan_cl_arms.glb',
 'www/proto3d/models-new/ssylthar_new.glb',
 'www/proto3d/models-beth/ssylthar.glb',
 'varnethryl-owner-test/owner-animated.glb',
)
def inspect(path):
 b=path.read_bytes()
 if len(b)<20: raise ValueError('GLB header too short')
 magic,ver,size=struct.unpack_from('<4sII',b)
 if magic!=b'glTF' or ver!=2 or size!=len(b):raise ValueError('GLB magic, version, or byte length mismatch')
 off=12;chunks=[]
 while off<len(b):
  if off+8>len(b):raise ValueError('Truncated chunk header')
  length,kind=struct.unpack_from('<II',b,off);off+=8
  if length%4 or off+length>len(b):raise ValueError('Corrupt chunk size/alignment')
  chunks.append((kind,b[off:off+length]));off+=length
 if not chunks or chunks[0][0]!=0x4e4f534a:raise ValueError('Missing first JSON chunk')
 d=json.loads(chunks[0][1].decode('utf8').rstrip(' \x00'))
 if d.get('asset',{}).get('version')!='2.0':raise ValueError('Invalid glTF asset version')
 nodes=d.get('nodes',[]);skins=d.get('skins',[]);meshes=d.get('meshes',[])
 animations=d.get('animations',[]);accessors=d.get('accessors',[])
 views=d.get('bufferViews',[]);buffers=d.get('buffers',[])
 errors=[];warnings=[]
 def valid(i,items,field):
  if not isinstance(i,int) or i<0 or i>=len(items):errors.append(f'{field}: invalid index {i!r}');return False
  return True
 joints=set()
 for i,n in enumerate(nodes):
  if 'skin' in n:valid(n['skin'],skins,f'node[{i}].skin')
  if 'mesh' in n:valid(n['mesh'],meshes,f'node[{i}].mesh')
  for x in n.get('children',[]):valid(x,nodes,f'node[{i}].children')
 for i,skin in enumerate(skins):
  if not skin.get('joints'):errors.append(f'skin[{i}] contains no joints')
  for j in skin.get('joints',[]):
   if valid(j,nodes,f'skin[{i}].joint'):joints.add(j)
  if 'inverseBindMatrices' in skin:valid(skin['inverseBindMatrices'],accessors,'inverseBindMatrices')
 weighted=0
 for i,mesh in enumerate(meshes):
  for prim in mesh.get('primitives',[]):
   attrs=prim.get('attributes',{})
   if 'POSITION' not in attrs:errors.append(f'mesh[{i}] primitive missing POSITION')
   for field,index in attrs.items():valid(index,accessors,f'mesh[{i}].{field}')
   if 'indices' in prim:valid(prim['indices'],accessors,f'mesh[{i}].indices')
   if 'JOINTS_0' in attrs or 'WEIGHTS_0' in attrs:
    if 'JOINTS_0' not in attrs or 'WEIGHTS_0' not in attrs:errors.append(f'mesh[{i}] incomplete skin attributes')
    else:weighted+=1
 for i,v in enumerate(views):
  valid(v.get('buffer',0),buffers,f'bufferView[{i}].buffer')
  if v.get('byteLength',0)<0:errors.append('Negative bufferView length')
 binary=[data for typ,data in chunks if typ==0x004e4942]
 if buffers and binary and buffers[0].get('byteLength',0)>len(binary[0]):errors.append('Embedded binary exceeds chunk bounds')
 animated=set();targeted=set();names=[];channels=0
 for i,a in enumerate(animations):
  names.append(a.get('name') or f'Animation {i+1}')
  ss=a.get('samplers',[])
  for k,samp in enumerate(ss):
   valid(samp.get('input'),accessors,f'animation[{i}].sampler[{k}].input')
   valid(samp.get('output'),accessors,f'animation[{i}].sampler[{k}].output')
  for k,ch in enumerate(a.get('channels',[])):
   channels+=1;valid(ch.get('sampler'),ss,f'animation[{i}].channel[{k}].sampler')
   target=ch.get('target',{});node=target.get('node')
   if node is not None and valid(node,nodes,f'animation[{i}].channel[{k}].node'):
    targeted.add(node)
    if node in joints and target.get('path') in ('rotation','translation','scale'):animated.add(node)
 bone_names=[nodes[n].get('name',str(n)) for n in joints]
 moving=[nodes[n].get('name',str(n)) for n in animated]
 serpent=lambda x:bool(re.search('spine|tail|body|neck',x,re.I))
 if not skins:warnings.append('No skeleton skins: cannot bend in an articulated gait')
 if not animations:warnings.append('No embedded animation clips')
 if skins and weighted==0:warnings.append('Skin exists without paired JOINTS_0 and WEIGHTS_0 geometry')
 if skins and not animated:warnings.append('No animation channels targeting skin joints')
 if 'vaelthryx' in path.name and any(map(serpent,bone_names)) and not any(map(serpent,moving)):
  warnings.append('Balthrix spine/tail bones lack authored motion: inspect procedural fallback')
 if 'ssylthar' in path.name:warnings.append('Sslythar stays HIDDEN until privately animated and tested')
 return dict(path=str(path.relative_to(ROOT)),valid=not errors,size_bytes=len(b),skins=len(skins),
             skin_joints=len(joints),weighted_primitives=weighted,animation_clips=len(animations),
             animation_channels=channels,animated_joint_count=len(animated),clip_names=names[:40],
             serpent_joint_count=sum(map(serpent,bone_names)),animated_serpent_joint_count=sum(map(serpent,moving)),
             warnings=warnings,errors=errors)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--report',default='model-rig-audit.json')
 ap.add_argument('--model',action='append',help='Optional single GLB path');args=ap.parse_args()
 records=[]
 for name in (args.model or MODELS):
  path=ROOT/name
  try:
   if not path.is_file():raise ValueError('model file missing')
   records.append(inspect(path))
  except Exception as e:records.append(dict(path=name,valid=False,errors=[str(e)],warnings=[]))
 report={'schema':1,'limitations':'Structure & animation targets only; not visual bone weights, run smoothness, combat, or mobile FPS',
         'total':len(records),'failed':sum(not r['valid'] for r in records),'models':records}
 Path(args.report).write_text(json.dumps(report,indent=2)+'\n')
 for r in records:
  print(('PASS' if r['valid'] else 'FAIL')+' '+r['path']+' | clips='+str(r.get('animation_clips','?'))+' | animated joints='+str(r.get('animated_joint_count','?')))
  print('  CLIPS: '+', '.join(r.get('clip_names',[])))
  print('  SERPENT: '+str(r.get('animated_serpent_joint_count',0))+' animated spine/tail joints of '+str(r.get('serpent_joint_count',0)))
  for w in r.get('warnings',[]):print('  WARN '+w)
  for err in r.get('errors',[]):print('  ERROR '+err)
 print('Audited',report['total'],'models; structural failures:',report['failed'])
 return 1 if report['failed'] else 0
if __name__=='__main__':sys.exit(main())
