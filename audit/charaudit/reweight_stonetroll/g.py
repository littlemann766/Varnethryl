import json,struct,numpy as np
CT={5120:np.int8,5121:np.uint8,5122:np.int16,5123:np.uint16,5125:np.uint32,5126:np.float32}
NC={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}
class G:
    def __init__(s,f):
        d=open(f,'rb').read(); n=struct.unpack('<I',d[12:16])[0]; s.j=json.loads(d[20:20+n]); o=20+n
        bl=struct.unpack('<I',d[o:o+4])[0]; s.bin=bytearray(d[o+8:o+8+bl])
    def view(s,i):
        a=s.j['accessors'][i]; bv=s.j['bufferViews'][a['bufferView']]
        off=bv.get('byteOffset',0)+a.get('byteOffset',0); nc=NC[a['type']]; dt=CT[a['componentType']]
        assert bv.get('byteStride',0) in (0,nc*np.dtype(dt).itemsize)
        return np.frombuffer(s.bin,dt,a['count']*nc,off).reshape(a['count'],nc), off
    def write(s,i,arr):
        v,off=s.view(i); b=arr.astype(v.dtype).tobytes(); s.bin[off:off+len(b)]=b
    def save(s,f):
        js=json.dumps(s.j,separators=(',',':')).encode(); js+=b' '*((4-len(js)%4)%4)
        b=bytes(s.bin); b+=b'\0'*((4-len(b)%4)%4)
        out=struct.pack('<III',0x46546C67,2,12+8+len(js)+8+len(b))+struct.pack('<I',len(js))+b'JSON'+js+struct.pack('<I',len(b))+b'BIN\0'+b
        open(f,'wb').write(out)
