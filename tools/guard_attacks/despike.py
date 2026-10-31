# post-pass on keyed pose-bone quaternions: a frame step that is >35 deg and >2.5x both neighbours is spread over a 5-frame window
import bpy,sys,math,json
from mathutils import Quaternion
a=sys.argv[sys.argv.index('--')+1:]; blend,acts,out=a[0],a[1].split(','),a[2]
bpy.ops.wm.open_mainfile(filepath=blend)
log={}
import os
SKIP=[x for x in os.environ.get('SKIP','').split(',') if x]
def sd(x): x=math.degrees(x); return x if x<=180 else 360-x
for an in acts:
    A=bpy.data.actions[an]
    bones=sorted({fc.data_path.split('"')[1] for fc in A.fcurves if fc.data_path.endswith('rotation_quaternion')})
    for bn in bones:
        if SKIP and any(bn==k or bn.endswith(':'+k) for k in SKIP): continue
        fcs=[A.fcurves.find(f'pose.bones["{bn}"].rotation_quaternion',index=k) for k in range(4)]
        n=len(fcs[0].keyframe_points)
        q=[Quaternion([fc.keyframe_points[t].co[1] for fc in fcs]) for t in range(n)]
        for it in range(4):
            st=[sd(q[i].rotation_difference(q[i+1]).angle) for i in range(n-1)]
            hit=False
            for i in range(n-1):
                nb=[st[j] for j in (i-1,i+1) if 0<=j<n-1]
                if st[i]>35 and st[i]>2.5*max(nb+[1]):
                    k0=max(0,i-2); k1=min(n-1,i+3)
                    for k in range(k0+1,k1): q[k]=q[k0].slerp(q[k1],(k-k0)/(k1-k0))
                    log.setdefault(an,[]).append([bn,i,round(st[i],1)]); hit=True
            if not hit: break
        prev=None
        for t in range(n):
            if prev is not None and q[t].dot(prev)<0: q[t].negate()
            prev=q[t]
            for k,fc in enumerate(fcs):
                p=fc.keyframe_points[t]; p.co[1]=q[t][k]; p.handle_left[1]=q[t][k]; p.handle_right[1]=q[t][k]
        for fc in fcs: fc.update()
print('DESPIKE',json.dumps(log))
bpy.ops.wm.save_as_mainfile(filepath=out)
if os.environ.get('GLB'):
    for o in list(bpy.data.objects):
        if o.name.startswith('Icosphere'): bpy.data.objects.remove(o)
    bpy.ops.export_scene.gltf(filepath=os.environ['GLB'],export_format='GLB',export_animation_mode='ACTIONS',export_force_sampling=True)
