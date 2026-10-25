# Round-4 High terrain: sculpted heightfield peaks with real snow caps, strata cliffs, volcano flank with emissive lava
# channels, shore/water-edge strips, big strata boulders. LODs by grid decimation. Vertex-colour free (hipack).
import sys,os,json,math,numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import kit,hipack
from kit import M,tile_uv
from PIL import Image,ImageDraw,ImageFilter
OUT=os.path.abspath(sys.argv[1]);HI=os.path.join(OUT,'hi','terrain');os.makedirs(HI,exist_ok=True)
T=256
def noise2(seed,s=T,oc=6):
  g=np.random.default_rng(seed);o=np.zeros((s,s))
  for k in range(oc):n=2**(k+2);o+=np.asarray(Image.fromarray((g.random((n,n))*255).astype(np.uint8)).resize((s,s),Image.BICUBIC))/255/2**k
  o-=o.min();return o/o.max()
def rgb(h):return np.array([(h>>16)&255,(h>>8)&255,h&255],float)
def tile(base,amt,seed):n=noise2(seed)[...,None];return np.clip(rgb(base)[None,None]*(1-amt+2*amt*n),0,255)
X=np.zeros((1024,1024,4),np.uint8);X[...,3]=255
EXTRA=['strata','lava','sand','wetsand','wetrock','mossrock','snowpack','scree','ash','foam','cliffgrass','obsidian']
def put(i,a):y,x=divmod(i,4);X[y*T:(y+1)*T,x*T:(x+1)*T,:3]=np.clip(a,0,255).astype(np.uint8)
yy=np.arange(T)[:,None]/T;n1=noise2(11)
bands=np.sin((yy*7+n1*.6)*2*math.pi)*.5+.5
put(0,tile(0x8a7a68,.12,1)*(.75+.35*bands[...,None]))
lv=noise2(12);cr=(np.abs(noise2(13)-.5)<.06).astype(float);put(1,np.dstack([255*np.ones((T,T)),120+110*lv,20+40*lv])*(1-.6*cr[...,None]))
put(2,tile(0xd8c49a,.08,3));put(3,tile(0xa08c68,.1,4));put(4,tile(0x4a4a4e,.25,5));put(5,tile(0x6a7258,.25,6));put(6,tile(0xeef3fa,.05,7));put(7,tile(0x7c766e,.3,8))
put(8,tile(0x48423e,.2,9));fo=noise2(10);put(9,np.dstack([230+20*fo,236+18*fo,240+15*fo]));put(10,tile(0x5e8a40,.2,14));put(11,tile(0x1e1a22,.15,15))
EI=os.path.join(HI,'extra');os.makedirs(EI,exist_ok=True);Image.fromarray(X).save(os.path.join(EI,'extra.png'))
kit.BTILES=EXTRA;kit.BOFF=1
def U(name,u,v):return tile_uv(name,u,v)
def fbm(x,z,seed,oc=6,ridged=False):
  r=np.random.default_rng(seed);v=np.zeros_like(x);a=1;f=1/40
  for k in range(oc):
    ph=r.uniform(0,100,4);s=np.sin(x*f+ph[0])*np.cos(z*f*1.13+ph[1])+np.sin((x*.7-z*.6)*f*1.7+ph[2])*.6+np.cos((x*.5+z*.8)*f*2.3+ph[3])*.4
    v+=a*((1-np.abs(s)) if ridged else s);a*=.5;f*=2.03
  return v
def grid_mesh(Hf,R,N,tilefn,seed=0,uvsz=4.0):
  """Hf(x,z)->y ; square grid of N cells over [-R,R]^2 ; tilefn(x,y,z,nx,ny,nz,slope)->(tile,col)"""
  xs=np.linspace(-R,R,N+1);Xg,Zg=np.meshgrid(xs,xs);Y=Hf(Xg,Zg);h=xs[1]-xs[0]
  gy,gx=np.gradient(Y,h);Nn=np.dstack([-gx,np.ones_like(Y),-gy]);Nn/=np.linalg.norm(Nn,axis=2,keepdims=True)
  m=M()
  for i in range(N):
    for j in range(N):
      ids=[(i,j),(i,j+1),(i+1,j+1),(i+1,j)]
      ys=[Y[a] for a in ids]
      if max(ys)<-50:continue
      cx,cz=(Xg[i,j]+Xg[i,j+1])/2,(Zg[i,j]+Zg[i+1,j])/2;cy=np.mean(ys);nn=Nn[i,j];sl=1-nn[1]
      tl,col=tilefn(cx,cy,cz,nn,sl)
      P=[np.array([Xg[a],Y[a],Zg[a]]) for a in ids];NN=[Nn[a] for a in ids]
      # triplanar-ish: steep cells map u along x/z, v along y
      if sl>.45:uv=[((p[0]+p[2])/uvsz%1,(p[1]/uvsz)%1) for p in P]
      else:uv=[((p[0]/uvsz)%1,(p[2]/uvsz)%1) for p in P]
      # avoid wrap inside a cell
      u0=min(q[0] for q in uv);v0=min(q[1] for q in uv)
      uv=[(min(1,q[0] if q[0]-u0<.5 else q[0]-1+1e-3),min(1,q[1] if q[1]-v0<.5 else q[1]-1+1e-3)) for q in uv]
      uv=[(max(0,a),max(0,b)) for a,b in uv]
      UV=[U(tl,*q) if tl in EXTRA else kit.tile_uv(tl,*q) for q in uv]
      m.tri([P[0],P[1],P[2]],[UV[0],UV[1],UV[2]],col,n=[NN[0],NN[1],NN[2]]);m.tri([P[0],P[2],P[3]],[UV[0],UV[2],UV[3]],col,n=[NN[0],NN[2],NN[3]])
  return m
