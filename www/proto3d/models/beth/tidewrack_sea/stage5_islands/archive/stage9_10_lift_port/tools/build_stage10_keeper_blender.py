"""Beth stage 10: Saltglass lift keeper - voxel NPC on the town-guard (mixamo) rig. Clips: idle (the guard's idle), crank (new, IK-baked)."""
import bpy, sys, math, numpy as np, mathutils
OUT = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath='/workspace/godot-art/voxel_cast/cape_fix32/glb/town_guard_voxel.glb')
A = bpy.data.objects['Armature']
for o in list(bpy.data.objects):
    if o.type != 'ARMATURE': bpy.data.objects.remove(o)
if A.animation_data:
    for t in list(A.animation_data.nla_tracks): A.animation_data.nla_tracks.remove(t)
for a in list(bpy.data.actions):
    if a.name != 'idle_Armature': bpy.data.actions.remove(a, do_unlink=True)
idle = bpy.data.actions['idle_Armature']; idle.name = 'idle'
# drop the guard's cape bones (keeper has an apron, no cape)
bpy.context.view_layer.objects.active = A; bpy.ops.object.mode_set(mode='EDIT')
for b in list(A.data.edit_bones):
    if b.name.startswith('capeV'): A.data.edit_bones.remove(b)
bpy.ops.object.mode_set(mode='OBJECT')
for fc in list(idle.fcurves):
    if 'capeV' in fc.data_path: idle.fcurves.remove(fc)
BN = {b.name.replace('mixamorig:', ''): b for b in A.data.bones}
def hd(n): return np.array(BN[n].head_local); 
def tl(n): return np.array(BN[n].tail_local)
rng = np.random.default_rng(7)
def C(r, g, b): return np.array([r, g, b], float)
SKIN = C(196, 146, 112); BEARD = C(156, 150, 142); CAP = C(58, 82, 90); SHIRT = C(116, 124, 142); TROU = C(92, 84, 74); BOOT = C(54, 42, 34)
GLOVE = C(96, 64, 40); CUFF = C(122, 84, 52); APRON = C(132, 94, 58); APRON2 = C(104, 72, 44); BRASS = C(206, 164, 82); BELT = C(62, 44, 30); EYE = C(30, 26, 24); NOSE = C(206, 132, 104)
# capsules: (bone, a, b, radius, colour)
caps = []
def cap(bone, a, b, r, col): caps.append((bone, np.array(a, float), np.array(b, float), r, col))
cap('Hips', hd('Hips') + [0, 0, -0.04], hd('Spine'), 0.16, TROU)
cap('Spine', hd('Spine'), tl('Spine'), 0.17, SHIRT); cap('Spine1', hd('Spine1'), tl('Spine1'), 0.175, SHIRT); cap('Spine2', hd('Spine2'), tl('Spine2') - [0, 0, 0.03], 0.165, SHIRT)
cap('Neck', hd('Neck'), tl('Neck'), 0.065, SKIN)
hc = hd('Head') + (tl('Head') - hd('Head')) * 0.45
cap('Head', hc + [0, 0, -0.04], hc + [0, 0, 0.06], 0.125, SKIN)
for s, S in (('Left', 1), ('Right', -1)):
    cap(s + 'Shoulder', hd(s + 'Shoulder') + [0, 0, -0.02], tl(s + 'Shoulder'), 0.075, SHIRT)
    a0, a1 = hd(s + 'Arm'), tl(s + 'Arm'); cap(s + 'Arm', a0, a0 + (a1 - a0) * 0.75, 0.062, SHIRT); cap(s + 'Arm', a0 + (a1 - a0) * 0.75, a1, 0.068, SHIRT)   # rolled sleeve bulge
    f0, f1 = hd(s + 'ForeArm'), tl(s + 'ForeArm'); cap(s + 'ForeArm', f0, f0 + (f1 - f0) * 0.45, 0.052, SKIN); cap(s + 'ForeArm', f0 + (f1 - f0) * 0.45, f1, 0.066, CUFF)
    h0 = hd(s + 'Hand'); hdir = (tl(s + 'Hand') - h0); hdir /= np.linalg.norm(hdir); cap(s + 'Hand', h0, h0 + hdir * 0.1, 0.06, GLOVE)
    cap(s + 'UpLeg', hd(s + 'UpLeg'), tl(s + 'UpLeg'), 0.095, TROU); cap(s + 'Leg', hd(s + 'Leg'), hd(s + 'Leg') + (tl(s + 'Leg') - hd(s + 'Leg')) * 0.55, 0.075, TROU)
    cap(s + 'Leg', hd(s + 'Leg') + (tl(s + 'Leg') - hd(s + 'Leg')) * 0.55, tl(s + 'Leg'), 0.08, BOOT)
    cap(s + 'Foot', hd(s + 'Foot'), tl(s + 'Foot'), 0.07, BOOT); cap(s + 'ToeBase', hd(s + 'ToeBase'), tl(s + 'ToeBase') + [0, -0.02, 0], 0.055, BOOT)
