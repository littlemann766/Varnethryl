import bpy,sys,json
import numpy as np, os
a=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.open_mainfile(filepath=a[0]); sc=bpy.context.scene
arm=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]
ob=[o for o in bpy.data.objects if o.type=='MESH' and o.parent==arm and len(o.data.vertices)>1000][0]
me=ob.data; n=len(me.vertices)
co=np.empty(n*3); me.vertices.foreach_get('co',co); co=co.reshape(-1,3)
co=np.c_[co,np.ones(n)]
mw=np.array(ob.matrix_world)
gi=np.array([v.groups[0].group if v.groups else -1 for v in me.vertices])
gname={g.index:g.name for g in ob.vertex_groups}
def cls(nm):
    l=nm.lower().replace('mixamorig:','')
    if l.startswith('cape'): return 'cape'
    if any(t in l for t in ('upperarm','forearm','leftarm','rightarm','hand','fingers','index','middle','ring','pinky','thumb','weapon')): return 'arm'
    if any(t in l for t in ('thigh','shin','foot','toe','upleg','leftleg','rightleg')): return 'leg'
    if l.startswith(('hair','coat','hood','tail')): return 'other'
    return 'body'
C=np.array([cls(gname.get(g,'')) for g in gi])
W=(mw@co.T).T
S=float(os.environ.get('S','0.018'))
res={}
for an in ['__rest__']+a[1].split(','):
    if an=='__rest__':
        arm.animation_data.action=None
        from mathutils import Matrix
        for pb in arm.pose.bones: pb.matrix_basis=Matrix()
        f1=0
    else:
        act=bpy.data.actions[an]; arm.animation_data.action=act; f1=int(act.frame_range[1])
    al=[];cb=[]
    for f in range(0,f1+1,1):
        if an!='__rest__': sc.frame_set(f)
        else: bpy.context.view_layer.update()
        P=np.zeros((n,3))
        for g,nm in gname.items():
            if nm not in arm.pose.bones: continue
            M=np.array(arm.matrix_world@arm.pose.bones[nm].matrix@arm.data.bones[nm].matrix_local.inverted()@arm.matrix_world.inverted())
            idx=gi==g
            P[idx]=(M@W[idx].T).T[:,:3]
        def occ(mask): return set(map(tuple,np.floor(P[mask]/S).astype(int)))
        legs=occ(C=='leg'); body=occ(C=='body')
        am=np.where(C=='arm')[0]; hits=[i for i,t in zip(am,map(tuple,np.floor(P[am]/S).astype(int))) if t in legs]
        al.append(len(hits))
        if os.environ.get('DIAG') and hits:
            import collections; print('DIAG',an,f,collections.Counter(gname[gi[i]] for i in hits).most_common(4))
        cm=np.where(C=='cape')[0]
        hitc=[i for i,t in zip(cm,map(tuple,np.floor(P[cm]/S).astype(int))) if t in body or t in legs]
        cb.append(len(hitc))
        if os.environ.get('CDIAG') and an!='__rest__':
            import collections
            bset=collections.Counter()
            for i in hitc[::5]:
                t=tuple(np.floor(P[i]/S).astype(int)); bset[gname[gi[i]]]+=1
            print('CDIAG',an,f,len(hitc),bset.most_common(5))
    hc=(C=='cape').any()
    if an=='__rest__': base=(al[0],cb[0]); res['rest_baseline']={'arm_in_leg':al[0],'cape_in_body':cb[0]}; continue
    al=[max(0,x-base[0]) for x in al]; cb=[max(0,x-base[1]) for x in cb]
    res[an]={'arm_in_leg_verts_max':int(max(al)),'arm_leg_frames_over24':int(sum(x>24 for x in al)),'cape_in_body_verts_max':int(max(cb)) if hc else None,'cape_frames_over24':int(sum(x>24 for x in cb)) if hc else None,'frames_sampled':len(al)}
print('CHECK',json.dumps(res))
json.dump(res,open(a[2],'w'),indent=1)
