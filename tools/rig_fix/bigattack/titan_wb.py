# Ashen Titan 'intro': climbs out of the lava ring, hauls over the arena edge, stands, roars. Root motion on 'root' bone.
# Local frame (model space, Blender Z-up, model faces -Y): arena rim edge at y=0 on the floor z=0, arena centre toward -Y, lava toward +Y.
# Clip ends with root at (0,0,0) = standing on the floor ENDY in front of the rim, so end transform == the placement transform.
import bpy, sys, math, json, os
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
IK = {}; FROT = {}
for s in 'LR':
    for limb, tip, chain, pole in (('leg', 'foot_'+s, 'shin_'+s, Vector((0,-1,0.3))), ('arm', 'hand_'+s, 'foreArm_'+s, Vector((0.6 if s=='L' else -0.6, 1, 0)))):
        t = empty(f'ik_{limb}_{s}', W(tip)); p = empty(f'pole_{limb}_{s}', W(chain) + pole*H*0.3)
        if limb == 'leg':
            c = P[tip].constraints.new('IK'); c.target = t; c.pole_target = p; c.chain_count = 3; c.use_tail = False; c.pole_angle = D(float(os.environ.get("LEGPOLE", 90))); c.name = 'ik'
            fe = bpy.data.objects.new('frot_'+s, None); bpy.context.scene.collection.objects.link(fe); fe.rotation_mode = 'QUATERNION'
            fe.rotation_quaternion = (arm.matrix_world @ arm.data.bones[tip].matrix_local).to_quaternion(); FROT[s] = (fe, fe.rotation_quaternion.copy())
            cr = P[tip].constraints.new('COPY_ROTATION'); cr.target = fe; cr.name = 'flat'
        else:
            c = P[chain].constraints.new('IK'); c.target = t; c.pole_target = p; c.chain_count = 2; c.pole_angle = D(-90); c.name = 'ik'
        IK[limb+s] = (t, p, c, W(tip).copy(), W(chain).copy())
REST_ROOT = W('root').copy()
FPS = 30; sc = bpy.context.scene; sc.render.fps = FPS
FYAW = {}
def key(t, root=(0,0,0), rot=None, ik=None, jaw=0, yaw=0.0, scl=1.0):
    """t sec; root = model-space offset (fractions of H) of the whole body; rot: bone->L; ik: name->(world pos as H fractions relative to rim origin, influence)"""
    f = 1 + round(t*FPS)
    off = Vector(root)*H
    rb = P['root']; rq = rb.bone.matrix_local.to_quaternion()
    rb.location = rq.inverted() @ (off / S); rb.keyframe_insert('location', frame=f)
    rb.rotation_mode = 'QUATERNION'; rb.rotation_quaternion = rq.inverted() @ q(Z, yaw) @ rq; rb.keyframe_insert('rotation_quaternion', frame=f)
    rb.scale = (scl, scl, scl); rb.keyframe_insert('scale', frame=f)
    for s_, (fe, q0) in FROT.items():
        fe.rotation_quaternion = q(Z, FYAW.get(s_, 0.0)) @ q0; fe.keyframe_insert('rotation_quaternion', frame=f)
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
# ================= WORLD-BOSS clips (slow, heavy). Root motion on 'root' (forward = -Y). =================
for s_ in 'LR':
    IK['arm'+s_][2].influence = 0
FR = {s_: IK['leg'+s_][3]/H for s_ in 'LR'}          # rest foot target (H fractions)
CLIPS = {}; EVENTS = {}; CONTACT = {}; ERR = []; CUR = ['']
def clip(name, fn):
    CUR[0] = name; act = bpy.data.actions.new(name); arm.animation_data.action = act
    EA = {}
    FYAW.clear()
    for ob in [v[0] for v in IK.values()] + [v[1] for v in IK.values()] + [v[0] for v in FROT.values()]:
            ob.animation_data_create(); ob.animation_data.action = bpy.data.actions.new(name + '_' + ob.name); EA[ob.name] = ob.animation_data.action
    end = fn(); CLIPS[name] = (act, end); EACT[name] = EA
