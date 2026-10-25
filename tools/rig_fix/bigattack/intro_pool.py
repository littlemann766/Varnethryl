# Ashen Titan 'intro': climbs out of the lava ring, hauls over the arena edge, stands, roars. Root motion on 'root' bone.
# Local frame (model space, Blender Z-up, model faces -Y): arena rim edge at y=0 on the floor z=0, arena centre toward -Y, lava toward +Y.
# Clip ends with root at (0,0,0) = standing on the floor ENDY in front of the rim, so end transform == the placement transform.
import bpy, sys, math, json
from mathutils import Vector, Quaternion, Matrix
src, dst = sys.argv[-2], sys.argv[-1]
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=src, bone_heuristic='TEMPERANCE')
arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]; P = arm.pose.bones
S = arm.matrix_world.to_scale()[0]
H = max((arm.matrix_world @ b.head_local).z for b in arm.data.bones if b.name == 'head') / 0.88   # model height (world units)
for a in list(bpy.data.actions): bpy.data.actions.remove(a)
arm.animation_data_create(); arm.animation_data.action = None
for pb in P: pb.rotation_mode = 'QUATERNION'; pb.matrix_basis.identity()
D = math.radians; X, Y, Z = (1,0,0), (0,1,0), (0,0,1)
def q(ax, d): return Quaternion(ax, D(d))
def setL(pb, L): r = pb.bone.matrix_local.to_quaternion(); pb.rotation_quaternion = r.inverted() @ L @ r
def empty(n, loc):
    e = bpy.data.objects.new(n, None); bpy.context.scene.collection.objects.link(e); e.location = loc; return e
W = lambda bn: arm.matrix_world @ arm.data.bones[bn].head_local
IK = {}
for s in 'LR':
    for limb, tip, chain, pole in (('leg', 'foot_'+s, 'shin_'+s, Vector((0,-1,0.3))), ('arm', 'hand_'+s, 'foreArm_'+s, Vector((0.6 if s=='L' else -0.6, 1, 0)))):
        t = empty(f'ik_{limb}_{s}', W(tip)); p = empty(f'pole_{limb}_{s}', W(chain) + pole*H*0.3)
        c = P[chain].constraints.new('IK'); c.target = t; c.pole_target = p; c.chain_count = 2; c.pole_angle = D(-90); c.name = 'ik'
        IK[limb+s] = (t, p, c, W(tip).copy(), W(chain).copy())
REST_ROOT = W('root').copy()
FPS = 30; sc = bpy.context.scene; sc.render.fps = FPS
def key(t, root=(0,0,0), rot=None, ik=None, jaw=0):
    """t sec; root = model-space offset (fractions of H) of the whole body; rot: bone->L; ik: name->(world pos as H fractions relative to rim origin, influence)"""
    f = 1 + round(t*FPS)
    off = Vector(root)*H
    rb = P['root']; rq = rb.bone.matrix_local.to_quaternion()
    rb.location = rq.inverted() @ (off / S); rb.keyframe_insert('location', frame=f)
    rot = dict(rot or {})
    for bn in ['hips','spine','spine2','chest','upperChest','neck','head','shoulder_L','shoulder_R','upperArm_L','upperArm_R','foreArm_L','foreArm_R','hand_L','hand_R','thigh_L','thigh_R','shin_L','shin_R','foot_L','foot_R','jaw']:
        L = rot.get(bn, Quaternion())
        if bn == 'jaw': L = q(X, jaw)
        setL(P[bn], L); P[bn].keyframe_insert('rotation_quaternion', frame=f)
    for name, (tg, pole, c, rest_tip, rest_mid) in IK.items():
        pos, infl = (ik or {}).get(name, (None, 0.0))
        if pos is None: tg.location = rest_tip + off       # follow the body (unused when influence 0)
        else: tg.location = Vector(pos)*H
        pole.location = rest_mid + off + ((Vector((0,-1,0.3)) if name.startswith('leg') else Vector((0.7 if name[-1]=='L' else -0.7, 0.8, 0))))*H*0.35
        c.influence = infl
        tg.keyframe_insert('location', frame=f); pole.keyframe_insert('location', frame=f); c.keyframe_insert('influence', frame=f)
    return f
def arms_fk(fwd, out=0, elbow=10, sym=True, fwdR=None):
    r = {}
    for s, sg in (('L',1),('R',-1)):
        a = fwd if (s == 'L' or fwdR is None) else fwdR
        r['upperArm_'+s] = q(X, -a) @ q(Y, sg*-out); r['foreArm_'+s] = q(X, -elbow); r['shoulder_'+s] = q(X, -a*0.12)
    return r
def lean(sp, hips=0, head=0):
    return {'hips': q(X, hips), 'spine': q(X, sp*0.3), 'spine2': q(X, sp*0.3), 'chest': q(X, sp*0.25), 'upperChest': q(X, sp*0.15), 'neck': q(X, head*0.5), 'head': q(X, head*0.5)}
