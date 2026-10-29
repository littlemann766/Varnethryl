# blender -b -P post.py -- <in.blend> <out prefix> <report.json with hold frames>
import sys,os,json,math
_a=sys.argv[sys.argv.index('--')+1:]; IN,OUT,REP=_a
sys.argv=sys.argv[:sys.argv.index('--')+1]+[IN,OUT]
exec(open('/workspace/titan2/tw2.py').read().split('# =============== WALK')[0])
_MG=float(os.environ.get('MGF','0'))*_H
def n_in(W):
    co=lbs_all(W); cv=[Vector(c) for c in co]
    bvh=BVHTree.FromPolygons(cv,_LP,all_triangles=False); out={'L':0,'R':0}
    for s_ in 'LR':
        for i in _ARMV[s_][::2]:
            r=bvh.find_nearest(cv[i],_H*0.2)
            if r[0] is None or (cv[i]-r[0]).length>0.06*_H: continue
            dist=(cv[i]-r[0]).length; hits=0;o=cv[i].copy()
            for _ in range(20):
                h=bvh.ray_cast(o,_DIR)
                if h[0] is None: break
                hits+=1;o=h[0]+_DIR*1e-5*_H
            if hits%2==1 or dist<_MG: out[s_]+=1
    return out
rep=json.load(open(REP)); HOLDS={c:set(i['hold_frames']) for c,i in rep.items() if not c.startswith('_') and 'hold_frames' in i}
def kneeout(W,s,ang):
    th,shn,ft=LEGS[s]; Hh=W[th].translation.copy(); F=W[ft].translation.copy(); fr_=W[ft].to_3x3()
    sg=1 if s=='L' else -1; ax=(F-Hh).normalized(); K=W[shn].translation-Hh
    R=Matrix.Rotation(math.radians(ang),4,ax)
    if ((R.to_3x3()@K).x-K.x)*sg*float(os.environ.get('KOS','1'))<0: R=Matrix.Rotation(math.radians(-ang),4,ax)
    xform_sub(W,th,Matrix.Translation(Hh)@R@Matrix.Translation(-Hh))
    p_=W[ft].translation.copy(); xform_sub(W,ft,Matrix.Translation(p_)@(fr_@W[ft].to_3x3().inverted()).to_4x4()@Matrix.Translation(-p_))
def swing(W,s,ang,abd,pin=False):
    W={k:m.copy() for k,m in W.items()}
    if KO[0] and pin: kneeout(W,s,KO[0]*ang/95.0)
    FI=float(os.environ.get('FI','0'))
    if FI and pin:
        th_,sh_,ft_=LEGS[s]; F=W[ft_].translation.copy(); Hx=W['hips'].translation.x
        t=Vector((Hx+(F.x-Hx)*(1-FI*min(1,ang/95.0)),F.y,F.z)); two_bone(W,th_,sh_,ft_,t,keep_rot=W[ft_].to_3x3())
    ang=ang*float(os.environ.get('HSWF','1')) if pin else ang
    sh,el,ha=ARMS[s]; S=W[sh].translation.copy(); Hd=W[ha].translation.copy()
    sg=1 if s=='L' else -1
    if ang:
        ax=(Hd-S).normalized()
        # pick direction that moves elbow outward (+sg x)
        E=W[el].translation-S
        R1=Matrix.Rotation(math.radians(ang),4,ax); 
        if ((R1.to_3x3()@E).x-E.x)*sg<0: R1=Matrix.Rotation(math.radians(-ang),4,ax)
        xform_sub(W,sh,Matrix.Translation(S)@R1@Matrix.Translation(-S))
    if abd:
        fw=Vector((0,-1,0)); R2=Matrix.Rotation(math.radians(float(os.environ.get('ASG','-1'))*sg*abd),4,fw)
        xform_sub(W,sh,Matrix.Translation(S)@R2@Matrix.Translation(-S))
    if pin:
        e=[x for x in PINE if x[-1]==s]
        if e:
            for _ in range(3):
                h=rmin(W,RG(e[0]))-GOAL
                if abs(h)<0.0005: break
                if os.environ.get('NOPIN'): break
                two_bone(W,*ARMS[s],W[ha].translation-Vector((0,0,h)),keep_rot=W[ha].to_3x3(),pole_hint=W[el].translation-W[sh].translation)
    return W
