import bpy,sys,json,math
import numpy as np
from mathutils import Vector,Matrix,Quaternion
a=sys.argv[sys.argv.index('--')+1:]; bpy.ops.wm.open_mainfile(filepath=a[0]); out=a[1]
sc=bpy.context.scene; arm=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]
ob=[o for o in bpy.data.objects if o.type=='MESH' and o.parent==arm and len(o.data.vertices)>1000][0]
MX='mixamorig:LeftHand' in arm.data.bones
BN=(lambda k,s:{'hand':'mixamorig:%sHand','fore':'mixamorig:%sForeArm','hips':'mixamorig:Hips'}[k].replace('%s','Left' if s=='L' else 'Right') ) if MX else (lambda k,s:{'hand':'hand_'+s,'fore':'foreArm_'+s,'hips':'hips'}[k])
if BN('hand','L') not in arm.data.bones: json.dump({'skip':'no hands'},open(out,'w')); sys.exit()
gi={g.name:g.index for g in ob.vertex_groups}; me=ob.data
M=arm.matrix_world; Mi=M.inverted(); Mo=Mi@ob.matrix_world
def verts(g):
    i=gi[g]; return np.array([tuple(Mo@v.co) for v in me.vertices if v.groups and max(v.groups,key=lambda q:q.weight).group==i])
hips=arm.data.bones[BN('hips','L')].head_local
res={'rest':{}}; N0={}
for s in 'LR':
    V=verts(BN('hand',s)) if BN('hand',s) in gi else np.zeros((0,3)); h=arm.data.bones[BN('hand',s)].head_local; f=arm.data.bones[BN('fore',s)].head_local
    if len(V)<20: N0[s]=None; res['rest'][s]={'nverts':len(V)}; continue
    d=Vector(V.mean(0))-h; d.normalize(); ax=(h-f).normalized()
    P=V-V.mean(0); P=P-np.outer(P@np.array(d),np.array(d)); w,U=np.linalg.eigh(P.T@P); n=Vector(U[:,0])
    # sign: rest arm horizontal -> palm down; arm hanging -> palm toward body
    if abs(ax.z)<0.6: n= n if n.z<0 else -n
    else:
        inw=Vector((hips.x-h.x,hips.y-h.y,0)).normalized(); n= n if n.dot(inw)>0 else -n
    N0[s]=n; res['rest'][s]={'arm_dir':[round(x,2) for x in ax],'palm':[round(x,2) for x in n],'nverts':len(V)}
want=a[2].split(',')
for act in bpy.data.actions:
    if not any(act.name.startswith(w) for w in want): continue
    arm.animation_data.action=act; f0,f1=map(int,act.frame_range); r={}
    for s in 'LR':
        up=[];inw=[];tw=[];swg=[]
        for fr in range(f0,f1+1,2):
            sc.frame_set(fr); pb=arm.pose.bones[BN('hand',s)]; pf=arm.pose.bones[BN('fore',s)]
            R=pb.matrix.to_3x3(); Rr=arm.data.bones[BN('hand',s)].matrix_local.to_3x3(); n=(M.to_3x3()@R@Rr.inverted()@N0[s]).normalized() if N0[s] else Vector((0,0,0))
            hp=M@pb.head; hz=M@arm.pose.bones[BN('hips','L')].head
            iv=Vector((hz.x-hp.x,hz.y-hp.y,0)); iv=iv.normalized() if iv.length>1e-4 else iv
            up.append(n.z); inw.append(n.dot(iv))
            F0=arm.data.bones[BN('fore',s)].matrix_local.to_3x3(); rel=((F0.inverted()@Rr).inverted()@pf.matrix.to_3x3().inverted()@R).to_quaternion(); axl=(F0.inverted()@(arm.data.bones[BN("hand",s)].head_local-arm.data.bones[BN("fore",s)].head_local)).normalized(); qa=Vector(rel[1:]); pr=axl*qa.dot(axl); tq=Quaternion((rel[0],*pr)); tq.normalize() if tq.magnitude>1e-6 else None; tw.append(math.degrees(2*math.atan2(Vector(tq[1:]).length,abs(tq[0])))); swg.append(math.degrees(rel.angle) if rel.angle<=math.pi else 360-math.degrees(rel.angle))
        up=np.array(up); r[s]={'palm_up_frac':round(float((up>0.6).mean()),3),'max_up':round(float(up.max()),2),'mean_inward':round(float(np.mean(inw)),2),'max_twist_deg':round(float(np.max(np.abs(tw))),1),'max_wrist_deg':round(float(np.max(swg)),1)}
    res[act.name]=r
json.dump(res,open(out,'w'),indent=1)
