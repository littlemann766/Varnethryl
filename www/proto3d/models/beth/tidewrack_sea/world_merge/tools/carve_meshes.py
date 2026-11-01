"""Stage 10 (Beth): apply island_carve.carve() to the Saltglass, Frost and Ash terrain meshes (tiles, lod1, terrain_col).
Originals -> <stage>/meshes_v2_backup/ (pre-island). Re-running always starts from the backup.
New shore vertices are recoloured: Saltglass sand/wet sand, Frost snow-ice/blue ice, Ash dark sand; raised spine land
takes the tile's median low-grass colour; new sea floor takes the tile's median seabed colour."""
import sys, os, glob, shutil, numpy as np, trimesh
sys.path.insert(0, os.path.dirname(__file__)); from island_carve import carve, fbm, ss
ROOT = sys.argv[1]   # .../tidewrack_sea
JOBS = [('B', 'stage2', 'coast_'), ('frost', 'stage4', 'frost_'), ('ash', 'stage4', 'ash_')]
SHORE = {'B': ((0.74, 0.66, 0.48), (0.45, 0.40, 0.31)), 'frost': ((0.80, 0.84, 0.88), (0.46, 0.58, 0.70)), 'ash': ((0.36, 0.31, 0.28), (0.18, 0.16, 0.16))}
def do(reg, f):
    s = trimesh.load(f, force='scene'); ch = 0
    for node in s.graph.nodes_geometry:
        xf, gn = s.graph[node]; g = s.geometry[gn]; P = trimesh.transform_points(g.vertices, xf)
        h2, sm = carve(reg, P[:, 0], P[:, 2], P[:, 1])
        if reg == 'ash':   # ash only changes near its west/north rect edges (the old notch); everything else stays
            h2 = np.where((P[:, 0] < -1450) | (P[:, 2] < 1650), h2, P[:, 1])
        dh = h2 - P[:, 1]; mv = np.abs(dh) > 0.05
        if not mv.any(): continue
        ch += int(mv.sum())
        Q = P.copy(); Q[:, 1] = h2; inv = np.linalg.inv(xf); g.vertices = trimesh.transform_points(Q, inv)
        vc = getattr(g.visual, 'vertex_colors', None)
        if vc is not None and len(vc) == len(P):
            c = vc[:, :3].astype(float) / 255
            sea = P[:, 1] < -8; low = (P[:, 1] > 2) & (P[:, 1] < 14)
            seab = np.median(c[sea], 0) if sea.sum() > 20 else np.array([0.25, 0.30, 0.30])
            lowc = np.median(c[low], 0) if low.sum() > 20 else np.array([0.36, 0.45, 0.25])
            dry, wet = map(np.array, SHORE[reg]); n = fbm(P[:, 0] * 3.1, P[:, 2] * 3.1, 3, 5)[:, None] * 0.06
            tgt = np.where((h2 < -2.5)[:, None], seab, np.where((h2 < 0.6)[:, None], wet, np.where((h2 < 2.8)[:, None], dry, lowc)))
            w = np.clip(np.abs(dh) / 2.0, 0, 1)[:, None] * mv[:, None]
            if reg == 'frost': w = w * np.where((h2 > 2.8)[:, None], 0.0, 1.0)   # frost keeps its snow/rock above the shore
            if reg == 'B': w = w * np.where(((h2 > 2.8) & (dh < 0))[:, None], 0.0, 1.0)  # carved hills keep their colour
            out = c * (1 - w) + (tgt + n) * w
            g.visual.vertex_colors = np.c_[(np.clip(out, 0, 1) * 255).astype(np.uint8), vc[:, 3]]
        g._cache.clear()
    return s, ch
for reg, st, pre in JOBS:
    D = f'{ROOT}/{st}/meshes'; BK = f'{ROOT}/{st}/meshes_v2_backup'; os.makedirs(BK, exist_ok=True)
    for f in sorted(glob.glob(f'{D}/{pre}tile_*.glb') + [f'{D}/{pre}terrain_col.glb']):
        b = f'{BK}/' + os.path.basename(f)
        if not os.path.exists(b): shutil.copy(f, b)
        gsrc = b.replace('.glb', '_grid.glb')
        s, ch = do(reg, gsrc if os.path.exists(gsrc) else b)
        if ch: s.export(f); print(reg, os.path.basename(f), ch, 'verts moved')
        elif os.path.exists(b) and open(b,'rb').read() == open(f,'rb').read(): os.remove(b)
