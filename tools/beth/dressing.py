# Round-3 road/wall/town dressing on the BUILDING atlas (one material) + decal quads on the decal atlas.
import sys,os,json,math,numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import kit
from kit import M,rot,write_glb,hexc as W,blob
from bldgeo import rect,obox
OUT=sys.argv[1];kit.OUT=OUT;kit.rng=np.random.default_rng(11);WH=np.ones(3)
BT=json.load(open(os.path.join(OUT,'buildings','atlas','atlas.json')))['tiles'];DT=json.load(open(os.path.join(OUT,'decals','atlas','atlas.json')))['tiles']
REG=[]
def emit(name,m,atlas='buildings/atlas',mat='beth_building_atlas',kind='dressing',**ex):
  kit.BTILES=BT if atlas.startswith('buildings') else DT
  t=write_glb(m,os.path.join(OUT,kind,name+'.glb'),name,extras={'units':'m',**ex},atlas=atlas,mat_name=mat);REG.append({'file':f'{kind}/{name}.glb','tris':t,'atlas':atlas,**ex});print(name,t)
kit.BTILES=BT
def curb(L=2.0):
  m=M()
  for i in range(4):obox(m,(-L/2+(i+.5)*L/4,0,0),(L/4-.04,.22,.34),'b_darkstone',WH*(.92+.04*(i%3)),faces=('front','back','left','right','top'))
  return m
def cobble_edge(L=2.0):
  m=M();rect(m,np.array([-L/2,.03,.6]),np.array([1.,0,0]),np.array([0,0,-1.]),L,.6,'b_cobble',WH*.95,(1.2,1.2))
  for i in range(5):obox(m,(-L/2+(i+.5)*L/5,0,.62),(L/5-.06,.12,.16),'b_stone',WH,faces=('front','back','left','right','top'))
  return m
def lantern_post():
  m=M();kit.cyl(m,'b_darkstone',.32,.3,.35,8,cap=True);kit.cyl(m,'b_iron',.07,.06,3.2,6,t=(0,.35,0))
  obox(m,(.3,3.3,0),(.7,.06,.06),'b_iron',WH);obox(m,(.55,2.75,0),(.32,.44,.32),'b_glass',W(0xfff0c0));kit.cyl(m,'b_iron',.24,.02,.3,4,t=(.55,3.2,0));return m
def wall_lantern():
  m=M();obox(m,(0,0,.18),(.06,.06,.36),'b_iron',WH);obox(m,(0,-.38,.36),(.24,.36,.24),'b_glass',W(0xfff0c0));obox(m,(0,-.04,.36),(.3,.06,.3),'b_iron',WH);obox(m,(0,0,0),(.2,.2,.04),'b_iron',WH);return m
def signpost():
  m=M();kit.cyl(m,'b_timber',.09,.08,2.6,6)
  for i,(y,a) in enumerate(((2.2,.4),(1.8,-.7),(1.45,2.0))):sub=M();obox(sub,(.55,0,0),(1.1,.26,.05),'b_planks',WH*1.1);obox(sub,(1.15,0,0),(.12,.18,.05),'b_planks',WH*1.1);m.merge(sub,rot('y',a),(0,y,0))
  return m
def milestone():m=M();blob(m,'b_stone',.4,scale=(.8,1.6,.5),sub=1,col=WH,uvs=1.0);return m
def well():
  m=M();kit.cyl(m,'b_stone',1.2,1.2,.9,14,cap=False);kit.cyl(m,'b_darkstone',1.3,1.3,.12,14,t=(0,.9,0),cap=True)
  rect(m,np.array([-1,.6,1.0]),np.array([1.,0,0]),np.array([0,0,-1.]),2,2,'b_glass',W(0x305068),(2,2))
  for s in (-1,1):obox(m,(s*1.05,.9,0),(.16,2.0,.16),'b_timber',WH)
  obox(m,(0,2.9,0),(2.4,.14,.14),'b_timber',WH);kit.cyl(m,'b_planks',.22,.22,.5,8,R=rot('z',math.pi/2),t=(-.25,2.6,0))
  from bldgeo import gable;gable(m,0,0,2.8,1.6,3.0,.6,.15,'x','b_shingle',WH,gtile='b_timber',gcol=WH,cap_tile='b_timber')
  kit.cyl(m,'b_planks',.22,.25,.4,8,t=(.5,0,1.5),cap=True);return m
