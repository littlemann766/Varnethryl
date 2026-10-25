import sys,json,struct,numpy as np
sys.path.insert(0,'/tmp/tg');from lib import load,acc
src,dst=sys.argv[1:3];j,b=load(src);b=bytearray(b)
sk=j['skins'][0];jn=[j['nodes'][n]['name'] for n in sk['joints']]
mp={i:jn.index('hand_'+n[-1]) for i,n in enumerate(jn) if n[:-2].rstrip('123') in ('index','middle','ring','pinky','thumb','fingers')}
tot=0
for m in j['meshes']:
    for p in m['primitives']:
        a=j['accessors'][p['attributes']['JOINTS_0']];v=j['bufferViews'][a['bufferView']];o=v.get('byteOffset',0)+a.get('byteOffset',0)
        dt={5121:np.uint8,5123:np.uint16}[a['componentType']];J=np.frombuffer(bytes(b[o:o+a['count']*4*np.dtype(dt).itemsize]),dt).reshape(-1,4).copy()
        W=acc(j,bytes(b),p['attributes']['WEIGHTS_0'])
        for k,t in mp.items():
            hit=(J==k)&(W>0);tot+=int(hit.any(1).sum());J[J==k]=t
        b[o:o+J.nbytes]=J.tobytes()
d=open(src,'rb').read();l=struct.unpack('<I',d[12:16])[0]
open(dst,'wb').write(d[:20+l+8]+bytes(b)+d[20+l+8+len(b):])
print('REMAP verts',tot)
