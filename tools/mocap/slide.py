import bpy,sys,json
a=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.open_mainfile(filepath=f'/workspace/mocap/out/{a[0]}.blend'); sc=bpy.context.scene
sp=json.load(open(f'/workspace/mocap/out/{a[0]}.speeds.json'))
arm=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]
feet=[b.name for b in arm.data.bones if b.name in ('toe_L','toe_R','mixamorig:LeftToeBase','mixamorig:RightToeBase')]
H=max((arm.matrix_world@b.head_local).z for b in arm.data.bones)
out={}
for clip in ('walk','run','idle'):
    act=bpy.data.actions[clip]; arm.animation_data.action=act; L=int(act.frame_range[1]); v=sp[clip]['speed_mps']
    P={f:[] for f in feet}
    for fr in range(L+1):
        sc.frame_set(fr)
        for f in feet: P[f].append((arm.matrix_world@arm.pose.bones[f].head).copy())
    worst=0; st=0
    for f in feet:
        zmin=min(p.z for p in P[f])
        for i in range(L):
            if P[f][i].z<zmin+0.015*H and P[f][i+1].z<zmin+0.015*H:
                d=(P[f][i+1]-P[f][i]); d.y-=v/30.0; d.z=0
                worst=max(worst,d.length); st+=1
    out[clip]={'stance_samples':st,'max_slide_mm_per_frame':round(worst*1000,1)}
print('SLIDE',a[0],json.dumps(out))
