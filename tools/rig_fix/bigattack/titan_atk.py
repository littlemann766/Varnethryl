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

for pb in P:
    for c in list(pb.constraints): pb.constraints.remove(c)
for o in list(bpy.data.objects):
    if o.type == 'EMPTY': bpy.data.objects.remove(o)
IK.clear()
GS = 1.3362
# plate (arena floor y39) relative to the node at stage 1 (node y 26.8): z = 12.2 m, 17 m out (game metres / GS -> native)
PZ = 12.2/GS; PY = -17.0/GS
FB = ['hips','spine','spine2','chest','upperChest','neck','head','shoulder_L','shoulder_R','upperArm_L','upperArm_R','foreArm_L','foreArm_R','hand_L','hand_R']
def pose_now(r):
    for bn in FB:
        if bn in P: setL(P[bn], r.get(bn, Quaternion()))
    bpy.context.view_layer.update()
def fist(s):
    h = arm.matrix_world @ P['hand_'+s].head; t_ = arm.matrix_world @ P['hand_'+s].tail; return h.lerp(t_, 0.5)
def solve(sp_rng, sides, tgt, tw=0, sd=0, head=10, out=10):
    """search torso lean + arm fwd/elbow so the fist(s) land on tgt (x mirrored for L). returns pose dict"""
    best = None; act_ = arm.animation_data.action; arm.animation_data.action = None
    for sp in sp_rng:
        for fwd in range(30, 151, 4):
            for el in (5, 12, 20, 30):
              for oo in (out-30, out-15, out):
                r = bd(sp, tw, sd, head)
                for s_ in sides: arm1(r, s_, fwd, oo, el)
                pose_now(r); c = 0
                for s_ in sides:
                    t_ = Vector(((tgt[0] if s_ == 'R' else -tgt[0]), tgt[1], tgt[2])); c += (fist(s_) - t_).length
                if best is None or c < best[0]: best = (c, sp, fwd, el, oo)
    c, sp, fwd, el, oo = best; r = bd(sp, tw, sd, head)
    for s_ in sides: arm1(r, s_, fwd, oo, el)
    pose_now(r); arm.animation_data.action = act_
    ERR.append((CUR[0], sides, round(c/len(sides), 2), 'tgt', [round(x,2) for x in tgt], 'recomp', round(sum((fist(s_) - Vector(((tgt[0] if s_ == 'R' else -tgt[0]), tgt[1], tgt[2]))).length for s_ in sides)/len(sides),2), sp, fwd, el, [round(x, 2) for x in fist(sides[0])]))
    return r
def full(r, legs=10): return legsdangle(r, legs)
ERR = []; CUR = ['']; CLIPS = {}; CONTACT = {}
def clip(name, fn):
    CUR[0] = name; act = bpy.data.actions.new(name); arm.animation_data.action = act
    end = fn(); CLIPS[name] = (act, end)
def idle_r():
    r = bd(8, 0, 0, -2); arm1(r, 'L', 12, 12, 20); arm1(r, 'R', 12, 12, 20); return r
def K(t, r, jaw=0, legs=10): return key(t, rot=full(dict(r), legs), jaw=jaw)
def A_(r, s, *a): arm1(r, s, *a); return r
# ---------- eruption_slam: wave trigger. Colossal double-fist overhead slam onto the plate ring, impact 1.288 ----------
def eruption():
    K(0, idle_r())
    r = bd(-16, 0, 0, -26); A_(r, 'L', 150, 22, 40); A_(r, 'R', 150, 22, 40); K(0.55, r, jaw=18)
    r = bd(-22, 0, 0, -30); A_(r, 'L', 150, 18, 30); A_(r, 'R', 150, 18, 30); K(0.95, r, jaw=30)
    r = solve(range(30, 81, 5), 'LR', (-0.25*H, PY, PZ), head=18, out=12); K(1.288, r, jaw=34); CONTACT['eruption_slam'] = 1.288
    K(1.55, r, jaw=20)
    r = bd(30, 0, 0, 8); A_(r, 'L', 70, 16, 30); A_(r, 'R', 70, 16, 30); K(2.2, r, jaw=6)
    return K(3.0, idle_r())
# ---------- magma_sweep: right arm sweeps right->left across the plate, spray from hand_R at 0.976 ----------
def sweep():
    K(0, idle_r())
    r = bd(10, -40, 6, -8); A_(r, 'R', 70, 70, 30); A_(r, 'L', 30, 20, 40); K(0.6, r, jaw=10)
    r = bd(28, -10, 2, 6); A_(r, 'R', 85, 40, 10); A_(r, 'L', 25, 25, 40); K(0.976, r, jaw=26); CONTACT['magma_sweep'] = 0.976
    r = bd(30, 30, -4, 8); A_(r, 'R', 85, 5, 10); A_(r, 'L', 20, 30, 40); K(1.35, r, jaw=16)
    r = bd(20, 40, -4, 4); A_(r, 'R', 70, -10, 25); K(1.8, r, jaw=6)
    return K(2.733, idle_r())
