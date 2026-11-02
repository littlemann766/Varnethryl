"""Beth land1 scatter: biome trees/rocks/props per region, chunked 256 m, High + lod1 (<=50%) + trunk/boulder colliders.
Seated on the land1 High terrain; avoids props (4 m), docks, POIs, routes, bridges (grids from build_land), steep and shore ground."""
import sys,os,json,numpy as np,trimesh
sys.path.insert(0,os.path.dirname(__file__)); sys.path.insert(0,'/tmp/land2w')
from glbio import write_glb
from noise import fbm
from files import G,REG,files,is_terrain
OUT=sys.argv[1]; rng=np.random.default_rng(7)
CELL=2.0; X0,Z0,NX=-3300.0,-3300.0,3300
def gidx(xz): return np.clip(((xz-[X0,Z0])/CELL).astype(int),0,NX-1)
# ---------- primitive builders (V,F,C)
def ring(r,y,n,ph=0,jit=0):
    a=np.linspace(0,2*np.pi,n,endpoint=False)+ph; rr=r*(1+jit*(rng.random(n)-0.5))
    return np.stack([np.cos(a)*rr,np.full(n,y),np.sin(a)*rr],1)
def loft(rings,cols,cap_top=True):
    V=np.concatenate(rings); n=len(rings[0]); F=[]; C=np.concatenate([np.tile(c,(n,1)) for c in cols])
    for k in range(len(rings)-1):
        for i in range(n):
            a=k*n+i; b=k*n+(i+1)%n; c=a+n; d=b+n; F+= [[a,c,b],[b,c,d]]
    if cap_top:
        V=np.vstack([V,[[rings[-1][:,0].mean(),rings[-1][0,1],rings[-1][:,2].mean()]]]); C=np.vstack([C,cols[-1]]); t=len(V)-1; o=(len(rings)-1)*n
        F+=[[o+i,t,o+(i+1)%n] for i in range(n)]
    return V,np.array(F),C
def cone(r,y0,h,n,col,tip=None):
    V=np.vstack([ring(r,y0,n,rng.random()*6,0.25),[[0,y0+h,0]]]); C=np.vstack([np.tile(col,(n,1)),tip if tip is not None else col])
    F=[[i,n,(i+1)%n] for i in range(n)]+[[i,(i+1)%n,n+1] for i in range(0)]
    # underside
    V=np.vstack([V,[[0,y0+h*0.12,0]]]); C=np.vstack([C,np.array(col)*0.6]); F+=[[i,(i+1)%n,n+1] for i in range(n)]
    return V,np.array(F),C
def blob(r,sub,col,sq=(1,1,1),jit=0.25,dark=0.75):
    s=trimesh.creation.icosphere(subdivisions=sub); V=np.array(s.vertices)
    V=V*(1+jit*(fbm(V*1.7+rng.random(3)*50,2)))[:,None]; V*=np.array(sq)*r
    sh=np.clip((V[:,1]/(r*sq[1])+1)/2,0,1)[:,None]; C=np.array(col)*(dark+(1-dark)*sh)
    return V,np.array(s.faces),C
def merge(parts):
    V=[];F=[];C=[];o=0
    for v,f,c in parts: V.append(v);F.append(f+o);C.append(c);o+=len(v)
    return np.concatenate(V),np.concatenate(F),np.concatenate(C)
def tr(p,s=1.0,y=0.0,dy=0.0,tilt=(0,0)):
    v,f,c=p; ca,sa=np.cos(y),np.sin(y); R=np.array([[ca,0,-sa],[0,1,0],[sa,0,ca]])
    v=v@R.T*s; v[:,0]+=v[:,1]*tilt[0]; v[:,2]+=v[:,1]*tilt[1]; v=v+[0,dy,0]; return v,f,c
BARK=np.array([0.24,0.17,0.11]); PINE=np.array([0.11,0.22,0.12]); LEAF=np.array([0.2,0.34,0.13])
def pine(hi,snow=False,tone=1.0):
    n=7 if hi else 5; h=rng.uniform(7,13); P=[loft([ring(0.28,-0.4,n),ring(0.12,h*0.5,n)],[BARK,BARK*1.1],False)]
    lv=4 if hi else 2; col=PINE*tone*rng.uniform(0.85,1.15)
    for k in range(lv):
        t=k/lv; r=(1-t)*h*0.26+0.6; y=h*(0.22+0.7*t)
        P.append(cone(r,y,h*(0.42 if hi else 0.55)*(1-t*0.3),n+1,col*(0.85+0.2*t),tip=np.array([0.9,0.93,0.97]) if snow else None))
        if snow: P[-1]=(P[-1][0],P[-1][1],np.where((P[-1][0][:,1]>y+0.3)[:,None],np.array([0.88,0.92,0.97]),P[-1][2]))
    return merge(P),h
