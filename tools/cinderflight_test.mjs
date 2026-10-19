import { createCinderFlight, cinderAnimationWeights } from '../www/proto3d/cinderflight.js';
import assert from 'node:assert/strict';
const s = createCinderFlight();
assert.equal(s.phase, 'ground');
assert.equal(s.alt, 0);
const ground = cinderAnimationWeights(s, 0); assert.equal(ground.idle, 1);
s.toggle(); for(let i=0;i<140;i++) s.step(1/60);
assert.equal(s.phase,'fly'); assert(s.alt >= 1.8 && s.alt < 10);
const flying=cinderAnimationWeights(s,4,1.4); assert(flying.glide>flying.flap && flying.flap>0);
const initial=s.alt;for(let i=0;i<50;i++)s.step(1/60,true);assert(s.alt>initial); const high=s.alt;
for(let i=0;i<50;i++)s.step(1/60,false,true);assert(s.alt<high);
s.toggle();for(let i=0;i<1000;i++)s.step(1/60);assert.equal(s.phase,'ground');assert.equal(s.alt,0);
s.toggle();s.step(1/60);s.reset();assert.equal(s.phase,'ground');assert.equal(s.alt,0);
for(const phase of ['ground','takeoff','fly','landing']) {const x=cinderAnimationWeights({phase,verticalSpeed:0},3,1);assert(Math.abs(Object.values(x).reduce((a,b)=>a+b,0)-1)<1e-6);}
console.log('Cinder flight physics and clip weights: PASS');
