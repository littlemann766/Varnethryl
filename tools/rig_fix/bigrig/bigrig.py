# Big-creature re-rig + attack authoring (Mossgut pipeline, generalised).
# usage: blender -b --python bigrig.py -- in.glb out.glb STYLE [--scale K] [--lower DEG] [--weapon w.glb] [--keep-loco 0/1]
import bpy, sys, math, json, bmesh
from mathutils import Vector, Quaternion, Matrix, kdtree
A = sys.argv[sys.argv.index('--')+1:]; src, dst, STYLE = A[0], A[1], A[2]
opt = lambda k, d=None: A[A.index(k)+1] if k in A else d
SCALE = float(opt('--scale', 1)); LOWER = float(opt('--lower', 0)); WEAPON = opt('--weapon'); 
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=src, bone_heuristic='TEMPERANCE')
BUILD = opt('--build')
if BUILD:   # clean mesh without rig: build a fitted skeleton from a joint table (Blender world coords, model faces -Y)
    J = {k: Vector(v) for k, v in json.load(open(BUILD)).items()}
    for k in list(J):
        if k.endswith('_L'): J[k[:-2]+'_R'] = Vector((-J[k].x, J[k].y, J[k].z))
    ad = bpy.data.armatures.new('troll_Rig'); ao = bpy.data.objects.new('troll_Rig', ad); bpy.context.scene.collection.objects.link(ao)
    bpy.context.view_layer.objects.active = ao; bpy.ops.object.mode_set(mode='EDIT'); E = ad.edit_bones
    CH = [('root',None,'root','root_t'),('hips','root','hips','spine'),('spine','hips','spine','chest'),('chest','spine','chest','neck'),('neck','chest','neck','head'),('head','neck','head','head_t'),('jaw','head','jaw','jaw_t')]
    for s in 'LR':
        CH += [('shoulder_'+s,'chest','shoulder_'+s,'upperArm_'+s),('upperArm_'+s,'shoulder_'+s,'upperArm_'+s,'foreArm_'+s),('foreArm_'+s,'upperArm_'+s,'foreArm_'+s,'hand_'+s),('hand_'+s,'foreArm_'+s,'hand_'+s,'fingers_'+s),('fingers_'+s,'hand_'+s,'fingers_'+s,'fingers_t_'+s),
               ('thigh_'+s,'hips','thigh_'+s,'shin_'+s),('shin_'+s,'thigh_'+s,'shin_'+s,'foot_'+s),('foot_'+s,'shin_'+s,'foot_'+s,'toe_'+s),('toe_'+s,'foot_'+s,'toe_'+s,'toe_t_'+s)]
    J.setdefault('root', Vector((0,0,0))); J.setdefault('root_t', Vector((0,0.3,0)))
    for n, p, h, t in CH:
        e = E.new(n); e.head = J[h]; e.tail = J[t]; e.roll = 0
        if p: e.parent = E[p]
    bpy.ops.object.mode_set(mode='OBJECT')
    m0 = [o for o in bpy.data.objects if o.type == 'MESH'][0]
    m0.parent = ao; m0.vertex_groups.new(name='hips'); m0.modifiers.new('Armature','ARMATURE').object = ao
for o in list(bpy.data.objects):
    if o.name.startswith('Icosphere'): bpy.data.objects.remove(o)
arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]; P = arm.pose.bones
mesh = max([o for o in bpy.data.objects if o.type == 'MESH' and o.vertex_groups], key=lambda o: len(o.data.vertices))
for a in bpy.data.actions:
    a.name = a.name.replace('_' + arm.name, ''); a.use_fake_user = True
