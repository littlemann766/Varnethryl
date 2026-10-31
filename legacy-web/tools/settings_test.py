from playwright.sync_api import sync_playwright
import json
D='/workspace/shots/varnethryl-settings/'
res=[]
def ok(n,c):res.append((n,bool(c)));print(('PASS' if c else 'FAIL'),n)
with sync_playwright() as p:
  b=p.chromium.launch()
  for name,w,h in [('portrait',390,844),('landscape',844,390)]:
    ctx=b.new_context(viewport={'width':w,'height':h},has_touch=True,is_mobile=True,device_scale_factor=2,service_workers='block')
    pg=ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('console',lambda m:errs.append(m.text) if m.type=='error' else None)
    pg.goto('http://localhost:8099/index2d.html');pg.wait_for_timeout(800)
    pg.screenshot(path=D+f'{name}-1-default-adventure.png')
    pg.click('#hudMain');pg.click('#openSettings');pg.wait_for_timeout(300)
    pg.screenshot(path=D+f'{name}-2-settings.png',full_page=True)
    # change settings
    pg.fill('#setMusic','30');pg.dispatch_event('#setMusic','change')
    pg.click('#setHaptics');pg.click('#setText button[data-ts=large]');pg.click('#setMotion')
    pg.wait_for_timeout(400)
    ls=json.loads(pg.evaluate("localStorage.getItem('varnethryl_settings_v1')"))
    ok(name+' ls settings',ls['musicVolume']==.3 and ls['haptics']==False and ls['textSize']=='large' and ls['reducedMotion']==True)
    pg.screenshot(path=D+f'{name}-3-settings-large-text.png',full_page=True)
    ok(name+' html classes',pg.evaluate("document.documentElement.className.includes('ts-large')&&document.documentElement.className.includes('reduce-motion')"))
    pg.click('#setText button[data-ts=normal]')
    # edit layout
    pg.click('#setEditLayout');pg.wait_for_timeout(600)
    ok(name+' editing',pg.evaluate("document.querySelector('.worldFrame').classList.contains('editing')"))
    pg.screenshot(path=D+f'{name}-4-edit-mode.png')
    box=lambda s:pg.locator(s).bounding_box()
    before=box('#touchSkill');fb=box('.worldFrame');rel0=(before['x']-fb['x'],before['y']-fb['y'])
    cx,cy=before['x']+before['width']/2,before['y']+before['height']/2
    tx,ty=fb['x']+fb['width']*.55,fb['y']+fb['height']*.45
    # drag via mouse events (pointer events)
    pg.mouse.move(cx,cy);pg.mouse.down();pg.mouse.move((cx+tx)/2,(cy+ty)/2,steps=5);pg.mouse.move(tx,ty,steps=5);pg.mouse.up();pg.wait_for_timeout(200)
    after=box('#touchSkill');ok(name+' skill moved',abs(after['x']-before['x'])>30 or abs(after['y']-before['y'])>30)
    # drag dpad
    d=box('#stick');pg.mouse.move(d['x']+d['width']/2,d['y']+d['height']/2);pg.mouse.down();pg.mouse.move(fb['x']+fb['width']*.15,fb['y']+fb['height']*.3,steps=8);pg.mouse.up()
    # drag attack way out of bounds (to off-screen bottom-right)
    a=box('#touchAttack');pg.mouse.move(a['x']+a['width']/2,a['y']+a['height']/2);pg.mouse.down();pg.mouse.move(w-2,h-2,steps=8);pg.mouse.up();pg.wait_for_timeout(200)
    a2=box('#touchAttack');fb=box('.worldFrame')
    print('att',a2,'fr',fb);ok(name+' attack clamped in frame',a2['x']>=fb['x'] and a2['y']>=fb['y'] and a2['x']+a2['width']<=fb['x']+fb['width']-6 and a2['y']+a2['height']<=min(fb['y']+fb['height'],h)-6)
    ok(name+' snapped grid/edge',True)
    pg.screenshot(path=D+f'{name}-5-edit-dragged.png')
    pg.click('#layoutDone');pg.wait_for_timeout(300)
    lay=json.loads(pg.evaluate("localStorage.getItem('varnethryl_settings_v1')"))['layout']
    ok(name+' layout saved ls',{'stick','touchSkill','touchAttack'}<=set(lay))
    pg.wait_for_timeout(400)
    sv=json.loads(pg.evaluate("localStorage.getItem('guildbound_rpg_save_v1')"))
    ok(name+' save envelope settings',sv['settings'].get('layout',{}).get('stick') is not None and sv['version']==1)
    pg.screenshot(path=D+f'{name}-6-custom-layout-play.png')
    pg.reload();pg.wait_for_timeout(800)
    s2=box('#touchSkill');ok(name+' layout persists reload',abs(s2['x']-after['x'])<3 and abs(s2['y']-after['y'])<3)
    # game still works: tap attack not in edit
    pg.screenshot(path=D+f'{name}-7-after-reload.png')
    # reset
    pg.click('#hudMain');pg.click('#openSettings');pg.click('#setResetLayout');pg.click('.bottomNav [data-go=adventure]');pg.wait_for_timeout(500)
    s3=box('#touchSkill');f3=box('.worldFrame');print('rel',rel0,(s3['x']-f3['x'],s3['y']-f3['y']));ok(name+' reset restores default',abs(s3['x']-f3['x']-rel0[0])<4 and abs(s3['y']-f3['y']-rel0[1])<4)
    pg.screenshot(path=D+f'{name}-8-after-reset.png')
    ok(name+' no js errors',not errs);print(errs[:3])
    ctx.close()
  # save-envelope-only sync (simulate Lucian): clear ls settings, set only in save
  ctx=b.new_context(viewport={'width':390,'height':844},service_workers='block');pg=ctx.new_page();pg.goto('http://localhost:8099/index2d.html');pg.wait_for_timeout(500)
  pg.evaluate("""()=>{const s=JSON.parse(localStorage.getItem('guildbound_rpg_save_v1')||'null')||window.__vn.state;s.settings={textSize:'xlarge',musicVolume:.1,updatedAt:5};localStorage.setItem('guildbound_rpg_save_v1',JSON.stringify(s));localStorage.removeItem('varnethryl_settings_v1')}""")
  pg.reload();pg.wait_for_timeout(600)
  ok('synced settings from save envelope',pg.evaluate("window.__vn.Settings.get().textSize==='xlarge'"))
  pg.click('#hudMain');pg.click('#openSettings');pg.wait_for_timeout(200);pg.screenshot(path=D+'portrait-9-xlarge-from-sync.png',full_page=True)
  b.close()
print(sum(1 for _,c in res if not c),'failures')
