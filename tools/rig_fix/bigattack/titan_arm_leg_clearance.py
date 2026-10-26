import os
import bpy,sys,json,math,numpy as np
from mathutils import Vector,Quaternion
from mathutils.bvhtree import BVHTree
src,dst,mode=sys.argv[-3:]   # mode fix|check
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.scene.render.fps=30;bpy.context.scene.render.fps_base=1;bpy.ops.import_scene.gltf(filepath=src)
arm=[o for o in bpy.data.objects if o.type=='ARMATURE'][0];sc=bpy.context.scene;P=arm.pose.bones
bodies=[o for o in bpy.data.objects if o.type=='MESH' and o.find_armature()==arm]
body=max(bodies,key=lambda o:len(o.data.vertices))
GN={g.index:g.name for g in body.vertex_groups}
def dom(v): return GN[max(v.groups,key=lambda g:g.weight).group] if v.groups else ''
ARMS={s:[] for s in 'LR'};LEG=set()
for v in body.data.vertices:
    n=dom(v)
    if n.startswith(('thigh_','shin_','foot_')): LEG.add(v.index)
    elif n[-2:] in ('_L','_R') and n.split('_')[0].rstrip('0123456789') in ('upperArm','foreArm','hand','fingers','thumb','index','middle','ring','pinky'): ARMS[n[-1]].append(v.index)
LP=[p.index for p in body.data.polygons if all(i in LEG for i in p.vertices)]
H=max(o.dimensions.z for o in bodies)*1.0
MARG=0.004*H
DIR=Vector((0.0123,0.0071,0.99991)).normalized()
for s in 'LR': P['upperArm_'+s].rotation_mode='QUATERNION'
def mesh():
    dg=bpy.context.evaluated_depsgraph_get();e=body.evaluated_get(dg);m=e.to_mesh();M=body.matrix_world
    co=[M@v.co for v in m.vertices];tris=[[m.polygons[i].vertices[k] for k in range(len(m.polygons[i].vertices))] for i in LP]
    e.to_mesh_clear();return co,tris
def pen(co,tris):
    bvh=BVHTree.FromPolygons(co,tris,all_triangles=False);out={}
    for s in 'LR':
        c=0;d=9
        for i in ARMS[s][::2]:
            r=bvh.find_nearest(co[i],H*0.2)
            if r[0] is None: continue
            dist=(co[i]-r[0]).length
            if dist>0.06*H: continue
            hits=0;o=co[i].copy()
            for _ in range(20):
                h=bvh.ray_cast(o,DIR)
                if h[0] is None: break
                hits+=1;o=h[0]+DIR*1e-5*H
            ins=hits%2==1;sd=-dist if ins else dist;d=min(d,sd)
            if sd<MARG: c+=1
        out[s]=(c,d)
    return out
# abduction axis per side: maximize hand lateral distance at rest
arm.animation_data_create();acts=list(bpy.data.actions);arm.animation_data.action=None
for pb in P: pb.matrix_basis.identity()
bpy.context.view_layer.update()
lat=(P['hand_R'].head-P['hand_L'].head).normalized()
AX={'X':Vector((1,0,0)),'-X':Vector((-1,0,0)),'Z':Vector((0,0,1)),'-Z':Vector((0,0,-1))}
up=Vector((0,0,1));fw=lat.cross(up).normalized()
toe=[b for b in P if b.name.startswith('toe_')]
if toe and (toe[0].head-P['foot_'+toe[0].name[-1]].head).dot(fw)<0: fw=-fw
FLEX={}
ABD={}
for s,sg in (('L',-1),('R',1)):
    best=None
    for k,a in AX.items():
        P['upperArm_'+s].rotation_quaternion=Quaternion(a,math.radians(10));bpy.context.view_layer.update()
        v=P['hand_'+s].head.dot(lat)*sg
        if best is None or v>best[0]: best=(v,k)
        P['upperArm_'+s].rotation_quaternion=Quaternion()
    ABD[s]=AX[best[1]]
    perp=[k for k in AX if k.strip('-')!=best[1].strip('-')];bf=None
    for k in perp:
        P['upperArm_'+s].rotation_quaternion=Quaternion(AX[k],math.radians(10));bpy.context.view_layer.update()
        v=P['hand_'+s].head.dot(fw)
        if bf is None or v>bf[0]: bf=(v,k)
        P['upperArm_'+s].rotation_quaternion=Quaternion()
    FLEX[s]=AX[bf[1]]*float(os.environ.get("FSIGN","1"))
