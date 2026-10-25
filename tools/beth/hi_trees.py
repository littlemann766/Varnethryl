# Round-4 High trees & foliage: branching trunks, dense alpha-cut leaf cards with canopy-spherical normals, LOD1/LOD2.
import sys,os,json,math,numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import kit,hipack
from kit import M,rot,cyl,tile_uv,hexc as W
from assets import LEAFC,billboard
from PIL import Image
OUT=os.path.abspath(sys.argv[1]);HI=os.path.join(OUT,'hi','trees');os.makedirs(HI,exist_ok=True)
def card(m,c,cen,size,tile,col,r):
  a=r.uniform(0,6.28);t=r.uniform(-.6,.6);R=rot('y',a)@rot('x',t);u=R@np.array([1.,0,0])*size/2;v=R@np.array([0,1.,0])*size/2
  P=[c-u-v,c+u-v,c+u+v,c-u+v];UV=[tile_uv(tile,*q) for q in ((0,1),(1,1),(1,0),(0,0))]
  N=[(p-cen)/(np.linalg.norm(p-cen)+1e-9)*.7+np.array([0,.3,0]) for p in P];N=[n/np.linalg.norm(n) for n in N]
  cc=col*(1+r.uniform(-.12,.12))
  m.tri([P[0],P[1],P[2]],[UV[0],UV[1],UV[2]],cc,n=[N[0],N[1],N[2]]);m.tri([P[0],P[2],P[3]],[UV[0],UV[2],UV[3]],cc,n=[N[0],N[2],N[3]])
def branchy(m,r,base,dirv,L,rad,depth,tips,tile='bark',col=np.ones(3),seg=7):
  d=dirv/np.linalg.norm(dirv);ax=np.cross([0,1,0],d);s=np.linalg.norm(ax)
  R=np.eye(3) if s<1e-6 else (lambda k,ang:np.eye(3)+math.sin(ang)*k+(1-math.cos(ang))*k@k)(np.array([[0,-ax[2],ax[1]],[ax[2],0,-ax[0]],[-ax[1],ax[0],0]])/s,math.asin(min(1,s)) if d[1]>0 else math.pi-math.asin(min(1,s)))
  cyl(m,tile,rad,rad*.62,L,seg,R=R,t=tuple(base),col=col);end=base+d*L
  if depth==0:tips.append(end);return
  for k in range(3 if depth>1 else 2):
    nd=d+np.array([r.uniform(-.9,.9),r.uniform(.1,.6),r.uniform(-.9,.9)]);branchy(m,r,base+d*L*r.uniform(.55,1.0),nd,L*r.uniform(.55,.75),rad*.6,depth-1,tips,tile,col,max(4,seg-2))
  tips.append(end)
def broadleaf(seed,lod,pal,H=(3.0,3.6),crown=2.4,cards=(1100,300),tile_b='bark',bcol=np.ones(3),leafsize=.9):
  m=M();r=np.random.default_rng(seed);h=r.uniform(*H);tips=[]
  branchy(m,r,np.zeros(3),np.array([r.uniform(-.1,.1),1,r.uniform(-.1,.1)]),h,.32,3 if lod==0 else 2,tips,tile_b,bcol,9 if lod==0 else 6)
  cen=np.mean(tips,0);cen[1]=max(cen[1],h+.6);n=cards[lod]
  for i in range(n):
    tp=tips[i%len(tips)];c=tp+r.normal(0,crown*.33,3)*np.array([1,.7,1]);c=cen+(c-cen)*min(1,crown/(np.linalg.norm(c-cen)+1e-6))
    card(m,c,cen,leafsize*r.uniform(.8,1.25)*(1 if lod==0 else 1.6),'leaf',LEAFC[pal],r)
  return m
