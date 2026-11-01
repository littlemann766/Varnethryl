"""Stage 11 (Beth): the authored frost_ice_floes fields had square outlines on the map. Drop floes outside an fbm mask
(irregular field edges) and any floe now over land. Original -> meshes_v2_backup/."""
import sys, os, shutil, numpy as np, trimesh
sys.path.insert(0, os.path.dirname(__file__)); from island_carve import fbm
R, HA = sys.argv[1], sys.argv[2]; H = np.fromfile(HA, np.float32).reshape(640, 640)
for nm in ('frost_ice_floes', 'frost_ice_floes_lod1'):
    f = f'{R}/stage4/meshes/{nm}.glb'; b = f'{R}/stage4/meshes_v2_backup/{nm}.glb'
    if not os.path.exists(b): shutil.copy(f, b)
    s = trimesh.load(b, force='scene'); kept = tot = 0
    for node in s.graph.nodes_geometry:
        xf, gn = s.graph[node]; g = s.geometry[gn]; P = trimesh.transform_points(g.vertices, xf)
        Fc = P[g.faces].mean(1); tot += len(Fc)
        h = H[np.clip(((Fc[:, 2] + 3200) / 10).astype(int), 0, 639), np.clip(((Fc[:, 0] + 3200) / 10).astype(int), 0, 639)]
        m = fbm(Fc[:, 0] * 2.2, Fc[:, 2] * 2.2, 1, 5)
        cell = np.floor(Fc[:, [0, 2]] / 3.0)   # per-face test; keep whole little floes together by 3 m cell vote
        keep = (h < -0.5) & (m > -0.05); kept += int(keep.sum())
        g.update_faces(keep); g.remove_unreferenced_vertices()
    s.export(f); print(nm, kept, '/', tot)
