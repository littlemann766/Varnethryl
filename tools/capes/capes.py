from mathutils import Quaternion
import bpy,sys,math,json,os,colorsys
import numpy as np
from mathutils import Vector,Matrix
a=sys.argv[sys.argv.index('--')+1:]; name=a[0]; R=int(a[1]); Cn=int(a[2]); only=a[3].split(',') if len(a)>3 and a[3] else None
OUT=f'/workspace/capes/out/{name}'
src=OUT+'.stage1.blend'
if not os.path.exists(src): src=f'/workspace/mocap/out/{name}.blend'
bpy.ops.wm.open_mainfile(filepath=src); sc=bpy.context.scene; sc.render.fps=30; sc.render.fps_base=1
arm=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]
ob=[o for o in bpy.data.objects if o.type=='MESH' and o.parent==arm and len(o.data.vertices)>1000][0]
TB=arm.data.bones; MIX='mixamorig:Hips' in TB
P='mixamorig:' if MIX else ''
def bn(k):
    m={'anchor':('Spine2','upperChest' if 'upperChest' in TB else 'chest'),'hips':('Hips','hips'),'neck':('Neck','neck'),
       'thL':('LeftUpLeg','thigh_L'),'thR':('RightUpLeg','thigh_R'),'shL':('LeftLeg','shin_L'),'shR':('RightLeg','shin_R'),'ftL':('LeftFoot','foot_L'),'ftR':('RightFoot','foot_R'),'spine':('Spine','spine')}
    x=m[k]; return P+x[0] if MIX else x[1]
