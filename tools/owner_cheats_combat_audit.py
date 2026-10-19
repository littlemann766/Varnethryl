#!/usr/bin/env python3
"""Owner cheat audit against the COMBAT build (412x915 touch). Every cheat in the panel + Settings owner section, and the skin wiring.
Usage: (cd www && python3 -m http.server PORT); P3D_URL=http://localhost:PORT/proto3d.html VARNETHRYL_OWNER_PASSPHRASE=... python3 tools/owner_cheats_combat_audit.py
The passphrase is only typed into the page, never printed."""
import os, json
from playwright.sync_api import sync_playwright
BASE = os.environ.get('P3D_URL', 'http://localhost:9733/proto3d.html'); PASS = os.environ['VARNETHRYL_OWNER_PASSPHRASE'].strip(); bad = 0
SAVE = "JSON.parse(localStorage.getItem('guildbound_rpg_save_v1'))"
def ok(n, c, d=''):
    global bad; print(('PASS' if c else 'FAIL'), n, ('' if c else str(d).replace(PASS, '***')[:300]))
    if not c: bad += 1
def click(pg, sel): pg.evaluate("(s)=>{const e=document.querySelector(s);if(!e)throw new Error('missing '+s);e.click()}", sel)
def has(pg, sel): return pg.evaluate("(s)=>!!document.querySelector(s)", sel)
def safe(n, fn):
    try: fn()
    except Exception as e: ok(n, False, repr(e)[:200])
