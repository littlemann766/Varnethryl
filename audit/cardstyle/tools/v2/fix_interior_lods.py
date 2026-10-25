# Rebuild interior prop LODs that exceed the caps (lod1<=50%, lod2<=20% of High): decimate High geometry (deci, UV reproject)
# and write it into the existing LOD GLB, keeping its embedded lod-res atlas images/material untouched.
import json, struct, numpy as np, trimesh, os, sys
from deci import decimate, normals
D='/workspace/godot-art/interiors'
def rglb(f):
    b=open(f,'rb').read(); n=struct.unpack('<I',b[12:16])[0]; j=json.loads(b[20:20+n]); o=20+n; bl=struct.unpack('<I',b[o:o+4])[0]; return j,b[o+8:o+8+bl]
def wglb(f,j,bin_):
    js=json.dumps(j,separators=(',',':')).encode(); js+=b' '*((4-len(js)%4)%4); bin_+=b'\0'*((4-len(bin_)%4)%4)
    out=struct.pack('<III',0x46546C67,2,12+8+len(js)+8+len(bin_))+struct.pack('<II',len(js),0x4E4F534A)+js+struct.pack('<II',len(bin_),0x004E4942)+bin_
    open(f,'wb').write(out)
def put(j,lod_file,P,F,UV):
    j0,b0=rglb(lod_file); bv=j0['bufferViews']; acc=j0['accessors']; prim=j0['meshes'][0]['primitives'][0]
    geo_idx=[prim['attributes']['POSITION'],prim['attributes']['NORMAL'],prim['attributes']['TEXCOORD_0'],prim['indices']]
    assert len(j0['meshes'])==1 and len(prim['attributes'])==3 and sorted(acc[i]['bufferView'] for i in geo_idx)==[0,1,2,3]
    # weld for compact indices
    key=np.hstack([P.round(5),UV.round(5)]); u,first,inv=np.unique(key,axis=0,return_index=True,return_inverse=True); inv=inv.ravel()
    Pv=P[first].astype(np.float32); UVv=UV[first].astype(np.float32); UVv[:,1]=1-UVv[:,1]; I=inv.reshape(-1).astype(np.uint32)
    Nf=normals(P,F); N=np.zeros_like(Pv,dtype=np.float64); np.add.at(N,inv,np.repeat(Nf,3,axis=0) if len(Nf)==len(F) else Nf)
    N/=np.linalg.norm(N,axis=1,keepdims=True)+1e-12; N=N.astype(np.float32)
    parts=[Pv.tobytes(),N.tobytes(),UVv.tobytes(),I.tobytes()]; new=b''; views=[]
    for p,t in zip(parts,(34962,34962,34962,34963)):
        views.append({'buffer':0,'byteOffset':len(new),'byteLength':len(p),'target':t}); new+=p; new+=b'\0'*((4-len(new)%4)%4)
    for v in bv[4:]:
        data=b0[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']]; nv=dict(v); nv['byteOffset']=len(new); views.append(nv); new+=data; new+=b'\0'*((4-len(new)%4)%4)
    j0['bufferViews']=views; j0['buffers']=[{'byteLength':len(new)}]
    acc[geo_idx[0]].update(bufferView=0,count=len(Pv),min=Pv.min(0).tolist(),max=Pv.max(0).tolist())
    acc[geo_idx[1]].update(bufferView=1,count=len(Pv)); acc[geo_idx[2]].update(bufferView=2,count=len(Pv)); acc[geo_idx[3]].update(bufferView=3,count=len(I),componentType=5125)
    wglb(lod_file,j0,new)
idx=json.load(open(D+'/index.json')); fixed={}
for k,p in idx['props'].items():
    hi=trimesh.load(f"{D}/{p['files']['high']}",force='mesh',process=False); n=len(hi.faces)
    P=hi.vertices[hi.faces].reshape(-1,3); UV=hi.visual.uv[hi.faces].reshape(-1,2); F=np.arange(len(P)).reshape(-1,3)
    for lv,fr in (('lod1',0.5),('lod2',0.2)):
        lf=f"{D}/{p['files'][lv]}"; cur=len(trimesh.load(lf,force='mesh',process=False).faces)
        if cur<=n*fr: continue
        P2,F2,UV2=decimate(P,F,UV,int(n*fr*0.97)); put(None,lf,P2,F2,UV2)
        new=len(trimesh.load(lf,force='mesh',process=False).faces); p['tris'][lv]=new; fixed.setdefault(k,{})[lv]=(cur,new)
    p['tris']['high']=n
json.dump(idx,open(D+'/index.json','w'),indent=1); print(json.dumps(fixed))