EACT = {}
def smooth(x): x = max(0.0, min(1.0, x)); return x*x*(3 - 2*x)
def legs_free(r):
    KS = float(os.environ.get('KSIGN', 1))
    for s_ in 'LR': r.setdefault('thigh_'+s_, q(X, -12*KS)); r.setdefault('shin_'+s_, q(X, 24*KS))
    return r
def foot_track(t, T, s, ph, duty, lift):
    """returns (y offset, z lift, planted?) for foot s; body travels -2s per cycle T; ph = phase offset"""
    u = ((t/T - ph) % 1.0)
    k = math.floor(t/T - ph)                     # cycle index
    plant_y = lambda kk: -2*s*((kk + ph) + duty/2)    # body pos at mid-stance (fraction of cycle) times 2s
    if u < duty: return plant_y(k), 0.0, True
    w = (u - duty)/(1 - duty); e = smooth(w)
    return plant_y(k) + (plant_y(k+1) - plant_y(k))*e, lift*math.sin(math.pi*w), False
def locomotion(T, stride, duty, lift, bob, sway, lean_, armsw, cycles=1, label='walk'):
    N = int(T*cycles*FPS); ev = []
    prev = {}
    for f in range(0, N + 1, 2):
        t = f/FPS; body_y = -2*stride*t/T
        ik = {}; plantedL = None
        for s_, ph in (('L', 0.0), ('R', 0.5)):
            y, z, pl = foot_track(t, T, stride, ph, duty, lift)
            p = FR[s_].copy(); p.y += y; p.z += z; ik['leg'+s_] = (tuple(p), 1.0)
            if pl and prev.get(s_) is False: ev.append((round(t, 3), s_))
            prev[s_] = pl
        # weight shift: over the planted (stance) foot; settle dip just after each heel strike
        ph2 = (t/T) % 1.0
        side = math.sin(2*math.pi*(ph2 - duty/2 + 0.25))   # +1 over L stance
        settle = min(((ph2 - a) % 1.0) for a in (0.0, 0.5))
        dip = bob*math.exp(-settle*T/0.35) + bob*0.4*math.cos(4*math.pi*ph2)
        root = (sway*side, body_y, -dip - bob*0.6 - 0.035)
        r = bd(lean_ + 3*math.exp(-settle*T/0.35), -6*side, -5*side, -2 + 3*math.exp(-settle*T/0.5), hips=4*side)
        sw = armsw*math.sin(2*math.pi*ph2)
        arm1(r, 'L', 14 - sw, 14, 22); arm1(r, 'R', 14 + sw, 14, 22)
        key(t, root=root, rot=legs_free(r), ik=ik, jaw=2)
    # contact events at exact plant start
    EVENTS[label] = sorted({(round((k + ph)*T, 3) if ph == 0 else round((k + ph)*T, 3), s_) for k in range(cycles+1) for s_, ph in (('L', 0.0), ('R', 0.5)) if (k + ph)*T <= T*cycles - 1e-6})
    return 1 + N
def wb_walk(): return locomotion(T=10.0, stride=0.13, duty=0.66, lift=0.07, bob=0.018, sway=0.035, lean_=8, armsw=14, label='wb_walk')
def wb_run():  return locomotion(T=5.6, stride=0.20, duty=0.52, lift=0.11, bob=0.03, sway=0.03, lean_=16, armsw=26, label='wb_run')
def wb_idle():
    for f in range(0, int(6.0*FPS) + 1, 3):
        t = f/FPS; b = math.sin(2*math.pi*t/6.0)
        r = bd(8 - 2*b, 0, 0.6*math.sin(2*math.pi*t/12), -2 - 2*b); arm1(r, 'L', 12 + 2*b, 13 + 1.5*b, 20); arm1(r, 'R', 12 + 2*b, 13 + 1.5*b, 20)
        r['chest'] = q(X, -2.5*b) @ r['chest']; r['upperChest'] = q(X, -2*b) @ r['upperChest']
        key(t, root=(0, 0, 0.006*b - 0.006), rot=legs_free(r), ik={'legL': (tuple(FR['L']), 1.0), 'legR': (tuple(FR['R']), 1.0)}, jaw=1 + b)
    return 1 + int(6.0*FPS)
