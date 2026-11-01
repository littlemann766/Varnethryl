"""Terrain pass fix 1 (duplicate buildings): distinct filler variants on the SAME footprints and door positions as the
card2 kit they replace (house1-4, bakery, apothecary, smithy), so fillers.json doors/paths/interiors stay valid.
Variation: roof material, upper-wall material, timber framing, storeys and pitch kept within the bbox, plus trade signs as geometry.
Run: python3 variants.py OUTDIR [names...]"""
import sys, os, numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'v2'))
import build, house as H
from kit2 import barrel, crate, pot_plant, cyl, cone
from kit3 import awning, lancet
ORIG = H.house
EXTRA = {}
def _house(sp): sp = dict(sp); r = dict(sp.get('remap', {})); r.update(EXTRA.get('remap', {})); sp.update({k: v for k, v in EXTRA.items() if k != 'remap'}); sp['remap'] = r; return ORIG(sp)
build.house = _house
def V(base, extra, add=None):
    def f():
        EXTRA.clear(); EXTRA.update(extra)
        try: c = getattr(build, base)()
        finally: EXTRA.clear()
        if add: add(c)
        return c
    return f
def _front(c):   # front face + lateral axis before export rotation
    return ('x+' if c.get('front_gable') else 'z+')
def hang_sign(c, a, y, shape):
    m = c['m']; p, t, n = H.facepos(c, _front(c), a, y)
    m.beam(p, p + n * 1.1, 0.09, 'iron'); m.beam(p + n * 1.05, p + n * 1.05 - np.array([0, 0.25, 0]), 0.05, 'iron')
    q = p + n * 0.95 - np.array([0, 0.75, 0])
    m.obox(q, n, (0, 1, 0), t, (0.9, 0.9, 0.07), 'oak')
    s = q + t * 0.05
    if shape == 'scissors':
        for d in (1, -1): m.beam(s + n * (-0.3) + np.array([0, -0.3 * d, 0]), s + n * 0.3 + np.array([0, 0.3 * d, 0]), 0.07, 'iron')
        for d in (1, -1): m.obox(s + n * -0.33 + np.array([0, 0.3 * d, 0]), n, (0, 1, 0), t, (0.18, 0.18, 0.1), 'gold')
    elif shape == 'cleaver':
        m.obox(s + n * 0.1, n, (0, 1, 0), t, (0.5, 0.36, 0.1), 'iron'); m.obox(s + n * -0.3, n, (0, 1, 0), t, (0.3, 0.09, 0.11), 'oak')
    elif shape == 'candle':
        m.obox(s + np.array([0, -0.08, 0]), n, (0, 1, 0), t, (0.16, 0.5, 0.1), 'plaster'); m.obox(s + np.array([0, 0.25, 0]), n, (0, 1, 0), t, (0.07, 0.14, 0.11), 'gold')
    elif shape == 'shoe':
        for ang in np.linspace(-2.4, 2.4, 7): m.obox(s + n * (0.25 * np.sin(ang)) + np.array([0, 0.25 * np.cos(ang), 0]), n, (0, 1, 0), t, (0.12, 0.12, 0.1), 'iron')
    elif shape == 'barrel':
        m.obox(s, n, (0, 1, 0), t, (0.45, 0.6, 0.12), 'oak')
        for yy in (-0.2, 0.2): m.obox(s + np.array([0, yy, 0]), n, (0, 1, 0), t, (0.5, 0.06, 0.14), 'iron')
    elif shape == 'saw':
        m.obox(s, n, (0, 1, 0), t, (0.7, 0.2, 0.08), 'iron'); m.obox(s + n * -0.42, n, (0, 1, 0), t, (0.18, 0.3, 0.1), 'oak')
    elif shape == 'spindle':
        m.obox(s, n, (0, 1, 0), t, (0.12, 0.6, 0.1), 'oak'); m.obox(s, n, (0, 1, 0), t, (0.34, 0.14, 0.11), 'plaster')
def tailor_add(c):
    hang_sign(c, -3.0, c['g'] + 0.3, 'scissors')
    for x in (-2.4, -1.9, 2.0): cyl(c['m'], (x, 0, c['D'] / 2 + 0.6), 0.22, 0.0, 1.1, 'bluestone', 8)   # cloth bolts
def butcher_add(c):
    m = c['m']; hang_sign(c, 3.0, c['g'] + 0.3, 'cleaver'); awning(m, 0.2, 4.4, 2.6, c['D'] / 2 + 0.05, 1.3, 0.5, 6)
    for x in (2.2, 3.0, 3.8): m.obox((x, 2.0, c['D'] / 2 + 0.9), (1, 0, 0), (0, 1, 0), (0, 0, 1), (0.3, 0.55, 0.3), 'oak')   # hams
def candle_add(c):
    hang_sign(c, -3.0, c['g'] + 0.3, 'candle'); crate(c['m'], (3.6, 0, c['D'] / 2 + 0.7), 0.6)
def farrier_add(c):
    hang_sign(c, 3.2, c['g'] - 0.2, 'shoe')
def weaver_add(c):
    hang_sign(c, 3.0, c['g'] + 0.3, 'spindle')
def cooper_add(c):
    hang_sign(c, 3.2, c['g'] - 0.2, 'barrel')
def carpenter_add(c):
    hang_sign(c, 3.2, c['g'] - 0.2, 'saw')
