# Mossgut v2 re-rig: fit skeleton to original stonetroll mesh, auto-weight, rebind in A-pose, author lumbering clips, export GLB.
import bpy, sys, math, numpy as np
from mathutils import Vector, Quaternion, Matrix, Euler
src, dst = sys.argv[-2], sys.argv[-1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
for o in list(bpy.data.objects):
    if o.name.startswith('Icosphere'): bpy.data.objects.remove(o)
arm = bpy.data.objects['stonetroll_Rig']; mesh = [o for o in bpy.data.objects if o.type == 'MESH'][0]
for a in list(bpy.data.actions): bpy.data.actions.remove(a)
arm.animation_data_clear()
S = arm.matrix_world.to_scale()[0]; W2A = arm.matrix_world.inverted()
# ---- joint positions in WORLD (Blender) units, fitted to the mesh slices (shoulder where arm leaves torso, elbow/wrist at narrowest arm sections, hand to finger base) ----
J = {'root': (0,0,0), 'hips': (0,0.0,2.95), 'spine': (0,0.05,3.4), 'chest': (0,0.1,3.9), 'neck': (0,-0.2,4.7), 'head': (0,-0.55,5.0), 'head_t': (0,-0.9,5.6),
     'shoulder_L': (0.35,0.1,4.5), 'upperArm_L': (1.2,0.1,4.6), 'foreArm_L': (2.3,0.13,4.55), 'hand_L': (3.45,0.0,4.35), 'hand_t_L': (4.9,0.05,4.0),
     'thigh_L': (0.55,0.0,2.9), 'shin_L': (0.68,-0.1,1.45), 'foot_L': (0.95,0.2,0.5), 'foot_t_L': (1.0,-0.75,0.1), 'cape_t': (0,0.6,3.9)}
for k in list(J):
    if k.endswith('_L'): J[k[:-2]+'_R'] = (-J[k][0],)+tuple(J[k][1:])
A = {k: W2A @ Vector(v) for k, v in J.items()}
child = {'hips':'spine','spine':'chest','chest':'neck','neck':'head','head':'head_t','shoulder':'upperArm','upperArm':'foreArm','foreArm':'hand','hand':'hand_t','thigh':'shin','shin':'foot','foot':'foot_t'}
bpy.context.view_layer.objects.active = arm; bpy.ops.object.mode_set(mode='EDIT'); eb = arm.data.edit_bones
for b in eb:
    n = b.name; side = n[-2:] if n[-2:] in ('_L','_R') else ''; base = n[:-2] if side else n
    if n == 'root': b.head = A['root']; b.tail = A['root'] + Vector((0, 0.3/S, 0)); b.roll = 0; continue
    if n == 'cape': b.head = A['chest']; b.tail = A['cape_t']; b.roll = 0; continue
    if base in child:
        b.use_connect = False; b.head = A[n]; b.tail = A[child[base] + side]; b.roll = 0
for b in eb:   # leg bones bend forward at knee: roll so local X points sideways (IK plane)
    pass
bpy.ops.object.mode_set(mode='OBJECT')
# ---- weights: clear and auto (bone heat) ----
for vg in list(mesh.vertex_groups): mesh.vertex_groups.remove(vg)
for m in list(mesh.modifiers):
    if m.type == 'ARMATURE': mesh.modifiers.remove(m)
mw = mesh.matrix_world.copy(); bpy.ops.object.select_all(action='DESELECT'); mesh.select_set(True); arm.select_set(True); bpy.context.view_layer.objects.active = arm
for b in arm.data.bones: b.use_deform = b.name != 'root'
# bone heat needs a welded mesh: weight a welded proxy, then transfer weights to the real mesh (nearest face interpolated)
proxy = mesh.copy(); proxy.data = mesh.data.copy(); bpy.context.scene.collection.objects.link(proxy)
proxy.parent = None; proxy.data.transform(mw); proxy.matrix_world = Matrix.Identity(4)
import bmesh; bm = bmesh.new(); bm.from_mesh(proxy.data); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.002); bm.to_mesh(proxy.data); bm.free()
bpy.ops.object.select_all(action='DESELECT'); proxy.select_set(True); arm.select_set(True); bpy.context.view_layer.objects.active = arm
bpy.ops.object.parent_set(type='ARMATURE_AUTO')
pv=proxy.data.vertices; pn0={g.index:g.name for g in proxy.vertex_groups}
for lo,hi in [(0.8,1.2),(1.6,2.0),(2.4,2.8)]:
    acc={};n=0
    for v in pv:
        w=proxy.matrix_world@v.co
        if lo<w.z<hi and w.x>0.3 and w.x<1.6:
            n+=1
            for g in v.groups: acc[pn0[g.group]]=acc.get(pn0[g.group],0)+g.weight
    print('RERIG proxyw',lo,n,sorted(((round(b/n,2),a) for a,b in acc.items()),reverse=True)[:4])
