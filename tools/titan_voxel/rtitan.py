import bpy,sys,os,math,numpy as np
from mathutils import Vector
a=sys.argv[sys.argv.index('--')+1:]
blend,clips,outdir,N=a[0],a[1].split(','),a[2],int(a[3])
bpy.ops.wm.open_mainfile(filepath=blend)
sc=bpy.context.scene; sc.render.fps=30
arm=[o for o in sc.objects if o.type=='ARMATURE'][0]
ob=[o for o in sc.objects if o.type=='MESH' and o.parent==arm][0]
H=ob.dimensions.z if False else 21.14
k=114.0/H; arm.scale=arm.scale*k
# render palette = base + emission (workbench shows base texture only)
mat=ob.data.materials[0]; nt=mat.node_tree
texs=[n for n in nt.nodes if n.type=='TEX_IMAGE']
base=[n for n in texs if n.image.name.endswith('_pal')][0]; em=[n for n in texs if n.image.name.endswith('_emis')][0]
A=base.image.size[0]
bp=np.array(base.image.pixels[:]).reshape(-1,4); ep=np.array(em.image.pixels[:]).reshape(-1,4)
cp=bp.copy(); cp[:,:3]=np.clip(bp[:,:3]*0.85+ep[:,:3]*1.6,0,1)
im=bpy.data.images.new('rpal',A,A); im.pixels[:]=cp.ravel()
nn=nt.nodes.new('ShaderNodeTexImage'); nn.image=im; nn.interpolation='Closest'; nt.nodes.active=nn
sc.render.engine='BLENDER_WORKBENCH'; sc.display.shading.light='STUDIO'; sc.display.shading.color_type='TEXTURE'
sc.display.shading.show_shadows=False; sc.display.shading.show_cavity=False
sc.render.resolution_x=1280; sc.render.resolution_y=720
if sc.world is None: sc.world=bpy.data.worlds.new('W')
sc.world.color=(0.18,0.13,0.12)
def matc(n,c):
    m=bpy.data.materials.new(n); m.diffuse_color=c+(1,); return m
bpy.ops.mesh.primitive_plane_add(size=900); fl=bpy.context.object; fl.data.materials.append(matc('fl',(0.16,0.15,0.15)))
# scale posts
marks=[(2,'2m'),(10,'10m'),(30,'30m'),(60,'60m'),(114,'114m')]
cols=[(0.9,0.9,0.9),(0.2,0.8,0.3),(0.2,0.5,0.95),(0.95,0.8,0.2),(0.95,0.25,0.25)]
for i,((h,_),c) in enumerate(zip(marks,cols)):
    x=-45-i*9; y=10
    bpy.ops.mesh.primitive_cube_add(size=1,location=(x,y,h/2)); p=bpy.context.object; p.scale=(1.2,1.2,h); p.data.materials.append(matc(f'p{i}',c))
    # 10 m bands
    for z in range(10,int(h),10):
        bpy.ops.mesh.primitive_cube_add(size=1,location=(x,y,z)); b=bpy.context.object; b.scale=(1.6,1.6,0.6); b.data.materials.append(matc(f'b{i}{z}',(0.05,0.05,0.05)))
cam=bpy.data.objects.new('C',bpy.data.cameras.new('C')); sc.collection.objects.link(cam); sc.camera=cam; cam.data.lens=28; cam.data.clip_end=3000
CAM=Vector(tuple(float(x) for x in os.environ.get('CAM','95,-230,45').split(',')))
TGT=Vector(tuple(float(x) for x in os.environ.get('TGT','-15,0,52').split(',')))
cam.location=CAM; cam.rotation_euler=(TGT-CAM).to_track_quat('-Z','Y').to_euler()
for an in clips:
    act=bpy.data.actions[an]; arm.animation_data.action=act; f0,f1=[int(x) for x in act.frame_range]
    L=f1-f0+1; n=N if N>0 else L
    os.makedirs(f'{outdir}/{an}',exist_ok=True)
    for i in range(n):
        sc.frame_set(f0+(i%L))
        sc.render.filepath=f'{outdir}/{an}/{i:04d}.png'; bpy.ops.render.render(write_still=True)
