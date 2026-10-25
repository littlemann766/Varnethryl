# Detailed building exteriors (Beth). Authored in the building ROOT-LOCAL frame measured from bldview (walls bbox, door on +z,
# x=0, DW x DH), then scaled by K=1.7 so the GLB is in metres. Nodes: 'walls' (shell+trim), 'roof' (hide when inside), windmill 'blades'.
import sys,os,json,math,numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import kit
from kit import M,rot,write_glb,hexc as W,blob
from bldgeo import face,rect,obox,wall,gable,ring_wall
OUT=sys.argv[1];kit.OUT=OUT;BD=os.path.join(OUT,'buildings');kit.BTILES=json.load(open(os.path.join(BD,'atlas','atlas.json')))['tiles']
K=1.7;DH=1.95;WH=np.ones(3)
rng=np.random.default_rng(5);kit.rng=rng
def window(m,x,y,z,yaw,w=.9,h=1.1,shutters=False,bars=False,frame='b_timber'):
  R=rot('y',yaw);n=R@np.array([0,0,1.]);u=R@np.array([1.,0,0]);c=np.array([x,y,z])
  rect(m,c-u*w/2+n*.02,u,np.array([0,1.,0]),w,h,'b_window',WH,(w,h))
  for dy,hh in ((-.08,.1),(h,.12)):obox(m,c+np.array([0,dy,0])+n*.06,(w+.3,hh,.14),'b_darkstone' if frame=='stone' else frame,WH,yaw=yaw)
  for s in (-1,1):obox(m,c+u*s*(w/2+.04)+n*.05,(.08,h,.1),frame if frame!='stone' else 'b_darkstone',WH,yaw=yaw)
  if shutters:
    for s in (-1,1):rect(m,c+u*s*(w/2+.12)+(u*(0 if s>0 else -.5))+n*.07,u,np.array([0,1.,0]),.5,h,'b_door',W(0x6a8a6a)*1.2,(.5,h))
  if bars:
    for i in range(1,4):obox(m,c+u*(-w/2+i*w/4)+n*.08,(.04,h,.04),'b_iron',WH,yaw=yaw)
def door_surround(m,z,DW,tile='b_darkstone',steps=True,lantern=True,sign=None):
  for s in (-1,1):obox(m,(s*(DW/2+.16),0,z+.08),(.32,DH+.05,.36),tile,WH)
  obox(m,(0,DH,z+.1),(DW+.7,.32,.4),tile,WH);obox(m,(0,DH+.3,z+.14),(.32,.3,.3),tile,WH*1.05)
  if steps:
    obox(m,(0,0,z+.55),(DW+.9,.14,.9),'b_darkstone',WH*1.05);obox(m,(0,0,z+1.25),(DW+1.2,.07,.7),'b_stone',WH)
  if lantern:
    obox(m,(DW/2+.75,DH-.2,z+.18),(.06,.06,.36),'b_iron',WH);obox(m,(DW/2+.75,DH-.62,z+.36),(.24,.36,.24),'b_glass',WH);obox(m,(DW/2+.75,DH-.26,z+.36),(.3,.06,.3),'b_iron',WH)
  if sign:
    obox(m,(-DW/2-1.0,DH+.15,z+.45),(.06,.06,.9),'b_iron',WH);rect(m,np.array([-DW/2-1.0,DH-.55,z+.72]),np.array([0,0,1.]),np.array([0,1.,0]),.0001+.0,.0,'b_planks',WH) if False else obox(m,(-DW/2-1.0,DH-.6,z+.75),(.06,.6,.8),'b_planks',W(sign))
