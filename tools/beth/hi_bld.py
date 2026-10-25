# Round-4 High/Medium/Low building exteriors for Godot. Re-runs bld.py's authored buildings with detail injectors
# (High), as-is (Medium) or simplified (Low), adds bespoke character pieces (High+Medium), packs everything onto
# one vertex-colour-free slot atlas (2048/1024/512 with normal, ORM and emissive maps) and writes GLBs.
import sys,os,json,math,numpy as np,types
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import kit,bldgeo,hi_detail,hipack
from PIL import Image
OUT=os.path.abspath(sys.argv[1]);SPEC=os.path.abspath(sys.argv[2]);HI=os.path.join(OUT,'hi');os.makedirs(HI,exist_ok=True)
src=open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'bld.py')).read()
src=src.replace("def emit(name,nodes,meta):","def emit(name,nodes,meta):\n  CAP[name]=(nodes,meta);return\ndef _emit_orig(name,nodes,meta):")
src=src.replace("json.dump(REG,open(os.path.join(BD,'buildings_index.json'),'w'),indent=1)","")
HOOK='''
import hi_detail as _hd
_ow,_og,_owin,_otf,_oq,_ods,_orw=wall,gable,window,timber_frame,quoins,door_surround,ring_wall
def ring_wall(m,R,y0,y1,T,N,tile,col,door=None,taper=0.0,cell=(1.6,1.6)):
  _orw(m,R,y0,y1,T,N if MODE!='high' else max(N,int(N*1.5)),tile,col,door,taper,cell)
  if MODE=='high' and tile in('b_stone','b_darkstone','b_white','b_red') and y1-y0>1.5:_hd.ring_relief(m,R,y0,y1,door,tile,col,budget=int(min(8000,R*(y1-y0)*55)),taper=taper)
def wall(m,A,B,y0,y1,T,tile,col,openings=(),**k):
  r=_ow(m,A,B,y0,y1,T,tile,col,openings,**k)
  if MODE=='high' and tile in('b_stone','b_darkstone','b_white') and y0<4.5:_hd.stone_relief(m,A,B,y0,min(y1,4.6),openings,tile,col,budget=1800)
  return r
def gable(m,cx,cz,w,d,y,rise,over,ridge,tile,col,*a,**k):
  _og(m,cx,cz,w,d,y,rise,over,ridge,tile,col,*a,**k)
  if MODE=='high' and tile in('b_slate','b_shingle') and w*d>3:_hd.roof_rows(m,cx,cz,w,d,y,rise,over,ridge,tile,col)
def window(m,x,y,z,yaw,w=.9,h=1.1,shutters=False,bars=False,frame='b_timber'):
  if MODE=='low':
    R=rot('y',yaw);n=R@np.array([0,0,1.]);u=R@np.array([1.,0,0]);c=np.array([x,y,z]);rect(m,c-u*w/2+n*.03,u,np.array([0,1.,0]),w,h,'b_window',WH,(w,h));return
  _owin(m,x,y,z,yaw,w,h,shutters,bars,frame)
  if MODE=='high':
    R=rot('y',yaw);n=R@np.array([0,0,1.]);u=R@np.array([1.,0,0]);c=np.array([x,y,z])
    obox(m,c+u*0+n*.07,(.06,h,.05),'b_timber',WH,yaw=yaw);obox(m,c+np.array([0,h*.55,0])+n*.07,(w,.06,.05),'b_timber',WH,yaw=yaw)
    obox(m,c+np.array([0,-.16,0])+n*.12,(w+.45,.1,.3),'b_stone',WH,yaw=yaw);obox(m,c+np.array([0,h+.1,0])+n*.1,(w+.5,.22,.22),'b_stone',WH,yaw=yaw)
    for s in (-1,1):obox(m,c+u*s*(w/2+.2)+np.array([0,h+.06,0])+n*.12,(.14,.14,.16),'b_stone',WH,yaw=yaw)
def timber_frame(*a,**k):
  if MODE!='low':_otf(*a,**k)
def quoins(*a,**k):
  if MODE!='low':_oq(*a,**k)
def door_surround(m,z,DW,tile='b_darkstone',steps=True,lantern=True,sign=None):
  if MODE=='low':obox(m,(0,DH,z+.1),(DW+.6,.3,.3),tile,WH);return
  _ods(m,z,DW,tile,steps,lantern,sign)
  if MODE=='high':
    for i in range(7):a=math.pi*i/6;obox(m,(math.cos(a)*(DW/2+.18),DH+.32+math.sin(a)*.45,z+.12),(.36,.3,.3),tile,WH*1.05)
'''
src=src.replace("def scaleK(m):",HOOK+"\ndef scaleK(m):",1)
def run(mode):
  ns={'__name__':'bld_'+mode,'__file__':os.path.abspath('bld.py'),'MODE':mode,'CAP':{}};sys.argv=['bld.py',OUT,SPEC];kit.rng=np.random.default_rng(5)
  exec(compile(src,'bld.py','exec'),ns);return ns
