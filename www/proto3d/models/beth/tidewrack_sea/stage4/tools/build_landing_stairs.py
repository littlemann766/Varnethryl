"""Terrain pass fix 6 (Beth): built stone landing stairs for the 4 high landings (shore y 14-18 m on a sheer cliff), so the
generated 18-deg pier board is no longer needed. Each: a level stone bridge over the cliff rim, a 19-deg stepped masonry
stair-ramp on arched piers down to a timber jetty at y 1.4 over 8+ m deep water, mooring posts + lanterns.
Outputs <prefix>landing_<id>{.glb,_lod1.glb,_col.glb} into stage4/meshes (auto-loaded by tw_sea._files) + landing_stairs.json.
Needs ../landing_rim_profiles.json (cliff-top raycast profile from tools/probe_land.gd).
Run: python3 build_landing_stairs.py <landings.json> <out_meshes_dir>"""
import json, math, sys, os, numpy as np, trimesh
L = json.load(open(sys.argv[1])); OUT = sys.argv[2]
RIM = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'landing_rim_profiles.json')))
IDS = {'vent': 'ash_', 'aurora_arch': 'frost_', 'hot_spring': 'ash_', 'obsidian_arch': 'ash_'}
G = math.tan(math.radians(19.0)); W = 3.2; DECK_Y = 1.4
STONE = (0.50, 0.47, 0.43); STONE2 = (0.40, 0.38, 0.35); WOOD = (0.42, 0.30, 0.19); WOOD2 = (0.33, 0.23, 0.14); IRON = (0.15, 0.15, 0.16); GLOW = (1.0, 0.78, 0.45)
FROST = {'STONE': (0.62, 0.66, 0.72), 'STONE2': (0.50, 0.55, 0.62)}
def obox(c, d, n, size, col, parts):
    """oriented box: centre c, length axis d (unit xz), size (len, h, w)"""
    m = trimesh.creation.box(extents=(size[1], size[0], size[2]))   # placeholder axes, rebuilt below
    m = trimesh.creation.box(extents=size)
    R = np.eye(4); R[:3, 0] = d; R[:3, 1] = (0, 1, 0); R[:3, 2] = n; R[:3, 3] = c
    m.apply_transform(R); m.visual.vertex_colors = np.tile(np.array([*[int(v * 255) for v in col], 255], np.uint8), (len(m.vertices), 1)); parts.append(m)