def broadleaf(hi,tone=1.0):
    n=6 if hi else 5; h=rng.uniform(5,8); P=[loft([ring(0.35,-0.4,n),ring(0.2,h*0.6,n)],[BARK,BARK],False)]
    col=LEAF*tone*rng.uniform(0.8,1.2)
    for k in range(3 if hi else 1):
        o=rng.normal(0,0.9,3)*[1,0.4,1] if k else np.zeros(3); v,f,c=blob(rng.uniform(1.8,2.6),1,col,(1,0.8,1))
        P.append((v+[o[0],h*0.75+o[1],o[2]],f,c))
    if not hi: P=[P[0]]+[(lambda b_: (b_[0]+[0,h*0.75,0],b_[1],b_[2]))(blob(2.6,0,col,(1,0.8,1)))]
    return merge(P),h
def deadtree(hi):
    n=5 if hi else 4; h=rng.uniform(4,7); B=np.array([0.12,0.1,0.09]); P=[loft([ring(0.3,-0.4,n),ring(0.08,h,n)],[B,B*1.3])]
    for k in range(4 if hi else 2):
        a=rng.random()*6.28; y=h*rng.uniform(0.4,0.85); L=rng.uniform(1,2.2); d=np.array([np.cos(a),0.7,np.sin(a)])
        v,f,c=loft([ring(0.09,0,4),ring(0.03,L,4)],[B,B]); v2=v.copy(); v2[:,0]+=v[:,1]*d[0]; v2[:,2]+=v[:,1]*d[2]; v2[:,1]*=d[1]; P.append((v2+[0,y,0],f,c))
    return merge(P),h
def rock(hi,col,big=False):
    r=rng.uniform(1.2,2.6) if big else rng.uniform(0.35,0.9)
    v,f,c=blob(r,(2 if big else 1) if hi else 0,col*rng.uniform(0.85,1.15),(1,rng.uniform(0.5,0.8),rng.uniform(0.8,1.2)),0.45,0.6)
    return (v-[0,r*0.25,0],f,c),r
def crystal(hi,col,glint):
    P=[]
    for k in range(rng.integers(3,6) if hi else 2):
        h=rng.uniform(0.8,2.6); n=6 if hi else 4; v,f,c=cone(rng.uniform(0.15,0.35),-0.2,h,n,col,tip=glint)
        P.append(tr((v,f,c),1,rng.random()*6,0,(rng.normal(0,0.35),rng.normal(0,0.35))))
    return merge(P),2.5
def column(hi):
    P=[]; B=np.array([0.045,0.045,0.05])
    for k in range(rng.integers(3,7) if hi else 3):
        h=rng.uniform(1.2,4.5); n=6 if hi else 5; v,f,c=loft([ring(0.45,-0.3,n),ring(0.45,h,n)],[B,B*1.25]); P.append((v+[rng.normal(0,0.7),0,rng.normal(0,0.7)],f,c))
    return merge(P),2.0
def bush(hi,col):
    v,f,c=blob(rng.uniform(0.6,1.2),1 if hi else 0,col*rng.uniform(0.8,1.2),(1,0.7,1),0.4); return (v+[0,0.3,0],f,c),1.0
def tuft(hi,col):
    P=[]
    for k in range(5 if hi else 2):
        v,f,c=cone(0.12,-0.05,rng.uniform(0.4,0.8),3,col*rng.uniform(0.8,1.25),tip=col*1.5); P.append(tr((v,f,c),1,rng.random()*6,0,(rng.normal(0,0.3),rng.normal(0,0.3))))
        P[-1]=(P[-1][0]+[rng.normal(0,0.25),0,rng.normal(0,0.25)],P[-1][1],P[-1][2])
    return merge(P),0.5
