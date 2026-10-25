import sys,io,os,json,numpy as np
from PIL import Image,ImageDraw
from scipy import ndimage as nd
from lib import *
src,outdir,setname=sys.argv[1:4];os.makedirs(outdir,exist_ok=True)
j,b=load(src);p=j['meshes'][0]['primitives'][0];A=p['attributes']
P=acc(j,b,A['POSITION']).astype(float);UV=acc(j,b,A['TEXCOORD_0']).astype(float);J=acc(j,b,A['JOINTS_0']).astype(int);W=acc(j,b,A['WEIGHTS_0']).astype(float);F=acc(j,b,p['indices']).reshape(-1,3).astype(int)
sk=j['skins'][0];joints=sk['joints'];IBM=acc(j,b,sk['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1).astype(float)
N=j['nodes'];par={c:i for i,n in enumerate(N) for c in n.get('children',[])}
def local(i,ov):
    n=N[i];o=ov.get(i,{});t=o.get('t',n.get('translation',[0,0,0]));r=o.get('r',n.get('rotation',[0,0,0,1]));s=o.get('s',n.get('scale',[1,1,1]))
    M=np.eye(4);M[:3,:3]=q2m(r)*np.array(s);M[:3,3]=t;return M
def skin(ov):
    G={}
    def g(i):
        if i in G:return G[i]
        M=local(i,ov);G[i]=(g(par[i])@M) if i in par else M;return G[i]
    S=np.array([g(n)@IBM[k] for k,n in enumerate(joints)]);Ph=np.c_[P,np.ones(len(P))];o=np.zeros((len(P),3))
    for c in range(4):o+=W[:,c:c+1]*np.einsum('nij,nj->ni',S[J[:,c]],Ph)[:,:3]
    return o
def samp(an,t):
    ov={}
    for ch in an['channels']:
        s=an['samplers'][ch['sampler']];T=acc(j,b,s['input'])[:,0];V=acc(j,b,s['output']).astype(float)
        k=min(max(np.searchsorted(T,t),1),len(T)-1);a=np.clip((t-T[k-1])/max(T[k]-T[k-1],1e-6),0,1);v=V[k-1]*(1-a)+V[k]*a
        if ch['target']['path']=='rotation':v=v/np.linalg.norm(v)
        if ch['target']['path'] in('translation','rotation','scale'):ov.setdefault(ch['target']['node'],{})[ch['target']['path'][0]]=v
    return ov
R0=skin({});E=np.r_[F[:,[0,1]],F[:,[1,2]],F[:,[2,0]]]
el=lambda X:np.linalg.norm(X[E[:,0]]-X[E[:,1]],axis=1)+1e-9
e0=el(R0);fs=np.zeros(len(F))
for an in j.get('animations',[]):
    T=acc(j,b,an['samplers'][0]['input'])[:,0]
    for t in np.linspace(T[0],T[-1],6):fs=np.maximum(fs,np.abs(np.log(el(skin(samp(an,t)))/e0)).reshape(3,-1).max(0))
vs=np.zeros(len(P));np.maximum.at(vs,F.ravel(),np.repeat(fs,3))
ws=np.sort(W,1)[:,::-1];split=np.clip(ws[:,1]/np.maximum(ws[:,0],1e-6),0,1)
key=np.round(P*1e4).astype(np.int64);_,inv,cnt=np.unique(key,axis=0,return_inverse=True,return_counts=True);seam=(cnt[inv.ravel()]>1).astype(float)
jn=[N[i]['name'] for i in joints];JB=('shoulder','upperArm','foreArm','hand','head','thigh','shin','foot','hips','spine','chest','thumb','index','middle','ring','pinky')
jb=np.zeros(len(P))
for c in range(4):jb+=W[:,c]*np.array([jn[k].startswith(JB) for k in J[:,c]])
rk=np.argsort(np.argsort(vs))/len(vs);score=np.clip(0.55*rk**1.5+0.35*split*jb+0.15*seam,0,1)
# images
imgs={}
for im in j['images']:
    v=j['bufferViews'][im['bufferView']];o=v.get('byteOffset',0);I=Image.open(io.BytesIO(b[o:o+v['byteLength']])).convert('RGB');n=(im.get('name') or '').lower()
    k='emissive' if 'emissive' in n else 'normal' if 'normal' in n else 'rm' if n.endswith('_rm') or '_rm' in n else 'basecolor'
    imgs[k]=I;I.save(f'{outdir}/titan_{k}_{setname}.png')
Wd=2048;asp=imgs['basecolor'].size[1]/imgs['basecolor'].size[0];Hd=int(round(Wd*asp))
Rw,Rh=Wd//2,Hd//2;img=Image.new('F',(Rw,Rh),0);cov=Image.new('L',(Rw,Rh),0);d=ImageDraw.Draw(img);dc=ImageDraw.Draw(cov)
for f,s in zip(F,score[F].mean(1)):
    pts=[(UV[k,0]*Rw,UV[k,1]*Rh) for k in f];d.polygon(pts,fill=float(s));dc.polygon(pts,fill=255)
sc=np.array(img);cv=np.array(cov)>0;sc=np.maximum(sc,(cv&~nd.binary_erosion(cv,iterations=3))*0.75)
sc=nd.gaussian_filter(nd.grey_dilation(sc,size=5),6);sc=np.array(Image.fromarray(sc.astype(np.float32)).resize((Wd,Hd),Image.BILINEAR));sc/=sc.max()
pos=np.zeros((Hd,Wd,3));m=np.zeros((Hd,Wd),bool)
for f in F:
    u=UV[f]*[Wd,Hd];x0,y0=np.maximum(np.floor(u.min(0)).astype(int),0);x1,y1=np.minimum(np.ceil(u.max(0)).astype(int)+1,[Wd,Hd])
    if x1<=x0 or y1<=y0:continue
    yy,xx=np.mgrid[y0:y1,x0:x1]+0.5;a,b_,c=u;den=(b_[1]-c[1])*(a[0]-c[0])+(c[0]-b_[0])*(a[1]-c[1])
    if abs(den)<1e-12:continue
    l1=((b_[1]-c[1])*(xx-c[0])+(c[0]-b_[0])*(yy-c[1]))/den;l2=((c[1]-a[1])*(xx-c[0])+(a[0]-c[0])*(yy-c[1]))/den;l3=1-l1-l2
    mm=(l1>=-0.02)&(l2>=-0.02)&(l3>=-0.02)
    if mm.any():
        pp=l1[...,None]*P[f[0]]+l2[...,None]*P[f[1]]+l3[...,None]*P[f[2]];sl=(slice(y0,y1),slice(x0,x1));pos[sl][mm]=pp[mm];m[sl]|=mm
idx=nd.distance_transform_edt(~m,return_distances=False,return_indices=True);pos=pos[idx[0],idx[1]]
H=np.ptp(P[:,1]);rng=np.random.default_rng(3);G3=rng.random((64,64,64))
def vnoise(p):
    i=np.floor(p).astype(int);f=p-i;f=f*f*(3-2*f);o=0
    for dx in(0,1):
        for dy in(0,1):
            for dz in(0,1):
                w=(f[...,0] if dx else 1-f[...,0])*(f[...,1] if dy else 1-f[...,1])*(f[...,2] if dz else 1-f[...,2]);o=o+w*G3[(i[...,0]+dx)%64,(i[...,1]+dy)%64,(i[...,2]+dz)%64]
    return o
def fbm(p,o=4):
    s=0;a=1;t=0
    for k in range(o):s+=a*vnoise(p*2**k);t+=a;a*=.5
    return s/t
q=pos/H*9.0;warp=np.stack([fbm(q+11),fbm(q+23),fbm(q+37)],-1)
r1=np.abs(fbm(q+warp*1.2,4)-0.5);r2=np.abs(fbm(q*2.7+warp,3)-0.5)
w1=0.006+0.055*sc**1.2;w2=0.004+0.018*sc
vein=np.maximum(np.clip(1-r1/w1,0,1)**0.6,np.clip(1-r2/w2,0,1)**0.8*(0.35+0.65*sc))
vein=np.maximum(vein,np.clip((sc-0.7)/0.2,0,1)*np.clip((fbm(q*3+5)-0.45)*5,0,1))*nd.binary_dilation(m,iterations=4)
halo=np.clip(nd.gaussian_filter(nd.grey_dilation(vein,size=9),3)*1.5,0,1);flow=fbm(q*0.6+3,3)
em=np.array(imgs['emissive'].convert('L').resize((Wd,Hd)))/255. if 'emissive' in imgs else np.zeros((Hd,Wd))
Image.fromarray((np.clip(np.dstack([vein,halo,flow,em]),0,1)*255).astype(np.uint8),'RGBA').save(f'{outdir}/titan_lava_mask_{setname}.png')
al=np.array(imgs['basecolor'].resize((Wd,Hd))).astype(float)/255
alb=al*(1-0.8*halo[...,None])+np.array([0.05,0.04,0.035])*0.8*halo[...,None];alb=alb*(1-vein[...,None])+np.array([0.9,0.35,0.05])*vein[...,None]
Image.fromarray((np.clip(alb,0,1)*255).astype(np.uint8)).save(f'{outdir}/titan_lava_albedo_{setname}.png')
e0=np.array(imgs['emissive'].resize((Wd,Hd))).astype(float)/255 if 'emissive' in imgs else np.zeros((Hd,Wd,3))
Image.fromarray((np.maximum(e0,vein[...,None]*np.array([1.0,0.42,0.06]))*255).astype(np.uint8)).save(f'{outdir}/titan_lava_emissive_{setname}.png')
S=setname
open(f'{outdir}/titan_lava_material_{S}.tres','w').write(f'''[gd_resource type="ShaderMaterial" load_steps=6 format=3]

[ext_resource type="Shader" path="res://titan_lava.gdshader" id="1"]
[ext_resource type="Texture2D" path="res://titan_basecolor_{S}.png" id="2"]
[ext_resource type="Texture2D" path="res://titan_normal_{S}.png" id="3"]
[ext_resource type="Texture2D" path="res://titan_rm_{S}.png" id="4"]
[ext_resource type="Texture2D" path="res://titan_lava_mask_{S}.png" id="5"]

[resource]
shader = ExtResource("1")
shader_parameter/albedo_tex = ExtResource("2")
shader_parameter/normal_tex = ExtResource("3")
shader_parameter/rm_tex = ExtResource("4")
shader_parameter/lava_mask = ExtResource("5")
shader_parameter/glow_strength = 1.0
shader_parameter/flow_speed = 0.6
shader_parameter/pulse_speed = 1.4
shader_parameter/lava_hot = Color(1, 0.62, 0.16, 1)
shader_parameter/lava_cool = Color(0.75, 0.1, 0.02, 1)
shader_parameter/char_amount = 0.8
shader_parameter/base_glow = {1.0 if 'emissive' in imgs else 0.0}
shader_parameter/vein_scale = 1.0
''')
open(f'{outdir}/titan_lava_fallback_{S}.tres','w').write(f'''[gd_resource type="StandardMaterial3D" load_steps=5 format=3]

[ext_resource type="Texture2D" path="res://titan_lava_albedo_{S}.png" id="1"]
[ext_resource type="Texture2D" path="res://titan_normal_{S}.png" id="2"]
[ext_resource type="Texture2D" path="res://titan_rm_{S}.png" id="3"]
[ext_resource type="Texture2D" path="res://titan_lava_emissive_{S}.png" id="4"]

[resource]
cull_mode = 2
albedo_texture = ExtResource("1")
roughness_texture = ExtResource("3")
roughness_texture_channel = 1
normal_enabled = true
normal_texture = ExtResource("2")
emission_enabled = true
emission = Color(1, 1, 1, 1)
emission_energy_multiplier = 2.0
emission_texture = ExtResource("4")
''')
print('ok',S,Wd,Hd,(vein>0.3)[m].mean())
