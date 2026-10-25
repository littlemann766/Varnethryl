# VARNETHRYL world-art kit generator (Beth). One mesh + one shared atlas material per GLB. 1 unit = 1 m, Y-up.
import numpy as np, json, struct, math, os, sys
OUT=sys.argv[1] if len(sys.argv)>1 else '.'
TILES=json.load(open(os.path.join(OUT,'atlas','atlas.json')))['tiles'] if os.path.exists(os.path.join(OUT,'atlas','atlas.json')) else []
rng=np.random.default_rng(42)
BTILES=[]
def tile_uv(name,u,v):
  b=name not in TILES;i=BTILES.index(name) if b else TILES.index(name)
  ty,tx=divmod(i,4);e=3/1024
  return (tx/4+e+u*(0.25-2*e)+(BOFF if b else 0), ty/4+e+v*(0.25-2*e))
BOFF=0
def hexc(h):return np.array([(h>>16)&255,(h>>8)&255,h&255])/255.
def rot(ax,a):
  c,s=math.cos(a),math.sin(a)
  if ax=='y':return np.array([[c,0,s],[0,1,0],[-s,0,c]])
  if ax=='x':return np.array([[1,0,0],[0,c,-s],[0,s,c]])
  return np.array([[c,-s,0],[s,c,0],[0,0,1]])
class M:
  def __init__(s):s.P=[];s.N=[];s.U=[];s.C=[]
  def tri(s,p,uv,col,flat=True,n=None):
    p=np.asarray(p,float)
    if n is None:
      nn=np.cross(p[1]-p[0],p[2]-p[0]);l=np.linalg.norm(nn);nn=nn/l if l>1e-12 else np.array([0,1,0]);n=[nn]*3
    for k in range(3):s.P.append(p[k]);s.N.append(n[k]);s.U.append(uv[k]);s.C.append(col)
  def quad(s,a,b,c,d,tile,col,uvr=(0,0,1,1)):
    u0,v0,u1,v1=uvr
    A,B,C,D=[tile_uv(tile,*q) for q in [(u0,v1),(u1,v1),(u1,v0),(u0,v0)]]
    s.tri([a,b,c],[A,B,C],col);s.tri([a,c,d],[A,C,D],col)
  def merge(s,o,R=np.eye(3),t=(0,0,0),sc=1.0,tint=None):
    for p,n,u,c in zip(o.P,o.N,o.U,o.C):
      s.P.append(R@(np.asarray(p)*sc)+np.asarray(t));s.N.append(R@np.asarray(n));s.U.append(u)
      s.C.append(np.asarray(c)*(tint if tint is not None else 1))
  @property
  def tris(s):return len(s.P)//3
  def bounds(s):
    P=np.array(s.P);return P.min(0),P.max(0)
def box(m,tile,sx,sy,sz,R=np.eye(3),t=(0,0,0),col=(1,1,1),j=0.06):
  hx,hy,hz=sx/2,sy/2,sz/2;V=[np.array(v) for v in [(-hx,0,-hz),(hx,0,-hz),(hx,0,hz),(-hx,0,hz),(-hx,sy,-hz),(hx,sy,-hz),(hx,sy,hz),(-hx,sy,hz)]]
  V=[R@v+np.asarray(t) for v in V];F=[(3,2,6,7),(1,0,4,5),(2,1,5,6),(0,3,7,4),(7,6,5,4),(0,1,2,3)]
  for f in F:
    c=np.asarray(col)*(1+rng.uniform(-j,j));m.quad(V[f[0]],V[f[1]],V[f[2]],V[f[3]],tile,c,(0,0,min(1,sx/2+.2),min(1,sy/2+.2)))
def cyl(m,tile,r0,r1,h,seg,R=np.eye(3),t=(0,0,0),col=(1,1,1),cap=False,j=0.05,bend=(0,0)):
  t=np.asarray(t)
  for i in range(seg):
    a0,a1=2*math.pi*i/seg,2*math.pi*(i+1)/seg
    p=[np.array([math.cos(a)*r,y,math.sin(a)*r])+np.array([bend[0]*(y/h)**2,0,bend[1]*(y/h)**2]) for a,r,y in [(a0,r0,0),(a1,r0,0),(a1,r1,h),(a0,r1,h)]]
    p=[R@q+t for q in p];c=np.asarray(col)*(1+rng.uniform(-j,j))
    m.quad(p[0],p[1],p[2],p[3],tile,c,(i/seg,0,(i+1)/seg,1))
    if cap and r1>0.01:
      ct=R@np.array([bend[0],h,bend[1]])+t;m.tri([p[3],p[2],ct],[tile_uv(tile,.5,.5)]*3,c)
