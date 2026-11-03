import bpy,sys,json,numpy as np
G=sys.argv[-1]; OUT=f'/tmp/kr/{G}'
bpy.ops.wm.open_mainfile(filepath=f'{OUT}/stage4.blend')
exec(open('/tmp/kr/limits.py').read())
def bags(a):
    for l in a.layers:
        for s in l.strips:
            for sl in a.slots:
                cb=s.channelbag(sl)
                if cb: yield cb
n=0
def fq(cb,b):
    dp=f'pose.bones["{b}"].rotation_quaternion'; return [cb.fcurves.find(dp,index=i) for i in range(4)]
def rewrite(fcs,frames,vals):
    for f in fcs:
        while len(f.keyframe_points): f.keyframe_points.remove(f.keyframe_points[0])
    for x in frames:
        for i,f in enumerate(fcs): f.keyframe_points.insert(x,vals[x][i],options={'FAST'}).interpolation='LINEAR'
    for f in fcs: f.update()
for a in bpy.data.actions:
    for cb in bags(a):
        # rigid cuirass: fold spine2/upperChest rotation into chest (torso plates then never part)
        T=[fq(cb,b) for b in ('spine2','chest','upperChest')]
        if all(all(f is not None for f in t) for t in T):
            frames=sorted(set(k.co[0] for t in T for f in t for k in f.keyframe_points))
            ev={x:[Quaternion([f.evaluate(x) for f in t]) for t in T] for x in frames}
            rewrite(T[1],frames,{x:soft(ev[x][0]@ev[x][1]@ev[x][2],'torso') for x in frames})
            for t in (T[0],T[2]): rewrite(t,frames,{x:Quaternion() for x in frames})
for a in bpy.data.actions:
    for cb in bags(a):
        bones=set(f.data_path.split('"')[1] for f in cb.fcurves if f.data_path.endswith('rotation_quaternion'))
        for b in bones:
            if lim_for(b) is None or b in ('hips','spine2','chest','upperChest'): continue
            dp=f'pose.bones["{b}"].rotation_quaternion'; fcs=[cb.fcurves.find(dp,index=i) for i in range(4)]
            if any(f is None for f in fcs): continue
            frames=sorted(set(k.co[0] for f in fcs for k in f.keyframe_points))
            vals={x:soft([f.evaluate(x) for f in fcs],b) for x in frames}
            for f in fcs:
                while len(f.keyframe_points): f.keyframe_points.remove(f.keyframe_points[0])
            for x in frames:
                for i,f in enumerate(fcs): f.keyframe_points.insert(x,vals[x][i],options={'FAST'}).interpolation='LINEAR'
            for f in fcs: f.update()
            n+=1
print('LIMITED',n)
bpy.ops.wm.save_as_mainfile(filepath=f'{OUT}/stage'+__import__('os').environ.get('LIMSET','6')+'.blend')
