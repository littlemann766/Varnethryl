// Varnethryl 0.4.0: "A Light in Dusk Hollow" quest line (Count Veyra and Mortimer).
// Additive: all progress lives in state.veyra inside the existing guildbound_rpg_save_v1 save.
// This module never touches the DOM outside its own elements and never imports game.js (see bind()).
export const TITLE = 'A Light in Dusk Hollow';
const STAGES = ['locked', 'offer', 'active', 'finished'];
const DRAWINGS = [
  { id: 'library', name: 'The Library at Dusk' },
  { id: 'candle', name: 'Two Boys, One Candle' },
  { id: 'father', name: 'For Father (never delivered)' }
];
const BOOKS = [
  { id: 'atlas', label: '📘 The Star Atlas' },
  { id: 'hymnal', label: '📕 The Dawn Hymnal' },
  { id: 'bestiary', label: '📗 The Illustrated Bestiary' }
];
const CRESTS = {
  lionguard: ['Sir Aldric', 'Dame Seraphine'], fang: ['Rook Wildbane'], starforge: ['Kael Runebinder', 'Brynn Cogwright'],
  umbral: ['Morwen Blackveil', 'Vesper Crowe'], dawnsong: ['Brother Thorne', 'Talia Stormcall', 'Asha Ironfist']
};
const ALLIES = {
  pip: { name: 'Pip the Fox', icon: '🦊', note: 'A clever fox who finds the trail.' },
  zephyr: { name: 'Zephyr the Hippogriff', icon: '🦅', note: 'Carries the wounded over rough ground.' },
  coral: { name: 'Coral the Young Mermaid', icon: '🐠', note: 'Gave Mortimer a pearl and a hope.' },
  snowy: { name: 'Snowy the Yeti Cub', icon: '🐻', note: 'Small, loyal and very cold-proof.' },
  marella: { name: 'Queen Marella', icon: '🔱', note: 'Guest ally. Sings the tide back to peace.' }
};
const P = (scene, art, who, text, extra = {}) => ({ scene, art, who, text, ...extra });
const FIRST_DRAWING_REPLY = {
  library: 'Veyra: "I drew this from the stairs. I was nine. I thought if he saw the library, he would see me."',
  candle: 'Veyra: "Two of us, one candle. I kept this one. I never showed him, because I was afraid he would think it was enough."',
  father: 'Veyra: "I wrote his name at the top three hundred times. Not once did I ask him to look."'
};

