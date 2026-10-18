"""Playwright walk-through of "The Mirrored Flame" quest line (Kael Runebinder and Rowan Firebrand).
Usage: serve www/ (python3 -m http.server 8111 -d www) then VN_URL=http://localhost:8111/index2d.html python3 tools/mirror_test.py
Story panels, travel, swapping heroes, trading staves, the Mirror Trial and cracking the glass use real taps;
window.__vn.Mirror.debug only shortens fights."""
import os, json, sys
from playwright.sync_api import sync_playwright
URL = os.environ.get('VN_URL', 'http://localhost:8111/index2d.html')
res = []
def ok(n, c):
    res.append(bool(c)); print(('PASS' if c else 'FAIL'), n)
def tap_ok(pg, sel, name):
    bb = pg.locator(sel).first.bounding_box()
    ok(f'tap target >=44px: {name}', bb and bb['height'] >= 43.5 and bb['width'] >= 43.5)
def walk(pg, picks=None, check_taps=False):
    picks = picks or {}; n = 0
    while pg.evaluate("document.getElementById('storyDlg').open"):
        if check_taps and n == 0:
            tap_ok(pg, '#stNext', 'story Next'); tap_ok(pg, '#stSkip', 'story Skip')
        ch = pg.locator('.stChoice')
        if ch.count():
            key = ch.first.get_attribute('data-key'); pid = picks.get(key)
            (pg.locator(f'.stChoice[data-id="{pid}"]').first if pid else ch.first).click()
        else: pg.click('#stNext')
        n += 1; assert n < 40, 'panel loop'; pg.wait_for_timeout(30)
def mq(pg): return pg.evaluate("JSON.parse(JSON.stringify(window.__vn.state.mirror))")
def safe(pg): pg.evaluate("window.__vn.Mirror.debug.playerSafe()")
def newpage(p):
    b = p.chromium.launch()
    ctx = b.new_context(viewport={'width': 390, 'height': 844}, has_touch=True, is_mobile=True, service_workers='block')
    pg = ctx.new_page(); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e))); pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None)
    return b, pg, errs
