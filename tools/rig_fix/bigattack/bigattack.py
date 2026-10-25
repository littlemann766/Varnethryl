# Big-creature attack authoring on an existing rig (Darius-style 69-bone or 21-bone). Torso-driven FK + IK hands for exact ground contact.
# usage: blender -b --python bigattack.py -- in.glb out_roundtrip.glb STYLE
import bpy, sys, math, json
from mathutils import Vector, Quaternion
import bmesh
src, dst, STYLE = sys.argv[-3], sys.argv[-2], sys.argv[-1]
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=src, bone_heuristic='TEMPERANCE')
arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]; P = arm.pose.bones
mesh = max([o for o in bpy.data.objects if o.type == 'MESH' and o.vertex_groups], key=lambda o: len(o.data.vertices))
S = arm.matrix_world.to_scale()[0]
H = (arm.matrix_world @ arm.data.bones['head'].head_local).z / 0.88
for a in list(bpy.data.actions): bpy.data.actions.remove(a)
arm.animation_data_create(); arm.animation_data.action = None
for pb in P: pb.rotation_mode = 'QUATERNION'; pb.matrix_basis.identity()
D = math.radians; X, Y, Z = (1,0,0), (0,1,0), (0,0,1)
def q(ax, d): return Quaternion(ax, D(d))
def setL(pb, L): r = pb.bone.matrix_local.to_quaternion(); pb.rotation_quaternion = r.inverted() @ L @ r
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
    bpy.ops.object.mode_set(mode='OBJECT'); arm.animation_data.action.name = name; arm.animation_data.action.use_fake_user = True
    CLIPS[name] = (end-1)/FPS
exec(open(__file__.rsplit('/',1)[0] + f'/style_{STYLE}.py').read())
# remove helpers
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
    REP[nm] = rep
# dump heuristic-independent deform matrices D = pose_world * rest_world^-1 per bone per frame
DUMP = {}
for nm in CLIPS:
    arm.animation_data.action = bpy.data.actions[nm]; n = round(CLIPS[nm]*FPS); fr = []
    for f in range(1, n+2):
        sc.frame_set(f); fr.append({pb.name: [list(r) for r in (pb.matrix @ pb.bone.matrix_local.inverted())] for pb in P})
    DUMP[nm] = fr
json.dump(DUMP, open(dst + '.dump.json', 'w'))
arm.animation_data.action = None; sc.frame_set(1)
json.dump({'H': H, 'clips': REP}, open(dst + '.json', 'w'), indent=1)
print('BIG', json.dumps(REP))
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=dst, export_format='GLB', export_animation_mode='ACTIONS', export_force_sampling=True, export_skins=True, export_def_bones=False, export_optimize_animation_size=False)
