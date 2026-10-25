import sys,json,struct,numpy as np
from lib import *
import os
TCUT=float(os.environ.get("TCUT","-0.8"))
FAM=('hand','fingers','thumb','index','middle','ring','pinky')
def nz(v):return v/np.linalg.norm(v)
rng=np.random.default_rng(5);GN=rng.random((32,32,32))
def vn(p):
    i=np.floor(p).astype(int);f=p-i;f=f*f*(3-2*f);o=0
    for dx in(0,1):
        for dy in(0,1):
            for dz in(0,1):
                w=(f[:,0] if dx else 1-f[:,0])*(f[:,1] if dy else 1-f[:,1])*(f[:,2] if dz else 1-f[:,2]);o=o+w*GN[(i[:,0]+dx)%32,(i[:,1]+dy)%32,(i[:,2]+dz)%32]
    return o
def rot(v,ax,ang):
    ax=nz(ax);return v*np.cos(ang)+np.cross(ax,v)*np.sin(ang)+ax*np.dot(ax,v)*(1-np.cos(ang))
class Builder:
    def __init__(s):s.V=[];s.F=[];s.UV=[];s.B=[]  # B: list of {bone:w}
    def sweep(s,pts,frames,rads,bones,sides,uvrect,cap=True,capbone=None,reps=2):
        base=len(s.V);n=len(pts);u0,v0,u1,v1=uvrect
        L=np.r_[0,np.cumsum(np.linalg.norm(np.diff(pts,axis=0),axis=1))];L/=L[-1]
        for k in range(n):
            a,nn=frames[k];ra,rn,ex=rads[k]
            for i in range(sides+1):
                th=2*np.pi*i/sides;c,sn=np.cos(th),np.sin(th)
                cc=np.sign(c)*abs(c)**(2/ex);ss=np.sign(sn)*abs(sn)**(2/ex)
                x=(i/sides*reps)%2;x=x if x<=1 else 2-x
                s.V.append(pts[k]+a*ra*cc+nn*rn*ss);s.UV.append((u0+(u1-u0)*x,v0+(v1-v0)*L[k]));s.B.append(bones[k])
        R=sides+1
        for k in range(n-1):
            for i in range(sides):
                p0=base+k*R+i;p1=p0+1;q0=p0+R;q1=q0+1;s.F+=[(p0,q0,p1),(p1,q0,q1)]
        if cap:
            t=len(s.V);d=nz(pts[-1]-pts[-2]);s.V.append(pts[-1]+d*min(rads[-1][0],rads[-1][1])*0.8);s.UV.append(((u0+u1)/2,v1));s.B.append(capbone or bones[-1])
            for i in range(sides):s.F.append((base+(n-1)*R+i,t,base+(n-1)*R+i+1))
        return base
VS=1/1.375
def slot(i):
    c=i%8;r=i//8;u0=c*0.125;v0=VS+r*(0.1875*VS);e=0.006
    return (u0+e,v0+e,u0+0.125-e,v0+0.1875*VS-e)
