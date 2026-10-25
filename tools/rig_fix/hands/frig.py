# frig.py in.glb out.glb wd : per-finger chains at the open-hand joints, keyed open/fist/relaxed per clip
import sys,json,struct,numpy as np,math
sys.path.insert(0,'/tmp/tg');from lib import load,acc,bindglobal
src,dst,wd=sys.argv[1:4];HS=0.97
j,b=load(src);b=bytearray(b);G,IBM=bindglobal(j,b);sk=j['skins'][0];N=j['nodes'];idx={x.get('name'):i for i,x in enumerate(N)}
fr=json.load(open(wd+'/frame.json'))
FING=['index','middle','ring','pinky','thumb']
def quat(R):
    m=R;t=np.trace(m)
    if t>0: s=0.5/math.sqrt(t+1);w=0.25/s;x=(m[2,1]-m[1,2])*s;y=(m[0,2]-m[2,0])*s;z=(m[1,0]-m[0,1])*s
    else:
        i=int(np.argmax(np.diag(m)))
        if i==0: s=2*math.sqrt(1+m[0,0]-m[1,1]-m[2,2]);w=(m[2,1]-m[1,2])/s;x=0.25*s;y=(m[0,1]+m[1,0])/s;z=(m[0,2]+m[2,0])/s
        elif i==1: s=2*math.sqrt(1+m[1,1]-m[0,0]-m[2,2]);w=(m[0,2]-m[2,0])/s;x=(m[0,1]+m[1,0])/s;y=0.25*s;z=(m[1,2]+m[2,1])/s
        else: s=2*math.sqrt(1+m[2,2]-m[0,0]-m[1,1]);w=(m[1,0]-m[0,1])/s;x=(m[0,2]+m[2,0])/s;y=(m[1,2]+m[2,1])/s;z=0.25*s
    q=np.array([x,y,z,w]);return q/np.linalg.norm(q)
def aq(ax,deg): ax=ax/np.linalg.norm(ax);h=math.radians(deg)/2;return np.r_[ax*math.sin(h),math.cos(h)]
jl=list(sk['joints']);AX={}
for s in 'LR':
    z=np.load(f'{wd}/h_{s}.npz',allow_pickle=True);w=np.array(fr[s]['w']);Nd=w+(z['nodes']-w)*HS;tg=[str(t) for t in z['tags']];E=z['edges']
    head={}
    for i,k in E:
        if tg[k][:-1] in FING: head[tg[k]]=Nd[i]
    Gh=G['hand_'+s];Rh=Gh[:3,:3]/np.linalg.norm(Gh[:3,0])
    hp=idx['hand_'+s]
    for f in FING:
        par=hp
        for n in (1,2,3):
            nm=f'{f}{n}_{s}';ni=idx[nm]
            # reparent
            for x in N:
                if 'children' in x and ni in x['children']: x['children'].remove(ni)
            N[par].setdefault('children',[]).append(ni)
            Gc=Gh.copy();Gc[:3,3]=head[f'{f}{n}'];Gp=G[N[par]['name']]
            L=np.linalg.inv(Gp)@Gc;sc_=np.linalg.norm(L[:3,:3],axis=0);N[ni]['translation']=L[:3,3].tolist();N[ni]['rotation']=quat(L[:3,:3]/sc_).tolist();N[ni]['scale']=sc_.tolist()
            G[nm]=Gc;IBM[jl.index(ni)]=np.linalg.inv(Gc);par=ni
    across=head['pinky1']-head['index1'];across/=np.linalg.norm(across)
    fd=head['middle2']-head['middle1'];fd/=np.linalg.norm(fd)
    nrm=np.cross(across,fd);th=head['thumb3']-Gh[:3,3]
    if (th-(th@across)*across-(th@fd)*fd)@nrm<0: nrm=-nrm
    # sign: rotate middle2 about middle1 by +60 around across; tip should move toward nrm
    def rot(v,ax,deg):
        ax=ax/np.linalg.norm(ax);t=math.radians(deg);return v*math.cos(t)+np.cross(ax,v)*math.sin(t)+ax*(ax@v)*(1-math.cos(t))
    sg=1 if (rot(head['middle2']-head['middle1'],across,60)@nrm)>0 else -1
    a_f=Rh.T@(across*sg);ta=(across*math.cos(math.radians(45))+nrm*math.sin(math.radians(45)))
    sgt=1 if (rot(head['thumb2']-head['thumb1'],ta,60)@nrm)>0 else -1
    import os;FL=float(os.environ.get('FLIP','1'));AX[s]=(a_f*FL,Rh.T@(ta*sgt)*FL)
