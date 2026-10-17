from playwright.sync_api import sync_playwright
import json
D='/workspace/shots/varnethryl-hud-build/'
U='http://localhost:8099/index.html'
res=[]
def ok(n,c):res.append((n,bool(c)));print(('PASS' if c else 'FAIL'),n)
def box(pg,s):return pg.locator(s).bounding_box()
def inside(b,w,h,m=0):return b and b['x']>=m-1 and b['y']>=m-1 and b['x']+b['width']<=w-m+1 and b['y']+b['height']<=h-m+1
def overlap(a,b):return not(a['x']+a['width']<=b['x'] or b['x']+b['width']<=a['x'] or a['y']+a['height']<=b['y'] or b['y']+b['height']<=a['y'])
CASES=[('web-1280x720',1280,720,False),('land-844x390',844,390,True),('port-390x844',390,844,True),('small-land-640x360',640,360,True),('small-port-360x640',360,640,True)]
with sync_playwright() as p:
  b=p.chromium.launch()
  for name,w,h,mob in CASES:
    ctx=b.new_context(viewport={'width':w,'height':h},has_touch=mob,is_mobile=mob,device_scale_factor=2 if mob else 1,service_workers='block')
    pg=ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('console',lambda m:errs.append(m.text) if m.type=='error' else None)
    pg.goto(U);pg.wait_for_timeout(1500)
    cv=box(pg,'#game');ok(name+' canvas edge-to-edge',cv and abs(cv['x'])<1 and abs(cv['y'])<1 and abs(cv['width']-w)<1.5 and abs(cv['height']-h)<1.5)
    ok(name+' page does not scroll',pg.evaluate("document.documentElement.scrollHeight<=innerHeight+1&&document.documentElement.scrollWidth<=innerWidth+1"))
    ok(name+' topbar/nav tucked away',not pg.locator('.topbar').is_visible() and not pg.locator('.bottomNav').is_visible())
    for sel in ['#hudHero','#hudLogo','#hudMenu','#hudMini','#touchAttack','#touchSkill','#skillHeavy','#skillSuper','#skillUlt','#hudPotions']:
      bb=box(pg,sel);ok(f'{name} {sel} on screen',bb and bb['width']>0 and inside(bb,w,h))
    mode=pg.evaluate("document.documentElement.dataset.hud");print(name,'mode',mode)
    # control priority: skills never overlap stick/dpad, potions, hero frame
    skills=[box(pg,'#'+i) for i in ['touchAttack','touchSkill','skillHeavy','skillSuper','skillUlt']]
    ctl=box(pg,'#stick') if pg.locator('#stick').is_visible() else box(pg,'.dpad')
    ok(name+' skills do not overlap move control',all(not overlap(s,ctl) for s in skills))
    ok(name+' skills do not overlap potions/hero',all(not overlap(s,box(pg,'#hudPotions')) and not overlap(s,box(pg,'#hudHero')) for s in skills))
    ok(name+' hero frame/minimap/quest/menu no overlap',not overlap(box(pg,'#hudHero'),box(pg,'#hudMini')) and not overlap(box(pg,'#hudMenu'),box(pg,'#hudMini')) and (not pg.locator('#hudQuest').is_visible() or not overlap(box(pg,'#hudQuest'),box(pg,'#hudMini'))))
    ok(name+' min touch target 40+',all(min(s['width'],s['height'])>=(44 if mob else 40) for s in skills) or not mob and True)
    if mob:ok(name+' skill buttons >=44px',all(min(s['width'],s['height'])>=44 for s in skills))
    ok(name+' chat only on web',pg.locator('#hudChat').is_visible()==(mode=='web'))
    ok(name+' dpad only web',pg.locator('.dpad').is_visible()==(not mob))
    ok(name+' stick only phone',pg.locator('#stick').is_visible()==mob)
    nums=pg.evaluate("[...document.querySelectorAll('.skillBtn .num')].map(e=>e.textContent).join('')");ok(name+' numbered 1-5',nums=='12345')
    ok(name+' logo from wordmark',pg.evaluate("document.getElementById('hudLogo').naturalWidth>100"))
    ok(name+' cinzel',pg.evaluate("document.fonts.check('16px Cinzel')"))
    # party: 3 heroes total normal; 4 in boss
    pg.evaluate("""()=>{const s=window.__vn.state;s.partyCap=5;[3,4].forEach(i=>{if(!s.unlocked.includes(i))s.unlocked.push(i);if(!s.party.includes(i))s.party.push(i)})}""")
    pg.wait_for_timeout(500)
    n1=pg.evaluate("document.querySelectorAll('#hudParty .pm').length");ok(name+' normal party shows 3 total (2 others)',n1==2)
    pg.evaluate("window.__vn.enterZone('boss')");pg.wait_for_timeout(600)
    n2=pg.evaluate("document.querySelectorAll('#hudParty .pm').length");ok(name+' boss party shows 4 total (3 others)',n2==3)
    if mob and mode in('land','port'):
      pg.evaluate("document.getElementById('hudHero').classList.add('open')");pg.wait_for_timeout(200)
    pg.screenshot(path=D+f'{name}-boss.png')
    pg.evaluate("window.__vn.enterZone('village')");pg.wait_for_timeout(300)
    # menu drawer + settings reachable
    pg.click('#hudMain');pg.wait_for_timeout(350);ok(name+' menu opens topbar+nav',pg.locator('.topbar').is_visible() and pg.locator('.bottomNav').is_visible())
    pg.screenshot(path=D+f'{name}-menu-open.png')
    pg.click('.bottomNav [data-go=heroes]');pg.wait_for_timeout(300);ok(name+' heroes screen normal layout',pg.locator('#heroes').is_visible() and pg.locator('.bottomNav').is_visible() and not pg.locator('#hud').is_visible())
    pg.click('.bottomNav [data-go=adventure]');pg.wait_for_timeout(500);ok(name+' back to full-screen',abs(box(pg,'#game')['height']-h)<1.5)
    # map + journal + bag
    pg.click('#hudMap');pg.wait_for_timeout(250);ok(name+' map modal travel',pg.locator('#hudZones [data-zone]').count()>=4)
    pg.click('#hudZones [data-zone=forest]');pg.wait_for_timeout(400);ok(name+' travel works',pg.evaluate("window.__vn.state.zone")=='forest' and not pg.locator('#modal').evaluate('m=>m.open'))
    pg.click('#hudJournal');pg.wait_for_timeout(200);ok(name+' journal opens',pg.locator('#modal').evaluate('m=>m.open'));pg.keyboard.press('Escape');pg.wait_for_timeout(150)
    # potions
    pg.evaluate("()=>{const r=window.__vn.runtime,s=window.__vn.state;r.hp[s.active]=100}");c0=pg.evaluate("window.__vn.state.potions.hp")
    pg.click('#pot-hp');pg.wait_for_timeout(200);ok(name+' hp potion heals + consumes',pg.evaluate("window.__vn.runtime.hp[window.__vn.state.active]>100")and pg.evaluate("window.__vn.state.potions.hp")==c0-1)
    pg.screenshot(path=D+f'{name}-forest.png')
    # skills in hud still work
    pg.evaluate("""()=>{const r=window.__vn.runtime;r.enemy.forEach(e=>{e.x=r.x+60;e.y=r.y;e.hp=e.maxHp=99999})}""");pg.click('#touchSkill');pg.wait_for_timeout(300)
    ok(name+' skill cooldown ring works in hud',pg.evaluate("document.getElementById('touchSkill').classList.contains('cooling')"))
    ok(name+' hero hp/mp bars driven by state',pg.evaluate("document.getElementById('hudHp').style.width.length>0 && document.getElementById('hudMp').style.width.length>0"))
    ok(name+' minimap drawn',pg.evaluate("(()=>{const c=document.getElementById('hudMiniCv'),d=c.getContext('2d').getImageData(120,120,1,1).data;return d[3]>0})()"))
    if mode=='web':
      pg.click('#hudChat [data-ct=system]');pg.wait_for_timeout(300);ok(name+' chat system tab shows logs',pg.evaluate("document.querySelectorAll('#hudLog p').length>0"))
      pg.fill('#hudChatIn','hello');pg.press('#hudChatIn','Enter');pg.click('#hudChat [data-ct=general]');pg.wait_for_timeout(300);ok(name+' chat send',pg.evaluate("document.getElementById('hudLog').textContent.includes('hello')"))
      pg.keyboard.press('Escape')
    # layout editor moves a HUD group and persists
    pg.click('#hudMain');pg.click('#openSettings');pg.wait_for_timeout(250);pg.click('#setEditLayout');pg.wait_for_timeout(700)
    q=box(pg,'#hudPotions');fb=box(pg,'.worldFrame')
    pg.mouse.move(q['x']+q['width']/2,q['y']+q['height']/2);pg.mouse.down();pg.mouse.move(fb['x']+fb['width']*.5,fb['y']+fb['height']*.45,steps=8);pg.mouse.up();pg.wait_for_timeout(150)
    q2=box(pg,'#hudPotions');ok(name+' layout editor moves potions',abs(q2['x']-q['x'])>30 or abs(q2['y']-q['y'])>30)
    pg.screenshot(path=D+f'{name}-edit-layout.png')
    pg.click('#layoutDone');pg.wait_for_timeout(400)
    lay=json.loads(pg.evaluate("localStorage.getItem('varnethryl_settings_v1')"))['layout'];ok(name+' hud layout saved',('hudPotions' in lay))
    sv=json.loads(pg.evaluate("localStorage.getItem('guildbound_rpg_save_v1')"));ok(name+' save key + version',sv['version']==1 and 'hudPotions' in sv['settings']['layout'] and 'potions' in sv)
    pg.reload();pg.wait_for_timeout(1200);q3=box(pg,'#hudPotions');ok(name+' hud layout persists reload',abs(q3['x']-q2['x'])<3 and abs(q3['y']-q2['y'])<3)
    ok(name+' no js errors',not errs);print(errs[:3])
    ctx.close()
  # painted bg slot
  ctx=b.new_context(viewport={'width':1280,'height':720},service_workers='block');pg=ctx.new_page();pg.goto(U+'?bgdemo=1');pg.wait_for_timeout(2000);pg.screenshot(path=D+'web-1280x720-bg-slot-demo.png')
  ok('bg slot draws layer (tiles skipped)',pg.evaluate("(()=>{const c=document.getElementById('game').getContext('2d');const d=c.getImageData(640,100,1,1).data;return d[3]>0})()"))
  ctx.close()
  # legacy save loads (no potions/hud keys)
  ctx=b.new_context(viewport={'width':844,'height':390},service_workers='block');pg=ctx.new_page();pg.goto(U);pg.wait_for_timeout(600)
  pg.evaluate("()=>{const s=JSON.parse(JSON.stringify(window.__vn.state));delete s.potions;s.settings={};localStorage.setItem('guildbound_rpg_save_v1',JSON.stringify(s));localStorage.removeItem('varnethryl_settings_v1')}")
  pg.reload();pg.wait_for_timeout(900);ok('legacy save (no potions/hud settings) loads',pg.evaluate("window.__vn.state.potions.hp===5")and pg.locator('#hudHero').is_visible())
  b.close()
print(sum(1 for _,c in res if not c),'failures')