pz = sum(1 for v in proxy.data.vertices if sum(g.weight for g in v.groups) < 1e-3); print('RERIG proxy zero', pz, len(proxy.data.vertices))
bpy.ops.object.select_all(action='DESELECT'); mesh.select_set(True); arm.select_set(True); bpy.context.view_layer.objects.active = arm
bpy.ops.object.parent_set(type='ARMATURE_NAME')
mesh.matrix_world = mw
from mathutils import kdtree
pw = proxy.matrix_world; kd = kdtree.KDTree(len(proxy.data.vertices))
for v in proxy.data.vertices: kd.insert(pw @ v.co, v.index)
kd.balance(); pn = {g.index: g.name for g in proxy.vertex_groups}; MG = {g.name: g for g in mesh.vertex_groups}
for v in mesh.data.vertices:
    co, i, d = kd.find(mw @ v.co)  # proxy verts are world coords
    for g in proxy.data.vertices[i].groups:
        if g.weight > 1e-4: MG[pn[g.group]].add([v.index], g.weight, 'REPLACE')
bpy.context.view_layer.objects.active = mesh; bpy.ops.object.select_all(action='DESELECT'); mesh.select_set(True)
for v in mesh.data.vertices:   # any vertex the proxy left unweighted: take the weights of its nearest weighted neighbour
    if sum(g.weight for g in v.groups) < 1e-3:
        for co, i, d in kd.find_n(mw @ v.co, 12):
            gs = [g for g in proxy.data.vertices[i].groups if g.weight > 1e-4]
            if gs:
                for g in gs: MG[pn[g.group]].add([v.index], g.weight, 'REPLACE')
                break
bpy.data.objects.remove(proxy)
bpy.ops.object.vertex_group_normalize_all(lock_active=False)
zero = sum(1 for v in mesh.data.vertices if sum(g.weight for g in v.groups) < 1e-3)
print('RERIG zero-weight verts', zero, 'of', len(mesh.data.vertices))
# ---- rebind in A-pose: lower upper arms 45deg, apply to mesh, make it the new rest ----
def setL(pb, L):  # L = rotation in the bone's (posed-parent) armature-aligned axes
    r = pb.bone.matrix_local.to_quaternion(); pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = r.inverted() @ L @ r
P = arm.pose.bones
APOSE = 45
setL(P['upperArm_L'], Quaternion((0,1,0), math.radians(APOSE))); setL(P['upperArm_R'], Quaternion((0,1,0), math.radians(-APOSE)))
setL(P['shoulder_L'], Quaternion((0,1,0), math.radians(6))); setL(P['shoulder_R'], Quaternion((0,1,0), math.radians(-6)))
bpy.context.view_layer.update()
bpy.context.view_layer.objects.active = mesh; bpy.ops.object.select_all(action='DESELECT'); mesh.select_set(True)
md = [m for m in mesh.modifiers if m.type == 'ARMATURE'][0]; nm = md.name
bpy.ops.object.modifier_copy(modifier=nm); bpy.ops.object.modifier_apply(modifier=nm)   # bake A-pose into mesh, keep a fresh armature modifier
bpy.context.view_layer.objects.active = arm; bpy.ops.object.mode_set(mode='POSE'); bpy.ops.pose.select_all(action='SELECT'); bpy.ops.pose.armature_apply(selected=False); bpy.ops.object.mode_set(mode='OBJECT')
for pb in P: pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = (1,0,0,0); pb.location = (0,0,0)
# ---- IK legs ----
def empty(n, loc):
    e = bpy.data.objects.new(n, None); bpy.context.scene.collection.objects.link(e); e.location = loc; return e
