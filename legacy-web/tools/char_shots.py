"""Screenshots of the painted world with party + enemies, and a lineup of the 20 hero sprites. Serve www/ on :8123 first."""
from playwright.sync_api import sync_playwright
import json, sys
D='/workspace/shots/varnethryl-chars/'; U='http://localhost:8123/index.html?showEnemies=1'
with sync_playwright() as p:
  b=p.chromium.launch()
  for name,w,h,mob in [('web-1280x720',1280,720,False),('phone-844x390',844,390,True)]:
    ctx=b.new_context(viewport={'width':w,'height':h},has_touch=mob,is_mobile=mob,device_scale_factor=2 if mob else 1,service_workers='block')
    pg=ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('console',lambda m:errs.append(m.text) if m.type=='error' else None)
    pg.goto(U);pg.wait_for_timeout(1500)
    pg.evaluate("localStorage.setItem('guildbound_rpg_save_v1',JSON.stringify({...JSON.parse(localStorage.getItem('guildbound_rpg_save_v1')||'{}'),version:1,party:[0,7,9],unlocked:[0,1,2,3,7,9,10,15],active:0}))") if False else None
    pg.wait_for_timeout(7000)
    pg.screenshot(path=D+f'{name}-world-party-enemies.png'); print(name,errs[:3])
    pg.keyboard.down('d');pg.wait_for_timeout(700);pg.screenshot(path=D+f'{name}-world-moving.png');pg.keyboard.up('d')
    ctx.close()
  b.close()