bpy.context.view_layer.update()
def fcq(act,s):
    return sorted([f for f in act.fcurves if f.data_path=='pose.bones["upperArm_%s"].rotation_quaternion'%s],key=lambda f:f.array_index)
rep={}
import os
ONLY=os.environ.get('ONLY','').split(',')
for act in acts:
    if ONLY!=[''] and act.name.split('_Darius')[0] not in ONLY: continue
    arm.animation_data.action=act;f0,f1=map(int,act.frame_range);fr=list(range(f0,f1+1))
    ang={s:np.zeros(len(fr)) for s in 'LR'};fl={s:np.zeros(len(fr)) for s in 'LR'};bad0=0;worst=9
    fcs={s:fcq(act,s) for s in 'LR'}
    if mode=='fix':
      for t,f in enumerate(fr):
        sc.frame_set(f);base={s:P['upperArm_'+s].rotation_quaternion.copy() for s in 'LR'}
        r=pen(*mesh());
        if r['L'][0] or r['R'][0]: bad0+=1
        n=0
        while (r['L'][0] or r['R'][0]) and n<int(os.environ.get("NIT","26")):
            for s in 'LR':
                if r[s][0]:
                    if n<12 or n>=26: ang[s][t]+=3
                    else: fl[s][t]+=3
                P['upperArm_'+s].rotation_quaternion=base[s]@Quaternion(ABD[s],math.radians(ang[s][t]))@Quaternion(FLEX[s],math.radians(fl[s][t]))
            bpy.context.view_layer.update();r=pen(*mesh());n+=1
      # smooth: max-filter +-4 then gaussian, add 1 deg margin where nonzero
      def sm(a,loop):
        m=np.array([a[max(0,i-4):i+5].max() for i in range(len(a))])
        k=np.exp(-np.linspace(-2,2,9)**2);k/=k.sum();p=np.pad(m,4,mode='wrap' if loop else 'edge')
        g=np.maximum(np.convolve(p,k,'valid'),m);return g+(g>0)*1.5
      LOOP='loop' in act.name or act.name.split('_Darius')[0] in('walk','run','idle','wb_walk','wb_run','wb_idle','wb_stagger_hold','wb_down_loop')
      for s in 'LR':
        a=ang[s]
        if not (a.any() or fl[s].any()) or not fcs[s]: continue
        a[:]=sm(a,LOOP);fl[s][:]=sm(fl[s],LOOP)
        fc=fcs[s]
        for kp in range(len(fc[0].keyframe_points)):
            fi=int(round(fc[0].keyframe_points[kp].co[0]))-f0
            if fi<0 or fi>=len(a) or (a[fi]==0 and fl[s][fi]==0): continue
            q=Quaternion([fc[j].keyframe_points[kp].co[1] for j in range(4)])@Quaternion(ABD[s],math.radians(a[fi]))@Quaternion(FLEX[s],math.radians(fl[s][fi]))
            for j in range(4):
                K=fc[j].keyframe_points[kp];K.co[1]=q[j];K.handle_left[1]=q[j];K.handle_right[1]=q[j]
        for f_ in fc: f_.update()
    # verify every frame
    bad=0;inter=0
    for f in fr:
        sc.frame_set(f);r=pen(*mesh())
        if r['L'][0] or r['R'][0]: bad+=1
        if min(r['L'][1],r['R'][1])<0: inter+=1
        worst=min(worst,r['L'][1],r['R'][1])
    rep[act.name]={'intersect_frames':inter,'bad_before':bad0,'bad_after':bad,'maxdeg':[round(float(ang[s].max()),1) for s in 'LR'],'flexdeg':[round(float(fl[s].max()),1) for s in 'LR'],'min_clear_pct':round(100*worst/H,2)}
    print('CLR',act.name,rep[act.name],flush=True)
print('CLRJSON',json.dumps({'axis':{s:tuple(ABD[s]) for s in 'LR'},'flex':{s:tuple(FLEX[s]) for s in 'LR'},'H':H,'clips':rep}))
if mode=='fix': bpy.ops.export_scene.gltf(filepath=dst,export_format='GLB',export_animation_mode='ACTIONS',export_force_sampling=True,export_skins=True,export_def_bones=False,export_optimize_animation_size=False)
