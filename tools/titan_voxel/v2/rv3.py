import bpy,sys,os,math,numpy as np
from mathutils import Vector
a=sys.argv[sys.argv.index('--')+1:]; clip,outdir,view=a[0],a[1],a[2]
bpy.ops.wm.open_mainfile(filepath='/workspace/titan2/post/vx_m.blend'); sc=bpy.context.scene; sc.render.fps=30
arm=[o for o in sc.objects if o.type=='ARMATURE'][0]; ob=[o for o in sc.objects if o.type=='MESH' and o.parent==arm][0]
k=114.0/21.14; arm.scale=arm.scale*k
for o in list(sc.objects):
    if o.type=='MESH' and o!=ob: bpy.data.objects.remove(o)
mat=ob.data.materials[0]; nt=mat.node_tree; texs=[n for n in nt.nodes if n.type=='TEX_IMAGE']
base=[n for n in texs if n.image.name.endswith('_pal')][0]; em=[n for n in texs if n.image.name.endswith('_emis')][0]
A=base.image.size[0]; bp=np.array(base.image.pixels[:]).reshape(-1,4); ep=np.array(em.image.pixels[:]).reshape(-1,4)
cp=bp.copy(); cp[:,:3]=np.clip(bp[:,:3]*0.85+ep[:,:3]*1.6,0,1); im=bpy.data.images.new('rpal',A,A); im.pixels[:]=cp.ravel()
nn=nt.nodes.new('ShaderNodeTexImage'); nn.image=im; nn.interpolation='Closest'; nt.nodes.active=nn
sc.render.engine='BLENDER_WORKBENCH'; sh=sc.display.shading; sh.light='STUDIO'; sh.color_type='TEXTURE'
sc.render.resolution_x=1280; sc.render.resolution_y=720
if sc.world is None: sc.world=bpy.data.worlds.new('W')
sc.world.color=(0.18,0.13,0.12)
N=512; img=np.full((N,N,4),[0.22,0.21,0.21,1.0],dtype=np.float32)
for q in range(0,N,64): img[q:q+4,:,:3]=0.55; img[:,q:q+4,:3]=0.55
gi=bpy.data.images.new('grid',N,N); gi.pixels[:]=img.ravel()
bpy.ops.mesh.primitive_plane_add(size=2000); fl=bpy.context.object
for l in fl.data.uv_layers.active.data: l.uv=l.uv*200   # 10 m squares
gm=bpy.data.materials.new('g'); gm.use_nodes=True; tx=gm.node_tree.nodes.new('ShaderNodeTexImage'); tx.image=gi; tx.interpolation='Closest'
gm.node_tree.links.new(tx.outputs[0],gm.node_tree.nodes['Principled BSDF'].inputs['Base Color']); fl.data.materials.append(gm)
def mc(n,c): m=bpy.data.materials.new(n); m.diffuse_color=c+(1,); return m
posts=[(2,(0.9,0.9,0.9)),(10,(0.2,0.8,0.3)),(30,(0.2,0.5,0.95)),(60,(0.95,0.8,0.2)),(114,(0.95,0.25,0.25))]
def addposts(x0,y0,dx,dy):
    for i,(h,c) in enumerate(posts):
        bpy.ops.mesh.primitive_cube_add(size=1,location=(x0+i*dx,y0+i*dy,h/2)); p=bpy.context.object; p.scale=(1.5,1.5,h); p.data.materials.append(mc(f'p{i}',c))
act=bpy.data.actions[clip]; arm.animation_data.action=act; f0,f1=[int(x) for x in act.frame_range]
cam=bpy.data.objects.new('C',bpy.data.cameras.new('C')); sc.collection.objects.link(cam); sc.camera=cam; cam.data.lens=30; cam.data.clip_end=5000
os.makedirs(outdir,exist_ok=True)
if view=='walk':
    addposts(-40,-20,0,-25); frames=list(range(f0,f1))*2
    for i,f in enumerate(frames):
        sc.frame_set(f); off=-(f1-f0)*(i//(f1-f0)); arm.location.y=0
        hy=(arm.matrix_world@arm.pose.bones['hips'].head).y
        # second cycle: shift character by one cycle of root motion
        if i>=(f1-f0):
            d=(arm.matrix_world@arm.pose.bones['root'].head).y; 
        cam.location=(240,hy,60); cam.rotation_euler=(math.radians(89),0,math.radians(90))
        sc.render.filepath=f'{outdir}/{i:04d}.png'; bpy.ops.render.render(write_still=True)
else:
    addposts(-70,40,-12,0)
    CAM=Vector((170,-200,6)); TGT=Vector((0,-40,30))
    cam.location=CAM; cam.rotation_euler=(TGT-CAM).to_track_quat('-Z','Y').to_euler()
    for i,f in enumerate(range(f0,f1+1)):
        sc.frame_set(f); sc.render.filepath=f'{outdir}/{i:04d}.png'; bpy.ops.render.render(write_still=True)
