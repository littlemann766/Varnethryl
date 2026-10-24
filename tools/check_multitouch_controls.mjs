// Regression gate: a second finger must be able to jump and cast attacks while
// the first pointer retains movement. Runs offline in Android/Pages Actions.
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const read=p=>readFileSync(new URL('../'+p,import.meta.url),'utf8');
const main=read('www/proto3d/main.js');
const hud=read('www/proto3d/combat/hud.js');
const fight=read('www/proto3d/fight.js');
const css=read('www/proto3d/varn-ui.css');
const html=read('www/proto3d.html');

// Joystick ownership must not be replaced by a simultaneous skill/jump touch.
assert.ok(main.includes('if(joy.id!==null||(e.pointerType===\'mouse\'&&e.button!==0))return;'));
assert.ok(main.includes('if(e.pointerId!==joy.id)return;'));
assert.ok(main.includes("stick.addEventListener('lostpointercapture',joyEnd)"));
assert.ok(main.includes('jumpPointer=e.pointerId;'));
assert.ok(main.includes("jumpButton?.addEventListener('pointerdown',e=>"));
assert.ok(main.includes('jumpButton.setPointerCapture(e.pointerId)'));
assert.ok(main.includes('if(e.pointerId!==jumpPointer)return;'));
assert.ok(main.includes('if(e.detail===0)jump()'),'click is for keyboard, not for delayed mobile touch');
assert.ok(!main.includes("getElementById('jumpBtn')?.addEventListener('click'"),'no old click-only jumping');
assert.ok(main.includes('if(jumpsUsed>=jumpLimit())return false;'),'double/verified quadruple jump stays enforced');

// Real circle and separate accessible touch target (not a rectangular action).
assert.match(html,/id="jumpBtn" aria-label="Jump"/);
assert.match(html,/class="vn-jump-arrow"/);
assert.match(css,/#moveActions #jumpBtn\s*\{/);
assert.match(css,/border-radius:50%!important/);
assert.match(css,/touch-action:none!important/);

// Actions claim only their own pointer, and attack on down, even when the
// joystick's pointerId is active. No global single-touch gate is allowed.
assert.ok(hud.includes('this.actionPointers=new Set()'));
assert.ok(hud.includes('this.actionPointers.add(e.pointerId)'));
assert.ok(hud.includes('this.actionPointers.delete(e.pointerId)'));
assert.ok(hud.includes('b.setPointerCapture(e.pointerId)'));
assert.ok(hud.includes('if(key!==null)api.use(key)'));
assert.ok(hud.includes("addEventListener('pointercancel',up)"));
assert.ok(hud.includes('#cb .cx>.sl,#cb .ulp button{touch-action:none!important'));
assert.ok(hud.includes('if(this.ultP&&this.ultP.id===e.pointerId)'),'ultimate release must use its own finger');

// Animation-locked skill presses are buffered; skills are not gated by
// joystick movement. Attack cooldowns/resources still remain authoritative.
assert.ok(fight.includes('let bufferedSkill=null'));
assert.ok(fight.includes('bufferedSkill={key:i,remaining:1.3}'));
assert.ok(fight.includes('bufferedSkill.remaining-=dt'));
assert.ok(fight.includes('else if(!cc.busy())'));
assert.ok(fight.includes('const key=bufferedSkill.key;bufferedSkill=null;cc.use(key);'));
assert.ok(fight.includes('bufferedSkill=null;on = false;'));
assert.ok(fight.includes("window.__p3d?.jump?.()"),'combat Jump uses world jump physics');

console.log('PASS: two-pointer joystick + circular instant Jump + moving skill presses and buffered attacks.');