SPEC={  # region -> list of (name, weight, builder(hi)->((V,F,C),size), tree?, min_y, max_slope)
 'A':[('pine',30,lambda hi:pine(hi),1,2.5,26),('oak',22,lambda hi:broadleaf(hi),1,2.5,22),('bush',25,lambda hi:bush(hi,np.array([0.16,0.28,0.12])),0,1.5,30),
      ('boulder',8,lambda hi:rock(hi,np.array([0.4,0.39,0.36]),True),2,1.0,40),('stones',15,lambda hi:rock(hi,np.array([0.42,0.4,0.37])),0,0.5,40),('tuft',40,lambda hi:tuft(hi,np.array([0.2,0.36,0.12])),0,1.5,30)],
 'B':[('shore_pine',18,lambda hi:pine(hi,tone=0.9),1,4.0,24),('scrub',30,lambda hi:bush(hi,np.array([0.3,0.33,0.16])),0,2.0,30),('salt_crystal',16,lambda hi:crystal(hi,np.array([0.75,0.88,0.9]),np.array([0.97,1,1])),0,1.0,35),
      ('boulder',12,lambda hi:rock(hi,np.array([0.6,0.58,0.53]),True),2,1.0,40),('stones',24,lambda hi:rock(hi,np.array([0.64,0.62,0.57])),0,0.5,40),('dune_grass',30,lambda hi:tuft(hi,np.array([0.45,0.45,0.22])),0,1.0,30)],
 'frost':[('snow_pine',34,lambda hi:pine(hi,snow=True,tone=0.85),1,3.0,26),('ice_shard',14,lambda hi:crystal(hi,np.array([0.6,0.78,0.9]),np.array([0.92,0.97,1])),0,1.0,38),
      ('boulder',16,lambda hi:rock(hi,np.array([0.55,0.6,0.66]),True),2,1.0,40),('stones',20,lambda hi:rock(hi,np.array([0.6,0.64,0.7])),0,0.5,40),('dead_tree',8,lambda hi:deadtree(hi),1,3.0,24)],
 'ash':[('lava_rocks',22,lambda hi:rock(hi,np.array([0.22,0.08,0.04]),True),2,1.0,40),('sulfur',12,lambda hi:crystal(hi,np.array([0.75,0.62,0.12]),np.array([0.95,0.85,0.3])),0,1.0,38),
      ('ash_grass',30,lambda hi:tuft(hi,np.array([0.13,0.12,0.09])),0,1.5,30),('cinders',30,lambda hi:rock(hi,np.array([0.035,0.03,0.03])),0,0.5,40),
      ('dead_tree',20,lambda hi:deadtree(hi),1,3.0,24),('basalt',20,lambda hi:column(hi),2,1.0,38),('obsidian',14,lambda hi:crystal(hi,np.array([0.06,0.05,0.07]),np.array([0.25,0.2,0.3])),0,1.0,38),
      ('boulder',16,lambda hi:rock(hi,np.array([0.06,0.055,0.055]),True),2,1.0,40),('stones',30,lambda hi:rock(hi,np.array([0.075,0.068,0.064])),0,0.5,40)]}
