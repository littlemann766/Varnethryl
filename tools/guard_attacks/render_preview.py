# preview: each new clip twice, 3/4 front + side, LOD0, frames to dir (mp4 made with ffmpeg)
import bpy,sys,math,os,json
a=sys.argv[sys.argv.index('--')+1:]; blend,outd,evj=a[0],a[1],a[2]; os.makedirs(outd,exist_ok=True)
EV=json.load(open(evj))['clips']
bpy.ops.wm.open_mainfile(filepath=blend); sc=bpy.context.scene; sc.render.fps=30
for o in list(sc.objects):
    if o.name.startswith('Icosphere'): o.hide_render=True
arm=[o for o in sc.objects if o.type=='ARMATURE'][0]
sc.render.engine='BLENDER_WORKBENCH'; sh=sc.display.shading; sh.light='STUDIO'; sh.color_type='TEXTURE'; sh.show_shadows=True
sc.render.resolution_x=480; sc.render.resolution_y=540
if sc.world is None: sc.world=bpy.data.worlds.new('W')
sc.world.color=(0.62,0.66,0.72)
bpy.ops.mesh.primitive_plane_add(size=8,location=(0,0,-0.03)); fl=bpy.context.object
mt=bpy.data.materials.new('f'); mt.diffuse_color=(0.33,0.36,0.30,1); fl.data.materials.append(mt)
cams=[]
for nm,az in (('front34',-35),('side',-90)):
    c=bpy.data.objects.new(nm,bpy.data.cameras.new(nm)); sc.collection.objects.link(c); c.data.type='ORTHO'; c.data.ortho_scale=2.9
    r=math.radians(az); c.location=(6*math.sin(r),-6*math.cos(r),1.25); c.rotation_euler=(math.radians(86),0,r); cams.append(c)
g=0; manifest=[]
for an in EV:
    A=bpy.data.actions[an]; arm.animation_data.action=A; L=int(A.frame_range[1])
    for c in cams:
        sc.camera=c
        for rep in range(2 if L<40 else 1):
            for f in range(L+1):
                fp=f'{outd}/f{g:05d}.png'
                sc.frame_set(f); sc.render.filepath=fp; bpy.ops.render.render(write_still=True)
                manifest.append([g,an,c.name,f,f==EV[an].get('hit_frame')]); g+=1
json.dump(manifest,open(outd+'/manifest.json','w'))
print('FRAMES',g)