ANCH=bn('anchor')
me=ob.data; S=0.018
gn={g.index:g.name for g in ob.vertex_groups}
# palette
img=[n.image for n in ob.active_material.node_tree.nodes if n.type=='TEX_IMAGE'][0]
Wd,Hd=img.size; pal=np.array(img.pixels[:]).reshape(Hd,Wd,4)
uvl=me.uv_layers.active.data
SPEC=json.load(open('/workspace/capes/spec.json'))[name]
if 'capeV_c0_r0' not in TB:
    # ---------- stage 1: build cape bones + reassign cubes
    cubes={}  # key -> dict(faces, center, color, group)
    for p in me.polygons:
        if p.area<(S*S*0.8): continue  # head cubes are smaller; skip
        c=p.center-p.normal*(S/2)
        k=tuple(int(round(x/(S/2))) for x in c)
        d=cubes.setdefault(k,{'f':[],'c':ob.matrix_world@c,'g':gn[me.vertices[p.vertices[0]].groups[0].group]})
        d['f'].append(p.index)
        if 'col' not in d:
            uv=uvl[p.loop_indices[0]].uv; d['col']=pal[int(uv.y*Hd)%Hd,int(uv.x*Wd)%Wd,:3]
    hipsY=(arm.matrix_world@TB[bn('hips')].head_local).y
    neckZ=(arm.matrix_world@TB[bn('neck')].head_local).z
    def iscape(d):
        if SPEC['mode']=='group': return d['g'].startswith('cape') and d['c'].y>hipsY+SPEC.get('behind',-9)
        h,l,s=colorsys.rgb_to_hls(*d['col'])
        hr=SPEC['hue']
        okc=(h<hr[1] or h>hr[0]) if hr[0]>hr[1] else (hr[0]<h<hr[1])
        return okc and s>SPEC.get('sat',0.25) and d['c'].y>hipsY+SPEC.get('behind',0.04) and d['c'].z<neckZ and d['g'] in [P+x for x in ('Hips','Spine','Spine1','Spine2')]
    cape=[d for d in cubes.values() if iscape(d)]
    if SPEC.get('cc',SPEC['mode']!='group'):
        ks={k for k,d in cubes.items() if iscape(d)}; seen=set(); comps=[]
        for k0 in ks:
            if k0 in seen: continue
            st_=[k0]; seen.add(k0); comp=[]
            while st_:
                k=st_.pop(); comp.append(k)
                for dx in (-2,0,2):
                    for dy in (-2,0,2):
                        for dz in (-2,0,2):
                            n_=(k[0]+dx,k[1]+dy,k[2]+dz)
                            if n_ in ks and n_ not in seen: seen.add(n_); st_.append(n_)
            comps.append(comp)
        comps.sort(key=len,reverse=True); keep=set(comps[0])
        for c_ in comps[1:]:
            if len(c_)>=0.15*len(comps[0]): keep|=set(c_)
        print('components',len(comps),'kept',len(keep),'of',len(ks))
        cape=[cubes[k] for k in keep]
    print('cape cubes',len(cape))
    pts=np.array([list(d['c']) for d in cape])
    ztop=min(pts[:,2].max(), (arm.matrix_world@TB[ANCH].head_local).z+SPEC.get('topoff',0.12)); zbot=pts[:,2].min()
    xmin,xmax=np.percentile(pts[:,0],2),np.percentile(pts[:,0],98)
    rows=[ztop-(ztop-zbot)*r/R for r in range(R+1)]
    J=[[None]*(R+1) for _ in range(Cn)]
    for c in range(Cn):
        x0=xmin+(xmax-xmin)*c/Cn; x1=xmin+(xmax-xmin)*(c+1)/Cn; xc=(x0+x1)/2
        for r in range(R+1):
            sel=pts[(abs(pts[:,2]-rows[r])<(ztop-zbot)/R*0.6)&(pts[:,0]>=x0-0.02)&(pts[:,0]<=x1+0.02)]
            y=float(np.percentile(sel[:,1],70)) if len(sel) else (J[c][r-1].y if r else float(pts[:,1].mean()))
            J[c][r]=Vector((xc,y,rows[r]))
    bpy.context.view_layer.objects.active=arm; bpy.ops.object.mode_set(mode='EDIT')
    eb=arm.data.edit_bones; inv=arm.matrix_world.inverted()
    for c in range(Cn):
        for r in range(R):
            b=eb.new(f'capeV_c{c}_r{r}'); b.head=inv@J[c][r]; b.tail=inv@J[c][r+1]
            xdir=(J[min(c+1,Cn-1)][r]-J[max(c-1,0)][r]).normalized() if Cn>1 else Vector((1,0,0))
            b.align_roll(inv.to_3x3()@Vector((0,-1,0)).cross(xdir) if False else inv.to_3x3()@ (xdir.cross((J[c][r+1]-J[c][r]).normalized())))
            b.parent=eb[ANCH] if r==0 else eb[f'capeV_c{c}_r{r-1}']; b.use_connect=r>0; b.use_deform=True
    bpy.ops.object.mode_set(mode='OBJECT')
    # reassign cape cubes
    for c in range(Cn):
        for r in range(R): ob.vertex_groups.new(name=f'capeV_c{c}_r{r}')
    VG={g.name:g for g in ob.vertex_groups}
    for d in cape:
        x,z=d['c'].x,d['c'].z
        c=min(Cn-1,max(0,int((x-xmin)/(xmax-xmin)*Cn)))
        r=min(R-1,max(0,int((ztop-z)/(ztop-zbot)*R)))
        vs=[v for f in d['f'] for v in me.polygons[f].vertices]
        for g in list(VG.values()):
            if g.name!=f'capeV_c{c}_r{r}': g.remove(vs)
        VG[f'capeV_c{c}_r{r}'].add(vs,1.0,'REPLACE')
    hipsZ=(arm.matrix_world@TB[bn('hips')].head_local).z
    if SPEC['mode']=='group':
        capeset=set(id(d) for d in cape)
        for g in ('anchor','hips'): ob.vertex_groups.get(bn(g)) or ob.vertex_groups.new(name=bn(g))
        VG={g.name:g for g in ob.vertex_groups}
        nside=0
        for d in cubes.values():
            if d['g'].startswith('cape') and id(d) not in capeset:
                tgt=bn('anchor') if d['c'].z>=hipsZ else bn('hips')
                vs=[v for f in d['f'] for v in me.polygons[f].vertices]
                VG[d['g']].remove(vs); VG[tgt].add(vs,1.0,'REPLACE'); nside+=1
        print('side cubes ->body',nside)
    json.dump({'J':[[list(p) for p in col] for col in J],'ncape':len(cape)},open(OUT+'.grid.json','w'))
    bpy.ops.wm.save_as_mainfile(filepath=OUT+'.stage1.blend')
    print('STAGE1 saved')
