#!/usr/bin/env python3
"""Titan fight + button editor + saber scaling checks at phone size (412x915, touch).
Usage: (cd www && python3 -m http.server PORT); P3D_URL=http://localhost:PORT/proto3d.html python3 tools/titan_fight_browser_test.py"""
import os
from playwright.sync_api import sync_playwright
BASE = os.environ.get('P3D_URL', 'http://localhost:9733/proto3d.html'); bad = 0
def ok(n, c, d=''):
    global bad; print(('PASS' if c else 'FAIL'), n, ('' if c else str(d)[:300]))
    if not c: bad += 1
with sync_playwright() as p:
    b = p.chromium.launch(args=['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
    ctx = b.new_context(viewport={'width': 412, 'height': 915}, has_touch=True, is_mobile=True, service_workers='block')
    pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(BASE + '?party=0&npcs=0'); pg.wait_for_function('window.__p3d && window.__p3d.frames>5', timeout=90000)
    pg.evaluate('__p3d.owner=true'); pg.wait_for_function('__p3d.combat && __p3d.combat.on', timeout=30000)
    pg.wait_for_function("__p3d.combat.enemies.some(e=>e.key==='titan')", timeout=30000)
    r = pg.evaluate("""()=>{const P=__p3d,T=P.THREE,t=P.combat.enemies.find(e=>e.key==='titan');const bb=m=>{m.updateMatrixWorld(true);const x=new T.Box3().setFromObject(m);return x.max.y-x.min.y};
      return {th:bb(t.foe.mesh),hh:bb(P.hero),hp:t.max,d:Math.hypot(t.x-P.state.heroX,t.z-P.state.heroZ)}}""")
    ok('titan is 6x hero height', abs(r['th'] / r['hh'] - 6) < 0.15, r); ok('titan 5,000,000 HP', r['hp'] == 5000000, r)
    ok('titan spawns in range', r['d'] < 40, r)
    # ---- saber scales with 3 hero sizes
    ks = []
    for sc in (0.6, 1.0, 1.7):
        pg.evaluate(f"(()=>{{const h=__p3d.hero;h.scale.setScalar({sc});}})()"); pg.wait_for_timeout(600)
        ks.append(pg.evaluate("[__p3d.combat.saberScale, __p3d.combat.saber.scale.y, __p3d.combat.saber.visible]"))
    pg.evaluate("__p3d.hero.scale.setScalar(1)")
    ok('saber scale grows with hero height (3 sizes)', ks[0][0] < ks[1][0] < ks[2][0] and abs(ks[2][0] / ks[1][0] - 1.7) < 0.1 and abs(ks[0][0] / ks[1][0] - 0.6) < 0.06, ks)
    ok('saber group scale applied (blade+hilt together)', all(abs(k[0] - k[1]) < 1e-6 for k in ks), ks)
    # ---- button editor
    pg.evaluate("document.querySelector('#settingsBtn,#openSettings,#hudMain')&&0")
    pg.evaluate("__p3d.settings&&__p3d.settings.open&&__p3d.settings.open()")
    pg.evaluate("__p3d.combat.hud.editor.enable(true)")
    box = pg.evaluate("(()=>{const r=document.querySelector('#cmb [data-a=dodge]').getBoundingClientRect();return [r.x+r.width/2,r.y+r.height/2,r.width]})()")
    fired = pg.evaluate("window.__fired=0;1")
    cdb = pg.evaluate("__p3d.combat.cc.cd.reset&&0")
    # synthetic pointer drag
    def drag(sel, dx, dy):
        pg.evaluate("""([s,dx,dy])=>{const e=document.querySelector(s),r=e.getBoundingClientRect(),x=r.x+r.width/2,y=r.y+r.height/2;
          const f=(t,X,Y)=>e.dispatchEvent(new PointerEvent(t,{bubbles:true,cancelable:true,pointerId:7,pointerType:'touch',clientX:X,clientY:Y,isPrimary:true}));
          f('pointerdown',x,y);f('pointermove',x+dx/2,y+dy/2);f('pointermove',x+dx,y+dy);f('pointerup',x+dx,y+dy)}""", [sel, dx, dy])
    drag('#cmb [data-a=dodge]', -60, -90); pg.wait_for_timeout(100)
    box2 = pg.evaluate("(()=>{const r=document.querySelector('#cmb [data-a=dodge]').getBoundingClientRect();return [r.x+r.width/2,r.y+r.height/2,r.width]})()")
    ok('drag moves the dodge button', abs((box2[0] - box[0]) + 60) < 3 and abs((box2[1] - box[1]) + 90) < 3, (box, box2))
    pg.evaluate("document.getElementById('btnEditSize').value=1.5;document.getElementById('btnEditSize').dispatchEvent(new Event('input'))")
    w3 = pg.evaluate("document.querySelector('#cmb [data-a=dodge]').getBoundingClientRect().width")
    ok('size slider resizes selected button', abs(w3 / box[2] - 1.5) < 0.05, (w3, box[2]))
    lay = pg.evaluate("localStorage.getItem('vn_btnlayout_v1')"); ok('layout persisted', lay and '"dodge"' in lay, lay)
    ok('editing a button does not attack', pg.evaluate("__p3d.combat.cc.cd && true"))
    for sel in ('atk', 'lock', 'u1', 'u5'): ok('editable: ' + sel, pg.evaluate(f"!!document.querySelector('#cmb .pad [data-a={sel}]')"))
    pg.evaluate("document.getElementById('btnEditDone').click()")
    ok('done hides the editor bar', pg.evaluate("getComputedStyle(document.getElementById('btnEditBar')).display")=='none')
    pg.reload(); pg.wait_for_function('window.__p3d && window.__p3d.frames>5 && __p3d.combat && __p3d.combat.on', timeout=90000); pg.wait_for_timeout(500)
    box3 = pg.evaluate("(()=>{const r=document.querySelector('#cmb [data-a=dodge]').getBoundingClientRect();return [r.x+r.width/2,r.y+r.height/2,r.width]})()")
    ok('layout survives reload', abs(box3[2] / box[2] - 1.5) < 0.05, box3)
    pg.evaluate("__p3d.combat.hud.editor.reset()")
    box4 = pg.evaluate("(()=>{const r=document.querySelector('#cmb [data-a=dodge]').getBoundingClientRect();return [r.x+r.width/2,r.y+r.height/2,r.width]})()")
    ok('reset restores default', abs(box4[2] - box[2]) < 1 and abs(box4[0] - box[0]) < 1, (box, box4))
    # ---- kill the titan: 51 owner-saber hits
    pg.evaluate("__p3d.owner=true"); pg.wait_for_function("__p3d.combat.enemies.some(e=>e.key==='titan')", timeout=60000)
    hits = 0; last = 5000000
    for i in range(200):
        pg.evaluate("""()=>{const P=__p3d,c=P.combat,t=c.enemies.find(e=>e.key==='titan');if(!t)return;P.state.heroX=t.x-5;P.state.heroZ=t.z-5;c.cc.res.full();c.cc.cd.reset()}""")
        pg.evaluate("__p3d.combat.api.lock()"); pg.evaluate("__p3d.combat.api.use(0)"); pg.wait_for_timeout(330)
        hp = pg.evaluate("(()=>{const t=__p3d.combat.enemies.find(e=>e.key==='titan');return t?t.hp:0})()")
        if hp < last: hits += -(-(last - hp) // 99999); last = hp
        if hp <= 0: break
    ok('titan dies after exactly 51 owner saber hits', hits == 51, hits)
    pg.wait_for_timeout(200); ok('no page errors', not errs, errs)
    b.close()
print('FAILURES: %d' % bad if bad else 'ALL PASS'); raise SystemExit(1 if bad else 0)
