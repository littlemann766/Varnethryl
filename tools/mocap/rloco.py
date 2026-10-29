import bpy,sys,math,os,json
import numpy as np
a=sys.argv[sys.argv.index('--')+1:]; name,view,outd=a[0],a[1],a[2]; os.makedirs(outd,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=f'/workspace/mocap/out/{name}.blend'); sc=bpy.context.scene; sc.render.fps=30
sp=json.load(open(f'/workspace/mocap/out/{name}.speeds.json'))
arm=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]
for o in list(bpy.data.objects):
    if o.name.startswith('Icosphere'): o.hide_render=True
# grid floor
N=512; img=np.full((N,N,4),[0.30,0.31,0.34,1.0],dtype=np.float32)
for k in range(0,N,64): img[k:k+3,:,:3]=0.75; img[:,k:k+3,:3]=0.75
img[0:5,:,:3]=[0.9,0.6,0.2]; img[:,0:5,:3]=[0.9,0.6,0.2]
im=bpy.data.images.new('grid',N,N); im.pixels[:]=img.ravel()
bpy.ops.mesh.primitive_plane_add(size=400,location=(0,-150,0)); fl=bpy.context.object
for l in fl.data.uv_layers.active.data: l.uv=l.uv*200
mt=bpy.data.materials.new('g'); mt.use_nodes=True; tx=mt.node_tree.nodes.new('ShaderNodeTexImage'); tx.image=im; tx.interpolation='Closest'
mt.node_tree.links.new(tx.outputs[0],mt.node_tree.nodes['Principled BSDF'].inputs['Base Color']); fl.data.materials.append(mt)
cam=bpy.data.objects.new('c',bpy.data.cameras.new('c')); sc.collection.objects.link(cam); sc.camera=cam
cam.data.type='ORTHO'; cam.data.ortho_scale=2.9
sc.render.engine='BLENDER_WORKBENCH'; sh=sc.display.shading; sh.color_type='TEXTURE'; sh.light='STUDIO'
sc.render.resolution_x=384; sc.render.resolution_y=432
segs=[('walk',120),('run',84),('idle',75)]
y=0.0; g=0
for clip,nf in segs:
    act=bpy.data.actions[clip]; arm.animation_data.action=act; L=int(act.frame_range[1])
    v=sp[clip]['speed_mps']
    for k in range(nf):
        fp=f'{outd}/f{g:05d}.png'
        if not os.path.exists(fp):
            sc.frame_set(k%L); arm.location.y=y
            if view=='side': cam.location=(5,y,1.9); cam.rotation_euler=(math.radians(80),0,math.pi/2)
            else: cam.location=(3.6,y-3.6,1.6); cam.rotation_euler=(math.radians(78),0,math.radians(45))
            sc.render.filepath=fp; bpy.ops.render.render(write_still=True)
        y-=v/30.0; g+=1
print('DONE',g)
