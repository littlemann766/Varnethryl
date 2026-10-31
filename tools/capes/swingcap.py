# Cap upper-arm abduction (frontal plane) to MAX deg in chosen clips; clip-only, re-runnable. usage: blender -b -P swingcap.py -- in.glb out.glb '<clip regex>' [MAX=30]
import bpy,sys,math,re,json
from mathutils import Matrix
a=sys.argv[sys.argv.index('--')+1:]; MAX=float(a[3]) if len(a)>3 else 30
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.context.scene.render.fps=30; bpy.ops.import_scene.gltf(filepath=a[0]); sc=bpy.context.scene
arm=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]; arm.animation_data_create(); mw=arm.matrix_world
ua=[b.name for b in arm.pose.bones if 'upperarm' in b.name.lower()]
def ab(pb):
    c=[x for x in pb.children if 'arm' in x.name.lower()][0]; d=(mw@c.head)-(mw@pb.head); return math.degrees(math.asin(min(1,abs(d.x)/d.length))),d
res={}
for act in bpy.data.actions:
    cl=act.name.rsplit('_',2)[0]
    if not re.search(a[2],cl): continue
    arm.animation_data.action=act; b0=a0=0
    for fr in range(int(act.frame_range[0]),int(act.frame_range[1])+1):
        sc.frame_set(fr)
        for u in ua:
            pb=arm.pose.bones[u]; g,d=ab(pb); b0=max(b0,g)
            if g>MAX:
                # rotate about the body front axis (Y) at the shoulder so |x| shrinks to sin(MAX)*len
                for _ in range(4):
                    g,d=ab(pb)
                    if g<=MAX+0.5: break
                    t=math.radians(g-MAX); s=1 if d.x>0 else -1
                    pw=mw@pb.head; R=Matrix.Translation(pw)@Matrix.Rotation(s*t,4,'Y')@Matrix.Translation(-pw)
                    pb.matrix=mw.inverted()@R@mw@pb.matrix; bpy.context.view_layer.update()
                    if ab(pb)[0]>g: pb.matrix=mw.inverted()@Matrix.Translation(pw)@Matrix.Rotation(-2*s*t,4,'Y')@Matrix.Translation(-pw)@mw@pb.matrix; bpy.context.view_layer.update()
                pb.rotation_mode='QUATERNION'; pb.keyframe_insert('rotation_quaternion',frame=fr)
    for fr in range(int(act.frame_range[0]),int(act.frame_range[1])+1):
        sc.frame_set(fr); a0=max([a0]+[ab(arm.pose.bones[u])[0] for u in ua])
    res[cl]=[round(b0,1),round(a0,1)]; print('CAP',cl,res[cl],flush=True)
json.dump(res,open(a[1].replace('.glb','.swingcap.json'),'w'))
bpy.ops.export_scene.gltf(filepath=a[1],export_format='GLB',export_animation_mode='ACTIONS',export_force_sampling=True,export_yup=True,export_skins=True,export_apply=False)