def build_hand(side,G,P,remv,sides,ringmul,uvrect,body_cx):
    sb=0 if side=='L' else 8
    g=lambda n:G[n+'_'+side][:3,3]
    w=g('hand')
    fd=nz(nz(np.mean([g(f+'3')-g(f+'1') for f in('index','middle','ring','pinky')],0))*0.4+nz(g('hand')-g('foreArm'))*0.6)
    a=g('index1')-g('pinky1');a=nz(a-fd*np.dot(a,fd))
    npalm=nz(np.cross(fd,a))
    if np.dot(npalm,np.array([body_cx,0,0])-w)*1<0 and abs(npalm[0])>0.3:npalm=-npalm
    elif abs(npalm[0])<=0.3 and np.dot(npalm,(np.array([body_cx,w[1],w[2]])-w))<0:npalm=-npalm
    Q=P[remv]-w;ed=np.ptp(Q@fd);ea=np.ptp(Q@a);en=np.ptp(Q@npalm)
    # wrist ring center/radius from remaining-boundary approx: verts of removed region nearest to forearm
    fa=g('foreArm');proj=(P[remv]-w)@fd;near=P[remv][proj<np.percentile(proj,12)]
    c0=near.mean(0);r0=np.median(np.linalg.norm((near-c0)-np.outer((near-c0)@fd,fd),axis=1))
    Lp=0.5*ed;Wp=max(0.62*ea,2.0*r0);Tp=max(0.3*en,0.95*r0)
    b=Builder();FB=lambda n:n+'_'+side
    # palm
    m=max(int(8*ringmul)+2,3);pts=[];fr=[];rd=[];bn=[]
    start=c0-fd*0.6*r0
    for k in range(m):
        t=k/(m-1);pts.append(start+fd*(Lp+0.6*r0)*t);fr.append((a,npalm))
        wdt=(1-t)*r0*1.25+t*Wp/2;th=((1-t)*r0*0.9+t*Tp/2)*(1-0.15*np.sin(np.pi*t))
        rd.append((wdt,th,2.0+0.6*t));bn.append({FB('foreArm'):0.5,FB('hand'):0.5} if k==0 else {FB('hand'):1.0})
    b.sweep(np.array(pts),fr,rd,bn,sides+(4 if ringmul>=0.5 else 0),slot(sb),cap=True,capbone={FB('hand'):1.0},reps=6)
    knuck=start+fd*(Lp+0.6*r0)*0.93
    Lf0=0.95*Lp
    spec=[('index',0.36,0.95,0.13,1),('middle',0.12,1.0,0.135,0),('ring',-0.12,0.95,0.128,-1),('pinky',-0.36,0.8,0.11,-2)]
    curls=np.radians([22,34,24])
    for fi,(nm,off,lm,rr,spr) in enumerate(spec):
        r=rr*Wp;base=knuck+a*off*Wp*0.95-npalm*0.05*Tp
        d=nz(rot(fd,npalm,0)+a*0.07*spr);seglen=np.array([0.45,0.30,0.25])*Lf0*lm
        joints=[base];dd=d;dirs=[]
        for s_ in range(3):
            dd=nz(rot(dd,np.cross(dd,npalm),-curls[s_]));dirs.append(dd);joints.append(joints[-1]+dd*seglen[s_])
        pts=[];fr=[];rd=[];bn=[]
        ts=[0,0.12,0.5,0.88] if ringmul>=1 else ([0,0.15,0.6] if ringmul>=0.5 else [0,0.55])
        for s_ in range(3):
            bone=FB(nm+str(s_+1));prev=FB('hand') if s_==0 else FB(nm+str(s_))
            dd=dirs[s_];aa=nz(a-dd*np.dot(a,dd));nn=nz(np.cross(dd,aa))
            if np.dot(nn,npalm)<0:nn=-nn
            for t in ts:
                if s_==0 and t==0:p=joints[0]-dd*0.3*seglen[0]
                else:p=joints[s_]+dd*seglen[s_]*t
                taper=1-0.25*(s_+t)/3;bulge=1.14 if t in(0,) and s_>0 else (1.06 if t in(0.12,0.15) else 1.0)
                pts.append(p);fr.append((aa,nn));rd.append((r*taper*bulge,r*0.88*taper*bulge,2.6))
                bn.append({prev:0.5,bone:0.5} if t==0 else {bone:1.0})
        pts.append(joints[3]);fr.append(fr[-1]);rd.append((r*0.7,r*0.6,2.4));bn.append({FB(nm+'3'):1.0})
        b.sweep(np.array(pts),fr,rd,bn,sides,slot(sb+1+fi),cap=True)
    # thumb
    tb=start+fd*0.35*Lp+a*0.42*Wp+npalm*0.25*Tp
    d=nz(fd*0.55+a*0.6+npalm*0.55);seglen=np.array([0.42,0.32,0.26])*Lf0*0.85;r=0.15*Wp
    joints=[tb];dd=d;dirs=[]
    for s_ in range(3):
        dd=nz(rot(dd,np.cross(dd,-a),-np.radians([10,20,18][s_])));dirs.append(dd);joints.append(joints[-1]+dd*seglen[s_])
    pts=[];fr=[];rd=[];bn=[]
    for s_ in range(3):
        bone=FB('thumb'+str(s_+1));prev=FB('hand') if s_==0 else FB('thumb'+str(s_))
        dd=dirs[s_];ref=npalm;aa=nz(ref-dd*np.dot(ref,dd));nn=np.cross(dd,aa)
        for t in ([0,0.12,0.5,0.88] if ringmul>=1 else ([0,0.15,0.6] if ringmul>=0.5 else [0,0.55])):
            p=joints[0]-dd*0.35*seglen[0] if (s_==0 and t==0) else joints[s_]+dd*seglen[s_]*t
            taper=1-0.22*(s_+t)/3;bulge=1.14 if t==0 and s_>0 else 1.0
            pts.append(p);fr.append((aa,nn));rd.append((r*taper*bulge,r*0.9*taper*bulge,2.6));bn.append({prev:0.5,bone:0.5} if t==0 else {bone:1.0})
    pts.append(joints[3]);fr.append(fr[-1]);rd.append((r*0.7,r*0.62,2.4));bn.append({FB('thumb3'):1.0})
    b.sweep(np.array(pts),fr,rd,bn,sides,slot(sb+5),cap=True)
    V=np.array(b.V);
    # rocky displacement
    sc=1.0/max(r0,1e-3)*1.6
    dsp=(vn(V*sc)-0.5)*0.35*r0+(vn(V*sc*3+7)-0.5)*0.12*r0
    cen=np.array([0,0,0.])
    return V,np.array(b.F),np.array(b.UV),b.B,dsp