arm.animation_data_create(); arm.animation_data.action = None
for pb in P: pb.rotation_mode = 'QUATERNION'; pb.matrix_basis.identity()
if SCALE != 1: arm.scale = arm.scale * SCALE; bpy.context.view_layer.update()
S = arm.matrix_world.to_scale()[0]
H = (arm.matrix_world @ arm.data.bones['head'].head_local).z / 0.88
sc = bpy.context.scene; FPS = 30; sc.render.fps = FPS
# ---- 1. clean weights: bone heat on a welded world-space proxy, copied back by nearest vertex ----
mw = mesh.matrix_world.copy()
proxy = mesh.copy(); proxy.data = mesh.data.copy(); sc.collection.objects.link(proxy)
proxy.parent = None; proxy.modifiers.clear(); proxy.data.transform(mw); proxy.matrix_world = Matrix.Identity(4)
for vg in list(proxy.vertex_groups): proxy.vertex_groups.remove(vg)
rm = proxy.modifiers.new('rm', 'REMESH'); rm.mode = 'VOXEL'; rm.voxel_size = 0.04 if BUILD else H/160; rm.use_smooth_shade = True
bpy.context.view_layer.objects.active = proxy; bpy.ops.object.select_all(action='DESELECT'); proxy.select_set(True); bpy.ops.object.modifier_apply(modifier='rm')
bm = bmesh.new(); bm.from_mesh(proxy.data); bm.verts.ensure_lookup_table(); lab = {}; isl = []
for v in bm.verts:
    if v.index in lab: continue
    st = [v]; lab[v.index] = len(isl); c = [v]
    while st:
        x = st.pop()
        for e in x.link_edges:
            y = e.other_vert(x)
            if y.index not in lab: lab[y.index] = len(isl); st.append(y); c.append(y)
    isl.append(c)
isl.sort(key=len, reverse=True); bmesh.ops.delete(bm, geom=[v for i in isl[1:] for v in i], context='VERTS'); bm.to_mesh(proxy.data); bm.free()
print('BIGRIG proxy verts', len(proxy.data.vertices), 'islands dropped', len(isl)-1)
DEF0 = {b.name: b.use_deform for b in arm.data.bones}
for b in arm.data.bones: b.use_deform = DEF0[b.name] and b.name not in ('root',) and not b.name.startswith('eye')
bpy.ops.object.select_all(action='DESELECT'); proxy.select_set(True); arm.select_set(True); bpy.context.view_layer.objects.active = arm
bpy.ops.object.parent_set(type='ARMATURE_AUTO')
if sum(1 for v in proxy.data.vertices if v.groups) == 0:   # heat failed: fall back to envelope-free nearest-bone-segment weights
    import numpy as np
    bones = [b for b in arm.data.bones if b.use_deform]
    segs = [(arm.matrix_world @ b.head_local, arm.matrix_world @ b.tail_local) for b in bones]
    PV = np.array([v.co for v in proxy.data.vertices]); A0 = np.array([s[0] for s in segs]); B0 = np.array([s[1] for s in segs])
    AB = B0 - A0; L2 = np.maximum((AB*AB).sum(1), 1e-9)
    t = np.clip(((PV[:, None, :] - A0[None]) * AB[None]).sum(2) / L2[None], 0, 1)
    d = np.linalg.norm(PV[:, None, :] - (A0[None] + t[..., None]*AB[None]), axis=2)
    sig = H*0.02; w = np.exp(-((d - d.min(1, keepdims=True))/sig)**2); w[d - d.min(1, keepdims=True) > 3*sig] = 0
    top = np.argsort(-w, 1)[:, :4]
    for vg in list(proxy.vertex_groups): proxy.vertex_groups.remove(vg)
    G = {b.name: proxy.vertex_groups.new(name=b.name) for b in bones}
    for i in range(len(PV)):
        ww = w[i, top[i]]; ww = ww/ww.sum()
        for k, j in enumerate(top[i]):
            if ww[k] > 0.01: G[bones[j].name].add([i], float(ww[k]), 'REPLACE')
    print('BIGRIG heat failed -> distance weights')