# ---------- bespoke character pieces (local units) ----------
def bespoke(ns,mode,bid,w_,r_):
  S=ns['SPEC'].get(bid,{});w,d=S.get('w',10),S.get('d',10);obox,cyl,WH,W,window,rot=ns['obox'],kit.cyl,ns['WH'],ns['W'],ns['window'],kit.rot
  seg=24 if mode=='high' else 12;BL=W(0x6f86d8)
  def cone(m,r,h,x,y,z,tile='b_slate',col=None):cyl(m,tile,r,.02,h,seg,t=(x,y,z),col=col if col is not None else W(0xb8c4ec))
  def tower(x,z,r,h,roofh,tile='b_stone',rcol=None,wins=3):
    pass
    sub=ns['M']();ns['ring_wall'](sub,r,0,h,.4,seg,tile,WH)
    if mode!='low':
      for k in range(int(h/1.6)):cyl(sub,'b_darkstone',r+.06,r+.06,.12,seg,t=(0,k*1.6+1.0,0),cap=False)
      for k in range(wins):a=k*2.1+.5;window(sub,math.sin(a)*(r+.05),h*(.35+.18*k),math.cos(a)*(r+.05),a,.5,1.3,frame='stone')
      for i in range(seg//2):a=i/(seg//2)*6.283;obox(sub,(math.sin(a)*(r+.1),h,math.cos(a)*(r+.1)),(.5,.5,.3),tile,WH,yaw=a)
    cyl(sub,'b_darkstone',r+.25,r+.25,.25,seg,t=(0,h-.05,0),cap=True);cone(sub,r+.35,roofh,0,h+.2,0,col=rcol)
    cyl(sub,'b_iron',.05,.02,1.2,5,t=(0,h+roofh+.1,0));w_.merge(sub,np.eye(3),(x,0,z))
  hw,hd=w/2,d/2
  if bid=='mage':
    for sx in (-1,1):tower(sx*(hw-2.0),-hd+2.0,2.0,15,7,rcol=BL);tower(sx*(hw-1.2),hd-1.2,1.2,11,4.5,rcol=BL,wins=2)
    tower(0,-hd*.2,1.5,ns['SPEC'][bid].get('h',8)+9,8,rcol=BL,wins=2)
    for x in (-hw/2.6,hw/2.6):ns_banner(ns,w_,x,4.4,hd+.05,0,0x2040a0)
  elif bid=='temple':
    for sx in (-1,1):
      sub=ns['M']();obox(sub,(0,0,0),(3.4,15,3.4),'b_white',WH)
      if mode!='low':
        for y in (5,9.5,13):
          for f in range(4):a=f*math.pi/2;window(sub,math.sin(a)*1.72,y,math.cos(a)*1.72,a,.6,1.6,frame='stone')
        for y in (4.8,9.3,14.8):obox(sub,(0,y,0),(3.7,.22,3.7),'b_white',WH*.95)
        for cx_ in (-1,1):
          for cz_ in (-1,1):obox(sub,(cx_*1.75,0,cz_*1.75),(.45,15.4,.45),'b_white',WH*.97);cone(sub,.3,2.2,cx_*1.75,15.4,cz_*1.75)
      cyl(sub,'b_slate',2.6,.03,8,4,R=rot('y',math.pi/4),t=(0,15,0),col=W(0xb8c4ec));w_.merge(sub,np.eye(3),(sx*(hw-1.7),0,hd-1.7))
    sub=ns['M']();cyl(sub,'b_glass',1.7,1.7,.12,seg,R=rot('x',math.pi/2),t=(0,0,0),cap=True)
    if mode!='low':
      for i in range(8):a=i/8*6.283;obox(sub,(math.cos(a)*.85,math.sin(a)*.85-.05,.12),(.08,1.7,.08),'b_white',WH) if False else ns['obox'](sub,(0,-.05,.08),(.08,3.4,.08),'b_white',WH,yaw=0) if i==0 else None
      cyl(sub,'b_white',1.9,1.9,.25,seg,R=rot('x',math.pi/2),t=(0,0,-.05),cap=False)
    w_.merge(sub,np.eye(3),(0,ns['SPEC'][bid].get('h',9)+2.0,hd+.15))
    h=9;rise=.7*hw;cyl(r_,'b_white',4.0,4.0,2.4,seg,t=(0,h+rise-1.0,-hd*.35),cap=False)
    kit.blob(r_,'b_slate',4.1,scale=(1,1,1),sub=3 if mode=='high' else 2 if mode=='medium' else 1,jit=0,t=(0,h+rise+1.4,-hd*.35),flat_bottom=0,col=W(0xb8c4ec),uvs=1.0,colvar=0)
    cyl(r_,'b_iron',.08,.02,2.2,6,t=(0,h+rise+5.4,-hd*.35))
  elif bid=='colosseum':
    R=w/2
    for t in range(6 if mode!='low' else 3):
      rr=R-1.0-t*(1.3 if mode!='low' else 2.6);ns['ring_wall'](w_,rr,0,7.0-t*(1.15 if mode!='low' else 2.3),1.3 if mode!='low' else 2.6,seg+8,'b_stone',W(0xd8ccb0),door=(3.2,8))
    if mode!='low':
      for i in range(32):
        a=(i+.5)/32*6.283
        if abs(((a+math.pi)%6.283)-math.pi)<.3:continue
        cyl(w_,'b_stone',.22,.2,2.2,8,t=(math.sin(a)*(R-.6),7.6,math.cos(a)*(R-.6)))
      cyl(w_,'b_darkstone',R-.4,R-.4,.3,seg+8,t=(0,9.8,0),cap=False)
  elif bid=='keep':
    if mode!='low':
      for (L,fn) in ((w,lambda u:(u,hd,0)),(w,lambda u:(-u,-hd,math.pi)),(d,lambda u:(hw,-u,math.pi/2)),(d,lambda u:(-hw,u,-math.pi/2))):
        n=int(L/.9)
        for i in range(n):
          u=(i+.5)*L/n-L/2;x,z,yw=fn(u);R=rot('y',yw);nn=R@np.array([0,0,1.])
          obox(w_,np.array([x,9.3,z])+nn*.25,(.3,.7,.5),'b_stone',WH,yaw=yw)
          if i%3==1 and not(yw==0 and abs(u)<2.5):obox(w_,np.array([x,5.5,z])+nn*.04,(.16,1.1,.08),'b_darkstone',W(0x202020),yaw=yw)
      for x in (-1.1,-.55,0,.55,1.1):obox(w_,(x,ns['DH']+.35,hd+.32),(.07,.9,.07),'b_iron',WH)
      obox(w_,(0,ns['DH']+.8,hd+.32),(2.4,.08,.08),'b_iron',WH)
  elif bid=='smithy':
    sub=ns['M']()
    for i in range(9):a=math.pi*i/8;obox(sub,(math.cos(a)*1.8,ns['DH']-.2+math.sin(a)*1.0,hd+.15),(.5,.35,.35),'b_timber',WH)
    w_.merge(sub,np.eye(3),(0,0,0));obox(w_,(hw*.6,0,hd+1.6),(.5,.5,.9),'b_darkstone',WH);obox(w_,(hw*.6,.5,hd+1.6),(.35,.3,1.0),'b_iron',WH)
    cyl(w_,'b_planks',.45,.5,.8,12,t=(hw*.6+1.2,0,hd+1.2),cap=True);obox(r_,(-hw*.55,4,-hd*.3),(1.8,5.5,1.8),'b_stone',WH);obox(r_,(-hw*.55,9.5,-hd*.3),(2.1,.3,2.1),'b_darkstone',WH)
    for i in range(5):obox(w_,(-hw*.6+i*.35,0,hd+1.0),(.06,1.6,.06),'b_iron',WH)
  elif bid=='inn':
    obox(w_,(-2.6,3.6,hd+.6),(.08,.08,1.2),'b_iron',WH);obox(w_,(-2.6,2.7,hd+1.05),(.08,.9,1.0),'b_planks',W(0xa06020)*1.3)
    for x in (-hw*.55,hw*.55):ns_banner(ns,w_,x,5.6,hd+.05,0,0x2040a0)
    for x in (-hw*.3,hw*.3):ns['chimney'](r_,x,-hd*.3,5.4,6.6+.7*hd+.6)
  elif bid=='guildhall':
    h=7.2;rise=.7*hd;sub=ns['M']();obox(sub,(0,0,0),(3.6,h+rise+4.5,3.6),'b_stone',WH)
    cyl(sub,'b_white',1.0,1.0,.12,seg,R=rot('x',math.pi/2),t=(0,h+rise+2.6,1.82),cap=True);obox(sub,(0,h+rise+2.6,1.92),(.08,.8,.05),'b_iron',WH);obox(sub,(.25,h+rise+2.6,1.93),(.6,.08,.05),'b_iron',WH)
    obox(sub,(0,h+rise+4.5,0),(4.0,.3,4.0),'b_darkstone',WH);cyl(sub,'b_slate',2.9,.03,4.5,4,R=rot('y',math.pi/4),t=(0,h+rise+4.8,0),col=W(0xb8c4ec))
    r_.merge(sub,np.eye(3),(0,0,hd*.15))
  elif bid=='library':
    for sx in (-1,1):
      for k in range(4):z=-hd+d*(k+.5)/4;obox(w_,(sx*(hw+.35),0,z),(.7,6.5,.9),'b_stone',WH)
  elif bid=='townhall':
    h=7.6;rise=.7*hd;obox(r_,(0,h+rise-.4,0),(2.2,3.2,2.2),'b_white',WH);cyl(r_,'b_slate',1.8,.03,2.8,4,R=rot('y',math.pi/4),t=(0,h+rise+2.8,0),col=W(0xb8c4ec))
  elif bid=='lighthouse' and mode!='low':
    for i in range(24):a=i/24*6.283;obox(w_,(math.sin(a)*5.35,11.3,math.cos(a)*5.35),(.3,.7,.45),'b_darkstone',WH,yaw=a)
def ns_banner(ns,m,x,y,z,yaw,col,h=2.6):
  R=kit.rot('y',yaw);n=R@np.array([0,0,1.]);u=R@np.array([1.,0,0]);W=ns['W']
  ns['obox'](m,np.array([x,y+.05,z])+n*.25,(1.2,.08,.08),'b_iron',ns['WH'],yaw=yaw)
  ns['rect'](m,np.array([x,y-h,z])+n*.3-u*.5,u,np.array([0,1.,0]),1.0,h,'b_white',W(col)*1.1,(1,h))
  ns['rect'](m,np.array([x,y-h-.4,z])+n*.3-u*.5,u,np.array([0,1.,0]),1.0,.4,'b_white',W(0xd0a040),(1,.4))
# ---------- run all modes, pack, write ----------
MODES={}
for mode in ('high','medium','low'):
  ns=run(mode);CAP=ns['CAP'];out={}
  for name,(nodes,meta) in CAP.items():
    bid=meta['id'].split(',')[0]
    nd={nn:mm for nn,mm,tr in nodes};w_,r_=nd.get('walls'),nd.get('roof')
    if w_ is not None and r_ is not None:bespoke(ns,mode,bid,w_,r_)
    out[name]=([(nn,ns['scaleK'](mm),tuple(np.asarray(tr)*ns['K'])) for nn,mm,tr in nodes],meta)
  MODES[mode]=out;print(mode,{k:sum(len(m.P)//3 for _,m,_ in v[0]) for k,v in out.items()})
BT=json.load(open(os.path.join(OUT,'buildings','atlas','atlas.json')))['tiles']
def props(src,tile):
  n=BT[tile];p={'rough':.85,'metal':0,'bump':1.0}
  if n=='b_iron':p.update(rough=.45,metal=1.0)
  if n in('b_glass','b_window'):p.update(rough=.15,bump=.2,emit={'col':(255,196,120),'thr':105})
  if n in('b_slate','b_shingle'):p.update(rough=.7)
  if n in('b_white','b_red','b_plaster'):p.update(rough=.9,bump=.5)
  return p
P=hipack.Packer([Image.open(os.path.join(OUT,'buildings','atlas','atlas.png'))],props)
for mode in MODES:
  for name,(nodes,meta) in MODES[mode].items():
    for nn,mm,tr in nodes:P.add(mm)
print('slots',P.solve());TD=os.path.join(HI,'buildings','tex');P.paint(TD)
REG=[]
for mode,res in (('high',2048),('medium',1024),('low',512)):
  for name,(nodes,meta) in MODES[mode].items():
    sfx={'high':'','medium':'_lod1','low':'_lod2'}[mode];path=os.path.join(HI,'buildings',name+sfx+'.glb')
    t=hipack.write_hi(path,name+sfx,[(nn,P.remap(mm),tr) for nn,mm,tr in nodes],os.path.join(TD,str(res)),emissive=True,extras={**meta,'tier':mode,'tex':res})
    REG.append({'file':f'hi/buildings/{name}{sfx}.glb','tier':mode,'tris':t,'tex':res,'id':meta['id']});print(name+sfx,t)
json.dump(REG,open(os.path.join(HI,'buildings','index.json'),'w'),indent=1)
