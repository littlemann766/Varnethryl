# generic despike/cyclic smooth for creature run clips: bones whose per-frame rotation > LIM get iterative cyclic smoothing
import bpy,sys,math,json,os
import numpy as np
from mathutils import Quaternion
a=sys.argv[sys.argv.index('--')+1:]; src,out=a[0],a[1]; CL=os.environ.get('CL','run').split(','); LIM=float(os.environ.get('LIM','40'))
bpy.ops.wm.read_factory_settings(use_empty=True); sc=bpy.context.scene; sc.render.fps=30; sc.render.fps_base=1
bpy.ops.import_scene.gltf(filepath=src)
for x in list(bpy.data.actions): x.name=x.name[:x.name.rindex('_',0,x.name.rindex('_'))] if x.name.count('_')>=2 and x.name.endswith('_Rig') else (x.name[:-9] if x.name.endswith('_Armature') else x.name)
arm=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]; rep={}
def mx(Q):
    n=len(Q); return max(math.degrees(2*math.acos(min(1,abs(float(Q[i]@Q[i+1]))))) for i in range(n-1))
for act in bpy.data.actions:
    if act.name not in CL: continue
    BS=os.environ.get("BONES")
    for pb in arm.pose.bones:
        if BS and pb.name not in BS.split(","): continue
        fcs=[act.fcurves.find('pose.bones["%s"].rotation_quaternion'%pb.name,index=k) for k in range(4)]
        if any(f is None for f in fcs): continue
        n=len(fcs[0].keyframe_points)
        Q=np.array([[fcs[k].keyframe_points[t].co[1] for k in range(4)] for t in range(n)])
        for t in range(1,n):
            if Q[t]@Q[t-1]<0: Q[t]*=-1
        b=mx(Q)
        if b<=LIM: continue
        it=0
        while mx(Q)>LIM and it<12:
            m=len(Q); P=Q.copy()
            for t in range(m):
                acc=np.zeros(4)
                for d,w in ((-1,.25),(0,.5),(1,.25)):
                    q=P[(t+d)%m] if os.environ.get('CYC','1')=='1' else P[min(m-1,max(0,t+d))]; acc+=w*(q if q@P[t]>=0 else -q)
                Q[t]=acc/np.linalg.norm(acc)
            it+=1
        rep['%s/%s'%(act.name,pb.name)]=[round(b,1),round(mx(Q),1),it]
        for t in range(n):
            for k in range(4):
                p=fcs[k].keyframe_points[t]; p.co[1]=Q[t][k]; p.handle_left[1]=Q[t][k]; p.handle_right[1]=Q[t][k]
        for f in fcs: f.update()
print('CFIX',json.dumps(rep)); json.dump(rep,open(out+'.cfix.json','w'),indent=1)
for o in list(bpy.data.objects):
    if o.name.startswith('Icosphere'): bpy.data.objects.remove(o)
for x in bpy.data.actions: x.use_fake_user=True
bpy.ops.wm.save_as_mainfile(filepath=out+'.blend')
bpy.ops.export_scene.gltf(filepath=out,export_format='GLB',export_animation_mode='ACTIONS',export_force_sampling=True)
