import bpy,sys,math,os,json
a=sys.argv[sys.argv.index('--')+1:]; blend,outd,dist,cz=a[0],a[1],float(a[2]),float(a[3]); clips=a[4].split(',') ; os.makedirs(outd,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=blend); sc=bpy.context.scene; sc.render.fps=30
arm=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]
for o in bpy.data.objects:
    if o.type=='MESH' and 'lod1' in o.name: o.hide_render=True
sp=json.load(open(blend.replace('.blend','.speeds.json'))) if os.path.exists(blend.replace('.blend','.speeds.json')) else {}
bpy.ops.mesh.primitive_plane_add(size=60,location=(0,0,0)); fl=bpy.context.object
sc.render.engine='BLENDER_WORKBENCH'; sh=sc.display.shading; sh.color_type=os.environ.get('CT','SINGLE'); sh.single_color=(0.32,0.16,0.1); sh.show_cavity=True; sh.light='STUDIO'; sh.show_shadows=True

cam=bpy.data.objects.new('c',bpy.data.cameras.new('c')); sc.collection.objects.link(cam); sc.camera=cam
cam.data.lens=35
sc.render.resolution_x=480; sc.render.resolution_y=360
from mathutils import Vector
g=0; meta=[]
txt=bpy.data.curves.new('t','FONT'); to=bpy.data.objects.new('t',txt); sc.collection.objects.link(to)
for clip in clips:
    act=bpy.data.actions[clip]; arm.animation_data.action=act; L=int(act.frame_range[1])
    reps=2 if L<45 else 1
    v=sp.get(clip,{}).get('speed_mps',0.0); y=0.0
    for k in range(L*reps+1):
        sc.frame_set(k%(L+1) if reps==1 else k%L); arm.location.y=y; arm.location.z=float(os.environ.get('ZOFF','0'))
        tgt=Vector((0,y,cz)); cam.location=tgt+Vector((dist*0.75,-dist*0.75,dist*0.25)); cam.rotation_euler=(tgt-cam.location).to_track_quat('-Z','Y').to_euler()
        txt.body=clip; to.location=tgt+Vector((-1.2,0.5,cz*1.1)); to.rotation_euler=cam.rotation_euler; to.scale=(0.25,0.25,0.25)
        sc.render.filepath=f'{outd}/f{g:05d}.png'; bpy.ops.render.render(write_still=True); g+=1
        y-=v/30.0
print('DONE',g)
