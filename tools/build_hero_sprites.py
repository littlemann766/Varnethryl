#!/usr/bin/env python3
"""Cut the 20 hero cards into full-body painted in-world sprites (www/assets/sprites/N.png).
Needs: pip install rembg onnxruntime scipy pillow numpy.  Originals of the old flat sprites live in assets/sprites-old-flat/."""
import sys, pathlib, numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage as ndi
ROOT = pathlib.Path(__file__).resolve().parents[1]
W, H, FEET_PAD, FIG_H, FIG_W = 186, 250, 6, 236, 180   # canvas, feet margin, max figure size (same ratio as the draw rect 52x70)
def cut(card, session, box=(0, 0, 620, 545)):
    from rembg import remove
    im = card.convert('RGB').crop(box)        # figure area; below is the stat plate
    return remove(im, session=session)
def clean(rgba, fill=True):
    a = np.array(rgba); al = a[..., 3]
    m = al > 100
    lab, n = ndi.label(ndi.binary_dilation(m, iterations=3))
    if n:
        sizes = ndi.sum(m, lab, range(1, n + 1)); keep = [i + 1 for i, s in enumerate(sizes) if s > 0.04 * sizes.max()]
        m = m & np.isin(lab, keep)
    if fill: m = ndi.binary_fill_holes(m)
    soft = ndi.gaussian_filter(ndi.binary_erosion(m, iterations=1).astype(float), 0.8)   # crisp but anti-aliased edge, kills halo
    a[..., 3] = (soft * 255).astype(np.uint8)
    # kill light halo: pull edge colours toward the interior
    edge = (soft > 0) & (soft < 0.98)
    blur = np.stack([ndi.gaussian_filter(np.where(m, a[..., c], 0).astype(float), 2) / np.maximum(ndi.gaussian_filter(m.astype(float), 2), 1e-3) for c in range(3)], -1)
    a[..., :3][edge] = blur[edge].astype(np.uint8)
    return Image.fromarray(a)
def place(fig, W=W, H=H, FEET_PAD=FEET_PAD, FIG_H=FIG_H, FIG_W=FIG_W):
    fig = fig.crop(fig.getbbox()); s = min(FIG_H / fig.height, FIG_W / fig.width)
    fig = fig.resize((max(1, round(fig.width * s)), max(1, round(fig.height * s))), Image.LANCZOS)
    out = Image.new('RGBA', (W, H), (0, 0, 0, 0)); out.alpha_composite(fig, ((W - fig.width) // 2, H - FEET_PAD - fig.height)); return out
if __name__ == '__main__':
    from rembg import new_session
    sess = new_session('isnet-general-use'); ids = [int(x) for x in sys.argv[1:]] or range(20)
    for i in ids:
        card = Image.open(ROOT / f'www/assets/heroes/{i}.webp')
        place(clean(cut(card, sess))).save(ROOT / f'www/assets/sprites/{i}.png', optimize=True); print('sprite', i)
