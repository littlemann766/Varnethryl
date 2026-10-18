#!/usr/bin/env python3
"""Contact sheets: ids from argv -> /workspace/shots/buildings/_m_N.png (ext | int per row, 4 rows)."""
import sys
from PIL import Image, ImageDraw
D = '/workspace/shots/buildings'; ids = sys.argv[2:]; tag = sys.argv[1]
for k in range(0, len(ids), 4):
    ch = ids[k:k + 4]; sh = Image.new('RGB', (1000, 330 * len(ch)), (20, 20, 24))
    for r, i in enumerate(ch):
        for c, n in enumerate(('ext', 'int')):
            im = Image.open(f'{D}/{i}_{n}.png').resize((500, 330)); sh.paste(im, (c * 500, r * 330))
        ImageDraw.Draw(sh).text((8, r * 330 + 6), i, fill=(255, 255, 255))
    sh.save(f'{D}/_m_{tag}_{k // 4}.png')
