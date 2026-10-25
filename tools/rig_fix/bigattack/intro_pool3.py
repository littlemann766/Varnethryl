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
# STAGGERED in-place pool intro: R arm reaches & plants, then L, then torso-led haul with side-to-side weight shift, roar.
# FK only (no IK -> no pole flips); elbow is a one-way hinge (elbow >= 5 deg always).
def arm1(r, s, fwd, out=8, elbow=15, twist=0):
    sg = 1 if s == 'L' else -1; elbow = max(5, min(elbow, 120))
    r['upperArm_'+s] = q(Z, sg*twist) @ q(X, -fwd) @ q(Y, sg*-out); r['foreArm_'+s] = q(X, -elbow); r['shoulder_'+s] = q(X, -fwd*0.12) @ q(Y, sg*-min(fwd,120)*0.05)
    r['hand_'+s] = q(X, -elbow*0.2)
def bd(sp, tw=0, sd=0, head=0, hips=0):
    r = lean(sp, hips=hips, head=head)
    r['spine'] = q(Z, tw*0.3) @ q(Y, sd*0.4) @ r['spine']; r['spine2'] = q(Z, tw*0.35) @ q(Y, sd*0.35) @ r['spine2']; r['chest'] = q(Z, tw*0.35) @ q(Y, sd*0.25) @ r['chest']
    r['head'] = q(Z, -tw*0.4) @ r['head']; return r
def K(t, sp, tw, sd, head, L, R, jaw=0, hips=0, legs=12):
    r = bd(sp, tw, sd, head, hips); arm1(r, 'L', *L); arm1(r, 'R', *R); key(t, rot=legsdangle(r, legs), jaw=jaw)
