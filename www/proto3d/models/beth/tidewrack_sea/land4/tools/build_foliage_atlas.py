"""Build the scatter cutout atlas from CC0 ambientCG photos.

Sources, all CC0 1.0, https://ambientcg.com :
  Bark012 color + OpenGL normal  (trunks; copied beside this atlas)
  Foliage001 color + opacity     (grass blades and pine-needle fans)
  LeafSet001 color + opacity     (broadleaf and bush sprigs)

Flower heads are painted here. They are not a third-party texture.
The atlas is 4x2 cells of 512. Transparent texels get their neighbours'
colour so mipmaps do not fringe grey.
"""
import os
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.environ.get("FOLIAGE_SRC", "/tmp/cc0")
CELL = 512
COLS, ROWS = 4, 2


def sprites(color_path, opacity_path, min_px):
    col = np.asarray(Image.open(color_path).convert("RGB"))
    op = np.asarray(Image.open(opacity_path).convert("L"))
    mask = op > 28
    lab, n = ndimage.label(mask)
    out = []
    for i in range(1, n + 1):
        ys, xs = np.nonzero(lab == i)
        if len(xs) < min_px:
            continue
        x0, x1 = int(xs.min()), int(xs.max()) + 1
        y0, y1 = int(ys.min()), int(ys.max()) + 1
        sl = lab[y0:y1, x0:x1] == i
        rgba = np.zeros((y1 - y0, x1 - x0, 4), np.uint8)
        rgb = col[y0:y1, x0:x1].astype(np.float32)
        # Keep the vein photograph, pull it to a forest green so a card is a leaf clump.
        rgba[:, :, :3] = np.clip(rgb * np.array([0.62, 0.92, 0.42]), 0, 255).astype(np.uint8)
        a = op[y0:y1, x0:x1].astype(np.float32)
        a[~sl] = 0
        rgba[:, :, 3] = np.clip(a * 1.35, 0, 255).astype(np.uint8)
        out.append(rgba)
    out.sort(key=lambda s: s.shape[0] * s.shape[1], reverse=True)
    return out


def paste(canvas, sprite, cx, cy, angle, scale):
    im = Image.fromarray(sprite, "RGBA")
    w = max(1, int(im.width * scale))
    h = max(1, int(im.height * scale))
    im = im.resize((w, h), Image.Resampling.LANCZOS)
    im = im.rotate(angle, expand=True, resample=Image.Resampling.BICUBIC)
    canvas.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))


def cell():
    return Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))


