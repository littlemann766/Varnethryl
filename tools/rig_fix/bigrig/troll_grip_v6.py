import bpy,sys,json,math
from mathutils import Vector,Quaternion,Matrix
src,wpn,dst,mode=sys.argv[-4:]
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=src)
arm=[o for o in bpy.data.objects if o.type=='ARMATURE'][0];P=arm.pose.bones;sc=bpy.context.scene
body=max([o for o in bpy.data.objects if o.type=='MESH' and o.find_armature()==arm],key=lambda o:len(o.data.vertices))
S=bpy.data.objects['weapon_R']
for c in list(S.children_recursive): bpy.data.objects.remove(c,do_unlink=True)
before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=wpn);new=set(bpy.data.objects)-before
for o in new:
    if o.parent is None: o.parent=S;o.matrix_parent_inverse=Matrix.Identity(4);o.location=(0,0,0);o.rotation_mode='QUATERNION';o.rotation_quaternion=(1,0,0,0);o.scale=(1,1,1)
W=[o for o in new if o.type=='MESH'];bpy.context.view_layer.update()
gi={g.name:g.index for g in body.vertex_groups}
HV=[v.index for v in body.data.vertices if v.groups and max(v.groups,key=lambda g:g.weight).group in (gi.get('hand_R'),gi.get('fingers_R'))]
FI=[v.index for v in body.data.vertices if v.groups and max(v.groups,key=lambda g:g.weight).group==gi.get('fingers_R')]
def axis():
    m=S.matrix_world;o=m.translation.copy();d=(m.to_3x3()@Vector((0,0,1))).normalized()  # glTF +Y -> Blender local +Z for objects
    return o,d
def dists(idx):
    me=body.evaluated_get(bpy.context.evaluated_depsgraph_get());md=me.to_mesh();o,d=axis();out=[]
    for i in idx:
        w=body.matrix_world@md.vertices[i].co-o;along=w.dot(d);out.append(((w-along*d).length,along))
    body.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh_clear();return out
# weapon handle radius actual (world): verts of weapon near origin along axis
o,d=axis();wr=[];sc_=S.matrix_world.to_scale()[0]
for ob in W:
    for v in ob.data.vertices:
        w=ob.matrix_world@v.co-o;al=w.dot(d)
        if abs(al)<0.15*sc_: wr.append((w-al*d).length)
wr.sort();R=wr[len(wr)//2] if wr else 0.15
info={'handle_r_world':round(R,3),'scale':round(sc_,3)}
fb=P['fingers_R'];fb.rotation_mode='QUATERNION'
arm.animation_data_create()
acts=list(bpy.data.actions)
if mode=='curl':
    arm.animation_data.action=None
    for pb in P: pb.matrix_basis.identity()
    bpy.context.view_layer.update()
    best=None
    for ax in ('X','-X','Z','-Z'):
        v={'X':Vector((1,0,0)),'-X':Vector((-1,0,0)),'Z':Vector((0,0,1)),'-Z':Vector((0,0,-1))}[ax]
        for a in range(70,91,5):
            fb.rotation_quaternion=Quaternion(v,math.radians(a));bpy.context.view_layer.update()
            me=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mdh=me.to_mesh()
            HI=[i for i in HV if i not in set(FI)]
            pc=sum((body.matrix_world@mdh.vertices[i].co for i in HI),Vector())/len(HI)
            fc_=sum((body.matrix_world@mdh.vertices[i].co for i in FI),Vector())/len(FI)
            o_,d_=axis();n=(fc_-pc);n=(n-n.dot(d_)*d_).normalized();c0=pc+n*0.15
            ds=[];inside=0
            for i in FI:
                w=body.matrix_world@mdh.vertices[i].co-c0;ds.append((w-w.dot(d_)*d_).length)
            me.to_mesh_clear();ds.sort();md=ds[len(ds)//2];mn=ds[0]
            c=abs(md-0.18)+(5 if mn<0.14 else 0)
            if best is None or c<best[0]: best=(c,ax,a,md,mn)
    _,ax,a,md,mn=best;info.update(cyl='0.30m dia, centre 0.15m off palm',curl_axis=ax,curl_deg=a,finger_median=round(md,3),finger_min=round(mn,3))
    v={'X':Vector((1,0,0)),'-X':Vector((-1,0,0)),'Z':Vector((0,0,1)),'-Z':Vector((0,0,-1))}[ax];CQ=Quaternion(v,math.radians(a))
    for act in acts:
        arm.animation_data.action=act
        for fc in [f for f in act.fcurves if f.data_path=='pose.bones["fingers_R"].rotation_quaternion']: act.fcurves.remove(fc)
        f0,f1=map(int,act.frame_range)
        for f in (f0,f1): fb.rotation_quaternion=CQ;fb.keyframe_insert('rotation_quaternion',frame=f)
        for fc in act.fcurves:
            if fc.data_path.startswith('pose.bones["fingers_R"]'):
                for k in fc.keyframe_points:k.interpolation='CONSTANT'
    info['grip_quat_local_wxyz']=[round(x,4) for x in CQ]
# per-frame palm check: hand/finger verts inside the handle cylinder
worst={}
for act in acts:
    arm.animation_data.action=act;f0,f1=map(int,act.frame_range);w=9
    for f in range(f0,f1+1,2):
        sc.frame_set(f);ds=[x for x,al in dists(HV) if abs(al)<0.3*sc_]
        if ds: w=min(w,min(ds))
    worst[act.name.split('_Armature')[0]]=round(w/R,3)
info['min_hand_dist_over_handle_r']=worst
print('TROLL',json.dumps(info))
bpy.ops.export_scene.gltf(filepath=dst,export_format='GLB',export_animation_mode='ACTIONS',export_force_sampling=True,export_skins=True,export_def_bones=False,export_optimize_animation_size=False)