PINE=[]; KO=[float(os.environ.get('KO','35'))]
CL=os.environ.get('CLIPS','').split(',')
summary={}
for clip in CL:
    act=bpy.data.actions[clip]; T.animation_data.action=act
    f0,f1=[int(round(x)) for x in act.frame_range]; fr=list(range(f0,f1+1))
    W0=[]; 
    for f in fr: sc.frame_set(f); W0.append(getW())
    PINE[:]=rep.get(clip,{}).get('effectors',[]); hold=HOLDS.get(clip,set()); n=len(fr); loop=clip in('wb_walk','wb_idle')
    def par(sv,f): return ((float(os.environ.get('HSW','95'))*sv,float(os.environ.get('HAB','0'))*sv,True) if f in hold else (0.0,float(os.environ.get('NAB','50'))*sv,False))
    def pose(t,S):
        W=W0[t]
        for s in 'LR':
            if S[s][t]>0: W=swing(W,s,*par(S[s][t],fr[t]))
        return W
    S={s:[0.0]*n for s in 'LR'}; before=0
    for t in range(n):
        r=n_in(W0[t]); before+=1 if (r['L'] or r['R']) else 0
        for s in 'LR':
            if not r[s]: continue
            for k in range(1,11):
                if n_in(swing(W0[t],s,*par(k/10,fr[t])))[s]==0: break
            S[s][t]=k/10
    def sm(a):
        idx=lambda i:(i%n) if loop else max(0,min(n-1,i))
        m=[max(a[idx(i+k)] for k in range(-5,6)) for i in range(n)]
        ks=[math.exp(-(x/2.5)**2) for x in range(-5,6)]; z=sum(ks)
        return [a[i] if fr[i] in hold else min(1.0,max(sum(ks[k+5]*m[idx(i+k)] for k in range(-5,6))/z, a[i])) for i in range(n)]
    for it in range(5):
        Ss={s:sm(S[s]) for s in 'LR'}; bad=0
        for t in range(n):
            if not (any(Ss[s][t] for s in 'LR')): 
                continue
            r=n_in(pose(t,Ss))
            for s in 'LR':
                if r[s]: bad+=1; S[s][t]=min(1.0,max(S[s][t],Ss[s][t])+0.1)
        print('IT',clip,it,bad,flush=True)
        if bad==0: break
    S=Ss; A={s:[par(S[s][t],fr[t])[0] for t in range(n)] for s in 'LR'}; B={s:[par(S[s][t],fr[t])[1] for t in range(n)] for s in 'LR'}
    newact=bpy.data.actions.new(clip+'_p'); newact.use_fake_user=True; T.animation_data.action=newact
    after=0; hts=[]
    for t,f in enumerate(fr):
        W=W0[t]
        for s in 'LR':
            if A[s][t] or B[s][t]: W=swing(W,s,A[s][t],B[s][t],f in hold)
        r=n_in(W); after+= 1 if (r['L'] or r['R']) else 0
        apply(W,f)
        if f in hold: hts.append({e:round(rmin(W,RG(e))*M2G,3) for e in rep[clip]['effectors']})
    old=bpy.data.actions[clip]; old.name=clip+'__o'; newact.name=clip; bpy.data.actions.remove(old)
    summary[clip]={'frames_before':before,'frames_after':after,'hold_heights':hts,'max_swing':[max(A['L']),max(A['R'])],'max_abd':[max(B['L']),max(B['R'])]}
    print('POST',clip,summary[clip],flush=True)
json.dump(summary,open(OUT+'.post.json','w'))
T.animation_data.action=bpy.data.actions['wb_idle']
bpy.ops.wm.save_as_mainfile(filepath=OUT+'.blend')
