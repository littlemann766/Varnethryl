#!/usr/bin/env python3
"""Compare images: [boss beauty render | 3D exterior | 3D interior | 3D upstairs] -> /workspace/shots/buildings/compare/<id>.png  (run capture_buildings.py first)"""
import os, sys
from PIL import Image, ImageDraw
D = '/workspace/shots/buildings'; R = '/workspace/refs'; os.makedirs(D + '/compare', exist_ok=True)
ids = os.environ.get('ONLY', '').split(',') if os.environ.get('ONLY') else sorted(f[:-4] for f in os.listdir(R))
for i in ids:
    if not os.path.exists(f'{D}/{i}_ext.png'): continue
    ref = Image.open(f'{R}/{i}.jpg').convert('RGB') if os.path.exists(f'{R}/{i}.jpg') else Image.new('RGB', (900, 600), (30, 30, 30))
    tiles = [('reference', ref), ('3D front', Image.open(f'{D}/{i}_front.png') if __import__('os').path.exists(f'{D}/{i}_front.png') else Image.open(f'{D}/{i}_ext.png')), ('3D 3/4 view', Image.open(f'{D}/{i}_ext.png'))]
    ups = sorted(f for f in os.listdir(D) if f.startswith(i + '_up') and f.endswith('.png'))
    tiles.append(('3D interior', Image.open(f'{D}/{i}_int.png')))
    for u in []: tiles.append(('3D upstairs', Image.open(f'{D}/{u}')))
    TW, TH = 800, 534; ims = []
    for n, im in tiles:
        im = im.convert('RGB'); im = im.resize((TW, TH), Image.LANCZOS); ImageDraw.Draw(im).rectangle((0, 0, 190, 18), fill=(0, 0, 0)); ImageDraw.Draw(im).text((4, 3), f'{i}: {n}', fill=(255, 255, 255)); ims.append(im)
    out = Image.new('RGB', (TW * 2, TH * 2), (20, 20, 24))
    for k, im in enumerate(ims[:4]): out.paste(im, ((k % 2) * TW, (k // 2) * TH))
    out.save(f'{D}/compare/{i}.png')
print('ok')