def stall(col=0xb03030):
  m=M();obox(m,(0,.85,0),(2.8,.1,1.2),'b_planks',WH);obox(m,(0,.4,.55),(2.8,.8,.06),'b_planks',WH*.85)
  for sx in (-1,1):
    for sz in (-1,1):obox(m,(sx*1.35,0,sz*.55),(.1,2.3 if sz<0 else 2.0,.1),'b_timber',WH)
  for i in range(6):
    sub=M();rect(sub,np.array([-1.6+i*.533,0,0]),np.array([1.,0,0]),np.array([0,0,1.]),.533,1.6,'b_white' if i%2 else 'b_red',W(col)*1.5 if not i%2 else WH,(.53,1.6));m.merge(sub,rot('x',-.3),(0,2.3,-.75))
  for i in range(5):kit.cyl(m,'b_planks',.17,.17,.22,8,t=(-1.1+i*.55,.95,-.1),cap=True,col=W([0xc04030,0x50a040,0xe0b040,0xa06030,0x80a040][i])*1.4)
  obox(m,(.9,.95,.25),(.6,.3,.4),'b_planks',WH);return m
def banner_pole(col=0x2040a0):
  m=M();kit.cyl(m,'b_timber',.08,.07,5.0,6);kit.cyl(m,'b_iron',.12,.01,.3,5,t=(0,5.0,0));obox(m,(.6,4.7,0),(1.3,.06,.06),'b_iron',WH)
  rect(m,np.array([0,2.5,0]),np.array([1.,0,0]),np.array([0,1.,0]),1.2,2.2,'b_white',W(col)*1.1,(1.2,2.2));return m
def wall_cap(L=4.0):
  m=M();obox(m,(0,0,0),(L,.25,1.0),'b_darkstone',WH,faces=('front','back','left','right','top'));obox(m,(0,.25,0),(L*.98,.12,.7),'b_stone',WH*1.05,faces=('front','back','left','right','top'));return m
def rubble():
  m=M();r=np.random.default_rng(4)
  for i in range(6):blob(m,'b_stone',r.uniform(.15,.35),scale=(1,.6,1),sub=0,t=(r.uniform(-.8,.8),0,r.uniform(-.4,.4)),col=WH,uvs=1.0,seed=int(r.integers(1e6)))
  return m
def bench():
  m=M();obox(m,(0,.45,0),(1.8,.08,.45),'b_planks',WH)
  for s in (-1,1):obox(m,(s*.75,0,0),(.12,.45,.4),'b_stone',WH)
  return m
def flower_planter():
  m=M();obox(m,(0,0,0),(1.4,.45,.5),'b_planks',WH*.9)
  for i in range(6):blob(m,'b_thatch',.2,scale=(1,.8,1),sub=0,t=(-.55+i*.22,.45,0),col=W([0xd04060,0xe0c040,0x6080e0][i%3])*1.3,uvs=.5)
  return m
for n,f in (('curb_2m',curb),('cobble_edge_2m',cobble_edge),('lantern_post',lantern_post),('wall_lantern',wall_lantern),('signpost',signpost),('milestone',milestone),('well',well),
  ('market_stall_red',lambda:stall(0xb03030)),('market_stall_blue',lambda:stall(0x3050b0)),('market_stall_green',lambda:stall(0x3a8a3a)),('banner_pole_blue',lambda:banner_pole(0x2040a0)),('banner_pole_red',lambda:banner_pole(0x902020)),
  ('wall_cap_4m',wall_cap),('rubble',rubble),('bench',bench),('flower_planter',flower_planter)):emit(n,f())
# decals: quads with a little lift; 'ground' lie flat (+y), 'wall' stand on +z face
kit.BTILES=DT
for n,t,sz,mode in (('decal_moss_wall','d_moss2',(2.4,1.6),'wall'),('decal_moss_ground','d_moss',(2.2,2.2),'ground'),('decal_crack_wall','d_crack',(1.6,1.6),'wall'),('decal_crack_ground','d_crack2',(1.8,1.8),'ground'),
  ('decal_dirt_ground','d_dirt',(2.6,2.6),'ground'),('decal_dirt_wall','d_dirt2',(2.6,1.4),'wall'),('decal_grime_wall','d_grime',(2.0,2.4),'wall'),('decal_leaves','d_leaves',(2.0,2.0),'ground'),('decal_puddle','d_puddle',(2.0,1.4),'ground'),('decal_soot_wall','d_soot',(1.4,2.2),'wall')):
  m=M();w,h=sz
  if mode=='ground':rect(m,np.array([-w/2,.025,h/2]),np.array([1.,0,0]),np.array([0,0,-1.]),w,h,t,WH,(w,h),jit=0)
  else:rect(m,np.array([-w/2,0,.03]),np.array([1.,0,0]),np.array([0,1.,0]),w,h,t,WH,(w,h),jit=0)
  emit(n,m,atlas='decals/atlas',mat='beth_decal_atlas',kind='decals',mode=mode)
json.dump(REG,open(os.path.join(OUT,'dressing','dressing_index.json'),'w'),indent=1)
