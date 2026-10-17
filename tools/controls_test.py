from playwright.sync_api import sync_playwright
import json,math
D='/workspace/shots/varnethryl-controls/'
res=[]
def ok(n,c):res.append((n,bool(c)));print(('PASS' if c else 'FAIL'),n)
U='http://localhost:8099/index.html'
def drag_stick(pg,dx,dy,hold=700,shot=None):
  s=pg.locator('#stick').bounding_box();cx,cy=s['x']+s['width']/2,s['y']+s['height']/2
  pg.mouse.move(cx,cy);pg.mouse.down();pg.mouse.move(cx+dx,cy+dy,steps=4);pg.wait_for_timeout(hold)
  if shot:pg.screenshot(path=shot)
with sync_playwright() as p:
  b=p.chromium.launch()
  for name,w,h in [('portrait',390,844),('landscape',844,390)]:
    ctx=b.new_context(viewport={'width':w,'height':h},has_touch=True,is_mobile=True,device_scale_factor=2,service_workers='block')
    pg=ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('console',lambda m:errs.append(m.text) if m.type=='error' else None)
    pg.goto(U);pg.wait_for_timeout(900)
    ok(name+' mode stick',pg.evaluate("document.documentElement.dataset.ctl")=='stick')
    ok(name+' dpad hidden',not pg.locator('.dpad').is_visible())
    ok(name+' stick visible',pg.locator('#stick').is_visible())
    for i in ['touchAttack','touchSkill','skillHeavy','skillSuper','skillUlt']:ok(name+' btn '+i,pg.locator('#'+i).is_visible())
    pg.screenshot(path=D+f'{name}-1-default.png')
    # movement
    x0=pg.evaluate("window.__vn.runtime.x");
    drag_stick(pg,40,0,hold=150);v1=pg.evaluate("window.__vn.runtime.vx");pg.wait_for_timeout(500)
    v2=pg.evaluate("window.__vn.runtime.vx")
    ok(name+' accelerates (not instant)',0<v1<v2*1.01 and v2>.05)
    drag_stick(pg,0,0,hold=10) if False else None
    pg.mouse.up();pg.wait_for_timeout(120)
    vd=pg.evaluate("window.__vn.runtime.vx");ok(name+' inertia on release',vd>0.01)
    pg.wait_for_timeout(900);ok(name+' stops',pg.evaluate("Math.abs(window.__vn.runtime.vx)<.005"))
    # deadzone
    s=pg.locator('#stick').bounding_box();cx,cy=s['x']+s['width']/2,s['y']+s['height']/2
    pg.mouse.move(cx,cy);pg.mouse.down();pg.mouse.move(cx+3,cy+1,steps=2);pg.wait_for_timeout(300)
    ok(name+' dead zone ignores small drift',pg.evaluate("window.__vn.Controls.input.mag===0 && window.__vn.runtime.speed<.005"));pg.mouse.up()
    # analog magnitude -> speed: half vs full
    drag_stick(pg,22,0,hold=900);sh=pg.evaluate("window.__vn.runtime.speed");pg.mouse.up();pg.wait_for_timeout(900)
    drag_stick(pg,60,0,hold=900,shot=D+f'{name}-2-running-right.png');sf=pg.evaluate("window.__vn.runtime.speed");gait=pg.evaluate("window.__vn.Motion.pose(window.__vn.state.active,window.__vn.runtime.x,window.__vn.runtime.y,window.__vn.runtime.time,null,false).gaitName");pg.mouse.up();pg.wait_for_timeout(120)
    print('speeds half/full',sh,sf,gait);ok(name+' analog magnitude drives speed',sf>sh*1.5 and gait in('run','jog'))
    pg.wait_for_timeout(900)
    # 360: diagonal + up-left
    drag_stick(pg,-40,-40,hold=500);fa=pg.evaluate("window.__vn.runtime.faceA");vy=pg.evaluate("window.__vn.runtime.vy");pg.mouse.up()
    ok(name+' 360 diagonal (vy<0, facing up-left)',vy<-.03 and abs(abs(fa)-math.pi*.75)<.4);pg.wait_for_timeout(700)
    pg.screenshot(path=D+f'{name}-3-facing-chevron.png')
    # skills: go to forest to find enemies
    pg.evaluate("window.__vn.enterZone('forest')");pg.wait_for_timeout(400)
    zs=pg.evaluate("window.__vn.state.zone");print('zone',zs)
    pg.evaluate("""()=>{const r=window.__vn.runtime;r.enemy.forEach(e=>{e.x=r.x+60;e.y=r.y;e.hp=e.maxHp=99999})}""")
    en=pg.evaluate("window.__vn.runtime.enemy.length")
    pg.wait_for_timeout(100)
    pg.click('#touchAttack');pg.wait_for_timeout(120)
    pg.screenshot(path=D+f'{name}-4-attack-windup.png')
    pg.wait_for_timeout(500)
    pg.click('#touchSkill');pg.wait_for_timeout(200);pg.wait_for_timeout(350)
    pg.screenshot(path=D+f'{name}-5-cooldown-rings.png')
    ok(name+' minor cooling ring',pg.evaluate("document.getElementById('touchSkill').classList.contains('cooling')"))
    pg.click('#skillHeavy');pg.wait_for_timeout(300);pg.click('#skillSuper');pg.wait_for_timeout(300)
    ok(name+' heavy+super cooling',pg.evaluate("['skillHeavy','skillSuper'].every(i=>document.getElementById(i).classList.contains('cooling'))"))
    pg.evaluate("window.__vn.Controls.addCharge(window.__vn.state.active,100)");pg.wait_for_timeout(300)
    ok(name+' ult ready at full charge',pg.evaluate("document.getElementById('skillUlt').classList.contains('ready')"))
    pg.screenshot(path=D+f'{name}-6-ult-ready.png')
    pg.click('#skillUlt');pg.wait_for_timeout(1300)
    ok(name+' ult resets charge',pg.evaluate("!document.getElementById('skillUlt').classList.contains('ready')"))
    pg.screenshot(path=D+f'{name}-7-after-ultimate.png')
    # layout editor with new controls
    pg.click('#hudMain');pg.click('#openSettings');pg.wait_for_timeout(300)
    pg.click('#setFloat');pg.click('#setFloat')  # toggle on/off
    pg.screenshot(path=D+f'{name}-8-settings.png',full_page=True)
    pg.click('#setEditLayout');pg.wait_for_timeout(700)
    pg.screenshot(path=D+f'{name}-9-edit-mode.png')
    fb=pg.locator('.worldFrame').bounding_box()
    for i,(fx,fy) in {'stick':(.5,.35),'skillUlt':(.3,.25),'skillHeavy':(.7,.3)}.items():
      bb=pg.locator('#'+i).bounding_box();cx,cy=bb['x']+bb['width']/2,bb['y']+bb['height']/2
      pg.mouse.move(cx,cy);pg.mouse.down();pg.mouse.move(fb['x']+fb['width']*fx,fb['y']+fb['height']*fy,steps=8);pg.mouse.up();pg.wait_for_timeout(100)
      a=pg.locator('#'+i).bounding_box();ok(name+' moved '+i,abs(a['x']-bb['x'])>15 or abs(a['y']-bb['y'])>15)
    pg.click('#layoutDone');pg.wait_for_timeout(500)
    lay=json.loads(pg.evaluate("localStorage.getItem('varnethryl_settings_v1')"))['layout']
    ok(name+' layout has new ids',{'stick','skillUlt','skillHeavy'}<=set(lay) and 'dpad' not in lay)
    sv=json.loads(pg.evaluate("localStorage.getItem('guildbound_rpg_save_v1')"))
    ok(name+' save key/version ok + layout in envelope',sv['version']==1 and 'stick' in sv['settings']['layout'])
    pg.screenshot(path=D+f'{name}-10-custom-layout.png')
    pg.reload();pg.wait_for_timeout(900)
    # moved stick still drives movement after layout change
    s=pg.locator('#stick').bounding_box();print('stick',s,pg.evaluate('(([x,y])=>document.elementFromPoint(x,y).id)',[s['x']+s['width']/2,s['y']+s['height']/2]));drag_stick(pg,50,0,hold=500);print('spd',pg.evaluate('window.__vn.runtime.speed'),pg.evaluate('window.__vn.Controls.input.mag'));ok(name+' moved stick still works',pg.evaluate("window.__vn.runtime.speed>.05"));pg.mouse.up()
    ok(name+' no js errors',not errs);print(errs[:3])
    # floating stick
    pg.evaluate("window.__vn.Settings.get().floatingStick=true;window.dispatchEvent(new Event('vn-controls'))");pg.wait_for_timeout(200)
    fb=pg.locator('.worldFrame').bounding_box();tx,ty=fb['x']+fb['width']*.3,fb['y']+fb['height']*.55
    pg.mouse.move(tx,ty);pg.mouse.down();pg.mouse.move(tx+35,ty+10,steps=3);pg.wait_for_timeout(200)
    sb=pg.locator('#stick').bounding_box();ok(name+' floating stick follows touch',abs(sb['x']+sb['width']/2-tx)<10 and abs(sb['y']+sb['height']/2-ty)<10)
    pg.screenshot(path=D+f'{name}-11-floating-stick.png');pg.mouse.up()
    ctx.close()
  # desktop
  ctx=b.new_context(viewport={'width':1280,'height':800},service_workers='block');pg=ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.goto(U);pg.wait_for_timeout(900)
  ok('desktop mode dpad',pg.evaluate("document.documentElement.dataset.ctl")=='dpad' and pg.locator('.dpad').is_visible() and not pg.locator('#stick').is_visible())
  pg.screenshot(path=D+'desktop-1-dpad.png')
  pg.keyboard.down('d');pg.wait_for_timeout(120);v1=pg.evaluate("window.__vn.runtime.vx");pg.wait_for_timeout(500);v2=pg.evaluate("window.__vn.runtime.vx");pg.keyboard.up('d')
  ok('desktop keyboard accelerates',0<v1<v2)
  d=pg.locator('[data-dir=up]').bounding_box();pg.mouse.move(d['x']+10,d['y']+10);pg.mouse.down();pg.wait_for_timeout(500);ok('dpad moves',pg.evaluate("window.__vn.runtime.vy<-.03"));pg.mouse.up()
  # capacitor simulation: native => stick even on desktop
  ctx2=b.new_context(viewport={'width':1280,'height':800},service_workers='block');p2=ctx2.new_page()
  p2.add_init_script("window.Capacitor={isNativePlatform:()=>true,getPlatform:()=>'android'}");p2.goto(U);p2.wait_for_timeout(700)
  ok('Capacitor native => stick, no dpad',p2.evaluate("document.documentElement.dataset.ctl")=='stick' and not p2.locator('.dpad').is_visible())
  p2.screenshot(path=D+'desktop-2-capacitor-native-stick.png')
  ok('desktop no js errors',not errs)
  b.close()
print(sum(1 for _,c in res if not c),'failures')
