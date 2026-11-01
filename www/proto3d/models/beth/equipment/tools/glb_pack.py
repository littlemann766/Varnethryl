# Repack voxel glbs: COLOR_0 float32 -> normalized uint8 (4x smaller), lossless for 8-bit art colours.
import json,struct,sys,numpy as np,glob,os
def pack(f):
    b=open(f,'rb').read(); n=struct.unpack('<I',b[12:16])[0]; j=json.loads(b[20:20+n]); bin_=b[20+n+8:]
    views=[]
    for ai,a in enumerate(j['accessors']):
        bv=j['bufferViews'][a['bufferView']]; off=bv.get('byteOffset',0)+a.get('byteOffset',0)
        k={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']]; dt={5126:np.float32,5123:np.uint16,5125:np.uint32,5121:np.uint8}[a['componentType']]
        arr=np.frombuffer(bin_,dt,count=a['count']*k,offset=off).copy()
        views.append([ai,arr,bv.get('target')])
    cols={m['attributes'].get('COLOR_0') for me in j['meshes'] for m in me['primitives']}
    out=b''; j['bufferViews']=[]
    for ai,arr,tg in views:
        a=j['accessors'][ai]
        if ai in cols and a['componentType']==5126:
            arr=np.clip(np.round(arr*255),0,255).astype(np.uint8); a['componentType']=5121; a['normalized']=True
        data=arr.tobytes(); pad=(-len(out))%4; out+=b'\0'*pad
        bv={'buffer':0,'byteOffset':len(out),'byteLength':len(data)}
        if tg: bv['target']=tg
        if a['type']=='VEC4' and a['componentType']==5121: bv['byteStride']=4
        j['bufferViews'].append(bv); a['bufferView']=len(j['bufferViews'])-1; a.pop('byteOffset',None); out+=data
    out+=b'\0'*((-len(out))%4); j['buffers']=[{'byteLength':len(out)}]
    js=json.dumps(j,separators=(',',':')).encode(); js+=b' '*((-len(js))%4)
    tot=12+8+len(js)+8+len(out)
    open(f,'wb').write(struct.pack('<III',0x46546C67,2,tot)+struct.pack('<II',len(js),0x4E4F534A)+js+struct.pack('<II',len(out),0x004E4942)+out)
if __name__=="__main__":
    fs=[x for p in sys.argv[1:] for x in glob.glob(p,recursive=True)]
    for f in fs: pack(f)
    print(len(fs))
