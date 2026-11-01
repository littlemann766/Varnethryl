"""Terrain pass fix 8d (Beth): carved waystone (fast-travel stone), 3.2 m tall, with a glowing rune band (separate emissive mesh).
Outputs waystone{,_lod1,_col,_glow}.glb."""
import numpy as np, trimesh, math
def col(m, c): m.visual.vertex_colors = np.tile(np.array([*c, 255], np.uint8), (len(m.vertices), 1)); return m
def stone(sections, sub):
    s = trimesh.creation.cylinder(radius=0.55, height=3.2, sections=sections); s = s.subdivide() if sub else s
    v = np.array(s.vertices); t = (v[:, 2] + 1.6) / 3.2
    v[:, 0] *= 1.0 - 0.35 * t; v[:, 1] *= 0.75 - 0.25 * t
    v[:, :2] *= (1 + 0.06 * np.sin(v[:, 2] * 4.1 + np.arctan2(v[:, 1], v[:, 0]) * 3))[:, None]
    v[:, 2] += 1.6; s.vertices = v[:, [0, 2, 1]]
    s.faces = s.faces[:, [0, 2, 1]]; s.fix_normals()
    return col(s, (118, 112, 104))
base = col(trimesh.creation.cylinder(radius=1.1, height=0.35, sections=10), (90, 86, 80)); base.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, [1, 0, 0])); base.apply_translation((0, 0.05, 0))
hi = trimesh.util.concatenate([stone(12, True), base]); lo = trimesh.util.concatenate([stone(7, False), base.copy()])
glow = []
for k in range(6):
    a = k / 6 * math.tau; g = col(trimesh.creation.box(extents=(0.14, 0.32, 0.04)), (150, 230, 255))
    r = 0.47; g.apply_transform(trimesh.transformations.rotation_matrix(-a, [0, 1, 0])); g.apply_translation((math.sin(a) * r * 0.95, 1.9, math.cos(a) * r * 0.7)); glow.append(g)
hi.export('waystone.glb'); lo.export('waystone_lod1.glb'); trimesh.util.concatenate(glow).export('waystone_glow.glb')
c = trimesh.creation.cylinder(radius=0.6, height=3.0, sections=8); c.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, [1, 0, 0])); c.apply_translation((0, 1.5, 0)); c.export('waystone_col.glb')
print(len(hi.faces), len(lo.faces), round(100 * len(lo.faces) / len(hi.faces)))
