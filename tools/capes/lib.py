import bpy,bmesh,collections
import numpy as np
from mathutils import Vector,Matrix
def load(f):
    bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=f)
    me=max([o for o in bpy.data.objects if o.type=='MESH'],key=lambda o:len(o.data.vertices)); return me,me.parent
def cls(nm):
    l=nm.lower().replace('mixamorig:','').replace('mixamorig_','')
    if l.startswith('cape'): return 'cape'
    if any(t in l for t in ('upperarm','forearm','leftarm','rightarm','hand','fingers','index','middle','ring','pinky','thumb','weapon')): return 'arm'
    if any(t in l for t in ('thigh','shin','foot','toe','upleg','leftleg','rightleg')): return 'leg'
    if l.startswith(('hair','coat','hood','tail')): return 'other'
    return 'body'
def vinfo(me):
    m=me.data; n=len(m.vertices)
    co=np.empty(n*3); m.vertices.foreach_get('co',co); co=co.reshape(-1,3)
    gi={g.index:g.name for g in me.vertex_groups}
    dom=np.array([gi[max(v.groups,key=lambda g:g.weight).group] if v.groups else '' for v in m.vertices],dtype=object)
    return co,dom
def bonemats(arm,names):
    return {nm:np.array(arm.matrix_world@arm.pose.bones[nm].matrix@arm.data.bones[nm].matrix_local.inverted()@arm.matrix_world.inverted()) for nm in names if nm in arm.pose.bones}
def posed(co,dom,M,mask=None):
    P=co.copy() if mask is None else co[mask].copy(); d=dom if mask is None else dom[mask]
    for nm in set(d):
        if nm not in M: continue
        i=d==nm; X=np.c_[P[i],np.ones(i.sum())]; P[i]=(M[nm]@X.T).T[:,:3]
    return P
def find(arm,*keys):
    for b in arm.data.bones:
        l=b.name.lower()
        if all(k in l for k in keys): return b
def legbones(arm):
    th=[b for b in arm.data.bones if cls(b.name)=='leg' and ('thigh' in b.name.lower() or 'upleg' in b.name.lower())]
    sh=[b for b in arm.data.bones if cls(b.name)=='leg' and ('shin' in b.name.lower() or (b.name.lower().endswith('leg') and 'up' not in b.name.lower()))]
    return th,sh