def run(p, label, puzzle_wrong, ending):
    b, pg, errs = newpage(p)
    pg.goto(URL); pg.wait_for_timeout(500)
    names = pg.evaluate("window.__vn.Mirror.debug.heroNames()")
    K, R = names.index('Kael Runebinder'), names.index('Rowan Firebrand')
    cap0 = pg.evaluate("window.__vn.state.partyCap")
    # legacy save without mirror key
    pg.evaluate("(()=>{const s=JSON.parse(JSON.stringify(window.__vn.state));delete s.mirror;s.kills=0;s.questStep=0;localStorage.setItem('guildbound_rpg_save_v1',JSON.stringify(s))})()")
    pg.reload(); pg.wait_for_timeout(600)
    q = mq(pg); ok(f'{label}: legacy save loads with default mirror state', q['stage'] == 'locked' and q['ch'] == 1 and q['done'] == [])
    ok(f'{label}: card visible while locked', pg.locator('#mirrorCard').is_visible())
    pg.evaluate("window.__vn.state.kills=6"); pg.wait_for_timeout(700)
    ok(f'{label}: banner appears', pg.locator('#mirrorBanner').is_visible())
    tap_ok(pg, '#mqBanner', 'banner')
    veyra_before = pg.evaluate("window.__vn.state.veyra.stage")
    ids = ['M1', 'M2', 'M3', 'M4', 'M5', 'M6', 'M7']
    for i, cid in enumerate(ids):
        q = mq(pg); ok(f'{label}: {cid} offered', q['stage'] == 'offer' and q['ch'] == i + 1)
        pg.evaluate("document.getElementById('mqRead')&&document.getElementById('mqRead').scrollIntoView()")
        pg.click('#mqBanner' if cid == 'M1' else '#mqRead')
        walk(pg, picks={'mq_first': 'rowan'}, check_taps=(cid in ('M1', 'M5')))
        q = mq(pg); ok(f'{label}: {cid} intro leads to active', q['stage'] == 'active')
        if cid == 'M1':
            ok(f'{label}: M1 choice saved', q['choices'].get('mq_first') == 'rowan')
            ok(f'{label}: Kael and Rowan unlocked', pg.evaluate("(a)=>a.every(i=>window.__vn.state.unlocked.includes(i))", [K, R]))
        need = pg.evaluate("window.__vn.Mirror.debug.chapters()[%d].zone" % i)
        if pg.evaluate("window.__vn.state.zone") != need:
            tap_ok(pg, '#mqGoto', 'travel button'); pg.click('#mqGoto'); pg.wait_for_timeout(300)
        ok(f'{label}: {cid} in zone {need}', pg.evaluate("window.__vn.state.zone") == need)
        fights = pg.evaluate("window.__vn.Mirror.debug.chapters()[%d].fights" % i)
        if cid == 'M2':
            ok(f'{label}: M2 both heroes in party', pg.evaluate("(a)=>a.every(i=>window.__vn.state.party.includes(i))", [K, R]))
            # must play as both: start with whichever is NOT active, then the other
            act = pg.evaluate("window.__vn.state.active")
            first, second = (K, R) if act != K else (R, K)
            safe(pg); pg.wait_for_function("window.__vn.runtime.enemy.some(e=>e.mq&&e.hp>0)", timeout=8000)
            pg.evaluate("window.__vn.Mirror.debug.killQuestEnemies()"); pg.wait_for_timeout(900)
            q = mq(pg); ok(f'{label}: M2 not complete until both heroes were played', 'M2' not in q['done'] and q['stage'] == 'active')
            for hid_ in (K, R):
                pg.evaluate("(i)=>window.__vn.state.active!==i&&document.querySelector(`[data-switch='${i}']`).click()", hid_); pg.wait_for_timeout(450)
            pg.wait_for_function("window.__vn.state.mirror.done.includes('M2')", timeout=6000)
            pg.wait_for_selector('#storyDlg[open]', timeout=4000); walk(pg)
            q = mq(pg); ok(f'{label}: M2 complete after switching', 'M2' in q['done'] and q['swapK'] and q['swapR'])
            continue
        if cid == 'M4':
            tap_ok(pg, '#mqTrade', 'trade staves'); 
            safe(pg); pg.wait_for_function("window.__vn.runtime.enemy.some(e=>e.mq&&e.hp>0)", timeout=8000)
            pg.evaluate("window.__vn.Mirror.debug.killQuestEnemies()"); pg.wait_for_timeout(300)
            ok(f'{label}: M4 not complete before trading staves', 'M4' not in mq(pg)['done'])
            pg.click('#mqTrade'); pg.wait_for_selector('#storyDlg[open]', timeout=6000); walk(pg)
            q = mq(pg); ok(f'{label}: M4 complete, Mirror Bond granted', 'M4' in q['done'] and 'Mirror Bond' in q['items'] and 'hollow' in q['zones'])
            ok(f'{label}: Brynn recruited', 'Brynn Cogwright' in q['recruits'])
            continue
        if cid == 'M5':
            tap_ok(pg, '#mqTrial', 'mirror trial button')
            pg.click('#mqTrial')
            picks = {'mq_r1': 'a', 'mq_r2': 'b', 'mq_r3': 'a'} if puzzle_wrong else {'mq_r1': 'b', 'mq_r2': 'a', 'mq_r3': 'b'}
            walk(pg, picks=picks)
            q = mq(pg); ok(f'{label}: M5 trial done, mistakes={3 if puzzle_wrong else 0}', q['puzzleDone'] and q['mistakes'] == (3 if puzzle_wrong else 0))
            safe(pg); pg.wait_for_function("window.__vn.runtime.enemy.some(e=>e.mq&&!e.mqx&&e.hp>0)", timeout=8000)
            shades = pg.evaluate("window.__vn.runtime.enemy.filter(e=>e.mqx).length")
            ok(f'{label}: M5 Mirror Shades = mistakes', shades == (3 if puzzle_wrong else 0))
            pg.evaluate("window.__vn.Mirror.debug.finishWarden()"); pg.wait_for_selector('#storyDlg[open]', timeout=6000); walk(pg)
            q = mq(pg); ok(f'{label}: M5 complete, Starforge unlocked', 'M5' in q['done'] and 'starforge' in q['zones'])
            continue
        if cid == 'M6':
            safe(pg); pg.wait_for_function("window.__vn.runtime.enemy.some(e=>e.mqw&&e.hp>0)", timeout=8000)
            pg.wait_for_timeout(200)
            drawn = pg.evaluate("window.__vn.runtime.drawn"); ok(f'{label}: M6 one sprite per hero', len(drawn) == len(set(drawn)))
            pg.evaluate("window.__vn.Mirror.debug.setWardenHp(.4)"); pg.wait_for_timeout(900)
            ok(f'{label}: M6 shield phase', pg.evaluate("window.__vn.Mirror.status().phase") == 2)
            hp0 = pg.evaluate("window.__vn.runtime.enemy.find(e=>e.mqw).hp")
            pg.evaluate("window.__vn.hitEnemy(window.__vn.runtime.enemy.find(e=>e.mqw),window.__vn.state.active,50)")
            ok(f'{label}: M6 shield blocks damage', pg.evaluate("window.__vn.runtime.enemy.find(e=>e.mqw).hp") >= hp0)
            tap_ok(pg, '#mqCrack', 'crack button')
            pg.evaluate("(i)=>window.__vn.state.active!==i&&document.querySelector(`[data-switch='${i}']`).click()", K); pg.wait_for_timeout(200)
            pg.click('#mqCrack'); pg.wait_for_timeout(300)
            ok(f'{label}: one crack does not break shield', pg.evaluate("window.__vn.Mirror.status().phase") == 2 and mq(pg)['crackK'] and not mq(pg)['crackR'])
            pg.click('#mqCrack'); pg.wait_for_timeout(300)
            ok(f'{label}: same hero twice does not break it', pg.evaluate("window.__vn.Mirror.status().phase") == 2)
            pg.evaluate("(i)=>document.querySelector(`[data-switch='${i}']`).click()", R); pg.wait_for_timeout(200)
            pg.click('#mqCrack'); pg.wait_for_timeout(600)
            ok(f'{label}: Kael then Rowan breaks shield', pg.evaluate("window.__vn.Mirror.status().phase") == 3)
            pg.evaluate("window.__vn.Mirror.debug.finishWarden()"); pg.wait_for_selector('#storyDlg[open]', timeout=6000); walk(pg)
            q = mq(pg); ok(f'{label}: M6 complete', 'M6' in q['done']); continue
        if cid == 'M7':
            ok(f'{label}: M7 needs no fight, finishes in Liongate', pg.evaluate("window.__vn.state.zone") == 'village')
            pg.wait_for_selector('#storyDlg[open]', timeout=6000); walk(pg, picks={'mq_end': ending})
            q = mq(pg); ok(f'{label}: M7 ending {ending}', q['ending'] == ending and q['stage'] == 'finished' and q['title'] == 'Mirrorbound' and "Brothers' Rune" in q['items'])
            continue
        for f in range(fights):
            safe(pg); pg.wait_for_function("window.__vn.runtime.enemy.some(e=>e.mq&&e.hp>0)", timeout=8000); pg.wait_for_timeout(150)
            drawn = pg.evaluate("window.__vn.runtime.drawn"); ok(f'{label}: {cid} fight {f+1} one sprite per hero', len(drawn) == len(set(drawn)))
            pg.evaluate("window.__vn.Mirror.debug.killQuestEnemies()"); pg.wait_for_timeout(400)
        pg.wait_for_selector('#storyDlg[open]', timeout=6000); walk(pg)
        ok(f'{label}: {cid} complete', cid in mq(pg)['done'])
    q = mq(pg)
    pg.wait_for_timeout(400)
    sv = json.loads(pg.evaluate("localStorage.getItem('guildbound_rpg_save_v1')"))
    ok(f'{label}: save key unchanged, version 1, additive mirror key', sv['version'] == 1 and 'mirror' in sv and 'veyra' in sv)
    ok(f'{label}: Veyra quest untouched by Mirror quest', pg.evaluate("window.__vn.state.veyra.stage") in ('locked', 'offer') and pg.evaluate("window.__vn.state.veyra.done.length") == 0)
    ok(f'{label}: party cap unchanged, no duplicate party members', pg.evaluate("window.__vn.state.partyCap") == cap0 and pg.evaluate("new Set(window.__vn.state.party).size===window.__vn.state.party.length") and pg.evaluate("window.__vn.state.party.length") <= cap0)
    ok(f'{label}: Kael and Rowan both in party', pg.evaluate("(a)=>a.every(i=>window.__vn.state.party.includes(i))", [K, R]))
    a = pg.evaluate("window.__vn.Mirror.atk()"); ok(f'{label}: Mirror Bond buff active ({a:.2f})', a > 1.05)
    if ending == 'unity': ok(f'{label}: unity gives bigger buff than base', a >= 1.18)
    else: ok(f'{label}: paths gear (scarf and cloak) added', all(any(g['name'] == n for g in sv['gear']) for n in ['Silver Rune Scarf', 'Red Ember Cloak']))
    pg.evaluate("document.getElementById('mqJournal').click()"); pg.wait_for_timeout(250)
    ok(f'{label}: journal lists 7 mirror chapters', pg.locator('#mqChapters li').count() == 7)
    pg.click('#closeModal')
    pg.reload(); pg.wait_for_timeout(700); ok(f'{label}: progress survives reload', mq(pg)['stage'] == 'finished' and mq(pg)['ending'] == ending)
    ok(f'{label}: no console errors', not errs); print(errs[:3])
    b.close()
with sync_playwright() as p:
    run(p, 'unity', False, 'unity')
    run(p, 'paths', True, 'paths')
    # import of an old backup (no mirror key) keeps working
    b, pg, errs = newpage(p); pg.goto(URL); pg.wait_for_timeout(500)
    ok('ensure() repairs junk mirror data', pg.evaluate("(()=>{const s={mirror:{ch:99,stage:'x',done:'no',choices:[]}};window.__vn.Mirror.ensure(s);return s.mirror.ch===7&&s.mirror.stage==='locked'&&Array.isArray(s.mirror.done)&&!Array.isArray(s.mirror.choices)})()"))
    b.close()
print(f"{sum(res)}/{len(res)} checks passed")
sys.exit(0 if all(res) else 1)
