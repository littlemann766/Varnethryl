import json,struct
def load(p):
    b=open(p,'rb').read(); jl=struct.unpack('<I',b[12:16])[0]; j=json.loads(b[20:20+jl]); o=20+jl
    bl=struct.unpack('<I',b[o:o+4])[0]; bin_=b[o+8:o+8+bl]; return j,bin_
def images(j,bin_):
    out={}
    for i,im in enumerate(j['images']):
        bv=j['bufferViews'][im['bufferView']]; out[im.get('name',str(i))]=bin_[bv.get('byteOffset',0):bv.get('byteOffset',0)+bv['byteLength']]
    return out
def save(p,j,bin_,repl):
    # repl: name->bytes ; rebuild bin with bufferViews in order
    views=[]
    imgview={j['images'][i]['bufferView']:repl[im.get('name')] for i,im in enumerate(j['images']) if im.get('name') in repl}
    nb=bytearray()
    for k,bv in enumerate(j['bufferViews']):
        d=imgview.get(k) or bin_[bv.get('byteOffset',0):bv.get('byteOffset',0)+bv['byteLength']]
        while len(nb)%4: nb+=b'\0'
        bv['byteOffset']=len(nb); bv['byteLength']=len(d); nb+=d
    while len(nb)%4: nb+=b'\0'
    j['buffers'][0]['byteLength']=len(nb)
    for i,im in enumerate(j['images']):
        if im.get('name') in repl: im['mimeType']='image/png' if repl[im['name']][:4]==b'\x89PNG' else 'image/jpeg'
    js=json.dumps(j,separators=(',',':')).encode()
    while len(js)%4: js+=b' '
    out=struct.pack('<III',0x46546C67,2,12+8+len(js)+8+len(nb))+struct.pack('<II',len(js),0x4E4F534A)+js+struct.pack('<II',len(nb),0x004E4942)+bytes(nb)
    open(p,'wb').write(out)
