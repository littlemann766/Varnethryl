"""Reassign the 212 town fillers to distinct variants (same footprint+door as the original model) so that no two
identical models stand closer than possible (greedy max-min, 40 m target), and landmark shops are never used as fillers."""
import json, math, sys
src, dst = sys.argv[1], sys.argv[2]
it = json.load(open(src))
C = {'house1': ['house1', 'townhouse_a', 'townhouse_e'], 'house2': ['house2', 'townhouse_b', 'townhouse_f'], 'house3': ['house3', 'townhouse_c', 'townhouse_g'],
     'house4': ['house4', 'townhouse_d', 'townhouse_h'], 'bakery': ['butcher', 'candlemaker', 'merchant_house', 'merchant_house_b'], 'apothecary': ['tailor', 'weaver', 'guild_house', 'guild_house_b'],
     'smithy': ['farrier', 'cooper', 'carpenter', 'chapel', 'stone_hall', 'stone_hall_b']}
CAP = {'chapel': 2, 'butcher': 4, 'candlemaker': 4, 'tailor': 4, 'weaver': 4, 'farrier': 4, 'cooper': 4, 'carpenter': 4}
LBL = {'butcher': 'Butcher', 'candlemaker': 'Candle Maker', 'tailor': 'Tailor', 'weaver': 'Weaver', 'farrier': 'Farrier', 'chapel': 'Chapel'}
LAND = {'house1': (-25.7, 58.5), 'house2': (25.0, 57.5), 'house3': (-25.4, 83.0), 'house4': (26.0, 80.5)}   # landmark kit houses (main.DEFS)
placed = {k: [v] for k, v in LAND.items()}
order = sorted(range(len(it)), key=lambda i: (it[i]['pos'][0] ** 2 + it[i]['pos'][1] ** 2))
for i in order:
    f = it[i]; b = f['model']; best = None
    for cand in C[b]:
        if len(placed.get(cand, [])) >= CAP.get(cand, 999): continue
        d = min([math.dist(f['pos'], p) for p in placed.get(cand, [])] + [1e9])
        if best is None or d > best[0]: best = (d, cand)
    f['model_v1'] = b; f['model'] = best[1]; placed.setdefault(best[1], []).append(f['pos'])
    if best[1] in LBL: f['label'] = LBL[best[1]]
    if best[1] == 'chapel': f['interior'] = ''
json.dump(it, open(dst, 'w'), indent=1)
from collections import Counter
print(Counter(f['model'] for f in it))
mind = {}
for a in range(len(it)):
    for b2 in range(a + 1, len(it)):
        if it[a]['model'] == it[b2]['model']:
            d = math.dist(it[a]['pos'], it[b2]['pos']); mind[it[a]['model']] = min(mind.get(it[a]['model'], 1e9), d)
print('min same-model spacing (m):', {k: round(v, 1) for k, v in sorted(mind.items())})
print('pairs < 25 m:', sum(1 for a in range(len(it)) for b2 in range(a + 1, len(it)) if it[a]['model'] == it[b2]['model'] and math.dist(it[a]['pos'], it[b2]['pos']) < 25))
print('pairs < 40 m:', sum(1 for a in range(len(it)) for b2 in range(a + 1, len(it)) if it[a]['model'] == it[b2]['model'] and math.dist(it[a]['pos'], it[b2]['pos']) < 40))
