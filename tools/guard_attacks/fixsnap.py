# replace single-frame bone snaps (step >35 deg and >2.5x neighbours, motion_checks definition) by slerp over a +-2 frame window. usage: blender -b -P fixsnap.py -- in.blend clip1,clip2 bone1,bone2 out.blend
import bpy,sys,math,json
from mathutils import Quaternion
a=sys.argv[sys.argv.index('--')+1:]; bpy.ops.wm.open_mainfile(filepath=a[0]); log={}
def sd(q1,q2): return math.degrees(q1.rotation_difference(q2).angle) if True else 0
for an in a[1].split(','):
    A=bpy.data.actions[an]
    for bn in a[2].split(','):
        fcs=[A.fcurves.find(f'pose.bones["{bn}"].rotation_quaternion',index=k) for k in range(4)]
        if not fcs[0]: continue
        n=len(fcs[0].keyframe_points)
        for it in range(3):
            q=[Quaternion([fc.keyframe_points[t].co[1] for fc in fcs]) for t in range(n)]
            st=[min(sd(q[i],q[i+1]),360-sd(q[i],q[i+1])) for i in range(n-1)]
            hit=False
            for i,x in enumerate(st):
                nb=[st[j] for j in (i-1,i+1) if 0<=j<len(st)]
                if x>35 and x>2.5*max(nb+[1]):
                    lo,hi=max(0,i-2),min(n-1,i+3); qa,qb=q[lo],q[hi]
                    if qa.dot(qb)<0: qb=-qb
                    for t in range(lo+1,hi):
                        r=qa.slerp(qb,(t-lo)/(hi-lo))
                        for k in range(4): fcs[k].keyframe_points[t].co[1]=r[k]; fcs[k].keyframe_points[t].handle_left[1]=r[k]; fcs[k].keyframe_points[t].handle_right[1]=r[k]
                    log.setdefault(an,[]).append([bn,i,round(x,1)]); hit=True; break
            if not hit: break
print('FIXSNAP',json.dumps(log)); bpy.ops.wm.save_as_mainfile(filepath=a[3])
