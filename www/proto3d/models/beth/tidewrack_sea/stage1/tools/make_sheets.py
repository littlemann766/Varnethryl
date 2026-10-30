#!/usr/bin/env python3
"""Beth: compose before/after, hero sheet and ship-upgrade contact sheet from ../renders."""
import os
from PIL import Image, ImageDraw, ImageFont
R = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'renders') + '/'
OLD = '/workspace/godot-art/ocean_map_concept/renders/A1_archipelago_High.jpg'
F = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 26); f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 20)
def lab(im, t, sub=''):
    d = ImageDraw.Draw(im, 'RGBA'); d.rectangle([0, 0, im.width, 40 + (26 if sub else 0)], fill=(0, 0, 0, 170)); d.text((12, 6), t, font=F, fill=(255, 235, 170))
    if sub: d.text((12, 40), sub, font=f, fill=(255, 255, 255))
    return im
b = Image.open(OLD).convert('RGB').resize((1280, 720)); a = Image.open(R + 'A1_archipelago_hero_High.jpg').convert('RGB')
c = Image.new('RGB', (2560, 720)); c.paste(lab(b, 'BEFORE: concept blockout (placeholder islands)'), (0, 0)); c.paste(lab(a, 'AFTER: Stage 1 art, islands from the v4 land mask (High)'), (1280, 0)); c.save(R + 'before_after_archipelago.jpg', quality=88)
names = [('A1_archipelago_hero_High', 'Archipelago, High (T3 galleon off Gullhaven)'), ('A1_archipelago_hero_Low', 'Same view, Low tier'), ('A2_gullhaven_port_High', 'Gullhaven port'),
         ('A3_lantern_rock_High', 'Lantern Rock'), ('A4_wreck_reef_High', 'Wreck Reef, sunken galleons (skiff zone)'), ('A5_saltwatch_dive_bell_High', 'Saltwatch Keep and the dive bell'),
         ('A6_brinecrown_coil_arena_High', 'Brinecrown Coil in its sea-stack arena'), ('A6_brinecrown_coil_arena_Low', 'Coil arena, Low tier'), ('A7_storm_wall_border_High', 'Storm wall at the region border'),
         ('A8_region_overview_High', 'Region A overview'), ('B1_coil_rest_pose_side', 'Coil rest pose (rig-ready, straight +Z)'), ('B2_coil_rest_pose_head', 'Coil head and brine crown')]
W, H = 960, 540; c = Image.new('RGB', (W * 3, H * 4))
for i, (n, t) in enumerate(names): c.paste(lab(Image.open(R + n + '.jpg').convert('RGB').resize((W, H)), t), ((i % 3) * W, (i // 3) * H))
c.save(R + 'stage1_hero_sheet.jpg', quality=86)
tn = ['T0 Base (your model)', 'T1 Patched Canvas', 'T2 Gullwing Rig', 'T3 Stormsilk']; gs = ['13', '16', '20', '26']; ss = ['9', '11', '13.5', '17']
c = Image.new('RGB', (W * 4, H * 2 + 60), (20, 24, 30)); d = ImageDraw.Draw(c)
d.text((14, 14), 'Ship upgrade tiers: add-on meshes on your models (galleon top, skiff bottom). Speeds in m/s.', font=F, fill=(255, 235, 170))
for r, (k, sp) in enumerate([('galleon', gs), ('skiff', ss)]):
    for t in range(4): c.paste(lab(Image.open(R + f'U_{k}_t{t}.jpg').convert('RGB').resize((W, H)), f'{k.title()} {tn[t]}', f'top speed {sp[t]} m/s'), (t * W, 60 + r * H))
c.save(R + 'ship_upgrade_contact_sheet.jpg', quality=88); print('ok')
