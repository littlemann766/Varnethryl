import sys,os,json,math,numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from assets import *
OUT=sys.argv[1];os.makedirs(OUT,exist_ok=True);import kit;kit.OUT=OUT
REG=[]
def emit(name,m,cat,replaces='',extras=None):
  d=os.path.join(OUT,cat);os.makedirs(d,exist_ok=True)
  mn,mx=m.bounds();t=write_glb(m,os.path.join(d,name+'.glb'),name,extras)
  REG.append({'file':f'{cat}/{name}.glb','tris':t,'h':round(float(mx[1]),2),'w':round(float(max(mx[0]-mn[0],mx[2]-mn[2])),2),'cat':cat,'replaces':replaces})
  return m
def place(dst,m,x,z,ry=0,s=1,y=0):dst.merge(m,rot('y',ry),(x,y,z),s)
# trees + LODs
T={}
for nm,fn,kw,bb in [('oak_a',oak,dict(seed=1),('oak',5.6,4.6)),('oak_b',oak,dict(seed=2,pal='deep'),('oak',5.6,4.6)),('oak_autumn',oak,dict(seed=3,pal='autumn'),('oak',5.6,4.6)),
  ('oak_yellow',oak,dict(seed=10,pal='yellow'),('oak',5.6,4.6)),('oak_red',oak,dict(seed=11,pal='red'),('oak',5.6,4.6)),('pine_a',pine,dict(seed=4),('pine',7.4,4.0)),('pine_b',pine,dict(seed=5),('pine',7.4,4.0)),('birch_a',birch,dict(seed=6),('oak',5.6,3.2)),
  ('dead_a',dead,dict(seed=7),None),('pine_snow',pine,dict(seed=8,snowy=True),('pine',7.4,4.0)),('apple_blossom',oak,dict(seed=9,pal='blossom'),('oak',5.0,4.2))]:
  T[nm]=emit('tree_'+nm,fn(**kw),'trees','trees/'+nm.split('_')[0]+' (scenery.js) + main.js cone trees')
  T[nm+'_lod1']=emit('tree_'+nm+'_lod1',fn(**kw,lod=1),'trees')
  if bb:emit('tree_'+nm+'_bb',billboard(bb[0],bb[1],bb[2]),'trees')
# vegetation
V={}
V['bush_a']=emit('bush_a',bush(11),'veg','bushes/round,hedge');V['bush_b']=emit('bush_b',bush(12,'deep'),'veg','bushes/hedge')
V['grass_a']=emit('grass_a',grass(13),'veg','flowers/grass');V['grass_dry']=emit('grass_dry',grass(14,0xe0d080,.6),'veg','flowers/grass:dry')
for c,h in [('white',0xffffff),('yellow',0xf2cc2a),('purple',0x9c5fdf),('red',0xe8444a),('blue',0x5a84f0)]:
  V['flowers_'+c]=emit('flowers_'+c,flowers(15,h),'veg','flowers/daisy,tulip,lavender,bellflower')
# rocks
R={}
R['rock_small']=emit('rock_small',rock(21,.5),'rocks','rocks/stone,cluster');R['rock_mossy']=emit('rock_mossy',rock(22,.8,top=W(0x8ab070)),'rocks','rocks/stone:mossy')
R['boulder']=emit('boulder',rock(23,1.3,sub=2,top=W(0x9ab880)),'rocks','rocks/boulder');R['slab']=emit('rock_slab',rock(24,1.0,sq=(1.4,.3,1.1)),'rocks','rocks/slab')
R['standing']=emit('standing_stone',rock(25,.6,sq=(.7,2.2,.5)),'rocks','rocks/standing')
R['cliff_a']=emit('cliff_a',cliff(26),'rocks');R['cliff_b']=emit('cliff_b',cliff(27,col=0xd0c4b0),'rocks')
# props
P={}
P['fence']=emit('fence_2m',fence(),'props','props/fence');P['crate']=emit('crate',crate(),'props','props/crate');P['barrel']=emit('barrel',barrel(),'props','props/barrel')
P['cart']=emit('cart',cart(),'props');P['lamp']=emit('lamp_post',lamppost(),'props','props/lamp (glow strip removed; no emissive)')
# zone kits
Z={}
Z['ice_rock']=emit('ice_rock',rock(31,1.1,kind='ice',sq=(1,.9,.9),top=W(0xffffff)),'frost','townlands ice shards (MeshPhong emissive)')
Z['snow_rock']=emit('snow_rock',rock(32,1.0,top=W(0xf4f8ff)*1.0),'frost')
Z['basalt']=emit('basalt_columns',(lambda:(lambda m:[cyl(m,'basalt',.45,.45,np.random.default_rng(i).uniform(1.2,3.4),6,t=(math.cos(i*1.3)*(i%3)*.5,0,math.sin(i*1.3)*(i%3)*.5),cap=True) for i in range(7)] and m)(M()))(),'volcano','townlands volcano basalt cylinders')
Z['lava_rock']=emit('lavacrust_rock',rock(33,1.0,kind='lavacrust'),'volcano','townlands ember slabs (emissive)')
Z['dock']=emit('dock_10m',dock(),'port','harbor box piers');Z['ship']=emit('ship_cog',ship(),'port','(kept by Lucky: current curved-hull ship; offered as lighter alternative)')
Z['tent']=emit('hob_tent',tent(),'hobcamp');Z['palisade']=emit('hob_palisade',palisade(),'hobcamp');Z['firepit']=emit('hob_firepit',firepit(),'hobcamp')
Z['ruin_wall']=emit('ruin_wall',ruin_wall(41),'ruins');Z['ruin_arch']=emit('ruin_arch',ruin_arch(),'ruins');Z['path']=emit('path_stones',path_stones(42),'ruins')
# ---- merged clusters (1 draw each) ----
r=np.random.default_rng(99)
def scat(dst,pool,n,rad,smin=.8,smax=1.3,minr=0):
  for i in range(n):
    a=r.uniform(0,6.28);d=r.uniform(minr,rad);place(dst,pool[int(r.integers(len(pool)))],math.cos(a)*d,math.sin(a)*d,r.uniform(0,6.28),r.uniform(smin,smax))
