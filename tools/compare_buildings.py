#!/usr/bin/env python3
"""Sheet-vs-3D comparison images: /workspace/shots/buildings/compare_<id>.png = [boss sheet | 3D exterior | 3D interior cutaway]."""
import sys
from PIL import Image, ImageDraw
D = '/workspace/shots/buildings'; import os; os.makedirs(D + '/compare', exist_ok=True); S = '/workspace/sheets/bld/'
SHEET = dict(guildhall='g5', library='g3', townhall='d', mage='a', treasury='c', keep='e', observatory='f5', crypt='f6', market='g4', apothecary='apothecary', bakery='f4', inn='inn', smithy='smithy', temple='temple', training='training', colosseum='colosseum', thieves='g2', farmhouse='h2', barn='h2', stables='b', windmill='g1', house1='h3', house2='h3', house3='h3', house4='h3', lighthouse='h1', port='f2', gatehouse='f1', fountain='f3')
BEAUTY = dict(inn='beauty_inn', smithy='beauty_smithy', apothecary='beauty_apothecary', temple='beauty_temple', mage='beauty_mage', training='beauty_training')
for i, s in SHEET.items():
    sh = Image.open(S + s + '.jpg').convert('RGB'); sh = sh.resize((int(sh.width * 640 / sh.height), 640))
    ext = Image.open(f'{D}/{i}_ext.png').resize((640, 455)); it = Image.open(f'{D}/{i}_int.png').resize((640, 455))
    W = sh.width + 640 * 1; out = Image.new('RGB', (sh.width + 640, 640 + 0), (22, 20, 26)); out.paste(sh, (0, 0)); out.paste(ext, (sh.width, 0)); out.paste(it, (sh.width, 185)) if False else None
    out = Image.new('RGB', (sh.width + 640, 640), (22, 20, 26)); out.paste(sh, (0, 0)); out.paste(ext.resize((640, 320)), (sh.width, 0)); out.paste(it.resize((640, 320)), (sh.width, 320))
    ImageDraw.Draw(out).text((sh.width + 8, 6), f'{i}: 3D exterior (top) / interior cutaway (bottom)', fill=(255, 255, 255)); out.save(f'{D}/compare/{i}.png')
print('ok')
