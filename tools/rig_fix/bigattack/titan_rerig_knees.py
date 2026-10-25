import bpy,sys,json,os
from mathutils import Vector,Matrix
src,dst=sys.argv[-2],sys.argv[-1]
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=src)
a=[o for o in bpy.data.objects if o.type=='ARMATURE'][0];P=a.pose.bones;sc=bpy.context.scene;S=a.matrix_world.to_scale()[0]
LEG=['hips']+[b+s for s in 'LR' for b in ('thigh_','shin_','foot_')]
# new rest y (armature units) per Beth
NEW={k:v/S for k,v in json.loads(os.environ.get('NEWY','{"shin_R":-0.25,"foot_L":-0.15,"foot_R":-0.15}')).items()}
oldrest={n:a.data.bones[n].matrix_local.copy() for n in LEG+['toe_L','toe_R']}
ATTK={'attack1','attack2','attack3','boulder_hurl','eruption_slam','magma_sweep'}
def tgt(name):
    n=name
    if n in ('idle','wb_idle'): return 7.5
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
        sc.frame_set(f);fr.append({n:P[n].matrix.copy() for n in LEG+['toe_L','toe_R','hand_L','hand_R']})
    samp[act.name]=(f0,f1,fr)
# edit rest: translate bones (orientation/roll kept)
bpy.context.view_layer.objects.active=a;bpy.ops.object.mode_set(mode='EDIT')
for n,y in NEW.items():
    e=a.data.edit_bones[n];dy=y-e.head.y;e.head.y+=dy;e.tail.y+=dy
bpy.ops.object.mode_set(mode='OBJECT')
if os.environ.get('SMOOTHKNEE'):
    import numpy as np
    me=max([o for o in bpy.data.objects if o.type=='MESH' and o.find_armature()==a],key=lambda o:len(o.data.vertices))
    bpy.context.view_layer.objects.active=me;bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='DESELECT');bpy.ops.object.mode_set(mode='OBJECT')
    rad=float(os.environ.get('KRAD','0.2'))*(a.data.bones['thigh_L'].head_local-a.data.bones['foot_L'].head_local).length
    kn=[a.data.bones['shin_'+s_].head_local for s_ in 'LR']
    for v in me.data.vertices:
        if any((me.matrix_world@v.co)/S-k_ if False else ((a.matrix_world.inverted()@(me.matrix_world@v.co))-k_).length<rad for k_ in kn): v.select=True
    me.data.update()
    for g in ['thigh_L','thigh_R','shin_L','shin_R']:
        me.vertex_groups.active_index=me.vertex_groups[g].index
        bpy.ops.object.mode_set(mode='WEIGHT_PAINT');me.data.use_paint_mask_vertex=True
        bpy.ops.object.vertex_group_smooth(group_select_mode='ACTIVE',factor=0.6,repeat=8,expand=0.0)
        bpy.ops.object.mode_set(mode='OBJECT')
    GI={g.index:g for g in me.vertex_groups};buck={}
    for v in me.data.vertices:
        if v.select: buck.setdefault(tuple(round(c,3) for c in v.co),[]).append(v.index)
    nw=0
    for ids in buck.values():
        if len(ids)<2: continue
        acc={}
        for i in ids:
            for e in me.data.vertices[i].groups: acc[e.group]=acc.get(e.group,0)+e.weight/len(ids)
        for i in ids:
            for e in list(me.data.vertices[i].groups):
                if e.group not in acc: GI[e.group].remove([i])
            for gidx,w in acc.items(): GI[gidx].add([i],w,'REPLACE')
        nw+=1
    print('WELDW',nw)
    bpy.ops.object.vertex_group_limit_total(limit=4);bpy.ops.object.vertex_group_normalize_all(lock_active=False)
    print('SMOOTHKNEE',sum(v.select for v in me.data.vertices))
    bpy.context.view_layer.objects.active=a
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
    nF=len(fr);LOAD=[0.0]*nF
    if name in ATTK and nF>3:
        sp=[0.0]+[max((fr[i]['hand_'+x].translation-fr[i-1]['hand_'+x].translation).length for x in 'LR') for i in range(1,nF)]
        sm=[sum(sp[max(0,j-4):j+5])/len(sp[max(0,j-4):j+5]) for j in range(nF)]
        dl=[sm[max(0,j-3)] for j in range(nF)];mx=max(dl) or 1;LOAD=[x/mx for x in dl]
    AMP=float(os.environ.get('AMPK','0.04'))*(L1['L']+L2['L'])*fr[0]['hips'].to_scale()[0]
    def H(fm,s,d): m=fm['hips'].copy();m.translation-=up*d;return (m@R['hips'].inverted()@R['thigh_'+s]).translation
    def kmin(d):
        w=99
        for j,(fm,ft) in enumerate(zip(fr,feet)):
            for s in 'LR':
                h=H(fm,s,d+AMP*LOAD[j]);A=ft[s].translation;D=(A-h).length;k_=fm['thigh_'+s].to_scale()[0];l1,l2=L1[s]*k_,L2[s]*k_
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
        hm=fm['hips'].copy();hm.translation-=up*(d+AMP*LOAD[i]);P['hips'].matrix=hm;bpy.context.view_layer.update()
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