VS = float(sys.argv[-1]) if sys.argv[-1].replace('.', '').isdigit() else 0.03
lo = np.min([np.minimum(a, b) - r for _, a, b, r, _ in caps], 0) - VS * 3; hi = np.max([np.maximum(a, b) + r for _, a, b, r, _ in caps], 0) + VS * 3
lo[2] = 0.0; hi[2] += 0.08
xs = np.arange(lo[0], hi[0], VS) + VS / 2; ys = np.arange(lo[1], hi[1], VS) + VS / 2; zs = np.arange(lo[2], hi[2], VS) + VS / 2
X, Y, Z = np.meshgrid(xs, ys, zs, indexing='ij'); P = np.stack([X, Y, Z], -1)
best = np.full(X.shape, 1e9); own = np.full(X.shape, -1)
for i, (b, a, c, r, col) in enumerate(caps):
    u = c - a; t = np.clip(((P - a) @ u) / max(u @ u, 1e-9), 0, 1); d = np.linalg.norm(P - (a + t[..., None] * u), axis=-1) - r
    m = d < best; best[m] = d[m]; own[m] = i
fill = best < 0
COL = np.zeros(X.shape + (3,)); BONE = np.empty(X.shape, object)
for i, (b, a, c, r, col) in enumerate(caps):
    m = own == i; COL[m] = col; BONE[m] = b
# face features + hair/beard/cap (in the head's frame: front = -y)
H0 = hc; hr = 0.125
def sel(m, col, bone='Head', add=False):
    global fill
    if add: fill = fill | m
    COL[m & fill] = col; BONE[m & fill] = bone
