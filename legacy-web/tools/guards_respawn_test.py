#!/usr/bin/env python3
"""Town guards + Wilds respawn (headless).
 guards: posts at gate / guild hall / town hall; a monster within 15 m is struck (DamageCalculator.guardHit, modest), the hero is never hit.
 respawn: Wilds population respects per-biome caps; a killed monster comes back 20-40 s (sim time) later, out of the camera view and >= 22 m away;
          nothing ever spawns in town. usage: python3 tools/guards_respawn_test.py"""
import http.server, threading, functools, os, sys, json
from playwright.sync_api import sync_playwright
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'www')
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a, **k): pass
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Q, directory=ROOT)); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
fails = 0
def chk(n, c, x=''):
    global fails; print(('PASS ' if c else 'FAIL ') + n, x, flush=True); fails += 0 if c else 1
with sync_playwright() as p:
    b = p.chromium.launch(args=['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist']); pg = b.new_page(viewport={'width': 390, 'height': 844})
    errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(f'http://127.0.0.1:{port}/proto3d.html?nosave=1'); pg.wait_for_function('window.__p3d && __p3d.frames>5', timeout=180000); pg.wait_for_timeout(1000)
    pg.evaluate("__p3d.fightToggle(true)"); pg.wait_for_function("__p3d.guards && __p3d.fight", timeout=60000)
    posts = pg.evaluate("__p3d.guards.posts.map(g=>g.at)")
    chk('guard posts at gatehouse, guild hall, town hall', all(k in posts for k in ('gatehouse', 'guildhall', 'townhall')), str(posts))
    pg.evaluate("__p3d.fight.startAuto()"); pg.wait_for_timeout(6000)
    chk('no monsters spawn in town', pg.evaluate("__p3d.fight.monsters.length") == 0, str(pg.evaluate("__p3d.fight.monsters.length")))
    # one wolf 9 m from the guild hall guards, hero 45 m away
    g = pg.evaluate("(()=>{const g=__p3d.guards.posts.find(q=>q.at==='guildhall');return [g.x,g.z]})()")
    pg.evaluate("([g])=>{__p3d.teleport(g[0]+40,g[1]+20,0)}", [g])
    pg.evaluate("window.__ai0=__p3d.fight.cc.ai.update;__p3d.fight.cc.ai.update=()=>null;window.__gs=[];__p3d.guards.onStrike=(g,e)=>{__gs.push(__p3d.fight.monsters.includes(e))};0")   # freeze monster AI: any hero HP change could only come from the guards
    pg.evaluate("([g])=>__p3d.fight.spawn('wolf',0,{at:[g[0]+6,g[1]+6.5],aggroR:0.01})", [g])
    pg.wait_for_function("__p3d.fight.monsters.length>0", timeout=60000)
    hp0 = pg.evaluate("__p3d.fight.hp"); pg.evaluate("(()=>{const e=__p3d.fight.monsters[0];e.hp=e.max=120;0})()")   # freeze monster AI: any hero HP change could only come from the guards
    try: pg.wait_for_function("__p3d.fight.monsters[0].state==='defeated'", timeout=120000); dead = True
    except Exception: dead = False
    st = pg.evaluate("({hits:__p3d.guards.hits,dmg:__p3d.guards.dmgDone,onlyEnemies:__gs.every(x=>x),hp:__p3d.fight.hp,by:__p3d.fight.monsters[0]&&__p3d.fight.monsters[0].byGuard})")
    chk('guards strike a monster within 15 m and defeat it', dead and st['hits'] > 0 and st['by'], json.dumps(st))
    chk('guard damage is modest (22-38 per hit)', st['hits'] > 0 and 22 <= st['dmg'] / st['hits'] <= 38, json.dumps(st))
    chk('guards only target monsters; hero untouched', st['onlyEnemies'] and st['hp'] == hp0, f"{hp0} -> {st['hp']}")
    pg.evaluate("__p3d.fight.cc.ai.update=__ai0;__p3d.fight.stop()")
    if os.environ.get('GUARDS_ONLY'): print('FAILS', fails); sys.exit(1 if fails else 0)
    # Wilds
    pg.evaluate("__p3d.setZone('wilds')"); pg.wait_for_function("__p3d.zone==='wilds' && __p3d.fight && __p3d.fight.on", timeout=120000)
    pg.evaluate("__p3d.fight.cc.god=true")
    try: pg.wait_for_function("__p3d.fight.monsters.filter(e=>e.state!=='defeated').length>=5", timeout=240000); ok = True
    except Exception: ok = False
    caps = pg.evaluate("(()=>{const c={};for(const e of __p3d.fight.monsters)if(e.state!=='defeated')c[e.biome]=(c[e.biome]||0)+1;return c})()")
    chk('Wilds populate', ok, json.dumps(caps))
    lim = {'meadow': 4, 'forest': 3, 'rock': 2, 'snow': 2, 'shore': 2}
    chk('per-biome caps respected', all(v <= lim.get(k, 2) for k, v in caps.items()), json.dumps(caps))
    pg.wait_for_function("__p3d.fight.respawner.ready.length===0 && __p3d.fight.respawner.pending===0", timeout=240000)
    pg.evaluate("(()=>{const f=__p3d.fight;const e=f.monsters.find(m=>m.state!=='defeated');f.cc.defeat(e)})()")
    try: pg.wait_for_function("__p3d.fight.respawner.log.some(l=>l.delayed&&l.used)", timeout=420000); ok = True
    except Exception: ok = False
    lg = pg.evaluate("__p3d.fight.respawner.log.filter(l=>l.delayed).map(l=>({delay:+(l.due-l.freed).toFixed(1),waited:l.used?+(l.at-l.freed).toFixed(1):null,vis:l.vis,d:l.d&&+l.d.toFixed(1),b:l.b}))")
    used = [x for x in lg if x.get('waited') is not None]; e = used[0] if used else {}   # other kills may queue more slots meanwhile: check the first one that came back
    chk('killed monster respawns after 20-40 s', ok and 20 <= e.get('delay', 0) <= 40 and e.get('waited') is not None and e['waited'] >= 20, json.dumps(lg))
    chk('respawn is out of sight and >= 22 m from the hero', ok and e.get('vis') is False and e.get('d', 0) >= 22, json.dumps(e))
    pg.evaluate("__p3d.setZone('town')"); pg.wait_for_timeout(3000)
    chk('leaving the Wilds clears monsters (none in town)', pg.evaluate("__p3d.fight.monsters.length") == 0)
    chk('no page errors', not errs, str(errs[:3])); b.close()
print('FAILS', fails); sys.exit(1 if fails else 0)