import os
if os.environ.get('CLIP','intro') == 'intro':
    # v3: plants solved onto the LOCAL lava surface. Game rise y = 10 + 16.8*min(t,3.5)/3.5 (linear), node scale 1.3362, lava y 38.
    GS = 1.3362
    def LAVA(t): return (38.0 - (10.0 + 16.8*min(t, 3.5)/3.5)) / GS      # native units, model space z
    def pose_now(r):
        for bn in ['hips','spine','spine2','chest','upperChest','neck','head','shoulder_L','shoulder_R','upperArm_L','upperArm_R','foreArm_L','foreArm_R','hand_L','hand_R']:
            if bn in P: setL(P[bn], r.get(bn, Quaternion()))
        bpy.context.view_layer.update()
    def palm(s):
        h = arm.matrix_world @ P['hand_'+s].head; t_ = arm.matrix_world @ P['hand_'+s].tail; return h.lerp(t_, 0.6), (t_ - h).normalized()
    def solve(r, s, tz, out):
        sg = 1 if s == 'L' else -1; best = None
        for fwd in range(20, 151, 2):
            for el in range(5, 96, 3):
                arm1(r, s, fwd, out, el); r['shoulder_'+s] = r['shoulder_'+s] @ q(Y, sg*10); r['hand_'+s] = q(X, 0); pose_now(r); p, d = palm(s)
                c = (p.z - tz)**2 + 0.02*(p.y + 0.36*H)**2
                if best is None or c < best[0]: best = (c, fwd, el)
        _, fwd, el = best; arm1(r, s, fwd, out, el); r['shoulder_'+s] = r['shoulder_'+s] @ q(Y, sg*10); hb = None
        for hp in range(-90, 91, 5):     # palm down: fingers level/slightly down
            r['hand_'+s] = q(X, hp); pose_now(r); p, d = palm(s); c = (d.z + 0.15)**2
            if hb is None or c < hb[0]: hb = (c, hp)
        r['hand_'+s] = q(X, hb[1])
        bb = None
        for fw2 in [fwd + k*0.5 for k in range(-16, 17)]:
            arm1(r, s, fw2, out, el); r['shoulder_'+s] = r['shoulder_'+s] @ q(Y, sg*10); r['hand_'+s] = q(X, hb[1]); pose_now(r); p, d = palm(s)
            if bb is None or abs(p.z - tz) < bb[0]: bb = (abs(p.z - tz), fw2)
        fwd = bb[1]; arm1(r, s, fwd, out, el); r['shoulder_'+s] = r['shoulder_'+s] @ q(Y, sg*10); r['hand_'+s] = q(X, hb[1])
        pose_now(r); p, d = palm(s); PLANT.append((s, round(r_t[0], 2), round(p.z, 2), round(tz, 2), fwd, el, hb[1]))
    PLANT = []; r_t = [0]
    def K3(t, sp, tw, sd, head, L, R, jaw=0, hips=0, legs=12):
        r_t[0] = t; r = bd(sp, tw, sd, head, hips); tz = LAVA(t)
        for s_, A_ in (('L', L), ('R', R)):
            if A_[0] == 'P': arm1(r, s_, 60, A_[1], 15)
            else: arm1(r, s_, *A_)
        for s_, A_ in (('L', L), ('R', R)):
            if A_[0] == 'P': solve(r, s_, tz + 0.01*H, A_[1])
        key(t, rot=legsdangle(r, legs), jaw=jaw)
    # 0-0.75: right arm already up through the surface (fingertips above LAVA(0)=1.0H), left low
    K3(0.0, 30, 10, 6, -25, (25, 12, 55), (168, 18, 25))
    K3(0.75, 26, 14, 7, -22, (28, 12, 52), (172, 20, 22), jaw=6)
    K3(1.2, 24, 16, 8, -24, (30, 14, 50), (160, 22, 30), jaw=8)
    # smooth overhead -> forward reach -> plant (0.8 s instead of 0.25 s)
    K3(1.6, 30, 14, 2, -16, (34, 14, 52), (122, 24, 32), jaw=10)
    K3(2.0, 40, 14, -8, -8, (55, 16, 70), ('P', 26), jaw=14)
    K3(2.3, 42, 8, -10, -6, (105, 18, 55), ('P', 26), jaw=8)
    K3(2.8, 36, -6, -10, -16, (166, 22, 30), ('P', 26), jaw=8)
    K3(3.05, 38, -10, -4, -10, (124, 24, 32), ('P', 26), jaw=10)
    K3(3.3, 46, -12, 4, -4, ('P', 26), ('P', 26), jaw=16)
    K3(3.55, 48, -10, 6, -2, ('P', 26), ('P', 26), jaw=6)
    K3(4.1, 54, 10, -10, 6, ('P', 28), ('P', 24), jaw=16, hips=-4)
    K3(4.6, 42, -8, 9, 10, ('P', 26), ('P', 28), jaw=10, hips=-6)
    K3(5.1, 30, 6, -5, 6, (45, 26, 30), (40, 24, 40), jaw=8, hips=-4)
    K3(5.6, 16, 0, 2, 0, (30, 18, 30), (34, 18, 24), jaw=4)
    K3(6.1, 12, 4, 0, 10, (25, 14, 45), (10, 40, 45), jaw=8, legs=8)
    K3(6.6, -14, -4, 0, -28, (-10, 45, 40), (-25, 58, 35), jaw=30, legs=8)
    K3(6.9, -18, 0, 0, -32, (-26, 58, 36), (-28, 60, 38), jaw=34, legs=8)
    K3(8.0, -20, 3, -2, -34, (-28, 60, 38), (-26, 56, 36), jaw=34, legs=8)
    K3(8.7, 6, 0, 0, -2, (6, 10, 14), (4, 10, 12), jaw=2, legs=8)
    r = bd(5, 0, 0, -2); arm1(r, 'L', 5, 8, 12); arm1(r, 'R', 5, 8, 12); END = key(9.2, rot=legsdangle(r, 8))
    for p_ in PLANT: print('PLANT', p_)
