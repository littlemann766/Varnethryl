import json,struct,sys,numpy as np
sys.path.insert(0,'/tmp'); from skinh import height
def rescale(p,f):
    b=open(p,'rb').read(); n=struct.unpack('<I',b[12:16])[0]; j=json.loads(b[20:20+n]); rest=b[20+n:]
    animated={(c['target']['node'],c['target']['path']) for a in j.get('animations',[]) for c in a['channels']}
    for r in j['scenes'][j.get('scene',0)]['nodes']:
        nd=j['nodes'][r]; assert 'matrix' not in nd and (r,'scale') not in animated and (r,'translation') not in animated, (p,r)
        nd['scale']=[v*f for v in nd.get('scale',[1,1,1])]
        if 'translation' in nd: nd['translation']=[v*f for v in nd['translation']]
    bj=json.dumps(j,separators=(',',':')).encode(); bj+=b' '*((-len(bj))%4)
    out=struct.pack('<III',0x46546C67,2,12+8+len(bj)+len(rest))+struct.pack('<II',len(bj),0x4E4F534A)+bj+rest
    open(p,'wb').write(out)
SPEC={'stonetroll':5.715,'frosttroll_a':5.715,'frosttroll_b':5.715,'ashentitan':11.43,'ashentitan_volcano':20.955,'titan_giant_20x':38.151,'titan_giant_40x':76.302,'titan_giant_60x':114.453}
idx=json.load(open('index.json')); rep=[]
for c in idx['characters']:
    if c['name'] not in SPEC: continue
    t=SPEC[c['name']]; row=[c['name'],t]
    for l in ('high','lod1','lod2'):
        f=c['lods'][l]['file']; h0=height(f)[0]; k=t/h0
        if abs(k-1)>0.002:
            import shutil; shutil.copy2(f,'/tmp/charbak/'+f); rescale(f,k)
        h1=height(f)[0]; row.append((l,h0,round(k,4),h1))
    c['height_m']=t; c.setdefault('notes',[]).append(f"2026-10-25: armature-root scale re-baked per LOD so skinned rest height = {t} m (measured before: "+", ".join(f'{x[0]} {x[1]}' for x in row[2:])+")")
    rep.append(row); print(row,flush=True)
json.dump(idx,open('index.json','w'),indent=1)