DENS={'A':1/220,'B':1/420,'frost':1/650,'ash':1/70}   # instances per m2 of eligible land (before forest-noise thinning)
def main():
    stats={}
    for r,(d,pre) in REG.items():
        g=np.load(f'/tmp/land2w/grids_{r}.npz'); props=np.unpackbits(g['props'])[:NX*NX].reshape(NX,NX).astype(bool); keep=np.unpackbits(g['keep'])[:NX*NX].reshape(NX,NX).astype(bool)
        # dilate keep/props by 3 m for scatter
        from scipy.ndimage import binary_dilation
        block=binary_dilation(props|keep,iterations=2)
        ms=[]
        for f in files(r):
            b=f.split('/')[-1][:-4]
            if not is_terrain(b): continue
            p='/tmp/land2o/'+f; s=trimesh.load(p,force='mesh',process=False)
            a=np.array(s.visual.vertex_colors)[:,3] if s.visual.kind=='vertex' else None
            ms.append((s,b))
        # sample points on terrain faces (alpha terrain), area weighted
        pts=[];nrm=[];isl_cover=np.unpackbits(g['isl'])[:NX*NX].reshape(NX,NX).astype(bool)
        for s,b in ms:
            A=np.array(s.visual.vertex_colors)[:,3]>127; fm=A[s.faces].all(1)
            area=s.area_faces*fm; n=int(area.sum()*DENS[r]*3)
            if n==0: continue
            fi=rng.choice(len(area),n,p=area/area.sum()); u=rng.random((n,2)); m=u.sum(1)>1; u[m]=1-u[m]
            T=s.vertices[s.faces[fi]]; P=T[:,0]+(T[:,1]-T[:,0])*u[:,:1]+(T[:,2]-T[:,0])*u[:,1:]
            N=s.face_normals[fi]
            if '_isl_' not in b: 
                ok=~isl_cover[tuple(gidx(P[:,[0,2]]).T)]; P=P[ok]; N=N[ok]   # island patches have their own scatter + sit above the base
            pts.append(P); nrm.append(N)
        P=np.concatenate(pts); N=np.concatenate(nrm); sl=np.degrees(np.arccos(np.clip(np.abs(N[:,1]),0,1)))
        ok=~block[tuple(gidx(P[:,[0,2]]).T)]; small_ok=~binary_dilation(props,iterations=1)[tuple(gidx(P[:,[0,2]]).T)]
        forest=fbm(P[:,[0,2,1]]*[1/120,1/120,0],3,r.__len__()*5)   # groves vs clearings
        keepp=rng.random(len(P))<np.clip(0.15+ (forest+0.1)*1.6,0.05,1.0)
        m_=(ok|small_ok)&keepp; okk=ok[m_]
        P=P[m_]; sl=sl[m_]; forest=forest[m_]
        sp=SPEC[r]; W=np.array([s_[1] for s_ in sp],float); W/=W.sum()
        kind=rng.choice(len(sp),len(P),p=W)
        sel=np.array([P[i,1]>=sp[k][4] and sl[i]<=sp[k][5] and (okk[i] or sp[k][3]==0) for i,k in enumerate(kind)],bool)   # land2: small no-collider detail may sit by paths
        # trees mostly in groves
        tree=np.array([sp[k][3]==1 for k in kind]); sel&=~(tree&(forest<-0.05))
        P,kind=P[sel],kind[sel]
        # min spacing 3.5 m
        from scipy.spatial import cKDTree
        kd=cKDTree(P[:,[0,2]]); drop=np.zeros(len(P),bool)
        for i,j in kd.query_pairs(2.6):
            if not drop[i] and not drop[j]: drop[j]=True
        P,kind=P[~drop],kind[~drop]
        # build chunks
        ch=np.floor(P[:,[0,2]]/256).astype(int); keys=np.unique(ch,axis=0); od=OUT+'/'+d; os.makedirs(od,exist_ok=True)
        tot=[0,0,0]; cnt={}
        for key in keys:
            ii=np.nonzero((ch==key).all(1))[0]; H=[];Lo=[];Co=[]
            for i in ii:
                k=kind[i]; seed=int(rng.integers(1<<30)); yaw=rng.random()*6.283; sc=rng.uniform(0.8,1.25)
                for hi,dst in ((True,H),(False,Lo)):
                    globals()['rng']=np.random.default_rng(seed); (v,f,c),size=sp[k][2](hi)
                    v,f,c=tr((v,f,c),sc,yaw); dst.append((v+P[i]-[0,0.15,0],f,c))
                cnt[sp[k][0]]=cnt.get(sp[k][0],0)+1
                if sp[k][3]>=1:   # collider: trunk / boulder box
                    w=0.5 if sp[k][3]==1 else 1.4*sc
                    bx=trimesh.creation.box([w,3.0,w]); Co.append((np.array(bx.vertices)+P[i]+[0,1.2,0],np.array(bx.faces),np.zeros((8,3))))
            globals()['rng']=np.random.default_rng(int(abs(key[0])*1000+abs(key[1])))
            nm=f'{pre}land_scatter_c{key[0]+20:02d}_{key[1]+20:02d}'
            for parts,suf in ((H,''),(Lo,'_lod1')):
                V,F,C=merge(parts); write_glb(od+nm+suf+'.glb',V,F,np.hstack([C,np.zeros((len(C),1))]),None,nm+suf)
                tot[0 if suf=='' else 1]+=len(F)
            if Co:
                V,F,C=merge(Co); write_glb(od+nm+'_col.glb',V,F,np.hstack([C,np.zeros((len(C),1))]),None,nm+'_col'); tot[2]+=len(F)
        stats[r]=dict(instances=int(len(P)),by_kind=cnt,chunks=int(len(keys)),tris_high=tot[0],tris_lod1=tot[1],lod1_pct=round(100*tot[1]/max(tot[0],1),1),col_tris=tot[2])
        print(r,stats[r],flush=True)
    json.dump(stats,open(OUT+'/scatter_stats.json','w'),indent=1)
main()
