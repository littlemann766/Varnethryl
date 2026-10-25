import bpy,sys,numpy as np
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=sys.argv[-1])
arm=[o for o in bpy.data.objects if o.type=='ARMATURE'][0];me=max([o for o in bpy.data.objects if o.type=='MESH'],key=lambda o:len(o.data.vertices));sc=bpy.context.scene
GN={g.index:g.name for g in me.vertex_groups}
dom=np.array([GN[max(v.groups,key=lambda g:g.weight).group] if v.groups else '' for v in me.data.vertices])
H=np.array([d.startswith(('index','middle','ring','pinky','thumb','hand')) for d in dom])
TIP=np.array([d[:-2] in ('index3','middle3','ring3','pinky3') for d in dom])
EI=np.array([e.vertices[:] for e in me.data.edges]);EI=EI[H[EI[:,0]]&H[EI[:,1]]]
def cur():
    e=me.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();R=np.empty(len(m.vertices)*3);m.vertices.foreach_get('co',R);e.to_mesh_clear();return R.reshape(-1,3)
arm.animation_data_create();arm.animation_data.action=None
for p in arm.pose.bones:p.matrix_basis.identity()
R0=np.array([tuple(v.co) for v in me.data.vertices]);L0=np.linalg.norm(R0[EI[:,0]]-R0[EI[:,1]],axis=1);ok=L0>0.25*np.median(L0)
out=[]
for act in bpy.data.actions:
    arm.animation_data.action=act;f0,f1=map(int,act.frame_range);w=(0,0);pen=9
    for f in np.linspace(f0,f1,6).astype(int):
        sc.frame_set(int(f));R=cur();r_=(np.linalg.norm(R[EI[:,0]]-R[EI[:,1]],axis=1)/np.where(ok,L0,1))[ok];r=np.maximum(r_/np.median(r_)-1,0)
        p=np.percentile(r,99);w=max(w,(round(float(p),3),round(float(r.max()),2)))
        # palm pass-through: fingertip verts vs palm plane (hand bone head + palm normal from evaluated hand verts)
        for s in 'LR':
            hb=arm.pose.bones['hand_'+s];hh=arm.matrix_world.inverted()@(arm.matrix_world@hb.head)
            tips=R[TIP&np.char.endswith(dom.astype(str),'_'+s)]
            palm=R[np.char.startswith(dom.astype(str),'hand_'+s)]
            if len(tips) and len(palm):
                pp=palm[::max(1,len(palm)//1500)];d=np.sqrt(((tips[:,None,:]-pp[None])**2).sum(-1)).min(1);pen=min(pen,float(np.percentile(d,1))/float(np.median(r_)))
    out.append((act.name.split('_Armature')[0].split('_Darius')[0],w,round(pen,3)))
print('HSTR',out)
