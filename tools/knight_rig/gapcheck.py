import bpy,sys,os,json,math,numpy as np
from mathutils import Quaternion,Vector
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view
from scipy import ndimage
G=sys.argv[-2]; STG=sys.argv[-1]; OUT=f'/tmp/kr/{G}'; RAW=f'/tmp/kr/gc_{G}_{STG}'; os.makedirs(RAW,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=f'{OUT}/{STG}.blend')
ARM=bpy.data.objects['knight_rig']; fig=bpy.data.objects[f'knight_{G}']; me=fig.data; ARM.data.pose_position='POSE'; sc=bpy.context.scene
for a in bpy.data.actions:
    for fc in list(a.fcurves) if hasattr(a,'fcurves') else []:
        bn=fc.data_path.split('"')[1] if '"' in fc.data_path else ''
        if (fc.data_path.endswith('location') and bn not in ('hips','root')) or fc.data_path.endswith('scale'): a.fcurves.remove(fc)
for pb in ARM.pose.bones: pb.rotation_mode='QUATERNION'
ARM.animation_data_create()
me.calc_loop_triangles(); T=np.array([t.vertices for t in me.loop_triangles])
bl=np.zeros(len(me.vertices),np.int32); me.attributes['blended'].data.foreach_get('value',bl)
gn=[g.name for g in fig.vertex_groups]
vb=np.array([gn[max(v.groups,key=lambda g:g.weight).group] if len(v.groups) else 'hips' for v in me.vertices],dtype=object)
PT=bl[T].max(1)==0
tb=np.where(PT,vb[T[:,0]],'')
# diagnostic material: front plate white, back-face red, underlayer blue
m=bpy.data.materials.new('diag'); m.use_nodes=True; nt=m.node_tree; nt.nodes.clear()
o=nt.nodes.new('ShaderNodeOutputMaterial'); e=nt.nodes.new('ShaderNodeEmission'); geo=nt.nodes.new('ShaderNodeNewGeometry')
at=nt.nodes.new('ShaderNodeAttribute'); at.attribute_name='blended'
m1=nt.nodes.new('ShaderNodeMix'); m1.data_type='RGBA'; m1.inputs[6].default_value=(1,1,1,1); m1.inputs[7].default_value=(0,0,1,1)
m2=nt.nodes.new('ShaderNodeMix'); m2.data_type='RGBA'; m2.inputs[7].default_value=(1,0,0,1)
nt.links.new(at.outputs['Fac'],m1.inputs[0]); nt.links.new(m1.outputs[2],m2.inputs[6])
mx=nt.nodes.new('ShaderNodeMath'); mx.operation='MULTIPLY'; nt.links.new(geo.outputs['Backfacing'],mx.inputs[0]); mx.inputs[1].default_value=1.0
inv=nt.nodes.new('ShaderNodeMath'); inv.operation='SUBTRACT'; inv.inputs[0].default_value=1.0; nt.links.new(at.outputs['Fac'],inv.inputs[1])
nt.links.new(geo.outputs['Backfacing'],mx.inputs[0]); nt.links.new(inv.outputs[0],mx.inputs[1]); nt.links.new(mx.outputs[0],m2.inputs[0])
nt.links.new(m2.outputs[2],e.inputs[0]); nt.links.new(e.outputs[0],o.inputs[0]); m.use_backface_culling=False
sc.view_layers[0].material_override=m
sc.render.engine='BLENDER_EEVEE'; sc.eevee.taa_render_samples=1
w=bpy.data.worlds.new('w'); sc.world=w; w.use_nodes=True; w.node_tree.nodes['Background'].inputs[0].default_value=(0,1,0,1)
sc.view_settings.view_transform='Standard'; sc.render.resolution_x=360; sc.render.resolution_y=480; sc.render.image_settings.file_format='PNG'
cam=bpy.data.objects.new('cam',bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera=cam; cam.data.type='ORTHO'; cam.data.ortho_scale=2.6
def look(yaw,tgt=(0,-0.1,1.0),dist=5,el=0.6):
    t=Vector(tgt); cam.location=t+Vector((math.sin(math.radians(yaw))*dist,-math.cos(math.radians(yaw))*dist,el)); cam.rotation_euler=(t-cam.location).to_track_quat('-Z','Y').to_euler()
JB=['neck','head','upperArm_L','upperArm_R','foreArm_L','foreArm_R','hand_L','hand_R','spine2','chest','thigh_L','thigh_R','shin_L','shin_R','foot_L','foot_R']
PAIRS=[('upperChest','neck'),('neck','head'),('upperChest','head'),('hips','spine2'),('spine2','chest'),('chest','upperChest')]
for X in ('_L','_R'): PAIRS+=[('shoulder'+X,'upperArm'+X),('upperChest'+X[:0],'upperArm'+X),('chest','upperArm'+X),('upperArm'+X,'foreArm'+X),('foreArm'+X,'hand'+X),('hips','thigh'+X),('thigh'+X,'shin'+X),('shin'+X,'foot'+X),('foot'+X,'toe'+X)]
PAIRS=[(a,b) for a,b in PAIRS if a in gn and b in gn]
rng=np.random.default_rng(1); SAMP={b:None for b in gn}
for b in gn:
    ids=np.where((vb==b)&(bl==0))[0]; SAMP[b]=ids if len(ids)<=600 else rng.choice(ids,600,replace=False)
def verts():
    dg=bpy.context.evaluated_depsgraph_get(); ev=fig.evaluated_get(dg); mm=ev.to_mesh(); a=np.zeros(len(mm.vertices)*3); mm.vertices.foreach_get('co',a); ev.to_mesh_clear(); return a.reshape(-1,3)
def pen(V):
    out={}; trees={}
    for a,b in PAIRS:
        for host,guest in ((a,b),(b,a)):
            if host not in trees:
                ft=T[tb==host]; trees[host]=BVHTree.FromPolygons([tuple(x) for x in V],[tuple(x) for x in ft]) if len(ft) else None
            tr=trees[host]
            if tr is None or len(SAMP[guest])==0: continue
            d=np.zeros(len(SAMP[guest]))
            for k,vi in enumerate(SAMP[guest]):
                r=tr.find_nearest(Vector(V[vi]),0.03)
                if r[0] is not None:
                    s=(Vector(V[vi])-r[0]).dot(r[1]); d[k]=max(0.0,-s)
            out[(host,guest)]=d
    return out
def setpose(p):
    ARM.animation_data.action=None
    for pb in ARM.pose.bones: pb.location=(0,0,0); pb.rotation_quaternion=(1,0,0,0)
    if p[0]=='ACT': ARM.animation_data.action=p[1]; sc.frame_set(p[2])
    else:
        for b,qq in p[1].items():
            if b in ARM.pose.bones: ARM.pose.bones[b].rotation_quaternion=qq
    bpy.context.view_layer.update()
def q(ax,deg): return Quaternion(ax,math.radians(deg))
exec(open('/tmp/kr/poses_ext.py').read())
acts=[a for a in bpy.data.actions if any(k in a.name for k in ('idle','walk','run','attack','hit','death','skill'))]
POSES=[('rest',('EXT',{}))]
for a in acts:
    f0,f1=a.frame_range
    for f in np.linspace(f0,f1,10): POSES.append((f'{a.name.split(".")[0]}@{int(round(f))}',('ACT',a,int(round(f)))))
for nm,P_ in EXT.items(): POSES.append((nm,('EXT',P_)))
SAVE=set(sys.argv[-3].split(',')) if len(sys.argv)>=4 else set()
setpose(('EXT',{})); base=pen(verts())
res={}
for nm,p in POSES:
    setpose(p); V=verts(); pd=pen(V); newpen=0; md=0.0
    for k,d in pd.items():
        d0=base.get(k,np.zeros_like(d)); ex=d-d0-0.003; newpen+=int((ex>0).sum()); md=max(md,float(ex.max()) if len(ex) else 0)
    # joint screen regions
    r={'pen_verts':newpen,'pen_max_mm':round(max(md,0)*1000+ (3 if md>0 else 0),1)}
    gap=back=under=0; jpx=0
    for yaw in (25,205,90):
        look(yaw); fp=f'{RAW}/{nm.replace("@","_")}_{yaw}.png'; sc.render.filepath=fp; bpy.ops.render.render(write_still=True)
        im=np.array(bpy.data.images.load(fp).pixels[:]).reshape(480,360,4)[::-1,:,:3]
        bg=(im[...,1]>0.6)&(im[...,0]<0.4)&(im[...,2]<0.4); red=(im[...,0]>0.6)&(im[...,1]<0.3)&(im[...,2]<0.3); blue=(im[...,2]>0.6)&(im[...,0]<0.3)&(im[...,1]<0.3)
        fill=ndimage.binary_fill_holes(~bg); hole=fill&bg
        mask=np.zeros_like(bg); yy,xx=np.mgrid[0:480,0:360]
        for b in JB:
            if b not in ARM.pose.bones: continue
            h=ARM.matrix_world@ARM.pose.bones[b].head; c=world_to_camera_view(sc,cam,h)
            mask|=(xx-c.x*360)**2+(yy-(1-c.y)*480)**2<14**2
        mask&=~bg|hole
        jpx+=mask.sum(); gap+=int((hole&mask).sum()); back+=int((red&mask).sum()); under+=int((blue&~bg).sum())
        pass
        bpy.data.images.remove(bpy.data.images[os.path.basename(fp)])
    r.update(gap_px=gap,backface_px=back,joint_px=int(jpx),gap_pct=round(100*(gap+back)/max(jpx,1),3),under_vis_px=under)
    res[nm]=r; print(nm,r,flush=True)
json.dump(res,open(f'{OUT}/gapcheck_{STG}.json','w'),indent=1)