def build(id_, pre):
    E = L[id_]; S = np.array(E['shore'], float); inl = np.array([E['inland'][0], 0, E['inland'][1]]); inl /= np.linalg.norm(inl)
    d = -inl; n = np.array([-d[2], 0, d[0]])
    st, st2 = (FROST['STONE'], FROST['STONE2']) if pre == 'frost_' else (STONE, STONE2)
    vis, col = [], []
    prof = RIM[id_]['dirs']['0']; ts = [-12 + 0.5 * i for i in range(len(prof))]   # cliff-top profile along d (t = -12..8 m)
    ytop = max(h for t, h in zip(ts, prof) if -3.0 <= t <= 3.5) + 0.03; t0, t1 = -3.0, 3.0   # level bridge flush with the landing pad
    t1 = 3.0
    while any(ytop - (t - t1) * G < h + 0.08 for t, h in zip(ts, prof) if t > t1): t1 += 0.5   # push the stair head past the rim
    AL = 6.0
    while AL < 9.0 and (ytop - prof[ts.index(-3.0 - AL)]) / AL > math.tan(math.radians(19)): AL += 1.0
    yin = prof[ts.index(-3.0 - AL)] + 0.02                                      # inland approach: slab from the pad down/up to the path at t=-9
    L1 = (ytop - DECK_Y) / G; t2 = t1 + L1; t3 = t2 + 9.0                    # ramp, then jetty
    def P(t, y): return S + d * t + np.array([0, y - S[1], 0])
    # bridge deck
    obox(P((t0 + t1) / 2, ytop - 0.3), d, n, (t1 - t0, 0.6, W), st, vis); obox(P((t0 + t1) / 2, ytop - 0.3), d, n, (t1 - t0, 0.6, W), st, col)
    ai = trimesh.creation.box(extents=(math.hypot(AL, ytop - yin) + 0.2, 0.5, W)); aang = math.atan2(ytop - yin, AL); ad = d * math.cos(aang) + np.array([0, 1.0, 0]) * math.sin(aang)
    au = np.cross(np.cross(ad, [0, 1, 0]), ad); au = au / np.linalg.norm(au); au = au if au[1] > 0 else -au
    R = np.eye(4); R[:3, 0] = ad; R[:3, 1] = au; R[:3, 2] = np.cross(ad, au); R[:3, 3] = P(-3.0 - AL / 2, (ytop + yin) / 2) - au * 0.25; ai.apply_transform(R)
    ai.visual.vertex_colors = np.tile(np.array([*[int(v * 255) for v in st2], 255], np.uint8), (len(ai.vertices), 1)); vis.append(ai); col.append(ai.copy())
    # ramp: collision = one smooth inclined slab; visual = stepped treads (0.17 m risers) on a solid masonry body
    ang = math.atan(G); Lr = L1 / math.cos(ang); mid = P((t1 + t2) / 2, (ytop + DECK_Y) / 2 - 0.3)
    dd = d * math.cos(ang) - np.array([0, 1, 0]) * math.sin(ang); up = np.cross(n, dd) * -1; up = up / np.linalg.norm(up)
    if up[1] < 0: up = -up
    def oslab(c, size, colr, parts):
        m = trimesh.creation.box(extents=size); R = np.eye(4); R[:3, 0] = dd; R[:3, 1] = up; R[:3, 2] = np.cross(dd, up); R[:3, 3] = c; m.apply_transform(R)
        m.visual.vertex_colors = np.tile(np.array([*[int(v * 255) for v in colr], 255], np.uint8), (len(m.vertices), 1)); parts.append(m)
    oslab(mid, (Lr, 0.6, W), st, col)
    nst = int((ytop - DECK_Y) / 0.17); run = L1 / nst
    for k in range(nst):
        y = ytop - (k + 1) * (ytop - DECK_Y) / nst; tc = t1 + (k + 0.5) * run
        obox(P(tc, y - 0.25), d, n, (run + 0.02, 0.5 + 0.0, W), st if k % 2 else st2, vis)
    # solid masonry body under the ramp down to the cliff/sea, as stacked piers every ~6 m with arches between
    npier = max(2, int(L1 / 6.5))
    for k in range(npier + 1):
        tc = t1 + L1 * k / npier; ytc = ytop - (tc - t1) * G
        h = ytc + 16.0; obox(P(tc, ytc - h / 2 - 0.4), d, n, (1.6, h, W + 0.6), st2, vis); obox(P(tc, ytc - h / 2 - 0.4), d, n, (1.6, h, W + 0.6), st2, col)
    # parapets (both sides) along bridge + ramp, 0.9 m tall, with a gap-free top so the capsule can't fall
    for side in (1, -1):
        for seg in range(nst):
            y = ytop - (seg + 0.5) * (ytop - DECK_Y) / nst; tc = t1 + (seg + 0.5) * run
            obox(P(tc, y + 0.45) + n * side * (W / 2 + 0.15), d, n, (run + 0.05, 0.9, 0.3), st2, vis)
        oslab(mid + n * side * (W / 2 + 0.15) + up * 0.75, (Lr, 0.9, 0.3), st2, col)
        obox(P((t0 + t1) / 2, ytop + 0.45) + n * side * (W / 2 + 0.15), d, n, (t1 - t0, 0.9, 0.3), st2, vis); obox(P((t0 + t1) / 2, ytop + 0.45) + n * side * (W / 2 + 0.15), d, n, (t1 - t0, 0.9, 0.3), st2, col)
    # timber jetty at the foot: planks + posts + mooring bollards + lanterns
    obox(P((t2 + t3) / 2, DECK_Y - 0.12), d, n, (t3 - t2, 0.24, W + 0.6), WOOD, col)
    for k in range(int((t3 - t2) / 0.5)):
        obox(P(t2 + 0.25 + k * 0.5, DECK_Y - 0.1), d, n, (0.46, 0.2, W + 0.6), WOOD if k % 2 else WOOD2, vis)
    for k in range(4):
        tc = t2 + (t3 - t2) * k / 3
        for side in (1, -1):
            obox(P(tc, DECK_Y - 6.0) + n * side * (W / 2 + 0.2), d, n, (0.35, 13.0, 0.35), WOOD2, vis)
    for side in (1, -1):
        obox(P(t3 - 0.6, DECK_Y + 0.35) + n * side * (W / 2), d, n, (0.4, 0.7, 0.4), IRON, vis)
        obox(P(t2 + 0.5, DECK_Y + 1.4) + n * side * (W / 2 + 0.2), d, n, (0.16, 2.8, 0.16), WOOD2, vis); obox(P(t2 + 0.5, DECK_Y + 2.9) + n * side * (W / 2 + 0.2), d, n, (0.3, 0.35, 0.3), GLOW, vis)
        obox(P(t1, ytop + 1.4) + n * side * (W / 2 + 0.15), d, n, (0.16, 2.8, 0.16), WOOD2, vis); obox(P(t1, ytop + 2.9) + n * side * (W / 2 + 0.15), d, n, (0.3, 0.35, 0.3), GLOW, vis)
    V = trimesh.util.concatenate(vis); C = trimesh.util.concatenate(col)
    base = os.path.join(OUT, f'{pre}landing_{id_}')
    V.export(base + '.glb'); C.export(base + '_col.glb')
    # lod1: drop the per-step treads + plank strips (keep the collision-shape slabs as visual)
    lo = [m for m in vis if len(m.faces) == 12 and m.extents.max() > 1.2]
    lod1 = trimesh.util.concatenate(lo + [c.copy() for c in col])
    if len(lod1.faces) > 0.5 * len(V.faces): lod1 = trimesh.util.concatenate([c.copy() for c in col])
    lod1.export(base + '_lod1.glb')
    moor = P(t3 + 5.0, 0.0); spawn = P(t3 - 1.5, DECK_Y + 0.1)
    route = [[round(float(v), 2) for v in P(t3 - 1.5, DECK_Y + 0.1)], [round(float(v), 2) for v in P(t2, DECK_Y + 0.1)], [round(float(v), 2) for v in P(t1, ytop + 0.05)], [round(float(v), 2) for v in P(-4.0 - AL, yin + 0.05)]]
    info = {'jetty': f'{pre}landing_{id_}', 'moor': [round(float(v), 2) for v in moor], 'shore': E['shore'], 'spawn': [round(float(v), 2) for v in spawn], 'inland': E['inland'],
            'pier_m': round(float(np.linalg.norm((moor - S)[[0, 2]])), 1), 'inland_target': [round(float(v), 2) for v in P(-4.0 - AL, yin)], 'inland_route': route,
            'stair_head_t': t1, 'approach_m': AL, 'stair': {'deg': 19.0, 'len_m': round(float(L1), 1), 'rise_m': round(float(ytop - DECK_Y), 1)}, 'tris': len(V.faces), 'lod1_tris': len(lod1.faces), 'lod1_pct': round(100 * len(lod1.faces) / len(V.faces), 1)}
    print(id_, info['stair'], info['tris'], info['lod1_pct'], '%'); return info
if __name__ == '__main__':
    res = {k: build(k, p) for k, p in IDS.items()}
    json.dump(res, open(os.path.join(OUT, '..', 'landing_stairs.json'), 'w'), indent=1)
