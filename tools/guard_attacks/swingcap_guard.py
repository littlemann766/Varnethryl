# cap upper-arm lateral-out angle (motion_checks.py definition, hip frame) to MAX deg in chosen clips. usage: blender -b -P swingcap_guard.py -- in.glb out.glb '<clip regex>' [MAX=30]
import bpy,sys,math,re,json
from mathutils import Matrix,Vector
a=sys.argv[sys.argv.index('--')+1:]; MAX=float(a[3]) if len(a)>3 else 30
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.context.scene.render.fps=30; bpy.ops.import_scene.gltf(filepath=a[0]); sc=bpy.context.scene
arm=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]; arm.animation_data_create(); mw=arm.matrix_world; P='mixamorig:'
def ang(s):
    hip=(mw@arm.pose.bones[P+'Hips'].matrix).to_3x3()@(mw@arm.data.bones[P+'Hips'].matrix_local).to_3x3().inverted()
    lat=(hip@Vector((1,0,0))).normalized(); up=(hip@Vector((0,0,1))).normalized(); fwd=lat.cross(up).normalized()
    pb=arm.pose.bones[P+s+'Arm']; d=(mw.to_3x3()@(pb.tail-pb.head)).normalized()
    sh=mw@pb.head; sg=1 if (sh-(mw@arm.pose.bones[P+'Hips'].head)).dot(lat)>0 else -1
    ox=d.dot(lat)*sg; pr=d-lat*sg*ox
    return math.degrees(math.atan2(ox,max(1e-6,pr.length))),fwd,sg
res={}
for act in bpy.data.actions:
    cl=act.name.split('_'+arm.name)[0]
    if not re.search(a[2],cl): continue
    arm.animation_data.action=act; b0=a0=0
    for fr in range(int(act.frame_range[0]),int(act.frame_range[1])+1):
        sc.frame_set(fr)
        for s in ('Left','Right'):
            g,fwd,sg=ang(s); b0=max(b0,g)
            if g<=MAX: continue
            pb=arm.pose.bones[P+s+'Arm']; pw=mw@pb.head
            for _ in range(6):
                g,fwd,sg=ang(s)
                if g<=MAX+0.3: break
                t=math.radians(g-MAX)
                for sign in (1,-1):
                    old=pb.matrix.copy()
                    pb.matrix=mw.inverted()@Matrix.Translation(pw)@Matrix.Rotation(sign*t,4,fwd)@Matrix.Translation(-pw)@mw@pb.matrix; bpy.context.view_layer.update()
                    if ang(s)[0]<g: break
                    pb.matrix=old; bpy.context.view_layer.update()
            pb.rotation_mode='QUATERNION'; pb.keyframe_insert('rotation_quaternion',frame=fr)
    for fr in range(int(act.frame_range[0]),int(act.frame_range[1])+1):
        sc.frame_set(fr); a0=max([a0]+[ang(s)[0] for s in ('Left','Right')])
    res[cl]=[round(b0,1),round(a0,1)]; print('CAP',cl,res[cl],flush=True)
json.dump(res,open(a[1].replace('.glb','.swingcap.json'),'w'))
bpy.ops.export_scene.gltf(filepath=a[1],export_format='GLB',export_animation_mode='ACTIONS',export_force_sampling=True,export_yup=True,export_skins=True,export_apply=False)
