"""Stage 10 (Beth): props standing on land that the island carve lowered are re-seated (moved down with the ground)
or dropped when their ground is now sea. Per connected component. Originals -> meshes_v2_backup/.
Usage: reseat_props.py <tidewrack_sea dir> <H_before.f32> <H_after.f32>"""
import sys, os, shutil, numpy as np, trimesh
R, HB, HA = sys.argv[1:4]
H0 = np.fromfile(HB, np.float32).reshape(640, 640); H1 = np.fromfile(HA, np.float32).reshape(640, 640)
def smp(H, x, z): return H[np.clip(((z + 3200) / 10).astype(int), 0, 639), np.clip(((x + 3200) / 10).astype(int), 0, 639)]
FILES = ['stage2/meshes/coast_beach_dressing', 'stage2/meshes/coast_saltglass_crystals', 'stage4/meshes/frost_icicles',
         'stage4/meshes/ash_vents', 'stage4/meshes/ash_glow', 'stage4/meshes/ash_steam', 'stage4/meshes/ash_lava_seams']
for base in FILES:
    for f in [f'{R}/{base}.glb', f'{R}/{base}_lod1.glb']:
        if not os.path.exists(f): continue
        bk = os.path.join(os.path.dirname(f), '..', 'meshes_v2_backup', os.path.basename(f)); os.makedirs(os.path.dirname(bk), exist_ok=True)
        if not os.path.exists(bk): shutil.copy(f, bk)
        s = trimesh.load(bk, force='scene'); moved = dropped = 0
        for node in s.graph.nodes_geometry:
            xf, gn = s.graph[node]; g = s.geometry[gn]; P = trimesh.transform_points(g.vertices, xf)
            lab = trimesh.graph.connected_component_labels(g.face_adjacency, node_count=len(g.faces))
            keepf = np.ones(len(g.faces), bool); Q = P.copy()
            for L in np.unique(lab):
                fi = np.where(lab == L)[0]; vi = np.unique(g.faces[fi])
                cx, cz = P[vi, 0].mean(), P[vi, 2].mean(); a = float(smp(H0, cx, cz)); c = float(smp(H1, cx, cz))
                if a > 0.3 and c < a - 1.0:
                    if c < 0.3: keepf[fi] = False; dropped += 1
                    else: Q[vi, 1] += c - a; moved += 1
            g.vertices = trimesh.transform_points(Q, np.linalg.inv(xf))
            if not keepf.all(): g.update_faces(keepf); g.remove_unreferenced_vertices()
        s.export(f); print(os.path.basename(f), 'moved', moved, 'dropped', dropped)