def cone(m,tile,r,h,seg,R=np.eye(3),t=(0,0,0),col=(1,1,1)):
  cyl(m,tile,r,0.0,h,seg,R,t,col)
def ico(sub=1):
  t=(1+5**.5)/2;V=[(-1,t,0),(1,t,0),(-1,-t,0),(1,-t,0),(0,-1,t),(0,1,t),(0,-1,-t),(0,1,-t),(t,0,-1),(t,0,1),(-t,0,-1),(-t,0,1)]
  V=[np.array(v)/np.linalg.norm(v) for v in V]
  F=[(0,11,5),(0,5,1),(0,1,7),(0,7,10),(0,10,11),(1,5,9),(5,11,4),(11,10,2),(10,7,6),(7,1,8),(3,9,4),(3,4,2),(3,2,6),(3,6,8),(3,8,9),(4,9,5),(2,4,11),(6,2,10),(8,6,7),(9,8,1)]
  for _ in range(sub):
    cache={};NF=[]
    def mid(a,b):
      k=(min(a,b),max(a,b))
      if k not in cache:v=V[a]+V[b];V.append(v/np.linalg.norm(v));cache[k]=len(V)-1
      return cache[k]
    for a,b,c in F:ab,bc,ca=mid(a,b),mid(b,c),mid(c,a);NF+=[(a,ab,ca),(b,bc,ab),(c,ca,bc),(ab,bc,ca)]
    F=NF
  return V,F
def blob(m,tile,rad,scale=(1,1,1),sub=1,jit=.18,R=np.eye(3),t=(0,0,0),col=(1,1,1),flat_bottom=None,seed=None,uvs=1.0,colvar=.07,top=None):
  r=np.random.default_rng(seed if seed is not None else int(rng.integers(1e9)))
  V,F=ico(sub);V=[v*(1+r.uniform(-jit,jit))*rad*np.asarray(scale) for v in V]
  if flat_bottom is not None:V=[np.array([v[0],max(v[1],flat_bottom),v[2]]) for v in V]
  V=[R@v+np.asarray(t) for v in V]
  for a,b,c in F:
    p=[V[a],V[b],V[c]];n=np.cross(p[1]-p[0],p[2]-p[0]);l=np.linalg.norm(n)
    if l<1e-9:continue
    n/=l;ax=np.argmax(np.abs(n));ix=[k for k in range(3) if k!=ax]
    b0=[math.floor(min(pp[ix[0]] for pp in p)*uvs*.25),math.floor(min(pp[ix[1]] for pp in p)*uvs*.25)]
    uv=[tile_uv(tile,min(1,q[ix[0]]*uvs*.25-b0[0]),min(1,q[ix[1]]*uvs*.25-b0[1])) for q in p]
    c=np.asarray(col)*(1+r.uniform(-colvar,colvar))
    if top is not None and n[1]>0.55:c=np.asarray(top)*(1+r.uniform(-colvar,colvar))
    m.tri(p,uv,c)
def cards(m,tile,w,h,n,t=(0,0,0),col=(1,1,1),yaw=0,tilt=0,y0=0):
  t=np.asarray(t)
  for i in range(n):
    a=yaw+math.pi*i/n;R=rot('y',a)@rot('x',tilt)
    pts=[R@np.array(v)+t for v in [(-w/2,y0,0),(w/2,y0,0),(w/2,y0+h,0),(-w/2,y0+h,0)]]
    m.quad(*pts,tile,np.asarray(col))
