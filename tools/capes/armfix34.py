import sys,bpy,json,numpy as np,math
import os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); from lib import *
from mathutils import Matrix,Quaternion,Vector
a=sys.argv[sys.argv.index('--')+1:]; src,OUT=a[0],a[1]; CAP=float(a[2]) if len(a)>2 else 40
me,arm=load(src); sc=bpy.context.scene; sc.render.fps=30
co,dom=vinfo(me); Cl=np.array([cls(d) for d in dom]); W=np.c_[co,np.ones(len(co))]; S=0.018
def K(P):
    k=np.floor(P/S).astype(np.int64); return (k[:,0]+4096)*67108864+(k[:,1]+4096)*8192+(k[:,2]+4096)
def side(n):
    l=n.lower(); return 'L' if (l.endswith(('_l','.l','left')) or 'left' in l) else ('R' if (l.endswith(('_r','.r')) or 'right' in l) else None)
ua={}
for b in arm.data.bones:
    l=b.name.lower()
    if cls(b.name)=='arm' and ('upperarm' in l or l.endswith('leftarm') or l.endswith('rightarm')) and side(b.name): ua[side(b.name)]=b.name
def desc(bn):
    s={bn}; [s.add(c.name) for c in arm.data.bones[bn].children_recursive]; return s
amask={s:np.isin(dom,list(desc(n))) for s,n in ua.items()}
names=sorted(set(dom))
def pose():
    P=np.zeros_like(co)
    for nm in names:
        if nm not in arm.pose.bones: continue
        Mx=np.array(arm.matrix_world@arm.pose.bones[nm].matrix@arm.data.bones[nm].matrix_local.inverted()@arm.matrix_world.inverted()); i=dom==nm; P[i]=(Mx@W[i].T).T[:,:3]
    return P
hips=[b.name for b in arm.data.bones if b.parent is None][0]
def rot(axis,ang):
    c,s=math.cos(ang),math.sin(ang); x,y,z=axis; C=1-c
    return np.array([[c+x*x*C,x*y*C-z*s,x*z*C+y*s],[y*x*C+z*s,c+y*y*C,y*z*C-x*s],[z*x*C-y*s,z*y*C+x*s,c+z*z*C]])
def frame_info():
    P=pose(); legs=np.unique(K(P[Cl=='leg'])); mw=np.array(arm.matrix_world)
    piv={s:(mw@np.r_[np.array(arm.pose.bones[n].head),1])[:3] for s,n in ua.items()}
    hp=(mw@np.r_[np.array(arm.pose.bones[hips].head),1])[:3]
    # forward axis in world = character facing; use armature -Y? use world Y (glTF imported Z-up, char faces -Y)
    return P,legs,piv,hp
def hits(P,legs,s,ang,piv,hp):
    Q=P[amask[s]]
    if ang:
        out=np.sign(piv[s][0]-hp[0]) or (1 if s=='L' else -1)
        R=rot((0,1,0),-out*ang)  # rotate about Y so arm swings outward in +out x
        Q=(Q-piv[s])@R.T+piv[s]
    return int(np.isin(K(Q),legs).sum())
def chk(act):
    arm.animation_data.action=act; f0,f1=map(int,act.frame_range); m=0
    for fr in range(f0,f1+1,2):
        sc.frame_set(fr); P,legs,piv,hp=frame_info(); m=max(m,sum(hits(P,legs,s,0,piv,hp) for s in ua))
    return m

import re
ONLY=a[3] if len(a)>3 else 'jump|swim|fly_bank'
ORIG=json.load(open(a[4])) if len(a)>4 else {}
fa={}
for s_,n in ua.items():
    ch=[c for c in arm.data.bones[n].children if cls(c.name)=='arm']
    if ch: fa[s_]=ch[0].name
fmask={s_:np.isin(dom,list(desc(n))) for s_,n in fa.items()}
def rotabout(Q,piv,ax,ang):
    if not ang: return Q
    return (Q-piv)@rot(ax,ang).T+piv
def hits2(P,legs,s_,ab,fl,el,piv,hp,ep,eax):
    out=np.sign(piv[s_][0]-hp[0]) or 1
    idx=np.where(amask[s_])[0]; Q=P[idx]
    if el:
        fm=fmask[s_][idx]; Q=Q.copy(); Q[fm]=rotabout(Q[fm],ep,eax,el)
    Q=rotabout(Q,piv[s_],(0,1,0),-out*ab); Q=rotabout(Q,piv[s_],(1,0,0),fl)
    return int(np.isin(K(Q),legs).sum())
