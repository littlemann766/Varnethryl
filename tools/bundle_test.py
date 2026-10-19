#!/usr/bin/env python3
"""test-bundle-1019: approved heights for bundle models, giant titans (owner-only spawn, weapon on hand_R, fit Wilds + camera), Vaelthryx new7 coil_windup telegraph. SHOTS=dir."""
import http.server, threading, functools, os, sys, json
from playwright.sync_api import sync_playwright
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'www')
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(s, *a, **k): pass
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Q, directory=ROOT)); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start(); bad = 0; SH = os.environ.get('SHOTS')
def T(n, c, d=''):
    global bad; print('PASS' if c else 'FAIL', n, '' if c else d); bad += 0 if c else 1
# approved height and Beth's baked (skinned idle t=0) height. Check: load scale x baked == approved (the static rest-pose bbox differs from the idle pose, e.g. Vaelthryx is straight at rest and coiled at idle)
BAKED = {'n:owner': 1.901, 'n:wren_new3': 1.35, 'n:pip_new2': 0.52, 'n:ember_new3': 1.296, 'n:garruk_new5': 2.02, 'n:brynn_armor2': 1.592, 'n:cedric_armor2': 2.017, 'n:phoenix_new3': 0.756, 'n:frosttroll_a': 5.724, 'n:frosttroll_b': 5.715, 'n:ashentitan_new': 11.445, 'n:vaelthryx_new7': 19.05}
IDS = {'n:owner': 1.905, 'n:wren_new3': 1.35, 'n:pip_new2': 0.52, 'n:ember_new3': 1.296, 'n:garruk_new5': 2.02, 'n:brynn_armor2': 1.626, 'n:cedric_armor2': 1.829, 'n:phoenix_new3': 0.756,
       'n:frosttroll_a': 5.7, 'n:frosttroll_b': 5.715, 'n:ashentitan_new': 11.4, 'n:vaelthryx_new7': 19.05}