export const CHAPTERS = [
  {
    id: 'V1', title: 'The Letter', zone: 'forest', hint: 'Find Snick the Sneak in Whispering Wilds and take back the wax seal.',
    intro: [
      P('library', '📚🕯️', 'Flashback · The Dusk Court library', 'The Dusk Court library at sunset. Two boys, about ten, share one candle and one book. They were born minutes apart.'),
      P('court', '👑🧒', 'Flashback · Lord Aurelian', 'Their father lifts Mortimer\'s hand before the whole court. "My heir. My pride." Behind a pillar, young Veyra clutches a drawing he made for his father.'),
      P('library', '🖼️👣', 'Flashback', 'The drawing slips from his fingers. A servant steps on it. Nobody notices.'),
      P('library', '🌙📖', 'Flashback · Mortimer', 'Night. Mortimer finds Veyra in the library. "I\'ll tell Father you\'re the clever one." Veyra: "He doesn\'t look at the clever one. He looks at you."'),
      P('fire', '🔥🕯️', 'Flashback · The east wing', 'Years later. Veyra stands at the library door with a torch of cold violet fire. "Then let them fear me instead." The east wing burns. You control young Mortimer: which book do you carry out?', { choice: 'book', choices: BOOKS }),
      P('wilds', '🦇✉️', 'A bat arrives in Liongate', 'A bat drops a sealed letter at the feet of Elder Wren. The wax seal has been stolen on the road, but the words inside are clear.'),
      P('wilds', '✉️', 'Mortimer, in the letter', '"I am the Archivist of Dusk Hollow, and I am out of ideas. My brother is not beyond saving. He is only beyond my voice. I need other voices."'),
      P('dawn', '☀️🙏', 'Brother Thorne', '"Light does not argue with the dark. It simply stays lit. I will go." Thorne steps forward. Snick the Sneak has the seal, hiding in Whispering Wilds.')
    ],
    fights: [{ name: 'Snick the Sneak', hp: 4200, attack: 90, xp: 420, gold: 300, color: '#b79a6a' }],
    recruits: ['Brother Thorne'], allies: ['pip'], zonesUnlocked: [],
    reward: { gold: 400, shards: 10, items: ['Mortimer\'s Seal'] },
    outro: [
      P('wilds', '🦊🔏', 'Snick', 'Snick drops the seal, squeaks something rude, and bolts. A small red fox trots out of the bushes and drops a sprig of berries at your feet. Pip has decided to come along.'),
      P('dawn', '🔏', 'Reward', 'You hold Mortimer\'s Seal. It will open the gate of Dusk Hollow. Brother Thorne has joined your guild.')
    ]
  },
  {
    id: 'V2', title: 'A Shield and a Spear', zone: 'forest', hint: 'Defeat Grukk the Warlord near Mossgut\'s bridge.',
    intro: [
      P('bridge', '🌉🧌', 'Mossgut the Troll', 'At the old bridge, Mossgut blocks the way. "Vampire. Double price." Mortimer, pale, polite and nervous, pays it without a word of complaint.'),
      P('bridge', '🛡️🧛', 'Sir Aldric', '"Why should we trust a vampire?" Mortimer: "You shouldn\'t, yet. Watch what I do."'),
      P('bridge', '🐦‍⬛👁️', 'Veyra\'s ravens', 'High above, Veyra\'s raven scouts watch. Grukk the Warlord charges out of the trees, paid to turn you back.')
    ],
    fights: [{ name: 'Grukk the Warlord', hp: 9000, attack: 150, xp: 700, gold: 500, color: '#7a8c4a' }],
    recruits: ['Sir Aldric', 'Dame Seraphine'], allies: ['zephyr'], zonesUnlocked: [],
    reward: { gold: 800, shards: 15, items: ['Lionguard Banner', 'Brother\'s Oath'] },
    outro: [
      P('bridge', '🦁🛡️', 'Dame Seraphine', 'Mortimer stood in front of the blows meant for the others and never raised his hands. Seraphine lowers her sword. "A shield for the people. That includes him." The Lionguard pledge protection.'),
      P('bridge', '🤝', 'Brother\'s Oath', 'A hippogriff named Zephyr lands beside you. Mortimer joins your party as a guest ally. Brother\'s Oath: your whole party grows stronger with every friend who joins.')
    ]
  },
  {
    id: 'V3', title: 'The Trail of the Raven', zone: 'ruins', hint: 'Follow the ravens through the Ashen Ruins. Defeat Fenrik Moonhowl and Lady Noctra.',
    intro: [
      P('shrine', '🐦‍⬛⛩️', 'The burned shrine', 'The ravens lead to a burned village shrine. A poem is scratched into the wall in Veyra\'s hand: "Nobody asked the second son."'),
      P('shrine', '🧛💭', 'Mortimer', '"He has been leaving clues for me. He wanted me to follow." Vesper Crowe frowns: "Hunt a monster and you end up hunting a man. Which one is he?"'),
      P('shrine', '🌑🔮', 'Morwen Blackveil', 'The Umbral Veil says Veyra is not the first soul to fall this way. Morwen offers a spell to read his memories. First, his hunter Fenrik and the guardian Lady Noctra stand in the way.')
    ],
    fights: [
      { name: 'Fenrik Moonhowl', hp: 16000, attack: 380, xp: 1300, gold: 900, color: '#9aa0b4' },
      { name: 'Lady Noctra', hp: 20000, attack: 420, xp: 1500, gold: 1000, color: '#8b5fa8' }
    ],
    recruits: ['Finn Valecourt', 'Vesper Crowe', 'Morwen Blackveil', 'Rook Wildbane'], allies: [], zonesUnlocked: ['coast'],
    reward: { gold: 1400, shards: 20, items: ['Veyra\'s Unsent Letter'] },
    outro: [
      P('shrine', '✉️💔', 'Lady Noctra', 'Noctra kneels beside a letter Veyra never sent. It is addressed to Mortimer. The envelope is soft from handling. Mortimer takes it and does not open it yet.'),
      P('shrine', '🧭', 'The trail', 'Rook Wildbane reads the tracks: the sirens of Tidewrack Coast have been told a lie. Finn, Vesper, Morwen and Rook join the cause. Tidewrack Coast is now on your map.')
    ]
  },
  {
    id: 'V4', title: 'The Singing Tide', zone: 'coast', hint: 'Travel to Tidewrack Coast. Defeat Siren Matron Lyrae and Hydrella.',
    intro: [
      P('coast', '🌊🎶', 'Tidewrack Coast', 'Veyra\'s agents have told the sirens a lie: that you mean to lock Veyra away forever. The sea sings against you.'),
      P('coast', '🧛🌊', 'Mortimer', '"He has told them I am the villain. Maybe, to him, I am."'),
      P('coast', '🐚', 'Queen Marella', 'Queen Marella listens at the water\'s edge. Asha Ironfist steps up beside you. "Then let us show her what we are." Siren Matron Lyrae rises first.')
    ],
    fights: [
      { name: 'Siren Matron Lyrae', hp: 26000, attack: 520, xp: 2000, gold: 1400, color: '#4fc1d1' },
      { name: 'Hydrella', hp: 45000, attack: 640, xp: 2800, gold: 2000, color: '#3e8f9c' }
    ],
    recruits: ['Asha Ironfist'], allies: ['coral', 'marella'], zonesUnlocked: [],
    reward: { gold: 2000, shards: 25, items: ['Tidepearl'] },
    outro: [
      P('coast', '🐠💎', 'Coral', 'A young mermaid named Coral swims up and presses a pearl into Mortimer\'s hand. "My mama says even sad songs can have a happy ending."'),
      P('coast', '🔱', 'Queen Marella', 'Marella calls off the tide. The Tidepearl will reflect Veyra\'s mist form when it matters most. Asha joins you and Coral rides along on a bubble.')
    ]
  },
  {
    id: 'V5', title: 'The Cold Hearth', zone: 'frost', hint: 'Cross Frostbite Pass. Defeat the Frost Troll Brute, Scorpa and Skarn.',
    intro: [
      P('snow', '❄️🧍', 'A figure on the cliff', 'Veyra appears in person for the first time, a shape in the snow high above. He speaks to the party, not to Mortimer. "You are very brave. Does he tell you who he is when he looks in a mirror?"'),
      P('snow', '🧛🤚', 'Mortimer', 'Mortimer reaches toward him. Veyra turns his back. The snow closes between them like a curtain.'),
      P('snow', '⚡🧊', 'Selene and Talia', 'Selene Frostveil and Talia Stormcall step forward. "Ice and storm will keep us alive. Keep walking." The pass has its own guards.')
    ],
    fights: [
      { name: 'Frost Troll Brute', hp: 38000, attack: 780, xp: 3200, gold: 2200, color: '#9bd0e0' },
      { name: 'Scorpa', hp: 34000, attack: 800, xp: 3300, gold: 2300, color: '#c98a5a' },
      { name: 'Skarn', hp: 42000, attack: 860, xp: 3500, gold: 2500, color: '#7a8fb5' }
    ],
    recruits: ['Selene Frostveil', 'Talia Stormcall'], allies: ['snowy'], zonesUnlocked: ['hollow'],
    reward: { gold: 3000, shards: 30, items: ['Frostmoon Cloak', 'Dragon-flight to Dusk Hollow'] },
    outro: [
      P('snow', '🐲', 'Glacia', 'Glacia the ice dragon circles overhead, tilts her head at Mortimer, and chooses not to fight. She will fly you to Dusk Hollow instead.'),
      P('snow', '🧣', 'Snowy', 'A yeti cub called Snowy tucks itself into the party. Dusk Hollow is now on your map through the Dragon-flight shortcut.')
    ]
  },
  {
    id: 'V6', title: 'The Library of Ashes', zone: 'hollow', needs: { candles: 3 }, hint: 'Enter Dusk Hollow. Light 3 candles to push back the mist and defeat the guards.',
    intro: [
      P('manor', '🏚️🕯️', 'Dusk Hollow Manor', 'The west wing is untouched, a warm study kept exactly as the boys left it. The mist presses at the windows. Light the candles to push it back.'),
      P('manor', '🖼️✍️', 'Veyra\'s room', 'Veyra\'s room, which Mortimer never entered, holds hundreds of drawings addressed "Father". None were ever delivered.'),
      P('manor', '🧛📖', 'Mortimer', 'Quietly: "I thought he hated the library. He was just hiding in it." Kael reads the runes. Brynn works the sealed vault. Morwen leads the Umbral Veil in.')
    ],
    fights: [
      { name: 'Dusk Court Thrall Captain', hp: 40000, attack: 900, xp: 4000, gold: 2800, color: '#6b5a86' },
      { name: 'Shadowblade Elf Warden', hp: 46000, attack: 960, xp: 4400, gold: 3000, color: '#4b4a70' }
    ],
    recruits: ['Kael Runebinder', 'Brynn Cogwright'], allies: [], zonesUnlocked: [],
    reward: { gold: 4000, shards: 35, items: [] },
    outro: [
      P('manor', '🗝️🖼️', 'The vault', 'Brynn opens the vault. Inside lie the drawings, all of them, kept dry and in order. Take them with you, or leave what is his?', { choice: 'drawings', choices: [{ id: 'take', label: '🖼️ Take the drawings' }, { id: 'leave', label: '🚪 Leave them, they are his' }] })
    ]
  },
  {
    id: 'V7', title: 'The Twin Eclipse', zone: 'hollow', needs: { candles: 3 }, hint: 'Face Count Veyra in the ballroom. Light 3 candles, break the clones, then use the Dawn Spell.',
    intro: v => v.redo ? [
      P('ballroom', '🌫️', 'Mortimer', '"He said not yet. Then it is not never." Mortimer waits at the gate. This time you bring the drawings.')
    ] : [
      P('ballroom', '🌫️🧛', 'The ballroom', 'Veyra waits among the cold candles. "You brought the whole kingdom, brother." Mortimer: "I brought friends."'),
      P('ballroom', '🕯️', 'Phase one', 'Veyra\'s mist form cannot be struck. Light three candles to keep him solid.'),
      P('ballroom', '🦇🦇', 'Phase two', 'When he breaks, bat clones will pour out. Only the real one counts. Strike the clones first.'),
      P('ballroom', '🌘☀️', 'Phase three', 'At the eclipse a shield rises. Thorne and Seraphine can break it with a dawn spell. Mortimer will not strike. He keeps stepping in front of attacks aimed at others.')
    ],
    fights: [{ name: 'Count Veyra', hp: 120000, attack: 1500, xp: 9000, gold: 6000, color: '#3a3f7a', veyra: true }],
    recruits: [], allies: [], zonesUnlocked: [],
    reward: { gold: 10000, shards: 80, items: [] },
    outro: v => (v.drawings.length ? [
      P('ballroom', '😞🛡️', 'Veyra', '"Why do you still protect me?" Mortimer: "Because you are my brother, and I was not a good one."'),
      P('ballroom', '⚔️⬇️', 'The party', 'The party lowers its weapons. You present the Drawings and the Unsent Letter. Which drawing do you give him first?', { choice: 'firstDrawing', choices: DRAWINGS.filter(d => v.drawings.includes(d.id)).map(d => ({ id: d.id, label: '🖼️ ' + d.name })) }),
      P('dawn', '🖼️🤲', 'Veyra', () => (FIRST_DRAWING_REPLY[state_.veyra.firstDrawing] || FIRST_DRAWING_REPLY.library) + ' His hand shakes as he takes it.'),
      P('dawn', '🕯️📖', 'Veyra', '"I wanted him to look at me. He was looking. I was not looking back." Veyra drops his violet fire. The burnt library wing rebuilds itself, page by page.'),
      P('dawn', '🌅🕯️', 'The brothers', 'He cannot undo what he did, so he promises to spend his years rebuilding the villages he scared. Mortimer offers to stand beside him in the sunrise window. The brothers share a candle again. The sun rises through the east wing for the first time in years.'),
      P('dawn', '🖼️✍️✍️', 'Credits panel', 'The old drawing, repaired and framed, hangs in the library with a second signature next to the first. Rewards: Moonsilver weapon, Brothers\' Sigil, Twin Moons, and the title Bringer of Dawn.')
    ] : [
      P('ballroom', '😶‍🌫️', 'Veyra', 'Veyra yields, but he does not forgive himself. He steps back into the mist. "Not yet." Mortimer waits at the gate. The quest will reopen: go back for the drawings.')
    ])
  }
];
let state_ = null, api = null, built = false;
const cname = n => api.HEROES.find(h => h.name === n);
export function defaults() {
  return { v: 1, ch: 1, stage: 'locked', fight: 0, done: [], recruits: [], allies: [], items: [], drawings: [], zones: [], candles: 0, dawn: false, book: null, firstDrawing: null, ending: null, title: null, redo: false, guest: false, seen: {} };
}
const arr = a => Array.isArray(a) ? a.filter(x => typeof x === 'string' || typeof x === 'number') : [];
export function ensure(s) {
  const d = defaults(), v = s.veyra && typeof s.veyra === 'object' ? s.veyra : {};
  const r = { ...d, ...v };
  r.ch = Math.min(7, Math.max(1, Math.floor(+r.ch) || 1));
  if (!STAGES.includes(r.stage)) r.stage = 'locked';
  r.fight = Math.max(0, Math.floor(+r.fight) || 0);
  for (const k of ['done', 'recruits', 'allies', 'items', 'drawings', 'zones']) r[k] = arr(r[k]);
  r.candles = Math.min(3, Math.max(0, Math.floor(+r.candles) || 0)); r.dawn = !!r.dawn; r.redo = !!r.redo; r.guest = !!r.guest;
  r.seen = r.seen && typeof r.seen === 'object' ? r.seen : {};
  s.veyra = r; return s;
}
const chap = () => CHAPTERS[state_.veyra.ch - 1];
const prop = (c, k) => typeof c[k] === 'function' ? c[k](state_.veyra) : c[k];
const $ = id => document.getElementById(id);
// ---------- binding ----------
export function bind(a) {
  api = a; state_ = a.state(); built = true;
  document.addEventListener('click', onClick);
  $('storyDlg').addEventListener('cancel', e => { e.preventDefault(); skip(); });
  render();
}
export function rebind() { state_ = api.state(); ensure(state_); render(); }
// ---------- progression ----------
// Mortimer walks with the party only once V2 has begun (V1 done and V2 active) or is complete. Progress that is inconsistent
// (e.g. a hand-edited/imported save with V1 done but later chapters not) must not spawn him.
function mortimerPresent() { const v = state_ && state_.veyra; if (!v || !Array.isArray(v.done) || !v.done.includes('V1')) return false; return v.done.includes('V2') || (v.ch === 2 && v.stage === 'active'); }
function unlockCheck() {
  const v = state_.veyra;
  if (v.stage === 'locked' && (state_.kills >= 3 || state_.questStep >= 1)) { v.stage = 'offer'; api.log('A bat has delivered a letter to Liongate. Open the story card to read it.'); api.save(); setTimeout(render, 0); }
}
export function atk() {
  if (!state_) return 1; const v = state_.veyra; if (!v) return 1;
  let m = 1;
  if (v.items.includes('Brother\'s Oath')) m += Math.min(.25, .02 * (v.recruits.length + v.allies.length));
  if (v.items.includes('Twin Moons')) m += .08;
  if (v.guest && state_.zone === 'boss') m += .10;
  return m;
}
export function def() { if (!state_) return 1; const v = state_.veyra; if (!v) return 1; return 1 + (v.items.includes('Twin Moons') ? .08 : 0) + (v.items.includes('Brother\'s Oath') ? Math.min(.15, .01 * v.recruits.length) : 0); }
function grantRecruit(name) {
  const h = cname(name); if (!h) return;
  const v = state_.veyra;
  if (!v.recruits.includes(name)) v.recruits.push(name);
  if (!state_.unlocked.includes(h.id)) state_.unlocked.push(h.id);
  const lv = Math.max(1, Math.round(state_.party.reduce((a, id) => a + api.nLevel(id), 0) / Math.max(1, state_.party.length)));
  state_.heroLevels[h.id] = Math.max(state_.heroLevels[h.id] || 1, lv);
  if (!state_.party.includes(h.id) && state_.party.length < state_.partyCap) { state_.party.push(h.id); api.runtime.hp[h.id] = api.heroMax(h.id); }
}
function startIntro() {
  const v = state_.veyra, c = chap();
  if (v.stage !== 'offer') return;
  play(prop(c, 'intro'), () => activate());
}
function activate() {
  const v = state_.veyra, c = chap();
  if (v.stage !== 'offer') return;
  v.stage = 'active'; v.fight = 0; v.candles = 0; v.dawn = false;
  if (c.id === 'V7' && v.redo) { v.drawings = DRAWINGS.map(d => d.id); v.items.includes('Veyra\'s Drawings') || v.items.push('Veyra\'s Drawings'); }
  if (c.id === 'V2') { /* Mortimer joins from here */ }
  api.log(`New objective: ${c.hint}`); api.save(); render();
}
function spawnFight() {
  const c = chap(), v = state_.veyra, tpl = c.fights[v.fight]; if (!tpl) return;
  const rt = api.runtime, ang = Math.random() * Math.PI * 2;
  const x = Math.min(1700, Math.max(105, rt.x + Math.cos(ang) * 190)), y = Math.min(1080, Math.max(105, rt.y + Math.sin(ang) * 150));
  const e = { ...tpl, id: ++rt.enemyIds, qid: 'q', qboss: true, boss: false, x, y, maxHp: tpl.hp, hp: tpl.hp, attackAt: 0, stunned: 0, slowUntil: 0, burn: 0, dx: 0, dy: 0 };
  if (tpl.veyra) { e.qid = 'veyra'; e.phase = 1; e.hold = e.maxHp; e.maxHp = tpl.hp; }
  rt.enemy.push(e); api.log(`${tpl.name} appears!`);
}
function spawnClones() {
  const rt = api.runtime;
  for (let i = 0; i < 2; i++) { const a = i * Math.PI + Math.random(); rt.enemy.push({ name: 'Bat Veyra', hp: 3500, maxHp: 3500, attack: 500, xp: 200, gold: 100, color: '#5b5f9c', id: ++rt.enemyIds, qid: 'clone', qboss: false, boss: false, x: Math.min(1700, Math.max(105, rt.x + Math.cos(a) * 170)), y: Math.min(1080, Math.max(105, rt.y + Math.sin(a) * 140)), attackAt: 0, stunned: 0, slowUntil: 0, burn: 0, dx: 0, dy: 0 }); }
}
let tickAcc = 0;
export function tick(dt) {
  if (!state_) return;
  tickAcc += dt; if (tickAcc < 350) return; tickAcc = 0;
  unlockCheck();
  const v = state_.veyra, c = chap();
  if (v.stage !== 'active' || !c) return;
  const rt = api.runtime;
  const vey = rt.enemy.find(e => e.qid === 'veyra' && e.hp > 0);
  if (vey) veyraPhases(vey);
  if (state_.zone === c.zone && v.fight < c.fights.length && !rt.enemy.some(e => (e.qid === 'q' || e.qid === 'veyra') && e.hp > 0)) { spawnFight(); render(); }
}
function veyraPhases(e) {
  const v = state_.veyra, M = e.maxHp, say = t => { api.toast(t); api.log(t); };
  if (e.phase === 1 && v.candles >= 3) { e.phase = 2; e.hold = .66 * M; say('The candles hold. Veyra is solid. Mortimer: "Brother, please stop!"'); render(); }
  else if (e.phase === 2 && e.hp <= .66 * M + 1) { e.phase = 3; e.hold = .66 * M; spawnClones(); say('Veyra bursts into bats! Strike the clones.'); render(); }
  else if (e.phase === 3 && !api.runtime.enemy.some(x => x.qid === 'clone' && x.hp > 0)) { e.phase = 4; e.hold = .33 * M; say('The real Veyra staggers. Mortimer steps in front of a blow meant for Seraphine.'); render(); }
  else if (e.phase === 4 && e.hp <= .33 * M + 1) { e.phase = 5; e.hold = .33 * M; v.dawn = false; say('Eclipse! A shield rises around Veyra. Use the Dawn Spell.'); render(); }
  else if (e.phase === 5 && v.dawn) { e.phase = 6; e.hold = 0; say('The dawn spell shatters his shield. "Why do you still protect me?"'); render(); }
}
export function onDefeat(e) {
  if (!e || !e.qid) return;
  const v = state_.veyra, c = chap();
  if (e.qid === 'clone') return;
  if (v.stage !== 'active' || !c) return;
  v.fight++;
  if (v.fight < c.fights.length) { api.toast(`Next: ${c.fights[v.fight].name}`); api.save(); render(); return; }
  tryFinish();
}
function needsMet() { const c = chap(), v = state_.veyra; return !c.needs || (!c.needs.candles || v.candles >= c.needs.candles); }
function tryFinish() {
  const v = state_.veyra, c = chap();
  if (v.stage !== 'active' || v.fight < c.fights.length) return;
  if (!needsMet()) { api.toast(`Light the candles first (${v.candles}/3).`); render(); return; }
  finish();
}
function finish() {
  const v = state_.veyra, c = chap(), id = c.id;
  if (v.done.includes(id)) return;
  const redeemed = id === 'V7' && v.drawings.length > 0;
  if (id === 'V7' && !redeemed) {
    // "Not yet" ending: Veyra retreats and the quest reopens as a later side quest.
    v.ending = 'notyet'; v.redo = true; v.stage = 'offer'; v.fight = 0;
    api.save(); render();
    play(prop(c, 'outro'));
    return;
  }
  v.done.push(id);
  for (const n of c.recruits) grantRecruit(n);
  for (const a of c.allies) if (!v.allies.includes(a)) v.allies.push(a);
  for (const z of c.zonesUnlocked) if (!v.zones.includes(z)) v.zones.push(z);
  for (const it of c.reward.items) if (!v.items.includes(it)) v.items.push(it);
  state_.gold += c.reward.gold; state_.shards += c.reward.shards;
  if (id === 'V2') grantRecruit('Sir Aldric');
  if (id === 'V7') grantEnding();
  api.log(`Chapter complete: ${c.title}. +${fmt(c.reward.gold)} gold, +${c.reward.shards} shards.`);
  if (id === 'V7') { v.stage = 'finished'; } else { v.ch = v.ch + 1; v.stage = 'offer'; v.fight = 0; }
  v.candles = 0; v.dawn = false;
  api.renderCounters(); api.renderParty && api.renderParty(); api.renderHeroes && api.renderHeroes(); api.save(); render();
  const out = prop(c, 'outro');
  play(out);
}
const fmt = n => Math.round(n).toLocaleString('en-US');
function grantEnding() {
  const v = state_.veyra, hid = state_.active;
  v.ending = 'redeemed'; v.title = 'Bringer of Dawn';
  const crestsOk = Object.values(CRESTS).every(list => list.some(n => v.recruits.includes(n) || n === 'Sir Aldric'));
  v.guest = !v.redo && v.drawings.length >= DRAWINGS.length && crestsOk;
  for (const it of ['Twin Moons', 'Brothers\' Sigil', 'Moonsilver weapon skin']) if (!v.items.includes(it)) v.items.push(it);
  const w = api.baseItem('weapon', hid, 9); w.name = 'Moonsilver ' + w.name; state_.gear.push(w);
  const s = api.baseItem('charm', hid, 6); s.name = 'Brothers\' Sigil'; state_.gear.push(s);
  api.toast('Redemption! Moonsilver weapon, Brothers\' Sigil, and the title Bringer of Dawn are yours.');
}
// ---------- story panels ----------
let seq = null;
export function play(panels, done, replay = false) {
  if (!panels || !panels.length) { done && done(); return; }
  seq = { panels, i: 0, done, closed: false, replay };
  showPanel(); const d = $('storyDlg'); if (!d.open) d.showModal();
}
function showPanel() {
  const p = seq.panels[seq.i], n = seq.panels.length, text = typeof p.text === 'function' ? p.text() : p.text;
  const choices = p.choices ? `<div class="stChoices">${p.choices.map(c => `<button type="button" class="stChoice" data-vq="choice" data-key="${p.choice}" data-id="${c.id}">${api.esc(c.label)}</button>`).join('')}</div>` : '';
  $('storyBody').innerHTML = `<div class="stFrame sc-${p.scene}"><span class="stNum">PANEL ${seq.i + 1} / ${n}</span><div class="stArt" aria-hidden="true">${p.art}</div></div><div class="stBox"><b class="stWho">${api.esc(p.who)}</b><p class="stText" id="stText">${api.esc(text)}</p>${choices}</div>`;
  $('stNext').hidden = !!p.choices; $('stNext').textContent = seq.i === n - 1 ? 'Done ✓' : 'Next ▶';
}
function advancePanel() {
  if (!seq) return;
  if (seq.panels[seq.i].choices) return;
  if (seq.i < seq.panels.length - 1) { seq.i++; showPanel(); } else closeSeq();
}
function closeSeq() {
  const s = seq; seq = null; $('storyDlg').close();
  if (s && !s.closed) { s.closed = true; s.done && s.done(); }
  render();
}
function pick(key, id) {
  const v = state_.veyra;
  if (seq && seq.replay) { if (seq.i < seq.panels.length - 1) { seq.i++; showPanel(); } else closeSeq(); return; }
  if (key === 'book') { v.book = id; const b = BOOKS.find(x => x.id === id); const it = 'Keepsake: ' + b.label.replace(/^\S+\s/, ''); if (!v.items.includes(it)) v.items.push(it); }
  if (key === 'drawings') { if (id === 'take') { v.drawings = DRAWINGS.map(d => d.id); if (!v.items.includes('Veyra\'s Drawings')) v.items.push('Veyra\'s Drawings'); } else v.drawings = []; }
  if (key === 'firstDrawing') v.firstDrawing = id;
  api.save();
  if (!seq) return;
  if (seq.i < seq.panels.length - 1) { seq.i++; showPanel(); } else closeSeq();
}
function skip() {
  if (!seq) { $('storyDlg').close(); return; }
  // Skipping auto-picks the first choice so progress never gets stuck.
  for (let i = seq.i; i < seq.panels.length && !seq.replay; i++) { const p = seq.panels[i]; if (p.choices) { const v = state_.veyra, pk = p.choices[0].id; if (p.choice === 'book' && !v.book) pick('book', pk); else if (p.choice === 'drawings' && !seq.picked) { v.drawings = DRAWINGS.map(d => d.id); v.items.includes('Veyra\'s Drawings') || v.items.push('Veyra\'s Drawings'); } else if (p.choice === 'firstDrawing' && !v.firstDrawing) v.firstDrawing = pk; } }
  seq.i = seq.panels.length - 1; closeSeq();
}
// ---------- UI ----------
function onClick(e) {
  const b = e.target.closest('[data-vq]'); if (!b) return;
  const a = b.dataset.vq;
  if (a === 'read') startIntro();
  else if (a === 'next') advancePanel();
  else if (a === 'skip') skip();
  else if (a === 'choice') pick(b.dataset.key, b.dataset.id);
  else if (a === 'goto') { const c = chap(); if (c) api.enterZone(c.zone); }
  else if (a === 'candle') lightCandle();
  else if (a === 'dawn') dawnSpell();
  else if (a === 'replay') { const c = CHAPTERS.find(x => x.id === b.dataset.id); if (c) { if (api.closeModal) api.closeModal(); play([...prop(c, 'intro'), ...(typeof c.outro === 'function' ? [] : c.outro)], null, true); } }
  else if (a === 'journal') api.openJournal();
}
function lightCandle() {
  const v = state_.veyra, c = chap();
  if (v.stage !== 'active' || !c || !c.needs?.candles || state_.zone !== 'hollow' || v.candles >= 3) return;
  v.candles++; api.toast(`Candle lit (${v.candles}/3). The mist recoils.`); api.log(`You light a candle (${v.candles}/3).`); api.save();
  if (c.id === 'V6') tryFinish();
  render();
}
function dawnSpell() {
  const v = state_.veyra, vey = api.runtime.enemy.find(e => e.qid === 'veyra' && e.hp > 0);
  if (!vey || vey.phase !== 5) return;
  v.dawn = true; api.sfx && api.sfx('skill'); api.save(); veyraPhases(vey); render();
}
export function status() {
  const v = state_.veyra, c = chap(); if (!c) return null;
  const vey = api.runtime.enemy.find(e => e.qid === 'veyra' && e.hp > 0);
  return { chapter: c.id, stage: v.stage, fight: v.fight, fights: c.fights.length, candles: v.candles, phase: vey ? vey.phase : 0 };
}
export function render() {
  if (!built || !state_) return;
  unlockCheck();
  const v = state_.veyra, c = chap(), card = $('veyraCard'), banner = $('storyBanner');
  if (!card) return;
  const finished = v.stage === 'finished';
  if (v.stage === 'locked') {
    card.hidden = false;
    card.innerHTML = `<span class="eyebrow">STORY · ${esc(TITLE.toUpperCase())}</span><h2>A letter is coming</h2><p>Defeat 3 monsters in Whispering Wilds and a messenger will find you.</p>`;
    banner.hidden = true; return;
  }
  card.hidden = false;
  if (finished) {
    card.innerHTML = `<span class="eyebrow">STORY · ${esc(TITLE.toUpperCase())}</span><h2>The brothers are reunited</h2><p>Title: ${esc(v.title || '')}. ${v.guest ? 'Veyra and Mortimer will stand with you in the Titan Vault.' : 'Veyra is spared and redeemed.'}</p><div class="buttonRow"><button type="button" class="vqBtn" data-vq="journal" id="vqJournal">📜 Story journal</button></div>`;
    banner.hidden = true; return;
  }
  const z = api.zones.find(x => x.id === c.zone);
  const inZone = state_.zone === c.zone;
  let html = `<span class="eyebrow">STORY · ${esc(TITLE.toUpperCase())}</span><h2>${c.id} · ${esc(c.title)}</h2>`;
  const btns = [];
  if (v.stage === 'offer') {
    html += `<p>${v.redo ? 'Veyra said "Not yet." Mortimer waits at the gate.' : 'A new chapter of the story is ready.'}</p>`;
    btns.push(`<button type="button" class="vqBtn gold" data-vq="read" id="vqRead">📜 Read the story</button>`);
    banner.hidden = false; banner.innerHTML = `<button type="button" class="storyBannerBtn" data-vq="read" id="vqBanner">📜 New chapter ${c.id}: ${esc(c.title)} · tap to read</button>`;
  } else {
    banner.hidden = true;
    const total = c.fights.length, cleared = Math.min(v.fight, total);
    html += `<p>${esc(c.hint)}</p><div class="meter"><div style="width:${(cleared / total) * 100}%"></div></div><p class="micro" id="vqNums">Fights ${cleared} / ${total}${c.needs ? ` · Candles ${v.candles} / ${c.needs.candles}` : ''}${!inZone ? ` · Go to ${esc(z.name)}` : ''}</p>`;
    if (!inZone) btns.push(`<button type="button" class="vqBtn gold" data-vq="goto" id="vqGoto">➤ Travel to ${esc(z.name)}</button>`);
    if (inZone && c.needs?.candles && v.candles < 3) btns.push(`<button type="button" class="vqBtn gold" data-vq="candle" id="vqCandle">🕯 Light a candle (${v.candles}/3)</button>`);
    const vey = api.runtime.enemy.find(e => e.qid === 'veyra' && e.hp > 0);
    if (vey) html += `<p class="micro" id="vqPhase">${['', 'Veyra is mist. Light all three candles.', 'Veyra is solid. Strike him down to the eclipse.', 'Defeat the bat clones.', 'Strike the real Veyra.', 'Eclipse shield. Use the Dawn Spell.', 'The shield is broken. Finish the fight.'][vey.phase] || ''}</p>`;
    if (vey && vey.phase === 5) btns.push(`<button type="button" class="vqBtn gold" data-vq="dawn" id="vqDawn">☀ Dawn Spell</button>`);
  }
  btns.push(`<button type="button" class="vqBtn" data-vq="journal" id="vqJournal">📜 Story journal</button>`);
  card.innerHTML = html + `<div class="buttonRow">${btns.join('')}</div>`;
}
const esc = s => String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
export function journalHTML() {
  const v = state_.veyra;
  const rows = CHAPTERS.map((c, i) => {
    const done = v.done.includes(c.id), cur = v.ch === c.id && v.stage !== 'finished' && v.stage !== 'locked';
    const st = done ? '✔ Complete' : cur ? (v.stage === 'offer' ? '📜 Ready to read' : '⚔ In progress') : '🔒 Locked';
    const replay = done ? ` <button type="button" class="vqBtn small" data-vq="replay" data-id="${c.id}">Replay story</button>` : '';
    return `<li><b>${c.id} · ${esc(c.title)}</b> <span class="micro">${st}</span>${replay}</li>`;
  }).join('');
  const heroes = v.recruits.length ? v.recruits.map(esc).join(', ') : 'None yet';
  const allies = v.allies.length ? v.allies.map(a => `${ALLIES[a]?.icon || ''} ${esc(ALLIES[a]?.name || a)}`).join(', ') : 'None yet';
  const items = v.items.length ? v.items.map(esc).join(', ') : 'None yet';
  return `<hr><span class="eyebrow">STORY · ${esc(TITLE.toUpperCase())}</span><h2>The Brothers of Dusk Hollow</h2><p>Count Veyra and Mortimer are twin brothers. Mortimer, the elder, was favored, and Veyra turned cold with jealousy. Mortimer gathers friends from every crest to bring his brother home.</p><ul class="list" id="vqChapters">${rows}</ul><p class="micro"><b>Recruited heroes:</b> ${heroes}</p><p class="micro"><b>Creature allies:</b> ${allies}</p><p class="micro"><b>Keepsakes and rewards:</b> ${items}</p>${v.title ? `<p class="micro"><b>Title:</b> ${esc(v.title)}</p>` : ''}`;
}
// ---------- world drawing (canvas-drawn guests, no extra sprites; heroes keep one sprite each) ----------
const pos = {};
function follow(key, tx, ty, dt) { const p = pos[key] || (pos[key] = { x: tx, y: ty }); const d = Math.hypot(tx - p.x, ty - p.y); if (d > 260) { p.x = tx; p.y = ty; } else if (d > 1) { const q = Math.min(d, Math.max(1, dt * .16)); p.x += (tx - p.x) / d * q; p.y += (ty - p.y) / d * q; } return p; }
let lastT = 0;
export function drawAllies(C, rt) {
  const t = rt.time, dt = Math.min(60, Math.max(0, t - lastT)); lastT = t;
  if (!state_ || !mortimerPresent()) return;
  const v = state_.veyra;
  const m = follow('mort', rt.x + 70, rt.y - 26, dt);
  figure(C, m.x, m.y, t, '#2b2f55', '#c9a85b', 'Mortimer', false);
  if (v.guest && state_.zone === 'boss') { const q = follow('vey', rt.x - 80, rt.y - 30, dt); figure(C, q.x, q.y, t, '#1b2a5c', '#7a6bd6', 'Veyra', true); }
  let i = 0;
  for (const a of v.allies) { if (!ALLIES[a] || a === 'marella') continue; const p = follow(a, rt.x - 60 - i * 26, rt.y + 52 + (i % 2) * 14, dt); C.save(); C.translate(Math.round(p.x), Math.round(p.y + Math.sin(t * .004 + i) * 2)); C.fillStyle = '#06131a99'; C.beginPath(); C.ellipse(0, 8, 11, 4, 0, 0, 7); C.fill(); C.font = '20px system-ui,sans-serif'; C.textAlign = 'center'; C.fillText(ALLIES[a].icon, 0, 4); C.restore(); i++; }
}
function figure(C, x, y, t, cloak, trim, label, crown) {
  C.save(); C.translate(Math.round(x), Math.round(y + Math.sin(t * .003) * 1.5));
  C.fillStyle = '#06131aa8'; C.beginPath(); C.ellipse(0, 14, 17, 5, 0, 0, 7); C.fill();
  C.fillStyle = cloak; C.beginPath(); C.moveTo(-17, -22); C.lineTo(-9, 12); C.lineTo(9, 12); C.lineTo(17, -22); C.lineTo(8, -14); C.lineTo(-8, -14); C.closePath(); C.fill();
  C.fillStyle = '#1a1c33'; C.fillRect(-7, -22, 14, 32);
  C.fillStyle = '#e8d2b8'; C.beginPath(); C.arc(0, -29, 8, 0, 7); C.fill();
  C.fillStyle = '#2b1f2d'; C.fillRect(-8, -38, 16, 6);
  C.strokeStyle = trim; C.lineWidth = 1.5; C.strokeRect(-6, -31, 5, 4); C.strokeRect(1, -31, 5, 4);
  if (crown) { C.fillStyle = trim; C.fillRect(-6, -41, 12, 3); }
  C.fillStyle = trim; C.fillRect(-7, -14, 14, 2);
  C.font = 'bold 10px system-ui,sans-serif'; C.textAlign = 'center'; C.fillStyle = '#e6d9ff'; C.fillText(label, 0, -45);
  C.restore();
}
// ---------- test hooks (read-only helpers; they ship in the page like window.__vn does) ----------
export const debug = {
  mortimerPresent: () => mortimerPresent(),
  chapters: () => CHAPTERS.map(c => ({ id: c.id, title: c.title, zone: c.zone, fights: c.fights.length })),
  killQuestEnemies() { const rt = api.runtime; for (const e of rt.enemy.filter(x => x.qid && x.hp > 0 && x.qid !== 'veyra')) { e.hold = 0; e.hp = 1; api.hitEnemy(e, state_.active, 1); } },
  setVeyraHp(frac) { const e = api.runtime.enemy.find(x => x.qid === 'veyra' && x.hp > 0); if (!e) return false; e.hp = Math.max(1, Math.floor(e.maxHp * frac)); api.hitEnemy(e, state_.active, 1e-9); return true; },
  finishVeyra() { const e = api.runtime.enemy.find(x => x.qid === 'veyra' && x.hp > 0); if (!e) return false; e.hold = 0; e.hp = 1; api.hitEnemy(e, state_.active, 1); return true; },
  playerSafe() { for (const id of state_.party) api.runtime.hp[id] = api.heroMax(id); }
};