IKT, POLE, FR = {}, {}, {}
for s in 'LR':
    ank = arm.matrix_world @ arm.data.bones['foot_'+s].head_local; kn = arm.matrix_world @ arm.data.bones['shin_'+s].head_local
    IKT[s] = empty('ik_'+s, ank); POLE[s] = empty('pole_'+s, kn + Vector((0,-3,0))); FR[s] = empty('frot_'+s, ank)
    FR[s].rotation_mode = 'QUATERNION'
    c = P['shin_'+s].constraints.new('IK'); c.target = IKT[s]; c.pole_target = POLE[s]; c.chain_count = 2; c.pole_angle = math.radians(-90)
    c2 = P['foot_'+s].constraints.new('COPY_ROTATION'); c2.target = FR[s]; c2.target_space = 'WORLD'; c2.owner_space = 'WORLD'
bpy.context.view_layer.update()
REST_ANK = {s: IKT[s].location.copy() for s in 'LR'}
FQ = {s: arm.matrix_world.to_quaternion() @ arm.data.bones['foot_'+s].matrix_local.to_quaternion() for s in 'LR'}
sc = bpy.context.scene; FPS = 30; sc.render.fps = FPS
D = math.radians
def q(ax, deg): return Quaternion(ax, D(deg))
X, Y, Z = (1,0,0), (0,1,0), (0,0,1)
def pose(f, d):
    """d: bone -> L quaternion (armature axes); 'hipsLoc' world offset; feet: ('L', loc offset, pitch)"""
    for bn, L in d.get('rot', {}).items():
        pb = P[bn]; setL(pb, L); pb.keyframe_insert('rotation_quaternion', frame=f)
    hl = Vector(d.get('hipsLoc', (0,0,0)))/S; r = P['hips'].bone.matrix_local.to_quaternion()
    P['hips'].location = r.inverted() @ hl; P['hips'].keyframe_insert('location', frame=f)
    for s in 'LR':
        off, pitch = d.get('foot'+s, ((0,0,0), 0))
        IKT[s].location = REST_ANK[s] + Vector(off); IKT[s].keyframe_insert('location', frame=f)
        FR[s].location = IKT[s].location; FR[s].rotation_quaternion = Quaternion((1,0,0), D(pitch)) @ FQ[s]; FR[s].keyframe_insert('location', frame=f); FR[s].keyframe_insert('rotation_quaternion', frame=f)
        POLE[s].location = REST_ANK[s] + Vector(off) + Vector((0, -3, 1.0)); POLE[s].keyframe_insert('location', frame=f)
ALLB = [pb.name for pb in P]
def arms(sw, side_out=0, elbow=18, hang=33, twist=0, lag=0):
    """sw: forward swing deg (+ forward) per side dict; returns rot dict for the arms (hanging, palms in)"""
    r = {}
    for s, sg in (('L',1),('R',-1)):
        a = sw.get(s, 0)
        r['shoulder_'+s] = q(X, -a*0.15)
        r['upperArm_'+s] = q(X, -a) @ q(Y, sg*(hang - side_out.get(s,0) if isinstance(side_out, dict) else hang - side_out))
        e = elbow + max(0, a)*0.35 + (lag.get(s,0) if isinstance(lag, dict) else 0)
        r['foreArm_'+s] = q(X, -e)
        r['hand_'+s] = q(X, -8) @ q(Z, sg*twist)
    return r
