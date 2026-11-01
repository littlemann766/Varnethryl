"""Stage 11 (Beth): the three Frost POI island meshes (frostreach, frozen_wreck, aurora_arch) sat on the frost tiles as
square patches. Their outer band (fbm-wobbled, 25-70 m) now tucks 0.6 m under the frost tile surface (or to -3 m over sea)
and takes the tile colour, so the patch edge follows an irregular line. Nothing moves within 60 m of a landing
shore/moor/spawn point or the ice dock. Visual, lod1 and col. Originals -> stage5_islands/meshes_v2_backup/frost/."""
import sys, os, glob, shutil, json, numpy as np, trimesh
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(__file__)); from island_carve import fbm, ss
R = sys.argv[1]
T = []   # carved frost tile grid (7.5 m): height + colour
for f in glob.glob(f'{R}/stage4/meshes/frost_tile_x?z?.glb'):
    m = trimesh.load(f, force='mesh'); T.append(np.c_[m.vertices, m.visual.vertex_colors[:, :3]])
T = np.concatenate(T); x0, z0, st = -2400.0, -3000.0, 7.5; nx, nz = 521, 201
GH = np.full((nz, nx), -3.0); GC = np.zeros((nz, nx, 3)) + [60, 80, 95]
ix = np.round((T[:, 0] - x0) / st).astype(int); iz = np.round((T[:, 2] - z0) / st).astype(int)
GH[iz, ix] = T[:, 1]; GC[iz, ix] = T[:, 3:6]
def tile(x, z):
    i = np.clip(np.round((x - x0) / st).astype(int), 0, nx - 1); k = np.clip(np.round((z - z0) / st).astype(int), 0, nz - 1); return GH[k, i], GC[k, i]
avoid = []
for p in json.load(open(os.environ.get('TW', '/tmp/gv2/tidewrack') + '/landings.json')).values():
    for key in ('shore', 'moor', 'spawn'):
        if key in p: avoid.append((p[key][0], p[key][2]))
for q in json.load(open(f'{R}/stage4/landing_stairs.json')).get('stairs', []) if os.path.exists(f'{R}/stage4/landing_stairs.json') else []:
    pass
avoid += [(-891, -1950), (-988, -1946)]; avoid = np.array(avoid, float)
D = f'{R}/stage5_islands/meshes/frost'; BK = f'{R}/stage5_islands/meshes_v2_backup/frost'; os.makedirs(BK, exist_ok=True)
for name in ('frostreach', 'frozen_wreck', 'aurora_arch'):
    src = f'{D}/frost_isl_{name}.glb'; b0 = f'{BK}/frost_isl_{name}.glb'
    if not os.path.exists(b0): shutil.copy(src, b0)
    ref = trimesh.load(b0, force='mesh'); lo, hi = ref.vertices.min(0), ref.vertices.max(0)
    for suf in ('', '_lod1'):   # visual only: the walk-tested _col stays as authored
        f = f'{D}/frost_isl_{name}{suf}.glb'; b = f'{BK}/frost_isl_{name}{suf}.glb'
        if not os.path.exists(b): shutil.copy(f, b)
        s = trimesh.load(b, force='scene'); n = 0
        for node in s.graph.nodes_geometry:
            xf, gn = s.graph[node]; g = s.geometry[gn]; P = trimesh.transform_points(g.vertices, xf)
            de = np.minimum(np.minimum(P[:, 0] - lo[0], hi[0] - P[:, 0]), np.minimum(P[:, 2] - lo[2], hi[2] - P[:, 2]))
            band = 45 + 25 * fbm(P[:, 0] * 1.7, P[:, 2] * 1.7, 1, 5)
            w = 1 - ss(band - 20, band + 10, de)
            av = np.min(np.hypot(P[:, 0, None] - avoid[None, :, 0], P[:, 2, None] - avoid[None, :, 1]), 1)
            w = w * ss(60, 90, av)
            th, tc = tile(P[:, 0], P[:, 2]); tgt = np.where(th > 0.2, th - 0.6, -3.0)
            ny = np.minimum(P[:, 1], P[:, 1] * (1 - w) + tgt * w); mv = np.abs(ny - P[:, 1]) > 0.05
            if not mv.any(): continue
            n += int(mv.sum()); Q = P.copy(); Q[:, 1] = ny; g.vertices = trimesh.transform_points(Q, np.linalg.inv(xf))
            vc = getattr(g.visual, 'vertex_colors', None)
            if vc is not None and len(vc) == len(P):
                wc = (1 - ss(band + 5, band + 45, de)) * ss(60, 90, av)   # colour band wider than the tuck band
                c = vc[:, :3].astype(float); out = c * (1 - wc[:, None]) + tc * wc[:, None]
                g.visual.vertex_colors = np.c_[np.clip(out, 0, 255).astype(np.uint8), vc[:, 3]]
        s.export(f); print(name + suf, n, 'verts tucked')