print('BIGRIG proxy groups', len(proxy.vertex_groups), sum(1 for v in proxy.data.vertices if v.groups), [b.name for b in arm.data.bones if b.use_deform][:5], len([b for b in arm.data.bones if b.use_deform]))
kd = kdtree.KDTree(len(proxy.data.vertices))
for v in proxy.data.vertices: kd.insert(v.co, v.index)
kd.balance(); pn = {g.index: g.name for g in proxy.vertex_groups}
for vg in list(mesh.vertex_groups): mesh.vertex_groups.remove(vg)
MG = {n: mesh.vertex_groups.new(name=n) for n in pn.values()}
zero = 0
for v in mesh.data.vertices:
    for co, i, d in kd.find_n(mw @ v.co, 8):
        gs = [g for g in proxy.data.vertices[i].groups if g.weight > 1e-4]
        if gs:
            for g in gs: MG[pn[g.group]].add([v.index], g.weight, 'REPLACE')
            break
    else: zero += 1
bpy.data.objects.remove(proxy)
bpy.context.view_layer.objects.active = mesh; bpy.ops.object.select_all(action='DESELECT'); mesh.select_set(True)
bpy.ops.object.vertex_group_limit_total(limit=4); bpy.ops.object.vertex_group_normalize_all(lock_active=False)
print('BIGRIG reweighted', len(mesh.data.vertices), 'unweighted', zero)
D = math.radians; X, Y, Z = (1,0,0), (0,1,0), (0,0,1)
def q(ax, d): return Quaternion(ax, D(d))
def setL(pb, L): r = pb.bone.matrix_local.to_quaternion(); pb.rotation_quaternion = r.inverted() @ L @ r
# ---- 2. optional A-pose rebind (arms lowered LOWER deg); invalidates the old clips ----
if LOWER:
    setL(P['upperArm_L'], q(Y, LOWER)); setL(P['upperArm_R'], q(Y, -LOWER)); bpy.context.view_layer.update()
    md = [m for m in mesh.modifiers if m.type == 'ARMATURE'][0]
    bpy.context.view_layer.objects.active = mesh; bpy.ops.object.select_all(action='DESELECT'); mesh.select_set(True)
    bpy.ops.object.modifier_copy(modifier=md.name); bpy.ops.object.modifier_apply(modifier=md.name)
    bpy.context.view_layer.objects.active = arm; bpy.ops.object.mode_set(mode='POSE'); bpy.ops.pose.select_all(action='SELECT'); bpy.ops.pose.armature_apply(selected=False); bpy.ops.object.mode_set(mode='OBJECT')
    for pb in P: pb.matrix_basis.identity()
    for a in list(bpy.data.actions): bpy.data.actions.remove(a)
    print('BIGRIG rebind arms lowered', LOWER)
# ---- 3. weapon socket in the right hand (+Z of socket = weapon +Y glTF = shaft toward the head) ----
SOCK = None
if WEAPON or STYLE.startswith('troll'):
    hb = arm.data.bones['hand_R']; fb = arm.data.bones.get('fingers_R')
    h0 = arm.matrix_world @ hb.head_local; f0 = arm.matrix_world @ (fb.head_local if fb else hb.tail_local)
    fore = (h0 - arm.matrix_world @ arm.data.bones['foreArm_R'].head_local).normalized()
    grip = h0.lerp(f0, 0.75)
    shaft = Vector([float(x) for x in opt('--shaft', '0,-1,-0.35').split(',')]); shaft = (shaft - shaft.dot(fore)*fore).normalized()
    xa = fore.cross(shaft).normalized(); ya = shaft.cross(xa)
    SOCK = [o for o in bpy.data.objects if o.name == 'weapon_R']
    SOCK = SOCK[0] if SOCK else bpy.data.objects.new('weapon_R', None)
    if SOCK.name not in sc.collection.objects and not SOCK.users_collection: sc.collection.objects.link(SOCK)
    SOCK.parent = arm; SOCK.parent_type = 'BONE'; SOCK.parent_bone = 'hand_R'
    SOCK.matrix_world = Matrix.Translation(grip) @ Matrix((xa, ya, shaft)).transposed().to_4x4()
    if WEAPON:
        before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=WEAPON)
        for o in set(bpy.data.objects) - before:
            if o.parent is None or o.parent not in (set(bpy.data.objects) - before):
                o.parent = SOCK; o.matrix_parent_inverse = Matrix.Identity(4); o.location = (0,0,0); o.rotation_mode = 'QUATERNION'; o.rotation_quaternion = (1,0,0,0); o.scale = (1,1,1)
        WLEN = max((v.co.z for o in set(bpy.data.objects)-before if o.type == 'MESH' for v in o.data.vertices), default=3.0)
    else: WLEN = 3.4
    bpy.context.view_layer.update()
