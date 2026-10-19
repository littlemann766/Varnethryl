/* Armory ENGINE (pure data + validation, no DOM/THREE). The UI (armoryui.js) only sends REQUESTS to Armory.request(); every request is validated here
   (owner gate, slot fit, hero eligibility, ring uniqueness, gold, caps). Client-side hiding of owner items is NOT security: ownerOnly items are refused here
   unless ownerOk() is true. No 3D gear mesh swapping exists (the Owner GLB is one mesh) - equipment changes numbers only, never the model.
   Non-Owner heroes: item stats are percent points (dmg/hp/mp/sp/def) that feed controller.setGear(). The Owner keeps his fixed rules (999,999 HP, 99,999 damage rules):
   Owner gear is shown/preview-only and bonuses() returns zeros for him. Lore height 1.905 m is untouched. */
import { KITS, LOADOUT, heroKey } from './herokits.js';

export const SLOTS = [
  { id: 'weapon', name: 'Weapon', icon: 'staff', side: 'left' }, { id: 'head', name: 'Head', icon: 'helm', side: 'left' }, { id: 'chest', name: 'Chest', icon: 'armor', side: 'left' },
  { id: 'gloves', name: 'Gloves', icon: 'glove', side: 'left' }, { id: 'legs', name: 'Legs', icon: 'pants', side: 'left' }, { id: 'boots', name: 'Boots', icon: 'boot', side: 'left' },
  { id: 'offhand', name: 'Off-hand', icon: 'shield', side: 'right' }, { id: 'necklace', name: 'Necklace', icon: 'necklace', side: 'right' }, { id: 'ring1', name: 'Ring I', icon: 'ring', side: 'right' },
  { id: 'ring2', name: 'Ring II', icon: 'ring', side: 'right' }, { id: 'trinket', name: 'Relic', icon: 'relic', side: 'right' }, { id: 'cape', name: 'Cape', icon: 'cape', side: 'right' }];
export const RARITIES = ['common', 'uncommon', 'rare', 'epic', 'legendary'];
export const ENH_MAX = 5, PRESETS = 3, ENH_PER_LEVEL = 0.1, START_GOLD = 5000;
export const enhanceCost = (cur) => 350 * (cur + 1) * (cur + 1);
const I = (id, name, slot, category, rarity, icon, stats, description, x) => Object.assign({ id, name, slot, category, rarity, icon, stats: stats || {}, description: description || '', enhanceMax: ENH_MAX }, x || {});

/* ---- shared, all non-Owner heroes (stats = percent points) ---- */
const SHARED = [
  I('iron-helm', 'Iron Helm', 'head', 'Armor', 'common', 'helm', { hp: 2, def: 2 }, 'Plain, dependable soldier equipment.'),
  I('obsidian-helm', 'Obsidian Crown', 'head', 'Armor', 'epic', 'helm', { hp: 4, def: 5, dmg: 1 }, 'A crown carved from black crystal.'),
  I('cinderplate', 'Cinderplate', 'chest', 'Armor', 'rare', 'armor', { hp: 5, def: 5 }, 'Forged in the heat of Starforge.'),
  I('shadow-grasp', 'Shadowgrasp Gauntlets', 'gloves', 'Armor', 'epic', 'glove', { dmg: 3, def: 1 }, 'Reach into the veil and seize what lies beyond.'),
  I('stone-guards', 'Stoneguard Legplates', 'legs', 'Armor', 'rare', 'pants', { hp: 3, def: 3 }, 'Rigid greaves with dependable coverage.'),
  I('ranger-boots', 'Ranger Boots', 'boots', 'Armor', 'uncommon', 'boot', { sp: 4, def: 1 }, 'Quiet on wood, grass and forest floor.'),
  I('small-buckler', 'Iron Buckler', 'offhand', 'Armor', 'common', 'shield', { def: 3 }, 'A light, reliable defensive tool.'),
  I('dawn-charm', 'Dawn Charm', 'necklace', 'Accessories', 'rare', 'necklace', { hp: 3, def: 1 }, 'The morning sun captured in silver.'),
  I('fire-ring', 'Ring of Embers', 'ring', 'Accessories', 'rare', 'ring', { dmg: 2 }, 'A warm glow pulses with every strike.'),
  I('star-ring', 'Starforge Band', 'ring', 'Accessories', 'epic', 'ring', { mp: 5, dmg: 1 }, 'Crafted beneath the stars.'),
  I('plain-ring', 'Copper Ring', 'ring', 'Accessories', 'common', 'ring', { def: 1 }, 'A simple band from a village jeweler.'),
  I('runestone', 'Ancient Runestone', 'trinket', 'Accessories', 'epic', 'relic', { hp: 3, mp: 2 }, 'Its markings refuse to hold still.'),
  I('traveler-cloak', 'Wanderer’s Cloak', 'cape', 'Armor', 'uncommon', 'cape', { sp: 3, def: 1 }, 'Practical protection on long journeys.')];
