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
# 0.0 submerged (head below the lava surface), 1.2 out -> 3.2 rise: arms burst up and forward
r = {**lean(25, head=-10), **arms_fk(30, elbow=40)}; key(0.0, root=(0, 0.30, -1.08), rot=legsdangle(dict(r)))
r = {**lean(30, head=-25), **arms_fk(150, elbow=35, out=10)}; key(1.3, root=(0, 0.27, -0.80), rot=legsdangle(dict(r)), jaw=6)
r = {**lean(35, head=-20), **arms_fk(120, elbow=20, out=12)}; key(1.75, root=(0, 0.25, -0.70), rot=legsdangle(dict(r)), jaw=4)
# 2.05 hands SLAM on the rim (IK on), body sags
r = {**lean(40, head=-15), **arms_fk(80, elbow=10)}; key(2.05, root=(0, 0.24, -0.74), rot=legsdangle(dict(r)), ik={'armL': RIMH('L'), 'armR': RIMH('R')}, jaw=10)
key(2.3, root=(0, 0.24, -0.78), rot=legsdangle(dict(r)), ik={'armL': RIMH('L'), 'armR': RIMH('R')}, jaw=4)
# 2.3-4.0 haul: strain up, chest over the edge (two pulls)
r = {**lean(55, head=10), **arms_fk(60)}; key(3.0, root=(0, 0.17, -0.52), rot=legsdangle(dict(r), 40), ik={'armL': RIMH('L'), 'armR': RIMH('R')}, jaw=14)
key(3.3, root=(0, 0.16, -0.50), rot=legsdangle(dict(r), 40), ik={'armL': RIMH('L'), 'armR': RIMH('R')}, jaw=8)
r = {**lean(65, head=15), **arms_fk(40)}; key(4.0, root=(0, 0.08, -0.33), rot=legsdangle(dict(r), 55), ik={'armL': RIMH('L'), 'armR': RIMH('R')}, jaw=12)
# 4.0-5.0 right knee/foot up onto the floor
r = {**lean(60, head=10), **arms_fk(40)}
key(4.7, root=(0, 0.03, -0.22), rot=r, ik={'armL': RIMH('L'), 'armR': RIMH('R'), 'legR': ((fx('R'), -0.02, 0.0), 1.0), 'legL': ((fx('L'), 0.12, -0.25), 1.0)}, jaw=6)
key(5.1, root=(0, -0.02, -0.17), rot=r, ik={'armL': RIMH('L'), 'armR': RIMH('R'), 'legR': ((fx('R'), -0.02, 0.0), 1.0), 'legL': ((fx('L'), 0.10, -0.15), 1.0)}, jaw=6)
# 5.1-6.3 heavy stand: left foot up beside, hands release, rise
r = {**lean(40, head=0), **arms_fk(25, elbow=25)}
key(5.7, root=(0, -0.06, -0.09), rot=r, ik={'armL': ((0.25, -0.16, 0.10), 0.35), 'armR': ((-0.25, -0.16, 0.10), 0.35), 'legR': ((fx('R'), -0.02, 0.0), 1.0), 'legL': ((fx('L'), -0.08, 0.0), 1.0)}, jaw=2)
r = {**lean(8, head=-4), **arms_fk(8, elbow=15)}
key(6.5, root=(0, -0.08, -0.015), rot=r, ik={'legR': ((fx('R'), -0.02, 0.0), 1.0), 'legL': ((fx('L'), -0.08, 0.0), 1.0)})
key(6.8, root=(0, -0.08, -0.025), rot=r, ik={'legR': ((fx('R'), -0.02, 0.0), 1.0), 'legL': ((fx('L'), -0.08, 0.0), 1.0)})
# 6.8-9.0 ROAR: chest up, arms flung out/back, head back, jaw wide; 9.0-9.8 settle into idle stance
FT = {'legR': ((fx('R'), -0.02, 0.0), 1.0), 'legL': ((fx('L'), -0.08, 0.0), 1.0)}
r = {**lean(15, head=10), **arms_fk(20, elbow=50, out=10)}; key(7.3, root=(0, -0.08, -0.04), rot=r, ik=FT, jaw=8)
r = {**lean(-18, hips=-4, head=-30), **arms_fk(-25, elbow=35, out=55)}; key(7.8, root=(0, -0.08, -0.01), rot=r, ik=FT, jaw=32)
r2 = {**lean(-20, hips=-4, head=-34), **arms_fk(-28, elbow=38, out=58)}; key(8.8, root=(0, -0.08, -0.012), rot=r2, ik=FT, jaw=34)
r = {**lean(6, head=-2), **arms_fk(5, elbow=12)}; key(9.6, root=(0, -0.08, -0.004), rot=r, ik=FT, jaw=2)
END = key(10.0, root=(0, -0.08, 0.0), rot=r, ik=FT, jaw=0)
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
END_OFF = Vector((0, -0.08, 0))*H
json.dump({'clip': 'intro', 'seconds': (END-1)/FPS, 'H': H, 'start_root_model': [0, 0.30*H, -1.08*H], 'end_root_model': list(END_OFF), 'rig_scale': S}, open(dst + '.json', 'w'))
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=dst, export_format='GLB', export_animation_mode='ACTIONS', export_force_sampling=True, export_skins=True, export_def_bones=False, export_optimize_animation_size=False, export_image_format='NONE' if hasattr(bpy.types, 'x') else 'AUTO')
print('INTRO done', (END-1)/FPS, 'H', H)