else:
    # death_pool: in place, shudder, sag, collapse forward onto the rim; arms flop out ahead over the surface, stays mostly above the lava
    K(0.0, 6, 0, 0, -2, (8, 10, 14), (6, 10, 12))
    K(0.25, -12, 6, 4, -24, (20, 30, 40), (30, 34, 50), jaw=24)
    K(0.7, -6, -8, -6, -18, (35, 26, 60), (25, 28, 45), jaw=30)
    K(1.2, 28, 10, 8, 10, (55, 22, 40), (60, 20, 35), jaw=18, hips=4)
    K(1.8, 58, -6, -4, 22, (85, 30, 20), (95, 28, 18), jaw=10, hips=8)
    K(2.2, 74, 4, 3, 28, (100, 36, 12), (108, 32, 12), jaw=6, hips=10)
    K(2.45, 70, 2, 2, 24, (96, 36, 14), (104, 32, 14), jaw=4, hips=10)
    END = None
    r = bd(72, 2, 2, 26, 10); arm1(r, 'L', 98, 36, 12); arm1(r, 'R', 106, 32, 12); END = key(3.0, rot=legsdangle(r, 12))
    
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
arm.animation_data.action.name = os.environ.get('CLIP','intro')
n_ = END; fr = []
import numpy as np
mind = (1e9, 0); badel = 0
def segpts(a, b): return [a.lerp(b, k/6) for k in range(7)]
for f in range(1, END+1):
    sc.frame_set(f); Wp = lambda n: arm.matrix_world @ P[n].head
    PL = segpts(Wp('upperArm_L'), Wp('foreArm_L')) + segpts(Wp('foreArm_L'), Wp('hand_L')) + segpts(Wp('hand_L'), arm.matrix_world @ P['hand_L'].tail)
    PR = segpts(Wp('upperArm_R'), Wp('foreArm_R')) + segpts(Wp('foreArm_R'), Wp('hand_R')) + segpts(Wp('hand_R'), arm.matrix_world @ P['hand_R'].tail)
    d = min((a-b).length for a in PL for b in PR); mind = min(mind, (d/H, f))
    for s_ in 'LR':
        u = (Wp('foreArm_'+s_) - Wp('upperArm_'+s_)).normalized(); v = (Wp('hand_'+s_) - Wp('foreArm_'+s_)).normalized()
        if u.dot(v) < -0.2: badel += 1
if os.environ.get('CLIP','intro') == 'intro':
    for f in range(1, 24):
        sc.frame_set(f); t_ = (f-1)/FPS; tip = max((arm.matrix_world @ P['hand_'+x].tail).z for x in 'LR'); print('TIP', round(t_,2), 'tipz', round(tip,2), 'lava', round((38.0-(10.0+16.8*t_/3.5))/1.3362,2)) if f % 6 == 1 else None
print('CHECK arm-arm min dist (xH)', round(mind[0], 3), 'at t', round((mind[1]-1)/FPS, 2), 'elbow folds>100deg', badel)
for f in range(1, n_+1):
    sc.frame_set(f); fr.append({pb.name: [list(r) for r in (pb.matrix @ pb.bone.matrix_local.inverted())] for pb in P})
json.dump({os.environ.get('CLIP','intro'): fr}, open(dst + '.dump.json', 'w'))
for o in list(bpy.data.objects):
    if o.type == 'EMPTY' and (o.name.startswith('ik_') or o.name.startswith('pole_')): bpy.data.objects.remove(o)
for a in list(bpy.data.actions):
    if a.name != os.environ.get('CLIP','intro'): bpy.data.actions.remove(a)
END_OFF = Vector((0,0,0))
json.dump({'clip': 'intro', 'seconds': (END-1)/FPS, 'H': H, 'start_root_model': [0,0,0], 'end_root_model': list(END_OFF), 'rig_scale': S}, open(dst + '.json', 'w'))
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=dst, export_format='GLB', export_animation_mode='ACTIONS', export_force_sampling=True, export_skins=True, export_def_bones=False, export_optimize_animation_size=False, export_image_format='NONE' if hasattr(bpy.types, 'x') else 'AUTO')
print('INTRO done', (END-1)/FPS, 'H', H)