# ---------- stage 2: simulate & bake per clip
for md in ob.modifiers: md.show_viewport=False
G=json.load(open(OUT+'.grid.json')); J=[[Vector(p) for p in col] for col in G['J']]
pbA=arm.pose.bones[ANCH]
restA=arm.matrix_world@TB[ANCH].matrix_local
loc0=[[restA.inverted()@J[c][r] for r in range(R+1)] for c in range(Cn)]
L=[[(J[c][r+1]-J[c][r]).length for r in range(R)] for c in range(Cn)]
LX=[[(J[c+1][r]-J[c][r]).length for r in range(R+1)] for c in range(Cn-1)]
caps=[(bn('hips'),bn('spine'),None),(bn('spine'),ANCH,None),(bn('hips'),bn('neck'),None),(bn('thL'),bn('shL'),None),(bn('thR'),bn('shR'),None),(bn('shL'),bn('ftL'),None),(bn('shR'),bn('ftR'),None)]
# radii from rest mesh of non-cape verts near each segment
co=np.array([list(arm.matrix_world@v.co) for v in list(me.vertices)[::7]])
gidx=np.array([v.groups[0].group if v.groups else -1 for v in list(me.vertices)[::7]])
noncape=np.array([not gn.get(g,'').startswith('cape') and 'Arm' not in gn.get(g,'') and 'arm' not in gn.get(g,'') and 'hand' not in gn.get(g,'').lower() for g in gidx])
def segd(Pp,A,B):
    ab=B-A; t=np.clip(((Pp-A)@ab)/(ab@ab),0,1); return np.linalg.norm(Pp-(A+t[:,None]*ab),axis=1),t
MARG0=SPEC.get('margin',0.045)
RAD=[]
TORSO=[bn('hips'),bn('spine')]+[x for x in (P+'Spine1',P+'Spine2','spine2','chest','upperChest') if x in TB]
gnames=np.array([gn.get(g,'') for g in gidx])
for a_,b_,_ in caps:
    A=np.array(arm.matrix_world@TB[a_].head_local); B=np.array(arm.matrix_world@TB[b_].head_local)
    own=np.isin(gnames,TORSO if a_ in (bn('hips'),bn('spine')) else [a_])
    d,t=segd(co[own],A,B); m=(t>0.05)&(t<0.95)
    rr=float(np.percentile(d[m],70)) if m.sum()>20 else 0.07
    jp=np.array([list(J[c][r]) for c in range(Cn) for r in range(1,R+1)])
    dj,tj=segd(jp,A,B)
    rr=min(rr,float(dj.min())-MARG0)
    RAD.append(max(0.03,rr))
RC={}
for k_,(a_,b_,_) in enumerate(caps[:2]):
    A=arm.matrix_world@TB[a_].head_local; B=arm.matrix_world@TB[b_].head_local
    for c in range(Cn):
        for r in range(1,R+1):
            p=J[c][r]; AB=B-A; t=max(0,min(1,(p-A).dot(AB)/max(AB.length_squared,1e-9))); RC[(k_,c,r)]=(p-(A+AB*t)).length
print('RADII',[round(r,3) for r in RAD])
SPEC.setdefault('wind',{})
sp=json.load(open(f'/workspace/mocap/out/{name}.speeds.json'))
LOOP=lambda n:any(n.startswith(x) for x in ('walk','run','idle','fly','saber_ready'))
def wind_for(n):
    if n in ('walk','run','walk_saber','run_saber'): return Vector((0,sp.get(n.split('_')[0],{'speed_mps':1.0})['speed_mps'],0))
    if n in ('fly_forward','fly_bank_L','fly_bank_R'): return Vector((0,9,0))
    if n=='fly_fast': return Vector((0,15,0))
    if n=='fly_ascend': return Vector((0,3,-7))
    if n=='fly_descend': return Vector((0,2,6))
    if n=='fly_hover': return Vector((0,1.5,0))
    return Vector((0,0,0))
def frames_world(act):
    arm.animation_data.action=act; f0,f1=[int(round(x)) for x in act.frame_range]
    out=[]
    for f in range(f0,f1+1):
        sc.frame_set(f)
        Am=arm.matrix_world@pbA.matrix
        segs=[((arm.matrix_world@arm.pose.bones[a_].head).copy(),(arm.matrix_world@arm.pose.bones[b_].head).copy()) for a_,b_,_ in caps]
        out.append((Am.copy(),segs))
    return out,f0,f1