def normals(V,F):
    N=np.zeros_like(V);fn=np.cross(V[F[:,1]]-V[F[:,0]],V[F[:,2]]-V[F[:,0]])
    for c in range(3):np.add.at(N,F[:,c],fn)
    return N/np.maximum(np.linalg.norm(N,axis=1,keepdims=True),1e-9)
def inscribed_rect(j,b,UV,F,dom,jn,side_bone):
    from PIL import Image,ImageDraw
    from scipy import ndimage as nd
    R=512;img=Image.new('L',(R,R),0);d=ImageDraw.Draw(img)
    fm=np.all(np.isin(dom[F],[jn.index(x) for x in side_bone]),1)
    for f in F[fm]:d.polygon([(UV[k,0]*R,UV[k,1]*R) for k in f],fill=255)
    cov=np.array(img)>0;dt=nd.distance_transform_edt(cov);y,x=np.unravel_index(dt.argmax(),dt.shape);h=dt.max()*0.68
    return ((x-h)/R,(y-h)/R,(x+h)/R,(y+h)/R)
def crop_rects(UV,F,dom,jn):
    from PIL import Image,ImageDraw
    from scipy import ndimage as nd
    R=512;img=Image.new('L',(R,R),0);d=ImageDraw.Draw(img)
    ids=[jn.index(n) for n in jn if n.startswith(('foreArm','upperArm','hand','thigh','shin'))]
    fm=np.all(np.isin(dom[F],ids),1)
    for f in F[fm]:d.polygon([(UV[k,0]*R,UV[k,1]*R) for k in f],fill=255)
    dt=nd.distance_transform_edt(np.array(img)>0);out=[]
    for _ in range(16):
        y,x=np.unravel_index(dt.argmax(),dt.shape);h=max(dt.max()*0.7,3)
        out.append(((x-h)/R,(y-h)/R,(x+h)/R,(y+h)/R));dt[max(0,int(y-2*h)):int(y+2*h),max(0,int(x-2*h)):int(x+2*h)]=0
    return out
