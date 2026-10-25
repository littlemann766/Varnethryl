import json,struct,numpy as np
def write_glb(path,P,F,UV,N,name,atlas_rel):
    P=P.astype(np.float32);N=N.astype(np.float32);UV=UV.astype(np.float32).copy();UV[:,1]=1-UV[:,1]
    I=F.astype(np.uint32).ravel(); blobs=[];views=[];acc=[]
    def add(data,target):
        off=sum(len(b) for b in blobs); blobs.append(data+b'\0'*((-len(data))%4)); views.append({'buffer':0,'byteOffset':off,'byteLength':len(data),'target':target}); return len(views)-1
    def A(arr,typ,ct,target,mm=False):
        a={'bufferView':add(arr.tobytes(),target),'componentType':ct,'count':len(arr),'type':typ}
        if mm: a['min']=arr.min(0).tolist(); a['max']=arr.max(0).tolist()
        acc.append(a); return len(acc)-1
    pa=A(P,'VEC3',5126,34962,True); na=A(N,'VEC3',5126,34962); ua=A(UV,'VEC2',5126,34962); ia=A(I,'SCALAR',5125,34963)
    j={'asset':{'version':'2.0','generator':'beth-card2'},'scene':0,'scenes':[{'nodes':[0]}],'nodes':[{'name':name,'mesh':0}],
       'meshes':[{'name':name,'primitives':[{'attributes':{'POSITION':pa,'NORMAL':na,'TEXCOORD_0':ua},'indices':ia,'material':0}]}],
       'materials':[{'name':'card2_shared','doubleSided':True,'pbrMetallicRoughness':{'baseColorTexture':{'index':0},'metallicRoughnessTexture':{'index':2},'metallicFactor':1.0,'roughnessFactor':1.0},
          'normalTexture':{'index':1},'occlusionTexture':{'index':2},'emissiveTexture':{'index':3},'emissiveFactor':[1,1,1]}],
       'textures':[{'source':i,'sampler':0} for i in range(4)],'samplers':[{'magFilter':9729,'minFilter':9987,'wrapS':10497,'wrapT':10497}],
       'images':[{'uri':f'{atlas_rel}/card2_{k}.jpg'} for k in('albedo','normal','orm','emissive')],'accessors':acc,'bufferViews':views}
    b=b''.join(blobs); j['buffers']=[{'byteLength':len(b)}]; bj=json.dumps(j).encode(); bj+=b' '*((-len(bj))%4)
    open(path,'wb').write(struct.pack('<III',0x46546C67,2,28+len(bj)+len(b))+struct.pack('<II',len(bj),0x4E4F534A)+bj+struct.pack('<II',len(b),0x004E4942)+b)
