# Round-4 High packer: turns kit meshes (atlas UV + COLOR_0 tint) into vertex-colour-FREE meshes on a 2048 slot atlas
# (8x8 slots of 256). Each slot = (source tile, tint cluster) with the tint baked in. Also writes normal (from height),
# ORM (R=AO 1, G=roughness, B=metal) and emissive maps, plus 1024/512 downscales for Medium/Low.
import numpy as np, json, os, struct, math
from PIL import Image, ImageFilter
G=8;S=256;E=4/2048
class Packer:
  def __init__(s,sources,props):
    """sources: list of RGBA PIL images (grid-4 atlases, 1024). props: fn(src,tile)->dict(rough,metal,emit,bump,alpha)"""
    s.src=[np.asarray(im.convert('RGBA')).astype(np.float32) for im in sources];s.props=props;s.samples={};s.meshes=[]
  @staticmethod
  def tri_info(m):
    P=np.array(m.P,np.float32).reshape(-1,3,3);U=np.array(m.U,np.float32).reshape(-1,3,2);C=np.array(m.C,np.float32).reshape(-1,3,3)
    cu=U.mean(1);src=np.floor(cu[:,0]).astype(int);loc=cu-np.stack([src,np.zeros_like(src)],1);tx=np.clip((loc[:,0]*4).astype(int),0,3);ty=np.clip((loc[:,1]*4).astype(int),0,3)
    area=np.linalg.norm(np.cross(P[:,1]-P[:,0],P[:,2]-P[:,0]),axis=1)/2+1e-4
    return P,U,C.mean(1),src,ty*4+tx,area
  def add(s,m):
    P,U,c,src,tile,area=s.tri_info(m)
    for k in set(zip(src.tolist(),tile.tolist())):
      sel=(src==k[0])&(tile==k[1]);s.samples.setdefault(k,[]).append((c[sel],area[sel]))
  def solve(s,budget=G*G-1):
    keys=list(s.samples);data={k:(np.concatenate([a for a,_ in s.samples[k]]),np.concatenate([w for _,w in s.samples[k]])) for k in keys}
    K={k:1 for k in keys}
    def km(X,w,k,it=12):
      if len(X)>6000:idx=np.random.default_rng(0).choice(len(X),6000,replace=False,p=w/w.sum());X=X[idx];w=np.ones(len(X))
      C=X[np.linspace(0,len(X)-1,k).astype(int)].copy() if k>1 else (X*w[:,None]).sum(0,keepdims=True)/w.sum()
      for _ in range(it):
        a=np.argmin(((X[:,None]-C[None])**2).sum(2),1)
        for j in range(k):
          if (a==j).any():C[j]=(X[a==j]*w[a==j,None]).sum(0)/w[a==j].sum()
      err=(w*((X-C[a])**2).sum(1)).sum();return C,err
    res={k:km(*data[k],1) for k in keys}
    while sum(K.values())<budget:
      gains={k:res[k][1] for k in keys if K[k]<len(data[k][0])};
      if not gains:break
      k=max(gains,key=gains.get)
      if gains[k]<1e-3:break
      K[k]+=1;res[k]=km(*data[k],K[k])
    s.slots=[];s.cent={}
    for k in keys:
      s.cent[k]=res[k][0];
      for j in range(len(res[k][0])):s.slots.append((k,j))
    assert len(s.slots)<=G*G,len(s.slots)
    s.slot_of={sl:i for i,sl in enumerate(s.slots)};return len(s.slots)
  def remap(s,m):
    """returns new (P,N,UV) arrays without colour; UV remapped into slots"""
    P,U,c,src,tile,_=s.tri_info(m);N=np.array(m.N,np.float32).reshape(-1,3,3);out=np.zeros_like(U)
    for k in set(zip(src.tolist(),tile.tolist())):
      sel=np.where((src==k[0])&(tile==k[1]))[0];C=s.cent[k];a=np.argmin(((c[sel][:,None]-C[None])**2).sum(2),1)
      for j in range(len(C)):
        ii=sel[a==j];si=s.slot_of[(k,j)];sy,sx=divmod(si,G)
        loc=U[ii]-np.array([k[0],0]);ty,tx=divmod(k[1],4);lu=np.clip((loc[...,0]-tx/4)*4,0,1);lv=np.clip((loc[...,1]-ty/4)*4,0,1)
        out[ii,:,0]=sx/G+E+lu*(1/G-2*E);out[ii,:,1]=sy/G+E+lv*(1/G-2*E)
    return P.reshape(-1,3),N.reshape(-1,3),out.reshape(-1,2)
  def paint(s,outdir,name='atlas'):
    os.makedirs(outdir,exist_ok=True);A=np.zeros((G*S,G*S,4),np.float32);NM=np.zeros((G*S,G*S,3),np.float32);NM[...,2]=1
    ORM=np.zeros((G*S,G*S,3),np.float32);EM=np.zeros((G*S,G*S,3),np.float32);ORM[...,0]=1;ORM[...,1]=.85
    for i,((src,tile),j) in enumerate(s.slots):
      sy,sx=divmod(i,G);ty,tx=divmod(tile,4);t=s.src[src][ty*256:(ty+1)*256,tx*256:(tx+1)*256].copy();pr=s.props(src,tile)
      col=s.cent[(src,tile)][j];t[...,:3]=np.clip(t[...,:3]*col[None,None,:],0,255)
      A[sy*S:(sy+1)*S,sx*S:(sx+1)*S]=t
      h=(t[...,:3].mean(2)/255.)*pr.get('bump',1.0);gx=(np.roll(h,-1,1)-np.roll(h,1,1));gy=(np.roll(h,-1,0)-np.roll(h,1,0));st=6.0
      n=np.dstack([-gx*st,gy*st,np.ones_like(h)]);n/=np.linalg.norm(n,axis=2,keepdims=True);NM[sy*S:(sy+1)*S,sx*S:(sx+1)*S]=n
      ORM[sy*S:(sy+1)*S,sx*S:(sx+1)*S,1]=np.clip(pr.get('rough',.85)+(.5-h/max(pr.get('bump',1),1e-3))*.15,0.05,1);ORM[sy*S:(sy+1)*S,sx*S:(sx+1)*S,2]=pr.get('metal',0)
      ORM[sy*S:(sy+1)*S,sx*S:(sx+1)*S,0]=np.clip(.75+.25*h/max(pr.get('bump',1),1e-3),0,1)
      if pr.get('emit'):e=pr['emit'];m=(t[...,:3].mean(2)>e.get('thr',110)).astype(np.float32)if e.get('mask',True) else np.ones((S,S));EM[sy*S:(sy+1)*S,sx*S:(sx+1)*S]=m[...,None]*np.array(e['col'])[None,None,:]
    ims={'albedo':Image.fromarray(np.clip(A,0,255).astype(np.uint8),'RGBA'),'normal':Image.fromarray(((NM*.5+.5)*255).astype(np.uint8)),
         'orm':Image.fromarray((np.clip(ORM,0,1)*255).astype(np.uint8)),'emissive':Image.fromarray(np.clip(EM,0,255).astype(np.uint8))}
    for res in (2048,1024,512):
      d=os.path.join(outdir,str(res));os.makedirs(d,exist_ok=True)
      for k,im in ims.items():(im if res==2048 else im.resize((res,res),Image.LANCZOS)).save(os.path.join(d,k+'.png'),optimize=True)
    json.dump({'grid':G,'slot':S,'slots':[[int(a),int(b),int(j),[round(float(v),4) for v in s.cent[(a,b)][j]]] for (a,b),j in s.slots]},open(os.path.join(outdir,'slots.json'),'w'))
