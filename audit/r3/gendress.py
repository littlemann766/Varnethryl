import json,math,re,random
random.seed(20261024)
PK=2.8;K=1.7;CH=185
src=open('www/proto3d/buildings.js').read()
D=[(m[0],float(eval(m[1].replace('Math.PI','math.pi'))) if False else m) for m in []]
defs=[]
for m in re.finditer(r"\{ id: '(\w+)', f: [^,]+, cx: ([-\d.]+), cz: ([-\d.]+), rot: ([^,]+),",src):
  defs.append((m[1],float(m[2])*PK,float(m[3])*PK,eval(m[4].replace('Math.PI','math.pi'))))
S=json.load(open('audit/r3/bld_spec.json'))
rects=[]
for i,x,z,r in defs:
  s=S.get(i)
  if not s or not s.get('w'):continue
  w,d=s['w']*K,s['d']*K
  if abs(math.sin(r))>.5:w,d=d,w
  rects.append((i,x,z,w/2+2.5,d/2+(9 if True else 2)))  # +yard/door apron
rects.append(('fountain',0,0,20,20))
def blocked(x,z,pad=0):return any(abs(x-a)<hw+pad and abs(z-b)<hd+pad for _,a,b,hw,hd in rects)
T=[];DEC=[];R=[]
def add(L,f,x,z,ry=0,y=None,sc=1.0,rep='new'):L.append({'file':f,'position':[round(x,2),y if y is None else round(y,2),round(z,2)],'rotation':[0,round(ry,3),0],'scale':[sc,sc,sc],'replaces':rep})
# street edges: N-S street half width 4.25, E-W 3.4; plaza r=36.4
for axis,hw in (('ns',4.25),('ew',3.4)):
  for side in (-1,1):
    for k in range(int((CH-40)/2)):
      t=38+k*2+1
      for sg in (-1,1):
        x,z=(side*(hw+.25),sg*t) if axis=='ns' else (sg*t,side*(hw+.25))
        if blocked(x,z,-2.0):continue
        ry=(math.pi/2 if axis=='ns' else 0)+(0 if side<0 else math.pi)
        add(T,'dressing/cobble_edge_2m.glb' if (k//6)%2==0 else 'dressing/curb_2m.glb',x,z,ry,0.0)
        if k%8==3 and side==(1 if sg>0 else -1):lx,lz=(side*(hw+1.2),sg*t) if axis=='ns' else (sg*t,side*(hw+1.2));add(T,'dressing/lantern_post.glb',lx,lz,ry+math.pi/2,0.0)
for i in range(56):  # plaza rim curb
  a=i/56*6.283
  if min(abs(math.sin(a)),abs(math.cos(a)))*36.4<5.5:continue
  add(T,'dressing/curb_2m.glb',math.cos(a)*36.6,math.sin(a)*36.6,-a+math.pi/2,0.0)
for q,(a0) in enumerate((.6,2.2,3.75,5.35)):  # stalls, benches, planters per plaza quadrant
  for j in range(3):a=a0+(j-1)*.28;add(T,f"dressing/market_stall_{['red','blue','green'][(q+j)%3]}.glb",math.cos(a)*29,math.sin(a)*29,-a-math.pi/2,0.0)
  a=a0+.55;add(T,'dressing/bench.glb',math.cos(a)*33,math.sin(a)*33,-a-math.pi/2,0.0);a=a0-.55;add(T,'dressing/flower_planter.glb',math.cos(a)*33.5,math.sin(a)*33.5,-a-math.pi/2,0.0)
for x,z in ((7.5,40),(-7.5,40),(7.5,-40),(-7.5,-40),(40,6.5),(-40,6.5),(40,-6.5),(-40,-6.5)):add(T,'dressing/banner_pole_%s.glb'%('blue' if z<0 or x<0 else 'red'),x,z,0,0.0)
for x,z in ((7,172),(9,-48)):add(T,'dressing/signpost.glb',x,z,.3,0.0)
for x,z in ((18,110),(-18,-112),(-60,60)):
  if not blocked(x,z):add(T,'dressing/well.glb',x,z,random.uniform(0,6),0.0)
# wall inner faces: lanterns, rubble, decals
WI=CH-2.4
for side,(nx,nz) in (('n',(0,1)),('s',(0,-1)),('e',(-1,0)),('w',(1,0))):
  for k in range(-7,8):
    u=k*24+12
    if abs(u)<10:continue
    if side in 'ns':x,z=u,-WI if side=='n' else WI
    else:x,z=(WI if side=='e' else -WI),u
    ry=math.atan2(nx,nz)
    add(T,'dressing/wall_lantern.glb',x,z,ry,4.6)
    for j in range(2):
      v=u+random.uniform(-10,10);px,pz=(v,z) if side in 'ns' else (x,v)
      add(DEC,random.choice(['decals/decal_moss_wall.glb','decals/decal_grime_wall.glb','decals/decal_dirt_wall.glb']),px,pz,ry,0.0,round(random.uniform(1,1.6),2))
    if k%3==0:px,pz=(u+5,z+nz*1.5) if side in 'ns' else (x+nx*1.5,u+5);add(T,'dressing/rubble.glb',px,pz,random.uniform(0,6),0.0)
# street ground decals
for i in range(140):
  if random.random()<.5:x,z=random.uniform(-3.5,3.5),random.choice([-1,1])*random.uniform(40,178)
  else:x,z=random.choice([-1,1])*random.uniform(40,178),random.uniform(-2.8,2.8)
  add(DEC,random.choice(['decals/decal_dirt_ground.glb','decals/decal_crack_ground.glb','decals/decal_puddle.glb','decals/decal_leaves.glb','decals/decal_moss_ground.glb']),x,z,random.uniform(0,6.28),0.0,round(random.uniform(.8,1.5),2))
# building plinth decals (moss/soot at front corners)
for i,x,z,r in defs:
  s=S.get(i)
  if not s or not s.get('w'):continue
  w,d=s['w']*K/2,s['d']*K/2;fx,fz=math.sin(r),math.cos(r);rx,rz=math.cos(r),-math.sin(r)
  for sg in (-1,1):px=x+fx*(d+.5)+rx*sg*(w-1.2);pz=z+fz*(d+.5)+rz*sg*(w-1.2);add(DEC,'decals/decal_moss_ground.glb' if sg<0 else 'decals/decal_dirt_ground.glb',px,pz,r,0.02,1.0)
# outskirts roads: milestones + lanterns near town, signposts at ends
roads=re.findall(r"\{id:'([\w-]+)',points:\[(.*?)\]\],width",open('www/proto3d/townlands.js').read())
for rid,pts in roads:
  P=[tuple(map(float,p)) for p in re.findall(r"\[([-\d.]+),([-\d.]+)\]",'['+pts+']')]
  acc=0
  for (ax,az),(bx,bz) in zip(P,P[1:]):
    L=math.hypot(bx-ax,bz-az);ux,uz=(bx-ax)/L,(bz-az)/L;nx,nz=-uz,ux
    for s in range(0,int(L),4):
      acc+=4;x,z=ax+ux*s,az+uz*s
      if abs(x)<CH+4 and abs(z)<CH+4:continue
      if acc%80==0:add(R,'dressing/milestone.glb',x+nx*5.6,z+nz*5.6,math.atan2(ux,uz))
      if acc%40==0:add(R,random.choice(['decals/decal_dirt_ground.glb','decals/decal_leaves.glb']),x,z,random.uniform(0,6),None,1.6)
      if acc%120==60:add(R,'dressing/rubble.glb',x-nx*5.8,z-nz*5.8,random.uniform(0,6))
  x,z=P[1];add(R,'dressing/signpost.glb',x+4,z,0.3)
for n,L,note in (('dressing_town',T,'Town interior, world coords, y given (town ground is flat y=0).'),('decals',DEC,'Decals: town walls/streets/building fronts. Separate decal atlas material.'),('dressing_roads',R,'Outskirt roads (y:null = snap to townElevation).')):
  json.dump({'zone':n,'note':note,'items':L},open(f'www/proto3d/models/beth/PLACEMENT_{n}.json','w'),indent=0);print(n,len(L))