rel = P - H0
sel((rel[..., 2] > 0.035) & (np.linalg.norm(rel, axis=-1) < hr + 0.035) & (rel[..., 2] < 0.13), CAP, add=True)   # wool cap
sel((rel[..., 2] > 0.075) & (np.linalg.norm(rel - [0, 0, 0.03], axis=-1) < hr + 0.02), CAP, add=True)
sel((np.abs(rel[..., 0]) < 0.12) & (rel[..., 1] < -0.02) & (rel[..., 2] < -0.04) & (rel[..., 2] > -0.17) & (np.linalg.norm(rel - [0, -0.03, -0.07], axis=-1) < 0.135), BEARD, add=True)   # beard
sel((np.abs(rel[..., 0]) < 0.022) & (rel[..., 1] < -hr + 0.005) & (rel[..., 1] > -hr - 0.04) & (np.abs(rel[..., 2] + 0.0) < 0.03), NOSE, add=True)
for ex in (-0.05, 0.05): sel((np.abs(rel[..., 0] - ex) < 0.018) & (rel[..., 1] < -hr + 0.03) & (np.abs(rel[..., 2] - 0.035) < 0.015), EYE)
sel((np.abs(rel[..., 0]) < 0.11) & (rel[..., 1] < -0.04) & (np.abs(rel[..., 2] - 0.06) < 0.012) & (np.linalg.norm(rel, axis=-1) > hr - 0.02), BEARD)   # brows
# apron: front layer of torso/hips/thighs + a hanging flap to the knees, straps over the shoulders, pocket + brass buckle
tor = np.isin(own, [i for i, c in enumerate(caps) if c[0] in ('Hips', 'Spine', 'Spine1', 'Spine2', 'LeftUpLeg', 'RightUpLeg')])
front = np.full(X.shape[::2], 0)
yfront = np.where(fill, Y, 9).min(1, keepdims=True)
ap = fill & tor & (Y < yfront + 0.05) & (np.abs(X - 0.011) < 0.2) & (Z > 0.62) & (Z < 1.42)
sel(ap, APRON, 'Hips'); BONE[ap & (Z > 1.12)] = 'Spine1'
flap = (np.abs(X - 0.011) < 0.21) & (Y > -0.16) & (Y < -0.11) & (Z > 0.5) & (Z < 1.0) & ~fill
sel(flap, APRON, 'Hips', add=True)
sel((fill & (Y < yfront + 0.05) & (np.abs(X - 0.011) < 0.11) & (np.abs(Z - 0.9) < 0.08)) | (flap & (np.abs(X - 0.011) < 0.11) & (np.abs(Z - 0.85) < 0.07)), APRON2, 'Hips')   # pocket
sel(fill & tor & (np.abs(Z - 1.1) < 0.025), BELT, 'Spine'); sel(fill & (Y < yfront + 0.05) & (np.abs(X - 0.011) < 0.03) & (np.abs(Z - 1.1) < 0.03), BRASS, 'Spine')
for sx in (-0.09, 0.11): sel(fill & np.isin(own, [i for i, c in enumerate(caps) if c[0] in ('Spine1', 'Spine2')]) & (np.abs(X - sx) < 0.03) & (Z > 1.38), APRON2, 'Spine2')   # straps
# colour noise (weathered)
COL = np.clip(COL * rng.uniform(0.9, 1.08, X.shape)[..., None], 0, 255)
# surface faces
I = np.argwhere(fill); occ = fill
pal = {}; verts = []; faces = []; fcol = []; fbone = []
D = [((1, 0, 0), [(1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1)]), ((-1, 0, 0), [(0, 0, 0), (0, 0, 1), (0, 1, 1), (0, 1, 0)]), ((0, 1, 0), [(0, 1, 0), (0, 1, 1), (1, 1, 1), (1, 1, 0)]),
     ((0, -1, 0), [(0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)]), ((0, 0, 1), [(0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)]), ((0, 0, -1), [(0, 0, 0), (0, 1, 0), (1, 1, 0), (1, 0, 0)])]
