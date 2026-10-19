/* Hero kits (data-driven): per-hero basic style + 3 skills + ultimate, color and icon. No logic here; rules run in controller.js (damage only via calc.js).
   kinds: melee (cone), aoe (ring), ranged (target), line (corridor), dash (move + corridor hit), blink (teleport behind target + hit), heal, storm (3 ticks), meteor (delayed area), shield.
   Draft table for all 20 heroes: /workspace/varn/HERO-ABILITIES.md. Archetypes implemented first: aldric, elira, rowan, thorne, nyx. Others fall back to the generic bar. */
const sk = (hero, n, o) => Object.assign({ id: hero + '.' + n, kit: true, stagger: 0, windup: 0.18, T: 0.5, arc: 0.3, cost: {}, mult: 1.5 }, o);
const ult = (hero, o) => sk(hero, 'u', Object.assign({ fury: 100, cd: 30, windup: 0.3, T: 0.9, cost: {} }, o));
export const KITS = {
  aldric: { color: '#d9b44a', basic: 'Shield Bash combo', skills: [
    sk('aldric', 1, { name: 'Shield Bash', icon: 'shield', cd: 4, cost: { sp: 15 }, kind: 'melee', range: 3.6, arc: 0.3, mult: 1.6, stagger: 1 }),
    sk('aldric', 2, { name: 'Guardian Slam', icon: 'ring', cd: 8, cost: { sp: 25 }, kind: 'aoe', range: 6, arc: -1, mult: 2.2, stagger: 1, knock: 4 }),
    sk('aldric', 3, { name: 'Bulwark Charge', icon: 'dash', cd: 12, cost: { sp: 30 }, kind: 'dash', range: 9, dist: 9, arc: 0.7, mult: 2.4, stagger: 1 }),
    ult('aldric', { name: 'Lionheart Bulwark', icon: 'lion', kind: 'aoe', range: 10, arc: -1, mult: 4.5, stagger: 1, knock: 6, shield: 4 })] },
  elira: { color: '#5fbf6a', basic: 'Quick-draw arrow', skills: [
    sk('elira', 1, { name: 'Aimed Shot', icon: 'arrow', cd: 4, cost: { sp: 12 }, kind: 'ranged', range: 20, arc: 0.6, mult: 1.8 }),
    sk('elira', 2, { name: 'Piercing Arrow', icon: 'line', cd: 8, cost: { mp: 20 }, kind: 'line', range: 22, arc: 0.93, mult: 2.6 }),
    sk('elira', 3, { name: 'Snare Trap', icon: 'trap', cd: 12, cost: { mp: 25 }, kind: 'aoe', range: 5, arc: -1, mult: 1.2, stagger: 2 }),
    ult('elira', { name: 'Eagle-Eye Barrage', icon: 'volley', kind: 'storm', range: 16, arc: 0.4, mult: 6 })] },
  rowan: { color: '#ff7a2a', basic: 'Firebolt', skills: [
    sk('rowan', 1, { name: 'Firebolt', icon: 'flame', cd: 4, cost: { mp: 15 }, kind: 'ranged', range: 18, arc: 0.6, mult: 2 }),
    sk('rowan', 2, { name: 'Flame Wave', icon: 'wave', cd: 8, cost: { mp: 25 }, kind: 'melee', range: 9, arc: 0.25, mult: 2.4, stagger: 1 }),
    sk('rowan', 3, { name: 'Ember Burst', icon: 'ring', cd: 12, cost: { mp: 30 }, kind: 'aoe', range: 6.5, arc: -1, mult: 2.6, stagger: 1 }),
    ult('rowan', { name: 'Meteor Burst', icon: 'meteor', kind: 'meteor', mult: 8, radius: 10, delay: 1.4 })] },
  thorne: { color: '#f3f0d0', basic: 'Staff light bolt', skills: [
    sk('thorne', 1, { name: 'Radiant Bolt', icon: 'sun', cd: 4, cost: { mp: 12 }, kind: 'ranged', range: 18, arc: 0.6, mult: 1.8 }),
    sk('thorne', 2, { name: 'Mend', icon: 'heal', cd: 8, cost: { mp: 25 }, kind: 'heal', heal: 0.3 }),
    sk('thorne', 3, { name: 'Holy Smite', icon: 'ring', cd: 12, cost: { mp: 30 }, kind: 'aoe', range: 5.5, arc: -1, mult: 2.4, stagger: 1 }),
    ult('thorne', { name: 'Divine Renewal', icon: 'heal2', kind: 'aoe', range: 8, arc: -1, mult: 3, heal: 0.6 })] },
  nyx: { color: '#7a4bd0', basic: 'Twin dagger flurry', skills: [
    sk('nyx', 1, { name: 'Dagger Flurry', icon: 'dagger', cd: 4, cost: { sp: 15 }, kind: 'storm', range: 3.8, arc: -1, mult: 2.4 }),
    sk('nyx', 2, { name: 'Shadow Step', icon: 'blink', cd: 8, cost: { sp: 20 }, kind: 'blink', range: 14, arc: 0.6, mult: 2 }),
    sk('nyx', 3, { name: 'Poison Cut', icon: 'poison', cd: 12, cost: { sp: 25 }, kind: 'melee', range: 3.8, arc: 0.3, mult: 2.6, stagger: 1 }),
    ult('nyx', { name: 'Shadow Flurry', icon: 'storm', kind: 'storm', range: 8, arc: -1, mult: 7 })] },
};
export const heroKey = id => String(id || '').replace(/^[a-z]:/, '').replace(/_(smooth|new\d*|cl_arms|fight\d*)$/, '');
export const kitFor = id => KITS[heroKey(id)] || null;
export const kitSkill = (kit, id) => (kit && kit.skills.find(s => s.id === id)) || null;