def chapel_add(c):   # bell turret on the rear gable + lancet windows (smithy footprint, stone)
    m = c['m']; E = c['E']; X0 = c['X0'] if 'X0' in c else -c['W'] / 2
    x = X0 + 1.2
    m.box((x - 0.9, E, -0.9), (x + 0.9, E + 4.2, 0.9), 'ashlar'); m.box((x - 0.95, E + 4.2, -0.95), (x + 0.95, E + 4.4, 0.95), 'stone')
    cone(m, (x, 0, 0), 1.25, E + 4.4, 3.2, 'slate', 4)
    m.box((x - 0.5, E + 2.4, 0.91), (x + 0.5, E + 3.6, 0.95), 'iron'); m.box((x - 0.5, E + 2.4, -0.95), (x + 0.5, E + 3.6, -0.91), 'iron')
    p, t, n = H.facepos(c, 'x+', 0, E + 1.6); m.obox(p + n * 0.1, t, (0, 1, 0), n, (0.18, 1.4, 0.1), 'gold'); m.obox(p + n * 0.1 + np.array([0, 0.25, 0]), t, (0, 1, 0), n, (0.8, 0.18, 0.1), 'gold')
SIGNS = {'sign_bread': 'banner', 'sign_potion': 'banner', 'sign_anvil': 'banner', 'sign_inn': 'banner'}
VAR = {
    # townhouses (same footprint/door as the kit house they replace)
    'townhouse_a': V('house1', {'remap': {'slate': 'oak'}}),                                    # oak-shingle roof
    'townhouse_b': V('house2', {'remap': {'plaster': 'oak', 'slate': 'rock'}, 'pitch': 50}),      # weatherboard, stone-tile roof
    'townhouse_c': V('house3', {'remap': {'plaster': 'ashlar'}, 'pitch': 62}),                     # cut-stone upper, steep slate
    'townhouse_d': V('house4', {'remap': {'slate': 'oak', 'beam': 'oak'}, 'framing': False}),       # plain render, wooden roof
    'townhouse_e': V('house1', {'remap': {'plaster': 'stone'}, 'framing': False, 'pitch': 50}),     # all-stone cottage
    'townhouse_f': V('house2', {'remap': {'slate': 'oak'}, 'floors': 2, 'fh': 2.5}),               # tall narrow, oak roof
    'townhouse_g': V('house3', {'remap': {'slate': 'rock'}, 'pitch': 50}),                     # stone-tile roof, low pitch
    'townhouse_h': V('house4', {'remap': {'plaster': 'oak'}, 'pitch': 54}),                        # timber-clad 3-storey
    # trades (replace the cloned landmark shops)
    'tailor': V('apothecary', {'remap': dict(SIGNS, slate='oak')}, tailor_add),
    'weaver': V('apothecary', {'remap': dict(SIGNS, plaster='ashlar')}, weaver_add),
    'butcher': V('bakery', {'remap': dict(SIGNS, plaster='oak')}, butcher_add),
    'candlemaker': V('bakery', {'remap': dict(SIGNS, slate='rock')}, candle_add),
    'farrier': V('smithy', {'remap': dict(SIGNS, slate='oak', stone='rock')}, farrier_add),
    'cooper': V('smithy', {'remap': dict(SIGNS, slate='rock')}, cooper_add),
    'carpenter': V('smithy', {'remap': dict(SIGNS, stone='ashlar', slate='oak')}, carpenter_add),
    'merchant_house': V('bakery', {'remap': {'sign_bread': 'window', 'slate': 'oak', 'plaster': 'ashlar'}}),
    'merchant_house_b': V('bakery', {'remap': {'sign_bread': 'window', 'slate': 'rock'}, 'pitch': 52}),
    'guild_house': V('apothecary', {'remap': {'sign_potion': 'window', 'plaster': 'oak'}}),
    'guild_house_b': V('apothecary', {'remap': {'sign_potion': 'window', 'slate': 'rock', 'plaster': 'stone'}}),
    'stone_hall': V('smithy', {'remap': {'sign_anvil': 'window', 'stone': 'ashlar', 'slate': 'rock'}}),
    'stone_hall_b': V('smithy', {'remap': {'sign_anvil': 'window', 'slate': 'oak'}}),
    'chapel': V('smithy', {'remap': dict(SIGNS, stone='ashlar')}, chapel_add),
}
BASE = {'townhouse_a': 'house1', 'townhouse_e': 'house1', 'townhouse_b': 'house2', 'townhouse_f': 'house2', 'townhouse_c': 'house3', 'townhouse_g': 'house3',
        'townhouse_d': 'house4', 'townhouse_h': 'house4', 'tailor': 'apothecary', 'weaver': 'apothecary', 'butcher': 'bakery', 'candlemaker': 'bakery', 'farrier': 'smithy', 'cooper': 'smithy', 'carpenter': 'smithy', 'chapel': 'smithy', 'merchant_house': 'bakery', 'merchant_house_b': 'bakery', 'guild_house': 'apothecary', 'guild_house_b': 'apothecary', 'stone_hall': 'smithy', 'stone_hall_b': 'smithy'}
if __name__ == '__main__':
    build.OUT = sys.argv[1]; build.SPECS.update(VAR)
    for n in (sys.argv[2:] or VAR): build.export(n)