MARG=SPEC.get('margin',0.045)
def simulate(FW,wind,loop,cycles):
    n=len(FW)-1 if loop else len(FW)
    pos=[[FW[0][0]@loc0[c][r] for r in range(R+1)] for c in range(Cn)]
    prev=[[p.copy() for p in col] for col in pos]
    rec=[]
    steps=(cycles*n) if loop else (40+n)
    sub=4; dt=1/30/sub
    for s in range(steps):
        if loop: fi=s%n
        else: fi=max(0,s-40)
        Am,segs=FW[fi]; Am2,segs2=FW[min(fi+1,len(FW)-1)] if loop or fi+1<len(FW) else FW[fi]
        gust=1+0.15*math.sin(s*0.37)+0.1*math.sin(s*1.13)
        for k in range(sub):
            u=k/sub
            for c in range(Cn):
                for r in range(R+1):
                    anchor=(Am@loc0[c][r]).lerp(Am2@loc0[c][r],u)
                    if r==0: pos[c][r]=anchor; prev[c][r]=anchor; continue
                    p=pos[c][r]; v=(p-prev[c][r])/dt
                    w=wind*gust
                    acc=Vector((0,0,-9.8))*SPEC.get('grav',0.6)+(w-v)*SPEC.get('drag',2.5)+(anchor-p)*SPEC.get('shape',30.0)*(1.0/(1+r*SPEC.get('decay',0.15)))
                    nxt=p+(p-prev[c][r])*SPEC.get('damp',0.93)+acc*dt*dt
                    prev[c][r]=p; pos[c][r]=nxt
            for it in range(6):
                for c in range(Cn):
                    for r in range(R):
                        a_,b_=pos[c][r],pos[c][r+1]; d=b_-a_; l=d.length or 1e-6; e=(l-L[c][r])/l
                        if r==0: pos[c][r+1]=b_-d*e
                        else: pos[c][r]=a_+d*e*0.5; pos[c][r+1]=b_-d*e*0.5
                BEND=SPEC.get('bend',0.5)
                for c in range(Cn):
                    for r in range(R-1):
                        a_,b_=pos[c][r],pos[c][r+2]; tgt=pos[c][r+1]; mid=(a_+b_)*0.5
                        rest2=(loc0[c][r+2]-loc0[c][r]).length; d=b_-a_; l=d.length or 1e-6
                        if l<rest2*0.97:
                            e=(l-rest2*0.97)/l*BEND
                            if r==0: pos[c][r+2]=b_-d*e
                            else: pos[c][r]=a_+d*e*0.5; pos[c][r+2]=b_-d*e*0.5
                for c in range(Cn-1):
                    for r in range(1,R+1):
                        a_,b_=pos[c][r],pos[c+1][r]; d=b_-a_; l=d.length or 1e-6; e=(l-LX[c][r])/l*0.5
                        pos[c][r]=a_+d*e*0.5; pos[c+1][r]=b_-d*e*0.5
                # collisions (particles + bone midpoints)
                for c in range(Cn):
                    for r in range(1,R+1):
                        for (A,B),rad in zip(segs,RAD):
                            AB=B-A; t=max(0,min(1,(pos[c][r]-A).dot(AB)/AB.length_squared)); q=A+AB*t
                            d=pos[c][r]-q; dl=d.length
                            if dl<rad+MARG:
                                nrm=d/dl if dl>1e-6 else (Am.to_3x3()@Vector((0,1,0))).normalized()
                                pos[c][r]=q+nrm*(rad+MARG)
                for c in range(Cn):
                    for r in range(R):
                        mpt=(pos[c][r]+pos[c][r+1])*0.5
                        for (A,B),rad in zip(segs,RAD):
                            AB=B-A; t=max(0,min(1,(mpt-A).dot(AB)/AB.length_squared)); q=A+AB*t
                            d=mpt-q; dl=d.length
                            if dl<rad+MARG and dl>1e-6:
                                push=d/dl*(rad+MARG-dl)
                                if r>0: pos[c][r]+=push
                                pos[c][r+1]+=push
        if (loop and s>=(cycles-1)*n) or (not loop and s>=40):
            rec.append([[p.copy() for p in col] for col in pos])
    if loop:
        rec.append([[p.copy() for p in col] for col in rec[0]])
        # seam: distribute end-start residual in anchor-local space
        N=len(rec)-1
        first=[[FW[0][0].inverted()@rec[0][c][r] for r in range(R+1)] for c in range(Cn)]
        last_=[[FW[N-1][0].inverted()@rec[N-1][c][r] for r in range(R+1)] for c in range(Cn)]
        # predicted next-of-last should equal first; blend over last 30% of cycle
        K=max(3,int(N*0.3))
        for i in range(N-K,N):
            w=(i-(N-K)+1)/(K+1)
            Ai=FW[i][0]
            for c in range(Cn):
                for r in range(1,R+1):
                    li=Ai.inverted()@rec[i][c][r]
                    rec[i][c][r]=Ai@li.lerp(first[c][r],w*w*(3-2*w))
        rec[N]=[[FW[N][0]@first[c][r] if r else FW[N][0]@loc0[c][0] for r in range(R+1)] for c in range(Cn)]
    return rec