C={}
def cl(name,build,note):
  m=M();build(m);emit(name,m,'clusters','(new: fills empty land; merged into the chunk batch so it adds no draw call)',extras={'note':note})
cl('cluster_grove_mixed',lambda m:(scat(m,[T['oak_a'],T['oak_b'],T['birch_a']],5,7,minr=1),scat(m,[V['bush_a'],V['bush_b']],5,8),scat(m,[V['grass_a'],V['flowers_white'],V['flowers_yellow']],14,9)),'15 m grove')
cl('cluster_pine_stand',lambda m:(scat(m,[T['pine_a'],T['pine_b']],6,8,.9,1.4,1),scat(m,[R['rock_small'],R['rock_mossy']],4,8),scat(m,[V['grass_a']],10,9)),'pine stand')
cl('cluster_meadow',lambda m:scat(m,[V['grass_a'],V['grass_a'],V['flowers_purple'],V['flowers_red'],V['flowers_blue'],V['flowers_yellow']],26,7),'flower meadow 14 m')
cl('cluster_outcrop_a',lambda m:(place(m,R['cliff_a'],0,0),scat(m,[R['boulder'],R['rock_small'],R['slab']],6,6,minr=3),scat(m,[V['grass_a'],V['bush_a']],8,7,minr=2)),'rock outcrop 6 m high')
cl('cluster_outcrop_b',lambda m:(place(m,R['cliff_b'],0,0,1.2),place(m,R['standing'],4,2),scat(m,[R['rock_small'],R['rock_mossy']],6,6,minr=3),place(m,T['dead_a'],-3,3)),'tan outcrop + standing stone')
cl('cluster_ruins',lambda m:(place(m,Z['ruin_wall'],0,0),place(m,Z['ruin_arch'],5,1.5,.3),place(m,Z['ruin_wall'],-3,4,1.7,.8),place(m,Z['path'],5,7.5,.3),scat(m,[V['grass_a'],V['bush_b']],10,8)),'ruined wall + walk-through arch (1.6 m x 3.4 m)')
cl('cluster_roadside',lambda m:(place(m,P['cart'],0,0,.4),place(m,P['barrel'],1.6,.8),place(m,P['crate'],1.4,-.6,.3),place(m,P['crate'],1.5,-.6,1.0,.8,.9),[place(m,P['fence'],-2.2+i*2.15,-2.2) for i in range(3)],scat(m,[V['grass_a'],V['grass_dry']],6,4)),'cart + crates + fence run')
cl('cluster_frost',lambda m:(scat(m,[T['pine_snow']],5,8,.9,1.4,1),scat(m,[Z['ice_rock'],Z['snow_rock']],6,8)),'Frostreach snowy pines + ice rocks')
cl('cluster_volcano',lambda m:(place(m,Z['basalt'],0,0),scat(m,[Z['lava_rock'],Z['basalt']],6,7,.6,1.4,2),place(m,T['dead_a'],4,-3,0,1,0)),'basalt + lava-crust (albedo only)')
cl('cluster_hobcamp',lambda m:(place(m,Z['tent'],-2.5,0),place(m,Z['tent'],2.5,-1,1,1.1),place(m,Z['firepit'],0,2.5),[place(m,Z['palisade'],math.cos(a)*7,math.sin(a)*7,-a+1.57) for a in np.linspace(.3,5.4,10)],place(m,P['crate'],3,3),place(m,P['barrel'],-3.5,3)),'hob camp: 2 tents, fire pit, palisade ring (gap facing +x)')
cl('cluster_port_dock',lambda m:(place(m,Z['dock'],0,0),place(m,Z['dock'],0,10),place(m,P['barrel'],1,3,0,1,1.04),place(m,P['crate'],-1,6,0,1,1.04),place(m,P['lamp'],1.7,9,0,1,1.04)),'20 m pier, deck at y=1.04')
json.dump(REG,open(os.path.join(OUT,'kit_index.json'),'w'),indent=1)
for e in REG:print(f"{e['file']:42s} {e['tris']:6d} tris  h={e['h']}")
