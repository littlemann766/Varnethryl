import bpy,sys,math,json,os
import numpy as np
from mathutils import Quaternion,Vector
a=sys.argv[sys.argv.index('--')+1:]; blend,outblend,evout=a[0],a[1],a[2]
LOOPS=set(os.environ.get('LOOPS','idle,walk,run').split(',')); TH=float(os.environ.get('TH','38')); PERF=set(os.environ.get('PERFRAME','death').split(','))
bpy.ops.wm.open_mainfile(filepath=blend); sc=bpy.context.scene; sc.render.fps=30
arm=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]
me=[o for o in bpy.data.objects if o.type=='MESH' and 'lod1' not in o.name][0]
def qcurves(act,b):
    return [act.fcurves.find(f'pose.bones["{b}"].rotation_quaternion',index=i) for i in range(4)]
def minz_all(act):
    arm.animation_data.action=act; f0,f1=[int(x) for x in act.frame_range]; out=[]
    for f in range(f0,f1+1):
        sc.frame_set(f); dg=bpy.context.evaluated_depsgraph_get(); ev=me.evaluated_get(dg); m=ev.to_mesh()
        co=np.empty(len(m.vertices)*3); m.vertices.foreach_get('co',co); ev.to_mesh_clear()
        out.append(float((co.reshape(-1,3)@np.array(me.matrix_world.to_3x3()).T)[:,2].min()+me.matrix_world.translation.z))
    return np.array(out)
from mathutils import Matrix
LIFTLOG={}
def handlift(act,f0,f1,off,clear=0.08):
    arm.animation_data.action=act
    for s_ in ('L','R'):
        ua,tip='upperArm_'+s_,'fingers_'+s_
        if ua not in arm.pose.bones: continue
        th=[]
        for f in range(f0,f1+1):
            sc.frame_set(f); pb=arm.pose.bones[ua]
            sh=arm.matrix_world@pb.head; tp=arm.matrix_world@arm.pose.bones[tip].tail
            d=clear-(tp.z+off)
            th.append(max(0.0,d/max(0.2,(tp-sh).length)*1.15) if d>0 else 0.0)
        th=np.array(th)
        if th.max()<=0: continue
        k=np.exp(-0.5*(np.arange(-6,7)/2.5)**2); k/=k.sum()
        thm=np.array([th[max(0,i-3):i+4].max() for i in range(len(th))])
        ths=np.convolve(np.pad(thm,6,mode='edge'),k,mode='valid'); ths=np.maximum(ths,th)
        LIFTLOG[act.name+'_'+s_]=round(math.degrees(ths.max()),1)
        for i,f in enumerate(range(f0,f1+1)):
            if ths[i]<=1e-4: continue
            sc.frame_set(f); pb=arm.pose.bones[ua]
            sh=pb.head.copy(); tp=arm.pose.bones[tip].tail
            v=(tp-sh); ax=v.cross(Vector((0,0,1)))
            if ax.length<1e-6: continue
            R=Matrix.Rotation(ths[i],4,ax.normalized())
            pb.matrix=Matrix.Translation(sh)@R@Matrix.Translation(-sh)@pb.matrix
            pb.keyframe_insert('rotation_quaternion',frame=f)