def simulate2(FW,wind,loop,name):
    n=len(FW)-1 if loop else len(FW)
    if n<2: n=len(FW)
    R0=restA.to_3x3()
    bk=(R0.inverted()@Vector((0,1,0))).normalized(); dn=(R0.inverted()@Vector((0,0,-1))).normalized()
    ax=dn.cross(bk).normalized()
    P=[FW[i][0].translation for i in range(len(FW))]
    def vel(i):
        if loop: a=P[(i-1)%n]; b=P[(i+1)%n]
        else: a=P[max(0,i-1)]; b=P[min(len(FW)-1,i+1)]
        return (b-a)*15
    MAXT=math.radians(SPEC.get('maxtilt',75))
    raw=[]
    for i in range(len(FW)):
        rel=wind-vel(i)
        a=FW[i][0].to_3x3().normalized().inverted()@rel
        sp=max(0.0,a.dot(bk))+0.3*abs(a.dot(ax))
        lat=a.dot(ax)
        raw.append((MAXT*(1-math.exp(-sp/SPEC.get('tscale',3.0))),lat))
    # temporal lag (circular for loops)
    th=[x[0] for x in raw]; la=[x[1] for x in raw]
    k=SPEC.get('lag',0.25)
    for it in range(3 if loop else 1):
        cur=th[n-1] if (loop and it) else th[0]
        for i in range(len(th)):
            cur=cur+(th[i]-cur)*k if not (loop and i>=n) else cur
            th[i]=cur
    cyc=SPEC.get('ripcyc',{}).get(name, 2 if name.startswith('run') else 1)
    amp0=math.radians(SPEC.get('ripple',10))
    rec=[]
    for i in range(len(FW)):
        Am=FW[i][0]; ii=i%n if loop else i
        spd=th[i]/MAXT if MAXT else 0
        amp=amp0*(0.25+spd)
        st=[]
        hw=0.0 if name.startswith('fly') else SPEC.get('hang',0.85)
        cur_dn=(Am.to_3x3()@dn).normalized(); want=(R0@dn).normalized()
        Qg=Quaternion().slerp(cur_dn.rotation_difference(want),hw)
        A3=Am.to_3x3()
        bkw=(A3@bk).normalized()
        if (Qg@cur_dn).dot(bkw) < cur_dn.dot(bkw): Qg=Quaternion()
        for c in range(Cn):
            col=[Am@loc0[c][0]]; pw=Am@loc0[c][0]
            acc=0.0
            for r in range(R):
                u=(r+1)/R
                ph=2*math.pi*(cyc*ii/max(1,n))-r*0.75+c*(0 if name.startswith('fly') else SPEC.get('cph',0.1))
                phi=th[i]*(0.35+0.65*u)+amp*u*math.sin(ph)
                sw=math.radians(6)*u*max(-1,min(1,la[i]/4))+amp*0.25*u*math.sin(ph*0.5)
                d=loc0[c][r+1]-loc0[c][r]
                q=Quaternion(ax,phi)@Quaternion(bk,sw)
                pw=pw+Qg@(A3@(q@d))
                col.append(pw.copy())
            st.append(col)
        segs=FW[i][1]
        MG=MARG+(SPEC.get('extra_nonloop',0.06) if not loop else SPEC.get('extra_loop',0.03))+(0.03 if name.startswith('fly_fast') else 0)
        for it in range(SPEC.get('xit',8)*(3 if name.startswith('fly') else 1)):
            for c in range(Cn):
                for r in range(1,R+1):
                    for k_,((A_,B_),rad) in enumerate(zip(segs,RAD)):
                        AB=B_-A_; t=max(0,min(1,(st[c][r]-A_).dot(AB)/max(AB.length_squared,1e-9))); q_=A_+AB*t
                        d=st[c][r]-q_; dl=d.length; need=max(rad+MG,RC.get((k_,c,r),0)*SPEC.get('rcf',1.0))
                        if dl<need and dl>1e-6: st[c][r]=q_+d/dl*need
            for c in range(Cn-1):
                for r in range(1,R+1):
                    a_,b_=st[c][r],st[c+1][r]; d=b_-a_; l=d.length or 1e-6
                    if l>LX[c][r]*(1.0 if name.startswith('fly') else 1.02):
                        e=(l-LX[c][r]*1.02)/l*0.5; st[c][r]=a_+d*e; st[c+1][r]=b_-d*e
            for c in range(Cn):
                for r in range(R):
                    a_,b_=st[c][r],st[c][r+1]; d=b_-a_; l=d.length or 1e-6; e=(l-L[c][r])/l
                    st[c][r+1]=b_-d*e
        for c in range(Cn):
            for r in range(1,R+1):
                for k_,((A_,B_),rad) in enumerate(zip(segs,RAD)):
                    AB=B_-A_; t=max(0,min(1,(st[c][r]-A_).dot(AB)/max(AB.length_squared,1e-9))); q_=A_+AB*t
                    d=st[c][r]-q_; dl=d.length; need=max(rad+MG,RC.get((k_,c,r),0)*SPEC.get('rcf',1.0))
                    if dl<need and dl>1e-6: st[c][r]=q_+d/dl*need
        rec.append(st)
    if loop: rec[-1]=rec[0] if len(rec)>n else rec[-1]
    # recompute last frame for loop to match first exactly in anchor space
    if loop and len(FW)>n:
        rec[n]=[[FW[n][0]@(FW[0][0].inverted()@rec[0][c][r]) for r in range(R+1)] for c in range(Cn)]
    return rec