hx = lambda s: (0.27 if s=='L' else -0.27)      # hand spacing on the rim (fraction of H)
fx = lambda s: (0.14 if s=='L' else -0.16)
RIMH = lambda s: ((hx(s), -0.08, 0.0), 1.0)    # hands planted on the floor just inside the rim edge
def legsdangle(r, k=25):
    for s in 'LR': r['thigh_'+s] = q(X, -k); r['shin_'+s] = q(X, k*1.4)
    return r
seq = []
# IN-PLACE pool intro (root stays at 0; the game raises the node y10->26.8 over 0-3.5s). Lava at ~0.40H (mid-thigh) at the end.
LZ = 0.40
BR = lambda s: ((0.30 if s=='L' else -0.30, -0.22, LZ+0.02), 1.0)   # hands braced on the lava surface, forward of the hips
r = {**lean(35, head=-25), **arms_fk(20, elbow=60)}; key(0.0, rot=legsdangle(dict(r),15))
r = {**lean(20, head=-30), **arms_fk(160, elbow=30, out=15)}; key(1.2, rot=legsdangle(dict(r),15), jaw=8)
r = {**lean(10, head=-20), **arms_fk(170, elbow=20, out=20)}; key(2.3, rot=legsdangle(dict(r),12), jaw=12)
r = {**lean(30, head=-10), **arms_fk(110, elbow=25, out=15)}; key(3.1, rot=legsdangle(dict(r),12), jaw=6)
# 3.5 brace: hands slam down onto the surface
r = {**lean(50, head=5), **arms_fk(60, elbow=15)}; key(3.6, rot=legsdangle(dict(r),10), ik={'armL': BR('L'), 'armR': BR('R')}, jaw=14)
key(3.9, rot=legsdangle(dict(r),10), ik={'armL': BR('L'), 'armR': BR('R')}, jaw=6)
# 3.9-5.4 haul: two heaving pushes, chest rises
r = {**lean(38, hips=-6, head=10), **arms_fk(40)}; key(4.6, rot=legsdangle(dict(r),8), ik={'armL': BR('L'), 'armR': BR('R')}, jaw=16)
r = {**lean(44, head=8), **arms_fk(45)}; key(4.9, rot=legsdangle(dict(r),8), ik={'armL': BR('L'), 'armR': BR('R')}, jaw=8)
r = {**lean(20, hips=-4, head=0), **arms_fk(30, elbow=25)}; key(5.5, rot=legsdangle(dict(r),5), ik={'armL': ((0.30,-0.16,LZ+0.12),0.4), 'armR': ((-0.30,-0.16,LZ+0.12),0.4)}, jaw=4)
# ROAR 6.0-8.4, settle 9.0
r = {**lean(15, head=10), **arms_fk(20, elbow=50, out=10)}; key(6.1, rot=r, jaw=8)
r = {**lean(-18, hips=-4, head=-30), **arms_fk(-25, elbow=35, out=55)}; key(6.6, rot=r, jaw=32)
r2 = {**lean(-20, hips=-4, head=-34), **arms_fk(-28, elbow=38, out=58)}; key(8.2, rot=r2, jaw=34)
r = {**lean(6, head=-2), **arms_fk(5, elbow=12)}; key(8.8, rot=r, jaw=2)
END = key(9.2, rot=r, jaw=0)
# heavy feel: ease every curve
for ob in [arm] + [v[0] for v in IK.values()] + [v[1] for v in IK.values()]:
    if ob.animation_data and ob.animation_data.action:
        for fc in ob.animation_data.action.fcurves:
            for kp in fc.keyframe_points: kp.interpolation = 'BEZIER'; kp.easing = 'AUTO'
sc.frame_start, sc.frame_end = 1, END
bpy.ops.object.select_all(action='DESELECT'); arm.select_set(True); bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='POSE'); bpy.ops.pose.select_all(action='SELECT')
bpy.ops.nla.bake(frame_start=1, frame_end=END, only_selected=True, visual_keying=True, clear_constraints=True, use_current_action=False, bake_types={'POSE'})
bpy.ops.object.mode_set(mode='OBJECT')
arm.animation_data.action.name = 'intro'
n_ = END; fr = []
for f in range(1, n_+1):
    sc.frame_set(f); fr.append({pb.name: [list(r) for r in (pb.matrix @ pb.bone.matrix_local.inverted())] for pb in P})
json.dump({'intro': fr}, open(dst + '.dump.json', 'w'))
for o in list(bpy.data.objects):
    if o.type == 'EMPTY' and (o.name.startswith('ik_') or o.name.startswith('pole_')): bpy.data.objects.remove(o)
for a in list(bpy.data.actions):
    if a.name != 'intro': bpy.data.actions.remove(a)
END_OFF = Vector((0,0,0))
json.dump({'clip': 'intro', 'seconds': (END-1)/FPS, 'H': H, 'start_root_model': [0,0,0], 'end_root_model': list(END_OFF), 'rig_scale': S}, open(dst + '.json', 'w'))
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=dst, export_format='GLB', export_animation_mode='ACTIONS', export_force_sampling=True, export_skins=True, export_def_bones=False, export_optimize_animation_size=False, export_image_format='NONE' if hasattr(bpy.types, 'x') else 'AUTO')
print('INTRO done', (END-1)/FPS, 'H', H)
