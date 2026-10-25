import bpy,numpy as np
from mathutils import Vector
for tag,f in [('v2','/workspace/hero-motion/beth-reweight/v2/stonetroll_lod1.glb'),('v3','/workspace/hero-motion/beth-reweight/v3/stonetroll_lod1.glb')]:
    bpy.ops.wm.read_factory_settings(use_empty=True); sc=bpy.context.scene; bpy.ops.import_scene.gltf(filepath=f)
    arm=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]; me=max([o for o in bpy.data.objects if o.type=='MESH'],key=lambda o:len(o.data.vertices))
    rest=np.array([v.co[:] for v in me.data.vertices]); rx=np.abs(rest[:,0]); 
    # identify fist & leg verts by rest pose in blender local coords (y-up glTF -> z-up)
    print("BB",rest.min(0),rest.max(0)); up=int(np.argmax(rest.max(0)-rest.min(0)>1.7)) if False else (1 if rest[:,1].max()>1.7 else 2); fist=rx>1.1; leg=rest[:,up]<0.85
    res=[]
    for c in ['idle','walk','run','attack1','attack2','attack3']:
        a=bpy.data.actions[c]; arm.animation_data_create(); arm.animation_data.action=a
        if getattr(a,'slots',None): arm.animation_data.action_slot=a.slots[0]
        r=a.frame_range; worst=9
        for k in range(12):
            sc.frame_set(int(r[0]+(r[1]-r[0])*k/12)); dg=bpy.context.evaluated_depsgraph_get(); e=me.evaluated_get(dg); m=e.to_mesh()
            P=np.array([v.co[:] for v in m.vertices]); e.to_mesh_clear()
            F=P[fist][::3]; L=P[leg][::3]
            d=np.sqrt(((F[:,None,:]-L[None,:,:])**2).sum(-1)).min(1); worst=min(worst,9-(d<0.03).mean()*100) if False else max(worst if worst!=9 else 0,(d<0.03).mean()*100)
        res.append((c,round(float(worst),3)))
    print('CLIP',tag,res)
