import json,struct,io,numpy as np
from PIL import Image
def write_glb(path,V,F,UV,N,imgs,name):
    V=V.astype(np.float32);N=N.astype(np.float32);UV=UV.astype(np.float32).copy();UV[:,1]=1-UV[:,1]
    I=F.astype(np.uint32).ravel()
    blobs=[];views=[];acc=[]
    def add(data,target=None):
        off=sum(len(b) for b in blobs); pad=(-len(data))%4; blobs.append(data+b'\0'*pad)
        v={'buffer':0,'byteOffset':off,'byteLength':len(data)}
        if target: v['target']=target
        views.append(v); return len(views)-1
    def acc_add(arr,typ,ct,target,minmax=False):
        a={'bufferView':add(arr.tobytes(),target),'componentType':ct,'count':len(arr),'type':typ}
        if minmax: a['min']=arr.min(0).tolist(); a['max']=arr.max(0).tolist()
        acc.append(a); return len(acc)-1
    pa=acc_add(V,'VEC3',5126,34962,True); na=acc_add(N,'VEC3',5126,34962); ua=acc_add(UV,'VEC2',5126,34962); ia=acc_add(I,'SCALAR',5125,34963)
    images=[]
    for k,fmt in [('a','JPEG'),('n','JPEG'),('o','JPEG'),('e','JPEG')]:
        b=io.BytesIO(); Image.fromarray((np.clip(imgs[k],0,1)*255).astype(np.uint8)).save(b,fmt,**({'quality':88} if fmt=='JPEG' else {'optimize':True}))
        images.append({'bufferView':add(b.getvalue()),'mimeType':'image/jpeg' if fmt=='JPEG' else 'image/png'})
    j={'asset':{'version':'2.0','generator':'beth-cardstyle'},'scene':0,'scenes':[{'nodes':[0]}],
       'nodes':[{'name':name,'mesh':0}],'meshes':[{'name':name,'primitives':[{'attributes':{'POSITION':pa,'NORMAL':na,'TEXCOORD_0':ua},'indices':ia,'material':0}]}],
       'materials':[{'name':name+'_mat','pbrMetallicRoughness':{'baseColorTexture':{'index':0},'metallicRoughnessTexture':{'index':2},'metallicFactor':1.0,'roughnessFactor':1.0},
         'normalTexture':{'index':1},'occlusionTexture':{'index':2},'emissiveTexture':{'index':3},'emissiveFactor':[1,1,1]}],
       'textures':[{'source':i,'sampler':0} for i in range(4)],'samplers':[{'magFilter':9729,'minFilter':9987,'wrapS':33071,'wrapT':33071}],
       'images':images,'accessors':acc,'bufferViews':views}
    bin_=b''.join(blobs); j['buffers']=[{'byteLength':len(bin_)}]; bj=json.dumps(j).encode(); bj+=b' '*((-len(bj))%4)
    with open(path,'wb') as f:
        f.write(struct.pack('<III',0x46546C67,2,12+8+len(bj)+8+len(bin_)))
        f.write(struct.pack('<II',len(bj),0x4E4F534A)+bj+struct.pack('<II',len(bin_),0x004E4942)+bin_)