del G
# write IBM back in place
a=j['accessors'][sk['inverseBindMatrices']];v=j['bufferViews'][a['bufferView']];o=v.get('byteOffset',0)+a.get('byteOffset',0)
b[o:o+IBM.size*4]=IBM.transpose(0,2,1).astype(np.float32).tobytes()
POSE={'open':(8,6,4,10,8,5),'fist':(70,80,60,40,35,30),'relax':(25,25,15,15,15,10),'grip':(60,70,50,40,35,30)}
def poseof(c):
    if c.startswith(('wb_ritual_lavawave','wb_ritual_meteor','wb_knockdown','wb_getup','wb_down','idle','walk','run','wb_idle','wb_walk','wb_run','wb_turn','death','hit','intro','grow','volcano_roar','skill','wb_stagger')): return 'open'
    if c.startswith(('attack','eruption_slam','wb_ritual_fissure','wb_stomp','wb_swat','windup','magma_sweep')): return 'fist'
    if c.startswith('boulder_hurl'): return 'grip'
    return 'relax'
fnodes={idx[f'{f}{n}_{s}'] for f in FING for n in (1,2,3) for s in 'LR'}
newb=bytearray();extra_views=[];base=len(b)
def addacc(arr,typ):
    global newb
    while (base+len(newb))%4: newb+=b'\0'
    off=base+len(newb);newb+=arr.astype(np.float32).tobytes()
    j['bufferViews'].append({'buffer':0,'byteOffset':off,'byteLength':arr.nbytes});ac={'bufferView':len(j['bufferViews'])-1,'componentType':5126,'count':len(arr),'type':typ}
    if typ=='SCALAR': ac['min']=[float(arr.min())];ac['max']=[float(arr.max())]
    j['accessors'].append(ac);return len(j['accessors'])-1
report={}
for an in j['animations']:
    keep=[c for c in an['channels'] if c['target'].get('node') not in fnodes];an['channels']=keep
    ins=[acc(j,b,an['samplers'][c['sampler']]['input']) for c in keep];t1=max(float(x.max()) for x in ins);t0=min(float(x.min()) for x in ins)
    p=poseof(an['name']);d=POSE[p];report[an['name']]=p;ti=addacc(np.array([t0,t1]),'SCALAR')
    for s in 'LR':
        af,at=AX[s]
        for f in FING:
            for n in (1,2,3):
                ni=idx[f'{f}{n}_{s}'];deg=(d[3+n-1] if f=='thumb' else d[n-1]);ax=at if f=='thumb' else af
                q0=np.array(N[ni]['rotation']);q=aq(ax,deg)  # in hand-aligned frame; node rest rot ~ identity relative to parent
                # compose: rest rotation * curl
                x1,y1,z1,w1=q0;x2,y2,z2,w2=q
                qq=np.array([w1*x2+x1*w2+y1*z2-z1*y2,w1*y2-x1*z2+y1*w2+z1*x2,w1*z2+x1*y2-y1*x2+z1*w2,w1*w2-x1*x2-y1*y2-z1*z2])
                oi=addacc(np.array([qq,qq]),'VEC4');an['samplers'].append({'input':ti,'output':oi,'interpolation':'STEP'})
                an['channels'].append({'sampler':len(an['samplers'])-1,'target':{'node':ni,'path':'rotation'}})
b=bytes(b)+bytes(newb)
while len(b)%4: b+=b'\0'
j['buffers'][0]['byteLength']=len(b)
js=json.dumps(j,separators=(',',':')).encode();js+=b' '*((4-len(js)%4)%4)
open(dst,'wb').write(struct.pack('<III',0x46546C67,2,28+len(js)+len(b))+struct.pack('<II',len(js),0x4E4F534A)+js+struct.pack('<II',len(b),0x004E4942)+b)
print('FRIG',dst,json.dumps({k:sum(1 for v in report.values() if v==k) for k in POSE}))
