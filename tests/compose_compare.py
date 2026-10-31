#!/usr/bin/env python3
"""Side-by-side: building card (left) vs interior renders (right). python3 tests/compose_compare.py [ids...]"""
import sys, glob, os, re
from PIL import Image, ImageDraw
ROOT = os.path.dirname(os.path.abspath(__file__))
CARDS = "/workspace/beth-world/audit/cardstyle/cards/"
MAP = {"inn": "card_inn.jpg", "guildhall": "card_guild_hall.png", "townhall": "card_town_hall.jpg", "smithy": "card_blacksmith.jpg",
       "bakery": "card_bakery.jpg", "temple": "card_temple.jpg", "library": "card_grand_library.png", "mage": "card_mage_academy.jpg",
       "treasury": "card_treasury.jpg", "keep": "card_castle_keep.jpg", "observatory": "card_observatory.jpg", "crypt": "card_crypt.jpg",
       "market": "card_market_provisioner.png", "apothecary": "card_apothecary.jpg", "training": "card_training_hall.jpg",
       "colosseum": "card_colosseum.jpg", "thieves": "card_thieves_den.jpg", "farmhouse": "card_farmhouse_barn.jpg", "barn": "card_farmhouse_barn.jpg",
       "stables": "card_stables.jpg", "windmill": "card_windmill.jpg", "house1": "card_village_houses.jpg", "house2": "card_village_houses.jpg", "house3": "card_village_houses.jpg", "house4": "card_village_houses.jpg", "gatehouse": "card_gatehouse.jpg",
       "lighthouse": "card_lighthouse_tidewrack.jpg", "port": "card_port.jpg", "watchtower": "card_town_walls_watchtowers.jpg", "fountain": "card_fountain_monument.jpg"}
SH = os.path.join(ROOT, "shots/interiors")
ids = sys.argv[1:] or sorted({re.match(r"(.+)_[fpr]\d+\.png", os.path.basename(p)).group(1) for p in glob.glob(SH + "/*_[fpr]*.png")})
for id in ids:
    shots = sorted(glob.glob(f"{SH}/{id}_p*.png")) + sorted(glob.glob(f"{SH}/{id}_f*.png")) + sorted(glob.glob(f"{SH}/{id}_r*.png"), key=lambda p: int(re.search(r"_r(\d+)", p).group(1)))
    if not shots: continue
    card = Image.open(CARDS + MAP[id]).convert("RGB"); H = 1400
    card = card.resize((int(card.width * H / card.height), H))
    cols = 3; tw = 480; th = 320; rows = (len(shots) + cols - 1) // cols
    grid = Image.new("RGB", (cols * tw, max(H, rows * th)), (20, 16, 12))
    d = ImageDraw.Draw(grid)
    for i, p in enumerate(shots):
        im = Image.open(p).convert("RGB").resize((tw, th)); grid.paste(im, ((i % cols) * tw, (i // cols) * th))
        d.text(((i % cols) * tw + 6, (i // cols) * th + 4), os.path.basename(p)[:-4], fill=(255, 230, 160))
    out = Image.new("RGB", (card.width + grid.width, max(H, grid.height)), (20, 16, 12))
    out.paste(card, (0, 0)); out.paste(grid, (card.width, 0))
    out.save(f"{SH}/compare_{id}.jpg", quality=85); print("wrote", f"{SH}/compare_{id}.jpg")
