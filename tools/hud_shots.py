from playwright.sync_api import sync_playwright
import sys
D='/workspace/shots/varnethryl-hud-build/'
U='http://localhost:8099/index.html'
extra=sys.argv[1] if len(sys.argv)>1 else ''
with sync_playwright() as p:
  b=p.chromium.launch()
  for name,w,h,mob in [('web-1280x720',1280,720,False),('phone-landscape-844x390',844,390,True),('phone-portrait-390x844',390,844,True)]:
    ctx=b.new_context(viewport={'width':w,'height':h},has_touch=mob,is_mobile=mob,device_scale_factor=2 if mob else 1,service_workers='block')
    pg=ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('console',lambda m:errs.append(m.text) if m.type=='error' else None)
    pg.goto(U+extra);pg.wait_for_timeout(2500)
    pg.screenshot(path=D+f'{name}{"-bgdemo" if extra else ""}-default.png');print(name,errs[:3])
    ctx.close()
  b.close()