# second pass: the other POI islands (A, B, ash) are square insets on arch_islands / the region tiles. Their outer band
# (fbm 30-60 m) tucks 0.6 m under that base terrain (or to -3 m where the base is sea), so the seam follows the
# terrain instead of the square. Nothing within 60 m of a landing point; the Saltglass port is not touched.
from rast import raster
BASE = {'A': [f'{R}/stage1/meshes/arch_islands.glb'],   # isl_blend runs before the wobble, so this is the original
        'B': sorted(glob.glob(f'{R}/stage2/meshes/coast_tile_x?z?.glb')), 'ash': sorted(glob.glob(f'{R}/stage4/meshes/ash_tile_x?z?.glb'))}
for reg, pre in (('A', 'arch_'), ('B', 'coast_'), ('ash', 'ash_')):
    D = f'{R}/stage5_islands/meshes/{reg}'; BK = f'{R}/stage5_islands/meshes_v2_backup/{reg}'; os.makedirs(BK, exist_ok=True)
    for src in sorted(glob.glob(f'{D}/{pre}isl_*.glb')):
        if any(t in src for t in ('_lod1', '_col', '_glow', 'saltglass_port')): continue
        name = os.path.basename(src)[:-4]; b0 = f'{BK}/{name}.glb'
        if not os.path.exists(b0): shutil.copy(src, b0)
        ref = trimesh.load(b0, force='mesh'); lo, hi = ref.vertices.min(0), ref.vertices.max(0)
        rr = [lo[0] - 3, lo[2] - 3, hi[0] - lo[0] + 6, hi[2] - lo[2] + 6]; BH = raster(BASE[reg], rr, 2.0)
        def base(x, z):
            i = np.clip(((x - rr[0]) / 2.0).astype(int), 0, BH.shape[1] - 1); j = np.clip(((z - rr[1]) / 2.0).astype(int), 0, BH.shape[0] - 1); return BH[j, i]
        for suf in ('', '_lod1'):   # visual only: the walk-tested _col stays as authored (tucking it dropped walkers through)
            f = f'{D}/{name}{suf}.glb'; b = f'{BK}/{name}{suf}.glb'
            if not os.path.exists(f): continue
            if not os.path.exists(b): shutil.copy(f, b)
            s = trimesh.load(b, force='scene'); n = 0
            for node in s.graph.nodes_geometry:
                xf, gn = s.graph[node]; g = s.geometry[gn]; P = trimesh.transform_points(g.vertices, xf)
                de = np.minimum(np.minimum(P[:, 0] - lo[0], hi[0] - P[:, 0]), np.minimum(P[:, 2] - lo[2], hi[2] - P[:, 2]))
                band = 45 + 15 * fbm(P[:, 0] * 1.9, P[:, 2] * 1.9, 1, 5)
                av = np.min(np.hypot(P[:, 0, None] - avoid[None, :, 0], P[:, 2, None] - avoid[None, :, 1]), 1)
                w = (1 - ss(band - 20, band + 10, de)) * ss(60, 90, av)
                bh = base(P[:, 0], P[:, 2]); tgt = np.where(bh > 0.2, bh - 0.6, -3.0)
                ny = np.minimum(P[:, 1], P[:, 1] * (1 - w) + tgt * w); mv = np.abs(ny - P[:, 1]) > 0.05
                if not mv.any(): continue
                n += int(mv.sum()); Q = P.copy(); Q[:, 1] = ny; g.vertices = trimesh.transform_points(Q, np.linalg.inv(xf))
            s.export(f); print(name + suf, n, 'edge verts tucked under base')
