from playwright.sync_api import sync_playwright
import json,sys
bad=0
def ok(n,c):
  global bad
  print('PASS' if c else 'FAIL',n)
  if not c:bad+=1
def check(pg,n):
  pg.wait_for_timeout(250)
  r=pg.evaluate("(()=>{const v=window.__vn;return {party:v.state.party,active:v.state.active,drawn:v.runtime.drawn||[]}})()")
  d=sorted(r['drawn']);p=sorted(r['party'])
  ok(f"{n}: drawn {d} == party {p}, unique, active in party",d==p and len(set(d))==len(d) and r['active'] in r['party'])
  return r
with sync_playwright() as p:
  b=p.chromium.launch()
  ctx=b.new_context(viewport={'width':390,'height':844},has_touch=True,service_workers='block')
  pg=ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.goto('http://localhost:8099/index2d.html');pg.wait_for_timeout(800)
  check(pg,'initial')
  ids=pg.evaluate("window.__vn.state.party")
  for rnd in range(3):
    for i in ids:
      for _ in range(2):
        pg.evaluate(f"document.querySelector('#partyStrip [data-switch=\"{i}\"]').click()")
        r=check(pg,f'tap {i}')
        ok(f'active=={i}',r['active']==i)
  pg.evaluate(f"document.querySelector('#partyStrip [data-switch=\"{ids[2]}\"]').click()");pg.wait_for_timeout(300)
  pos=pg.evaluate("(()=>{const r=window.__vn.runtime;return [r.x,r.y]})()")
  ok('swap: previous leader follows (is companion)',pg.evaluate("Object.keys(window.__vn.runtime.companions).map(Number).sort().join()")==','.join(map(str,sorted(set(ids)-{ids[2]}))))
  pg.evaluate("window.__vn.enterZone('forest')");check(pg,'forest')
  pg.evaluate(f"document.querySelector('#partyStrip [data-switch=\"{ids[1]}\"]').click()");check(pg,'forest tap')
  pg.evaluate("window.__vn.enterZone('village')");check(pg,'village')
  pg.reload();pg.wait_for_timeout(800);check(pg,'reload')
  # old/corrupt save: duplicate party ids, active not in party
  pg.evaluate("(()=>{const k='guildbound_rpg_save_v1';const s=JSON.parse(localStorage.getItem(k));s.party=[0,1,1,2,0];s.active=9;localStorage.setItem(k,JSON.stringify(s))})()")
  pg.reload();pg.wait_for_timeout(800)
  r=check(pg,'corrupt save');ok('party deduped',r['party']==[0,1,2])
  ok('no page errors',not errs)
  b.close()
sys.exit(1 if bad else 0)