/* ---- Beth's 7 new weapons (/workspace/weapons) as OPTIONAL items; original signature weapons stay the default. dmg from the manifest's suggested tier (1..5 -> 3,4,5,7,9). glb = file under proto3d/models-weapons (data only, not attached to rigs: grips not validated) ---- */
const TIER = [0, 3, 4, 5, 7, 9];
const NEW_W = [
  { id: 'frost_greatsword', name: 'Frost Greatsword', tier: 4, heroes: ['aldric', 'darius', 'thorne', 'cedric'], icon: 'sword' }, { id: 'war_axe', name: 'War Axe', tier: 4, heroes: ['garruk', 'thorne', 'darius', 'orin'], icon: 'sword' },
  { id: 'war_spear', name: 'War Spear', tier: 3, heroes: ['orin', 'aldric', 'rook'], icon: 'sword' }, { id: 'arcane_staff', name: 'Arcane Staff', tier: 3, heroes: ['kael', 'rowan', 'talia', 'selene', 'morwen'], icon: 'staff' },
  { id: 'longbow', name: 'Longbow', tier: 3, heroes: ['elira', 'vesper', 'rook'], icon: 'sword' }, { id: 'dual_kukri', name: 'Dual Kukri', tier: 2, heroes: ['nyx', 'finn', 'rook', 'asha'], icon: 'sword' },
  { id: 'round_shield', name: 'Round Shield', tier: 0, heroes: null, icon: 'shield', offhand: true }];
const NEWWEAPONS = NEW_W.map(w => I('w-' + w.id, w.name, w.offhand ? 'offhand' : 'weapon', w.offhand ? 'Armor' : 'Weapons', w.tier >= 4 ? 'epic' : 'rare', w.icon,
  w.offhand ? { def: 4, hp: 2 } : { dmg: TIER[w.tier] }, 'Beth\u2019s new test-branch model (' + w.id + '.glb). Optional; the hero\u2019s original weapon stays the default.', { heroes: w.heroes, glb: 'proto3d/models-weapons/' + w.id + '.glb', optional: true, beth: true }));

