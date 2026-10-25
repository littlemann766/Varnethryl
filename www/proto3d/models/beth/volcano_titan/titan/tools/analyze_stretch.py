import json,struct,numpy as np
d=open('/workspace/godot-art/volcano/titan/ashentitan_volcano_glow.glb','rb').read()
l=struct.unpack('<I',d[12:16])[0];j=json.loads(d[20:20+l]);b=d[20+l+8:]
CT={5126:np.float32,5123:np.uint16,5125:np.uint32,5121:np.uint8}
NC={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}
def acc(i):
    a=j['accessors'][i];v=j['bufferViews'][a['bufferView']]
    n=NC[a['type']];dt=CT[a['componentType']]
    o=v.get('byteOffset',0)+a.get('byteOffset',0)
    r=np.frombuffer(b,dt,a['count']*n,o).reshape(a['count'],n)
    if a.get('normalized'):r=r/ np.iinfo(dt).max
    return r.astype(np.float64) if dt==np.float32 or a.get('normalized') else r
p=j['meshes'][0]['primitives'][0];A=p['attributes']
P=acc(A['POSITION']);UV=acc(A['TEXCOORD_0']);J=acc(A['JOINTS_0']).astype(int);W=acc(A['WEIGHTS_0']);F=acc(p['indices']).reshape(-1,3).astype(int)
sk=j['skins'][0];joints=sk['joints'];IBM=acc(sk['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1)
N=j['nodes'];par={c:i for i,n in enumerate(N) for c in n.get('children',[])}
def q2m(q):
    x,y,z,w=q;return np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
def local(i,ov):
    n=N[i];t,r,s=ov.get(i,{}).get('t',n.get('translation',[0,0,0])),ov.get(i,{}).get('r',n.get('rotation',[0,0,0,1])),ov.get(i,{}).get('s',n.get('scale',[1,1,1]))
    M=np.eye(4);M[:3,:3]=q2m(r)*np.array(s);M[:3,3]=t;return M
def glob(ov):
    G={}
    def g(i):
        if i in G:return G[i]
        M=local(i,ov);G[i]=(g(par[i])@M) if i in par else M;return G[i]
    return [g(i) for i in joints]
def skin(ov):
    G=glob(ov);S=np.array([G[k]@IBM[k] for k in range(len(joints))])
    Ph=np.c_[P,np.ones(len(P))];out=np.zeros((len(P),3))
    for c in range(4):out+=W[:,c:c+1]*np.einsum('nij,nj->ni',S[J[:,c]],Ph)[:,:3]
    return out
def samp(an,t):
    ov={}
    for ch in an['channels']:
        s=an['samplers'][ch['sampler']];T=acc(s['input'])[:,0];V=acc(s['output'])
        k=np.searchsorted(T,t);k=min(max(k,1),len(T)-1);a=np.clip((t-T[k-1])/max(T[k]-T[k-1],1e-6),0,1)
        v=V[k-1]*(1-a)+V[k]*a;path=ch['target']['path'][0]
        if path=='r':v=v/np.linalg.norm(v)
        ov.setdefault(ch['target']['node'],{})[path]=v
    return ov
R=skin({});E=np.r_[F[:,[0,1]],F[:,[1,2]],F[:,[2,0]]]
def el(X):return np.linalg.norm(X[E[:,0]]-X[E[:,1]],axis=1)
def ar(X):return np.linalg.norm(np.cross(X[F[:,1]]-X[F[:,0]],X[F[:,2]]-X[F[:,0]]),axis=1)
e0=el(R)+1e-9;a0=ar(R)+1e-12
fs=np.zeros(len(F));poses=[]
for an in j['animations']:
    T=acc(an['samplers'][0]['input'])[:,0];best=(0,0)
    for t in np.linspace(T[0],T[-1],10):
        X=skin(samp(an,t));e=np.abs(np.log(el(X)/e0)).reshape(3,-1).max(0);aa=np.abs(np.log(ar(X)/a0))
        s=np.maximum(e,aa*0.5);fs=np.maximum(fs,s)
        m=np.percentile(s,99)
        if m>best[0]:best=(m,t)
    poses.append((an['name'],best[1],best[0]));print(an['name'],best)
# vertex stretch
vs=np.zeros(len(P));np.maximum.at(vs,F.ravel(),np.repeat(fs,3))
# joint region: weight split
ws=np.sort(W,1)[:,::-1];split=np.clip(ws[:,1]/np.maximum(ws[:,0],1e-6),0,1)
# seams: positions with multiple UVs
key=np.round(P*1e4).astype(np.int64);_,inv,cnt=np.unique(key,axis=0,return_inverse=True,return_counts=True)
seam=(cnt[inv.ravel()]>1).astype(float)
jn=[N[i]['name'] for i in joints]
np.savez('an.npz',P=P,UV=UV,F=F,vs=vs,split=split,seam=seam,J=J,W=W,R=R)
json.dump({'poses':poses,'joints':jn},open('an.json','w'))
print('stretch pct',np.percentile(vs,[50,90,99]),'seam',seam.mean(),'split>0.3',(split>0.3).mean())
# top bones by stretch
dom=J[np.arange(len(J)),W.argmax(1)];import collections
sc=collections.defaultdict(list)
for v,bn in zip(vs,dom):sc[jn[bn]].append(v)
print(sorted([(round(float(np.mean(v)),3),k) for k,v in sc.items()])[-15:])