def loco(T, v, duty, lift, bob, lean, swing, sway, yaw, elbow, name, stride_scale=1.0):
    n = int(round(T*FPS)); A_ = v*T*duty/2*stride_scale
    for i in range(n+1):
        p = i/n; f = i+1; d = {'rot': {}}
        for s, ph in (('L', 0.0), ('R', 0.5)):
            u = (p + ph) % 1.0
            if u < duty: y = -A_ + 2*A_*u/duty; z = 0; pitch = 0          # stance: foot moves back at exactly v (no slide)
            else:
                w = (u-duty)/(1-duty); y = A_ - 2*A_*(0.5-0.5*math.cos(math.pi*w)); z = lift*math.sin(math.pi*w); pitch = -25*math.sin(math.pi*min(1,w*1.6)) if w < .62 else 12*math.sin(math.pi*(w-.62)/.38)
            d['foot'+s] = ((0, y, z), pitch)
        c = math.cos(2*math.pi*p); s2 = math.sin(2*math.pi*p)
        # left foot forward at p=0 (stance start, y=-A). Heavy: lowest just after heel strike.
        d['hipsLoc'] = (sway*math.cos(2*math.pi*p + math.pi/2*0)*-1, 0, -bob*(0.5+0.5*math.cos(4*math.pi*(p-0.08))))
        d['rot']['hips'] = q(Z, yaw*c) @ q(Y, -sway*12*c) @ q(X, lean*0.4)
        d['rot']['spine'] = q(Z, -yaw*0.6*c) @ q(X, lean*0.3)
        d['rot']['chest'] = q(Z, -yaw*0.6*c) @ q(X, lean*0.3 + 2*math.cos(4*math.pi*p)) @ q(Y, sway*8*c)
        d['rot']['neck'] = q(X, -lean*0.5) @ q(Z, yaw*0.4*c)
        d['rot']['head'] = q(X, -lean*0.3 - 3*math.cos(4*math.pi*(p-0.1)))
        # arms opposite legs: right arm forward when left leg forward (p=0); lag the forearm
        lagc = math.cos(2*math.pi*(p-0.08))
        d['rot'].update(arms({'L': -swing*lagc, 'R': swing*lagc}, side_out=4, elbow=elbow, lag={'L': 6*max(0,-lagc), 'R': 6*max(0,lagc)}))
        d['rot']['cape'] = q(X, -4 - 4*math.cos(4*math.pi*p))
        pose(f, d)
    return n+1
def keyseq(keys, name):
    """keys: list of (time_s, dict) -> poses at those times, Bezier in between"""
    last = 1
    for t, d in keys: f = 1 + round(t*FPS); pose(f, d); last = f
    return last
def base(lean=8, **kw):
    d = {'rot': {'hips': q(X, lean*0.4), 'spine': q(X, lean*0.3), 'chest': q(X, lean*0.3), 'neck': q(X, -lean*0.5), 'head': q(X, -lean*0.3), 'cape': q(X, -4)}}
    d['rot'].update(arms({}, elbow=18)); d.update(kw); return d
def mix(d, **rot):
    d = {**d, 'rot': {**d['rot'], **rot}}; return d
CLIPS = {}
def clip(name, builder):
    act = bpy.data.actions.new(name+'_src')
    for ob in [arm] + list(IKT.values()) + list(POLE.values()) + list(FR.values()):
        ob.animation_data_create(); ob.animation_data.action = None
    # each object gets its own action named per clip
    for ob in [arm] + list(IKT.values()) + list(POLE.values()) + list(FR.values()):
        ob.animation_data.action = bpy.data.actions.new(name + '__' + ob.name)
    end = builder()
    sc.frame_start, sc.frame_end = 1, end
    bpy.ops.object.select_all(action='DESELECT'); arm.select_set(True); bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='POSE'); bpy.ops.pose.select_all(action='SELECT')
    bpy.ops.nla.bake(frame_start=1, frame_end=end, only_selected=True, visual_keying=True, clear_constraints=False, use_current_action=False, bake_types={'POSE'})
    bpy.ops.object.mode_set(mode='OBJECT')
    baked = arm.animation_data.action; baked.name = name; baked.use_fake_user = True
    CLIPS[name] = (end-1)/FPS
    bpy.data.actions.remove(act)
# Speeds in WORLD units/s (rig scale S): game metres = /S
WALK_V, RUN_V = 0.95*S, 2.5*S
clip('walk', lambda: loco(T=1.35, v=WALK_V, duty=0.64, lift=0.35, bob=0.10, lean=12, swing=22, sway=0.10, yaw=7, elbow=20, name='walk'))
clip('run',  lambda: loco(T=0.82, v=RUN_V, duty=0.42, lift=0.65, bob=0.22, lean=22, swing=38, sway=0.12, yaw=10, elbow=45, name='run'))
def idle():
    n = int(2.6*FPS)
    for i in range(n+1):
        p = i/n; b = math.sin(2*math.pi*p); d = base(lean=9+2*b, hipsLoc=(0,0,-0.04-0.03*b))
        d['rot'].update(arms({'L': 3*math.sin(2*math.pi*(p-.1)), 'R': 3*math.sin(2*math.pi*(p-.15))}, elbow=20+3*b, hang=33-2*b))
        d['rot']['chest'] = q(X, 3 - 3*b); d['rot']['head'] = q(X, -2 + 2*b) @ q(Z, 4*math.sin(2*math.pi*p*1+1))
        d['footL'] = ((0,0,0),0); d['footR'] = ((0,0,0),0); pose(i+1, d)
    return n+1
