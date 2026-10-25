# Re-bake round-4 hi buildings into card/realistic style: one material, one atlas (walls top half, roof bottom half).
import sys,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import numpy as np,trimesh
from PIL import Image,ImageDraw
from scipy import ndimage
T='/workspace/beth-world/www/proto3d/models/beth/textures/realmed'
def L(n,k,mode='RGB'): return np.asarray(Image.open(f'{T}/{n}_{k}').convert(mode)).astype(np.float32)/255
TEX={n:dict(a=L(n,'albedo.jpg'),n=L(n,'normal.png'),r=L(n,'rough.png','L')) for n in['fieldstone','cobblestone','slate','oak','plaster_timber']}
# plain plaster from plaster_timber's plaster panel area tiled noise
pa=TEX['plaster_timber']['a'].copy(); TEX['plaster']=dict(a=np.roll(pa,0,0),n=TEX['plaster_timber']['n'],r=TEX['plaster_timber']['r'])
def hexc(h): return np.array([int(h[i:i+2],16) for i in(1,3,5)])/255
# card tints
TINT=dict(slate=hexc('#46638F')/hexc('#4a5664'),plaster=hexc('#E6D6B8')/hexc('#d9cdb2')*0.86,oak=hexc('#4A3220')/hexc('#3a2a1d')*0.8)
# shared atlas cell categories (8x8, row 0 = top of image)
CAT=[ 'PPPCCSSK','SSSSSSSS','SSSDDDWW','WWWWWWWS','SSGGGRRR','RRRRHHRR','PPPPPPBR','RRBBBBBK']
STONEONLY={'keep','gate_tower','lighthouse','colosseum','crypt','temple','treasury','observatory','library','mage','townhall'}
def tri(tex,P,Nw,scale,upright=False):
    a=np.abs(Nw)**4; a/=a.sum(1,keepdims=True)+1e-9; S=tex['a'].shape[0]
    out={k:0 for k in'anr'}
    projs=[(P[:,[2,1]],a[:,0]),(P[:,[0,2]],a[:,1]),(P[:,[0,1]],a[:,2])]
    for uv,w in projs:
        ij=(np.floor(uv/scale*S)).astype(int)%S
        for k in'anr':
            v=tex[k][S-1-ij[:,1],ij[:,0]]
            out[k]=out[k]+(v*w[:,None] if v.ndim==2 else v*w)
    return out
def raster(uv,faces,W,H):
    im=Image.new('I',(W,H),-1); d=ImageDraw.Draw(im)
    px=np.stack([uv[:,0]*W,(1-uv[:,1])*H],1)
    for i,f in enumerate(faces): d.polygon([tuple(px[j]) for j in f],fill=i)
    return np.asarray(im)
