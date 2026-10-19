#!/usr/bin/env python3
"""Fight test mode: starts via __p3d.fightToggle (the owner-panel hook), Owner gets the lightsaber, monsters spawn/chase/attack, swing damages, kill+respawn, HUD. SHOTS=dir for screenshots."""
import http.server, threading, functools, os, sys
from playwright.sync_api import sync_playwright
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'www')
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a, **k): pass
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Q, directory=ROOT)); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
SH = os.environ.get('SHOTS')
with sync_playwright() as p:
    b = p.chromium.launch(args=['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
    pg = b.new_context(viewport={'width':390,'height':844}, has_touch=True, is_mobile=True).new_page(); errs=[]
    pg.on('pageerror', lambda e: errs.append(str(e))); pg.on('console', lambda m: errs.append(m.text[:150]) if m.type == 'error' else 0)
    pg.goto(f'http://127.0.0.1:{port}/proto3d.html?nosave=1&party=0&npcs=0', wait_until='commit', timeout=120000); pg.wait_for_function('window.__p3d&&__p3d.frames>5', timeout=120000); pg.wait_for_timeout(1500)
    pg.evaluate("window.__p3d.owner=true; window.__p3d.cheats=window.__p3d.cheats||{}"); pg.evaluate("__p3d.fightToggle()"); pg.wait_for_function("__p3d.fight&&__p3d.fight.on&&__p3d.fight.hasSaber", timeout=60000)
    hid = pg.evaluate("__p3d.modelStatus().models[__p3d.heroIndex].id"); print('hero', hid, 'saber', pg.evaluate("__p3d.fight.hasSaber"))
    pg.wait_for_function("__p3d.fight.monsters.length>=1", timeout=60000); pg.wait_for_timeout(1500)
    pg.wait_for_timeout(1500)
    vis = pg.evaluate("(()=>{const q=s=>{const e=document.querySelector('#cb '+s);return !!e&&e.offsetParent!==null||(!!e&&getComputedStyle(e).display!=='none')};return {root:getComputedStyle(document.getElementById('cb')).display,slots:document.querySelectorAll('#cb .sl').length,cl:document.querySelectorAll('#cb .cl button').length,vit:q('.vit'),ab:q('.ab')}})()"); print('hud', vis)
    if SH: pg.screenshot(path=f'{SH}/c_start.png')
    # keep the hero alive for ability checks
    pg.evaluate("__p3d.cheat.god=true;__p3d.fight.cc.god=true")   # fight.js re-syncs cc.god from the owner cheat flag every frame (merge-all), so set the flag, not just cc.god
    def tap(sel):
        b = pg.evaluate("(s=>{const r=document.querySelector(s).getBoundingClientRect();return [r.x+r.width/2,r.y+r.height/2]})", sel); pg.touchscreen.tap(b[0], b[1])
    # basic attack via ability slot 1 until a kill (99,999 flat)
    pg.evaluate("__p3d.fight.spawn('wolf',3)"); pg.wait_for_function("__p3d.fight.monsters.some(m=>m.def.key==='wolf'||m.key==='wolf')", timeout=90000); pg.wait_for_timeout(500)
    for i in range(60):
        tap('#cb .sl[data-s="0"]'); pg.wait_for_timeout(700)
        if i == 0 and SH: pg.screenshot(path=f'{SH}/c_swing.png')
        if pg.evaluate("__p3d.fight.kills>0||__p3d.fight.monsters.some(m=>m.hp<m.max)"): break
    pg.wait_for_function("__p3d.fight.monsters.length>0", timeout=60000)
    dealt = pg.evaluate("__p3d.fight.kills>0||__p3d.fight.monsters.some(m=>m.hp<m.max)"); print('damage dealt', dealt, 'saber parent', pg.evaluate("(()=>{let n=null;__p3d.hero.traverse(o=>{if(o.name==='saber')n=o.parent&&o.parent.parent&&o.parent.parent.name});return n})()"))
    kills = pg.evaluate("__p3d.fight.kills"); print('kills', kills, 'xp/gold', pg.evaluate("[__p3d.fight.cc.xp,__p3d.fight.cc.gold]"))
    dm = pg.evaluate("document.querySelectorAll('#cb .fn').length"); print('number elements (pooled)', dm)
    # other slots
    pg.evaluate("__p3d.fight.cc.res.mp=100;__p3d.fight.cc.res.sp=100")
    for s in (1,2,3,4):   # a skill tapped while the previous one is still animating is ignored: retry until its cooldown starts
        for _ in range(4):
            tap(f'#cb .sl[data-s="{s}"]'); pg.wait_for_timeout(900)
            if s == 4 or pg.evaluate("k=>__p3d.fight.cc.cd.left(k)>0", ['royal','chains','wrath'][s-1]): break
        pg.evaluate("__p3d.fight.cc.res.mp=100;__p3d.fight.cc.res.sp=100")
    cds = pg.evaluate("['royal','chains','wrath'].map(k=>__p3d.fight.cc.cd.left(k)>0)"); print('cooldowns started', cds)   # new HUD: slots 1-3 = Owner skills (OWNER_CLUSTER), 4 = ultimate (needs Fury)
    tap('#cb [data-a=dodge]'); pg.wait_for_timeout(100); ifr = pg.evaluate("__p3d.fight.cc.iframes>0"); print('dodge iframes', ifr)
    pg.evaluate("__p3d.fight.spawn('wolf',8)"); pg.wait_for_function("__p3d.fight.monsters.some(m=>m.state!=='defeated')", timeout=60000)
    tap('#cb [data-a=lock]'); pg.wait_for_timeout(300); lk = pg.evaluate("__p3d.fight.cc.tgt.locked"); print('locked', lk)
    if SH: pg.screenshot(path=f'{SH}/c_lock.png')
    pg.evaluate("__p3d.fight.cc.res.hp=1000"); tap('#cb [data-a=potion]'); pg.wait_for_timeout(200); pot = pg.evaluate("__p3d.fight.cc.potions"); print('potions', pot)
    # boss
    pg.evaluate("__p3d.fight.cc.clearEnemies();__p3d.fight.spawnBoss()"); pg.wait_for_function("__p3d.fight.monsters.some(m=>m.def.boss)", timeout=90000); pg.wait_for_timeout(2500)
    bi = pg.evaluate("(()=>{const m=__p3d.fight.monsters.find(m=>m.def.boss);const bb=new __p3d.THREE.Box3().setFromObject(m.view);return [m.max,m.def.atk,m.def.atkMs,+(bb.max.y-bb.min.y).toFixed(2),+(6*1.8*1.5).toFixed(2),document.querySelector('#cb .tp').className]})()") if pg.evaluate("!!__p3d.THREE") else pg.evaluate("(()=>{const m=__p3d.fight.monsters.find(m=>m.def.boss);return [m.max,m.def.atk,m.def.atkMs,0,2.7,document.querySelector('#cb .tp').className]})()")
    print('boss', bi)
    pg.evaluate("(()=>{const m=__p3d.fight.monsters.find(m=>m.def.boss);const s=__p3d.state;s.heroX=m.x;s.heroZ=m.z-14})()"); pg.wait_for_timeout(2500)
    if SH: pg.screenshot(path=f'{SH}/c_boss.png')
    pg.evaluate("__p3d.cheat.god=false;__p3d.fight.cc.god=false;__p3d.fight.cc.res.hp=__p3d.fight.cc.res.max.hp"); pg.wait_for_timeout(300)
    pg.evaluate("(()=>{const m=__p3d.fight.monsters.find(m=>m.def.boss);const s=__p3d.state;s.heroX=m.x;s.heroZ=m.z-6})()")
    try: pg.wait_for_function("__p3d.fight.monsters.some(m=>m.def.boss&&m.state==='telegraph')", timeout=60000); pg.wait_for_timeout(400)
    except Exception: pass
    if SH: pg.screenshot(path=f'{SH}/c_telegraph.png')
    # death / respawn
    pg.evaluate("__p3d.fight.hurt(9999999)"); pg.wait_for_timeout(500); dead = pg.evaluate("__p3d.fight.hp"); pg.wait_for_function('__p3d.fight.hp>0', timeout=60000); back = pg.evaluate("__p3d.fight.hp"); print('death hp', dead, 'respawn hp', back)
    pg.evaluate("__p3d.selectHero(1)"); pg.wait_for_timeout(5000); sab = pg.evaluate("__p3d.fight.hasSaber"); print('darius has saber', sab)
    if SH: pg.screenshot(path=f'{SH}/c_darius.png')
    pg.evaluate("__p3d.fight.cc.use(2)"); pg.wait_for_timeout(200)
    tp = pg.evaluate("document.querySelector('#cb .msg').textContent"); print('msg', tp)
    pg.evaluate("__p3d.fight.stop()"); print('errs', errs[:4])
    gone = pg.evaluate("document.getElementById('cb').style.display")
    ok = hid == 'n:owner' and vis['slots']==5 and all(cds) and vis['cl']==6 and dealt and ifr and lk and pot == 2 and bi[0]==5000000 and bi[1]==2100 and bi[2]==2300 and dead == 0 and back > 0 and sab and gone == 'none' and not errs
    print('PASS' if ok else 'FAIL'); b.close()