def conifer(seed,lod,snowy):
  m=M();r=np.random.default_rng(seed);H=r.uniform(8,10);cyl(m,'bark',.3,.08,H,9 if lod==0 else 6)
  tiers=9 if lod==0 else 5;cen=np.array([0,H*.45,0])
  for i in range(tiers):
    y=H*(.15+.82*i/tiers);rad=(2.6-2.1*i/tiers)
    nb=18 if lod==0 else 8
    for k in range(nb):
      a=k/nb*6.283+r.uniform(-.2,.2);d=np.array([math.cos(a),-.35,math.sin(a)])
      if lod==0:cyl(m,'bark',.06,.02,rad,4,R=rot('y',-a)@rot('z',-math.pi/2+.35),t=(0,y,0))
      for q in range(5 if lod==0 else 2):
        c=np.array([0,y,0])+d*rad*(.35+.3*q);card(m,c,cen,1.3*(1 if lod==0 else 1.8),'pinecard',W(0xffffff),r)
        if snowy and q==0:kit.blob(m,'snow',.32*rad,scale=(1.4,.35,1),sub=0,t=tuple(c+np.array([0,.25,0])),col=np.ones(3),uvs=1.0)
  return m
def bush(seed,lod,pal):
  m=M();r=np.random.default_rng(seed);cen=np.array([0,.6,0])
  for i in range(380 if lod==0 else 90):c=cen+r.normal(0,.45,3)*np.array([1.3,.6,1.2]);card(m,c,cen,.55*(1 if lod==0 else 1.6),'leaf',LEAFC[pal]*.9,r)
  return m
def grass(seed,lod):
  m=M();r=np.random.default_rng(seed);cen=np.array([0,-1.0,0])
  for i in range(220 if lod==0 else 50):
    c=np.array([r.uniform(-1,1),.32,r.uniform(-1,1)]);card(m,c,cen,.7,'grass',np.ones(3),r)
  return m
SET=[('oak_hi',lambda l:broadleaf(1,l,'green')),('oak_autumn_hi',lambda l:broadleaf(2,l,'autumn')),('oak_deep_hi',lambda l:broadleaf(3,l,'deep',H=(3.4,4.0),crown=2.8)),
     ('birch_hi',lambda l:broadleaf(4,l,'lime',H=(4.4,5.2),crown=1.9,tile_b='snow',bcol=W(0xd8d4cc),leafsize=.7)),('blossom_hi',lambda l:broadleaf(5,l,'blossom',crown=2.2)),
     ('pine_hi',lambda l:conifer(6,l,False)),('pine_snow_hi',lambda l:conifer(7,l,True)),('bush_hi',lambda l:bush(8,l,'green')),('bush_autumn_hi',lambda l:bush(9,l,'autumn')),('grass_clump_hi',lambda l:grass(10,l))]
BB={'oak':('oak',6.0,6.0),'pine':('pine',10.0,5.5)}
MESH={}
for name,f in SET:
  for l in (0,1):kit.rng=np.random.default_rng(3);MESH[(name,l)]=f(l)
  kind='pine' if 'pine' in name else 'oak'
  if 'bush' not in name and 'grass' not in name:MESH[(name,2)]=billboard(*BB[kind])
  print(name,[len(MESH[(name,l)].P)//3 for l in (0,1,2) if (name,l) in MESH])
LT=json.load(open(os.path.join(OUT,'atlas','atlas.json')))['tiles']
def props(src,t):
  n=LT[t];p={'rough':.8,'bump':1.0}
  if n in('leaf','pinecard','grass','imp_oak','imp_pine'):p.update(rough=.7,bump=.6)
  if n=='snow':p.update(rough=.6,bump=.4)
  return p
P=hipack.Packer([Image.open(os.path.join(OUT,'atlas','atlas.png'))],props)
for m in MESH.values():P.add(m)
print('slots',P.solve());TD=os.path.join(HI,'tex');P.paint(TD)
REG=[]
for (name,l),m in MESH.items():
  sfx=['','_lod1','_lod2'][l];res=[2048,1024,512][l];path=os.path.join(HI,name+sfx+'.glb')
  t=hipack.write_hi(path,name+sfx,[(name,P.remap(m),(0,0,0))],os.path.join(TD,str(res)),alpha=True,extras={'tier':['high','medium','low'][l],'units':'m'})
  REG.append({'file':f'hi/trees/{name}{sfx}.glb','tris':t,'tex':res})
json.dump(REG,open(os.path.join(HI,'index.json'),'w'),indent=1);print('done')