def bake_part(g,orig,W,H,name):
    uv=g['uv']; F=g['F']; V=g['V']; VN=g['VN']; OUV=g['ouv']
    tid=raster(uv,F,W,H); m=tid>=0; yy,xx=np.nonzero(m); t=tid[m]
    px=np.stack([(xx+0.5)/W,1-(yy+0.5)/H],1); A,B,C=[uv[F[t,k]] for k in range(3)]
    v0=B-A;v1=C-A;v2=px-A; d=v0[:,0]*v1[:,1]-v1[:,0]*v0[:,1]; d[np.abs(d)<1e-12]=1e-12
    b1=(v2[:,0]*v1[:,1]-v1[:,0]*v2[:,1])/d; b2=(v0[:,0]*v2[:,1]-v2[:,0]*v0[:,1])/d; b0=1-b1-b2
    bw=np.clip(np.stack([b0,b1,b2],1),0,1)
    P=sum(V[F[t,k]]*bw[:,k:k+1] for k in range(3)); Nw=sum(VN[F[t,k]]*bw[:,k:k+1] for k in range(3)); Nw/=np.linalg.norm(Nw,axis=1,keepdims=True)+1e-9
    # original maps
    oa,on,oo,oe=orig; S=oa.shape[0]
    ou=sum(OUV[F[t,k]]*bw[:,k:k+1] for k in range(3))
    oi=np.clip(((1-ou[:,1])*S).astype(int),0,S-1); oj=np.clip((ou[:,0]*S).astype(int),0,S-1)
    O_a=oa[oi,oj];O_n=on[oi,oj];O_o=oo[oi,oj];O_e=oe[oi,oj]
    cat=np.array([CAT[r][c] for r,c in zip(oi*8//S,oj*8//S)])
    if g.get('tripo'):
        y0,y1=V[:,1].min(),V[:,1].max(); hn=(P[:,1]-y0)/(y1-y0+1e-6)
        cat=np.where(hn<0.33,'S','T'); cat[(Nw[:,1]>0.3)&(hn>0.4)]='R'; cat[(Nw[:,1]>0.7)&(hn<0.1)]='C'
        O_e=O_e*0
    if name in STONEONLY: cat[cat=='P']='S'
    if name in('barn','stables','windmill'): cat[cat=='P']='W'
    isroof=g['roof'][t]; cat[isroof&((cat=='P')|(cat=='S'))&(Nw[:,1]>0.35)]='R'
    col=O_a.copy(); nrm=np.zeros_like(O_a); nrm[:,2]=1; rough=np.full(len(t),0.8); emi=O_e.copy()
    for c,tx,sc,tn in[('S','fieldstone',3.0,None),('C','cobblestone',2.5,None),('W','oak',2.0,'oak'),('D','oak',2.0,'oak'),('R','slate',3.5,'slate'),('P','plaster',2.8,'plaster'),('T','plaster_timber',3.0,None)]:
        k=cat==c
        if not k.any(): continue
        o=tri(TEX[tx],P[k],Nw[k],sc)
        a=o['a']*(TINT[tn] if tn else 1)
        if c=='D': a=a*0.6+O_a[k]*0.4   # keep door paint/iron reading
        col[k]=a; nrm[k]=o['n']*2-1; rough[k]=o['r']
    k=cat=='G'; col[k]=hexc('#E0A040')*(0.6+0.4*O_a[k].mean(1,keepdims=True)); rough[k]=0.25
    emi[k]=np.maximum(emi[k],hexc('#FFB24A')*0.9)
    k=cat=='B'; col[k]=np.where(O_a[k,0:1]>O_a[k,2:3],hexc('#8A2A22'),hexc('#203552'))*(0.8+0.3*O_a[k].mean(1,keepdims=True)); rough[k]=0.9
    k=cat=='H'; col[k]=O_a[k]*0.85
    # weathering: dirt + moss at base, rain streaks, height/normal variation
    y=P[:,1]; vert=np.abs(Nw[:,1])<0.5; rr=np.random.default_rng(0)
    dirt=np.clip(1-y/1.2,0,1)*vert
    mn=np.sin(P[:,0]*1.7+P[:,2]*1.3)*0.5+0.5
    col=col*(1-0.45*dirt[:,None])+dirt[:,None]*0.45*np.where(mn[:,None]>0.5,hexc('#4E5A2A'),hexc('#3B3226'))
    streak=(np.sin(P[:,0]*9.1+np.sin(P[:,2]*3.3)*2)*np.sin(P[:,2]*7.7)*0.5+0.5)**6
    sk=vert&np.isin(cat,['P','S','T']); col[sk]*=(1-0.18*streak[sk])[:,None]
    rough=np.clip(rough+0.1*dirt,0,1)
    # roof edge moss
    rk=(cat=='R'); col[rk]*=(0.9+0.15*np.clip(P[rk,1]%3/3,0,1))[:,None]
    # combine normals: original (tangent) + detail (whiteout)
    on2=O_n*2-1; dn=nrm
    nn=np.stack([on2[:,0]+dn[:,0],on2[:,1]+dn[:,1],on2[:,2]*dn[:,2]],1); nn/=np.linalg.norm(nn,axis=1,keepdims=True)+1e-9
    ao=O_o[:,0]*(1-0.35*dirt)
    out=dict(a=col,n=nn*0.5+0.5,o=np.stack([ao,rough,np.zeros_like(ao)],1),e=emi)
    imgs={}
    for kk,v in out.items():
        img=np.zeros((H,W,3),np.float32); img[yy,xx]=np.clip(v,0,1)
        imgs[kk]=img
    # pad: fill empty texels from nearest baked
    _,ind=ndimage.distance_transform_edt(~m,return_indices=True)
    for kk in imgs: imgs[kk]=imgs[kk][ind[0],ind[1]]
    return imgs
def run(src,dst,res):
    import xatlas
    s=trimesh.load(src); name=os.path.basename(src).split('.')[0].replace('bld_','').split('_lod')[0]
    gs=[(n,s.geometry[n]) for n in['walls','roof'] if n in s.geometry] or [(n,g) for n,g in s.geometry.items()]
    TRIPO=('walls' not in s.geometry)
    mt=gs[0][1].visual.material; rs=lambda im:np.ones((1024,1024,3),np.float32) if im is None else np.asarray(im.convert('RGB').resize((1024,1024)),np.float32)/255
    orig=(rs(mt.baseColorTexture),np.full((1024,1024,3),[0.5,0.5,1.0],np.float32),rs(mt.occlusionTexture or mt.metallicRoughnessTexture),rs(mt.emissiveTexture) if mt.emissiveTexture is not None else np.zeros((1024,1024,3),np.float32))
    V=[];F=[];UV=[];ROOF=[];off=0
    for n,g in gs:
        V.append(g.vertices);F.append(g.faces+off);UV.append(g.visual.uv);ROOF.append(np.full(len(g.faces),n=='roof'));off+=len(g.vertices)
    V=np.concatenate(V);F=np.concatenate(F);UV=np.concatenate(UV);ROOF=np.concatenate(ROOF)
    VN=trimesh.Trimesh(V,F,process=False).vertex_normals.copy()
    po=xatlas.PackOptions(); po.resolution=res; po.padding=3; po.bilinear=True
    atl=xatlas.Atlas(); atl.add_mesh(V.astype(np.float32),F.astype(np.uint32)); atl.generate(pack_options=po)
    vmap,F2,uv2=atl[0]
    g=dict(tripo=TRIPO,V=V[vmap],F=F2.astype(np.int64),uv=uv2,ouv=UV[vmap],VN=VN[vmap],roof=ROOF)
    Wm=int(res*0.9); imgs=bake_part(g,orig,Wm,res,name)
    ban=np.asarray(Image.open(f'{T}/banner_lion_albedo.jpg').convert('RGB').resize((res-Wm,(res-Wm)*2)),np.float32)/255
    for k in imgs:
        full=np.zeros((res,res,3),np.float32); full[:,:Wm]=imgs[k]
        full[:,Wm:]={'a':0,'n':np.array([0.5,0.5,1.0]),'o':np.array([1.0,0.85,0.0]),'e':0}[k]
        if k=='a': full[:,Wm:]=hexc('#4A3220'); full[:ban.shape[0],Wm:]=ban
        imgs[k]=full
    Vn=g['V'];Fn=g['F'];uvn=uv2.copy(); uvn[:,0]*=Wm/res
    # lion banners on the front facade (raycast to wall), cheap quads
    if name not in('colosseum','crypt','windmill','barn','lighthouse'):
        tm=trimesh.Trimesh(V,F,process=False); lo,hi=V.min(0),V.max(0); bw,bh=1.4,2.8
        u0=Wm/res; vb=1-ban.shape[0]/res
        for fx in(-0.28,0.28):
            x=lo[0]+(hi[0]-lo[0])*(0.5+fx); yb=min(5.5,hi[1]*0.55)
            Tr=V[F]; a,b,c=Tr[:,0],Tr[:,1],Tr[:,2]; p=np.array([x,yb])
            d=(b[:,1]-c[:,1])*(a[:,0]-c[:,0])+(c[:,0]-b[:,0])*(a[:,1]-c[:,1]); d[np.abs(d)<1e-9]=1e-9
            l1=((b[:,1]-c[:,1])*(p[0]-c[:,0])+(c[:,0]-b[:,0])*(p[1]-c[:,1]))/d; l2=((c[:,1]-a[:,1])*(p[0]-c[:,0])+(a[:,0]-c[:,0])*(p[1]-c[:,1]))/d; l3=1-l1-l2
            ins=(l1>=0)&(l2>=0)&(l3>=0)
            if not ins.any(): continue
            z=(l1*a[:,2]+l2*b[:,2]+l3*c[:,2])[ins].max()+0.12
            q=np.array([[x-bw/2,yb+bh/2,z],[x+bw/2,yb+bh/2,z],[x+bw/2,yb-bh/2,z+0.05],[x-bw/2,yb-bh/2,z+0.05]])
            qu=np.array([[u0,1],[1,1],[1,vb],[u0,vb]])
            b0=len(Vn); Vn=np.concatenate([Vn,q,q]); uvn=np.concatenate([uvn,qu,qu])
            Fn=np.concatenate([Fn,[[b0,b0+3,b0+2],[b0,b0+2,b0+1],[b0+4,b0+5,b0+6],[b0+4,b0+6,b0+7]]])
    g['V'],g['F']=Vn,Fn; uv2=uvn
    toI=lambda a:Image.fromarray((np.clip(a,0,1)*255).astype(np.uint8))
    mat=trimesh.visual.material.PBRMaterial(name=name+'_card',baseColorTexture=toI(imgs['a']),normalTexture=toI(imgs['n']),
        metallicRoughnessTexture=toI(imgs['o']),occlusionTexture=toI(imgs['o']),emissiveTexture=toI(imgs['e']),emissiveFactor=[1,1,1],metallicFactor=1.0,roughnessFactor=1.0)
    from glbw import write_glb
    Nv=trimesh.Trimesh(g['V'],g['F'],process=False).vertex_normals.copy()
    # keep smooth normals from source where available (banner verts get face normals)
    nb=len(VN[vmap]); Nv[:nb]=VN[vmap]
    write_glb(dst,g['V'],g['F'],uv2,Nv,imgs,name+'_card')
    return imgs
if __name__=='__main__':
    src,dst,res=sys.argv[1],sys.argv[2],int(sys.argv[3]); a=run(src,dst,res)
    if len(sys.argv)>4: Image.fromarray((np.clip(a['a'],0,1)*255).astype(np.uint8)).save(sys.argv[4])