D=math.radians
def mkgrid(abmax,flmax): return sorted([(ab,fl) for ab in range(-24,abmax+1,8) for fl in range(-40,flmax+1,10)],key=lambda t:abs(t[0])+abs(t[1]))
G0=mkgrid(60,60); GS=mkgrid(60,150); GB=mkgrid(88,60); GR=mkgrid(8,60)
arm.animation_data_create(); res={}
for act in sorted(bpy.data.actions,key=lambda x:x.name):
    cl=act.name.split('_'+arm.name)[0]
    if not re.search(ONLY,cl): continue
    arm.animation_data.action=act; f0,f1=map(int,act.frame_range); before=0; prm={s_:[] for s_ in ua}
    for fr in range(f0,f1+1):
        sc.frame_set(fr); P,legs,piv,hp=frame_info(); mw=np.array(arm.matrix_world)
        for s_ in ua:
            fb=arm.pose.bones[fa[s_]]; ep=(mw@np.r_[np.array(fb.head),1])[:3]
            eax=(mw[:3,:3]@np.array(fb.matrix.to_3x3().col[0])); eax/=np.linalg.norm(eax)
            h0=hits2(P,legs,s_,0,0,0,piv,hp,ep,eax); before=max(before,h0); best=(h0,0,0,0)
            if h0>0:
                for ab,fl in (GS if ('swim' in cl or (os.environ.get('WIDE') and 'jump' in cl)) else GB if 'bank' in cl else GR if cl in ('run','walk') else G0):
                    h=hits2(P,legs,s_,D(ab),D(fl),0,piv,hp,ep,eax)
                    if h<best[0]: best=(h,ab,fl,0)
                    if h==0: break
                if best[0]>0:
                    for el in (30,-30,60,-60,90,-90):
                        h=hits2(P,legs,s_,D(best[1]),D(best[2]),D(el),piv,hp,ep,eax)
                        if h<best[0]: best=(h,best[1],best[2],el)
                        if h==0: break
            prm[s_].append(best[1:])
    g=np.exp(-0.5*(np.arange(-4,5)/2.0)**2); g/=g.sum()
    for s_ in ua:
        A=np.array(prm[s_],float); prm[s_]=np.stack([np.convolve(np.pad(A[:,i],4,mode='edge'),g,'valid') for i in range(3)],1)
    for fr in range(f0,f1+1):
        sc.frame_set(fr); mw=arm.matrix_world; hpv=mw@arm.pose.bones[hips].head
        for s_,n in ua.items():
            ab,fl,el=[D(x) for x in prm[s_][fr-f0]]
            if abs(ab)+abs(fl)+abs(el)<1e-4: continue
            pb=arm.pose.bones[n]; pw=mw@pb.head; out=1 if pw.x>=hpv.x else -1
            fb=arm.pose.bones[fa[s_]]
            if el:
                ew=mw@fb.head; ax=(mw.to_3x3()@fb.matrix.to_3x3().col[0]).normalized()
                Re=Matrix.Translation(ew)@Matrix.Rotation(el,4,ax)@Matrix.Translation(-ew)
                fb.matrix=mw.inverted()@Re@mw@fb.matrix; fb.rotation_mode='QUATERNION'; fb.keyframe_insert('rotation_quaternion',frame=fr); bpy.context.view_layer.update()
            Rw=Matrix.Translation(pw)@Matrix.Rotation(fl,4,'X')@Matrix.Rotation(-out*ab,4,'Y')@Matrix.Translation(-pw)
            M=mw.inverted()@Rw@mw@pb.matrix; 
            if el: fb_m=fb.matrix.copy()
            pb.matrix=M; pb.rotation_mode='QUATERNION'; pb.keyframe_insert('rotation_quaternion',frame=fr); bpy.context.view_layer.update()
    # pass 2: fix leftover single frames directly (no smoothing)
    for fr in range(f0,f1+1):
        sc.frame_set(fr); P,legs,piv,hp=frame_info(); mw=np.array(arm.matrix_world)
        for s_,n in ua.items():
            fb=arm.pose.bones[fa[s_]]; ep=(mw@np.r_[np.array(fb.head),1])[:3]
            eax=(mw[:3,:3]@np.array(fb.matrix.to_3x3().col[0])); eax/=np.linalg.norm(eax)
            h0=hits2(P,legs,s_,0,0,0,piv,hp,ep,eax)
            if h0<=3: continue
            best=(h0,0,0,0)
            for ab,fl in (GS if ('swim' in cl or (os.environ.get('WIDE') and 'jump' in cl)) else GB if 'bank' in cl else GR if cl in ('run','walk') else G0):
                for el in (0,30,-30,60,-60):
                    h=hits2(P,legs,s_,D(ab),D(fl),D(el),piv,hp,ep,eax)
                    if h<best[0]: best=(h,ab,fl,el)
                if best[0]==0: break
            _,ab,fl,el=best
            if (ab,fl,el)==(0,0,0): continue
            ab,fl,el=D(ab),D(fl),D(el); mwm=arm.matrix_world; hpv=mwm@arm.pose.bones[hips].head
            pb=arm.pose.bones[n]; pw=mwm@pb.head; out=1 if pw.x>=hpv.x else -1
            if el:
                ew=mwm@fb.head; ax=(mwm.to_3x3()@fb.matrix.to_3x3().col[0]).normalized()
                fb.matrix=mwm.inverted()@Matrix.Translation(ew)@Matrix.Rotation(el,4,ax)@Matrix.Translation(-ew)@mwm@fb.matrix; fb.keyframe_insert('rotation_quaternion',frame=fr); bpy.context.view_layer.update()
            pb.matrix=mwm.inverted()@Matrix.Translation(pw)@Matrix.Rotation(fl,4,'X')@Matrix.Rotation(-out*ab,4,'Y')@Matrix.Translation(-pw)@mwm@pb.matrix
            pb.keyframe_insert('rotation_quaternion',frame=fr); bpy.context.view_layer.update()
            P,legs,piv,hp=frame_info()
    after=chk(act); ob=ORIG.get(cl,{}).get('before',before)
    res[cl]={'start':before,'orig_before':ob,'after':after}
    print('CLIP',cl,res[cl],flush=True)
json.dump(res,open(OUT.replace('.glb','.armfix34.json'),'w'),indent=1)
print('SUMMARY',json.dumps(res))
bpy.ops.export_scene.gltf(filepath=OUT,export_format='GLB',export_animation_mode='ACTIONS',export_force_sampling=True,export_yup=True,export_skins=True,export_apply=False)
