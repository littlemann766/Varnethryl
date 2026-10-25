# wsmooth.py in out iters : Laplacian-smooth hand/finger weights over mesh topology (welded by position), top-4
import sys,json,struct,numpy as np
sys.path.insert(0,'/tmp/tg');from lib import load,acc
src,dst=sys.argv[1:3];IT=int(sys.argv[3]) if len(sys.argv)>3 else 12
j,b=load(src);b=bytearray(b);p=j['meshes'][0]['primitives'][0];A=p['attributes']
P=acc(j,bytes(b),A['POSITION']).astype(float);F=acc(j,bytes(b),p['indices']).reshape(-1,3).astype(int)
ja=j['accessors'][A['JOINTS_0']];jv=j['bufferViews'][ja['bufferView']];jo=jv.get('byteOffset',0)+ja.get('byteOffset',0);jdt={5121:np.uint8,5123:np.uint16}[ja['componentType']]
J=np.frombuffer(bytes(b[jo:jo+ja['count']*4*np.dtype(jdt).itemsize]),jdt).reshape(-1,4).astype(int)
wa=j['accessors'][A['WEIGHTS_0']];wv=j['bufferViews'][wa['bufferView']];wo=wv.get('byteOffset',0)+wa.get('byteOffset',0)
assert wa['componentType']==5126
W=np.frombuffer(bytes(b[wo:wo+wa['count']*16]),np.float32).reshape(-1,4).astype(float)
sk=j['skins'][0];jn=[j['nodes'][n]['name'] for n in sk['joints']];nJ=len(jn)
fing=[i for i,n in enumerate(jn) if n[:-2].rstrip('123') in ('index','middle','ring','pinky','thumb')]
sel=np.isin(J,fing).any(1)&(W>0).any(1)
# weld
key=np.unique(np.round(P*2000),axis=0,return_inverse=True)[1].ravel();nk=key.max()+1
D=np.zeros((nk,nJ));np.add.at(D,(np.repeat(key,4),J.ravel()),W.ravel());cnt=np.bincount(key,minlength=nk)[:,None];D/=cnt
ks=np.zeros(nk,bool);ks[key[sel]]=True
# grow selection 2 rings so the blend reaches into the palm/hand verts
E=np.unique(np.sort(np.r_[F[:,[0,1]],F[:,[1,2]],F[:,[2,0]]],1),axis=0);E=key[E];E=E[E[:,0]!=E[:,1]]
for _ in range(2):
    g=ks.copy();g[E[ks[E[:,0]],1]]=True;g[E[ks[E[:,1]],0]]=True;ks=g
deg=np.bincount(E.ravel(),minlength=nk).astype(float)[:,None]
for _ in range(IT):
    S=np.zeros_like(D);np.add.at(S,E[:,0],D[E[:,1]]);np.add.at(S,E[:,1],D[E[:,0]])
    Dn=0.5*D+0.5*S/np.maximum(deg,1);D[ks]=Dn[ks]
Vd=D[key];o=np.argsort(-Vd,1)[:,:4];w4=np.take_along_axis(Vd,o,1);w4/=w4.sum(1,keepdims=True)
upd=ks[key]
J[upd]=o[upd];W[upd]=w4[upd]
b[jo:jo+J.size*np.dtype(jdt).itemsize]=J.astype(jdt).tobytes();b[wo:wo+W.size*4]=W.astype(np.float32).tobytes()
d=open(src,'rb').read();l=struct.unpack('<I',d[12:16])[0]
open(dst,'wb').write(d[:20+l+8]+bytes(b)+d[20+l+8+len(b):])
print('WSMOOTH verts',int(upd.sum()))
