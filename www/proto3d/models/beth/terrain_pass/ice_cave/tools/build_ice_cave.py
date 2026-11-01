"""Terrain pass fix 7 (Beth): Frost Troll Ice Cave ("frost" zone in cheats.gd). Built in the legacy frost-realm LOCAL frame so
PLACEMENT_frost_realm.json (80 cave-floor props) drops straight in: entrance tunnel at z~-58 (opening faces -z), a winding
gallery, and the troll arena chamber (~150 x 110 m) at z 90..200. Outputs ice_cave{,_lod1,_col}.glb + ice_cave_glow.glb + ice_cave.json.
Vertex colours only (snow 0.78, ice blue strata, dark rock skirt) -> no blown-out white."""
import json, math, os, sys, numpy as np, trimesh
OUT = sys.argv[1] if len(sys.argv) > 1 else '.'; rng = np.random.default_rng(7)
# centreline (x, z, width, height)
CL = np.array([(-8, -62, 12, 9), (-10, -40, 16, 11), (-16, -10, 30, 15), (-22, 25, 42, 19), (-18, 60, 60, 24),
               (-14, 95, 120, 32), (-14, 130, 160, 38), (-14, 165, 150, 36), (-14, 192, 90, 28), (-14, 206, 20, 12), (-14, 210, 3, 4)], float)
def n3(x, y, z, s):
    return (np.sin(x * 0.11 * s + 1.3) * np.cos(z * 0.09 * s - 0.7) + 0.6 * np.sin(y * 0.23 * s + x * 0.05 * s + 2.1) + 0.4 * np.sin((x + z) * 0.31 * s)) / 2.0