has = lambda n: n in P
W = lambda bn: arm.matrix_world @ arm.data.bones[bn].head_local
SP = [b for b in ['spine','spine2','chest','upperChest'] if has(b)]
def empty(n, loc):
    e = bpy.data.objects.new(n, None); bpy.context.scene.collection.objects.link(e); e.location = loc; return e
IK = {}
for s in 'LR':
    for limb, tip, mid in (('leg', 'foot_'+s, 'shin_'+s), ('arm', 'hand_'+s, 'foreArm_'+s)):
        t = empty(f'ik_{limb}_{s}', W(tip)); p = empty(f'pole_{limb}_{s}', W(mid))
        c = P[mid].constraints.new('IK'); c.target = t; c.pole_target = p; c.chain_count = 2; c.pole_angle = D(-90)
        IK[limb+s] = (t, p, c, W(tip).copy(), W(mid).copy())
FPS = 30; sc = bpy.context.scene; sc.render.fps = FPS
FK = ['hips'] + SP + ['neck','head'] + [f'{b}_{s}' for s in 'LR' for b in ('shoulder','upperArm','foreArm','hand','thigh','shin','foot')] + (['jaw'] if has('jaw') else [])
def key(t, hips=(0,0,0), rot=None, ik=None, jaw=0):
    f = 1 + round(t*FPS); rot = rot or {}
    off = Vector(hips)*H; hb = P['hips']; hq = hb.bone.matrix_local.to_quaternion()
    hb.location = hq.inverted() @ (off / S); hb.keyframe_insert('location', frame=f)
    for bn in FK:
        L = q(X, jaw) if bn == 'jaw' else rot.get(bn, Quaternion())
        setL(P[bn], L); P[bn].keyframe_insert('rotation_quaternion', frame=f)
    for name, (tg, pole, c, rt, rm) in IK.items():
        pos, infl = (ik or {}).get(name, (None, 0.0))
        if name.startswith('leg') and pos is None: pos, infl = (tuple(rt/H), 1.0)     # feet stay planted by default
        tg.location = Vector(pos)*H if pos is not None else rt + off
        pole.location = rm + off + (Vector((0,-1,0.2)) if name.startswith('leg') else Vector((0.8 if name[-1]=='L' else -0.8, 1.0, -0.2)))*H*0.35
        c.influence = infl
        tg.keyframe_insert('location', frame=f); pole.keyframe_insert('location', frame=f); c.keyframe_insert('influence', frame=f)
    return f
def body(lean=0, twist=0, side=0, head=0, knees=0):
    r = {'hips': q(Z, twist*0.35) @ q(X, lean*0.25)}
    for b in SP: r[b] = q(Z, twist*0.65/len(SP)) @ q(X, lean*0.75/len(SP)) @ q(Y, side/len(SP))
    r['neck'] = q(X, -lean*0.3 + head*0.5); r['head'] = q(X, -lean*0.2 + head*0.5) @ q(Z, -twist*0.3)
    return r