def _thin(sp):
    return np.asarray(Image.fromarray(sp, "RGBA").resize(
        (max(1, sp.shape[1] // 3), sp.shape[0]), Image.Resampling.LANCZOS))


def _disk_mask(im, power=1.1):
    a = np.asarray(im).copy()
    h, w = a.shape[:2]
    y, x = np.mgrid[0:h, 0:w]
    nx = (x / (w - 1)) * 2 - 1
    ny = (y / (h - 1)) * 2 - 1
    fall = np.clip(1.08 - np.sqrt(nx ** 2 + ny ** 2), 0, 1) ** power
    a[:, :, 3] = np.clip(a[:, :, 3].astype(np.float32) * fall, 0, 255).astype(np.uint8)
    return Image.fromarray(a, "RGBA")


def needle_fan(blades, seed):
    """A packed bough. The middle is needles, the edge frays into tips."""
    rng = np.random.default_rng(seed)
    im = cell()
    for i in range(64):
        t = rng.random()
        ang = rng.uniform(-88, 88)
        sp = _thin(blades[i % len(blades)])
        scale = rng.uniform(0.28, 0.55)
        cx = CELL * (0.5 + rng.uniform(-0.28, 0.28) * (0.35 + t))
        cy = CELL * rng.uniform(0.18, 0.82)
        paste(im, sp, cx, cy, ang, scale)
    a = np.asarray(im).copy()
    h, w = a.shape[:2]
    y, x = np.mgrid[0:h, 0:w]
    # wide at the bottom of the image, pointed at the top
    ny = y / (h - 1)
    nx = np.abs((x / (w - 1)) * 2 - 1)
    half = 0.18 + 0.78 * ny
    fall = np.clip((half - nx) / 0.18, 0, 1)
    a[:, :, 3] = np.clip(a[:, :, 3].astype(np.float32) * fall, 0, 255).astype(np.uint8)
    return Image.fromarray(a, "RGBA")


def leaf_sprig(leaves, seed, dense):
    """Enough real leaves to fill a card, with a ragged round edge."""
    rng = np.random.default_rng(seed)
    im = cell()
    n = 46 if dense else 34
    for i in range(n):
        sp = leaves[i % len(leaves)]
        ang = rng.uniform(0, 360)
        scale = rng.uniform(0.22, 0.42) if dense else rng.uniform(0.26, 0.48)
        cx = CELL * (0.5 + rng.uniform(-0.34, 0.34))
        cy = CELL * (0.5 + rng.uniform(-0.34, 0.34))
        paste(im, sp, cx, cy, ang, scale)
    return _disk_mask(im, 0.85 if dense else 1.05)


def grass_tuft(blades, seed):
    rng = np.random.default_rng(seed)
    im = cell()
    for i in range(14):
        ang = rng.uniform(-28, 28)
        sp = blades[i % len(blades)]
        scale = rng.uniform(0.34, 0.52)
        cx = CELL * (0.5 + rng.uniform(-0.12, 0.12))
        cy = CELL * rng.uniform(0.42, 0.58)
        paste(im, sp, cx, cy, ang, scale)
    return im


def flower(kind):
    im = cell()
    layer = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    petals = {"y": (236, 186, 48, 255), "w": (242, 240, 232, 255), "p": (206, 86, 112, 255)}[kind]
    center = {"y": (92, 58, 18, 255), "w": (214, 164, 42, 255), "p": (120, 36, 58, 255)}[kind]
    cx = cy = CELL // 2
    for i in range(7):
        ang = i / 7 * 360.0
        pet = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
        d = ImageDraw.Draw(pet)
        d.ellipse([cx - 46, cy - 150, cx + 46, cy - 8], fill=petals)
        # a slightly darker vein
        vein = tuple(max(0, c - 30) if k < 3 else c for k, c in enumerate(petals))
        d.line([(cx, cy - 20), (cx, cy - 130)], fill=vein, width=3)
        pet = pet.rotate(ang, center=(cx, cy), resample=Image.Resampling.BICUBIC)
        layer.alpha_composite(pet)
    d = ImageDraw.Draw(layer)
    d.ellipse([cx - 38, cy - 38, cx + 38, cy + 38], fill=center)
    d.ellipse([cx - 16, cy - 18, cx + 14, cy + 12], fill=tuple(min(255, c + 40) if k < 3 else c for k, c in enumerate(center)))
    return layer


def bleed(im):
    a = np.asarray(im).copy()
    opaque = a[:, :, 3] > 8
    if not opaque.any():
        return im
    _, idx = ndimage.distance_transform_edt(~opaque, return_indices=True)
    rgb = a[:, :, :3]
    a[:, :, :3] = rgb[idx[0], idx[1]]
    return Image.fromarray(a, "RGBA")


def main():
    blades = sprites(os.path.join(SRC, "grass/Foliage001_1K-PNG_Color.png"),
                     os.path.join(SRC, "grass/Foliage001_1K-PNG_Opacity.png"), 800)
    leaves = sprites(os.path.join(SRC, "leaves/LeafSet001_1K-PNG_Color.png"),
                     os.path.join(SRC, "leaves/LeafSet001_1K-PNG_Opacity.png"), 400)
    if len(blades) < 4 or len(leaves) < 4:
        raise SystemExit(f"sprites blades={len(blades)} leaves={len(leaves)}")
    cells = [
        needle_fan(blades, 1),
        needle_fan(blades, 2),
        leaf_sprig(leaves, 3, False),
        leaf_sprig(leaves, 4, True),
        grass_tuft(blades, 5),
        flower("y"),
        flower("w"),
        flower("p"),
    ]
    atlas = Image.new("RGBA", (CELL * COLS, CELL * ROWS), (0, 0, 0, 0))
    for i, im in enumerate(cells):
        c, r = i % COLS, i // COLS
        # Bleed inside the cell only, so a mip does not pull the daisy into the leaves.
        atlas.paste(bleed(im), (c * CELL, r * CELL))
    out = os.path.join(ROOT, "textures", "foliage_atlas.png")
    atlas.save(out, optimize=True)
    print("atlas", out, atlas.size, "bytes", os.path.getsize(out))


if __name__ == "__main__":
    main()