report={}
for act in bpy.data.actions:
    f0,f1=[int(x) for x in act.frame_range]; loop=act.name in LOOPS; fixes=0
    for pb in arm.pose.bones:
        fc=qcurves(act,pb.name)
        if None in fc: continue
        Q=[Quaternion([fc[i].evaluate(f) for i in range(4)]) for f in range(f0,f1+1)]
        n=len(Q)
        for it in range(4):
            bad=False
            for f in range(n):
                p=f-1; q=f+1
                if p<0: 
                    if not loop: continue
                    p=n-2
                if q>=n:
                    if not loop: continue
                    q=1
                d=math.degrees(Q[p].rotation_difference(Q[f]).angle); d=min(d,360-d)
                if d>TH:
                    Q[f]=Q[p].slerp(Q[q],0.5); bad=True; fixes+=1
                    if loop and f==0: Q[n-1]=Q[0]
                    if loop and f==n-1: Q[0]=Q[n-1]
            if not bad: break
        for i in range(4):
            for k,kp in enumerate(fc[i].keyframe_points): kp.co[1]=Q[int(kp.co[0])-f0][i]; kp.handle_left[1]=kp.co[1]; kp.handle_right[1]=kp.co[1]
            fc[i].update()
    # ground
    mz=minz_all(act)
    if act.name in PERF:
        off=-mz; k=np.ones(3)/3; off=np.convolve(np.pad(off,1,mode='edge'),k,mode='valid')
    else: off=np.full(len(mz),-float(np.median(mz)) if act.name not in LOOPS else -mz.min())
    if act.name not in PERF: handlift(act,f0,f1,float(off[0]))
    rb=arm.data.bones['root']; Rinv=rb.matrix_local.to_3x3().inverted()
    lc=[act.fcurves.find('pose.bones["root"].location',index=i) for i in range(3)]
    if None in lc:
        arm.animation_data.action=act
        for f in range(f0,f1+1): arm.pose.bones['root'].location=(0,0,0); arm.pose.bones['root'].keyframe_insert('location',frame=f)
        lc=[act.fcurves.find('pose.bones["root"].location',index=i) for i in range(3)]
    for kp_i in range(len(lc[0].keyframe_points)):
        f=int(lc[0].keyframe_points[kp_i].co[0]); dl=Rinv@Vector((0,0,float(off[f-f0])))
        for i in range(3):
            kp=lc[i].keyframe_points[kp_i]; kp.co[1]+=dl[i]; kp.handle_left[1]=kp.co[1]; kp.handle_right[1]=kp.co[1]
    for c in lc: c.update()
    mz2=minz_all(act)
    report[act.name]={'despike_fixes':fixes,'ground_offset_m':[round(float(off.min()),3),round(float(off.max()),3)],'min_z_after':[round(float(mz2.min()),3),round(float(mz2.max()),3)],'min_z_last':round(float(mz2[-1]),3)}
    print('POST',act.name,report[act.name])
# events
def bw(b,f): sc.frame_set(f); return arm.matrix_world@arm.pose.bones[b].tail
def gl(v): return [round(v.x,3),round(v.z,3),round(-v.y,3)]   # blender -> glTF model space (+Z fwd, +X left, +Y up)
ev={}
HANDS=[x for x in ('fingers_L','fingers_R') if x in arm.pose.bones]
for act in bpy.data.actions:
    arm.animation_data.action=act; f0,f1=[int(x) for x in act.frame_range]; n=f1-f0
    e={'frames':n,'seconds':round(n/30,3),'fps':30,'loop':act.name in LOOPS}
    if act.name.startswith('attack') and HANDS:
        best=None
        for h in HANDS:
            P=[bw(h,f) for f in range(f0,f1+1)]; fw=[-p.y for p in P]
            mx=int(np.argmax(fw)); wu=int(np.argmin(fw[:mx+1])) if mx>0 else 0
            amp=fw[mx]-fw[wu]
            if best is None or amp>best[0]: best=(amp,h,mx,wu,P,fw)
        amp,h,mx,wu,P,fw=best
        c=next(i for i in range(wu,mx+1) if fw[i]>=fw[wu]+0.9*amp)
        d0=[(P[i]-P[0]).length for i in range(wu+1)]; ws=next((i for i in range(wu+1) if d0[i]>0.15*max(d0[-1],1e-6)),0)
        sp=[(P[i+1]-P[i]).length*30 for i in range(n)]
        best=(max(sp),)
        hp=P[c]; root=arm.matrix_world@arm.pose.bones['root'].head
        e.update({'hand':h.replace('fingers_','hand_'),'windup_start_frame':ws,'windup_peak_frame':wu,'hit_frame':c,'hit_time':round(c/30,3),
          'recover_frame':n,'hit_point_model':gl(hp),'reach_m':round(math.hypot(hp.x-root.x,hp.y-root.y),2),'peak_hand_speed_mps':round(best[0],1)})
    if act.name in ('walk','run'):
        steps=[]
        for s in ('foot_L','foot_R'):
            Z=[bw(s,f).z for f in range(f0,f1+1)]; zmin=min(Z)
            con=[z<zmin+0.03 for z in Z]
            for i in range(1,n+1):
                if con[i] and not con[i-1]: steps.append({'foot':s,'frame':i,'time':round(i/30,3)})
        e['footsteps']=sorted(steps,key=lambda x:x['frame'])
    if act.name.startswith('death'):
        H=[bw('hips',f).z for f in range(f0,f1+1)]; fin=H[-1]; h0=H[0]
        imp=next(i for i in range(n+1) if H[i]<fin+0.1*(h0-fin))
        e.update({'ground_impact_frame':imp,'ground_impact_time':round(imp/30,3),'hips_height_start':round(h0,2),'hips_height_end':round(fin,2)})
    ev[act.name]=e
json.dump({'post':report,'hand_ground_lift_deg':LIFTLOG,'clips':ev},open(evout,'w'),indent=1)
bpy.ops.wm.save_as_mainfile(filepath=outblend)