def build(step, nth, nfl, icicles):
    t = np.linspace(0, 1, len(CL)); L = np.cumsum(np.r_[0, np.linalg.norm(np.diff(CL[:, :2], axis=0), axis=1)])
    ss = np.arange(0, L[-1] + 1e-6, step)
    P = np.c_[[np.interp(ss, L, CL[:, k]) for k in range(4)]].T
    V, F, C = [], [], []; FV, FF, FC = [], [], []
    for i, (x, z, w, h) in enumerate(P):
        j = min(i + 1, len(P) - 1); k = max(i - 1, 0); d = P[j, :2] - P[k, :2]; d /= np.linalg.norm(d); nx = np.array([-d[1], d[0]])
        for a in range(nth + 1):
            th = math.pi * a / nth; r = 1 + 0.10 * n3(x, th * 20, z, 1.0) + 0.05 * n3(z, x, th * 40, 3.0)
            ox = w / 2 * math.cos(th) * r; oy = max(0.0, h * math.sin(th) * r) - 1.5 * (1 - math.sin(th))   # walls dip below floor
            px, pz = x + nx[0] * ox, z + nx[1] * ox; V.append((px, oy, pz))
            hgt = oy / max(h, 1); s = 0.5 + 0.5 * n3(px, oy * 3, pz, 2.0)
            c = np.array([0.30, 0.31, 0.35]) if oy < 1.8 else np.array([0.52, 0.66, 0.80]) * (0.78 + 0.18 * s) + np.array([0.08, 0.08, 0.06]) * hgt
            if 0.35 < s < 0.42: c = c * 0.8   # strata
            C.append(c)
        for b in range(nfl + 1):
            u = -0.5 + b / nfl; ox = u * w * 0.98; px, pz = x + nx[0] * ox, z + nx[1] * ox
            y = 0.35 * n3(px, 0, pz, 1.5) + 0.25 * n3(pz, px, 0, 4.0) - 0.4 * (abs(u) * 2) ** 4
            FV.append((px, y, pz)); s = 0.5 + 0.5 * n3(px, 1, pz, 3.0); FC.append(np.array([0.74, 0.77, 0.82]) * (0.92 + 0.1 * s))
    nr = nth + 1; nf = nfl + 1
    for i in range(len(P) - 1):
        for a in range(nth):
            p = i * nr + a; F += [(p, p + nr, p + 1), (p + 1, p + nr, p + nr + 1)]
        for b in range(nfl):
            p = i * nf + b; FF += [(p, p + 1, p + nf), (p + 1, p + nf + 1, p + nf)]
    def mk(v, f, c):
        m = trimesh.Trimesh(np.array(v), np.array(f), process=False); m.visual.vertex_colors = (np.clip(np.array(c), 0, 1) * 255).astype(np.uint8); return m
    shell = mk(V, F, C); floor = mk(FV, FF, FC)
    if np.mean(floor.face_normals[:, 1]) < 0: floor.invert()
    # shell normals should face inward (toward centreline): test one face
    fc = shell.triangles_center[len(F) // 2]; ii = (len(F) // 2) // (2 * nth); cen = np.array([P[ii, 0], 0, P[ii, 1]])
    if np.dot(shell.face_normals[len(F) // 2], cen - fc * np.array([1, 0, 1])) < 0: shell.invert()
    parts = [shell, floor]; glow = []; pillars = []
    if icicles:
        for _ in range(icicles):
            i = rng.integers(2, len(P) - 2); x, z, w, h = P[i]; th = rng.uniform(0.35, 2.8); j = min(i + 1, len(P) - 1); d = P[j, :2] - P[i - 1, :2]; d /= np.linalg.norm(d); nx = np.array([-d[1], d[0]])
            ox = w / 2 * math.cos(th) * 0.92; oy = h * math.sin(th) * 0.92; ln = rng.uniform(0.8, 4.5) * (h / 30 + 0.4); rad = ln * 0.14
            cn = trimesh.creation.cone(radius=rad, height=ln, sections=6); cn.apply_transform(trimesh.transformations.rotation_matrix(math.pi, [1, 0, 0]))
            cn.apply_translation((x + nx[0] * ox, oy, z + nx[1] * ox)); cn.visual.vertex_colors = np.tile([150, 190, 225, 255], (len(cn.vertices), 1)).astype(np.uint8); parts.append(cn)
        for (px, pz, r, hh) in [(-60, 120, 3.0, 36), (30, 135, 2.6, 36), (-40, 172, 2.4, 34), (20, 100, 2.2, 32), (-75, 150, 2.0, 30)]:
            cy = trimesh.creation.cylinder(radius=r, height=hh, sections=9); cy.apply_translation((px, hh / 2 - 1, pz))
            vv = cy.vertices; vv[:, 0] += 0.5 * np.sin(vv[:, 1] * 0.4); cy.vertices = vv
            cy.visual.vertex_colors = np.tile([120, 160, 200, 255], (len(cy.vertices), 1)).astype(np.uint8); parts.append(cy); pillars.append(cy)
        for _ in range(60):
            i = rng.integers(3, len(P) - 2); x, z, w, h = P[i]; u = rng.choice([-1, 1]) * rng.uniform(0.36, 0.47); j = min(i + 1, len(P) - 1); d = P[j, :2] - P[i - 1, :2]; d /= np.linalg.norm(d); nx = np.array([-d[1], d[0]])
            cr = trimesh.creation.cone(radius=rng.uniform(0.3, 0.8), height=rng.uniform(1.2, 3.2), sections=5)
            cr.apply_transform(trimesh.transformations.rotation_matrix(rng.uniform(-0.4, 0.4), [1, 0, 0])); cr.apply_translation((x + nx[0] * u * w, -0.2, z + nx[1] * u * w))
            cr.visual.vertex_colors = np.tile([140, 235, 255, 255], (len(cr.vertices), 1)).astype(np.uint8); glow.append(cr)
    return trimesh.util.concatenate(parts), floor, shell, pillars, (trimesh.util.concatenate(glow) if glow else None), P
hi, floor, shell, pillars, glow, P = build(2.0, 28, 24, 420)
lo, floor_lo, shell_lo, _, _, _ = build(4.0, 14, 12, 0)
os.makedirs(OUT, exist_ok=True)
hi.export(f'{OUT}/ice_cave.glb'); lo.export(f'{OUT}/ice_cave_lod1.glb'); glow.export(f'{OUT}/ice_cave_glow.glb')
col = trimesh.util.concatenate([floor_lo, shell_lo] + [p.copy() for p in pillars]); col.export(f'{OUT}/ice_cave_col.glb')
info = {'frame': 'frost-realm LOCAL (PLACEMENT_frost_realm.json frame). Place the root at CAVE_ORIGIN (README).',
        'entrance': [-8.0, 0.0, -58.0], 'spawn': [-10.0, 0.6, -45.0], 'spawn_yaw': 0.0, 'exit_trigger': {'pos': [-8.0, 1.0, -62.0], 'radius': 4.0},
        'arena_center': [-14.0, 0.0, 140.0], 'arena_radius': 60.0, 'troll_spawns': {'frosttroll_a': [-40.0, 0.0, 150.0], 'frosttroll_b': [15.0, 0.0, 160.0]},
        'lights': [[-10, 8, -40], [-18, 12, 10], [-20, 16, 55], [-14, 24, 110], [-50, 20, 150], [25, 20, 150], [-14, 22, 185]],
        'tris': {'hi': len(hi.faces), 'lod1': len(lo.faces), 'lod1_pct': round(100 * len(lo.faces) / len(hi.faces), 1), 'col': len(col.faces), 'glow': len(glow.faces)}}
json.dump(info, open(f'{OUT}/ice_cave.json', 'w'), indent=1); print(info['tris'])