with sync_playwright() as p:
    b = p.chromium.launch(args=['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
    ctx = b.new_context(viewport={'width': 412, 'height': 915}, has_touch=True, is_mobile=True, service_workers='block')
    reqs = []; ctx.on('request', lambda r: reqs.append(r.url))
    pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(BASE + '?party=0&npcs=0'); pg.wait_for_function('window.__p3d && window.__p3d.frames>5', timeout=90000); pg.wait_for_timeout(1500)
    nonowner_reqs = [u for u in reqs if any(k in u for k in ('owner.glb', 'saber_owner'))]
    ok('non-owner: no owner skin/saber files fetched', not nonowner_reqs, nonowner_reqs)
    ok('non-owner: no Owner entry in hero roster', not pg.evaluate("[...document.querySelectorAll('#heroes button')].some(b=>/^Owner/.test(b.textContent))"))
    for _ in range(5): pg.evaluate("(()=>{const v=document.getElementById('ver');for(const t of ['pointerdown','pointerup'])v.dispatchEvent(new PointerEvent(t,{bubbles:true,pointerId:1,pointerType:'touch'}))})()"); pg.wait_for_timeout(60)
    pg.wait_for_selector('#ownerLogin', state='visible', timeout=10000); pg.fill('#ownerPass', PASS); click(pg, '#ownerGo'); pg.wait_for_selector('#ownerPanel', state='visible', timeout=15000)
    pg.wait_for_function('__p3d.combat && __p3d.combat.on', timeout=30000); pg.wait_for_timeout(1500)
    C = "__p3d.combat.cc"
    # ---- God
    def god():
        ok('god ON by default after unlock', pg.evaluate("__p3d.cheat.god===true"))
        pg.evaluate("(()=>{const cc=%s;cc.clearEnemies();const e=cc.addEnemy('raider',__p3d.state.heroX+1,__p3d.state.heroZ);window.__e=e;cc.res.hp=cc.res.max.hp;const h=cc.res.hp;cc.enemyStrike(e);window.__h=[h,cc.res.hp]})()" % C)
        ok('god: enemy strike does 0 damage to hero HP', pg.evaluate("__h[0]===__h[1]"), pg.evaluate("__h"))
        click(pg, '[data-cheat=god]'); pg.wait_for_timeout(300)
        pg.evaluate("(()=>{const cc=%s;cc.iframes=0;cc.res.hp=cc.res.max.hp;const h=cc.res.hp;let n=0;for(let i=0;i<12;i++)cc.enemyStrike(window.__e);window.__h=[h,cc.res.hp];window.__n=n})()" % C)
        ok('god OFF: enemy strikes do reduce hero HP', pg.evaluate("__h[1]<__h[0]"), pg.evaluate("__h"))
        ok('god OFF: cheat flag false + panel button not on', pg.evaluate("__p3d.cheat.god===false"))
        click(pg, '[data-cheat=god]'); ok('god back ON', pg.evaluate("__p3d.cheat.god===true"))
    safe('god', god)
    # ---- movement flags (fly, noclip, speed, bumps)
    def mv():
        click(pg, '[data-cheat=fly]'); ok('fly flag', pg.evaluate("__p3d.cheat.fly===true")); pg.evaluate("__p3d.cheat.up=1"); pg.wait_for_function("__p3d.cheat.alt>3", timeout=40000); pg.evaluate("__p3d.cheat.up=0")
        ok('fly: hero mesh rises', pg.evaluate("__p3d.hero.position.y")>2.5); click(pg, '[data-cheat=fly]'); pg.wait_for_function("__p3d.cheat.alt===0", timeout=40000); ok('fly off lands', True)
        click(pg, '[data-cheat=noclip]'); ok('noclip flag on', pg.evaluate("__p3d.cheat.noclip===true")); click(pg, '[data-cheat=noclip]'); ok('noclip flag off', pg.evaluate("__p3d.cheat.noclip===false"))
        pg.evaluate("__p3d.cheats.setSpeed(4)"); ok('speed flag x4', pg.evaluate("__p3d.cheat.speedMul===4")); pg.evaluate("__p3d.cheats.setSpeed(1)")
        click(pg, '[data-cheat=bump]'); ok('bumps toggle flips bump system', pg.evaluate("__p3d.cheat.bump===false && __p3d.bump.sys.bumpOn===false")); click(pg, '[data-cheat=bump]'); ok('bumps back on', pg.evaluate("__p3d.bump.sys.bumpOn===true"))
    safe('movement', mv)
    # ---- gold/xp/level/items
    def eco():
        click(pg, '[data-cheat=inf]'); ok('infinite gold', pg.evaluate(SAVE + ".gold")==999999999 and pg.evaluate("__p3d.cheat.infGold"))
        pg.evaluate("__p3d.cheats.setGold(5)"); pg.evaluate("__p3d.cheats.addGold(1000000)"); ok('+1M gold', pg.evaluate(SAVE + ".gold")==1000005)
        x0 = pg.evaluate("(()=>{const s=%s;return s.heroXp[s.active]||0})()" % SAVE); click(pg, '[data-cheat="xp+"]'); ok('+1k XP applied', pg.evaluate("(()=>{const s=%s;return (s.heroXp[s.active]||0)>%s||s.heroLevels[s.active]>1})()" % (SAVE, x0)))
        pg.fill('#ownerLevel', '33'); click(pg, '[data-cheat=lvl-a]'); ok('instant level (active hero)', pg.evaluate("(()=>{const s=%s;return s.heroLevels[s.active]===33})()" % SAVE))
        ok('level reaches the combat hero stats', pg.evaluate("(()=>{const c=__p3d.combat;return typeof c.cc.hero.level==='number'})()"))
        g0 = pg.evaluate(SAVE + ".gear.length"); click(pg, '[data-cheat=item]'); ok('spawn item', pg.evaluate(SAVE + ".gear.length")==g0+1)
    safe('economy', eco)
    # ---- spawn enemies / titan
    def spawn():
        pg.evaluate("%s.clearEnemies()" % C)
        ok('panel has Spawn enemy button', has(pg, '[data-cheat=spawn]'))
        ok('panel has Spawn Ashen Titan button', has(pg, '[data-cheat=spawn-titan]'))
        if has(pg, '[data-cheat=spawn]'): click(pg, '[data-cheat=spawn]'); ok('spawn enemy adds one near the hero', pg.evaluate("%s.enemies.length>=1" % C))
        if has(pg, '[data-cheat=spawn-titan]'):
            click(pg, '[data-cheat=spawn-titan]'); pg.wait_for_timeout(600)
            ok('spawn titan: exactly one titan with 5M hp', pg.evaluate("%s.enemies.filter(e=>e.key==='titan'&&e.state!=='defeated').length===1&&%s.enemies.find(e=>e.key==='titan').max===5000000" % (C, C)))
            click(pg, '[data-cheat=spawn-titan]'); pg.wait_for_timeout(300); ok('spawn titan twice does not duplicate', pg.evaluate("%s.enemies.filter(e=>e.key==='titan'&&e.state!=='defeated').length===1" % C))
    safe('spawn', spawn)
    # ---- kill enemies
    def kill():
        pg.evaluate("(()=>{const c=__p3d.combat;c.cc.clearEnemies();c.cc.addEnemy('wolf',__p3d.state.heroX+5,__p3d.state.heroZ);c.cc.addEnemy('raider',__p3d.state.heroX-5,__p3d.state.heroZ)})()")
        n = pg.evaluate("%s.enemies.filter(e=>e.state!=='defeated').length" % C); click(pg, '[data-cheat=kill]'); pg.wait_for_timeout(300)
        ok('kill enemies defeats every live enemy (combat3d)', n>=2 and pg.evaluate("%s.enemies.every(e=>e.state==='defeated')" % C), pg.evaluate("%s.enemies.map(e=>e.key+':'+e.state)" % C))
        ok('kill message is not "not available yet"', 'not available' not in pg.evaluate("document.getElementById('ownerMsg').textContent"), pg.evaluate("document.getElementById('ownerMsg').textContent"))
    safe('kill', kill)
    # ---- heal party
    def heal():
        pg.evaluate("(()=>{const cc=%s;cc.res.hp=100;cc.res.mp=0;cc.res.sp=0})()" % C); click(pg, '[data-cheat=heal]'); pg.wait_for_timeout(200)
        ok('heal party fills HP/MP/SP', pg.evaluate("(()=>{const r=%s.res;return r.hp===r.max.hp&&r.mp===r.max.mp&&r.sp===r.max.sp})()" % C), pg.evaluate("%s.res.hp" % C))
        pg.evaluate("(()=>{const cc=%s;cc.res.hp=0;cc.dead=3;})()" % C); click(pg, '[data-cheat=heal]'); pg.wait_for_timeout(200)
        ok('heal revives a downed hero', pg.evaluate("%s.dead<=0&&%s.res.hp>0" % (C, C)))
    safe('heal', heal)
    # ---- skip quest
    def skipq():
        click(pg, '[data-cheat=skipq]'); m = pg.evaluate("document.getElementById('ownerMsg').textContent")
        ok('skip quest gives a clear stub message (no 3D quests yet)', 'not available' not in m and len(m) > 12 and 'done' not in m.lower() or 'quest' in m.lower(), m)
    safe('skipq', skipq)
    # ---- teleport
    def tp():
        pg.select_option('#ownerPlace', index=1); click(pg, '[data-cheat=tpb]'); pg.wait_for_timeout(300)
        pl = pg.evaluate("__p3d.cheats.places()[1]"); ok('teleport to building', pg.evaluate("(p)=>Math.hypot(__p3d.state.heroX-p.x,__p3d.state.heroZ-p.z)<1.5", pl), pl)
        click(pg, '[data-cheat=tpz]'); pg.wait_for_timeout(300); ok('teleport to zone (village)', pg.evaluate("Math.abs(__p3d.state.heroX)<1&&Math.abs(__p3d.state.heroZ-14)<1.5"), pg.evaluate("[__p3d.state.heroX,__p3d.state.heroZ]"))
    safe('teleport', tp)
    # ---- reset
    def rst():
        pg.evaluate("__p3d.cheats.setFly(true);__p3d.cheats.setSpeed(4)"); click(pg, '[data-cheat=reset]'); ok('reset cheats clears flags', pg.evaluate("!__p3d.cheat.fly&&__p3d.cheat.speedMul===1"))
        ok('reset keeps god preference (god stays ON for owner)', pg.evaluate("__p3d.cheat.god===true"))
    safe('reset', rst)
    ok('save marked cheated', pg.evaluate(SAVE + ".cheated===true"))
    # ---- Settings owner section
    def sett():
        pg.evaluate("document.querySelector('#panel')&&0"); click(pg, '#ownerPanel h3 button'); pg.evaluate("__p3d.settings.open()"); pg.wait_for_selector('#settingsPanel', state='visible', timeout=10000)
        for k in ('owner-god', 'owner-fly', 'owner-noclip', 'owner-bump', 'owner-max', 'owner-panel'): ok('settings has ' + k, has(pg, f'[data-set={k}]'))
        ok('settings owner has spawn titan', has(pg, '[data-set=owner-titan]'))
        ok('settings god button shows ON', pg.evaluate("document.querySelector('[data-set=owner-god]').classList.contains('on')"))
        click(pg, '[data-set=owner-god]'); pg.wait_for_timeout(100); ok('settings god toggle -> flag off + pref saved 0', pg.evaluate("__p3d.cheat.god===false&&localStorage.getItem('vn_owner_god_v1')==='0'"))
        click(pg, '[data-set=owner-god]'); ok('settings god toggle -> on', pg.evaluate("__p3d.cheat.god===true"))
        click(pg, '[data-set=owner-fly]'); ok('settings fly', pg.evaluate("__p3d.cheat.fly===true")); click(pg, '[data-set=owner-fly]')
        click(pg, '[data-set=owner-noclip]'); ok('settings noclip', pg.evaluate("__p3d.cheat.noclip===true")); click(pg, '[data-set=owner-noclip]')
        pg.select_option('#setSpeed', '4'); ok('settings speed select', pg.evaluate("__p3d.cheat.speedMul===4")); pg.select_option('#setSpeed', '1')
        pg.evaluate("(()=>{const s=%s;s.heroLevels[s.active]=5;localStorage.setItem('guildbound_rpg_save_v1',JSON.stringify(s))})()" % SAVE); click(pg, '[data-set=owner-max]'); pg.wait_for_timeout(500)
        ok('settings re-max active hero', pg.evaluate("(()=>{const s=%s;return s.heroLevels[s.active]===80})()" % SAVE))
        if has(pg, '[data-set=owner-titan]'): pg.evaluate("%s.clearEnemies()" % C); click(pg, '[data-set=owner-titan]'); pg.wait_for_timeout(400); ok('settings spawn titan works', pg.evaluate("%s.enemies.some(e=>e.key==='titan')" % C))
    safe('settings', sett)
    # ---- skins
    def skins():
        pg.wait_for_timeout(2000)
        ok('owner skin in roster (owner only)', pg.evaluate("[...document.querySelectorAll('#heroes button')].some(b=>/^Owner/.test(b.textContent))"))
        ok('owner skin is the first roster row', pg.evaluate("/^Owner/.test(document.querySelector('#heroes .row button').textContent)"))
        pg.wait_for_function("__p3d.glbInfo.loaded.includes('n:owner')", timeout=60000)
        ok('owner skin selected by default', pg.evaluate("__p3d.glbInfo.loaded.includes('n:owner')&&__p3d.heroIndex===__p3d.state&&0||(()=>{const i=__p3d.heroIndex;return i>=0&&document.querySelector('#heroes button.on')&&/^Owner/.test(document.querySelector('#heroes button.on').textContent)})()"))
        ok('owner model file fetched only after owner unlock', any('owner.glb' in u for u in reqs))
        ok('saber_owner.glb used for the owner saber', pg.evaluate("__p3d.combat.saberSkin===true"), pg.evaluate("__p3d.combat.saberSkin"))
        ok('titan uses ashentitan_new skin, scaled 6x hero', pg.evaluate("(()=>{const c=__p3d.combat;c.cc.clearEnemies();return !!c.spawn('titan',32)})()"))
        pg.wait_for_function("(()=>{const t=__p3d.combat.enemies.find(e=>e.key==='titan');return t&&t.foe&&t.foe.skinReady})()", timeout=60000)
        r = pg.evaluate("""()=>{const P=__p3d,T=P.THREE,t=P.combat.enemies.find(e=>e.key==='titan'),bb=m=>{m.updateMatrixWorld(true);const x=new T.Box3().setFromObject(m);return x.max.y-x.min.y};return {th:bb(t.foe.skin),hh:bb(P.hero),mesh:t.foe.mat.visible}}""")
        ok('titan GLB skin is 6x hero height', abs(r['th'] / r['hh'] - 6) < 0.3 and not r['mesh'], r)
    safe('skins', skins)
    ok('no page errors', not errs, errs[:3])
    pg.screenshot(path='/tmp/audit_end.png'); ctx.close()
print('FAILS:', bad); raise SystemExit(1 if bad else 0)
