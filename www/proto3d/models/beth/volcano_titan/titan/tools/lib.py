import json,struct,numpy as np
CT={5126:np.float32,5123:np.uint16,5125:np.uint32,5121:np.uint8,5122:np.int16,5120:np.int8}
NC={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}
def load(f):
    d=open(f,'rb').read();l=struct.unpack('<I',d[12:16])[0];j=json.loads(d[20:20+l]);b=d[20+l+8:20+l+8+struct.unpack('<I',d[20+l:24+l])[0]]
    return j,b
def acc(j,b,i):
    a=j['accessors'][i];v=j['bufferViews'][a['bufferView']];n=NC[a['type']];dt=CT[a['componentType']]
    o=v.get('byteOffset',0)+a.get('byteOffset',0);st=v.get('byteStride')
    isz=np.dtype(dt).itemsize
    if st and st!=n*isz:
        raw=np.frombuffer(b,np.uint8,(a['count']-1)*st+n*isz,o)
        r=np.lib.stride_tricks.as_strided(raw,(a['count'],n*isz),(st,1)).copy().view(dt).reshape(a['count'],n)
    else:r=np.frombuffer(b,dt,a['count']*n,o).reshape(a['count'],n)
    if a.get('normalized'):r=np.maximum(r/np.iinfo(dt).max,-1.0)
    return r
def q2m(q):
    x,y,z,w=q;return np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
def bindglobal(j,b):
    sk=j['skins'][0];IBM=acc(j,b,sk['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1)
    return {j['nodes'][n]['name']:np.linalg.inv(IBM[k]) for k,n in enumerate(sk['joints'])},IBM
