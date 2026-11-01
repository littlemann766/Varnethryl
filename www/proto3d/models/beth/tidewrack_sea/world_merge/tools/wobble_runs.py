"""Stage 11 (Beth): break every straight coast run found by straight_scan.py. Terrain vertices within ~22 m of the run
are pushed sideways along its normal by an along-run noise (+-7 m, 14-30 m wavelengths), so the edge becomes coves
and small headlands. Built structures are exempt: runs within 45 m of a port anchor, landing shore/moor point, landing
stair or the Saltglass port mesh are kept and listed as quays/piers. Same field for visual, lod1 and col meshes.
Usage: wobble_runs.py <tidewrack_sea dir> <runs.json> <exempt_out.json>  (runs accumulate in world_merge/wobble_runs.json)"""
import sys, os, glob, json, shutil, numpy as np, trimesh
R, RUNS, EX = sys.argv[1:4]
LD = json.load(open(os.environ.get('TW', '/tmp/gv2/tidewrack') + '/landings.json'))
S1 = json.load(open(os.environ.get('TW', '/tmp/gv2/tidewrack') + '/stage1/meshes/stage1_manifest.json'))
S2 = json.load(open(os.environ.get('TW', '/tmp/gv2/tidewrack') + '/stage2/meshes/stage2_manifest.json')); S4 = json.load(open(os.environ.get('TW', '/tmp/gv2/tidewrack') + '/stage4/meshes/stage4_manifest.json'))
built = [(S1['props']['gullhaven']['anchor'], 'Gullhaven port'), (S2['props']['saltglass_landing']['anchor'], 'Saltglass Landing quay'),
         (S4['props']['frostreach_ice_dock']['anchor'], 'Frostreach ice dock'), (S4['props']['frostreach_ice_dock']['pos'], 'Frostreach ice dock'), (S4['props']['vent_harbour']['anchor'], 'Vent Harbour quay')]
for k, v in LD.items():
    built += [(v['shore'], f'{v["name"]} landing pier'), (v['moor'], f'{v["name"]} mooring')]
pm = trimesh.load(f'{R}/stage5_islands/meshes/B/coast_isl_saltglass_port.glb', force='mesh'); plo, phi = pm.bounds[0], pm.bounds[1]
def exempt(a, b):
    for t in np.linspace(0, 1, 7):
        p = a + (b - a) * t
        if plo[0] - 10 <= p[0] <= phi[0] + 10 and plo[2] - 10 <= p[1] <= phi[2] + 10: return 'Saltglass port (quay walls)'
        for q, nm in built:
            if np.hypot(p[0] - q[0], p[1] - q[2]) < 45: return nm
    return None
acc_p = f'{R}/world_merge/wobble_runs.json'; acc = json.load(open(acc_p)) if os.path.exists(acc_p) else []
ex = []
for s in json.load(open(RUNS)):
    a, b = np.array(s['a'], float), np.array(s['b'], float); why = exempt(a, b)
    if why: ex.append(dict(s, exempt=why)); continue
    if not any(np.allclose(a, q['a']) and np.allclose(b, q['b']) for q in acc): acc.append({'a': s['a'], 'b': s['b'], 'len_m': s['len_m'], 'seed': len(acc)})
json.dump(acc, open(acc_p, 'w'), indent=0); json.dump(ex, open(EX, 'w'), indent=1)
def field(P):
    off = np.zeros((len(P), 2))
    for q in acc:
        a, b = np.array(q['a'], float), np.array(q['b'], float); L = max(np.hypot(*(b - a)), 1); u = (b - a) / L; n = np.array([-u[1], u[0]])
        rel = P[:, [0, 2]] - a; t = rel @ u; e = rel @ n
        w = (1 - np.clip((np.abs(e) - 10) / 12, 0, 1)) * np.clip((t + 14) / 14, 0, 1) * np.clip((L + 14 - t) / 14, 0, 1)
        if not (w > 0).any(): continue
        k = q['seed'] * 1.7
        nz = 0.55 * np.sin(t / 30 * 6.283 + k) + 0.3 * np.sin(t / 17 * 6.283 + 2.1 * k) + 0.15 * np.sin(t / 9.5 * 6.283 + 0.7 * k)
        nz = nz + 0.35 * np.sign(np.sin(k + 0.5))   # whole run pushed a little in or out too
        off += (7.0 * nz * w)[:, None] * n[None, :]
    return off
lo = np.min([q['a'] for q in acc] + [q['b'] for q in acc], 0) - 40 if acc else None; hi = np.max([q['a'] for q in acc] + [q['b'] for q in acc], 0) + 40 if acc else None
files = []
for st, pre in (('stage1', 'arch_islands'), ('stage2', 'coast_tile_'), ('stage4', 'frost_tile_'), ('stage4', 'ash_tile_')):
    files += glob.glob(f'{R}/{st}/meshes/{pre}*.glb')
files += glob.glob(f'{R}/stage2/meshes/coast_terrain_col.glb') + glob.glob(f'{R}/stage4/meshes/frost_terrain_col.glb') + glob.glob(f'{R}/stage4/meshes/ash_terrain_col.glb')
files += [f for f in glob.glob(f'{R}/stage5_islands/meshes/*/*_isl_*.glb') if '_glow' not in f and 'saltglass_port' not in f]
n_files = 0
for f in sorted(set(files)):
    bdir = os.path.join(os.path.dirname(f), '..', 'meshes_v2_backup') if '/stage5_islands/' not in f else f.replace('/meshes/', '/meshes_v2_backup/').rsplit('/', 1)[0]
    os.makedirs(bdir, exist_ok=True); b = os.path.join(bdir, os.path.basename(f)); w0 = os.path.join(bdir, os.path.basename(f).replace('.glb', '_prewobble.glb'))
    if not os.path.exists(w0): shutil.copy(f, w0)   # pre-wobble state of this pipeline run
    s = trimesh.load(w0, force='scene'); moved = 0
    for node in s.graph.nodes_geometry:
        xf, gn = s.graph[node]; g = s.geometry[gn]; P = trimesh.transform_points(g.vertices, xf)
        if acc is None or not acc or P[:, 0].max() < lo[0] or P[:, 0].min() > hi[0] or P[:, 2].max() < lo[1] or P[:, 2].min() > hi[1]: continue
        o = field(P); mv = np.abs(o).sum(1) > 0.05
        if not mv.any(): continue
        P[:, 0] += o[:, 0]; P[:, 2] += o[:, 1]; g.vertices = trimesh.transform_points(P, np.linalg.inv(xf)); moved += int(mv.sum())
    if moved: s.export(f); n_files += 1
    elif open(w0, 'rb').read() != open(f, 'rb').read(): shutil.copy(w0, f)
print(len(acc), 'runs wobbled in', n_files, 'files;', len(ex), 'exempt (built)')