WH=np.ones(3)
def peak(N,seed=1,R=60,H=72,snowy=True):
  def Hf(x,z):
    r=np.sqrt(x*x+z*z)/R;base=np.clip(1-r,0,1)**1.6*H;rid=fbm(x,z,seed,6,True)
    return base*(.75+.25*rid/2)+fbm(x,z,seed+5,4)*2.0-np.clip(r-1,0,1)*30
  def tf(x,y,z,n,sl):
    sn=y>H*(.5+.06*math.sin(x*.2)+.05*math.cos(z*.17))
    if snowy and sn and sl<.55:return 'snowpack',WH
    if snowy and sn:return 'snow' if sl<.7 else 'rock',WH*(.95 if sl<.7 else .9)
    if sl>.4:return 'strata',WH*(.9+.1*math.sin(y*.35))
    if y<H*.15:return ('cliffgrass' if snowy else 'scree'),WH
    return 'scree',WH
  return grid_mesh(Hf,R*1.05,N,tf)
def volcano(N,seed=3,R=70,H=55):
  ang=np.linspace(0,2*math.pi,7)[:-1]+.3
  def Hf(x,z):
    r=np.sqrt(x*x+z*z)/R;a=np.arctan2(z,x);base=np.clip(1-r,0,1)**1.2*H
    crater=np.clip(.16-r,0,1)/.16*H*.35
    ch=sum(np.exp(-((np.angle(np.exp(1j*(a-c))))*(r*R+8)/2.2)**2) for c in ang)*np.clip((r-.1)*3,0,1)*np.clip(1-r,0,1)*3.0
    return base-crater-ch+fbm(x,z,seed,5,True)*1.8
  def tf(x,y,z,n,sl):
    r=math.hypot(x,z)/R;a=math.atan2(z,x)
    d=min(abs(math.atan2(math.sin(a-c),math.cos(a-c)))*(r*R+8) for c in ang)
    if d<1.4 and .12<r<.92:return 'lava',WH
    if r<.17:return 'lava' if y<H*.6 else 'obsidian',WH
    if d<3.2:return 'obsidian',WH
    return ('ash' if sl<.35 else 'basalt'),WH*(.9+.1*math.sin(y*.4))
  return grid_mesh(Hf,R,N,tf)
