# frame-evaluated snap fix: world-space step of a bone >35 deg and >2.5x its neighbours (motion_checks definition) -> the bone's local quaternion over a +-W window is slerped between the window ends and re-keyed.
# usage: blender -b -P fixsnap2.py -- in.blend clip1,clip2 bone1,bone2 out.blend [W=2]
import bpy,sys,math,json
a=sys.argv[sys.argv.index('--')+1:]; bpy.ops.wm.open_mainfile(filepath=a[0]); Wd=int(a[4]) if len(a)>4 else 2
arm=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]; sc=bpy.context.scene; sc.render.fps=30; log={}
for an in a[1].split(','):
    A=bpy.data.actions[an]; arm.animation_data.action=A; f0,f1=map(int,A.frame_range)
    for bn in a[2].split(','):
        pb=arm.pose.bones[bn]; pb.rotation_mode='QUATERNION'
        for it in range(4):
            Wq=[];Lq=[]
            for f in range(f0,f1+1): sc.frame_set(f); Wq.append((arm.matrix_world@pb.matrix).to_quaternion()); Lq.append(pb.rotation_quaternion.copy())
            st=[(lambda d:min(d,360-d))(math.degrees(Wq[i].rotation_difference(Wq[i+1]).angle)) for i in range(len(Wq)-1)]
            bad=[i for i,x in enumerate(st) if x>35 and x>2.5*max([st[j] for j in (i-1,i+1) if 0<=j<len(st)]+[1])]
            if not bad: break
            i=bad[0]; lo,hi=max(0,i-Wd),min(len(Lq)-1,i+1+Wd); qa,qb=Lq[lo],Lq[hi].copy()
            if qa.dot(qb)<0: qb.negate()
            for t in range(lo+1,hi):
                pb.rotation_quaternion=qa.slerp(qb,(t-lo)/(hi-lo)); pb.keyframe_insert('rotation_quaternion',frame=f0+t)
            log.setdefault(an,[]).append([bn,i,round(st[i],1)])
print('FIXSNAP',json.dumps(log)); bpy.ops.wm.save_as_mainfile(filepath=a[3])
