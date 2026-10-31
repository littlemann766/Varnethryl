# Close thin horizontal see-through seams (two cube grids with a small z gap) in a band around the neck.
# usage: blender -b -P neckseam.py -- in.glb out.glb [band=1.0 world units around neck head]
import bpy,sys,numpy as np,json
a=sys.argv[sys.argv.index('--')+1:]; BAND=float(a[2]) if len(a)>2 else 1.0
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.context.scene.render.fps=30; bpy.ops.import_scene.gltf(filepath=a[0])
arm=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]; me=max([o for o in bpy.data.objects if o.type=='MESH'],key=lambda o:len(o.data.vertices))
nz=(arm.matrix_world@[b for b in arm.data.bones if b.name.lower()=='neck'][0].head_local).z
M=me.matrix_world; Mi=M.inverted(); vs=me.data.vertices
co=np.array([M@v.co for v in vs]); z=co[:,2]
lv=np.unique(np.round(z[np.abs(z-nz)<BAND],4)); d=np.diff(lv); step=np.median(d[d>0.01*BAND]) if len(d) else 0
fixes=[]
for i in range(len(lv)-1):
    g=lv[i+1]-lv[i]
    if 1e-4<g<0.35*step:
        lo,hi=lv[i],lv[i+1]
        # lower level = tops of the lower grid only if those verts are cube tops (their cube lies below)
        sel=np.where(np.abs(z-lo)<5e-5)[0]
        for j in sel:
            w=M@vs[j].co; w.z=hi; vs[j].co=Mi@w
        fixes.append({'from':float(lo),'to':float(hi),'gap':round(float(g),4),'verts':int(len(sel))})
print('SEAM',json.dumps({'neck_z':round(nz,3),'step':round(float(step),4),'fixes':fixes}))
json.dump(fixes,open(a[1].replace('.glb','.neckseam.json'),'w'))
bpy.ops.export_scene.gltf(filepath=a[1],export_format='GLB',export_animation_mode='ACTIONS',export_force_sampling=True,export_yup=True,export_skins=True,export_apply=False)