def extend_images(j,b,UV,F,dom,jn):
    import io
    from PIL import Image
    rects=crop_rects(UV,F,dom,jn);res={}
    bc=[im for im in j['images'] if 'basecolor' in (im.get('name') or '')] or j['images'][-1:]
    v=j['bufferViews'][bc[0]['bufferView']];o=v.get('byteOffset',0);Ib=np.array(Image.open(io.BytesIO(b[o:o+v['byteLength']])).convert('RGB')).astype(float);hh,ww=Ib.shape[:2]
    def orange(r):
        c=Ib[int(r[1]*hh):max(int(r[3]*hh),int(r[1]*hh)+1),int(r[0]*ww):max(int(r[2]*ww),int(r[0]*ww)+1)]
        return (c[...,0]-c[...,2]).mean()+ (c.mean()>140)*100
    rects=sorted(rects,key=orange)[:5]
    for im in j.get('images',[]):
        vi=im['bufferView'];v=j['bufferViews'][vi];o=v.get('byteOffset',0)
        I=Image.open(io.BytesIO(b[o:o+v['byteLength']]));mode=I.mode;I=I.convert('RGBA' if 'A' in mode else 'RGB')
        w,h=I.size;sh=int(round(0.375*w));N=Image.new(I.mode,(w,h+sh));N.paste(I,(0,0))
        tw,th=w//8,sh//2;isn='normal' in (im.get('name') or '').lower()
        rs=np.random.default_rng(11)
        for i in range(16):
            T=Image.new(N.mode,(tw,th));x0=(i%8)*tw;y0=h+(i//8)*th
            for k in range(60):
                r=rects[rs.integers(len(rects))];cw=max(int((r[2]-r[0])*w),8);ch=max(int((r[3]-r[1])*h),8)
                cs=min(cw,ch);sx=rs.random();sy=rs.random();px=rs.random();py=rs.random();flip=rs.random()<0.5
                cx=int(r[0]*w+(cw-cs)*sx);cy=int(r[1]*h+(ch-cs)*sy)
                P_=I.crop((cx,cy,cx+cs,cy+cs))
                ps=max(int(tw*0.45),8);P_=P_.resize((ps,ps),Image.BICUBIC)
                if flip and not isn:P_=P_.transpose(Image.FLIP_TOP_BOTTOM)
                yy,xx=np.mgrid[0:ps,0:ps]/ps;msk=np.clip(np.minimum(np.minimum(xx,1-xx),np.minimum(yy,1-yy))*5,0,1)
                M=Image.fromarray((msk*255).astype(np.uint8))
                T.paste(P_,(int(px*(tw-ps*0.5)-ps*0.25),int(py*(th-ps*0.5)-ps*0.25)),M)
            N.paste(T,(x0,y0))
        bio=io.BytesIO()
        if im['mimeType']=='image/webp':N.save(bio,'WEBP',quality=92)
        else:N.save(bio,'PNG',optimize=True)
        res[vi]=bio.getvalue()
    return res
def island_rect(UV,Fs):
    from PIL import Image,ImageDraw
    from scipy import ndimage as nd
    R=512;img=Image.new('L',(R,R),0);d=ImageDraw.Draw(img)
    for f in Fs:d.polygon([(UV[k,0]*R,UV[k,1]*R) for k in f],fill=255)
    cov=np.array(img)>0;dt=nd.distance_transform_edt(cov);y,x=np.unravel_index(dt.argmax(),dt.shape);h=dt.max()*0.68
    return ((x-h)/R,(y-h)/R,(x+h)/R,(y+h)/R)
def process(src,dst,sides,ringmul):
    j,b=load(src);p=j['meshes'][0]['primitives'][0];A=p['attributes']
    P=acc(j,b,A['POSITION']).astype(np.float64);N=acc(j,b,A['NORMAL']).astype(np.float64);UV=acc(j,b,A['TEXCOORD_0']).astype(np.float64)
    J=acc(j,b,A['JOINTS_0']).astype(int);W=acc(j,b,A['WEIGHTS_0']).astype(np.float64);F=acc(j,b,p['indices']).reshape(-1,3).astype(int)
    G,IBM=bindglobal(j,b);sk=j['skins'][0];jn=[j['nodes'][n]['name'] for n in sk['joints']]
    dom=J[np.arange(len(J)),W.argmax(1)]
    keepF=np.ones(len(F),bool);newparts=[]
    cx=P[:,0].mean()
    for side in 'LR':
        fam=[i for i,n in enumerate(jn) if n.endswith('_'+side) and n.startswith(FAM)]
        arm=fam+[jn.index('foreArm_'+side)]
        wv=G['hand_'+side][:3,3];fdv=nz(wv-G['foreArm_'+side][:3,3]);tt=(P-wv)@fdv
        rr=np.linalg.norm((P-wv)-np.outer(tt,fdv),axis=1);FL=np.linalg.norm(wv-G['foreArm_'+side][:3,3])
        vm=np.isin(dom,arm)&(tt>TCUT/4.72*FL)&(rr<3.0/4.72*FL)
        vm|=np.isin(dom,fam)
        fm=np.all(vm[F],1);keepF&=~fm
        rect=island_rect(UV,F[fm])
        newparts.append(build_hand(side,G,P,np.where(vm)[0],sides,ringmul,rect,cx))
    newimg=extend_images(j,b,UV,F,dom,jn)
    UV=UV.copy();UV[:,1]*=VS
    F2=F[keepF];used=np.unique(F2);remap=-np.ones(len(P),int);remap[used]=np.arange(len(used))
    P2=P[used];N2=N[used];UV2=UV[used];J2=J[used];W2=W[used];F2=remap[F2]
    allP=[P2];allN=[N2];allUV=[UV2];allJ=[J2];allW=[W2];allF=[F2];off=len(P2)
    for V,Fh,Uh,Bh,dsp in newparts:
        Nh=normals(V,Fh);V=V+Nh*dsp[:,None];Nh=normals(V,Fh)
        jj=np.zeros((len(V),4),int);ww=np.zeros((len(V),4))
        for i,bd in enumerate(Bh):
            for c,(k,v) in enumerate(bd.items()):jj[i,c]=jn.index(k);ww[i,c]=v
        allP.append(V);allN.append(Nh);allUV.append(Uh);allJ.append(jj);allW.append(ww);allF.append(Fh+off);off+=len(V)
    P3=np.vstack(allP).astype(np.float32);N3=np.vstack(allN).astype(np.float32);UV3=np.vstack(allUV).astype(np.float32)
    J3=np.vstack(allJ).astype(np.uint8);W3=np.vstack(allW).astype(np.float32);F3=np.vstack(allF).astype(np.uint32 if off>65535 else np.uint16)
    # rebuild buffer
    repl={A['POSITION']:P3,A['NORMAL']:N3,A['TEXCOORD_0']:UV3,A['JOINTS_0']:J3,A['WEIGHTS_0']:W3,p['indices']:F3.reshape(-1)}
    replviews={j['accessors'][i]['bufferView'] for i in repl}
    nb=bytearray();newviews=[];vmap={}
    for vi,v in enumerate(j['bufferViews']):
        if vi in replviews:continue
        while len(nb)%4:nb+=b'\0'
        o=v.get('byteOffset',0);nv=dict(v);nv['byteOffset']=len(nb);dat=newimg.get(vi,b[o:o+v['byteLength']]);nv['byteLength']=len(dat);nb+=dat;vmap[vi]=len(newviews);newviews.append(nv)
    for i,arr in repl.items():
        while len(nb)%4:nb+=b'\0'
        a=j['accessors'][i];bv={'buffer':0,'byteOffset':len(nb),'byteLength':arr.nbytes}
        if i!=p['indices']:bv['target']=34962
        else:bv['target']=34963
        nb+=arr.tobytes();vmap[('n',i)]=len(newviews);newviews.append(bv)
    for i,a in enumerate(j['accessors']):
        if i in repl:
            arr=repl[i];a['bufferView']=vmap[('n',i)];a['byteOffset']=0;a['count']=len(arr);a.pop('normalized',None)
            a['componentType']={np.float32:5126,np.uint8:5121,np.uint16:5123,np.uint32:5125}[arr.dtype.type]
            if 'min' in a and i==A['POSITION']:a['min']=P3.min(0).tolist();a['max']=P3.max(0).tolist()
            elif 'min' in a:a.pop('min');a.pop('max')
        elif 'bufferView' in a:a['bufferView']=vmap[a['bufferView']]
    for im in j.get('images',[]):
        if 'bufferView' in im:im['bufferView']=vmap[im['bufferView']]
    j['bufferViews']=newviews;j['buffers']=[{'byteLength':len(nb)}]
    while len(nb)%4:nb+=b'\0'
    js=json.dumps(j,separators=(',',':')).encode();js+=b' '*((4-len(js)%4)%4)
    out=struct.pack('<III',0x46546C67,2,12+8+len(js)+8+len(nb))+struct.pack('<II',len(js),0x4E4F534A)+js+struct.pack('<II',len(nb),0x004E4942)+nb
    open(dst,'wb').write(out)
    print(dst,'verts',len(P),'->',len(P3),'tris',len(F),'->',len(F3)//1)
    return len(F3)
if __name__=='__main__':
    process(sys.argv[1],sys.argv[2],int(sys.argv[3]),float(sys.argv[4]))
