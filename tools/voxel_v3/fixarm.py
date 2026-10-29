import bpy,sys,math,os
from mathutils import Matrix
a=sys.argv[sys.argv.index('--')+1:]; blend,act,out=a[0],a[1],a[2]
F0,F1=[int(x) for x in os.environ['FR'].split(':')]; ANG=float(os.environ['ANG']); RAMP=int(os.environ.get('RAMP','6'))
SIDES=os.environ.get('SIDES','LR')
bpy.ops.wm.open_mainfile(filepath=blend); sc=bpy.context.scene; sc.render.fps=30
arm=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]; A=bpy.data.actions[act]; arm.animation_data.action=A
TB=arm.data.bones
ups=[n for n in ('upperArm_L','upperArm_R','mixamorig:LeftArm','mixamorig:RightArm') if n in TB and (n.endswith(('_L','LeftArm')) and 'L' in SIDES or n.endswith(('_R','RightArm')) and 'R' in SIDES)]
f0,f1=[int(round(x)) for x in A.frame_range]
def w(f):
    if F0<=f<=F1: return 1
    d=F0-f if f<F0 else f-F1
    return max(0,1-d/RAMP)
mats={}
for f in range(f0,f1+1):
    sc.frame_set(f)
    mats[f]={n:arm.matrix_world@arm.pose.bones[n].matrix for n in ups}
for f in range(f0,f1+1):
    k=w(f)
    if k<=0: continue
    sc.frame_set(f)
    for n in ups:
        M=mats[f][n]; h=M.translation
        sgn=-1 if h.x>(arm.matrix_world@arm.pose.bones['mixamorig:Hips' if 'mixamorig:Hips' in TB else 'hips'].head).x else 1
        R=Matrix.Translation(h)@Matrix.Rotation(math.radians(sgn*ANG*k),4,'Y')@Matrix.Translation(-h)
        pb=arm.pose.bones[n]; pb.matrix=arm.matrix_world.inverted()@R@M
        bpy.context.view_layer.update()
        pb.keyframe_insert('rotation_quaternion',frame=f); pb.keyframe_insert('location',frame=f)
bpy.ops.wm.save_as_mainfile(filepath=out)
print('FIXED',act,ups)
