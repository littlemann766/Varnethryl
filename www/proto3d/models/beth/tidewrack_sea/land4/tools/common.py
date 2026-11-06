"""Shared glTF writer, noise and mesh helpers for land4. COLOR_0 stays uint8 normalized, same encoding as land1-3."""
import json, struct
import numpy as np

def write_glb(path, V, F, C, N=None, name='mesh'):
    V = np.asarray(V, np.float32); F = np.asarray(F, np.uint32).reshape(-1); C = np.asarray(C, np.float32)
    bufs = []; views = []; acc = []; off = 0
    def add(arr, target, comp, typ, count, mm=False):
        nonlocal off
        b = arr.tobytes(); pad = (-len(b)) % 4
        views.append(dict(buffer=0, byteOffset=off, byteLength=len(b), target=target))
        bufs.append(b + b'\0' * pad); off += len(b) + pad
        a = dict(bufferView=len(views) - 1, componentType=comp, count=count, type=typ)
        if mm:
            a['min'] = arr.reshape(count, -1).min(0).tolist(); a['max'] = arr.reshape(count, -1).max(0).tolist()
        acc.append(a); return len(acc) - 1
    attrs = {'POSITION': add(V, 34962, 5126, 'VEC3', len(V), True)}
    if N is not None:
        attrs['NORMAL'] = add(np.asarray(N, np.float32), 34962, 5126, 'VEC3', len(V))
    attrs['COLOR_0'] = add(np.clip(np.round(C * 255), 0, 255).astype(np.uint8), 34962, 5121, 'VEC4', len(V))
    acc[-1]['normalized'] = True
    ind = add(F, 34963, 5125, 'SCALAR', len(F))
    j = dict(asset=dict(version='2.0', generator='beth land4'), scene=0, scenes=[dict(nodes=[0])],
             nodes=[dict(mesh=0, name=name)],
             meshes=[dict(name=name, primitives=[dict(attributes=attrs, indices=ind, mode=4)])],
             accessors=acc, bufferViews=views, buffers=[dict(byteLength=off)])
    js = json.dumps(j, separators=(',', ':')).encode(); js += b' ' * ((-len(js)) % 4); bin_ = b''.join(bufs)
    with open(path, 'wb') as f:
        f.write(struct.pack('<III', 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(bin_)))
        f.write(struct.pack('<II', len(js), 0x4E4F534A)); f.write(js)
        f.write(struct.pack('<II', len(bin_), 0x004E4942)); f.write(bin_)

def _h(ix, iy, iz, seed):
    n = (ix * 73856093) ^ (iy * 19349663) ^ (iz * 83492791) ^ (seed * 2654435761)
    n = (n ^ (n >> 13)) * 1274126177; n = n ^ (n >> 16)
    return (n & 0xffff).astype(np.float64) / 65535.0

def vnoise(p, seed=0):
    p = np.asarray(p, np.float64); i = np.floor(p).astype(np.int64); f = p - i; u = f * f * (3 - 2 * f)
    r = 0
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                w = (u[:, 0] if dx else 1 - u[:, 0]) * (u[:, 1] if dy else 1 - u[:, 1]) * (u[:, 2] if dz else 1 - u[:, 2])
                r = r + w * _h(i[:, 0] + dx, i[:, 1] + dy, i[:, 2] + dz, seed)
    return r * 2 - 1

def fbm(p, oct=4, seed=0):
    a = 0.5; s = 0; p = np.asarray(p, np.float64)
    for o in range(oct):
        s = s + a * vnoise(p, seed + o); p = p * 2.03 + 17.1; a *= 0.5
    return s

def face_normals(V, F):
    fn = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
    ln = np.linalg.norm(fn, axis=1, keepdims=True) + 1e-12
    return fn / ln

def vnormals(V, F):
    fn = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
    N = np.zeros_like(V)
    for i in range(3):
        np.add.at(N, F[:, i], fn)
    N /= np.linalg.norm(N, axis=1, keepdims=True) + 1e-12
    N[N[:, 1] < 0] *= -1
    return N

def slope_deg(n):
    return np.degrees(np.arccos(np.clip(np.abs(n[:, 1]), 0, 1)))

def unique_edges(F):
    E = np.sort(np.concatenate([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]]), 1)
    u, c = np.unique(E, axis=0, return_counts=True)
    return u, c

def subdivide(V, F, C, W, mark):
    """Midpoint-subdivide marked faces. A face with two split edges is closed to three. New weight = min of endpoints."""
    if not np.any(mark):
        return V, F, C, W
    nV = len(V)
    E = np.sort(np.stack([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]], 1), 2)
    key = E[:, :, 0].astype(np.int64) * (nV + 1) + E[:, :, 1]
    split = set(key[mark].ravel().tolist())
    while True:
        s = np.isin(key, np.fromiter(split, dtype=np.int64, count=len(split))).sum(1)
        add = (s == 2)
        if not add.any():
            break
        split.update(key[add].ravel().tolist())
    sk = np.fromiter(split, dtype=np.int64); sk.sort()
    a = sk // (nV + 1); b = sk % (nV + 1)
    mid = np.arange(nV, nV + len(sk))
    V2 = np.concatenate([V, (V[a] + V[b]) * 0.5])
    C2 = np.concatenate([C, (C[a] + C[b]) * 0.5])
    W2 = np.concatenate([W, np.minimum(W[a], W[b])])
    def ek(u, v):
        lo = np.minimum(u, v); hi = np.maximum(u, v)
        return lo.astype(np.int64) * (nV + 1) + hi
    def lookup(e):
        i = np.searchsorted(sk, e)
        ok = (i < len(sk)) & (sk[np.minimum(i, len(sk) - 1)] == e)
        return np.where(ok, mid[np.minimum(i, len(sk) - 1)], -1)
    m01 = lookup(ek(F[:, 0], F[:, 1])); m12 = lookup(ek(F[:, 1], F[:, 2])); m20 = lookup(ek(F[:, 2], F[:, 0]))
    n = (m01 >= 0).astype(np.int32) + (m12 >= 0).astype(np.int32) + (m20 >= 0).astype(np.int32)
    out = [F[n == 0]]
    s3 = n == 3
    f = F[s3]; aa, bb, cc = m01[s3], m12[s3], m20[s3]
    if len(f):
        out += [np.stack([f[:, 0], aa, cc], 1), np.stack([aa, f[:, 1], bb], 1),
                np.stack([cc, bb, f[:, 2]], 1), np.stack([aa, bb, cc], 1)]
    s1 = n == 1
    for mm, (i0, i1, i2) in ((m01, (0, 1, 2)), (m12, (1, 2, 0)), (m20, (2, 0, 1))):
        sel = s1 & (mm >= 0)
        f = F[sel]; x = mm[sel]
        if len(f):
            out += [np.stack([f[:, i0], x, f[:, i2]], 1), np.stack([x, f[:, i1], f[:, i2]], 1)]
    if np.any(n == 2):
        # should have been closed; leave those faces unsplit rather than invent a T-junction
        out.append(F[n == 2])
    F2 = np.concatenate([o for o in out if len(o)], 0).astype(np.int64)
    return V2, F2, C2, W2
