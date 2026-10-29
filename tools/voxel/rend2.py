import bpy,sys,math,os,re
a=sys.argv[sys.argv.index('--')+1:]; mode=a[0]; outd=a[1]; wi=int(a[2]) if len(a)>2 else 0; wn=int(a[3]) if len(a)>3 else 1; os.makedirs(outd,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc=bpy.context.scene; sc.render.fps=30; sc.render.fps_base=1
H=['owner','selene','darius']; arms={}; per={}
for n,h in enumerate(H):
    bo=set(bpy.data.objects); ba=set(bpy.data.actions)
    bpy.ops.import_scene.gltf(filepath=f'/workspace/voxel/v2_{h}_voxel.glb')
    for o in set(bpy.data.objects)-bo:
        if o.type=='ARMATURE': arms[h]=o; o.location.x=(n-1)*1.6
    for o in arms.values():
        if o.rotation_mode!='XYZ': e=o.matrix_world.to_euler('XYZ'); o.rotation_mode='XYZ'; o.rotation_euler=e
    per[h]={re.sub(r'_Darius_Rig.*','',x.name):x for x in set(bpy.data.actions)-ba}
for x in bpy.data.actions: x.use_fake_user=True
cam=bpy.data.objects.new('c',bpy.data.cameras.new('c')); sc.collection.objects.link(cam); sc.camera=cam
cam.data.lens=50; cam.location=(0,-8.6,1.2); cam.rotation_euler=(math.radians(88),0,0)
sc.render.engine='BLENDER_WORKBENCH'; sh=sc.display.shading
sh.color_type='TEXTURE'; sh.light='STUDIO'; sh.show_shadows=False; sh.shadow_intensity=0.4
sc.render.resolution_x=1280; sc.render.resolution_y=720
sc.world=bpy.data.worlds.new('w'); sh.background_type='VIEWPORT'; sh.background_color=(0.08,0.08,0.1)
# floor
bpy.ops.mesh.primitive_plane_add(size=20); fl=bpy.context.object
fm=bpy.data.materials.new('f'); fm.diffuse_color=(0.22,0.22,0.25,1); fl.data.materials.append(fm)
sh.color_type='TEXTURE'
def setpose(clip,t,yaw=0.0):
    for h,o in arms.items():
        act=per[h].get(clip) or per[h]['idle']
        o.animation_data.action=act
        f0,f1=act.frame_range; L=max(1,f1-f0)
        o.rotation_mode='XYZ'; o.rotation_euler=(math.radians(90),0,yaw) if o.rotation_mode=='XYZ' else None
        o.rotation_euler[2]=yaw
    # frame evaluated per armature: set scene frame then individually via action offset not possible; use common t mod length
    sc.frame_set(0)
    for h,o in arms.items():
        act=o.animation_data.action; f0,f1=act.frame_range; L=max(1,f1-f0)
        o.animation_data.action_extrapolation='HOLD'
    return
segs=[('turn','idle',120),('walk','walk',60),('run','run',42),('idle','idle',60),('attack','attack',45),('fly','fly_forward',48),('hover','fly_hover',60)]
if mode=='faces':
    for h,o in arms.items(): o.animation_data.action=per[h]['idle']
    sc.frame_set(10); sc.render.resolution_x=1800; sc.render.resolution_y=640
    sc.render.resolution_x=600; sc.render.resolution_y=640
    cam.data.type='ORTHO'; cam.data.ortho_scale=0.42; sh.light='FLAT'
    for h,o in arms.items():
        hp=o.matrix_world@o.pose.bones['head'].head
        cam.location=(hp.x,hp.y-3,hp.z+0.11); cam.rotation_euler=(math.radians(90),0,0)
        sc.render.filepath=outd+f'/face_{h}.png'; bpy.ops.render.render(write_still=True)
    sys.exit()
if mode=='still':
    for h,o in arms.items(): o.animation_data.action=per[h]['idle']
    sc.frame_set(10); sc.render.filepath=outd+'/still.png'; bpy.ops.render.render(write_still=True); sys.exit()
# use NLA-free approach: each armature uses action time scaled modulo own length
gi=0; log=[]
base={h:o.rotation_euler[2] for h,o in arms.items()}
for name,clip,n in segs:
    for k in range(n):
        fp=f'{outd}/f{gi:05d}.png'; gi+=1
        if os.path.exists(fp) or (gi-1)%wn!=wi: continue
        for h,o in arms.items():
            act=per[h].get(clip) or per[h]['idle']
            o.animation_data.action=act
            o.rotation_euler[2]= base[h]+(2*math.pi*k/n) if name=='turn' else (base[h]+math.radians(-35) if name in('walk','run','fly','hover') else base[h])
        # evaluate each armature at its own looped frame
        for h,o in arms.items():
            act=o.animation_data.action; f0,f1=act.frame_range; L=max(1.0,f1-f0)
            o.animation_data.action_blend_type='REPLACE'
        # Blender evaluates all at scene frame; emulate per-arm time with NLA strip offset trick: set strip-less, choose frame so modulo works
        fr=k if name=='turn' else k
        # build per-arm pose by evaluating the action fcurves directly
        for h,o in arms.items():
            act=o.animation_data.action; f0,f1=act.frame_range; L=max(1.0,f1-f0)
            t=f0+((fr % L) if name!='attack' else min(fr,L))
            o.animation_data.action=None
            for fc in act.fcurves:
                m=re.match(r'pose\.bones\["(.+)"\]\.(\w+)',fc.data_path)
                if not m or m.group(1) not in o.pose.bones: continue
                getattr(o.pose.bones[m.group(1)],m.group(2))[fc.array_index]=fc.evaluate(t)
        bpy.context.view_layer.update()
        sc.render.filepath=fp; bpy.ops.render.render(write_still=True)
        for h,o in arms.items():
            for pb in o.pose.bones: pb.location=(0,0,0); pb.rotation_quaternion=(1,0,0,0); pb.scale=(1,1,1)
print('DONE',gi)
