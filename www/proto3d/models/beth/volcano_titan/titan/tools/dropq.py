import json,struct,sys
for f in sys.argv[1:]:
    d=open(f,'rb').read();l=struct.unpack('<I',d[12:16])[0];j=json.loads(d[20:20+l]);rest=d[20+l:]
    for k in('extensionsUsed','extensionsRequired'):
        if k in j:j[k]=[e for e in j[k] if e!='KHR_mesh_quantization']
    js=json.dumps(j,separators=(',',':')).encode();js+=b' '*((4-len(js)%4)%4)
    open(f,'wb').write(struct.pack('<III',0x46546C67,2,12+8+len(js)+len(rest))+struct.pack('<II',len(js),0x4E4F534A)+js+rest)