YAWCAP = 18.0   # deg/s
def turn(sgn, label):
    # 90 deg in two heavy pivot steps; whole body yaw follows a capped-speed ramp; each foot lifts, re-plants rotated
    TOT = 90.0; T = TOT/YAWCAP*1.25; N = int(T*FPS)   # 6.25 s
    def rot2(v, a):
        c, s = math.cos(math.radians(a)), math.sin(math.radians(a)); return Vector((v.x*c - v.y*s, v.x*s + v.y*c, v.z))
    # steps: lead foot (turn side) at 0.10-0.40, other at 0.45-0.75 of T; each carries its foot through 45 deg -> 90
    lead, trail = ('L', 'R') if sgn > 0 else ('R', 'L')
    STEPS = {lead: [(0.08, 0.38, 0, 50), (0.52, 0.80, 50, 90)], trail: [(0.30, 0.58, 0, 45), (0.74, 0.98, 45, 90)]}
    ev = []
    for f in range(0, N + 1, 2):
        t = f/FPS; u = t/T
        yaw = sgn*TOT*smooth((u - 0.05)/0.9)
        ik = {}
        for s_ in 'LR':
            a = 0.0; z = 0.0
            for (u0, u1, a0, a1) in STEPS[s_]:
                if u >= u1: a = a1
                elif u > u0: w = (u - u0)/(u1 - u0); a = a0 + (a1 - a0)*smooth(w); z = 0.06*math.sin(math.pi*w)
            p = rot2(FR[s_], sgn*a); p.z += z; ik['leg'+s_] = (tuple(p), 1.0); FYAW[s_] = sgn*a
        dip = 0.015*sum(math.exp(-abs(u - u1)*T/0.4) for s_ in 'LR' for (_, u1, _, _) in STEPS[s_])
        r = bd(10, -sgn*8*math.sin(math.pi*u), 0, -4, hips=0); r['head'] = q(Z, sgn*14*math.sin(math.pi*min(1, u*1.4))) @ r['head']
        arm1(r, 'L', 14, 16, 24); arm1(r, 'R', 14, 16, 24)
        key(t, root=(0, 0, -dip), rot=legs_free(r), ik=ik, jaw=2, yaw=yaw)
    EVENTS[label] = sorted([(round(u1*T, 3), s_) for s_ in 'LR' for (_, u1, _, _) in STEPS[s_]])
    return 1 + N
FEET = lambda dz=0.0: {'legL': (tuple(FR['L'] + Vector((0, 0, 0)))  , 1.0), 'legR': (tuple(FR['R']), 1.0)}
def KK(t, r, jaw=0, root=(0, 0, 0), ik=None): return key(t, root=root, rot=legs_free(dict(r)), ik=ik or FEET(), jaw=jaw)
def idle_r():
    r = bd(8, 0, 0, -2); arm1(r, 'L', 12, 13, 20); arm1(r, 'R', 12, 13, 20); return r
FB = ['hips','spine','spine2','chest','upperChest','neck','head','shoulder_L','shoulder_R','upperArm_L','upperArm_R','foreArm_L','foreArm_R','hand_L','hand_R']
def pose_now(r):
    for bn in FB:
        if bn in P: setL(P[bn], r.get(bn, Quaternion()))
    bpy.context.view_layer.update()
def fist(s): h = arm.matrix_world @ P['hand_'+s].head; t_ = arm.matrix_world @ P['hand_'+s].tail; return h.lerp(t_, 0.5)
def solve(sp_rng, sides, tgt, tw=0, sd=0, head=10, out=10, root=(0,0,0)):
    best = None; act_ = arm.animation_data.action; arm.animation_data.action = None
    rb = P['root']; rq = rb.bone.matrix_local.to_quaternion(); rb.location = rq.inverted() @ (Vector(root)*H/S); rb.rotation_quaternion = Quaternion(); rb.scale = (1,1,1)
    for sp in sp_rng:
        for fwd in range(30, 151, 4):
            for el in (5, 12, 20, 30):
              for oo in (out-20, out-10, out):
                r = bd(sp, tw, sd, head)
                for s_ in sides: arm1(r, s_, fwd, oo, el)
                pose_now(r); c = sum((fist(s_) - Vector(((tgt[0] if s_ == 'R' else -tgt[0]), tgt[1], tgt[2]))).length for s_ in sides)
                if best is None or c < best[0]: best = (c, sp, fwd, el, oo)
    c, sp, fwd, el, oo = best; r = bd(sp, tw, sd, head)
    for s_ in sides: arm1(r, s_, fwd, oo, el)
    pose_now(r); ERR.append((CUR[0], sides, 'err_m', round(c/len(sides)*GS, 2), 'fist', [round(x*GS, 2) for x in fist(sides[0])])); arm.animation_data.action = act_
    return r
