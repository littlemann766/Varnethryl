import bpy,sys,json
from mathutils import Vector,Matrix
src,dst=sys.argv[-2],sys.argv[-1]
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=src)
a=[o for o in bpy.data.objects if o.type=='ARMATURE'][0];P=a.pose.bones;sc=bpy.context.scene;S=a.matrix_world.to_scale()[0]
LEG=['hips']+[b+s for s in 'LR' for b in ('thigh_','shin_','foot_')]
# new rest y (armature units) per Beth
NEW={'shin_R':-0.25/S,'foot_L':-0.15/S,'foot_R':-0.15/S}
oldrest={n:a.data.bones[n].matrix_local.copy() for n in LEG+['toe_L','toe_R']}
def tgt(name):
    n=name
    if n in ('idle',): return 7.5
    if n in ('walk','run'): return 5.5
    if n in ('attack1','attack2','attack3','eruption_slam','magma_sweep','boulder_hurl','windup','skill','volcano_roar'): return 4.0
    return 3.0
acts=list(bpy.data.actions); samp={}
a.animation_data_create()
for act in acts:
    a.animation_data.action=act
    try: a.animation_data.action_slot=act.slots[0]
    except: pass
    f0,f1=map(int,act.frame_range);fr=[]
    for f in range(f0,f1+1):
        sc.frame_set(f);fr.append({n:P[n].matrix.copy() for n in LEG+['toe_L','toe_R']})
    samp[act.name]=(f0,f1,fr)
# edit rest: translate bones (orientation/roll kept)
bpy.context.view_layer.objects.active=a;bpy.ops.object.mode_set(mode='EDIT')
for n,y in NEW.items():
    e=a.data.edit_bones[n];dy=y-e.head.y;e.head.y+=dy;e.tail.y+=dy
bpy.ops.object.mode_set(mode='OBJECT')
R={n:a.data.bones[n].matrix_local.copy() for n in LEG+['toe_L','toe_R']}
up=Vector((0,0,1))
def fwd(m_foot,m_toe,u):
    t=(m_toe@Vector((0,a.data.bones['toe_L'].length,0)) if False else m_toe.translation)
    f=t-m_foot.translation; f=f-f.dot(u)*u; return f.normalized()
L1={s:(R['shin_'+s].translation-R['thigh_'+s].translation).length for s in 'LR'}
L2={s:(R['foot_'+s].translation-R['shin_'+s].translation).length for s in 'LR'}
def frame0(d,f):
    d=d.normalized();f=(f-f.dot(d)*d).normalized();return Matrix((d,f,d.cross(f))).transposed()
rep={}
for act in acts:
    f0,f1,fr=samp[act.name];name=act.name.split('_Armature')[0].split('_Darius')[0]
    # new foot matrices
    feet=[{s:fm['foot_'+s]@oldrest['foot_'+s].inverted()@R['foot_'+s] for s in 'LR'} for fm in fr]
    # hip offset of thigh head from hips pose is rigid: H = hips@hipsRest^-1@thighRest
    def H(fm,s,d): m=fm['hips'].copy();m.translation-=up*d;return (m@R['hips'].inverted()@R['thigh_'+s]).translation
    def kmin(d):
        w=99
        for fm,ft in zip(fr,feet):
            for s in 'LR':
                h=H(fm,s,d);A=ft[s].translation;D=(A-h).length;k_=fm['thigh_'+s].to_scale()[0];l1,l2=L1[s]*k_,L2[s]*k_
                if D>=l1+l2: return -1
                x=(l1*l1-l2*l2+D*D)/(2*D);w=min(w,(max(l1*l1-x*x,0))**.5/(l1+l2)*100)
        return w
    T=tgt(name);lo,hi=0.0,3.0*fr[0]['hips'].to_scale()[0]
    pass #,name,kmin(0),kmin(0.1),kmin(0.3),L1,L2,[(fr[0]['foot_'+s_]@oldrest['foot_'+s_].inverted()@R['foot_'+s_]).translation for s_ in 'LR'],[H(fr[0],s_,0) for s_ in 'LR'])
    if kmin(0)<T:
        for _ in range(30):
            m=(lo+hi)/2
            if kmin(m)>=T: hi=m
            else: lo=m
        d=hi if kmin(hi)>=0 else 0.0
    else: d=0.0
    # rewrite
    a.animation_data.action=act
    try: a.animation_data.action_slot=act.slots[0]
    except: pass
    fcs=act.fcurves if hasattr(act,'fcurves') else None
    for fc in list(act.fcurves):
        if any(fc.data_path.startswith(f'pose.bones["{n}"]') for n in LEG): act.fcurves.remove(fc)
    for i,f in enumerate(range(f0,f1+1)):
        fm=fr[i];sc.frame_set(f)
        hm=fm['hips'].copy();hm.translation-=up*d;P['hips'].matrix=hm;bpy.context.view_layer.update()
        for s in 'LR':
            h=P['thigh_'+s].head.copy();A=feet[i][s].translation.copy();u=(A-h).normalized()
            bf=(hm.to_3x3()@R['hips'].to_3x3().inverted()@Vector((0,-1,0)));bf=(bf-bf.dot(u)*u).normalized();tf=fwd(feet[i][s],fm['toe_'+s],u);fw=(bf*2+tf).normalized() if tf.dot(bf)>0 else bf;fw=(fw-fw.dot(u)*u).normalized();D=(A-h).length;k_=fm['thigh_'+s].to_scale();l1,l2=L1[s]*k_[0],L2[s]*k_[0];D=min(D,l1+l2-1e-4)
            x=(l1*l1-l2*l2+D*D)/(2*D);hh=max(l1*l1-x*x,0)**.5;K=h+u*x+fw*hh
            f0r=fwd(R['foot_'+s],R['toe_'+s],(R['foot_'+s].translation-R['thigh_'+s].translation).normalized())
            for b,p,q in (('thigh_'+s,h,K),('shin_'+s,K,A)):
                rp,rq=R[b].translation,(R['shin_'+s] if b.startswith('thigh') else R['foot_'+s]).translation
                rot=frame0(q-p,fw)@frame0(rq-rp,f0r).inverted()
                m=Matrix.LocRotScale(p,(rot@R[b].to_3x3()).to_quaternion(),fm[b].to_scale());P[b].matrix=m;bpy.context.view_layer.update()
            P['foot_'+s].matrix=feet[i][s];bpy.context.view_layer.update()
        for n in LEG:
            P[n].keyframe_insert('location',frame=f);P[n].keyframe_insert('rotation_quaternion',frame=f);P[n].keyframe_insert('scale',frame=f)
    rep[name]=(round(d*S/fr[0]['hips'].to_scale()[0],3),T,round(kmin(d),1),round(kmin(0),1))
print('RERIG',json.dumps(rep))
bpy.ops.export_scene.gltf(filepath=dst, export_format='GLB', export_animation_mode='ACTIONS', export_force_sampling=True, export_skins=True, export_def_bones=False, export_optimize_animation_size=False)
