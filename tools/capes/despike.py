# Clip-only de-spike / loop-seam fix. Re-runnable on any re-skinned version of the same rig.
# usage: blender -b -P despike.py -- in.glb out.glb '<clip regex>' '<bone regex>' [thresh_deg=20] [seam=0|N]
import bpy,sys,re,json,math
from mathutils import Quaternion
a=sys.argv[sys.argv.index('--')+1:]; src,out,CR,BR=a[:4]; TH=math.radians(float(a[4]) if len(a)>4 else 20); SEAM=int(a[5]) if len(a)>5 else 0; RATE=math.radians(float(a[6])) if len(a)>6 else 0  # optional max deg/frame
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.context.scene.render.fps=30; bpy.ops.import_scene.gltf(filepath=src); bpy.context.scene.render.fps=30
arm=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]
def qcurves(act):
    d={}
    for fc in act.fcurves:
        m=re.match(r'pose\.bones\["(.+)"\]\.rotation_quaternion',fc.data_path)
        if m and re.search(BR,m.group(1)): d.setdefault(m.group(1),[None]*4)[fc.array_index]=fc
    return {k:v for k,v in d.items() if all(v)}
def getq(fcs):
    n=len(fcs[0].keyframe_points); Q=[Quaternion([fcs[i].keyframe_points[j].co[1] for i in range(4)]) for j in range(n)]
    for j in range(1,n):
        if Q[j].dot(Q[j-1])<0: Q[j].negate()
    return Q
def setq(fcs,Q):
    for j,q in enumerate(Q):
        for i in range(4):
            kp=fcs[i].keyframe_points[j]; kp.co[1]=q[i]; kp.handle_left[1]=q[i]; kp.handle_right[1]=q[i]
    for f in fcs: f.update()
def step(Q): return max([Q[j].rotation_difference(Q[j+1]).angle for j in range(len(Q)-1)] or [0])
def seamd(Q): return Q[-1].rotation_difference(Q[0]).angle
res={}
for act in bpy.data.actions:
    cl=act.name.split('_'+arm.name)[0]
    if not re.search(CR,cl): continue
    r={}
    for bn,fcs in qcurves(act).items():
        Q=getq(fcs); b0,s0=step(Q),seamd(Q); n=len(Q); fixed=0
        for it in range(3):
            for j in range(1,n-1):
                d1=Q[j-1].rotation_difference(Q[j]).angle; d2=Q[j].rotation_difference(Q[j+1]).angle; d=Q[j-1].rotation_difference(Q[j+1]).angle
                if d1+d2-d>TH: Q[j]=Q[j-1].slerp(Q[j+1],0.5); fixed+=1
        if RATE and n>2 and step(Q)>RATE:
            for it in range(30):
                F=[Q[0]]
                for j in range(1,n):
                    d=F[-1].rotation_difference(Q[j]).angle; F.append(F[-1].slerp(Q[j],min(1,RATE/d)) if d>RATE else Q[j])
                Bk=[Q[-1]]
                for j in range(n-2,-1,-1):
                    d=Bk[-1].rotation_difference(Q[j]).angle; Bk.append(Bk[-1].slerp(Q[j],min(1,RATE/d)) if d>RATE else Q[j])
                Bk=Bk[::-1]; Q=[F[j].slerp(Bk[j] if F[j].dot(Bk[j])>=0 else -Bk[j],0.5) for j in range(n)]
                if step(Q)<=RATE*1.05: break
            fixed+=1
        if SEAM and n>SEAM+2:
            q0=Q[0]
            for k in range(SEAM):
                j=n-SEAM+k; t=(k+1)/(SEAM+1)
                Q[j]=Q[j].slerp(q0 if Q[j].dot(q0)>=0 else -q0,t)
        setq(fcs,Q); a1,s1=step(Q),seamd(Q)
        if fixed or SEAM: r[bn]={'max_step_deg':[round(math.degrees(b0),1),round(math.degrees(a1),1)],'seam_deg':[round(math.degrees(s0),1),round(math.degrees(s1),1)],'frames_fixed':fixed}
    res[cl]=r; print('CLIP',cl,json.dumps({k:v for k,v in r.items() if v['frames_fixed'] or SEAM}),flush=True)
json.dump(res,open(out.replace('.glb','.despike.json'),'w'),indent=1)
bpy.ops.export_scene.gltf(filepath=out,export_format='GLB',export_animation_mode='ACTIONS',export_force_sampling=True,export_yup=True,export_skins=True,export_apply=False)
