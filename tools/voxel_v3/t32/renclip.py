# rename glb animation 'jump_loop' -> 'jump_hang' in the JSON chunk (Godot strips a _loop suffix, so jump_loop collided with jump)
import json,struct,sys
for p in sys.argv[1:]:
    b=bytearray(open(p,'rb').read()); l=struct.unpack('<I',b[12:16])[0]; j=json.loads(b[20:20+l]); ch=0
    for a in j.get('animations',[]):
        if a['name']=='jump_loop': a['name']='jump_hang'; ch=1
    if not ch: continue
    s=json.dumps(j,separators=(',',':')).encode(); s+=b' '*((4-len(s)%4)%4)
    nb=b[:12]+struct.pack('<I',len(s))+b[16:20]+s+b[20+l:]; nb[8:12]=struct.pack('<I',len(nb))
    open(p,'wb').write(nb); print('renamed',p)
