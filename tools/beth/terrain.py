# Round-3 terrain + mountain pieces on the landscape atlas, each with _lod1 (and _lod2 for the big ones). Godot: import as-is; LOD files map to Low/Medium tiers.
import sys,os,json,math,numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import kit
from kit import M,write_glb,hexc as W,blob,cards
OUT=sys.argv[1];kit.OUT=OUT;kit.rng=np.random.default_rng(21);REG=[]
def emit(name,m,**ex):
  t=write_glb(m,os.path.join(OUT,'terrain',name+'.glb'),name,extras={'units':'m',**ex});mn,mx=m.bounds();REG.append({'file':f'terrain/{name}.glb','tris':t,'size':[round(float(v),1) for v in (np.array(mx)-np.array(mn))],**ex});print(name,t)
SN=W(0xf4f8ff);RK=W(0x5e5650);GR=W(0x6a9a4a)
def peak(seed,sub,h=38,r=26,snow=True):
  m=M();g=np.random.default_rng(seed)
  blob(m,'rock',r,scale=(1,h/r,1),sub=sub,jit=.22,t=(0,0,0),flat_bottom=0,col=RK,top=SN if snow else None,seed=seed,uvs=.25,colvar=.08)
  for i in range(3 if sub>1 else 1):a=g.uniform(0,6.28);blob(m,'rock',r*.55,scale=(1,.9*h/r,1),sub=max(sub-1,0),jit=.25,t=(math.cos(a)*r*.7,0,math.sin(a)*r*.7),flat_bottom=0,col=RK*.92,top=SN if snow else None,seed=seed+i+1,uvs=.25)
  if snow:blob(m,'snow',r*.36,scale=(1,.55,1),sub=max(sub-1,0),jit=.2,t=(0,h*.78,0),col=SN,seed=seed+9,uvs=.4)
  return m
def ridge(seed,sub,L=60,h=16):
  m=M();g=np.random.default_rng(seed)
  for i in range(5):x=(i-2)*L/5;blob(m,'rock',L/6,scale=(1.3,h/(L/6)*g.uniform(.7,1.1),.8),sub=sub,jit=.25,t=(x,0,g.uniform(-2,2)),flat_bottom=0,col=RK*g.uniform(.9,1.05),top=GR*.9,seed=seed+i,uvs=.3)
  return m
def scree(seed,sub):
  m=M();g=np.random.default_rng(seed)
  blob(m,'rock',6,scale=(1.6,.35,1),sub=sub,jit=.15,flat_bottom=0,col=RK*1.05,seed=seed,uvs=.6)
  for i in range(14 if sub else 6):blob(m,'rock',g.uniform(.3,.9),scale=(1,.7,1),sub=0,t=(g.uniform(-8,8),g.uniform(0,1.2),g.uniform(-4,4)),col=RK*g.uniform(.85,1.1),seed=seed+10+i)
  return m
def mound(seed,sub):
  m=M();blob(m,'grass',9,scale=(1.4,.32,1),sub=sub,jit=.12,flat_bottom=0,col=GR,seed=seed,uvs=.4,colvar=.05)
  if sub:blob(m,'rock',1.4,scale=(1,.7,1),sub=1,t=(3,1.2,1),col=RK,top=GR,seed=seed+1)
  return m
def arch(sub):
  m=M()
  for i in range(9):a=i/8*math.pi;blob(m,'rock',2.2,scale=(1,1,1.3),sub=sub,jit=.2,t=(math.cos(a)*7,math.sin(a)*7,0),col=RK,top=GR,seed=40+i,uvs=.5)
  return m
SET=[('mountain_peak_snow',lambda s:peak(1,s),(3,2,1)),('mountain_peak_bare',lambda s:peak(2,s,30,22,False),(3,2,1)),('volcano_cone_flank',lambda s:peak(3,s,24,30,False),(3,2,1)),
     ('cliff_ridge_60m',lambda s:ridge(4,s),(2,1,0)),('scree_slope',lambda s:scree(5,s),(1,0)),('grass_mound',lambda s:mound(6,s),(2,1)),('rock_arch',lambda s:arch(s),(1,0))]
for n,f,subs in SET:
  for li,s in enumerate(subs):emit(n+('' if li==0 else f'_lod{li}'),f(s),lod=li)
json.dump(REG,open(os.path.join(OUT,'terrain','terrain_index.json'),'w'),indent=1)