sh = np.array(fill.shape)
for (n, q) in D:
    nb = I + n; inside = np.all((nb >= 0) & (nb < sh), 1); exp = ~inside.copy(); exp[inside] = ~occ[tuple(nb[inside].T)]
    for c in I[exp]:
        base = len(verts); o = np.array([xs[0], ys[0], zs[0]]) - VS / 2 + c * VS
        verts += [tuple(o + np.array(v) * VS) for v in q]; faces.append((base, base + 1, base + 2, base + 3))
        k = tuple((COL[tuple(c)] // 6 * 6).astype(int)); pal.setdefault(k, len(pal)); fcol.append(pal[k]); fbone.append(BONE[tuple(c)])
print('VOX', int(fill.sum()), 'quads', len(faces), 'tris', 2 * len(faces), 'pal', len(pal))
me = bpy.data.meshes.new('lift_keeper'); me.from_pydata(verts, [], faces); me.update()
ob = bpy.data.objects.new('lift_keeper', me); bpy.context.scene.collection.objects.link(ob)
# palette texture: 16 px cells
N = int(math.ceil(math.sqrt(len(pal)))); W = N * 4; img = bpy.data.images.new('keeper_pal', W, W); px = np.ones((W, W, 4))
for k, i in pal.items():
    cx, cy = i % N, i // N; px[cy * 4:cy * 4 + 4, cx * 4:cx * 4 + 4, :3] = np.array(k) / 255.0
img.pixels = px.ravel().tolist(); img.pack()
uv = me.uv_layers.new(name='UVMap')
for f, ci in zip(me.polygons, fcol):
    u_, v_ = ((ci % N) * 4 + 2) / W, ((ci // N) * 4 + 2) / W
    for li in f.loop_indices: uv.data[li].uv = (u_, v_)
mat = bpy.data.materials.new('lift_keeper'); mat.use_nodes = True; bs = mat.node_tree.nodes['Principled BSDF']; bs.inputs['Roughness'].default_value = 0.9
tx = mat.node_tree.nodes.new('ShaderNodeTexImage'); tx.image = img; tx.interpolation = 'Closest'; mat.node_tree.links.new(tx.outputs['Color'], bs.inputs['Base Color']); me.materials.append(mat)
# rigid skin
groups = {}
for fi, b in enumerate(fbone):
    for vi in faces[fi]: groups.setdefault(b, []).append(vi)
for b, vv in groups.items(): ob.vertex_groups.new(name='mixamorig:' + b).add(vv, 1.0, 'REPLACE')
ob.parent = A; md = ob.modifiers.new('Armature', 'ARMATURE'); md.object = A
# merge duplicate verts within each bone group only would bridge bones; keep flat voxels (exporter dedups)
# ---- crank clip: torso leans in, both gloves on a crank handle turning 1 rev / 30 frames (30 fps -> 1 rev/s)
A.animation_data_create(); crank = bpy.data.actions.new('crank'); A.animation_data.action = crank
bpy.context.view_layer.objects.active = A; bpy.ops.object.mode_set(mode='POSE')
pb = {p.name.replace('mixamorig:', ''): p for p in A.pose.bones}
# start pose = idle frame 0 for everything, then override
sc = bpy.context.scene; sc.render.fps = 24; sc.frame_start, sc.frame_end = 0, 48   # glTF clips here are keyed at 24 fps (the guard's idle too); never re-time
CEN = np.array([0.011, -0.20, 1.12]); R = 0.08
tg = {}
for s, S in (('Left', 1), ('Right', -1)):
    e = bpy.data.objects.new('tgt_' + s, None); sc.collection.objects.link(e); tg[s] = e
    pole = bpy.data.objects.new('pole_' + s, None); sc.collection.objects.link(pole); pole.location = (0.011 + S * 0.55, 0.25, 1.0)
    c = pb[s + 'ForeArm'].constraints.new('IK'); c.target = e; c.chain_count = 2; c.pole_target = pole; c.pole_angle = math.radians(-90 if S > 0 else -90)
for f in range(0, 49):
    ang = 2 * math.pi * f / 24.0
    for s, S in (('Left', 1), ('Right', -1)):
        p = CEN + [S * 0.085, -R * math.cos(ang), R * math.sin(ang)]; tg[s].location = p; tg[s].keyframe_insert('location', frame=f)
for f in range(0, 49, 4):   # lean + bob in time with the crank
    ang = 2 * math.pi * f / 24.0
    for n, amt in (('Spine', 0.10), ('Spine1', 0.08), ('Spine2', 0.04)):
        p = pb[n]; p.rotation_mode = 'XYZ'; p.rotation_euler = (amt + 0.03 * math.sin(ang), 0, 0.02 * math.cos(ang)); p.keyframe_insert('rotation_euler', frame=f)
    p = pb['Head']; p.rotation_mode = 'XYZ'; p.rotation_euler = (-0.12, 0, 0); p.keyframe_insert('rotation_euler', frame=f)
    p = pb['Hips']; p.location = (0, 0.012 * math.sin(ang), 0); p.keyframe_insert('location', frame=f)
    for s in ('Left', 'Right'):   # feet planted: legs from idle frame 0 are reused via NLA below; small knee flex
        p = pb[s + 'Leg']; p.rotation_mode = 'XYZ'; p.rotation_euler = (0.08 + 0.03 * math.sin(ang), 0, 0); p.keyframe_insert('rotation_euler', frame=f)
for p in pb.values():
    p.rotation_mode = 'XYZ'
bpy.ops.pose.select_all(action='SELECT')
bpy.ops.nla.bake(frame_start=0, frame_end=48, only_selected=True, visual_keying=True, clear_constraints=True, use_current_action=True, bake_types={'POSE'})
bpy.ops.object.mode_set(mode='OBJECT')
for o in list(bpy.data.objects):
    if o.type == 'EMPTY': bpy.data.objects.remove(o)
for a in bpy.data.actions: a.use_fake_user = True
A.animation_data.action = idle
tr = A.animation_data.nla_tracks
for a in (idle, bpy.data.actions['crank']):
    t = tr.new(); t.name = a.name; t.strips.new(a.name, 0, a)
A.animation_data.action = None
bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB', export_animations=True, export_animation_mode='NLA_TRACKS', export_skins=True, export_yup=True, export_apply=False)
print('EXPORTED', OUT)