/* ---- Owner items (ownerOnly; display/preview only, Owner rules are fixed) ---- */
const OWNER_ITEMS = [
  I('sovereign-end', "Sovereign's End", 'weapon', 'Weapons', 'legendary', 'staff', { atk: 420, mp: 250, critDamage: 35, shadow: 12 }, 'A royal staff crackling with forbidden violet light.', { ownerOnly: true, perk: 'Unholy Destruction' }),
  I('dusk-reaver', 'Dusk Reaver', 'weapon', 'Weapons', 'epic', 'sword', { atk: 355, crit: 8 }, 'Shadow-forged blade designed for close combat.', { ownerOnly: true }),
  I('yellow-hood', 'Owner’s Hood', 'head', 'Armor', 'epic', 'helm', { hp: 450, def: 60 }, 'An unmistakable yellow hood with black-tipped ears.', { ownerOnly: true }),
  I('royal-onesie', 'Royal Golden Suit', 'chest', 'Armor', 'epic', 'armor', { hp: 590, def: 210, mp: 100 }, 'Owner’s signature bright yellow outfit.', { ownerOnly: true }),
  I('golden-wraps', 'Royal Gloves', 'gloves', 'Armor', 'rare', 'glove', { def: 70, atk: 50 }, 'Flexible gloves fit for spellcasting.', { ownerOnly: true }),
  I('royal-leggings', 'Golden Leggings', 'legs', 'Armor', 'epic', 'pants', { hp: 350, def: 110 }, 'Matching trousers from the royal outfit.', { ownerOnly: true }),
  I('paw-slippers', 'Paw Slippers', 'boots', 'Armor', 'legendary', 'boot', { hp: 220, def: 30, moveSpeed: 15 }, 'Comfortable oversized slippers. Somehow, they are legendary.', { ownerOnly: true }),
  I('royal-guard', 'Royal Guard Shield', 'offhand', 'Armor', 'epic', 'shield', { hp: 275, def: 225 }, 'A regal shield inlaid with gold.', { ownerOnly: true }),
  I('shadow-pendant', 'Umbral Pendant', 'necklace', 'Accessories', 'epic', 'necklace', { mp: 80, shadow: 12 }, 'A violet crystal attuned to the dark plane.', { ownerOnly: true }),
  I('sovereign-ring', 'Sovereign’s Signet', 'ring', 'Accessories', 'legendary', 'ring', { atk: 115, mp: 70, crit: 3 }, 'A ring reserved for the ruler of Varnethryl.', { ownerOnly: true }),
  I('owner-fire-ring', 'Owner’s Ring of Embers', 'ring', 'Accessories', 'rare', 'ring', { atk: 55, critDamage: 10 }, 'A warm glow pulses with every strike.', { ownerOnly: true }),
  I('fallen-star', 'Fragment of the Fallen Star', 'trinket', 'Accessories', 'legendary', 'relic', { atk: 125, mp: 100 }, 'An unstable fragment of ancient starfire.', { ownerOnly: true }),
  I('violet-cape', 'Royal Violet Cape', 'cape', 'Armor', 'legendary', 'cape', { hp: 160, def: 45, shadow: 10 }, 'Purple velvet finished with the golden royal crest.', { ownerOnly: true })];
export const OWNER_DEFAULTS = { weapon: 'sovereign-end', head: 'yellow-hood', chest: 'royal-onesie', gloves: 'golden-wraps', legs: 'royal-leggings', boots: 'paw-slippers', necklace: 'shadow-pendant', ring1: 'sovereign-ring', ring2: 'owner-fire-ring', cape: 'violet-cape' };
export const OWNER_BASE = { hp: 999999, mp: 850, atk: 99999, def: 430 };   // display of the fixed Owner rules (not modified by gear)

const pc = (v) => Math.round(v * 100);
/* the signature weapon/armor of a hero come straight from herokits LOADOUT (real data), default equipped */
export function heroItems(key) {
  const L = LOADOUT[key]; if (!L) return [];
  return [I('sig-w-' + key, L.weapon.name, 'weapon', 'Weapons', 'rare', 'sword', { dmg: pc(L.weapon.dmgPct) }, 'Signature weapon. ' + (L.weapon.model || ''), { heroes: [key], sig: true, glb: L.weapon.glb ? 'proto3d/models-weapons/' + L.weapon.glb + '.glb' : null }),
    I('sig-a-' + key, L.armor.name, 'chest', 'Armor', 'epic', 'armor', { hp: pc(L.armor.hpPct), mp: pc(L.armor.mpPct), sp: pc(L.armor.spPct), def: pc(L.armor.defPct) }, 'Signature armor set (the hero\u2019s existing outfit).', { heroes: [key], sig: true })];
}
/* optional model variants (data only): refined rigs are NOT the default, partial refine, grips may be a few cm off. Files are not shipped in the APK yet. */
export const modelVariants = (key) => ({ default: true, refined: { id: key + '_refined', file: 'rigged/' + key + '_refined.glb', shipped: false, note: 'Optional test variant, not default' } });