def frame_of(st,c,r,Q=None):
    y=(arm.matrix_world.inverted().to_3x3()@(st[c][r+1]-st[c][r])).normalized()
    if Q is not None and (c,r) in RX:
        xd=Q@RX[(c,r)]; z=xd.cross(y).normalized(); x=y.cross(z).normalized()
        return Matrix((x,y,z)).transposed()
    cl=c+1 if c+1<Cn else c-1
    xd=(st[cl][r]+st[cl][r+1]-st[c][r]-st[c][r+1]) if Cn>1 else Vector((1,0,0))
    xd=arm.matrix_world.inverted().to_3x3()@xd
    if cl<c: xd=-xd
    z=xd.cross(y).normalized(); x=y.cross(z).normalized()
    return Matrix((x,y,z)).transposed()
AR=restA
restst=[[AR@loc0[c][r] for r in range(R+1)] for c in range(Cn)]
OFF={}; RX={}
for c in range(Cn):
    for r in range(R):
        nm=f'capeV_c{c}_r{r}'
        OFF[nm]=frame_of(restst,c,r).inverted()@TB[nm].matrix_local.to_3x3()
        RX[(c,r)]=TB[ANCH].matrix_local.to_3x3().inverted()@frame_of(restst,c,r).col[0]
def key(act,rec,f0):
    arm.animation_data.action=act
    for i,st in enumerate(rec):
        f=f0+i; sc.frame_set(f)
        Q=arm.pose.bones[ANCH].matrix.to_3x3()
        for c in range(Cn):
            parentM=arm.pose.bones[ANCH].matrix.copy()
            head=arm.matrix_world.inverted()@st[c][0]
            for r in range(R):
                nm=f'capeV_c{c}_r{r}'; b=TB[nm]
                R3=frame_of(st,c,r,Q)@OFF[nm]
                M=R3.to_4x4(); M.translation=head
                pb=arm.pose.bones[nm]; pb.rotation_mode='QUATERNION'
                bp=b.parent
                pb.matrix_basis=(bp.matrix_local.inverted()@b.matrix_local).inverted()@parentM.inverted()@M
                pb.keyframe_insert('rotation_quaternion',frame=f); pb.keyframe_insert('location',frame=f)
                parentM=M; head=head+R3.col[1]*b.length
acts=[x for x in bpy.data.actions if (only is None or x.name in only)]
done=set(json.load(open(OUT+'.done.json'))) if os.path.exists(OUT+'.done.json') else set()
for act in acts:
    if act.name in done: continue
    FW,f0,f1=frames_world(act)
    lp=LOOP(act.name)
    rec=simulate2(FW,wind_for(act.name),lp,act.name)
    # remove old capeV keys
    for fc in list(act.fcurves):
        if 'capeV_' in fc.data_path: act.fcurves.remove(fc)
    key(act,rec,f0)
    done.add(act.name); json.dump(sorted(done),open(OUT+'.done.json','w'))
    for md in ob.modifiers: md.show_viewport=True
    bpy.ops.wm.save_as_mainfile(filepath=OUT+'.stage1.blend')
    for md in ob.modifiers: md.show_viewport=False
    print('BAKED',act.name,len(rec),flush=True)
for md in ob.modifiers: md.show_viewport=True
bpy.ops.wm.save_as_mainfile(filepath=OUT+'.blend')
print('ALLDONE')