GS = 1.3362
CROUCH = (0, 0.06, -0.16)    # sink the root (knees bend via the foot IK) so the fists reach the ground
def wb_slam():       # two-fist overhead ground slam: anticipation dip 0-0.6, wind-up rise 0.6-2.2, impact 2.6, heavy follow-through, slow recovery to 5.2
    KK(0, idle_r())
    r = bd(16, 0, 0, 6); arm1(r, 'L', 30, 20, 50); arm1(r, 'R', 30, 20, 50); KK(0.6, r, jaw=4, root=(0, 0, -0.03))
    r = bd(-12, 0, 0, -20); arm1(r, 'L', 140, 22, 45); arm1(r, 'R', 140, 22, 45); KK(1.6, r, jaw=18, root=(0, 0.02, 0.01))
    r = bd(-20, 0, 0, -28); arm1(r, 'L', 158, 18, 32); arm1(r, 'R', 158, 18, 32); KK(2.2, r, jaw=30, root=(0, 0.03, 0.015))
    r = solve(range(40, 111, 5), 'LR', (-0.17*H, -0.34*H, 0.03*H), head=18, out=14, root=CROUCH); KK(2.6, r, jaw=36, root=CROUCH); CONTACT['wb_slam'] = 2.6
    KK(3.0, r, jaw=24, root=(CROUCH[0], CROUCH[1], CROUCH[2] - 0.01))
    r2 = bd(34, 0, 0, 10); arm1(r2, 'L', 60, 18, 35); arm1(r2, 'R', 60, 18, 35); KK(3.9, r2, jaw=10, root=(0, 0.02, -0.05))
    return KK(5.2, idle_r())
def wb_sweep():      # right backhand sweep along the ground: wind-up 0-1.8 (twist far left->right), hit 2.2, drag follow-through to 3.0, recover 4.6
    KK(0, idle_r())
    r = bd(6, 20, -4, 0); arm1(r, 'R', 30, 20, 50); arm1(r, 'L', 20, 20, 30); KK(0.5, r, jaw=4)
    r = bd(10, -45, 8, -10); arm1(r, 'R', 80, 80, 40); arm1(r, 'L', 30, 30, 40); KK(1.8, r, jaw=18, root=(0.02, 0, -0.02))
    CUR[0] = 'wb_sweep'; r = solve(range(40, 111, 5), 'R', (-0.22*H, -0.30*H, 0.05*H), tw=-10, sd=6, head=12, out=30, root=CROUCH); KK(2.2, r, jaw=30, root=CROUCH); CONTACT['wb_sweep'] = 2.2
    r = bd(40, 40, -6, 10); arm1(r, 'R', 70, -5, 15); arm1(r, 'L', 20, 30, 40); KK(3.0, r, jaw=14, root=(-0.02, 0.02, -0.07))
    return KK(4.6, idle_r())