export function catalogFor(key, owner) {
  const own = owner && key === 'owner';
  const all = own ? OWNER_ITEMS : [].concat(heroItems(key), SHARED, NEWWEAPONS);
  return all.filter(i => !i.heroes || i.heroes.includes(key));
}
export function defaultsFor(key, owner) {
  if (owner && key === 'owner') return Object.assign({}, OWNER_DEFAULTS);
  const o = {}; if (LOADOUT[key]) { o.weapon = 'sig-w-' + key; o.chest = 'sig-a-' + key; } return o;
}
const fits = (item, slot) => item.slot === 'ring' ? (slot === 'ring1' || slot === 'ring2') : item.slot === slot;
const STORE = 'varn:armory:v1';

export class Armory {
  /* opts: ownerOk() -> bool (the engine's owner gate), wallet {get(), spend(n)} (optional), storage (optional) */
  constructor(opts) {
    const o = opts || {}; this.ownerOk = o.ownerOk || (() => false); this.wallet = o.wallet || null; this._gold = START_GOLD;
    this.store = o.storage === undefined ? (typeof localStorage !== 'undefined' ? localStorage : null) : o.storage; this.listeners = []; this.key = ''; this.isOwnerHero = false; this.s = null; this.all = {}; this.setHero('owner', true);
  }
  get gold() { return this.wallet ? this.wallet.get() : this._gold; }
  on(fn) { this.listeners.push(fn); return this; }
  emit(ev) { for (const f of this.listeners) f(ev, this); }
  items() { return catalogFor(this.key, this.isOwnerHero).filter(i => !i.ownerOnly || this.ownerOk()); }   // Owner items are not even listed without the gate
  item(id) { return catalogFor(this.key, this.isOwnerHero).find(i => i.id === id) || null; }
  setHero(id, isOwner) {
    const key = isOwner ? 'owner' : heroKey(id); if (key === this.key && this.s) return;
    this.key = key; this.isOwnerHero = !!isOwner; this.load(); this.emit({ type: 'hero', hero: key });
  }
  fresh() { return { equipment: defaultsFor(this.key, this.isOwnerHero), enh: {}, presets: [null, null, null], active: -1, variant: 'default' }; }
  load() {
    let all = {}; try { all = JSON.parse((this.store && this.store.getItem(STORE)) || '{}') || {}; } catch (e) {} this.all = all; const sv = all[this.key], s = this.fresh();
    if (sv && typeof sv === 'object') {   // re-validate EVERYTHING from storage (it is untrusted)
      const used = new Set(); for (const [slot, id] of Object.entries(sv.equipment || {})) { const it = this.item(id); if (SLOTS.some(x => x.id === slot) && (id === null || (it && fits(it, slot) && !used.has(id) && (!it.ownerOnly || this.ownerOk())))) { s.equipment[slot] = id; if (id) used.add(id); } }
      for (const [id, l] of Object.entries(sv.enh || {})) { const it = this.item(id); if (it) s.enh[id] = Math.max(0, Math.min(it.enhanceMax, Math.floor(+l || 0))); }
      if (Array.isArray(sv.presets)) s.presets = [0, 1, 2].map(i => { const p = sv.presets[i]; if (!p || typeof p !== 'object') return null; const o = {}; for (const [slot, id] of Object.entries(p)) { const it = this.item(id); if (SLOTS.some(x => x.id === slot) && it && fits(it, slot) && (!it.ownerOnly || this.ownerOk())) o[slot] = id; } return o; });
      if (sv.variant === 'refined') s.variant = 'refined';
    }
    this.s = s;
  }
  save() { try { if (this.store) { this.all[this.key] = this.s; this.store.setItem(STORE, JSON.stringify(this.all)); } } catch (e) {} }
  level(id) { return this.s.enh[id] || 0; }
  effective(item) { const n = this.level(item.id), out = {}; for (const [k, v] of Object.entries(item.stats || {})) out[k] = Math.round(v * (1 + n * ENH_PER_LEVEL) * 10) / 10; return out; }
  statsOf(eq) { const st = {}; for (const id of Object.values(eq || this.s.equipment)) { const it = id && this.item(id); if (!it) continue; for (const [k, v] of Object.entries(this.effective(it))) st[k] = (st[k] || 0) + v; } return st; }
  /* what the combat engine consumes. Owner: always zeros (fixed rules). Owner gear can never leak into other heroes (catalog is per hero). */
  bonuses() {
    if (this.isOwnerHero) return { dmgPct: 0, hpPct: 0, mpPct: 0, spPct: 0, defPct: 0, owner: true };
    const s = this.statsOf(); return { dmgPct: (s.dmg || 0) / 100, hpPct: (s.hp || 0) / 100, mpPct: (s.mp || 0) / 100, spPct: (s.sp || 0) / 100, defPct: (s.def || 0) / 100 };
  }
  slotFor(item, want) { if (item.slot !== 'ring') return item.slot; if (want === 'ring1' || want === 'ring2') return want; return !this.s.equipment.ring1 ? 'ring1' : !this.s.equipment.ring2 ? 'ring2' : 'ring1'; }
  snapshot() { return { hero: this.key, owner: this.isOwnerHero, equipment: Object.assign({}, this.s.equipment), enh: Object.assign({}, this.s.enh), presets: this.s.presets.map(p => p && Object.assign({}, p)), active: this.s.active, variant: this.s.variant, gold: this.gold, bonuses: this.bonuses() }; }
  /* ---- the ONLY mutation entry point ---- */
  request(r) {
    const no = (error) => ({ ok: false, error, state: this.snapshot() }), done = (type, extra) => { this.save(); this.emit(Object.assign({ type }, extra)); return { ok: true, state: this.snapshot() }; };
    if (!r || typeof r !== 'object') return no('bad-request'); const S = this.s;
    switch (r.type) {
      case 'equip': {
        const it = this.item(r.itemId); if (!it) return no('unknown-item'); if (it.ownerOnly && !this.ownerOk()) return no('owner-only');
        const slot = r.slot ? String(r.slot) : this.slotFor(it); if (!SLOTS.some(x => x.id === slot) || !fits(it, slot)) return no('wrong-slot');
        if (S.equipment[slot] === it.id) return no('already-equipped');
        const prev = S.equipment[slot] || null; for (const k of Object.keys(S.equipment)) if (S.equipment[k] === it.id) S.equipment[k] = null;   // an item can never be in two slots
        S.equipment[slot] = it.id; S.active = -1; return done('equip', { slot, itemId: it.id, replaced: prev });
      }
      case 'unequip': { const slot = String(r.slot); if (!SLOTS.some(x => x.id === slot) || !S.equipment[slot]) return no('empty-slot'); const prev = S.equipment[slot]; S.equipment[slot] = null; S.active = -1; return done('unequip', { slot, replaced: prev }); }
      case 'enhance': {
        const it = this.item(r.itemId); if (!it) return no('unknown-item'); if (it.ownerOnly && !this.ownerOk()) return no('owner-only'); const lv = this.level(it.id);
        if (lv >= it.enhanceMax) return no('max-level'); const cost = enhanceCost(lv); if (this.gold < cost) return no('not-enough-gold');
        if (this.wallet) { if (!this.wallet.spend(cost)) return no('not-enough-gold'); } else this._gold -= cost; S.enh[it.id] = lv + 1; return done('enhance', { itemId: it.id, level: lv + 1, cost });
      }
      case 'savePreset': { const i = r.index | 0; if (i < 0 || i >= PRESETS) return no('bad-preset'); S.presets[i] = Object.fromEntries(Object.entries(S.equipment).filter(([, v]) => v)); S.active = i; return done('savePreset', { index: i }); }
      case 'loadPreset': {
        const i = r.index | 0; if (i < 0 || i >= PRESETS || !S.presets[i]) return no('bad-preset'); const eq = {}, used = new Set();
        for (const [slot, id] of Object.entries(S.presets[i])) { const it = this.item(id); if (!it || !fits(it, slot) || used.has(id) || (it.ownerOnly && !this.ownerOk())) continue; eq[slot] = id; used.add(id); }
        S.equipment = eq; S.active = i; return done('loadPreset', { index: i });
      }
      case 'variant': { if (r.value !== 'default' && r.value !== 'refined') return no('bad-variant'); S.variant = r.value; return done('variant', { value: r.value }); }   // data only: refined rigs are optional, not default
      case 'reset': S.equipment = defaultsFor(this.key, this.isOwnerHero); S.enh = {}; S.active = -1; return done('reset');
      default: return no('bad-request');
    }
  }
}
