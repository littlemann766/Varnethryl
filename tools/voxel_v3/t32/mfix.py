import bpy,sys,json,math,os
sys.path.insert(0,'/workspace/t32/tools'); from lib import *
a=sys.argv[sys.argv.index('--')+1:]; src,out=a[0],a[1]
CAP=float(os.environ.get('CAP','25')); TW=float(os.environ.get('TWIST','60'))
ARMCLIPS=os.environ.get('ARMCLIPS','run,walk').split(','); LEGCLIPS=os.environ.get('LEGCLIPS','run,walk').split(',')
SKIPWRIST=[x for x in os.environ.get('SKIPWRIST','').split(',') if x]
bpy.ops.wm.open_mainfile(filepath=src); sc=bpy.context.scene; sc.render.fps=30
arm,ob=scene_arm(); B=resolve(arm); TB=arm.data.bones
H=(ob.dimensions.z*ob.matrix_world.to_scale().z) if ob else 1.8
log={}
def gauss_cyc(x,s,cyc=True):
    n=len(x); 
    if s<=0 or n<3: return np.array(x)
    k=np.arange(-3,4); w=np.exp(-k**2/(2*s*s)); w/=w.sum(); y=np.zeros(n)
    for i in range(n):
        for kk,ww in zip(k,w):
            j=i+kk; j=j%n if cyc else min(max(j,0),n-1); y[i]+=ww*x[j]
    return y
def despike(act,T):
    f0,f1=[int(round(x)) for x in act.frame_range]; n=f1-f0+1; arm.animation_data.action=act; fixed=0
    for pb in arm.pose.bones:
        if pb.name.startswith('capeV'): continue
        dp='pose.bones["%s"].rotation_quaternion'%pb.name
        fcs=[act.fcurves.find(dp,index=k) for k in range(4)]
        if fcs[0] is None: continue
        Q=[Quaternion([fc.evaluate(f) for fc in fcs]).normalized() for f in range(f0,f1+1)]
        ch=False
        for it in range(3):
            for i in range(1,n-1):
                d1=ang(Q[i-1],Q[i]); 
                if d1<=T: continue
                for w in (1,2):
                    if i+w>=n: break
                    if ang(Q[i-1],Q[i+w])<0.5*d1:
                        for k in range(w):
                            Q[i+k]=Q[i-1].slerp(Q[i+w],(k+1)/(w+1)); 
                        ch=True; fixed+=1; break
        if ch: write_rot(act,arm,pb.name,f0,Q)
    return fixed
