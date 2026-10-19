"""Hero-size test helper. Heroes are looked up in www/proto3d/charscale.js (CHARS) by name; the boss's Beth heights (Pip 0.52 m, Phoenix 0.76 m,
Wren 1.35 m) are only used as an in-page TEST FIXTURE when a build's charscale.js has no entry for that hero yet (nothing is written to disk,
the game keeps reading charscale.js only). Usage: apply(pg, 'pip') -> worldProfile dict of the applied hero."""
FIXTURE_M = {'pip': 0.52, 'phoenix': 0.76, 'wren': 1.35}
GIANTS = {'vaelthryx': 'n:vaelthryx_straight_rig', 'troll': 'n:frosttroll_a', 'titan': 'n:ashentitan_new'}
JS = """async (name) => { const cs = await import('/proto3d/charscale.js'); let id = name === 'owner' ? '' : (cs.CHARS[name] ? name : Object.keys(cs.CHARS).find(k => k.toLowerCase().includes(name)));
  const fx = %s; if (!id && fx[name]) { id = 'fixture:' + name; const h = fx[name]; cs.CHARS[id] = { height: h, radius: 0.53 * h / cs.HERO_M, step: 0.35 * h / cs.HERO_M }; }
  __p3d.applyChar(id || ''); const p = cs.worldProfile(id || '', 1.5); return { id: id || '', fixture: (id || '').startsWith('fixture:'), height: p.height, heightW: p.heightW, radiusW: p.radiusW, giant: cs.isGiant(id || '') }; }"""
def apply(pg, name):
    import json
    return pg.evaluate(JS % json.dumps(FIXTURE_M), GIANTS.get(name, name))
