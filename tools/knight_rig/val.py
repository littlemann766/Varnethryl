import bpy,sys,os,json,math,numpy as np
from mathutils import Euler,Quaternion
G=sys.argv[-2]; MODE=sys.argv[-1]; OUT=f'/tmp/kr/{G}'
bpy.ops.wm.open_mainfile(filepath=f'{OUT}/'+os.environ.get('STG','stage2')+'.blend')
ARM=bpy.data.objects['knight_rig']; fig=bpy.data.objects[f'knight_{G}']; me=fig.data
ARM.data.pose_position='POSE'; sc=bpy.context.scene
me.calc_loop_triangles(); T=np.array([t.vertices for t in me.loop_triangles])
pid=np.zeros(len(me.vertices),np.int32); me.attributes['part'].data.foreach_get('value',pid)
bl=np.zeros(len(me.vertices),np.int32); me.attributes['blended'].data.foreach_get('value',bl)
tb=bl[T].max(1)>0; tcoll=bl[T].max(1)==2
def verts():
    dg=bpy.context.evaluated_depsgraph_get(); ev=fig.evaluated_get(dg); m=ev.to_mesh()
    a=np.zeros(len(m.vertices)*3); m.vertices.foreach_get('co',a); ev.to_mesh_clear(); return a.reshape(-1,3)
def tri_metrics(V):
    A,B,C=V[T[:,0]],V[T[:,1]],V[T[:,2]]
    L=np.stack([np.linalg.norm(B-A,axis=1),np.linalg.norm(C-B,axis=1),np.linalg.norm(A-C,axis=1)],1)
    ar=0.5*np.linalg.norm(np.cross(B-A,C-A),axis=1); return L,ar
for pb in ARM.pose.bones: pb.rotation_mode='QUATERNION'
ARM.animation_data_create()
POSES=[]
def reset():
    ARM.animation_data.action=None
    for pb in ARM.pose.bones: pb.location=(0,0,0); pb.rotation_quaternion=(1,0,0,0); pb.scale=(1,1,1)
reset(); bpy.context.view_layer.update(); V0=verts(); L0,A0=tri_metrics(V0); ok=(L0.min(1)>1e-6)&(A0>1e-10)
# strip non-root translation/scale keys (rotation-only retarget)
for a in bpy.data.actions:
    for fc in list(a.fcurves) if hasattr(a,'fcurves') else []:
        bn=fc.data_path.split('"')[1] if '"' in fc.data_path else ''
        if (fc.data_path.endswith('location') and bn not in ('hips','root')) or fc.data_path.endswith('scale'): a.fcurves.remove(fc)
acts=[a for a in bpy.data.actions if any(k in a.name for k in ('idle','walk','run','attack','hit','death','skill'))]
def q(ax,deg): return Quaternion(ax,math.radians(deg))
EXT={'arms_up':{'upperArm_L':q((0,1,0),-140),'upperArm_R':q((0,1,0),140)},
 'arms_forward':{'upperArm_L':q((1,0,0),95),'upperArm_R':q((1,0,0),95),'foreArm_L':q((1,0,0),60),'foreArm_R':q((1,0,0),60)},
 'elbows_140':{'foreArm_L':q((1,0,0),140),'foreArm_R':q((1,0,0),140)},
 'wrist_twist90':{'hand_L':q((0,0,1),90),'hand_R':q((0,0,1),-90),'foreArm_L':q((1,0,0),40),'foreArm_R':q((1,0,0),40)},
 'kick':{'thigh_L':q((1,0,0),-95),'shin_L':q((1,0,0),110),'thigh_R':q((1,0,0),30)},
 'crouch':{'thigh_L':q((1,0,0),-110),'thigh_R':q((1,0,0),-110),'shin_L':q((1,0,0),130),'shin_R':q((1,0,0),130),'foot_L':q((1,0,0),-30),'foot_R':q((1,0,0),-30)},
 'split':{'thigh_L':q((0,1,0),-60),'thigh_R':q((0,1,0),60)},
 'spine_twist':{'spine2':q((0,0,1),25),'chest':q((0,0,1),20),'upperChest':q((0,0,1),15),'neck':q((0,0,1),35),'head':q((0,0,1),35)},
 'spine_bend':{'spine2':q((1,0,0),25),'chest':q((1,0,0),20),'upperChest':q((1,0,0),15),'head':q((1,0,0),-30)},
 'fist':{f'{f}{k}{X}':q((1,0,0),80) for f in ('index','middle','ring','pinky') for k in (1,2,3) for X in ('_L','_R')},
 'wings_flap':{f'wing_{X}_0{i}':q((0,1,0),(25 if X=="L" else -25)) for X in 'LR' for i in range(1,5)},
 'tabard_sway15':{**{f'tabard_F_0{i}':q((1,0,0),-15) for i in (1,2,3)},**{f'tabard_B_0{i}':q((1,0,0),15) for i in (1,2,3)}},
 'tabard_swing':{**{f'tabard_F_0{i}':q((1,0,0),-30) for i in (1,2,3)},**{f'tabard_B_0{i}':q((1,0,0),30) for i in (1,2,3)}}}