# ---------- boulder_hurl: R hand rips a rock out of the lava beside him (1.224), heaves it overhead, throws at the plate (2.383) ----------
LZ1 = (38.0 - 26.8)/GS
def boulder():
    K(0, idle_r())
    r = bd(30, -30, 14, 10); A_(r, 'R', 40, 40, 40); A_(r, 'L', 30, 25, 30); K(0.7, r, jaw=6)
    CUR[0] = 'boulder_hurl'; rr = solve(range(30, 81, 5), 'R', (-0.24*H, -0.34*H, LZ1 + 0.02*H), tw=-20, sd=8, head=14, out=25); A_(rr, 'L', 30, 25, 30); K(1.224, rr, jaw=20)
    r = bd(5, -20, 4, -14); A_(r, 'R', 120, 30, 70); A_(r, 'L', 60, 25, 50); K(1.7, r, jaw=14)
    r = bd(-20, -10, 0, -26); A_(r, 'R', 160, 15, 80); A_(r, 'L', 100, 30, 40); K(2.05, r, jaw=24)
    r = bd(34, 16, -4, 10); A_(r, 'R', 95, 10, 12); A_(r, 'L', 20, 30, 30); K(2.383, r, jaw=34); CONTACT['boulder_hurl'] = 2.383
    r = bd(38, 22, -6, 12); A_(r, 'R', 70, 10, 15); K(2.7, r, jaw=14)
    return K(3.6, idle_r())
# ---------- attack1: right hammer-fist slam on the plate ----------
def a1():
    K(0, idle_r())
    r = bd(-10, -25, 8, -18); A_(r, 'R', 150, 30, 70); A_(r, 'L', 40, 30, 40); K(0.75, r, jaw=14)
    r = solve(range(30, 71, 5), 'R', (-0.18*H, PY, PZ), tw=15, sd=-4, head=16, out=14); A_(r, 'L', 10, 35, 40); K(1.2, r, jaw=28); CONTACT['attack1'] = 1.2
    K(1.45, r, jaw=12)
    return K(2.2, idle_r())
# ---------- attack2: left hammer-fist slam (mirror timing, different wind-up: sideways arc) ----------
def a2():
    K(0, idle_r())
    r = bd(-4, 30, -8, -10); A_(r, 'L', 130, 60, 50); A_(r, 'R', 40, 30, 40); K(0.7, r, jaw=12)
    r = solve(range(30, 71, 5), 'L', (-0.25*H, PY, PZ), tw=-18, sd=5, head=14, out=20); A_(r, 'R', 10, 35, 40); K(1.1, r, jaw=26); CONTACT['attack2'] = 1.1
    K(1.35, r, jaw=10)
    return K(2.0, idle_r())
# ---------- attack3: scoop lava with both hands and hurl it forward (throw) ----------
def a3():
    K(0, idle_r())
    CUR[0] = 'attack3'; r = solve(range(30, 81, 5), 'LR', (-0.2*H, -0.36*H, LZ1 + 0.02*H), head=12, out=12); K(0.7, r, jaw=8)
    r = bd(-12, 0, 0, -20); A_(r, 'L', 120, 25, 60); A_(r, 'R', 120, 25, 60); K(1.05, r, jaw=20)
    r = bd(26, 0, 0, 8); A_(r, 'L', 95, 15, 8); A_(r, 'R', 95, 15, 8); K(1.3, r, jaw=32); CONTACT['attack3'] = 1.3
    K(1.6, r, jaw=12)
    return K(2.4, idle_r())
for n, f in [('eruption_slam', eruption), ('magma_sweep', sweep), ('boulder_hurl', boulder), ('attack1', a1), ('attack2', a2), ('attack3', a3)]: clip(n, f)
for e in ERR: print('SOLVE', e)
# per-frame checks: arm-arm gap, elbow folds, hands vs torso hull (simple: hand inside chest capsule)
dump = {}
for n, (act, end) in CLIPS.items():
    arm.animation_data.action = act
    for fc in act.fcurves:
        for kp in fc.keyframe_points: kp.interpolation = 'BEZIER'
    fr = []; gap = 1e9; folds = 0
    for f in range(1, end+1):
        sc.frame_set(f)
        fr.append({pb.name: [list(r_) for r_ in (pb.matrix @ pb.bone.matrix_local.inverted())] for pb in P})
        Wp = lambda b: arm.matrix_world @ P[b].head
        pl = [Wp('foreArm_L').lerp(Wp('hand_L'), k/4) for k in range(5)]; pr = [Wp('foreArm_R').lerp(Wp('hand_R'), k/4) for k in range(5)]
        gap = min(gap, min((a-b).length for a in pl for b in pr))
        for s_ in 'LR':
            u = (Wp('foreArm_'+s_) - Wp('upperArm_'+s_)).normalized(); v = (Wp('hand_'+s_) - Wp('foreArm_'+s_)).normalized()
            if u.dot(v) < -0.2: folds += 1
    rep = {'sec': round((end-1)/FPS, 3), 'arm_gap_xH': round(gap/H, 3), 'folds': folds}
    if n in CONTACT:
        sc.frame_set(1 + round(CONTACT[n]*FPS)); rep['t'] = CONTACT[n]; rep['fistR'] = [round(x*GS, 2) for x in fist('R')]; rep['fistL'] = [round(x*GS, 2) for x in fist('L')]
    print('CLIP', n, rep); dump[n] = fr
json.dump(dump, open(dst + '.dump.json', 'w'))
print('ATK done')