clip('idle', idle)
B0 = lambda: base(lean=10, hipsLoc=(0,0,-0.08))
def atk1():   # two-handed overhead slam
    up = mix(base(lean=-8, hipsLoc=(0,0.05,0.04)), **arms({'L': 165, 'R': 165}, elbow=35, hang=25))
    up['rot']['chest'] = q(X, -12); up['rot']['spine'] = q(X, -8); up['rot']['head'] = q(X, 8)
    slam = mix(base(lean=34, hipsLoc=(0,-0.15,-0.45)), **arms({'L': 75, 'R': 75}, elbow=12, hang=12))
    slam['rot']['chest'] = q(X, 18); slam['rot']['head'] = q(X, -16)
    st = {'footL': ((0,-0.35,0),0), 'footR': ((0,0.1,0),0)}
    return keyseq([(0, B0()), (0.42, {**up, **st}), (0.62, {**slam, **st}), (0.78, {**slam, **st}), (1.35, B0())], 'attack1')
def side_swing(s, back):   # one-arm haymaker carried by the torso: shoulder out, elbow off the body, hand arcs in front at chest height
    sg = 1 if s == 'L' else -1; o = 'R' if s == 'L' else 'L'
    # wind-up: torso twists the striking shoulder back, arm raised out to the side and back, elbow bent
    w = mix(base(lean=4, hipsLoc=(0, 0, -0.10)), **arms({s: -10, o: 10}, elbow=30, hang=30))
    w['rot']['hips'] = q(Z, sg*18); w['rot']['spine'] = q(Z, sg*12); w['rot']['chest'] = q(Z, sg*16) @ q(X, 4)
    w['rot']['shoulder_'+s] = q(Z, sg*6) @ q(Y, -sg*10); w['rot']['upperArm_'+s] = q(Z, sg*35) @ q(Y, -sg*40); w['rot']['foreArm_'+s] = q(Z, -sg*45)
    # strike: torso unwinds hard, arm stays abducted ~horizontal and sweeps forward (never across the belly)
    h = mix(base(lean=14, hipsLoc=(0, -0.12, -0.22)), **arms({s: 0, o: 15}, elbow=20, hang=33))
    h['rot']['hips'] = q(Z, -sg*20); h['rot']['spine'] = q(Z, -sg*16); h['rot']['chest'] = q(Z, -sg*22) @ q(X, 6)
    h['rot']['shoulder_'+s] = q(Z, -sg*10) @ q(Y, -sg*10); h['rot']['upperArm_'+s] = q(Z, -sg*62) @ q(Y, -sg*38); h['rot']['foreArm_'+s] = q(Z, -sg*20)
    f = mix(h); f['rot'] = dict(h['rot']); f['rot']['upperArm_'+s] = q(Z, -sg*72) @ q(Y, -sg*30); f['rot']['chest'] = q(Z, -sg*26) @ q(X, 8)
    st = {'foot'+o: ((0, -0.3, 0), 0), 'foot'+s: ((0, 0.2, 0), 0)}
    return w, h, f, st
def atk2():   # right haymaker
    w, h, f, st = side_swing('R', 0)
    return keyseq([(0, B0()), (0.38, {**w, **st}), (0.56, {**h, **st}), (0.70, {**f, **st}), (1.15, B0())], 'attack2')
def atk3():   # left haymaker (mirror)
    w, h, f, st = side_swing('L', 0)
    return keyseq([(0, B0()), (0.40, {**w, **st}), (0.58, {**h, **st}), (0.72, {**f, **st}), (1.2, B0())], 'attack3')
def skill():  # roar: chest up, arms out
    r = mix(base(lean=-10, hipsLoc=(0,0.05,0.05)), **arms({'L': 20, 'R': 20}, elbow=35, hang=-5))
    r['rot']['chest'] = q(X, -15); r['rot']['head'] = q(X, 20)
    return keyseq([(0, B0()), (0.5, r), (1.2, r), (1.7, B0())], 'skill')