def wb_stomp():      # right-foot stomp: weight onto L 0-0.9, knee lifts 0.9-2.0 (arms rise), stomp 2.4, shudder, recover 4.4
    KK(0, idle_r())
    RL = lambda z, y=0.0: {'legL': (tuple(FR['L']), 1.0), 'legR': (tuple(FR['R'] + Vector((0, y, z))), 1.0)}
    r = bd(6, 0, 6, 0, hips=4); arm1(r, 'L', 20, 25, 30); arm1(r, 'R', 20, 25, 30); key(0.9, root=(0.05, 0, -0.02), rot=legs_free(r), ik=RL(0.0), jaw=4)
    r = bd(-6, 0, 8, -12, hips=6); arm1(r, 'L', 70, 45, 50); arm1(r, 'R', 70, 45, 50); key(2.0, root=(0.06, 0.01, 0.0), rot=legs_free(r), ik=RL(0.28, -0.08), jaw=22)
    r = bd(22, 0, 0, 8); arm1(r, 'L', 40, 30, 30); arm1(r, 'R', 40, 30, 30); key(2.4, root=(0.01, 0, -0.05), rot=legs_free(r), ik=RL(0.0, -0.10), jaw=36); CONTACT[CUR[0]] = 2.4
    key(2.8, root=(0.0, 0, -0.06), rot=legs_free(r), ik=RL(0.0, -0.10), jaw=20)
    r = bd(10, 0, 0, -2); arm1(r, 'L', 14, 14, 22); arm1(r, 'R', 14, 14, 22); key(3.6, root=(0, 0, -0.02), rot=legs_free(r), ik=RL(0.06, -0.05), jaw=6)
    return key(4.4, rot=legs_free(idle_r()), ik=FEET(), jaw=2)
def grow():          # brace, swell, roar: root scale 1 -> GROW over 1.0-4.2 s, holds at the end (Lucky can keep the node scale x GROW after)
    G = 3.0
    KK(0, idle_r())
    r = bd(26, 0, 0, 10); arm1(r, 'L', 30, 30, 70); arm1(r, 'R', 30, 30, 70); key(1.0, root=(0, 0, -0.04), rot=legs_free(r), ik=FEET(), jaw=6)
    r = bd(-14, 0, 0, -24); arm1(r, 'L', 110, 70, 40); arm1(r, 'R', 110, 70, 40)
    for t, sc_ in ((2.0, 1.6), (3.0, 2.4), (4.2, G)):
        rr = dict(r); key(t, root=(0, 0, 0), rot=legs_free(rr), ik={'legL': (tuple(FR['L']*sc_), 1.0), 'legR': (tuple(FR['R']*sc_), 1.0)}, jaw=34, scl=sc_)
    r = bd(8, 0, 0, -2); arm1(r, 'L', 12, 13, 20); arm1(r, 'R', 12, 13, 20)
    return key(5.4, rot=legs_free(r), ik={'legL': (tuple(FR['L']*G), 1.0), 'legR': (tuple(FR['R']*G), 1.0)}, jaw=4, scl=G)
HOLD = {}
def ritual_poses(kind):
    if kind == 'fissure':   # both fists high, glowing; release = ground slam
        r = bd(-14, 0, 0, -22); arm1(r, 'L', 150, 22, 40); arm1(r, 'R', 150, 22, 40); return r
    if kind == 'meteor':    # right arm raised to the sky, left braced, head up
        r = bd(-18, 10, -6, -34); arm1(r, 'R', 172, 10, 8); arm1(r, 'L', 40, 40, 60); return r
    r = bd(48, 0, 0, 14); arm1(r, 'L', 85, 22, 30); arm1(r, 'R', 85, 22, 30); return r   # lavawave: crouched scoop, hands low
def ritual_in(kind):
    KK(0, idle_r())
    r = bd(20, 0, 0, 8); arm1(r, 'L', 30, 25, 60); arm1(r, 'R', 30, 25, 60); KK(0.8, r, jaw=4, root=(0, 0, -0.03))     # anticipation dip
    root = CROUCH if kind == 'lavawave' else (0, 0.01, 0.0)
    KK(2.5, ritual_poses(kind), jaw=24, root=root); HOLD['wb_ritual_'+kind+'_in'] = 2.5; return 1 + int(2.5*FPS)
def ritual_loop(kind):   # 4 s seamless hold: slow tremble + breathing; interruptible any frame
    root = CROUCH if kind == 'lavawave' else (0, 0.01, 0.0)
    for f in range(0, 121, 6):
        t = f/FPS; b = math.sin(2*math.pi*t/4.0); r = ritual_poses(kind)
        r['chest'] = q(X, -2*b) @ q(Y, 0.8*math.sin(2*math.pi*t/2.0)) @ r['chest']
        KK(t, r, jaw=24 + 4*b, root=(root[0], root[1], root[2] + 0.004*b))
    return 121