with sync_playwright() as p:
    b = p.chromium.launch(args=['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']); pg = b.new_context(viewport={'width':844,'height':390}, has_touch=True, is_mobile=True).new_page(); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(f'http://127.0.0.1:{port}/proto3d.html?nosave=1&npcs=0&party=0', wait_until='commit', timeout=120000); pg.wait_for_function('window.__p3d&&__p3d.frames>5', timeout=120000); pg.wait_for_timeout(1500)
    got = {}
    for i, want in IDS.items():
        k = pg.evaluate("id=>__p3d.modelStatus().models.findIndex(m=>m.id===id)", i)
        if k < 0: got[i] = 'missing'; continue
        pg.evaluate("k=>__p3d.selectHero(k)", k)
        try: pg.wait_for_function("id=>{const h=__p3d.hero;return h&&h.userData&&h.userData.glb&&__p3d.modelStatus().models[__p3d.heroIndex].id===id&&h.userData.heightW>0}", arg=i, timeout=60000)
        except Exception: got[i] = 'timeout'; continue
        got[i] = round(pg.evaluate("__p3d.hero.userData.mscale") / (0.947 * 1.5) * BAKED[i], 3)
    print(json.dumps(got))
    for i, want in IDS.items():
        g = got[i]; tol = 0.03 if want < 3 else 0.02
        T(f'{i} renders at the approved {want} m', isinstance(g, float) and abs(g - want) / want <= tol, g)
    # giants: owner-only
    pg.evaluate("__p3d.setZone&&__p3d.setZone('wilds')"); pg.wait_for_timeout(3000)
    pg.evaluate("window.__p3d.owner=false"); pg.evaluate("__p3d.fight&&__p3d.fight.on||__p3d.fightToggle()"); pg.wait_for_function("__p3d.fight&&__p3d.fight.on", timeout=60000); pg.wait_for_timeout(800)
    T('giant spawn refused without the owner gate', pg.evaluate("__p3d.fight.cheatSpawn('titan_g20')") is False)
    pg.evaluate("window.__p3d.owner=true; window.__p3d.cheats=window.__p3d.cheats||{}")
    for k, hm in (('titan_g20', 38.1), ('titan_g40', 76.2), ('titan_g60', 114.3)):
        pg.evaluate("(()=>{const f=__p3d.fight;f.cc.god=true;for(const e of f.cc.enemies.slice()){e.hp=0;f.cc.defeat(e);f.cc.removeEnemy(e)}})()"); pg.wait_for_timeout(500)
        ok = pg.evaluate("k=>__p3d.fight.cheatSpawn(k)", k)
        try: pg.wait_for_function("k=>__p3d.fight.monsters.some(e=>e.key===k&&e.view&&e.view.userData.weapon)", arg=k, timeout=90000); w = True
        except Exception: w = False
        r = pg.evaluate("""k=>{const e=__p3d.fight.monsters.find(e=>e.key===k);if(!e)return null;const T=__p3d.THREE,bb=new T.Box3().setFromObject(e.view),h=(bb.max.y-bb.min.y);
          const cam=__p3d.camera||null,v=new T.Vector3(e.x,h*0.5,e.z);let on=null;if(cam){v.project(cam);on=Math.abs(v.x)<1.2&&Math.abs(v.y)<1.2&&v.z<1;}
          return {hm:+(e.view.userData.mscale/(0.947*1.5)*({titan_g20:38.1,titan_g40:76.2,titan_g60:114.3}[k])).toFixed(1),rest:+(h/(0.947*1.5)).toFixed(1),x:e.x,z:e.z,far:cam&&cam.far,fog:__p3d.scene&&__p3d.scene.fog&&__p3d.scene.fog.far,on}}""", k)
        if SH: pg.wait_for_timeout(1500); pg.screenshot(path=f'{SH}/{k}.png')
        print(k, r)
        T(f'{k}: owner spawn ok, {hm} m, weapon on hand_R', ok and w and r and abs(r['hm'] - hm) / hm < 0.03, r)
        T(f'{k}: inside the Wilds (|dx|,|dz| < 280 from centre)', r and abs(r['x'] - 1000) < 280 and abs(r['z']) < 280, r)
        T(f'{k}: camera far/fog cover it', r and (r['far'] is None or r['far'] >= 1500) and (r['fog'] is None or r['fog'] >= 900), r)
    T('Ashen Titan is still the normal boss', pg.evaluate("(async()=>{const m=await import('./proto3d/combat/data.js');return m.ENEMIES.titan.model==='n:ashentitan_new'&&!m.WAVE_TABLE.some(k=>/titan_g/.test(k))})()"))
    # vaelthryx coil_windup on telegraph
    pg.evaluate("(()=>{const f=__p3d.fight;for(const e of f.cc.enemies.slice()){e.hp=0;f.cc.defeat(e);f.cc.removeEnemy(e)}})()"); pg.wait_for_timeout(500)
    pg.evaluate("__p3d.fight.cheatSpawn('vaelthryx')"); pg.wait_for_function("__p3d.fight.monsters.some(e=>e.key==='vaelthryx'&&e.view)", timeout=90000)
    pg.evaluate("(()=>{const e=__p3d.fight.monsters.find(e=>e.key==='vaelthryx');e.aggroR=400;const p=__p3d.fight.cc.p;e.x=p.x+8;e.z=p.z;window.__v=e})()")
    tel = False
    for i in range(300):
        pg.wait_for_timeout(100)
        if pg.evaluate("__v.state==='telegraph'"): pg.wait_for_timeout(200); tel = pg.evaluate("(()=>{const a=__v.view.userData.act.telegraph;return !!a&&a.isRunning()&&a.getClip().name==='coil_windup'})()"); break
    print('vael', pg.evaluate("[__v.state,Object.keys(__v.view.userData.act).join(','),__v.view.userData.os&&__v.view.userData.os.a.getClip().name,Math.hypot(__v.x-__p3d.fight.cc.p.x,__v.z-__p3d.fight.cc.p.z)]"))
    T('Vaelthryx new7 plays coil_windup while telegraphing', tel)
    # Frost Troll B: club on weapon_R, windup then attack at 1.0 s
    pg.evaluate("(()=>{const f=__p3d.fight;for(const e of f.cc.enemies.slice()){e.hp=0;f.cc.defeat(e);f.cc.removeEnemy(e)}})()"); pg.wait_for_timeout(500)
    pg.evaluate("__p3d.fight.cheatSpawn('frosttroll_b')")
    try: pg.wait_for_function("__p3d.fight.monsters.some(e=>e.key==='frosttroll_b'&&e.view&&e.view.userData.weapon)", timeout=90000); tw = pg.evaluate("__p3d.fight.monsters.find(e=>e.key==='frosttroll_b').view.userData.weapon.parent.name")
    except Exception: tw = None
    T('Frost Troll B: troll_ice_club on weapon_R', tw == 'weapon_R', tw)
    pg.evaluate("(()=>{const e=__p3d.fight.monsters.find(e=>e.key==='frosttroll_b');const p=__p3d.fight.cc.p;e.x=p.x+5;e.z=p.z;e.aggroR=200;window.__tb=e})()")
    seq = []
    for i in range(250):
        pg.wait_for_timeout(60)
        st = pg.evaluate("(()=>{const u=__tb.view.userData;return [__tb.state,u.os&&u.os.a.getClip().name,+(__tb.wuT||0).toFixed(2)]})()")
        if st[1] and (not seq or seq[-1] != st[1]): seq.append(st[1])
        if 'windup' in seq and seq[-1] != 'windup' and seq.index('windup') < len(seq) - 1: break
    print('trollB clips', seq)
    T('Frost Troll B: windup clip then attack', 'windup' in seq and any(c.startswith('attack') for c in seq[seq.index('windup'):] if 'windup' in seq), seq)
    T('no page errors', not errs, errs[:3]); b.close()
print('FAILED' if bad else 'ALL PASS'); sys.exit(1 if bad else 0)