def legs(act):
    names=[B[k] for k in ('thighL','shinL','footL','thighR','shinR','footR')]
    f0,f1,M=sample(arm,act,names); n=f1-f0+1; rep={}
    for s in 'LR':
        th,sh,ft=B['thigh'+s],B['shin'+s],B['foot'+s]
        l1=(TB[sh].head_local-TB[th].head_local).length; l2=(TB[ft].head_local-TB[sh].head_local).length
        Hp=[M[th][i].translation for i in range(n)]; K=[M[sh][i].translation for i in range(n)]; A=[M[ft][i].translation.copy() for i in range(n)]
        rz=TB[ft].head_local.z
        st=[A[i].z-rz<0.03*H for i in range(n)]
        # lateral plant lock
        At=[x.copy() for x in A]; i=0; segs=[]
        while i<n:
            if st[i]:
                j=i
                while j+1<n and st[j+1]: j+=1
                segs.append((i,j)); i=j+1
            else: i+=1
        for (i0,i1) in segs:
            x0=A[i0].x
            for i in range(max(0,i0-3),min(n,i1+4)):
                w=1.0 if i0<=i<=i1 else 1-min(abs(i-i0),abs(i-i1))/4
                At[i].x=A[i].x*(1-w)+x0*w
        # knee angle profile, clamp + smooth
        L=l1+l2; th_=[]
        for i in range(n):
            d=min((At[i]-Hp[i]).length,0.995*L); c=(l1*l1+l2*l2-d*d)/(2*l1*l2); th_.append(math.pi-math.acos(max(-1,min(1,c))))
        th_=np.array(th_); th2=np.maximum(th_,0)
        sm=gauss_cyc(th2,1.2,cyc=act.name.startswith(('walk','run')))
        sm=np.maximum(sm,math.radians(8))
        Mn={k:list(M[k]) for k in (th,sh,ft)}
        # stable knee pole: thigh-local pole from frames with a real bend, filled across straight frames
        PL=[None]*n
        for i in range(n):
            uo=(A[i]-Hp[i]).normalized(); p=(K[i]-Hp[i]); p=p-uo*p.dot(uo)
            if th_[i]>math.radians(15) and p.length>1e-4: PL[i]=M[th][i].to_3x3().inverted()@p.normalized()
        good=[i for i in range(n) if PL[i] is not None]
        for i in range(n):
            if PL[i] is None and good:
                j=min(good,key=lambda g:min(abs(g-i),n-abs(g-i))); PL[i]=PL[j]
        for i in range(n):
            u=(At[i]-Hp[i]); dd=math.sqrt(max(1e-9,l1*l1+l2*l2-2*l1*l2*math.cos(math.pi-sm[i]))); u.normalize()
            Ai=Hp[i]+u*dd
            p=(M[th][i].to_3x3()@PL[i]) if PL[i] is not None else Vector((0,-1,0))
            p=p-u*p.dot(u)
            if p.length<1e-4: p=Vector((0,-1,0))-u*Vector((0,-1,0)).dot(u)
            p.normalize()
            ca=(l1*l1+dd*dd-l2*l2)/(2*l1*dd); ca=max(-1,min(1,ca)); al=math.acos(ca)
            Kn=Hp[i]+l1*(math.cos(al)*u+math.sin(al)*p)
            r1=(K[i]-Hp[i]).normalized().rotation_difference((Kn-Hp[i]).normalized()).to_matrix().to_4x4()
            Mth=Matrix.Translation(Hp[i])@r1@Matrix.Translation(-Hp[i])@M[th][i]
            Msh0=Matrix.Translation(Hp[i])@r1@Matrix.Translation(-Hp[i])@M[sh][i]
            r2=(Msh0.to_3x3()@Vector((0,1,0))).normalized()
            r2=(Ai-Kn).normalized(); cur=(Matrix.Translation(Hp[i])@r1@Matrix.Translation(-Hp[i])@A[i].to_4d()).to_3d()-Kn
            rr=cur.normalized().rotation_difference(r2).to_matrix().to_4x4()
            Msh=Matrix.Translation(Kn)@rr@Matrix.Translation(-Kn)@Msh0
            Mft=Matrix.Translation(Ai)@M[ft][i].to_3x3().to_4x4()
            Mn[th][i]=Mth; Mn[sh][i]=Msh; Mn[ft][i]=Mft
        Mall=dict(M); Mall.update(Mn)
        par={th:TB[th].parent.name}
        if par[th] not in Mall: _,_,Pm=sample(arm,act,[par[th]]); Mall[par[th]]=Pm[par[th]]; arm.animation_data.action=act
        for bn in (th,sh,ft):
            pn=TB[bn].parent.name
            qs=[basis_from(arm,bn,Mall[bn][i],Mall[pn][i]) for i in range(n)]
            write_rot(act,arm,bn,f0,qs)
        rep[s]={'stance_frames':int(sum(st)),'min_knee_deg':round(math.degrees(float(th_.min())),1)}
    return rep