def ritual_release(kind):
    root = CROUCH if kind == 'lavawave' else (0, 0.01, 0.0)
    KK(0, ritual_poses(kind), jaw=24, root=root)
    if kind == 'fissure':
        r = bd(-20, 0, 0, -28); arm1(r, 'L', 158, 18, 32); arm1(r, 'R', 158, 18, 32); KK(0.5, r, jaw=30, root=(0, 0.03, 0.015))
        CUR[0] = 'wb_ritual_fissure_release'; DEEP = (0, 0.07, -0.24); r = solve(range(40, 126, 5), 'LR', (-0.17*H, -0.30*H, 0.03*H), head=18, out=14, root=DEEP); KK(0.9, r, jaw=36, root=DEEP); t_hit = 0.9
        KK(1.4, r, jaw=24, root=(0, 0.07, -0.25))
    elif kind == 'meteor':
        r = bd(-24, 10, -6, -40); arm1(r, 'R', 178, 6, 5); arm1(r, 'L', 60, 50, 50); KK(0.6, r, jaw=38, root=(0, 0, 0.01)); t_hit = 0.6   # call: the meteors spawn here
        r = bd(30, -10, 4, 12); arm1(r, 'R', 90, 20, 20); arm1(r, 'L', 30, 30, 40); KK(1.4, r, jaw=20, root=(0, 0, -0.04))  # arm swept down at the area
    else:
        r = bd(-10, 0, 0, -18); arm1(r, 'L', 120, 30, 50); arm1(r, 'R', 120, 30, 50); KK(0.9, r, jaw=30, root=(0, 0.02, 0))   # heave up
        r = bd(30, 0, 0, 10); arm1(r, 'L', 70, 60, 15); arm1(r, 'R', 70, 60, 15); KK(1.3, r, jaw=38, root=(0, -0.01, -0.04)); t_hit = 1.3  # fling out: ring spawns
    CONTACT['wb_ritual_'+kind+'_release'] = t_hit
    r = bd(20, 0, 0, 4); arm1(r, 'L', 30, 20, 40); arm1(r, 'R', 30, 20, 40); KK(2.4, r, jaw=8, root=(0, 0, -0.03))
    return KK(3.6, idle_r())
def stagger():   # interrupt reaction: big recoil (0-0.6), stumble back with planted-foot shuffle, sag (to 2.5); then wb_stagger_loop holds the dazed sag
    KK(0, idle_r())
    r = bd(-26, 8, 6, -30); arm1(r, 'L', 60, 60, 60); arm1(r, 'R', 70, 55, 50); key(0.6, root=(0.02, 0.06, 0.0), rot=legs_free(r), ik={'legL': (tuple(FR['L']), 1.0), 'legR': (tuple(FR['R'] + Vector((0, 0.06, 0.0))), 1.0)}, jaw=36)
    r = bd(-10, -6, -8, -20); arm1(r, 'L', 30, 40, 40); arm1(r, 'R', 40, 40, 40); key(1.3, root=(-0.02, 0.10, -0.02), rot=legs_free(r), ik={'legL': (tuple(FR['L'] + Vector((0, 0.10, 0.0))), 1.0), 'legR': (tuple(FR['R'] + Vector((0, 0.12, 0.0))), 1.0)}, jaw=20)
    r = stag_pose(); key(2.5, root=(0, 0.11, -0.06), rot=legs_free(r), ik=STAGF(), jaw=14)
    CONTACT['wb_stagger'] = 0.25; return 1 + int(2.5*FPS)
def stag_pose():
    r = bd(34, 0, 4, 18); arm1(r, 'L', 20, 25, 30); arm1(r, 'R', 25, 25, 30); return r
STAGF = lambda: {'legL': (tuple(FR['L'] + Vector((0, 0.10, 0.0))), 1.0), 'legR': (tuple(FR['R'] + Vector((0, 0.12, 0.0))), 1.0)}
def stagger_loop():
    for f in range(0, 121, 6):
        t = f/FPS; b = math.sin(2*math.pi*t/4.0); r = stag_pose(); r['head'] = q(Z, 8*b) @ r['head']; r['chest'] = q(Y, 3*b) @ r['chest']
        key(t, root=(0.01*b, 0.11, -0.06 + 0.005*math.cos(2*math.pi*t/2)), rot=legs_free(r), ik=STAGF(), jaw=14 + 4*b)
    return 121
