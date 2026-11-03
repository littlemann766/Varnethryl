import json,struct,numpy as np
def write_glb(path, V, F, C, N=None, name='mesh'):
    """indexed POSITION (+NORMAL) + COLOR_0 (float vec4) glb, one node/mesh/primitive"""
    V=np.asarray(V,np.float32); F=np.asarray(F,np.uint32).reshape(-1); C=np.asarray(C,np.float32)
    bufs=[]; views=[]; acc=[]; off=0
    def add(arr,target,comp,typ,count,mm=False):
        nonlocal off
        b=arr.tobytes(); pad=(-len(b))%4
        views.append(dict(buffer=0,byteOffset=off,byteLength=len(b),target=target)); bufs.append(b+b'\0'*pad); off+=len(b)+pad
        a=dict(bufferView=len(views)-1,componentType=comp,count=count,type=typ)
        if mm: a['min']=arr.reshape(count,-1).min(0).tolist(); a['max']=arr.reshape(count,-1).max(0).tolist()
        acc.append(a); return len(acc)-1
    attrs={'POSITION':add(V,34962,5126,'VEC3',len(V),True)}
    if N is not None: attrs['NORMAL']=add(np.asarray(N,np.float32),34962,5126,'VEC3',len(V))
    attrs['COLOR_0']=add(np.clip(np.round(C*255),0,255).astype(np.uint8),34962,5121,'VEC4',len(V)); acc[-1]['normalized']=True
    ind=add(F,34963,5125,'SCALAR',len(F))
    j=dict(asset=dict(version='2.0',generator='beth land1'),scene=0,scenes=[dict(nodes=[0])],nodes=[dict(mesh=0,name=name)],
           meshes=[dict(name=name,primitives=[dict(attributes=attrs,indices=ind,mode=4)])],accessors=acc,bufferViews=views,buffers=[dict(byteLength=off)])
    js=json.dumps(j,separators=(',',':')).encode(); js+=b' '*((-len(js))%4); bin_=b''.join(bufs)
    with open(path,'wb') as f:
        f.write(struct.pack('<III',0x46546C67,2,12+8+len(js)+8+len(bin_))); f.write(struct.pack('<II',len(js),0x4E4F534A)); f.write(js); f.write(struct.pack('<II',len(bin_),0x004E4942)); f.write(bin_)
