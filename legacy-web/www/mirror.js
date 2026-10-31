// Varnethryl 0.5.0 (quest branch): "The Mirrored Flame" quest line (Kael Runebinder and Rowan Firebrand).
// Additive: all progress lives in state.mirror inside the existing guildbound_rpg_save_v1 save.
// Story panels reuse the Quest story dialog (Quest.play). No new party slots, no extra hero sprites.
import * as Quest from './quest.js';
export const TITLE = 'The Mirrored Flame';
const STAGES = ['locked', 'offer', 'active', 'finished'];
const KAEL = 'Kael Runebinder', ROWAN = 'Rowan Firebrand';
const P = (scene, art, who, text, extra = {}) => ({ scene, art, who, text, ...extra });
// Mirror Trial (M5): each round has one real answer. Wrong or skipped rounds bring extra Mirror Shades.
export const PUZZLE = {
  mq_r1: 'b', mq_r2: 'a', mq_r3: 'b'
};
const ENDINGS = { unity: 'Unity', paths: 'Own Paths' };
export const CHAPTERS = [
  {
    id: 'M1', title: 'Two of a Kind', zone: 'forest', hint: 'Defeat the Ember Wisp that is plaguing the village near Whispering Wilds.',
    intro: [
      P('wilds', '🔥🧙', 'Rowan Firebrand', 'A farmer slams a gate. "Firebrand! You burned my hay again!" The mage in red-trimmed robes blinks. "That was not me. I have never seen your hay."'),
      P('wilds', '🔷🧙', 'Kael Runebinder', 'Two streets over, the baker waves a rolling pin. "Runebinder! You owe me for the oven you cracked." The runemaster in the grey scarf sighs. "I was reading in the next county."'),
      P('wilds', '👥', 'The village', 'Each is blamed for the other\'s mess. Their faces are nearly the same: same jaw, same eyes, same tired smile. They finally meet at the well, and neither can speak.'),
      P('wilds', '🔥🔷', 'Rowan and Kael', 'Rowan: "You look like me." Kael: "You look like me." Brynn Cogwright, watching from a cart: "Not blood, boys. I have seen mirror runes before. Something in the Starforge made you alike."'),
      P('wilds', '✨', 'An Ember Wisp', 'An Ember Wisp tears loose from the hay fire and spirals toward the village, drawn to both of them at once. Who steps in front of it first?', { choice: 'mq_first', choices: [{ id: 'kael', label: '🔷 Kael steps in' }, { id: 'rowan', label: '🔥 Rowan steps in' }] })
    ],
    fights: [{ name: 'Ember Wisp', hp: 4200, attack: 90, xp: 420, gold: 300, color: '#ff9a4a' }],
    recruits: [ROWAN, KAEL], zonesUnlocked: [], reward: { gold: 400, shards: 10, items: ['Village Apology Note'] },
    outro: [
      P('wilds', '🙏', 'The village', 'The Wisp fades. The farmer and the baker apologise, mostly to the wrong person. Rowan and Kael agree to travel together until they learn why they share a face.'),
      P('wilds', '📜', 'Reward', 'Rowan Firebrand and Kael Runebinder join your guild. Tap a portrait to switch between them. Each hero keeps a single sprite.')
    ]
  },
  {
    id: 'M2', title: 'The Wrong Twin', zone: 'ruins', needs: { swaps: true }, hint: 'In the Ashen Ruins, play as both Kael and Rowan (tap portraits) and defeat the Ruin Sentinel.',
    intro: [
      P('shrine', '🏛️🔒', 'Ashen Ruins', 'A rune vault in the ruins has been robbed. The watch finds a scorched handprint and a runemaster\'s chalk mark: proof of both, and of neither.'),
      P('shrine', '⛓️🔥', 'The watch', '"Rowan Firebrand, you are under arrest." Rowan was in the party hall all night. Kael was seen at the vault, but Kael was in the party hall too. Brynn points out the camp roster has no gaps.'),
      P('shrine', '🔷🔥', 'Kael and Rowan', 'To prove it, they must work as two people: Kael reads the vault runes, Rowan burns the false wards. Switch between them to clear his name. The vault\'s Ruin Sentinel does not care who is who.')
    ],
    fights: [{ name: 'Ruin Sentinel', hp: 9000, attack: 150, xp: 700, gold: 500, color: '#829db6' }],
    recruits: [], zonesUnlocked: [], reward: { gold: 800, shards: 15, items: ['Cleared Name Writ'] },
    outro: [
      P('shrine', '🔎', 'Kael', 'Kael reads the Sentinel\'s memory runes. The thief wore Rowan\'s face, and left it behind in a thin sheet of silver glass.'),
      P('shrine', '🪞', 'Rowan', '"A mirror, then. Someone has been borrowing us." Rowan is released. A silver shard on the vault floor shows a masked figure, watching.')
    ]
  },
  {
    id: 'M3', title: 'Borrowed Faces', zone: 'coast', hint: 'Travel to Tidewrack Coast. Defeat the masked Shade and the Tidewrack Mimic.',
    intro: [
      P('coast', '⚓🌫️', 'Tidewrack Coast', 'The harbour is on fire. Witnesses say Rowan lit it, and one swears it was Kael. The dockmaster pulls a crossbow on both.'),
      P('coast', '🎭', 'The Shade', 'A masked figure on the pier wears Rowan\'s face for a heartbeat, then Kael\'s. It is a shade of the Mirror Warden, a thing that steals identities and keeps them.'),
      P('coast', '🪞🌊', 'Brynn', '"It cannot copy what you do together. Watch how it moves, then guess the real one." Rowan and Kael split up to chase it. Ahead, a Tidewrack Mimic waits in the tide.')
    ],
    fights: [
      { name: 'Masked Shade', hp: 22000, attack: 520, xp: 1900, gold: 1400, color: '#b8c4d8' },
      { name: 'Tidewrack Mimic', hp: 36000, attack: 640, xp: 2600, gold: 1900, color: '#3e8f9c' }
    ],
    recruits: [], zonesUnlocked: ['coast'], reward: { gold: 1900, shards: 22, items: ['Shade\'s Silver Mask'] },
    outro: [
      P('coast', '🎭💥', 'The Shade', 'The mask cracks. Underneath is only silver glass and a voice: "Two faces, one heart. The Warden wants the heart." It dissolves.'),
      P('coast', '🪞', 'Kael', 'Kael: "We were made to be copied." Rowan: "Then we were made to be stronger." The party stops trusting who is who by face, and starts trusting by deeds.')
    ]
  },
  {
    id: 'M4', title: 'Rune and Flame', zone: 'frost', needs: { trade: true }, hint: 'In Frostbite Pass, tap "Trade staves" and defeat the Frost Wyrm.',
    intro: [
      P('snow', '❄️🐉', 'Frostbite Pass', 'The Frost Wyrm\'s cold breaks fire spells and rune seals alike. Only a magic built from both will bite.'),
      P('snow', '🔥📜', 'Rowan', '"Hold my staff. Now hold your breath, it kicks." Rowan teaches Kael to burn clean and quick. Kael teaches Rowan to carve a rune and hold it still.'),
      P('snow', '🔷🔥', 'Kael and Rowan', 'They trade staves. Runic Cascade meets Meteor Burst, and for a moment the two spells draw the same shape in the air. Tap "Trade staves" when ready.')
    ],
    fights: [{ name: 'Frost Wyrm', hp: 44000, attack: 880, xp: 3400, gold: 2400, color: '#9bd0e0' }],
    recruits: ['Brynn Cogwright'], zonesUnlocked: ['hollow'], reward: { gold: 3000, shards: 30, items: ['Mirror Bond', 'Runeflame Sigil'] },
    outro: [
      P('snow', '☄️🔷', 'The Wyrm', 'The Wyrm falls to a spell neither could cast alone: a rune of fire.'),
      P('snow', '🔗', 'Mirror Bond', 'Mirror Bond: while Kael and Rowan are both in your party, the whole party hits harder and takes less damage. Brynn recommends Dusk Hollow next. The Warden\'s trail leads there. Dusk Hollow is now on your map.')
    ]
  },
  {
    id: 'M5', title: 'Which One Is Real?', zone: 'hollow', needs: { puzzle: true }, hint: 'In Dusk Hollow, face the mirrors (the Mirror Trial) and defeat the Mirror Warden.',
    intro: [
      P('manor', '🪞🪞', 'Dusk Hollow', 'In the old ballroom, hundreds of mirrors line the wall. The Mirror Warden, a tall figure with no reflection, steps from the glass. "Two hearts and one face. How wasteful. I will keep the better copy."'),
      P('manor', '👥👥', 'The Warden', 'The Warden duplicates both heroes and their allies. Eight shapes stand in the hall. Only your allies can tell which of each is real. Tap "Face the mirrors" to begin the Mirror Trial.')
    ],
    fights: [{ name: 'Mirror Warden', hp: 90000, attack: 1200, xp: 6000, gold: 4200, color: '#8fa8d8' }],
    recruits: [], zonesUnlocked: [], reward: { gold: 4500, shards: 40, items: ['Warden\'s Cracked Mirror'] },
    outro: [
      P('manor', '🪞💥', 'The Warden', 'The Warden recoils as the hall\'s mirrors crack. "You cannot tell yourselves apart. Why can they?" Kael: "Because they are watching what we do, not what we look like."'),
      P('manor', '🌌', 'The Warden', 'He retreats into a shard of silver glass. Brynn: "That shard points to the Starforge. Where you were made."')
    ]
  },
  {
    id: 'M6', title: 'The Shattered Glass', zone: 'starforge', needs: { crack: true }, hint: 'In the Starforge Hall, crack the glass once as Kael and once as Rowan (switch heroes between taps), then defeat the Mirror Warden.',
    intro: [
      P('forge', '⭐🔥', 'The Starforge Hall', 'A cooled forge under a night sky. In its heart, a mirror rune the height of a tower. Its light splits in two, like the heroes.'),
      P('forge', '🪞⚙️', 'Brynn', 'Brynn reads the plaque: "One hero was forged here, long ago, and split in two by the mirror rune so the world would never lose him. The Warden wants the rune, and the one hero it protects."'),
      P('forge', '🔷🔥', 'Kael and Rowan', '"So we were one person." "We are two now." The Warden returns, one face wearing both of theirs. Strike as separate people: the Warden\'s glass shield breaks only when it is cracked once by Kael and once by Rowan.')
    ],
    fights: [{ name: 'Mirror Warden, Unmasked', hp: 140000, attack: 1700, xp: 9000, gold: 6000, color: '#c7d2ff', warden: true }],
    recruits: [], zonesUnlocked: [], reward: { gold: 8000, shards: 60, items: ['Starforge Shard'] },
    outro: [
      P('forge', '💥🪞', 'The Warden', 'The shield shatters. The Warden\'s many faces fall away until only silver dust remains.'),
      P('forge', '🔷🔥', 'Kael and Rowan', 'The mirror rune dims but does not die. It waits for one final choice: how will the two of them carry it?')
    ]
  },
  {
    id: 'M7', title: 'Two Flames', zone: 'village', hint: 'Return to Liongate and choose how Kael and Rowan carry the rune.',
    intro: [
      P('dawn', '🏡🔥', 'Liongate', 'Back in Liongate, the baker offers Kael a loaf, and Rowan a pie. They are finally greeted by the right names.'),
      P('dawn', '🪞', 'The mirror rune', 'The shard in their pouch hums. It can keep them linked, or let them go their own ways. Either choice is theirs. The Mirror Bond will not break the friendship.')
    ],
    fights: [],
    recruits: [], zonesUnlocked: [], reward: { gold: 10000, shards: 80, items: ['Brothers\' Rune'] },
    outro: v => [
      P('dawn', '🔥🔷', 'Rowan', '"One heart, two hands."'),
      P('dawn', '🌅', 'Choose', 'Unity: share the rune and gain a big team buff. Own Paths: break the link; each hero gets a unique mark (Kael a silver ring, Rowan a red ring) and a personal bonus.', { choice: 'mq_end', choices: [{ id: 'unity', label: '🔗 Unity: share the rune' }, { id: 'paths', label: '🛤️ Own Paths: break the link' }] }),
      P('dawn', '🏅', 'Mirrorbound', `Title: Mirrorbound. Keepsake: Brothers' Rune. Ending: ${ENDINGS[v.ending] || ''}.`)
    ]
  }
];
let state_ = null, api = null, built = false, replaying = false, lastActive = null;
const hero = n => api.HEROES.find(h => h.name === n);
export function defaults() {
  return { v: 1, ch: 1, stage: 'locked', fight: 0, done: [], recruits: [], items: [], zones: [], choices: {}, puz: {}, puzzleDone: false, mistakes: 0, traded: false, swapK: false, swapR: false, crackK: false, crackR: false, ending: null, title: null };
}
const arr = a => Array.isArray(a) ? a.filter(x => typeof x === 'string') : [];
export function ensure(s) {
  const d = defaults(), v = s.mirror && typeof s.mirror === 'object' ? s.mirror : {};
  const r = { ...d, ...v };
  r.ch = Math.min(7, Math.max(1, Math.floor(+r.ch) || 1));
  if (!STAGES.includes(r.stage)) r.stage = 'locked';
  r.fight = Math.max(0, Math.floor(+r.fight) || 0); r.mistakes = Math.min(3, Math.max(0, Math.floor(+r.mistakes) || 0));
  for (const k of ['done', 'recruits', 'items', 'zones']) r[k] = arr(r[k]);
  for (const k of ['puzzleDone', 'traded', 'swapK', 'swapR', 'crackK', 'crackR']) r[k] = !!r[k];
  r.choices = r.choices && typeof r.choices === 'object' && !Array.isArray(r.choices) ? r.choices : {};
  r.puz = r.puz && typeof r.puz === 'object' && !Array.isArray(r.puz) ? r.puz : {};
  if (r.ending && !ENDINGS[r.ending]) r.ending = null;
  s.mirror = r; return s;
}
const m = () => state_.mirror;
const chap = () => CHAPTERS[m().ch - 1];
const prop = (c, k) => typeof c[k] === 'function' ? c[k](m()) : c[k];
const $ = id => document.getElementById(id);
const esc = s => String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const hid = n => { const h = hero(n); return h ? h.id : -1; };
const both = () => !!state_ && state_.party.includes(hid(KAEL)) && state_.party.includes(hid(ROWAN));
// ---------- binding ----------
export function bind(a) {
  api = a; state_ = a.state(); built = true;
  const vc = $('veyraCard');
  if (vc && !$('mirrorCard')) {
    const card = document.createElement('div'); card.className = 'panel vqCard'; card.id = 'mirrorCard'; card.setAttribute('aria-live', 'polite'); vc.after(card);
    const ban = document.createElement('div'); ban.id = 'mirrorBanner'; ban.className = 'storyBanner'; ban.hidden = true; const sb = $('storyBanner'); (sb || vc).after(ban);
  }
  document.addEventListener('click', onClick);
  rebind();
}
export function rebind() { state_ = api.state(); ensure(state_); lastActive = null; render(); }
// ---------- progression ----------
function unlockCheck() {
  if (m().stage === 'locked' && (state_.kills >= 6 || state_.veyra.done.includes('V1') || state_.questStep >= 2)) { m().stage = 'offer'; api.log('Two mages who look exactly alike are asking for you in Liongate. Open the Mirrored Flame card.'); api.save(); setTimeout(render, 0); }
}
export function atk() {
  if (!state_ || !state_.mirror) return 1; const v = state_.mirror; let x = 1;
  if (v.items.includes('Mirror Bond') && both()) x += v.ending === 'unity' ? .18 : .08;
  if (v.ending === 'paths' && (state_.active === hid(KAEL) || state_.active === hid(ROWAN))) x += .06;
  return x;
}
export function def() {
  if (!state_ || !state_.mirror) return 1; const v = state_.mirror; let x = 1;
  if (v.items.includes('Mirror Bond') && both()) x += v.ending === 'unity' ? .12 : .05;
  return x;
}
function grantRecruit(name) {
  const h = hero(name); if (!h) return;
  if (!m().recruits.includes(name)) m().recruits.push(name);
  if (!state_.unlocked.includes(h.id)) state_.unlocked.push(h.id);
  const lv = Math.max(1, Math.round(state_.party.reduce((s, id) => s + api.nLevel(id), 0) / Math.max(1, state_.party.length)));
  state_.heroLevels[h.id] = Math.max(state_.heroLevels[h.id] || 1, lv);
  if (!state_.party.includes(h.id) && state_.party.length < state_.partyCap) { state_.party.push(h.id); api.runtime.hp[h.id] = api.heroMax(h.id); }
}
// Make sure Kael and Rowan are both in the party without adding a slot: swap out the last non-essential member.
function ensureBoth() {
  const ids = [hid(KAEL), hid(ROWAN)].filter(i => i >= 0 && state_.unlocked.includes(i));
  for (const id of ids) {
    if (state_.party.includes(id)) continue;
    if (state_.party.length < state_.partyCap) state_.party.push(id);
    else { const out = [...state_.party].reverse().find(p => p !== state_.active && !ids.includes(p)); if (out === undefined) continue; state_.party[state_.party.indexOf(out)] = id; delete api.runtime.companions[out]; api.toast(`${api.HEROES[id].name} takes ${api.HEROES[out].name}'s place in the party for this chapter.`); }
    api.runtime.hp[id] ??= api.heroMax(id);
  }
  api.renderParty && api.renderParty(); api.renderHeroes && api.renderHeroes();
}
function startIntro() { const c = chap(); if (m().stage !== 'offer') return; play(prop(c, 'intro'), () => activate()); }
function activate() {
  const v = m(), c = chap(); if (v.stage !== 'offer') return;
  v.stage = 'active'; v.fight = 0; v.traded = false; v.swapK = false; v.swapR = false; v.crackK = false; v.crackR = false; v.puz = {}; v.puzzleDone = false; v.mistakes = 0;
  if (c.id === 'M1') for (const n of c.recruits) grantRecruit(n);
  if (c.needs && (c.needs.swaps || c.needs.crack)) ensureBoth();
  lastActive = null; track();
  api.log(`New objective: ${c.hint}`); api.save(); render();
}
function play(panels, done, replay = false) {
  replaying = replay;
  Quest.play(panels, () => { replaying = false; defaultChoices(panels); done && done(); }, replay);
}
function defaultChoices(panels) { // skipped panels pick the first choice so progress never gets stuck
  for (const p of panels) if (p.choices && p.choice && !(p.choice in PUZZLE) && !m().choices[p.choice]) m().choices[p.choice] = p.choices[0].id;
}
document.addEventListener('click', e => {
  const b = e.target.closest && e.target.closest('.stChoice'); if (!b || replaying || !state_ || !built) return;
  const k = b.dataset.key; if (!k || !k.startsWith('mq_')) return;
  if (k in PUZZLE) m().puz[k] = b.dataset.id; else m().choices[k] = b.dataset.id;
  api.save();
}, true);
function track() { const v = m(); if (v.stage !== 'active') return; if (state_.active === hid(KAEL)) v.swapK = true; if (state_.active === hid(ROWAN)) v.swapR = true; }
function spawn(tpl, extra = {}) {
  const rt = api.runtime, ang = Math.random() * Math.PI * 2;
  const x = Math.min(1700, Math.max(105, rt.x + Math.cos(ang) * 190)), y = Math.min(1080, Math.max(105, rt.y + Math.sin(ang) * 150));
  const e = { ...tpl, id: ++rt.enemyIds, mq: true, qboss: true, boss: false, x, y, maxHp: tpl.hp, hp: tpl.hp, attackAt: 0, stunned: 0, slowUntil: 0, burn: 0, dx: 0, dy: 0, ...extra };
  rt.enemy.push(e); return e;
}
function spawnFight() {
  const c = chap(), v = m(), tpl = c.fights[v.fight]; if (!tpl) return;
  const e = spawn(tpl);
  if (tpl.warden) { e.mqw = true; e.phase = 1; }
  api.log(`${tpl.name} appears!`);
  if (c.id === 'M5') for (let i = 0; i < v.mistakes; i++) spawn({ name: 'Mirror Shade', hp: 5000, attack: 400, xp: 150, gold: 80, color: '#aab6d6' }, { mqx: true, qboss: false });
}
const live = () => api.runtime.enemy.filter(e => e.mq && !e.mqx && e.hp > 0);
let acc = 0, lastZone = null, lastHero = null;
export function tick(dt) {
  if (!state_ || !state_.mirror) return;
  acc += dt; if (acc < 350) return; acc = 0;
  unlockCheck(); track();
  if (lastZone !== state_.zone || lastHero !== state_.active) { lastZone = state_.zone; lastHero = state_.active; render(); }
  const v = m(), c = chap(); if (v.stage !== 'active' || !c) return;
  const w = api.runtime.enemy.find(e => e.mqw && e.hp > 0); if (w) wardenPhases(w);
  if (state_.zone === c.zone && v.fight >= c.fights.length && needsMet()) { finish(); return; }
  const gated = (c.needs && c.needs.puzzle && !v.puzzleDone);
  if (!gated && state_.zone === c.zone && v.fight < c.fights.length && !live().length && !api.runtime.enemy.some(e => e.mqx && e.hp > 0)) { spawnFight(); render(); }
}
function wardenPhases(e) {
  const v = m(), M = e.maxHp;
  if (e.phase === 1 && e.hp <= .5 * M + 1) { e.phase = 2; e.hold = .5 * M; v.crackK = false; v.crackR = false; api.toast('A glass shield rises. Crack it as Kael, then as Rowan.'); api.log('The Warden raises a mirror shield.'); render(); }
  else if (e.phase === 2 && v.crackK && v.crackR) { e.phase = 3; e.hold = 0; api.toast('The shield shatters!'); api.log('Kael and Rowan, as two people, shatter the glass.'); render(); }
}
export function onDefeat(e) {
  if (!e || !e.mq) return;
  const v = m(), c = chap(); if (e.mqx || v.stage !== 'active' || !c) return;
  v.fight++;
  if (v.fight < c.fights.length) { api.toast(`Next: ${c.fights[v.fight].name}`); api.save(); render(); return; }
  tryFinish();
}
function needsMet() {
  const c = chap(), v = m(), n = c.needs || {};
  return (!n.swaps || (v.swapK && v.swapR)) && (!n.trade || v.traded) && (!n.puzzle || v.puzzleDone) && (!n.crack || (v.crackK && v.crackR));
}
function tryFinish() {
  const v = m(), c = chap(); if (v.stage !== 'active' || v.fight < c.fights.length) return;
  if (!needsMet()) { api.toast('Finish the chapter objective first.'); render(); return; }
  finish();
}
function finish() {
  const v = m(), c = chap(), id = c.id; if (v.done.includes(id)) return;
  v.done.push(id);
  for (const n of c.recruits) grantRecruit(n);
  for (const z of c.zonesUnlocked) if (!v.zones.includes(z)) v.zones.push(z);
  if (id === 'M3' && !v.zones.includes('coast')) v.zones.push('coast');
  if (id === 'M5' && !v.zones.includes('starforge')) v.zones.push('starforge'); // the Warden's shard points to the Starforge
  for (const it of c.reward.items) if (!v.items.includes(it)) v.items.push(it);
  state_.gold += c.reward.gold; state_.shards += c.reward.shards;
  api.log(`Chapter complete: ${c.title}. +${Math.round(c.reward.gold).toLocaleString('en-US')} gold, +${c.reward.shards} shards.`);
  if (id === 'M7') { v.stage = 'finished'; } else { v.ch += 1; v.stage = 'offer'; v.fight = 0; }
  api.renderCounters(); api.renderParty && api.renderParty(); api.renderHeroes && api.renderHeroes(); api.save(); render();
  const out = prop(c, 'outro');
  if (id === 'M7') play(out, () => { grantEnding(); render(); });
  else play(out);
}
function grantEnding() {
  const v = m(); if (v.ending) return;
  v.ending = v.choices.mq_end === 'paths' ? 'paths' : 'unity'; v.title = 'Mirrorbound';
  if (v.ending === 'paths') {
    for (const [n, nm] of [[KAEL, 'Silver Rune Scarf'], [ROWAN, 'Red Ember Cloak']]) { const h = hero(n); if (!h) continue; const it = api.baseItem('charm', h.id, 6); it.name = nm; state_.gear.push(it); }
  } else { const h = api.HEROES[state_.active]; const it = api.baseItem('charm', h.id, 6); it.name = 'Shared Rune Charm'; state_.gear.push(it); }
  api.toast(`Mirrorbound! Ending: ${ENDINGS[v.ending]}.`); api.renderCounters(); api.save();
}
// ---------- Mirror Trial, Trade staves, Crack the glass ----------
function trial() {
  const v = m(), c = chap(); if (v.stage !== 'active' || !c.needs?.puzzle || v.puzzleDone || state_.zone !== c.zone) return;
  const R = (key, scene, who, text, a, b) => P(scene, '🪞', who, text, { choice: key, choices: [{ id: 'a', label: a }, { id: 'b', label: b }] });
  const panels = [
    R('mq_r1', 'manor', 'Round 1 · Which Kael?', 'Two Kaels. One hums his rune under his breath as he thinks. The other stands perfectly silent and never blinks.', '🔇 The silent Kael', '🎶 The humming Kael'),
    R('mq_r2', 'manor', 'Round 2 · Which Rowan?', 'Two Rowans. One lights the nearest candle without looking. The other waits and glances at you first for approval.', '🔥 The one who lights it', '👀 The one who looks to you'),
    R('mq_r3', 'manor', 'Round 3 · Which pair?', 'The Warden blends them into one reflection. Brynn: "Look at their shadows." One pair\'s shadows move a heartbeat late.', '🌑 The pair whose shadows lag', '☀️ The pair whose shadows keep time')
  ];
  v.puz = {};
  play(panels, () => { v.mistakes = Object.keys(PUZZLE).filter(k => v.puz[k] !== PUZZLE[k]).length; v.puzzleDone = true; api.toast(v.mistakes ? `${v.mistakes} Mirror Shade${v.mistakes > 1 ? 's' : ''} will join the fight.` : 'Every answer was right. The Warden stands alone.'); api.save(); render(); });
}
function tradeStaves() {
  const v = m(), c = chap(); if (v.stage !== 'active' || !c.needs?.trade || state_.zone !== c.zone || v.traded) return;
  v.traded = true; api.toast('Staves traded. Runic Cascade and Meteor Burst hum as one.'); api.log('Kael and Rowan trade staves.'); api.save();
  if (v.fight >= c.fights.length) tryFinish();
  render();
}
function crack() {
  const v = m(), c = chap(); if (v.stage !== 'active' || !c.needs?.crack || state_.zone !== c.zone) return;
  const w = api.runtime.enemy.find(e => e.mqw && e.hp > 0); if (!w || w.phase !== 2) { api.toast('Wait for the Warden\'s shield.'); return; }
  if (state_.active === hid(KAEL)) v.crackK = true; else if (state_.active === hid(ROWAN)) v.crackR = true; else { api.toast('Only Kael or Rowan can crack the glass.'); return; }
  api.sfx && api.sfx('skill'); api.save(); wardenPhases(w); render();
}
// ---------- UI ----------
function onClick(e) {
  const b = e.target.closest('[data-mq]'); if (!b) return;
  const a = b.dataset.mq;
  if (a === 'read') startIntro();
  else if (a === 'goto') { const c = chap(); if (c) api.enterZone(c.zone); }
  else if (a === 'trial') trial();
  else if (a === 'trade') tradeStaves();
  else if (a === 'crack') crack();
  else if (a === 'replay') { const c = CHAPTERS.find(x => x.id === b.dataset.id); if (c) { if (api.closeModal) api.closeModal(); play([...prop(c, 'intro'), ...(typeof c.outro === 'function' ? [] : c.outro)], null, true); } }
  else if (a === 'journal') api.openJournal();
}
export function status() {
  const v = m(), c = chap(); if (!c) return null;
  const w = api.runtime.enemy.find(e => e.mqw && e.hp > 0);
  return { chapter: c.id, stage: v.stage, fight: v.fight, fights: c.fights.length, phase: w ? w.phase : 0, mistakes: v.mistakes };
}
export function render() {
  if (!built || !state_ || !state_.mirror) return;
  unlockCheck();
  const v = m(), c = chap(), card = $('mirrorCard'), banner = $('mirrorBanner'); if (!card) return;
  const eyebrow = `<span class="eyebrow">STORY · ${esc(TITLE.toUpperCase())}</span>`;
  if (v.stage === 'locked') { card.hidden = false; card.innerHTML = `${eyebrow}<h2>Two faces, one name?</h2><p>Defeat 6 monsters, or begin the Dusk Hollow story, and two near-identical mages will find you.</p>`; banner.hidden = true; return; }
  card.hidden = false;
  if (v.stage === 'finished') { card.innerHTML = `${eyebrow}<h2>Mirrorbound</h2><p>Ending: ${esc(ENDINGS[v.ending] || '')}. Kael and Rowan are two people, and a pair.</p><div class="buttonRow"><button type="button" class="vqBtn" data-mq="journal" id="mqJournal">📜 Story journal</button></div>`; banner.hidden = true; return; }
  const z = api.zones.find(x => x.id === c.zone), inZone = state_.zone === c.zone;
  let html = `${eyebrow}<h2>${c.id} · ${esc(c.title)}</h2>`; const btns = [];
  if (v.stage === 'offer') {
    html += '<p>A new chapter of the story is ready.</p>';
    btns.push('<button type="button" class="vqBtn gold" data-mq="read" id="mqRead">📜 Read the story</button>');
    banner.hidden = false; banner.innerHTML = `<button type="button" class="storyBannerBtn" data-mq="read" id="mqBanner">🪞 New chapter ${c.id}: ${esc(c.title)} · tap to read</button>`;
  } else {
    banner.hidden = true;
    const total = Math.max(1, c.fights.length), cleared = Math.min(v.fight, total), n = c.needs || {};
    const extra = [n.swaps ? `Play as both: Kael ${v.swapK ? '✔' : '✖'} Rowan ${v.swapR ? '✔' : '✖'}` : '', n.trade ? `Staves ${v.traded ? '✔' : '✖'}` : '', n.puzzle ? `Mirror Trial ${v.puzzleDone ? '✔' : '✖'}` : '', n.crack ? `Glass: Kael ${v.crackK ? '✔' : '✖'} Rowan ${v.crackR ? '✔' : '✖'}` : ''].filter(Boolean).join(' · ');
    html += `<p>${esc(c.hint)}</p><div class="meter"><div style="width:${c.fights.length ? (cleared / total) * 100 : 0}%"></div></div><p class="micro" id="mqNums">Fights ${c.fights.length ? cleared : 0} / ${c.fights.length}${extra ? ' · ' + extra : ''}${!inZone ? ` · Go to ${esc(z.name)}` : ''}</p>`;
    if (!inZone) btns.push(`<button type="button" class="vqBtn gold" data-mq="goto" id="mqGoto">➤ Travel to ${esc(z.name)}</button>`);
    if (inZone && n.puzzle && !v.puzzleDone) btns.push('<button type="button" class="vqBtn gold" data-mq="trial" id="mqTrial">🪞 Face the mirrors</button>');
    if (inZone && n.trade && !v.traded) btns.push('<button type="button" class="vqBtn gold" data-mq="trade" id="mqTrade">🔁 Trade staves</button>');
    const w = api.runtime.enemy.find(x => x.mqw && x.hp > 0);
    if (w) html += `<p class="micro" id="mqPhase">${['', 'Strike the Warden down to half health.', 'Glass shield! Crack it as Kael, then switch to Rowan and crack it again.', 'The shield is broken. Finish the fight.'][w.phase] || ''}</p>`;
    if (w && w.phase === 2) btns.push(`<button type="button" class="vqBtn gold" data-mq="crack" id="mqCrack">🪞 Crack the glass as ${esc(api.HEROES[state_.active].name.split(' ')[0])}</button>`);
  }
  btns.push('<button type="button" class="vqBtn" data-mq="journal" id="mqJournal">📜 Story journal</button>');
  card.innerHTML = html + `<div class="buttonRow">${btns.join('')}</div>`;
}
export function journalHTML() {
  const v = m();
  const rows = CHAPTERS.map(c => {
    const done = v.done.includes(c.id), cur = CHAPTERS[v.ch - 1] === c && v.stage !== 'finished' && v.stage !== 'locked';
    const st = done ? '✔ Complete' : cur ? (v.stage === 'offer' ? '📜 Ready to read' : '⚔ In progress') : '🔒 Locked';
    const replay = done ? ` <button type="button" class="vqBtn small" data-mq="replay" data-id="${c.id}">Replay story</button>` : '';
    return `<li><b>${c.id} · ${esc(c.title)}</b> <span class="micro">${st}</span>${replay}</li>`;
  }).join('');
  const items = v.items.length ? v.items.map(esc).join(', ') : 'None yet';
  return `<hr><span class="eyebrow">STORY · ${esc(TITLE.toUpperCase())}</span><h2>Kael and Rowan</h2><p>A Starforge mirror rune made two heroes who look the same. The Mirror Warden wants to steal one face for good. Not blood twins: magic doubles.</p><ul class="list" id="mqChapters">${rows}</ul><p class="micro"><b>Keepsakes and rewards:</b> ${items}</p>${v.title ? `<p class="micro"><b>Title:</b> ${esc(v.title)}${v.ending ? ' · ' + esc(ENDINGS[v.ending]) : ''}</p>` : ''}`;
}
// Small coloured ring under Kael/Rowan once the "Own Paths" ending is chosen (a canvas mark, not a sprite).
export function drawMarks(C, rt) {
  if (!state_ || !state_.mirror || state_.mirror.ending !== 'paths') return;
  const k = hid(KAEL), r = hid(ROWAN);
  const at = id => id === state_.active ? { x: rt.x, y: rt.y } : rt.companions[id];
  for (const [id, col] of [[k, '#d5dcea'], [r, '#e5483c']]) { const p = at(id); if (!p || !state_.party.includes(id)) continue; C.save(); C.strokeStyle = col; C.lineWidth = 3; C.beginPath(); C.ellipse(Math.round(p.x), Math.round(p.y + 14), 20, 7, 0, 0, 7); C.stroke(); C.restore(); }
}
export const debug = {
  chapters: () => CHAPTERS.map(c => ({ id: c.id, title: c.title, zone: c.zone, fights: c.fights.length })),
  killQuestEnemies() { const rt = api.runtime; for (const e of rt.enemy.filter(x => x.mq && x.hp > 0 && !x.mqw)) { e.hold = 0; e.hp = 1; api.hitEnemy(e, state_.active, 1); } },
  setWardenHp(frac) { const e = api.runtime.enemy.find(x => x.mqw && x.hp > 0); if (!e) return false; e.hp = Math.max(1, Math.floor(e.maxHp * frac)); api.hitEnemy(e, state_.active, 1e-9); return true; },
  finishWarden() { const e = api.runtime.enemy.find(x => x.mq && !x.mqx && x.hp > 0); if (!e) return false; e.hold = 0; e.hp = 1; api.hitEnemy(e, state_.active, 1); return true; },
  heroNames: () => api.HEROES.map(h => h.name),
  playerSafe() { for (const id of state_.party) api.runtime.hp[id] = api.heroMax(id); }
};
