import json,struct,numpy as np
CT={5126:np.float32,5123:np.uint16,5121:np.uint8,5125:np.uint32,5122:np.int16,5120:np.int8}
NC={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}
def load(f):
    b=open(f,'rb').read(); n=struct.unpack('<I',b[12:16])[0]; j=json.loads(b[20:20+n]); bin_=b[20+n+8:]
    def acc(i):
        a=j['accessors'][i]; bv=j['bufferViews'][a['bufferView']]; dt=CT[a['componentType']]; k=NC[a['type']]
        off=bv.get('byteOffset',0)+a.get('byteOffset',0); st=bv.get('byteStride',0); isz=np.dtype(dt).itemsize*k
        if st and st!=isz:
            raw=np.frombuffer(bin_,np.uint8,count=st*a['count'],offset=off).reshape(a['count'],st)[:,:isz].copy()
            arr=raw.view(dt).reshape(a['count'],k)
        else: arr=np.frombuffer(bin_,dt,count=a['count']*k,offset=off).reshape(a['count'],k)
        arr=arr.astype(np.float64)
        if a.get('normalized'):
            arr/= {5121:255,5123:65535,5120:127,5122:32767}[a['componentType']]
        return arr
    return j,acc
def local(nd):
    if 'matrix' in nd: return np.array(nd['matrix']).reshape(4,4).T
    t=nd.get('translation',[0,0,0]); r=nd.get('rotation',[0,0,0,1]); s=nd.get('scale',[1,1,1])
    x,y,z,w=r; R=np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
    M=np.eye(4); M[:3,:3]=R*np.array(s); M[:3,3]=t; return M
def globals_(j):
    par={}
    for i,nd in enumerate(j['nodes']):
        for c in nd.get('children',[]): par[c]=i
    G={}
    def g(i):
        if i in G: return G[i]
        M=local(j['nodes'][i]); 
        if i in par: M=g(par[i])@M
        G[i]=M; return M
    for i in range(len(j['nodes'])): g(i)
    return G