def cliff(N,seed=4,Lx=60,H=34):
  m=M();xs=np.linspace(-Lx/2,Lx/2,N+1);ys=np.linspace(0,H,max(4,N//2)+1);Xg,Yg=np.meshgrid(xs,ys)
  led=np.floor(Yg/4.0);Z=-(fbm(Xg,Yg*2.2,seed,5)*1.2+np.sin(Yg*1.6)*.35+led*.6+np.where((Yg%4)<.5,.9,0))
  Z=Z*(np.clip(np.abs(Xg)/(Lx/2),0,1)<.98)
  for i in range(len(ys)-1):
    for j in range(N):
      P=[np.array([Xg[i,j],Yg[i,j],Z[i,j]]),np.array([Xg[i,j+1],Yg[i,j+1],Z[i,j+1]]),np.array([Xg[i+1,j+1],Yg[i+1,j+1],Z[i+1,j+1]]),np.array([Xg[i+1,j],Yg[i+1,j],Z[i+1,j]])]
      n=np.cross(P[1]-P[0],P[3]-P[0]);n/=np.linalg.norm(n)+1e-9
      y=Yg[i,j];tl='cliffgrass' if y>H-1.5 or (n[1]>.6) else ('strata' if (int(y/4)%2==0) else 'rock');col=WH*(.82+.18*math.sin(y*.9))
      q=[((p[0]/4)%1,(p[1]/4)%1) for p in P];u0=min(a for a,_ in q);v0=min(b for _,b in q)
      q=[(a if a-u0<.5 else 0.999,b if b-v0<.5 else .999) for a,b in q]
      UV=[U(tl,*qq) if tl in EXTRA else kit.tile_uv(tl,*qq) for qq in q]
      m.tri([P[0],P[1],P[2]],[UV[0],UV[1],UV[2]],col,n=[n]*3);m.tri([P[0],P[2],P[3]],[UV[0],UV[2],UV[3]],col,n=[n]*3)
  top=grid_mesh(lambda x,z:H+fbm(x,z,seed+2,3)*.6+0*x,Lx/2,max(4,N//3),lambda x,y,z,n,sl:('cliffgrass',WH))
  sub=M();sub.merge(top,np.eye(3),(0,0,-Lx/2));m.merge(sub)
  return m
def shore(N,seed=6,L=40,W=14):
  m=M()
  def Hf(x,z):return (z/W)*3.2-0.9+fbm(x,z,seed,4)*.25
  def tf(x,y,z,n,sl):
    if y<-0.55:return 'wetrock',WH
    if y<-0.05:return 'wetsand',WH
    if y<0.18:return 'foam',WH
    if y<1.4:return 'sand',WH
    return 'cliffgrass',WH
  g=grid_mesh(Hf,L/2,N,tf,uvsz=3.0)
  r=np.random.default_rng(seed)
  for i in range(10 if N>20 else 4):kit.blob(g,'rock',r.uniform(.5,1.4),scale=(1.3,.6,1),sub=2 if N>20 else 1,t=(r.uniform(-L/2,L/2),-0.4,r.uniform(-W*.6,-1)),col=WH*.8,uvs=.5)
  return g
def boulder(sub,seed=7):
  m=M();kit.blob(m,'strata',4,scale=(1.3,.8,1),sub=sub,jit=.2,col=WH,seed=seed,uvs=.25) if False else None
  kit.BOFF=1;kit.blob(m,'strata',4,scale=(1.3,.8,1),sub=sub,jit=.2,col=WH,seed=seed,uvs=.25,top=WH*1.0);kit.blob(m,'mossrock',2.2,scale=(1.2,.6,1),sub=max(1,sub-1),t=(1.5,2.4,0),col=WH,seed=seed+1);return m
SET={'peak_snow_hi':[(lambda n:peak(n,1)),(170,70,24)],'peak_bare_hi':[(lambda n:peak(n,2,50,48,False)),(110,56,22)],'volcano_flank_hi':[(lambda n:volcano(n)),(165,70,26)],
     'cliff_strata_hi':[(lambda n:cliff(n)),(150,70,24)],'shore_edge_hi':[(lambda n:shore(n)),(80,40,12)],'boulder_strata_hi':[(lambda n:boulder(n)),(4,3,2)]}
MESH={}
for name,(f,Ns) in SET.items():
  for li,n in enumerate(Ns):kit.rng=np.random.default_rng(9);MESH[(name,li)]=f(n);print(name,li,len(MESH[(name,li)].P)//3)
LT=json.load(open(os.path.join(OUT,'atlas','atlas.json')))['tiles']
def props(src,t):
  n=(LT if src==0 else EXTRA)[t] if t<len(LT if src==0 else EXTRA) else '?';p={'rough':.9,'bump':1.2}
  if n in('ice','wetrock','wetsand'):p.update(rough=.25)
  if n in('snow','snowpack'):p.update(rough=.6,bump=.4)
  if n=='lava':p.update(rough=.5,emit={'col':(255,110,30),'mask':False})
  if n=='obsidian':p.update(rough=.2)
  return p
P=hipack.Packer([Image.open(os.path.join(OUT,'atlas','atlas.png')),Image.open(os.path.join(EI,'extra.png'))],props)
for m in MESH.values():P.add(m)
print('slots',P.solve());TD=os.path.join(HI,'tex');P.paint(TD)
REG=[]
for (name,li),m in MESH.items():
  sfx=['','_lod1','_lod2'][li];res=[2048,1024,512][li];path=os.path.join(HI,name+sfx+'.glb')
  t=hipack.write_hi(path,name+sfx,[(name,P.remap(m),(0,0,0))],os.path.join(TD,str(res)),emissive=name.startswith('volcano'),extras={'tier':['high','medium','low'][li],'units':'m'},emissive_strength=2.0)
  REG.append({'file':f'hi/terrain/{name}{sfx}.glb','tris':t,'tex':res});print(name+sfx,t)
json.dump(REG,open(os.path.join(HI,'index.json'),'w'),indent=1)