def windows_on(m,w,d,y,door_side=True,skip_door=1.6,**kw):
  out=[]
  for (L,fn) in ((w,lambda u:(u,d/2,0)),(w,lambda u:(-u,-d/2,math.pi)),(d,lambda u:(w/2,-u,math.pi/2)),(d,lambda u:(-w/2,u,-math.pi/2))):
    n=max(1,int((L-1.2)//2.6))
    for i in range(n):
      u=(i+.5)*L/n-L/2;x,z,yw=fn(u)
      if yw==0 and abs(u)<skip_door:continue
      window(m,x,y,z,yw,**kw);out.append((x,z,yw))
  return out
def timber_frame(m,w,d,y0,y1,tile='b_timber',col=WH,brace=True):
  for (L,o,yw) in ((w,(0,d/2),0),(w,(0,-d/2),math.pi),(d,(w/2,0),math.pi/2),(d,(-w/2,0),-math.pi/2)):
    R=rot('y',yw);n=R@np.array([0,0,1.]);u=R@np.array([1.,0,0]);c=np.array([o[0],0,o[1]])+n*.04
    for yy in (y0,(y0+y1)/2,y1-.18):obox(m,c+np.array([0,yy,0]),(L+.1,.18,.12),tile,col,yaw=yw)
    n_p=max(2,int(L//1.3))
    for i in range(n_p+1):obox(m,c+u*(-L/2+i*L/n_p)+np.array([0,y0,0]),(.16,y1-y0,.12),tile,col,yaw=yw)
    if brace:
      for i in range(0,n_p,2):
        a=c+u*(-L/2+i*L/n_p)+np.array([0,y0+.1,0]);b=c+u*(-L/2+(i+1)*L/n_p)+np.array([0,(y0+y1)/2,0]);mid=(a+b)/2;ln=np.linalg.norm(b-a)
        ang=math.atan2((b-a)[1],L/n_p);sub=M();obox(sub,(0,-.07,0),(ln,.14,.1),tile,col);m.merge(sub,R@rot('z',ang),mid+np.array([0,0,0]))
def quoins(m,w,d,y1,tile='b_stone'):
  for sx in (-1,1):
    for sz in (-1,1):
      for i in range(int(y1/.55)):
        big=i%2;obox(m,(sx*(w/2+.02)-sx*(.3 if big else .2),i*.55,sz*(d/2+.02)-sz*(.2 if big else .3)),(.62 if big else .42,.5,.42 if big else .62),tile,WH*1.06)
def chimney(m,x,z,y0,y1,tile='b_stone'):
  obox(m,(x,y0,z),(.9,y1-y0,.9),tile,WH);obox(m,(x,y1,z),(1.1,.22,1.1),'b_darkstone',WH)
  for s in (-1,1):kit.cyl(m,'b_darkstone',.12,.12,.4,6,t=(x+s*.2,y1+.22,z))
def house_like(name,w,d,h,hs,ridge,rise,roof_tile='b_slate',lower='b_stone',upper='b_plaster',DW=2.2,frame=True,frame_tile='b_timber',
               chimneys=((.28,-.22),),dormer=False,porch=False,yard=None,balcony=False,sign=None,bars=False,shutters=True,quo=True,lowcol=WH,upcol=WH,thatch=False):
  walls=M();roof=M();T=.45;hw,hd=w/2,d/2
  if rise is None:rise=.7*(hw if ridge=='z' else hd)
  ops=[(hw,DW,0,DH)]
  # front wall A->B so outer face is +z
  wall(walls,(-hw,hd),(hw,hd),0,hs,T,lower,lowcol,ops);wall(walls,(-hw,hd),(hw,hd),hs,h,T,upper,upcol)
  for A,B in (((hw,-hd),(-hw,-hd)),((hw,hd),(hw,-hd)),((-hw,-hd),(-hw,hd))):
    wall(walls,A,B,0,hs,T,lower,lowcol);wall(walls,A,B,hs,h,T,upper,upcol)
  obox(walls,(0,0,0),(w+.24,.42,d+.24),'b_darkstone',WH,faces=('front','back','left','right','top'))   # plinth
  obox(walls,(0,hs-.1,0),(w+.3,.22,d+.3),'b_timber',WH,faces=('front','back','left','right','top','bottom'))  # jetty beam
  if quo and lower=='b_stone':quoins(walls,w,d,hs)
  if frame:timber_frame(walls,w,d,hs+.1,h,frame_tile)
  windows_on(walls,w,d,.9,skip_door=DW/2+1.4,shutters=shutters,bars=bars,frame='stone' if lower in('b_stone','b_darkstone') else 'b_timber')
  for (x,z,yw) in windows_on(walls,w,d,hs+.8,skip_door=0.6,frame='b_timber',bars=bars):
    R=rot('y',yw);n=R@np.array([0,0,1.]);obox(walls,np.array([x,hs+.55,z])+n*.2,(1.1,.25,.3),'b_planks',WH*.9,yaw=yw)  # flower box
    rect(walls,np.array([x,hs+.8,z])+n*.3-R@np.array([.55,0,0]),R@np.array([1.,0,0]),np.array([0,1.,0]),1.1,.0001,'b_planks',WH) if False else None
  door_surround(walls,hd,DW,sign=sign)
  if yard:rect(walls,np.array([-yard[0],.02,yard[2]]),np.array([1.,0,0]),np.array([0,0,-1.]),2*yard[0],yard[2]-yard[1],'b_cobble',WH*.95,(1.4,1.4))
  for bx_ in ((DW/2+1.4,hd+.7),(DW/2+2.1,hd+.6)):kit.cyl(walls,'b_planks',.36,.4,.95,10,t=(bx_[0],0,bx_[1]),cap=True);kit.cyl(walls,'b_iron',.41,.41,.06,10,t=(bx_[0],.5,bx_[1]))
  if balcony:
    bz=hd;obox(walls,(-hw*.45,hs,bz+.7),(hw*.8,.12,1.4),'b_planks',WH)
    for i in range(7):obox(walls,(-hw*.85+i*hw*.8/6,hs+.12,bz+1.35),(.08,.9,.08),'b_timber',WH)
    obox(walls,(-hw*.45,hs+1.0,bz+1.35),(hw*.82,.1,.12),'b_timber',WH)
    for s2 in (-1,1):sub=M();obox(sub,(0,-.06,0),(1.3,.12,.12),'b_timber',WH);walls.merge(sub,rot('x',-.8),(-hw*.45+s2*hw*.35,hs-.45,bz+.45))
  over=.7
  gable(roof,0,0,w,d,h,rise,over,ridge,roof_tile,W(0xb8c4ec) if roof_tile=='b_slate' else WH,gtile=upper,gcol=upcol,cap_tile='b_darkstone' if not thatch else 'b_thatch')
  if frame:  # gable-end half-timbering
    span=w if ridge=='z' else d
    for sg in (-1,1):
      R=rot('y',0 if ridge=='z' else math.pi/2);off=R@np.array([0,0,sg*((d if ridge=='z' else w)/2+.05)])
      for yy,f in ((h+.05,1.0),(h+rise*.45,.55)):sub=M();obox(sub,(0,0,0),(span*f,.16,.12),frame_tile,WH);roof.merge(sub,R,off+np.array([0,yy,0]))
      sub=M();obox(sub,(0,0,0),(.16,rise*.92,.12),frame_tile,WH);roof.merge(sub,R,off+np.array([0,h,0]))
      for s3 in (-1,1):
        sub=M();ln=math.hypot(span*.27,rise*.45);obox(sub,(0,-.07,0),(ln,.14,.1),frame_tile,WH);roof.merge(sub,R@rot('z',s3*math.atan2(rise*.45,span*.27)),off+np.array([s3*span*.135,h+rise*.225,0]))
  if thatch:  # thick thatch eave roll
    L=(d if ridge=='z' else w)+2*over
    for s in (-1,1):
      if ridge=='z':obox(roof,(s*(w/2+over-.1),h-over*rise/(w/2)-.35,0),(.5,.45,L),'b_thatch',WH)
      else:obox(roof,(0,h-over*rise/(d/2)-.35,s*(d/2+over-.1)),(L,.45,.5),'b_thatch',WH)
  for (fx,fz) in chimneys:chimney(roof,fx*w,fz*d,h-1.0,h+rise+.6)
  if dormer:
    zf=hd*.35 if ridge=='x' else 0;x0=0
    if ridge=='x':
      y=h+rise*.25;obox(roof,(x0,y,hd*.35),(1.8,1.4,2.0),upper,upcol);window(roof,x0,y+.25,hd*.35+1.0,0,.8,.8);gable(roof,x0,hd*.35,1.8,2.0,y+1.4,.8,.2,'z',roof_tile,WH,gtile=upper,gcol=upcol)
  if porch:
    pz=hd+1.6
    for s in (-1,1):kit.cyl(walls,'b_timber',.14,.14,hs-.1,6,t=(s*(DW/2+1.4),0,pz))
    sub=M();gable(sub,0,0,DW+3.6,2.0,hs-.1,.7,.2,'x',roof_tile,WH,gtile='b_timber',gcol=WH,cap_tile='b_timber' if not thatch else 'b_thatch');roof.merge(sub,np.eye(3),(0,0,hd+1.0))
  return walls,roof
def scaleK(m):o=M();o.merge(m,np.eye(3),(0,0,0),K);return o
def emit(name,nodes,meta):
  path=os.path.join(BD,name+'.glb');ns=[(nn,scaleK(mm),tuple(np.asarray(tr)*K)) for nn,mm,tr in nodes]
  t=write_glb(None,path,name,extras=meta,atlas='buildings/atlas',nodes=ns,mat_name='beth_building_atlas')
  REG.append({'file':'buildings/'+name+'.glb','tris':t,'nodes':[n[0] for n in nodes],**meta});print(name,t)
REG=[]
SPEC=json.load(open(sys.argv[2]))
def meta(id_):s=SPEC[id_];return {'id':id_,'units':'metres (root-local x K=1.7)','K':K,'door':{'center_local':[0,0,round(s['d']/2,3)] if s.get('d') else None,'w_m':round((s.get('DW') or 2.2)*K,2),'h_m':round(DH*K,2)}}
HS={'house1':(5.6,2.6,'z',None,'b_slate'),'house2':(5.8,2.7,'x',None,'b_slate'),'house3':(5.4,2.5,'z',None,'b_slate'),'house4':(6.0,2.8,'x',None,'b_slate')}
for hid,(h,hs,ridge,rise,rt) in HS.items():
  s=SPEC[hid];n=int(hid[-1])-1
  w_,r_=house_like(hid,s['w'],s['d'],h,hs,ridge,rise,rt,dormer=n%2==1,sign=0xa04030 if n==1 else None,chimneys=((.28,-.22),),yard=(s['w']/2+1.45,-s['d']/2-1.7,s['d']/2+3.7),balcony=n in(0,2))
  emit('bld_'+hid,[('walls',w_,(0,0,0)),('roof',r_,(0,0,0))],meta(hid))
s=SPEC['farmhouse'];w_,r_=house_like('farmhouse',s['w'],s['d'],5.4,2.5,'x',None,'b_thatch',porch=True,thatch=True,chimneys=((.3,-.2),(-.32,-.2)));emit('bld_farmhouse',[('walls',w_,(0,0,0)),('roof',r_,(0,0,0))],meta('farmhouse'))
s=SPEC['thieves'];w_,r_=house_like('thieves',s['w'],s['d'],6.2,2.9,'x',None,'b_slate',lower='b_darkstone',upper='b_planks',frame_tile='b_timber',bars=True,shutters=False,sign=0x403040,quo=False,upcol=W(0x9a8a80),chimneys=((-.3,-.25),))
emit('bld_thieves',[('walls',w_,(0,0,0)),('roof',r_,(0,0,0))],meta('thieves'))
# barn: red planks, white corner boards and X-braced doors, shingle roof, cupola
s=SPEC['barn'];w_,r_=house_like('barn',s['w'],s['d'],4.8,1.0,'z',4.6,'b_shingle',lower='b_darkstone',upper='b_redplanks',frame=False,shutters=False,quo=False,chimneys=())
hw,hd=s['w']/2,s['d']/2
for sx in (-1,1):
  for sz in (-1,1):obox(w_,(sx*(hw-.08),0,sz*(hd-.08)),(.34,4.8,.34),'b_white',WH)
for s_ in (-1,1):
  sub=M();obox(sub,(0,-.08,0),(math.hypot(1.1,1.95)*1.0,.16,.1),'b_white',WH);w_.merge(sub,rot('z',s_*math.atan2(1.95,1.1)),(s_*(1.1+.0)*-1+s_*0+(-s_*0.0)+s_*0.0+(-1.1*s_)+1.1*s_+(1.1+.16)*(-1 if s_>0 else 1)*-1*0+(-(2.2/2+.9)*(-1)**(s_>0)*0)+(s_*(2.2/2+.9))*1,DH/2,hd+.12))
obox(w_,(0,3.0,hd+.05),(2.0,1.5,.08),'b_door',W(0xc05040));obox(w_,(0,4.6,hd+.3),(.2,.2,1.0),'b_timber',WH)
obox(r_,(0,4.8+4.6-.1,0),(1.2,1.0,1.2),'b_white',WH);sub=M();gable(sub,0,0,1.2,1.2,4.8+4.6+.9,.7,.15,'z','b_shingle',WH,gtile='b_white',gcol=WH);r_.merge(sub,np.eye(3),(0,0,0))
emit('bld_barn',[('walls',w_,(0,0,0)),('roof',r_,(0,0,0))],meta('barn'))
# stables: stone sill, planks, stall half-doors, shingle roof
s=SPEC['stables'];w_,r_=house_like('stables',s['w'],s['d'],4.6,1.1,'x',None,'b_shingle',lower='b_stone',upper='b_planks',frame=True,shutters=False,chimneys=())
for i,x in enumerate(np.linspace(-s['w']/2+1.6,s['w']/2-1.6,6)):
  if abs(x)<2.4:continue
  rect(w_,np.array([x-.75,.45,s['d']/2+.05]),np.array([1.,0,0]),np.array([0,1.,0]),1.5,1.6,'b_door',WH,(1.5,1.6));obox(w_,(x,2.05,s['d']/2+.12),(1.7,.12,.2),'b_timber',WH)
emit('bld_stables',[('walls',w_,(0,0,0)),('roof',r_,(0,0,0))],meta('stables'))
# windmill
R=5.2;H=5.4;wm=M();rf=M()
ring_wall(wm,R+.14,0,H,.55,16,'b_stone',WH,door=(2.0,DH))
ring_wall(wm,R-.25,H,H+4.6,.5,14,'b_plaster',WH,taper=.5)
for i in range(16):a=i/16*6.283;obox(wm,(math.sin(a)*(R+.2),H-.1,math.cos(a)*(R+.2)),(2.1,.26,.3),'b_timber',WH,yaw=a)
for i in range(3):a=i*2.1+.4;window(wm,math.sin(a)*(R-.55),H+2.2,math.cos(a)*(R-.55),a,.7,.9)
for i in range(2):a=i*3.14+1.6;window(wm,math.sin(a)*(R+.15),1.2,math.cos(a)*(R+.15),a,.6,.8,frame='stone')
door_surround(wm,R+.1,2.0,sign=None)
kit.cyl(rf,'b_slate',R-.6,0.01,3.0,16,t=(0,H+4.6,0));kit.cyl(rf,'b_timber',R-.4,R-.4,.2,16,t=(0,H+4.5,0));kit.cyl(rf,'b_iron',.06,.06,1.2,5,t=(0,H+7.5,0))
bl=M();kit.cyl(bl,'b_timber',.35,.35,.7,8,R=rot('x',math.pi/2),t=(0,0,-.1));kit.cyl(bl,'b_iron',.18,.18,1.2,6,R=rot('x',math.pi/2),t=(0,0,-1.0))
for k_ in range(4):
  a=k_*math.pi/2+.35;Ra=rot('z',a);arm=M();obox(arm,(0,0,0),(.2,8.2,.18),'b_timber',WH)
  rect(arm,np.array([.15,2.3,.1]),np.array([1.,0,0]),np.array([0,1.,0]),1.4,5.6,'b_white',W(0xe6dcc0),(1.4,1.4))
  for q in range(8):obox(arm,(.85,2.3+q*.78,.12),(1.5,.06,.06),'b_timber',WH)
  obox(arm,(1.55,2.3,.1),(.08,5.6,.08),'b_timber',WH);bl.merge(arm,Ra,(0,0,0))
emit('bld_windmill',[('walls',wm,(0,0,0)),('roof',rf,(0,0,0)),('blades',bl,(0,H+3.4,R+.6))],{**meta('windmill'),'blades':'node "blades": rotate about its local Z (origin = hub)'})
# lighthouse
R=5.2;H=12;lw=M();lr=M()
for b in range(6):
  y0,y1=b*2,b*2+2;ring_wall(lw,R+.1,y0,y1,.55,18,'b_red' if b%2 else 'b_white',WH,door=(1.9,DH) if b==0 else None)
for y in (4.2,8):kit.cyl(lw,'b_darkstone',R+.25,R+.25,.4,18,t=(0,y,0),cap=False)
kit.cyl(lw,'b_darkstone',R+.7,R+.7,.35,18,t=(0,H,0),cap=True)
for i in range(24):a=i/24*6.283;kit.cyl(lw,'b_iron',.05,.05,1.0,4,t=(math.sin(a)*(R+.6),H+.35,math.cos(a)*(R+.6)))
kit.cyl(lw,'b_iron',R+.6,R+.6,.06,24,t=(0,H+1.3,0))
kit.cyl(lr,'b_glass',1.5,1.5,2.2,12,t=(0,H+.35,0));kit.cyl(lr,'b_iron',1.62,1.62,.2,12,t=(0,H+2.55,0),cap=True)
kit.cyl(lr,'b_slate',1.9,.05,1.8,12,t=(0,H+2.7,0));kit.cyl(lr,'b_iron',.1,.02,.8,6,t=(0,H+4.4,0))
for y in (3,6,9):a=y*.7;window(lw,math.sin(a)*(R+.12),y,math.cos(a)*(R+.12),a,.5,1.0,frame='stone')
door_surround(lw,R+.05,1.9,lantern=False)
for i in range(9):
  a=i*.9+2.2;s_=1.5+(i%3)*.8;blob(lw,'b_darkstone',s_,scale=(1,.8,1),sub=1,t=(math.sin(a)*(R+2.0+(i%2)),s_*.35,math.cos(a)*(R+2.4+(i%2))),col=WH,uvs=1.0)
emit('bld_lighthouse',[('walls',lw,(0,0,0)),('roof',lr,(0,0,0))],{**meta('lighthouse'),'note':'lantern is pale glass albedo, no emissive; keep the game light/glow if wanted'})
# gate tower (gt0 / gt1)
R=5.4;tw=M();tr=M()
ring_wall(tw,R+.02,0,8.2,.6,16,'b_stone',WH,door=(2.2,DH))
kit.cyl(tw,'b_darkstone',R+.32,R+.32,.5,16,t=(0,8.2,0),cap=True)
for i in range(10):a=i/10*6.283;obox(tw,(math.sin(a)*(R+.15),8.7,math.cos(a)*(R+.15)),(1.0,.8,.7),'b_stone',WH,yaw=a)
for y in (2.6,5.6):
  for i in range(4):a=i*1.57+.78;obox(tw,(math.sin(a)*(R+.05),y,math.cos(a)*(R+.05)),(.25,1.0,.2),'b_darkstone',W(0x303030),yaw=a)   # arrow slits
door_surround(tw,R,2.2,lantern=True)
rect(tw,np.array([-.5,3.2,R+.12]),np.array([1.,0,0]),np.array([0,1.,0]),1.0,2.4,'b_red',WH,(1,2.4))
kit.cyl(tr,'b_slate',R+.8,.05,6.2,16,t=(0,8.7,0));kit.cyl(tr,'b_iron',.06,.06,2.4,5,t=(0,14.6,0))
rect(tr,np.array([.06,15.9,0]),np.array([1.,0,0]),np.array([0,1.,0]),1.4,.9,'b_red',WH,(1.4,.9))
emit('bld_gate_tower',[('walls',tw,(0,0,0)),('roof',tr,(0,0,0))],{**meta('gt0'),'id':'gt0,gt1'})
json.dump(REG,open(os.path.join(BD,'buildings_index.json'),'w'),indent=1)
