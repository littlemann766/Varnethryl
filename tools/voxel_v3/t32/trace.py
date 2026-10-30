import bpy,sys,math
a=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.read_factory_settings(use_empty=True); sc=bpy.context.scene; sc.render.fps=30
bpy.ops.import_scene.gltf(filepath=a[0]); arm=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]
act=[x for x in bpy.data.actions if x.name.startswith(a[1])][0]; arm.animation_data.action=act
f0,f1=map(int,act.frame_range); pb=arm.pose.bones[a[2]]; prev=None; s=[]
for f in range(f0,f1+1):
    sc.frame_set(f); q=pb.matrix_basis.to_quaternion()
    s.append('%d:%.0f'%(f,math.degrees(q.angle)) + ('/%.0f'%math.degrees(2*math.acos(min(1,abs(prev.dot(q))))) if prev else '')); prev=q
print('TR',f0,f1,' '.join(s))