res={}; wpos=np.zeros(len(T)); wneg=np.zeros(len(T)); worst=np.zeros(len(T)); worst_a=np.zeros(len(T)); per_pose={}
def measure(name):
    V=verts(); L,Ar=tri_metrics(V); s=np.abs(L/np.maximum(L0,1e-9)-1).max(1); a=np.abs(Ar/np.maximum(A0,1e-12)-1)
    s[~ok]=0; a[~ok]=0
    r_=L/np.maximum(L0,1e-9)-1; r_[~ok]=0; np.maximum(wpos,r_.max(1),out=wpos); np.minimum(wneg,r_.min(1),out=wneg)
    np.maximum(worst,s,out=worst); np.maximum(worst_a,a,out=worst_a)
    U_=tb&~tcoll; per_pose[name+'#under']=(float(r_.max(1)[U_].max()),float(np.percentile(r_.max(1)[U_],95)),float(np.percentile(r_.max(1)[U_],50)))
    per_pose[name]=(float(s[~tb].max()),float(s[tb].max()) if tb.any() else 0.0,float(np.percentile(s[tb],95)) if tb.any() else 0.0)
    return V,s
SAVE={}
for a in acts:
    reset(); ARM.animation_data.action=a; f0,f1=a.frame_range
    for k,f in enumerate(np.linspace(f0,f1,10)):
        sc.frame_set(int(round(f))); nm=f'{a.name}@{int(f)}'; V,s=measure(nm)
        if k==4: SAVE[a.name]=(V,s)
for nm,P_ in EXT.items():
    reset()
    for b,qq in P_.items():
        if b in ARM.pose.bones: ARM.pose.bones[b].rotation_quaternion=qq
    bpy.context.view_layer.update(); V,s=measure(nm); SAVE[nm]=(V,s)
reset()
mx=lambda x:float(x.max()) if len(x) else 0.0
pc=lambda x:float(np.percentile(x,95)) if len(x) else 0.0
st={'rigid_tris':int((~tb).sum()),'blended_tris':int(tb.sum()),
    'rigid_edge_stretch_max':mx(worst[~tb]),'rigid_edge_stretch_p95':pc(worst[~tb]),'rigid_area_max':mx(worst_a[~tb]),'rigid_area_p95':pc(worst_a[~tb]),
    'blended_edge_stretch_max':mx(worst[tb]),'blended_edge_stretch_p95':pc(worst[tb]),
    'all_edge_stretch_p95':pc(worst),'all_edge_stretch_max':mx(worst),'all_area_max':mx(worst_a),'tris_over_10pct':int((worst>0.10).sum()),'poses':len([k for k in per_pose if '#' not in k])}
# tiny-triangle precision check: area outliers only on sub-mm^2 triangles
st['under_edge_stretch_max_excl_collapsed']=mx(worst[tb&~tcoll]); st['under_edge_stretch_p95_excl_collapsed']=pc(worst[tb&~tcoll]); st['under_edge_stretch_p50']=float(np.median(worst[tb])) if tb.any() else 0; st['under_collapsed_tris']=int(tcoll.sum())
U=tb&~tcoll; st['under_elong_max']=mx(wpos[U]); st['under_elong_p95']=pc(wpos[U]); st['under_elong_p50']=float(np.median(wpos[U])); st['under_compress_p95']=pc(-wneg[U]); st['under_compress_max']=mx(-wneg[U])
np.save(f'{OUT}/under_elong_{MODE}.npy',wpos)
small=A0<1e-7; st['area_max_excl_submm2_tris']=mx(worst_a[~small])
print('STATS',json.dumps(st)); json.dump({'stats':st,'per_pose':per_pose},open(f'{OUT}/stretch_{MODE}.json','w'),indent=1)
# worst offending blended parts
if tb.any():
    tp=pid[T[:,0]]; bad={}
    for t in np.where(tb&(worst>0.10))[0]: bad[int(tp[t])]=max(bad.get(int(tp[t]),0),float(worst[t]))
    print('BADPARTS',sorted(bad.items(),key=lambda kv:-kv[1])[:15])
np.save(f'{OUT}/worst_{MODE}.npy',worst)
import pickle; pickle.dump({k:(v[0],v[1]) for k,v in SAVE.items()},open(f'{OUT}/poses_{MODE}.pkl','wb'))
