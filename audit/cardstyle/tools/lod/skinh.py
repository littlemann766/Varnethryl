import json,struct,sys,numpy as np
def load(p):
    b=open(p,'rb').read(); n=struct.unpack('<I',b[12:16])[0]; j=json.loads(b[20:20+n]); return j,b[20+n+8:]
CT={5126:np.float32,5123:np.uint16,5121:np.uint8,5125:np.uint32}; NC={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}
def acc(j,bin_,i):
    a=j['accessors'][i]; v=j['bufferViews'][a['bufferView']]; dt=CT[a['componentType']]; nc=NC[a['type']]
    st=v.get('byteStride',0); off=v.get('byteOffset',0)+a.get('byteOffset',0)
    if st and st!=nc*np.dtype(dt).itemsize:
        raw=np.frombuffer(bin_,np.uint8,a['count']*st,off).reshape(a['count'],st)[:,:nc*np.dtype(dt).itemsize].copy(); return raw.view(dt).reshape(a['count'],nc)
    x=np.frombuffer(bin_,dt,a['count']*nc,off).reshape(a['count'],nc).astype(np.float64)
    if a.get('normalized'): x=x/np.iinfo(dt).max
    return x
def M(n):
    if 'matrix' in n: return np.array(n['matrix']).reshape(4,4).T
    t=n.get('translation',[0,0,0]); r=n.get('rotation',[0,0,0,1]); s=n.get('scale',[1,1,1])
    x,y,z,w=r; R=np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
    m=np.eye(4); m[:3,:3]=R*np.array(s); m[:3,3]=t; return m
def height(p):
    j,bin_=load(p); N=j['nodes']; G={}
    def walk(i,P):
        G[i]=P@M(N[i]); [walk(c,G[i]) for c in N[i].get('children',[])]
    for r in j['scenes'][j.get('scene',0)]['nodes']: walk(r,np.eye(4))
    ys=[]
    for i,n in enumerate(N):
        if 'mesh' not in n: continue
        for pr in j['meshes'][n['mesh']]['primitives']:
            P=acc(j,bin_,pr['attributes']['POSITION']); Ph=np.c_[P,np.ones(len(P))]
            if 'skin' in n:
                sk=j['skins'][n['skin']]; IB=acc(j,bin_,sk['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1)
                J=np.stack([G[x]@IB[k] for k,x in enumerate(sk['joints'])])
                Ji=acc(j,bin_,pr['attributes']['JOINTS_0']).astype(int); W=acc(j,bin_,pr['attributes']['WEIGHTS_0']); W=W/W.sum(1,keepdims=True)
                out=np.zeros((len(P),4))
                for k in range(4): out+=W[:,k:k+1]*np.einsum('nij,nj->ni',J[Ji[:,k]],Ph)
            else: out=Ph@G[i].T
            ys.append(out[:,1])
    y=np.concatenate(ys); return round(y.max()-y.min(),3),round(y.min(),3)
if __name__=='__main__':
    import os
    d=json.load(open('/workspace/godot-art/characters/index.json'))
    for c in d['characters']:
        v=[height('/workspace/godot-art/characters/'+c['lods'][l]['file']) for l in ('high','lod1','lod2')]
        bad=any(abs(x[0]-c['height_m'])>0.04*c['height_m'] for x in v)
        print(('BAD ' if bad else '    ')+c['name'],c['height_m'],v,flush=True)
