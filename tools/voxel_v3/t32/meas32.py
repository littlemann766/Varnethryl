import bpy,sys,json,math,os
sys.path.insert(0,'/workspace/t32/tools'); from lib import *
a=sys.argv[sys.argv.index('--')+1:]; bpy.ops.wm.open_mainfile(filepath=a[0]); out=a[1]; only=a[2].split(',') if len(a)>2 and a[2] else None
arm,ob=scene_arm(); B=resolve(arm); MW=arm.matrix_world
H=max(0.3,(ob.dimensions.z if ob else 1.8)*ob.matrix_world.to_scale().z if ob else 1.8)
for pb in arm.pose.bones: pass
def rest_w(bn): return MW@arm.data.bones[bn].matrix_local
def segd(p,a,b):
    ab=b-a; t=max(0,min(1,(p-a).dot(ab)/max(ab.length_squared,1e-9))); return (p-(a+ab*t)).length
caps=[b.name for b in arm.data.bones if b.name.lower().startswith('cape')]
res={'H':H,'clips':{}}
RR={k:rest_w(v) for k,v in B.items()}
for act in bpy.data.actions:
    if only and act.name not in only: continue
    names=[b.name for b in arm.data.bones]
    f0,f1,M=sample(arm,act,names)
    n=f1-f0+1; o={'frames':n,'flip_max':0.0,'flip_bone':'','flip_frame':-1,'wrist_max':0.0,'arm_abd_max':0.0,'knee_max':0.0,'knee_hyper':0.0,'hand_in_leg':0,'cape_in_leg':0}
    prev={}
    W=lambda bn,i:MW@M[bn][i]
    lastfoot={}; cv=[]; lat_disp=0.0
    stance={'L':[],'R':[]}
    for i in range(n):
        for bn in names:
            if bn.startswith('capeV'): continue
            q=M[bn][i].to_quaternion()  # armature-space rot; local diff via parent
            par=arm.data.bones[bn].parent
            ql=(M[par.name][i].to_quaternion().inverted()@q) if par else q
            if bn in prev:
                d=ang(prev[bn],ql)
                if d>o['flip_max']: o.update(flip_max=d,flip_bone=bn,flip_frame=f0+i)
            prev[bn]=ql
        hp_hips=W(B['hips'],i).translation
        for s in 'LR':
            if 'farm'+s in B and 'hand'+s in B:
                rel=W(B['farm'+s],i).to_quaternion().inverted()@W(B['hand'+s],i).to_quaternion()
                rr=RR['farm'+s].to_quaternion().inverted()@RR['hand'+s].to_quaternion()
                o['wrist_max']=max(o['wrist_max'],ang(rr,rel))
            if 'uarm'+s in B and 'farm'+s in B:
                u=W(B['farm'+s],i).translation-W(B['uarm'+s],i).translation; lat=abs(u.x); down=-u.z
                o['arm_abd_max']=max(o['arm_abd_max'],math.degrees(math.atan2(lat,max(down,1e-4))) if down>0 else 90+math.degrees(math.atan2(-down,lat)))
                if 'hand'+s in B:
                    hp=W(B['hand'+s],i).translation
                    for lk in 'LR':
                        if 'thigh'+lk in B and segd(hp,W(B['thigh'+lk],i).translation,W(B['shin'+lk],i).translation)<0.045*H: o['hand_in_leg']+=1
            if 'thigh'+s in B and 'shin'+s in B and 'foot'+s in B:
                l1=W(B['shin'+s],i).translation-W(B['thigh'+s],i).translation; l2=W(B['foot'+s],i).translation-W(B['shin'+s],i).translation
                k=math.degrees(l1.angle(l2)) if l1.length*l2.length>0 else 0; o['knee_max']=max(o['knee_max'],k)
                if k>12 and (l2.normalized()-l1.normalized()).dot(Vector((0,-1,0)))>0.25: o['knee_hyper']=max(o['knee_hyper'],k)
        for cb in caps:
            cp=W(cb,i).translation
            for lk in 'LR':
                if 'thigh'+lk in B and segd(cp,W(B['thigh'+lk],i).translation,W(B['shin'+lk],i).translation)<0.035*H: o['cape_in_leg']+=1
        feet=[s for s in 'LR' if 'foot'+s in B]
        if feet:
            ys={s:W(B['foot'+s],i).translation.z-RR['foot'+s].translation.z for s in feet}
            lk=min(ys,key=ys.get); fp=W(B['foot'+lk],i).translation
            if lk in lastfoot and ys[lk]<0.03*H: cv.append((fp-lastfoot[lk])*30)
            for s in feet:
                lastfoot[s]=W(B['foot'+s],i).translation
                stance[s].append((ys[s]<0.03*H, W(B['foot'+s],i).translation.x))
    if cv:
        v=sum(cv,Vector());v/=len(cv); v.z=0
        o['facing_err_deg']=math.degrees(v.normalized().angle(Vector((0,1,0)))) if v.length>0.5 else -1
        o['lat_speed_mean']=float(np.mean([abs(x.x) for x in cv]))
    # max lateral travel of a foot within one contiguous stance
    mx=0.0
    for s,L in stance.items():
        seg=[]
        for c,x in L+[(False,0)]:
            if c: seg.append(x)
            else:
                if len(seg)>1: mx=max(mx,max(seg)-min(seg))
                seg=[]
    o['stance_lat_drift_m']=mx
    res['clips'][act.name]=o
json.dump(res,open(out,'w'),indent=1)
