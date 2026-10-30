import bpy,sys,json,math
a=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.read_factory_settings(use_empty=True); sc=bpy.context.scene; sc.render.fps=30
bpy.ops.import_scene.gltf(filepath=a[0])
arm=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]
out={}
for act in bpy.data.actions:
    if not any(k in act.name for k in a[1].split(',')): continue
    arm.animation_data.action=act; f0,f1=map(int,act.frame_range); prev=None; best=(0,'',0,0)
    for f in range(f0,f1+1):
        sc.frame_set(f); cur={pb.name:(pb.matrix_basis.to_quaternion(),(pb.matrix.to_3x3()@__import__('mathutils').Vector((0,1,0)))) for pb in arm.pose.bones}
        if prev:
            for n,(q,d) in cur.items():
                pq,pd=prev[n]; raw=math.degrees(2*math.acos(max(-1,min(1,abs(pq.dot(q))))));
                signed=math.degrees(2*math.acos(max(-1,min(1,pq.dot(q)))))
                vis=math.degrees(pd.angle(d,0))
                if signed>best[0]: best=(signed,n,f,raw,vis)
        prev=cur
    out[act.name]={'signed_naive':round(best[0],1),'bone':best[1],'frame':best[2],'true_rot':round(best[3],1),'visual_dir_change':round(best[4],1)} if len(best)>4 else {}
print('FLIP',json.dumps(out))