def arms(act):
    f0,f1=[int(round(x)) for x in act.frame_range]; n=f1-f0+1; rep={}
    for s in 'LR':
        if 'uarm'+s not in B: continue
        ua,fa,hd=B['uarm'+s],B['farm'+s],B['hand'+s]
        thighs=[(B['thigh'+k],B['shin'+k]) for k in 'LR' if 'thigh'+k in B]
        _,_,M=sample(arm,act,[ua,fa,hd,TB[ua].parent.name]+[x for t in thighs for x in t])
        pn=TB[ua].parent.name
        # 1) abduction cap about forward axis through shoulder
        newU=[]; dl=[]
        for i in range(n):
            S=M[ua][i].translation; E=M[fa][i].translation; u=E-S
            def abd(v): 
                lat=abs(v.x); down=-v.z
                return math.degrees(math.atan2(lat,max(down,1e-4))) if down>0 else 90+math.degrees(math.atan2(-down,lat))
            a0=abd(u); d=0.0
            if a0>CAP:
                best=None
                for sg in (1,-1):
                    R=Matrix.Rotation(math.radians(sg*(a0-CAP)),3,'Y'); a1=abd(R@u)
                    if best is None or a1<best[0]: best=(a1,sg)
                d=best[1]*(a0-CAP)
            dl.append(d)
        dl=gauss_cyc(np.array(dl),1.0,cyc=act.name.startswith(('walk','run')))
        Mu=[];Mf=[];Mh=[]
        for i in range(n):
            S=M[ua][i].translation; R=Matrix.Translation(S)@Matrix.Rotation(math.radians(dl[i]),4,'Y')@Matrix.Translation(-S)
            Mu.append(R@M[ua][i]); Mf.append(R@M[fa][i]); Mh.append(R@M[hd][i])
        # 2) elbow flex so the hand clears the thighs (hand forward)
        def segd(p,a,b):
            ab=b-a; t=max(0,min(1,(p-a).dot(ab)/max(ab.length_squared,1e-9))); return (p-(a+ab*t)).length
        need=[]
        for i in range(n):
            E=Mf[i].translation; up=(E-Mu[i].translation).normalized()
            ax=up.cross(Vector((0,-1,0)))
            if ax.length<1e-3: ax=Vector((1,0,0))
            ax.normalize(); got=0
            def clear(Mh_):
                hp=Mh_.translation; tip=(Mh_@Vector((0,TB[hd].length,0,1))).to_3d() if False else hp
                return min(segd(hp,M[t][i].translation,M[sh_][i].translation) for t,sh_ in thighs)
            for g in range(0,95,5):
                best=None
                for sg in (1,-1):
                    R=Matrix.Translation(E)@Matrix.Rotation(math.radians(sg*g),4,ax)@Matrix.Translation(-E)
                    hp=(R@Mh[i]).translation
                    if hp.y>E.y+0.02 and g>0: continue  # must go forward (-Y)
                    c=clear(R@Mh[i])
                    if c>=0.065*H: best=sg*g; break
                if best is not None: got=best; break
            need.append(got)
        need=np.array(need,float); mx=np.array([need[max(0,i-2):i+3][np.argmax(np.abs(need[max(0,i-2):i+3]))] for i in range(n)])
        need=gauss_cyc(mx,1.0,cyc=act.name.startswith(('walk','run')))
        for i in range(n):
            E=Mf[i].translation; up=(E-Mu[i].translation).normalized(); ax=up.cross(Vector((0,-1,0)))
            if ax.length<1e-3: ax=Vector((1,0,0))
            ax.normalize(); R=Matrix.Translation(E)@Matrix.Rotation(math.radians(need[i]),4,ax)@Matrix.Translation(-E)
            Mf[i]=R@Mf[i]; Mh[i]=R@Mh[i]
        qu=[basis_from(arm,ua,Mu[i],M[pn][i]) for i in range(n)]; qf=[basis_from(arm,fa,Mf[i],Mu[i]) for i in range(n)]
        write_rot(act,arm,ua,f0,qu); write_rot(act,arm,fa,f0,qf)
        rep[s]={'max_inward_deg':round(float(np.abs(dl).max()),1),'max_elbow_extra_deg':round(float(np.abs(need).max()),1)}
    return rep
def wrist(act):
    f0,f1=[int(round(x)) for x in act.frame_range]; n=f1-f0+1; rep={}
    for s in 'LR':
        if 'hand'+s not in B: continue
        fa,hd=B['farm'+s],B['hand'+s]; _,_,M=sample(arm,act,[fa,hd])
        F0=TB[fa].matrix_local.to_3x3(); Hr=TB[hd].matrix_local.to_3x3(); rr=(F0.inverted()@Hr).to_quaternion()
        axl=(F0.inverted()@(TB[hd].head_local-TB[fa].head_local)).normalized()
        qs=[]; mx=0; ch=False
        for i in range(n):
            F=M[fa][i].to_quaternion(); Hq=M[hd][i].to_quaternion()
            rel=rr.inverted()@F.inverted()@Hq
            v=Vector(rel[1:]); pr=axl*v.dot(axl); tw=Quaternion((rel[0],*pr)); 
            if tw.magnitude<1e-6: tw=Quaternion()
            tw.normalize(); sw=rel@tw.inverted()
            t=tw.angle; t=t if t<=math.pi else t-2*math.pi; sgn=1 if Vector(tw[1:]).dot(axl)>=0 else -1; td=math.degrees(t)*sgn
            mx=max(mx,abs(td))
            if abs(td)>TW:
                tw2=Quaternion(axl,math.radians(math.copysign(TW,td))); rel2=sw@tw2; ch=True
            else: rel2=rel
            Hn=F@rr@rel2; qs.append(Hn)
        if ch:
            Mh=[Matrix.Translation(M[hd][i].translation)@qs[i].to_matrix().to_4x4() for i in range(n)]
            write_rot(act,arm,hd,f0,[basis_from(arm,hd,Mh[i],M[fa][i]) for i in range(n)])
        rep[s]={'max_twist_deg':round(mx,1),'clamped':ch}
    return rep
for act in bpy.data.actions:
    nm=act.name; loco=nm.split('_')[0] in ('walk','run') or nm=='idle'; T=40 if loco else 70; r={}
    r['despike1']=despike(act,T)
    if nm in LEGCLIPS and all(k in B for k in ('thighL','shinL','footL')): r['legs']=legs(act)
    if nm in ARMCLIPS and 'uarmL' in B: r['arms']=arms(act)
    if 'handL' in B and nm not in SKIPWRIST: r['wrist']=wrist(act)
    r['despike2']=despike(act,T)
    log[nm]=r
arm.animation_data.action=bpy.data.actions.get('idle') or bpy.data.actions[0]
json.dump(log,open(out+'.mfix.json','w'),indent=1)
bpy.ops.wm.save_as_mainfile(filepath=out)