def knockdown():   # all weak points broken: drop to both knees and hands (4.0 s), wb_down_loop holds, wb_getup rises
    KK(0, idle_r())
    r = bd(-16, 0, 0, -26); arm1(r, 'L', 60, 50, 60); arm1(r, 'R', 60, 50, 60); key(0.8, root=(0, 0.02, -0.02), rot=legs_free(r), ik=FEET(), jaw=34)
    r = down_pose(); key(2.4, root=DOWNROOT, rot=legs_free(r), ik=DOWNF(), jaw=20); CONTACT['wb_knockdown'] = 2.4
    key(4.0, root=(DOWNROOT[0], DOWNROOT[1], DOWNROOT[2] - 0.01), rot=legs_free(down_pose()), ik=DOWNF(), jaw=12); return 1 + int(4.0*FPS)
DOWNROOT = (0, -0.05, -0.30)
def down_pose():
    r = bd(55, 0, 0, 20); arm1(r, 'L', 70, 18, 10); arm1(r, 'R', 70, 18, 10); return r
DOWNF = lambda: {'legL': (tuple(FR['L'] + Vector((0, 0.32, 0.0))), 1.0), 'legR': (tuple(FR['R'] + Vector((0, 0.32, 0.0))), 1.0)}
def down_loop():
    for f in range(0, 121, 6):
        t = f/FPS; b = math.sin(2*math.pi*t/4.0); r = down_pose(); r['chest'] = q(X, -2*b) @ r['chest']
        key(t, root=(0, DOWNROOT[1], DOWNROOT[2] - 0.01 + 0.006*b), rot=legs_free(r), ik=DOWNF(), jaw=12 + 3*b)
    return 121
def getup():
    key(0, root=(0, DOWNROOT[1], DOWNROOT[2] - 0.01), rot=legs_free(down_pose()), ik=DOWNF(), jaw=12)
    r = bd(40, 0, 6, 10, hips=4); arm1(r, 'L', 60, 25, 20); arm1(r, 'R', 50, 25, 40)
    key(1.6, root=(0.03, -0.02, -0.18), rot=legs_free(r), ik={'legL': (tuple(FR['L'] + Vector((0, 0.32, 0.0))), 1.0), 'legR': (tuple(FR['R']), 1.0)}, jaw=16)
    r = bd(20, 0, 0, 0); arm1(r, 'L', 30, 25, 30); arm1(r, 'R', 30, 25, 30)
    key(3.0, root=(0, 0, -0.08), rot=legs_free(r), ik={'legL': (tuple(FR['L'] + Vector((0, 0.05, 0.0))), 1.0), 'legR': (tuple(FR['R']), 1.0)}, jaw=8)
    return key(4.5, rot=legs_free(idle_r()), ik=FEET(), jaw=2)
def swat_forearm(s):   # brush swat across the front 25 m arc with the attacked forearm: 1.2 s telegraph (raise), hit 1.6, recover 3.4
    sg = 1 if s == 'L' else -1; o = 'R' if s == 'L' else 'L'
    KK(0, idle_r())
    r = bd(6, sg*30, -sg*4, -6); arm1(r, s, 70, 70, 40); arm1(r, o, 20, 20, 30); KK(1.2, r, jaw=14)
    CUR[0] = 'wb_swat_forearm_'+s; r = solve(range(30, 81, 5), s, (-0.08*H, -0.32*H, 0.06*H), tw=-sg*20, sd=sg*4, head=10, out=20, root=CROUCH); KK(1.6, r, jaw=28, root=CROUCH)
    CONTACT['wb_swat_forearm_'+s] = 1.6
    r = bd(26, -sg*35, sg*4, 6); arm1(r, s, 60, -10, 20); KK(2.2, r, jaw=12, root=(0, 0.03, -0.08))
    return KK(3.4, idle_r())