def armfk(r, s, fwd=0, out=0, elbow=10, yaw=0):
    sg = 1 if s == 'L' else -1
    r['upperArm_'+s] = q(Z, sg*yaw) @ q(X, -fwd) @ q(Y, -sg*out); r['foreArm_'+s] = q(X, -elbow); r['shoulder_'+s] = q(X, -fwd*0.1) @ q(Y, -sg*out*0.15)
    return r
def foot(s, dy=0, dz=0):   # planted foot target offset (fractions of H)
    t = IK['leg'+s][3]/H; return ((t.x, t.y+dy, t.z+dz), 1.0)
CLIPS = {}; CONTACT = {}
def clip(name, builder):
    for ob in [arm] + [v[0] for v in IK.values()] + [v[1] for v in IK.values()]:
        ob.animation_data_create(); ob.animation_data.action = bpy.data.actions.new(name + '__' + ob.name)
    end = builder()
    for ob in [arm] + [v[0] for v in IK.values()] + [v[1] for v in IK.values()]:
        for fc in ob.animation_data.action.fcurves:
            for kp in fc.keyframe_points: kp.interpolation = 'BEZIER'
    sc.frame_start, sc.frame_end = 1, end
    bpy.ops.object.select_all(action='DESELECT'); arm.select_set(True); bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='POSE'); bpy.ops.pose.select_all(action='SELECT')
    bpy.ops.nla.bake(frame_start=1, frame_end=end, only_selected=True, visual_keying=True, clear_constraints=False, use_current_action=False, bake_types={'POSE'})
    bpy.ops.object.mode_set(mode='OBJECT')
    if name in bpy.data.actions and bpy.data.actions[name] is not arm.animation_data.action: bpy.data.actions.remove(bpy.data.actions[name])
    arm.animation_data.action.name = name; arm.animation_data.action.use_fake_user = True
    CLIPS[name] = (end-1)/FPS

def loco(name, T, v, duty, lift, bob, lean, swing, sway, yaw, elbow, hang=0):
    def b():
        n = int(round(T*FPS)); Aa = v*T*duty/2
        for i in range(n+1):
            p = i/n; c = math.cos(2*math.pi*p); ik = {}
            for s, ph in (('L', 0.0), ('R', 0.5)):
                u = (p+ph) % 1.0
                if u < duty: y = -Aa + 2*Aa*u/duty; z = 0
                else: w = (u-duty)/(1-duty); y = Aa - 2*Aa*(0.5-0.5*math.cos(math.pi*w)); z = lift*math.sin(math.pi*w)
                ik['leg'+s] = foot(s, y, z)
            r = body(lean=lean + 2*math.cos(4*math.pi*p), twist=yaw*c, side=-sway*6*c)
            lc = math.cos(2*math.pi*(p-0.08))
            armfk(r, 'L', -swing*lc, -hang, elbow + 6*max(0, -lc)); armfk(r, 'R', swing*lc, -hang, elbow + 6*max(0, lc))
            key(i/FPS, hips=(sway*0.02*c, 0, -bob*(0.5+0.5*math.cos(4*math.pi*(p-0.08)))), rot=r, ik=ik)
        return n+1
    clip(name, b)
exec(open(__file__.rsplit('/',1)[0] + f'/style_{STYLE}.py').read())

for pb in P:
    for c in list(pb.constraints): pb.constraints.remove(c)
    pb.matrix_basis.identity()
for o in list(bpy.data.objects):
    if o.type == 'EMPTY' and (o.name.startswith('ik_') or o.name.startswith('pole_')): bpy.data.objects.remove(o)
for a in list(bpy.data.actions):
    if '__' in a.name: bpy.data.actions.remove(a)