# ---------- GLB writer ----------
def _pack(m):
  P=np.array(m.P,np.float32);N=np.array(m.N,np.float32);U=np.array(m.U,np.float32);C=np.clip(np.array(m.C,np.float32),0,1)
  N/=np.maximum(np.linalg.norm(N,axis=1,keepdims=True),1e-9)
  key=np.concatenate([P,N,U,C],1).round(5);uq,inv=np.unique(key,axis=0,return_inverse=True);inv=inv.reshape(-1)
  P,N,U,C=[uq[:,a:b].astype(np.float32) for a,b in ((0,3),(3,6),(6,8),(8,11))]
  I=inv.astype(np.uint16 if len(uq)<65535 else np.uint32);return I,P,N,U,C
def write_glb(m,path,name,extras=None,atlas='atlas',nodes=None,mat_name='beth_kit_atlas',emissive=None):
  """nodes: list of (node_name, M, translation) -> one mesh per node, all sharing ONE material."""
  nodes=nodes or [(name,m,(0,0,0))];blob=b'';views=[];acc=[];meshes=[];gn=[];tot=0
  def view(bb,tgt):
    nonlocal blob;pad=(4-len(bb)%4)%4;views.append({'buffer':0,'byteOffset':len(blob),'byteLength':len(bb),'target':tgt});blob+=bb+b'\0'*pad;return len(views)-1
  for ni,(nn,mm,tr) in enumerate(nodes):
    I,P,N,U,C=_pack(mm);tot+=len(I)//3;b0=len(acc)
    acc+= [{'bufferView':view(I.tobytes(),34963),'componentType':5123 if I.dtype==np.uint16 else 5125,'count':int(len(I)),'type':'SCALAR'},
       {'bufferView':view(P.tobytes(),34962),'componentType':5126,'count':len(P),'type':'VEC3','min':P.min(0).tolist(),'max':P.max(0).tolist()},
       {'bufferView':view(N.tobytes(),34962),'componentType':5126,'count':len(P),'type':'VEC3'},{'bufferView':view(U.tobytes(),34962),'componentType':5126,'count':len(P),'type':'VEC2'},
       {'bufferView':view(C.tobytes(),34962),'componentType':5126,'count':len(P),'type':'VEC3'}]
    meshes.append({'name':nn,'primitives':[{'attributes':{'POSITION':b0+1,'NORMAL':b0+2,'TEXCOORD_0':b0+3,'COLOR_0':b0+4},'indices':b0,'material':0}]})
    gn.append({'name':nn,'mesh':ni,'translation':list(map(float,tr))})
  rel=os.path.relpath(os.path.join(OUT,atlas),os.path.dirname(path))
  g={'asset':{'version':'2.0','generator':'beth-world-kit'},'extensionsUsed':['EXT_texture_webp'],'scene':0,'scenes':[{'nodes':[len(gn)]}],
     'nodes':gn+[{'name':name,'children':list(range(len(gn))),'extras':extras or {}}],'meshes':meshes,
     'materials':[{'name':mat_name,'pbrMetallicRoughness':{'baseColorTexture':{'index':0},'metallicFactor':0.0,'roughnessFactor':0.85},'alphaMode':'MASK','alphaCutoff':0.5,'doubleSided':True}],
     'textures':[{'sampler':0,'source':0,'extensions':{'EXT_texture_webp':{'source':1}}}],'samplers':[{'magFilter':9729,'minFilter':9987,'wrapS':33071,'wrapT':33071}],
     'images':[{'uri':rel+'/atlas.png'},{'uri':rel+'/atlas.webp'}],'accessors':acc,'bufferViews':views,'buffers':[{'byteLength':len(blob)}]}
  if emissive:  # night windows: emissive mask atlas (black except window/glass panes); scale emissiveFactor per quality tier / time of day
    g['images']+= [{'uri':rel+'/emissive.png'},{'uri':rel+'/emissive.webp'}];g['textures'].append({'sampler':0,'source':2,'extensions':{'EXT_texture_webp':{'source':3}}})
    g['materials'][0]['emissiveTexture']={'index':1};g['materials'][0]['emissiveFactor']=[float(v) for v in emissive]
  js=json.dumps(g).encode();js+=b' '*((4-len(js)%4)%4)
  data=struct.pack('<III',0x46546C67,2,12+8+len(js)+8+len(blob))+struct.pack('<II',len(js),0x4E4F534A)+js+struct.pack('<II',len(blob),0x004E4942)+blob
  open(path,'wb').write(data);return tot
