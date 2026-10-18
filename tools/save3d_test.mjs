/* proto3d save bridge tests. Run: node tools/save3d_test.mjs */
import fs from 'fs';
import {HEROES} from '../www/data.js';
import * as Save from '../www/core/save.js';
import {readSave,planFromState,readPos,writeSnapshot,createSaver} from '../www/proto3d/save3d.js';
let bad=0;const ok=(n,c,d='')=>{console.log(c?'PASS':'FAIL',n,c?'':d);if(!c)bad++};
const src=fs.readFileSync(new URL('../www/proto3d/main.js',import.meta.url),'utf8');
const GLB_NAMES=eval(src.match(/const GLB_NAMES = (\[.*?\]);/)[1]);
ok('20 3D names',GLB_NAMES.length===20&&GLB_NAMES.every(n=>HEROES.some(h=>h.name===n)));
const mem=(init)=>{const m=new Map(init?[[Save.SAVE_KEY,init]]:[]);return {getItem:k=>m.has(k)?m.get(k):null,setItem:(k,v)=>m.set(k,String(v)),m}};
const HOOKS={defaults:()=>({veyra:{v:1},mirror:{v:1}}),ensure:s=>{s.veyra={v:1,...(s.veyra||{})};s.mirror={v:1,...(s.mirror||{})}}};
const idOf=n=>HEROES.findIndex(h=>h.name===n);
// 2D writes a save (rich state) -> 3D reads
const st2d=Save.freshState(HOOKS);st2d.party=[idOf('Nyx Varrin'),idOf('Sir Aldric'),idOf('Rook Wildbane')];st2d.unlocked=[...new Set([...st2d.unlocked,...st2d.party])];st2d.active=idOf('Nyx Varrin');st2d.gold=777;st2d.questStep=2;st2d.zone='forest';st2d.kills=41;st2d.heroLevels[idOf('Nyx Varrin')]=33;
const store=mem();Save.writeState(store,st2d);
const r=readSave(store);ok('3D reads valid 2D save',r.status==='ok'&&r.state.gold===777);
const plan=planFromState(r.state,GLB_NAMES,60);
ok('plan hero = active',GLB_NAMES[plan.hero]==='Nyx Varrin');
ok('plan followers = rest of party',JSON.stringify(plan.followers.map(i=>GLB_NAMES[i]))===JSON.stringify(['Sir Aldric','Rook Wildbane']));
ok('no p3d field -> pos null',plan.pos===null);
// 3D writes
ok('3D write ok',writeSnapshot(store,{x:12.345,z:-7.5,yaw:1.2,heroGlb:GLB_NAMES.indexOf('Rook Wildbane')},GLB_NAMES));
const back=Save.loadState(store,HOOKS);
ok('2D loads 3D-written save',back.version===1&&back.gold===777&&back.questStep===2&&back.kills===41);
ok('2D zone untouched',back.zone==='forest');
ok('active switched to party member',back.active===idOf('Rook Wildbane'));
ok('party/gear/levels untouched',JSON.stringify(back.party)===JSON.stringify(st2d.party)&&back.gear.length===st2d.gear.length&&back.heroLevels[idOf('Nyx Varrin')]===33);
ok('veyra/mirror survive',back.veyra&&back.mirror);
ok('p3d pos stored',back.p3d.x===12.35||back.p3d.x===12.34,JSON.stringify(back.p3d));
// 2D re-saves (spread keeps p3d), 3D reads pos back
Save.writeState(store,{...back,gold:900});
const r2=readSave(store);const plan2=planFromState(r2.state,GLB_NAMES,60);
ok('2D->3D->2D->3D keeps pos',plan2.pos&&Math.abs(plan2.pos.x-12.35)<0.02&&plan2.pos.z===-7.5&&plan2.hero===GLB_NAMES.indexOf('Rook Wildbane'));
// non-party hero is ignored on write
writeSnapshot(store,{x:1,z:1,yaw:0,heroGlb:GLB_NAMES.indexOf('Selene Frostveil')},GLB_NAMES);
ok('non-party hero cannot become active',Save.loadState(store,HOOKS).active===idOf('Rook Wildbane'));
// empty / corrupt
ok('empty storage -> none',readSave(mem()).status==='none'&&planFromState(null,GLB_NAMES)===null);
for(const bad_ of ['{not json','null','"x"','{"version":2}','{"version":1,"gear":1,"party":[],"unlocked":[]}','[]'])ok('corrupt rejected: '+bad_.slice(0,18),readSave(mem(bad_)).status==='corrupt');
{const c=mem('{garbage');ok('corrupt save is never overwritten',writeSnapshot(c,{x:1,z:1,yaw:0,heroGlb:0},GLB_NAMES)===false&&c.getItem(Save.SAVE_KEY)==='{garbage')}
{const e=mem();ok('empty storage: 3D creates a valid save 2D loads',writeSnapshot(e,{x:3,z:4,yaw:0,heroGlb:0},GLB_NAMES)&&Save.loadState(e,HOOKS).p3d.x===3&&Save.loadState(e,HOOKS).party.length===3)}
{const t={getItem(){throw new Error('denied')},setItem(){throw new Error('full')}};ok('throwing storage is safe',readSave(t).status==='none'&&writeSnapshot(t,{x:1,z:1,yaw:0},GLB_NAMES)===false)}
// junk party in save -> sanitised
{const s=Save.freshState(HOOKS);s.party=[99,'x',-1];const m=mem(JSON.stringify(s));const p=planFromState(readSave(m).state,GLB_NAMES,60);ok('junk party falls back to Aldric',p&&p.party.length===1&&GLB_NAMES[p.hero]==='Sir Aldric')}
// NaN / bad pos safety
const mk=()=>{const m=mem();Save.writeState(m,Save.freshState(HOOKS));return m};
for(const [n,sn] of [['NaN x',{x:NaN,z:1,yaw:0}],['Infinity z',{x:1,z:Infinity,yaw:0}],['undefined',{}],['string',{x:'1',z:'2'}],['null snap',null]]){const m=mk();const before=m.getItem(Save.SAVE_KEY);ok('rejects '+n,writeSnapshot(m,sn,GLB_NAMES)===false&&m.getItem(Save.SAVE_KEY)===before)}
{const m=mk();writeSnapshot(m,{x:2,z:2,yaw:NaN,heroGlb:NaN},GLB_NAMES);const s=JSON.parse(m.getItem(Save.SAVE_KEY));ok('NaN yaw/hero become 0/ignored, JSON has no null',s.p3d.yaw===0&&!/NaN|null,"yaw/.test(m.getItem(Save.SAVE_KEY)))}
ok('readPos rejects NaN/out of range/unknown zone',readPos({p3d:{x:NaN,z:0}},60)===null&&readPos({p3d:{x:999,z:0}},60)===null&&readPos({p3d:{x:0,z:0,zone:'frost'}},60)===null&&readPos({p3d:{x:'a',z:0}},60)===null&&readPos({p3d:5},60)===null&&readPos({},60)===null);
ok('readPos accepts village',readPos({p3d:{x:1,z:2,zone:'village'}},60).x===1);
ok('unknown 2D zone does not affect 3D (still village)',planFromState({...Save.freshState(HOOKS),zone:'nowhere',p3d:{x:1,z:1,zone:'village'}},GLB_NAMES,60).pos.x===1);
// debounced saver with fake timers
{const m=mk();let cb=null,id=0,cleared=0;const T={setTimeout:(f)=>{cb=f;return ++id},clearTimeout:()=>{cleared++;cb=null}};let snap={x:1,z:1,yaw:0,heroGlb:0};let writes=0;const orig=m.setItem;m.setItem=(k,v)=>{writes++;orig(k,v)};
 const sv=createSaver(m,GLB_NAMES,()=>snap,900,T);sv.mark();sv.mark();sv.mark();ok('debounce: no write before timer',writes===0&&sv.dirty);
 cb();ok('debounce: one write after timer',writes===1&&!sv.dirty);
 sv.mark();snap={x:5,z:5,yaw:0,heroGlb:0};ok('flush writes immediately & cancels timer',sv.flush()===true&&writes===2&&JSON.parse(m.getItem(Save.SAVE_KEY)).p3d.x===5&&cleared>=1);
 ok('flush when clean is a no-op',sv.flush()===false&&writes===2)}
console.log(bad?`${bad} FAILED`:'ALL PASS');process.exit(bad?1:0);