def hit():
    h = mix(base(lean=-6, hipsLoc=(0,0.15,-0.05)), **arms({'L': -15, 'R': -12}, elbow=30, hang=26)); h['rot']['head'] = q(X, 18)
    return keyseq([(0, B0()), (0.12, h), (0.55, B0())], 'hit')
def death():
    k = mix(base(lean=40, hipsLoc=(0,-0.2,-1.2)), **arms({'L': 30, 'R': 25}, elbow=40, hang=30)); k['footL'] = ((0,0,0),0); k['footR'] = ((0,0,0),0)
    k2 = mix(base(lean=75, hipsLoc=(0,-0.6,-1.7)), **arms({'L': 70, 'R': 65}, elbow=10, hang=20)); k2['rot']['head'] = q(X, -10)
    return keyseq([(0, B0()), (0.6, k), (1.4, k2), (2.0, k2)], 'death')
for nm, fn in [('attack1', atk1), ('attack2', atk2), ('attack3', atk3), ('skill', skill), ('hit', hit), ('death', death)]: clip(nm, fn)
# ---- strip helpers, export ----
for pb in P:
    for c in list(pb.constraints): pb.constraints.remove(c)
    pb.rotation_quaternion = (1,0,0,0); pb.location = (0,0,0)
for e in list(IKT.values()) + list(POLE.values()) + list(FR.values()): bpy.data.objects.remove(e)
for a in list(bpy.data.actions):
    if '__' in a.name: bpy.data.actions.remove(a)

# ---- every-frame check: forearm/hand points inside the torso (hips/spine/chest/neck-weighted part of the mesh) ----
import bmesh
from mathutils.bvhtree import BVHTree
GN = {g.index: g.name for g in mesh.vertex_groups}; TORSO = {'hips','spine','chest'}
tv = [v.index for v in mesh.data.vertices if v.groups and GN[max(v.groups, key=lambda g: g.weight).group] in TORSO and abs((mesh.matrix_world @ v.co).x) < 1.4 and (mesh.matrix_world @ v.co).z > 2.6]
print('RERIG torso verts', len(tv))
tvs = set(tv); tf = [p.index for p in mesh.data.polygons if all(i in tvs for i in p.vertices)]
REP = {}
for nm in ['attack1','attack2','attack3','skill','idle','walk','run']:
    arm.animation_data.action = bpy.data.actions[nm]; n = int(round(CLIPS[nm]*FPS)); worst = (0, None)
    for f in range(1, n+2):
        sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get(); me = mesh.evaluated_get(dg); md = me.to_mesh()
        mwv = mesh.matrix_world; verts = [mwv @ md.vertices[i].co for i in range(len(md.vertices))]
        bmh = bmesh.new()
        for i in tv: bmh.verts.new(verts[i])
        bmesh.ops.convex_hull(bmh, input=bmh.verts[:]); bmh.normal_update(); me.to_mesh_clear()
        cen = sum((v.co for v in bmh.verts), Vector()) / len(bmh.verts)
        PL = []
        for fc in bmh.faces:
            c0 = fc.calc_center_median(); nn = fc.normal.copy()
            if (c0 - cen).dot(nn) < 0: nn = -nn
            PL.append((c0, nn))
        bmh.free()
        for s_ in 'LR':
            for b0, b1 in (('foreArm_'+s_, 'hand_'+s_), ('hand_'+s_, None)):
                pb = P[b0]; h0 = arm.matrix_world @ pb.head; h1 = arm.matrix_world @ (P[b1].head if b1 else pb.tail + (pb.tail-pb.head)*0.6)
                for k in range(6):
                    pt = h0.lerp(h1, k/5); dep = min(-(pt - c0).dot(nn) for c0, nn in PL)
                    if dep > worst[0]: worst = (dep, f'{b0} f{f}')
    REP[nm] = (round(worst[0]/S, 3), worst[1])
arm.animation_data.action = None; sc.frame_set(1)
print('RERIG penetration (m, inside torso):', REP)

print('RERIG clips', {k: round(v,2) for k, v in CLIPS.items()}, 'walk m/s', round(WALK_V/S,2), 'run m/s', round(RUN_V/S,2))
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=dst, export_format='GLB', export_animation_mode='ACTIONS', export_force_sampling=True, export_frame_step=1, export_yup=True, export_skins=True, export_def_bones=False, export_optimize_animation_size=False)