# ---- per-frame checks: hand/forearm inside torso hull; hand height at contact frames ----
GN = {g.index: g.name for g in mesh.vertex_groups}; TORSO = set(['hips'] + SP)
mw = mesh.matrix_world
tv = [v.index for v in mesh.data.vertices if v.groups and GN[max(v.groups, key=lambda g: g.weight).group] in TORSO]
REP = {}
for nm in CLIPS:
    arm.animation_data.action = bpy.data.actions[nm]; n = round(CLIPS[nm]*FPS); worst = (0, None); minz = {}
    for f in range(1, n+2):
        sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get(); me = mesh.evaluated_get(dg); md = me.to_mesh()
        bm = bmesh.new()
        for i in tv: bm.verts.new(mw @ md.vertices[i].co)
        me.to_mesh_clear(); bmesh.ops.convex_hull(bm, input=bm.verts[:]); bm.normal_update()
        cen = sum((v.co for v in bm.verts), Vector())/len(bm.verts); PL = []
        for fc in bm.faces:
            c0 = fc.calc_center_median(); nn = fc.normal.copy(); nn = nn if (c0-cen).dot(nn) >= 0 else -nn; PL.append((c0, nn))
        bm.free()
        PTS = []
        if SOCK is not None:
            Mw = SOCK.matrix_world
            PTS = [('weapon', Mw @ Vector((0, 0, WLEN*k/7))) for k in range(8)]
        if PTS: tz = PTS[-1][1].z; minz['W'] = min(minz.get('W', (1e9,0)), (tz, f))
        for nm_, pt in PTS:
            dep = min(-(pt-c0).dot(nn) for c0, nn in PL)
            if dep > worst[0]: worst = (dep, f'{nm_} f{f}')
        for s in 'LR':
            for b0, b1 in (('foreArm_'+s, 'hand_'+s), ('hand_'+s, None)):
                pb = P[b0]; h0 = arm.matrix_world @ pb.head; h1 = arm.matrix_world @ (P[b1].head if b1 else pb.tail)
                for k in range(6):
                    pt = h0.lerp(h1, k/5); dep = min(-(pt-c0).dot(nn) for c0, nn in PL)
                    if dep > worst[0]: worst = (dep, f'{b0} f{f}')
            hz = (arm.matrix_world @ P['hand_'+s].head).z; minz[s] = min(minz.get(s, (1e9,0)), (hz, f))
    rep = {'sec': round(CLIPS[nm], 3), 'inside_torso_m': round(worst[0], 3), 'at': worst[1], 'hand_min_z_m': {s: (round(v[0], 2), round((v[1]-1)/FPS, 3)) for s, v in minz.items()}}
    if nm in CONTACT:
        f = 1 + round(CONTACT[nm][0]*FPS); sc.frame_set(f)
        rep['contact'] = {s: [round(x, 2) for x in (arm.matrix_world @ P['hand_'+s].head)] for s in 'LR'}; rep['contact_t'] = CONTACT[nm][0]
        dg = bpy.context.evaluated_depsgraph_get(); me = mesh.evaluated_get(dg); md = me.to_mesh()
        for s in 'LR':
            hv = [ (mw @ md.vertices[v.index].co) for v in mesh.data.vertices if v.groups and GN[max(v.groups, key=lambda g: g.weight).group].startswith(('hand_'+s, 'fingers_'+s)) ]
            if hv: rep['fist_bottom_z_'+s] = round(min(p.z for p in hv), 2); rep['fist_y_'+s] = round(sum(p.y for p in hv)/len(hv), 2)
        me.to_mesh_clear()
        if SOCK is not None: rep['tip_at_hit'] = [round(x,2) for x in SOCK.matrix_world @ Vector((0,0,WLEN))]
    REP[nm] = rep
arm.animation_data.action = None; sc.frame_set(1)
json.dump({'H': H, 'clips': REP}, open(dst + '.json', 'w'), indent=1)
print('BIG', json.dumps(REP))
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=dst, export_format='GLB', export_animation_mode='ACTIONS', export_force_sampling=True, export_skins=True, export_def_bones=False, export_optimize_animation_size=False)
print('BIGRIG exported', dst, [a.name for a in bpy.data.actions])
