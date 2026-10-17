"""Class/hero motion + class skill pool tests, and attack/run frame strips. Needs static server: (cd www && python3 -m http.server 8099)."""
from playwright.sync_api import sync_playwright
from PIL import Image,ImageDraw
import json,io,os,time
D='/workspace/shots/varnethryl-class/';os.makedirs(D,exist_ok=True)
U='http://localhost:8099/index.html'
res=[]
def ok(n,c,extra=''):res.append((n,bool(c)));print(('PASS' if c else 'FAIL'),n,extra)
CLASSES="Knight Ranger Cleric Rogue Mage Paladin Berserker Druid Bard Necromancer Runemaster|Witch Hunter|Shaman Spearman Cryomancer|Dark Knight|Duelist Engineer Monk Beastmaster"
CLS=[]
for t in CLASSES.split('|'):
  for i,x in enumerate(t.split(' ')):CLS.append(x)
# rebuild properly (names with spaces)
CLS=['Knight','Ranger','Cleric','Rogue','Mage','Paladin','Berserker','Druid','Bard','Necromancer','Runemaster','Witch Hunter','Shaman','Spearman','Cryomancer','Dark Knight','Duelist','Engineer','Monk','Beastmaster']
with sync_playwright() as p:
  b=p.chromium.launch()
  ctx=b.new_context(viewport={'width':900,'height':520},device_scale_factor=2,service_workers='block')
  pg=ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('console',lambda m:errs.append(m.text) if m.type=='error' else None)
  pg.goto(U);pg.wait_for_timeout(1200)
  # ---------- data tests ----------
  d=pg.evaluate("""async()=>{const S=await import('./skills.js'),D=await import('./data.js'),M=await import('./classmotion.js');
   const cls=[...new Set(D.HEROES.map(h=>h.className))],out={cls,pools:{},ults:Object.keys(S.ULTIMATES).length,bad:[],src:{}};
   for(const c of cls){const p=S.CLASS_SKILLS[c];out.pools[c]=!!p&&['minor','heavy','superHeavy'].every(s=>p[s]&&p[s].name&&p[s].cd>0&&p[s].mult>0&&p[s].range>0&&p[s].effect&&M.VFX[p[s].fx]&&S.ICON_IDS.includes(p[s].icon)&&M.FAMILY[p[s].anim])}
   for(const h of D.HEROES){const r=S.resolve(h.id,h.name);out.src[h.id]=SLOTS_SRC(r);const pr=M.profileFor(h.id);if(!pr||!M.FAMILY[pr.fam]||!M.VFX[pr.fx])out.bad.push(h.id);if(!M.HERO_TWEAKS[h.id])out.bad.push('tw'+h.id);if(!S.ULTIMATES[h.id]||!S.ULTIMATES[h.id].placeholder||!M.VFX[S.ULTIMATES[h.id].fx])out.bad.push('ult'+h.id)}
   function SLOTS_SRC(r){return ['minor','heavy','superHeavy','ultimate'].map(s=>r[s].source).join(',')}
   // override precedence: hero override > class > default
   S.HERO_SKILLS[0].minor={name:'ZZ'};const r0=S.resolve(0,'Sir Aldric');out.over=[r0.minor.name,r0.minor.source,r0.heavy.name,r0.heavy.source];delete S.HERO_SKILLS[0].minor;
   out.names=new Set(Object.values(S.CLASS_SKILLS).flatMap(c=>Object.values(c).map(s=>s.name))).size;
   const prof=id=>M.profileFor(id);out.pf={spdKnight:prof(0).spd,spdRogue:prof(3).spd,spdMonk:prof(18).spd,spdDK:prof(15).spd,accDK:prof(15).acc,accRogue:prof(3).acc,hoverMage:prof(4).hover,hoverKnight:prof(0).hover,hoverCryo:prof(14).hover,atkMonk:prof(18).atk,atkDK:prof(15).atk,cadMonk:prof(18).cad,cadDK:prof(15).cad};
   const sp=new Set();for(const h of D.HEROES){const q=prof(h.id);sp.add([q.spd,q.acc,q.cad,q.bob,q.lean,q.atk].map(v=>v.toFixed(3)).join('/'))}out.uniqueProfiles=sp.size;
   return out}""")
  ok('20 classes covered',len(d['cls'])==20 and set(d['cls'])==set(CLS))
  ok('every class pool valid (minor/heavy/superHeavy w/ vfx, icon, anim)',all(d['pools'].values()),[c for c,v in d['pools'].items() if not v])
  ok('60 distinct class skill names',d['names']==60,d['names'])
  ok('20 placeholder ultimates + 20 hero tweaks + profiles valid',d['ults']==20 and not d['bad'],d['bad'])
  ok('resolution: all heroes class pool for 3 slots, hero ultimate',all(v=='class,class,class,hero' for v in d['src'].values()))
  ok('hero override > class > default',d['over']==['ZZ','hero','Guardian Slam','class'],d['over'])
  pf=d['pf']
  ok('heavy slower than light classes',pf['spdDK']<pf['spdKnight']<pf['spdRogue']<pf['spdMonk'],pf)
  ok('heavy accel < rogue accel',pf['accDK']<pf['accRogue'])
  ok('casters hover, knights do not',pf['hoverMage']>0 and pf['hoverCryo']>pf['hoverMage'] and pf['hoverKnight']==0)
  ok('monk attacks faster than dark knight',pf['atkMonk']<pf['atkDK'])
  ok('all 20 heroes have distinct motion signatures',d['uniqueProfiles']==20,d['uniqueProfiles'])
  # ---------- runtime tests ----------
  r=pg.evaluate("""()=>{const M=window.__vn.Motion,out={};
   // simulate steady run for heavy vs light: speed cap + acceleration over 300ms
   out.timing=[0,3,4,15,18].map(id=>{const d=M.act(id,'heavy',1000);return [id,Math.round(d.wind),Math.round(d.strike),Math.round(d.follow),d.fam]});
   const run=(id,reduce)=>{let x=0,t=0,P;for(let i=0;i<120;i++){t+=16;x+=M.maxSpeed(id)*.8*16;P=M.pose(id,x,0,t,0,reduce)}return P};
   const A=run(15,false),B=run(3,false),R=run(3,true);out.lean=[Math.abs(A.lean),Math.abs(B.lean)];out.bob=[A.dy,B.dy];
   // stride length proportional: phase advance per distance
   out.nan=[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19].some(id=>{const P=run(id,false);return Object.values(P).some(v=>typeof v==='number'&&!isFinite(v))});
   out.reduceOK=Math.abs(R.dy)<=Math.abs(B.dy)+1e-9&&Math.abs(R.lean)<=Math.abs(B.lean)+1e-9;
   // each family produces a distinct pose at mid-strike
   const fam=['slash','bash','thrust','overhead','flurry','draw','cast','strum'],poses={};for(const f of fam){const id=40+fam.indexOf(f);M.act(id,'heavy',5000,f);const q=M.pose(id,0,0,5000,0,false);M.pose(id,0,0,5000+260,0,false);const m=M.pose(id,0,0,5000+330,0,false);poses[f]=[+m.lean.toFixed(3),+m.dx.toFixed(2),+m.dy.toFixed(2),+m.sy.toFixed(3)].join('/')}
   out.poses=poses;return out}""")
  ok('heavy attack timing differs per class family',len({tuple(t[1:]) for t in r['timing']})>=4,r['timing'])
  ok('no NaN poses for all 20 heroes',not r['nan'])
  ok('heavy tank leans less than rogue at speed',r['lean'][0]<r['lean'][1],r['lean'])
  ok('reduced motion damps bob/lean',r['reduceOK'])
  ok('8 families give distinct mid-strike poses',len(set(r['poses'].values()))>=7,r['poses'])
  # ---------- in-game: skills, vfx, hitstop, camera ----------
  pg.evaluate("window.__vn.enterZone('forest')");pg.wait_for_timeout(500)
  def setup(hid,dist=120):
    pg.evaluate("""([hid,dist])=>{const v=window.__vn,r=v.runtime;v.state.active=hid;v.state.party=[hid];r.x=900;r.y=600;r.vx=r.vy=0;r.hp[hid]=v.heroMax(hid);
      r.enemy.forEach(e=>{e.x=r.x+dist;e.y=r.y;e.hp=e.maxHp=9e6;e.attackAt=1e12;e.slowUntil=0});r.target=r.enemy[0]&&r.enemy[0].id;r.faceA=0;r.attackUntil=0;window.__vn.CM.clearFx()}""",[hid,dist])
    pg.wait_for_timeout(450)
  setup(4,110)
  ok('enemies present',pg.evaluate("window.__vn.runtime.enemy.length")>0)
  pg.evaluate("window.__vn.Controls.useSkill('heavy')");pg.wait_for_timeout(100)
  ok('class skill spawns VFX',pg.evaluate("window.__vn.CM.fxCount()")>0)
  ts=pg.evaluate("[window.__vn.CM.timeScale(16,1e12,false),window.__vn.CM.timeScale(16,1e12,true)]")
  pg.wait_for_timeout(600)
  hp0=pg.evaluate("window.__vn.runtime.enemy[0].hp");ok('class skill damages enemy',hp0<9e6)
  ok('no page errors',not errs,errs[:3])
  # ---------- screenshots ----------
  def frames(hid,action,n=7,gap=55,dist=105,pre=0):
    setup(hid,dist);out=[]
    t0=time.time()
    pg.evaluate(action)
    for i in range(n):
      cl=pg.evaluate("()=>{const c=window.__vn.runtime.canvas.getBoundingClientRect(),cam=window.__vn.runtime.camera,r=window.__vn.runtime;return [c.left+(r.x-cam.x)-85,c.top+(r.y-cam.y)-125,230,175]}")
      cl=[max(0,cl[0]),max(0,cl[1]),cl[2],cl[3]]
      im=Image.open(io.BytesIO(pg.screenshot(clip=dict(x=cl[0],y=cl[1],width=cl[2],height=cl[3]))));out.append((im,int((time.time()-t0)*1000)))
      pg.wait_for_timeout(gap)
    return out
  def strip(name,rows,fn):
    W,H=rows[0][0][0].size;sheet=Image.new('RGB',(W*len(rows[0]),H*len(rows)+0),(10,12,16));dr=ImageDraw.Draw(sheet)
    for ri,(label,fr) in enumerate([(r[0],r[1]) for r in [(rr[1],rr[0]) for rr in rows]]):pass
    return sheet
  sets=[(0,'Knight'),(4,'Mage'),(3,'Rogue'),(1,'Ranger'),(18,'Monk'),(15,'Dark Knight'),(14,'Cryomancer'),(8,'Bard'),(13,'Spearman'),(2,'Cleric'),(6,'Berserker'),(9,'Necromancer')]
  def sheetfor(items,fname,mode):
    rows=[]
    for hid,cn in items:
      act="window.__vn.Controls.basic()" if mode=='basic' else f"window.__vn.Controls.useSkill('{mode}')"
      if mode=='ultimate':pg.evaluate(f"window.__vn.Controls.addCharge({hid},100)")
      rows.append((cn,frames(hid,act,n=9,gap=75 if mode!='basic' else 45)))
    W,H=rows[0][1][0][0].size;sh=Image.new('RGB',(W*9+90,H*len(rows)),(10,12,16));dr=ImageDraw.Draw(sh)
    for ri,(cn,fr) in enumerate(rows):
      dr.text((6,ri*H+6),f"{cn}",fill=(240,214,140))
      for ci,(im,ms) in enumerate(fr):sh.paste(im,(90+ci*W,ri*H));dr.text((90+ci*W+4,ri*H+H-14),f"{ms}ms",fill=(180,200,220))
    sh.save(D+fname);return rows
  five=[(0,'Knight'),(4,'Mage'),(3,'Rogue'),(1,'Ranger'),(18,'Monk')]
  sheetfor(five,'contact-five-basic-attack.png','basic')
  sheetfor(five,'contact-five-heavy.png','heavy')
  sheetfor(five,'contact-five-superheavy.png','superHeavy')
  sheetfor(sets[5:10],'contact-more-heavy.png','heavy')
  sheetfor([(15,'Dark Knight'),(11,'Witch Hunter'),(16,'Duelist'),(12,'Shaman'),(10,'Runemaster')],'contact-more2-superheavy.png','superHeavy')
  sheetfor([(0,'Knight'),(4,'Mage'),(3,'Rogue'),(1,'Ranger'),(18,'Monk')],'contact-five-ultimate.png','ultimate')
  # running strips: heavy vs light, heavy hero running right, 7 frames
  rows=[]
  for hid,cn in [(15,'Dark Knight'),(0,'Knight'),(3,'Rogue'),(18,'Monk'),(4,'Mage'),(1,'Ranger'),(8,'Bard')]:
    setup(hid,400);pg.evaluate("window.__vn.runtime.enemy.forEach(e=>{e.x=3000;e.y=3000})");pg.evaluate("""()=>{const r=window.__vn.runtime;r.walkingTarget={x:r.x+700,y:r.y}}""");pg.wait_for_timeout(120);out=[];t0=time.time()
    for i in range(7):
      cl=pg.evaluate("()=>{const c=window.__vn.runtime.canvas.getBoundingClientRect(),cam=window.__vn.runtime.camera,r=window.__vn.runtime;return [c.left+(r.x-cam.x)-85,c.top+(r.y-cam.y)-125,230,175]}")
      im=Image.open(io.BytesIO(pg.screenshot(clip=dict(x=max(0,cl[0]),y=max(0,cl[1]),width=230,height=175))));out.append((im,int((time.time()-t0)*1000)));pg.wait_for_timeout(110)
    spd=pg.evaluate("window.__vn.runtime.speed");rows.append((f"{cn} v={spd:.3f}",out));pg.evaluate("window.__vn.runtime.walkingTarget=null")
  W,H=rows[0][1][0][0].size;sh=Image.new('RGB',(W*7+130,H*len(rows)),(10,12,16));dr=ImageDraw.Draw(sh)
  for ri,(cn,fr) in enumerate(rows):
    dr.text((6,ri*H+6),cn,fill=(240,214,140))
    for ci,(im,ms) in enumerate(fr):sh.paste(im,(130+ci*W,ri*H))
  sh.save(D+'contact-running-by-class.png')
  # one full-viewport action shot
  setup(4,130);pg.evaluate("window.__vn.Controls.useSkill('superHeavy')");pg.wait_for_timeout(330);pg.screenshot(path=D+'mage-meteor-fullscreen.png')
  setup(0,100);pg.evaluate("window.__vn.Controls.useSkill('heavy')");pg.wait_for_timeout(300);pg.screenshot(path=D+'knight-guardian-slam-fullscreen.png')
  ok('no page errors during shots',not errs,errs[:3])
  b.close()
print(sum(1 for _,c in res if c),'/',len(res),'passed')
raise SystemExit(0 if all(c for _,c in res) else 1)
