# usage: blender -b -P measure.py -- <glb|blend> <out.json> [clips,comma]
import bpy,sys,json,numpy as np
a=sys.argv[sys.argv.index('--')+1:]; src,outp=a[0],a[1]; only=a[2].split(',') if len(a)>2 else None
if src.endswith('.blend'): bpy.ops.wm.open_mainfile(filepath=src)
else:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.render.fps=30; bpy.context.scene.render.fps_base=1
    bpy.ops.import_scene.gltf(filepath=src)
sc=bpy.context.scene; sc.render.fps=30
for o in list(bpy.data.objects):
    if o.name.startswith('Icosphere'): bpy.data.objects.remove(o)
arm=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]
body=max([o for o in bpy.data.objects if o.type=='MESH' and o.find_armature()==arm],key=lambda o:len(o.data.vertices))
GN={g.index:g.name for g in body.vertex_groups}
def reg(n):
    s=n[-1]
    if n[-2:] not in('_L','_R'): return None
    b=n[:-2].rstrip('0123456789')
    if b in('hand','fingers','thumb','index','middle','ring','pinky'): return 'fist_'+s
    if b=='foreArm': return 'forearm_'+s
    if b in('foot','toe'): return 'foot_'+s
    if b=='shin': return 'shin_'+s
    return None
R={}
for v in body.data.vertices:
    if not v.groups: continue
    r=reg(GN[max(v.groups,key=lambda g:g.weight).group])
    if r: R.setdefault(r,[]).append(v.index)
R={k:np.array(v) for k,v in R.items()}
H=21.14; M2G=114.0/H
for act in bpy.data.actions: act.name=act.name.split('_'+arm.name)[0]
out={}
for act in bpy.data.actions:
    if only and act.name not in only: continue
    arm.animation_data_create(); arm.animation_data.action=act
    f0,f1=[int(round(x)) for x in act.frame_range]; rows=[]
    for f in range(f0,f1+1):
        sc.frame_set(f); dg=bpy.context.evaluated_depsgraph_get(); e=body.evaluated_get(dg); m=e.to_mesh()
        co=np.empty(len(m.vertices)*3); m.vertices.foreach_get('co',co); co=co.reshape(-1,3)
        Mw=np.array(body.matrix_world); co=co@Mw[:3,:3].T+Mw[:3,3]
        rows.append({k:round(float(co[i,2].min())*M2G,3) for k,i in R.items()}|{'_all':round(float(co[:,2].min())*M2G,3)})
        e.to_mesh_clear()
    out[act.name]=rows; print('M',act.name,len(rows),flush=True)
json.dump(out,open(outp,'w'))