def _pk(P,N,U):
  key=np.concatenate([P,N,U],1).round(5);uq,inv=np.unique(key,axis=0,return_inverse=True);inv=inv.reshape(-1)
  return inv.astype(np.uint32),uq[:,0:3].astype(np.float32),uq[:,3:6].astype(np.float32),uq[:,6:8].astype(np.float32)
def write_hi(path,name,nodes,texdir,emissive=False,extras=None,alpha=False,emissive_strength=1.0):
  """nodes: [(node_name,(P,N,U),translation)]. One material, textures by relative uri; no COLOR_0."""
  for nn,(P,N,U),tr in nodes:
    nl=np.linalg.norm(N,axis=1,keepdims=True);N/=np.maximum(nl,1e-9)
  blob=b'';views=[];acc=[];meshes=[];gn=[];tot=0
  def view(bb,tgt):
    nonlocal blob;pad=(4-len(bb)%4)%4;views.append({'buffer':0,'byteOffset':len(blob),'byteLength':len(bb),'target':tgt});blob+=bb+b'\0'*pad;return len(views)-1
  for ni,(nn,(P,N,U),tr) in enumerate(nodes):
    I,P2,N2,U2=_pk(P,N,U);tot+=len(I)//3;b0=len(acc)
    acc+=[{'bufferView':view(I.tobytes(),34963),'componentType':5125,'count':int(len(I)),'type':'SCALAR'},
      {'bufferView':view(P2.tobytes(),34962),'componentType':5126,'count':len(P2),'type':'VEC3','min':P2.min(0).tolist(),'max':P2.max(0).tolist()},
      {'bufferView':view(N2.tobytes(),34962),'componentType':5126,'count':len(P2),'type':'VEC3'},{'bufferView':view(U2.tobytes(),34962),'componentType':5126,'count':len(P2),'type':'VEC2'}]
    meshes.append({'name':nn,'primitives':[{'attributes':{'POSITION':b0+1,'NORMAL':b0+2,'TEXCOORD_0':b0+3},'indices':b0,'material':0}]})
    gn.append({'name':nn,'mesh':ni,'translation':list(map(float,tr))})
  rel=os.path.relpath(texdir,os.path.dirname(path)).replace(os.sep,'/')
  imgs=[{'uri':rel+'/albedo.png'},{'uri':rel+'/normal.png'},{'uri':rel+'/orm.png'}]
  mat={'name':name+'_mat','pbrMetallicRoughness':{'baseColorTexture':{'index':0},'metallicRoughnessTexture':{'index':2},'metallicFactor':1.0,'roughnessFactor':1.0},
       'normalTexture':{'index':1,'scale':1.0},'occlusionTexture':{'index':2},'doubleSided':alpha}
  if alpha:mat['alphaMode']='MASK';mat['alphaCutoff']=0.5
  if emissive:imgs.append({'uri':rel+'/emissive.png'});mat['emissiveTexture']={'index':3};mat['emissiveFactor']=[emissive_strength]*3
  g={'asset':{'version':'2.0','generator':'beth-world-hi'},'scene':0,'scenes':[{'nodes':[len(gn)]}],'nodes':gn+[{'name':name,'children':list(range(len(gn))),'extras':extras or {}}],
     'meshes':meshes,'materials':[mat],'textures':[{'sampler':0,'source':i} for i in range(len(imgs))],'samplers':[{'magFilter':9729,'minFilter':9987,'wrapS':33071,'wrapT':33071}],
     'images':imgs,'accessors':acc,'bufferViews':views,'buffers':[{'byteLength':len(blob)}]}
  js=json.dumps(g).encode();js+=b' '*((4-len(js)%4)%4)
  open(path,'wb').write(struct.pack('<III',0x46546C67,2,12+8+len(js)+8+len(blob))+struct.pack('<II',len(js),0x4E4F534A)+js+struct.pack('<II',len(blob),0x004E4942)+blob);return tot
