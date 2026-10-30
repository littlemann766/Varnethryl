# push cape columns that enter body/leg cells outward on failing frames (check1 logic, relative to rest)
import bpy,sys,math,json,re
import numpy as np
from mathutils import Matrix,Vector
a=sys.argv[sys.argv.index('--')+1:]; blend,acts,out=a[0],a[1].split(','),a[2]
bpy.ops.wm.open_mainfile(filepath=blend); sc=bpy.context.scene; sc.render.fps=30
arm=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]
ob=[o for o in bpy.data.objects if o.type=='MESH' and o.parent==arm and len(o.data.vertices)>1000][0]
me=ob.data; n=len(me.vertices); S=0.018
co=np.empty(n*3); me.vertices.foreach_get('co',co); co=np.c_[co.reshape(-1,3),np.ones(n)]
W=(np.array(ob.matrix_world)@co.T).T
gi=np.array([max(v.groups,key=lambda g:g.weight).group if v.groups else -1 for v in me.vertices])
gname={g.index:g.name for g in ob.vertex_groups}
def cls(nm):
    l=nm.lower().replace('mixamorig:','')
    if l.startswith('cape'): return 'cape'
    if any(t in l for t in ('upperarm','forearm','leftarm','rightarm','hand','fingers','index','middle','ring','pinky','thumb','weapon')): return 'arm'
    if any(t in l for t in ('thigh','shin','foot','toe','upleg','leftleg','rightleg')): return 'leg'
    if l.startswith(('hair','coat','hood','tail')): return 'other'
    return 'body'
C=np.array([cls(gname.get(g,'')) for g in gi])
groups=[(g,nm) for g,nm in gname.items() if nm in arm.pose.bones]
cm=np.where(C=='cape')[0]
def count():
    P=np.zeros((n,3))
    for g,nm in groups:
        M=np.array(arm.matrix_world@arm.pose.bones[nm].matrix@arm.data.bones[nm].matrix_local.inverted()@arm.matrix_world.inverted())
        idx=gi==g; P[idx]=(M@W[idx].T).T[:,:3]
    T=np.floor(P/S).astype(int)
    occ=set(map(tuple,T[(C=='body')|(C=='leg')]))
    h=[i for i in cm if tuple(T[i]) in occ]
    return h
arm.animation_data.action=None
for pb in arm.pose.bones: pb.matrix_basis=Matrix()
bpy.context.view_layer.update(); base=len(count())
TB=arm.pose.bones
H=[b.name for b in TB if b.name.lower().endswith('hips')][0]
pat=re.compile(r'(cape\w*?_c(\d+))_r(\d+)')
cols={}
for b in TB:
    m=pat.fullmatch(b.name)
    if m: cols.setdefault(m.group(1),{})[int(m.group(3))]=b.name
rep={}
for an in acts:
    A=bpy.data.actions[an]; arm.animation_data.action=A; f0,f1=[int(round(x)) for x in A.frame_range]
    ang={}
    orig={}
    for f in range(f0,f1+1):
        sc.frame_set(f); orig[f]={b.name:(arm.matrix_world@b.matrix).copy() for b in TB if b.name.startswith('cape')}
    for it in range(20):
        worst=0; need={}
        for f in range(f0,f1+1):
            sc.frame_set(f); h=count(); ex=len(h)-base; worst=max(worst,ex)
            if ex>0:
                for i in h:
                    m=pat.fullmatch(gname[gi[i]])
                    if m: need.setdefault((m.group(1),f),[]).append(int(m.group(3)))
        print('IT',an,it,'worst',worst,flush=True)
        if worst<=0: break
        for (col,f),rows in need.items():
            r=max(0,min(rows)-2)
            for df in range(-2,3):
                ang[(col,r,f+df)]=ang.get((col,r,f+df),0)+3
        # apply: rebuild each frame from orig, rotating chosen bone (children follow via parenting)
        for f in range(f0,f1+1):
            sc.frame_set(f)
            hp=arm.matrix_world@arm.pose.bones[H].head
            for col,rows in cols.items():
                for r in sorted(rows):
                    nm=rows[r]; pb=TB[nm]
                    pb.matrix=arm.matrix_world.inverted()@orig[f][nm]
                bpy.context.view_layer.update()
                for r in sorted(rows):
                    k=ang.get((col,r,f),0)
                    if k:
                        nm=rows[r]; pb=TB[nm]; M=arm.matrix_world@pb.matrix; hd=M.translation; tl=arm.matrix_world@pb.tail
                        d=(tl-hd).normalized(); out_=Vector((hd.x-hp.x,hd.y-hp.y,0)).normalized()
                        ax=d.cross(out_)
                        if ax.length<1e-4: continue
                        R=Matrix.Translation(hd)@Matrix.Rotation(math.radians(-k),4,ax.normalized())@Matrix.Translation(-hd)
                        pb.matrix=arm.matrix_world.inverted()@R@M; bpy.context.view_layer.update()
                for r in sorted(rows):
                    pb=TB[rows[r]]; pb.keyframe_insert('rotation_quaternion',frame=f); pb.keyframe_insert('location',frame=f)
    rep[an]={'iters':it,'worst':int(worst)}
print('CAPEFIX',json.dumps(rep))
bpy.ops.wm.save_as_mainfile(filepath=out)
