#!/usr/bin/env python3
"""Derive gold-on-transparent heraldry decals (lion, fleur-de-lis) from the boss's Sir Aldric sheet shield. Output: www/proto3d/tex/emb_*.png (white-ish luminance + alpha; tinted by material colour)."""
from PIL import Image, ImageFilter
import numpy as np
im = Image.open('/workspace/sheets/aldric.jpg').convert('RGB')
crop = im.crop((385, 800, 565, 1090)).resize((360, 580), Image.LANCZOS)
a = np.asarray(crop).astype(float)
R, G, B = a[..., 0], a[..., 1], a[..., 2]
gold = np.clip((R - B - 25) / 60, 0, 1)
def out(box, name, size):
    x0, y0, x1, y1 = box
    m = np.zeros_like(gold); m[y0:y1, x0:x1] = gold[y0:y1, x0:x1]
    lum = (R * .3 + G * .5 + B * .2); lum = np.clip(lum / 190, .75, 1.1) / 1.1 * 1.0
    from scipy import ndimage
    lab, n = ndimage.label(m > .45); sizes = ndimage.sum(m > .45, lab, range(1, n + 1)); keep = np.isin(lab, [i + 1 for i, v in enumerate(sizes) if v > 0.02 * max(sizes)]); m = m * ndimage.binary_dilation(keep, iterations=2)
    al = Image.fromarray((m * 255).astype('uint8')).filter(ImageFilter.GaussianBlur(1.2))
    al = al.point(lambda v: 255 if v > 110 else int(max(0, (v - 70) * 255 / 40)))
    rgb = Image.fromarray((np.stack([lum] * 3, -1) * 255).astype('uint8'))
    img = Image.merge('RGBA', (*rgb.split(), al)); bb = al.getbbox(); img = img.crop(bb)
    s = max(img.size); sq = Image.new('RGBA', (s, s), (255, 255, 255, 0)); sq.paste(img, ((s - img.width) // 2, (s - img.height) // 2))
    sq.resize((size, size), Image.LANCZOS).save(f'www/proto3d/tex/{name}.png'); print(name, bb)
out((28, 58, 332, 432), 'emb_lion', 256)
out((130, 436, 215, 548), 'emb_fleur', 128)
