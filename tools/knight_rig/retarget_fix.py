# v3: rest-direction-corrected retarget + strip non-root loc/scale (Blender 5 channelbags)
from mathutils import Quaternion,Vector
SRC=json.load(open('/tmp/kr/src_rest.json'))['darius' if G=='male' else 'talia']
BHc={b.name:np.array(b.head_local) for b in ARM.data.bones}
CH_={}
for X in ('_L','_R'):
    for b,c in (('upperArm'+X,'foreArm'+X),('foreArm'+X,'hand'+X),('thigh'+X,'shin'+X),('shin'+X,'foot'+X)):
        do=Vector(BHc[c]-BHc[b]).normalized(); dd=Vector(np.array(SRC[c])-np.array(SRC[b])).normalized()
        CH_[b]=do.rotation_difference(dd)
CORR={}
for b in CH_: CORR[b]=(CH_.get(PARENT[b],Quaternion()),CH_[b])
for X in ('_L','_R'):
    for b in ('hand'+X,'foot'+X): CORR[b]=(CH_[PARENT[b]],Quaternion())
report['retarget_corr_deg']={b:round(math.degrees(q.angle),1) for b,q in CH_.items()}
def bags(a):
    for l in a.layers:
        for s in l.strips:
            for sl in a.slots:
                cb=s.channelbag(sl)
                if cb: yield cb
for a in bpy.data.actions:
    for cb in bags(a):
        for fc in list(cb.fcurves):
            bn=fc.data_path.split('"')[1] if '"' in fc.data_path else ''
            if (fc.data_path.endswith('location') and bn not in ('hips','root')) or fc.data_path.endswith('scale'): cb.fcurves.remove(fc)
        for b,(Cp,Cb) in CORR.items():
            dp=f'pose.bones["{b}"].rotation_quaternion'
            fcs=[cb.fcurves.find(dp,index=i) for i in range(4)]
            if fcs[0] is None:   # unkeyed child: key it at the parent's frames with identity
                pf=cb.fcurves.find(f'pose.bones["{PARENT[b]}"].rotation_quaternion',index=0)
                if pf is None: continue
                fr=[k.co[0] for k in pf.keyframe_points]
                fcs=[cb.fcurves.new(dp,index=i) for i in range(4)]
                for i,f in enumerate(fcs):
                    f.keyframe_points.add(len(fr))
                    for k,x in zip(f.keyframe_points,fr): k.co=(x,1.0 if i==0 else 0.0); k.interpolation='LINEAR'
            frames=sorted(set(k.co[0] for f in fcs for k in f.keyframe_points))
            vals={x:Quaternion([f.evaluate(x) for f in fcs]) for x in frames}
            for f in fcs:
                while len(f.keyframe_points): f.keyframe_points.remove(f.keyframe_points[0])
            for x in frames:
                qn=Cp.inverted()@vals[x]@Cb
                for i,f in enumerate(fcs): f.keyframe_points.insert(x,qn[i],options={'FAST'}).interpolation='LINEAR'
            for f in fcs: f.update()
print('RETARGET',report['retarget_corr_deg'])