def swat_back():   # shudder that knocks climbers off: 1.2 s telegraph hunch, violent shake 1.2-2.4 (peak 1.5), settle 3.4
    KK(0, idle_r())
    r = bd(30, 0, 0, 16); arm1(r, 'L', 30, 40, 70); arm1(r, 'R', 30, 40, 70); KK(1.2, r, jaw=10, root=(0, 0, -0.04))
    for i, t in enumerate([1.32, 1.44, 1.56, 1.7, 1.86, 2.04, 2.24]):
        a = (1 - i/8)*(1 if i % 2 == 0 else -1); r = bd(30 - 8*abs(a), 10*a, 12*a, 10); arm1(r, 'L', 40, 50 + 15*a, 60); arm1(r, 'R', 40, 50 - 15*a, 60)
        KK(t, r, jaw=24, root=(0.02*a, 0, -0.04 + 0.01*abs(a)))
    CONTACT['wb_swat_back'] = 1.5
    return KK(3.4, idle_r())
for n, f in [('wb_idle', wb_idle), ('wb_walk', wb_walk), ('wb_run', wb_run), ('wb_turn_L', lambda: turn(+1, 'wb_turn_L')), ('wb_turn_R', lambda: turn(-1, 'wb_turn_R')),
             ('wb_stomp', wb_stomp)] + [(f'wb_ritual_{k}_{ph}', (lambda k=k, fn=fn: fn(k))) for k in ('fissure', 'meteor', 'lavawave') for ph, fn in (('in', ritual_in), ('loop', ritual_loop), ('release', ritual_release))] + [
             ('wb_stagger', stagger), ('wb_stagger_loop', stagger_loop), ('wb_knockdown', knockdown), ('wb_down_loop', down_loop), ('wb_getup', getup),
             ('wb_swat_forearm_L', lambda: swat_forearm('L')), ('wb_swat_forearm_R', lambda: swat_forearm('R')), ('wb_swat_knee', wb_stomp), ('wb_swat_back', swat_back), ('grow', grow)]: clip(n, f)
for e in ERR: print('SOLVE', e)
dump = {}; slide = {}
for n, (act, end) in CLIPS.items():
    arm.animation_data.action = act
    for ob in [v[0] for v in IK.values()] + [v[1] for v in IK.values()] + [v[0] for v in FROT.values()]: ob.animation_data.action = EACT[n][ob.name]
    for ob in [arm] + [v[0] for v in IK.values()] + [v[1] for v in IK.values()]:
        if ob.animation_data and ob.animation_data.action:
            for fc in ob.animation_data.action.fcurves:
                for kp in fc.keyframe_points: kp.interpolation = 'BEZIER'
    # IK targets have their own actions (shared across clips) -> per clip: bake via frame dump only
    fr = []; foot = {s_: [] for s_ in 'LR'}
    for f in range(1, end + 1):
        sc.frame_set(f)
        fr.append({pb.name: [list(r_) for r_ in (pb.matrix @ pb.bone.matrix_local.inverted())] for pb in P})
        for s_ in 'LR': foot[s_].append((arm.matrix_world @ P['foot_'+s_].head).copy())
        if n in ('wb_walk','wb_run') and f % 15 == 1: print('DBG', n, f, [round(((arm.matrix_world @ P['foot_'+s_].head) - IK['leg'+s_][0].matrix_world.translation).length/H, 3) for s_ in 'LR'], [round(x/H,3) for x in (arm.matrix_world @ P['foot_L'].head)])
    # foot slide: max horizontal move between consecutive frames while the foot is on the ground (z < rest + 0.01H)
    ms = 0.0
    for s_ in 'LR':
        z0 = IK['leg'+s_][3].z
        for a_, b_ in zip(foot[s_], foot[s_][1:]):
            if a_.z < z0 + 0.002*H and b_.z < z0 + 0.002*H: ms = max(ms, ((a_ - b_).to_2d()).length)
    slide[n] = round(ms*GS, 3)
    print('CLIP', n, 'sec', round((end - 1)/FPS, 3), 'max planted-foot slide per frame (m@1.3362)', slide[n], 'events', EVENTS.get(n), 'hit', CONTACT.get(n))
    dump[n] = fr
json.dump(dump, open(dst + '.dump.json', 'w')); json.dump({'events': EVENTS, 'contact': CONTACT}, open(dst + '.events.json', 'w'))
print('WB done')
