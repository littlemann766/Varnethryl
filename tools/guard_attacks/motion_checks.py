# per-clip: single-frame snaps, upper-arm lateral-out angle, wrist twist vs forearm, ground penetration, weapon-hand speed (hit frame)
import bpy,sys,json,math
import numpy as np
from mathutils import Vector
a=sys.argv[sys.argv.index('--')+1:]; blend,acts,out=a[0],a[1].split(','),a[2]
bpy.ops.wm.open_mainfile(filepath=blend); sc=bpy.context.scene; sc.render.fps=30
arm=[o for o in sc.objects if o.type=='ARMATURE'][0]
ob=[o for o in sc.objects if o.type=='MESH' and o.parent==arm and len(o.data.vertices)>1000][0]
gn={g.index:g.name for g in ob.vertex_groups}
body=np.array([not(v.groups and gn[max(v.groups,key=lambda g:g.weight).group].startswith('cape')) for v in ob.data.vertices])
P='mixamorig:'
MAIN=[b.name for b in arm.data.bones if b.name.startswith(P) and not any(k in b.name for k in ('Index','Middle','Ring','Pinky','Thumb','_End','HeadTop'))]
def twist(s):
    h=arm.pose.bones[P+s+'Hand']; f=arm.pose.bones[P+s+'ForeArm']
    R0=(arm.data.bones[P+s+'ForeArm'].matrix_local.to_3x3().inverted()@arm.data.bones[P+s+'Hand'].matrix_local.to_3x3())
    q=(R0.inverted()@f.matrix.to_3x3().inverted()@h.matrix.to_3x3()).to_quaternion()
    # twist about hand's Y (bone axis)
    ang=2*math.degrees(math.atan2(q.y,q.w)); ang=(ang+180)%360-180
    return ang
res={}
for an in acts:
    A=bpy.data.actions[an]; arm.animation_data.action=A; L=int(A.frame_range[1])
    rots=[];outL=[];outR=[];twL=[];twR=[];zmin=[];hand=[]
    for f in range(L+1):
        sc.frame_set(f)
        rots.append({n:(arm.matrix_world@arm.pose.bones[n].matrix).to_quaternion() for n in MAIN})
        hip=(arm.matrix_world@arm.pose.bones[P+'Hips'].matrix).to_3x3()@(arm.matrix_world@arm.data.bones[P+'Hips'].matrix_local).to_3x3().inverted()
        lat=(hip@Vector((1,0,0))).normalized()
        for s,lst in (('Left',outL),('Right',outR)):
            pb=arm.pose.bones[P+s+'Arm']; d=(arm.matrix_world.to_3x3()@(pb.tail-pb.head)).normalized()
            sh=arm.matrix_world@pb.head; sgn=1 if (sh-(arm.matrix_world@arm.pose.bones[P+'Hips'].head)).dot(lat)>0 else -1
            # lateral-out angle of upper arm measured in coronal plane against straight down
            ox=d.dot(lat)*sgn; pr=d-lat*sgn*ox
            lst.append(math.degrees(math.atan2(ox,max(1e-6,pr.length))))
        twL.append(twist('Left')); twR.append(twist('Right'))
        e=ob.evaluated_get(bpy.context.evaluated_depsgraph_get()); m=e.to_mesh(); n=len(m.vertices); c=np.empty(n*3); m.vertices.foreach_get('co',c)
        z=(c.reshape(-1,3)@np.array(ob.matrix_world)[:3,:3].T)[:,2]+ob.matrix_world.translation.z; zmin.append(float(z[body].min())); e.to_mesh_clear()
        hand.append(np.array(arm.matrix_world@arm.pose.bones[P+'RightHand'].head))
    snaps={}
    for nme in MAIN:
        d=[math.degrees(rots[i][nme].rotation_difference(rots[i+1][nme]).angle) for i in range(L)]
        d=[x if x<=180 else 360-x for x in d]
        # snap = a frame step much larger than its neighbours
        for i,x in enumerate(d):
            nb=[d[j] for j in (i-1,i+1) if 0<=j<L]
            if x>35 and x>2.5*max(nb+[1]): snaps.setdefault(nme,[]).append([i,round(x,1)])
    sd=lambda x:x if x<=180 else 360-x
    mx={n:round(max([sd(math.degrees(rots[i][n].rotation_difference(rots[i+1][n]).angle)) for i in range(L)]),1) for n in MAIN}
    hs=np.r_[0,np.linalg.norm(np.diff(np.array(hand),axis=0),axis=1)*30]
    res[an]={'frames':L+1,'snaps':snaps,'max_step_deg_top':sorted(mx.items(),key=lambda x:-x[1])[:4],
      'arm_out_deg_max':{'L':round(max(outL),1),'R':round(max(outR),1)},
      'wrist_twist_deg_absmax':{'L':round(max(map(abs,twL)),1),'R':round(max(map(abs,twR)),1)},
      'body_min_z':round(min(zmin),3),'rest_min_z_ref':None,'r_hand_speed':[round(float(x),2) for x in hs]}
    print('MC',an,json.dumps({k:v for k,v in res[an].items() if k!='r_hand_speed'}))
json.dump(res,open(out,'w'),indent=1)
