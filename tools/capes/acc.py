# usage: blender -b -P acc.py -- file.glb '<clip regex>' bone1,bone2 : max |accel| of bone head (H/frame^2) + loop seam gap (H)
import bpy,sys,re,numpy as np
a=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.context.scene.render.fps=30; bpy.ops.import_scene.gltf(filepath=a[0]); sc=bpy.context.scene; sc.render.fps=30
arm=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]
me=max([o for o in bpy.data.objects if o.type=='MESH'],key=lambda o:len(o.data.vertices)); H=me.dimensions.z or 1
arm.animation_data_create()
for act in bpy.data.actions:
    cl=act.name.split('_'+arm.name)[0]
    if not re.search(a[1],cl): continue
    arm.animation_data.action=act; f0,f1=map(int,act.frame_range)
    for bn in a[2].split(','):
        if bn not in arm.pose.bones: continue
        P=[]
        for fr in range(f0,f1+1): sc.frame_set(fr); P.append(np.array(arm.matrix_world@arm.pose.bones[bn].head))
        P=np.array(P)/H; A=np.linalg.norm(P[2:]-2*P[1:-1]+P[:-2],axis=1); 
        print('ACC',cl,bn,'max_acc',round(float(A.max()),3),'at',int(A.argmax())+f0+1,'seam',round(float(np.linalg.norm(P[-1]-P[0])),3))
