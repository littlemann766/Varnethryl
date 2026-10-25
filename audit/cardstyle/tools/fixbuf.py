import sys,json,struct,glob
for f in sys.argv[1:]:
    b=open(f,'rb').read(); l=struct.unpack('<I',b[12:16])[0]; j=json.loads(b[20:20+l]); rest=b[20+l:]
    if 'buffers' in j: continue
    bl=struct.unpack('<I',rest[:4])[0]; j['buffers']=[{'byteLength':bl}]
    bj=json.dumps(j).encode(); bj+=b' '*((-len(bj))%4)
    out=struct.pack('<III',0x46546C67,2,12+8+len(bj)+len(rest))+struct.pack('<II',len(bj),0x4E4F534A)+bj+rest
    open(f,'wb').write(out)
