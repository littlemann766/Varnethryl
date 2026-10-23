/* Offline safety checks for the v1.5.29 multiplayer, ocean and Coliseum pass.
 * Run without accounts, a server, Android SDK or GLB downloads.
 */
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {remoteFacing,nextRemoteYaw} from '../www/proto3d/multiplayer-client.js';
import {isColiseumCombat,coliseumHeight} from '../www/proto3d/coliseum-pvp.js';
const src=path=>readFileSync(new URL('../'+path,import.meta.url),'utf8');

// Remote headings must remain stable at rest and wrap across 2π smoothly.
assert.equal(remoteFacing(1,1,0,0,false),1);
assert.equal(remoteFacing(1,-.8,0.7,0,true),-.8);
assert.ok(Math.abs(remoteFacing(0,0,.5,0,true)-Math.PI/2)<1e-6);
const wrapped=nextRemoteYaw(3.13,-3.13,.025);
assert.ok(wrapped>3.13 && wrapped<3.17,'turn crosses +/-π by the short arc');
assert.equal(nextRemoteYaw(1,1,1/60),1);

// PvP ground floor: spectators and the upper access ramp are noncombat.
assert.equal(isColiseumCombat(0,0),true);
assert.equal(isColiseumCombat(58.9,0),true);
assert.equal(isColiseumCombat(60,0),false);
assert.equal(isColiseumCombat(105,0),false);
assert.equal(coliseumHeight(0,0),0);
assert.ok(Math.abs(coliseumHeight(95,0)-18.2)<1e-6);
assert.equal(coliseumHeight(145,0),0);

const client=src('www/proto3d/multiplayer-client.js');
assert.match(client,/async function recoverFailedJump\(/,'failed teleport restores previous room');
assert.match(client,/await recoverFailedJump\(before,seq\)/,'teleport recovery used');
assert.doesNotMatch(client,/new THREE\.Vector3\(p\.x,p\.y,p\.z\)/,'avoid allocation per remote avatar per frame');
const relay=src('multiplayer/server.mjs');
assert.match(relay,/if\(!target\)\{send\(socket,\{type:isCoOwner\?'coowner-error':'owner-error'/,'CoOwner receives private rank error');
assert.match(relay,/if\(!next\|\|next\.size>=MAX_PLAYERS\)\{send\(socket,\{type:isCoOwner\?'coowner-error':'owner-error'/,'CoOwner full-world error');
const chat=src('www/proto3d/multiplayer-chat.js');
assert.match(chat,/firstDelivery\(m\.id\)/,'server messages deduplicated');
assert.match(chat,/if\(root\.hidden\)trigger\?\.classList\.add\('vn-chat-unread'\)/,'world chat unread indicator');
const ocean=src('www/proto3d/water-realms.js');
assert.match(ocean,/if\(c\)\{/,'water rendering survives missing Canvas2D');
assert.match(ocean,/water\.tex\?\.offset\.set/,'water texture animation is null-safe');
assert.match(ocean,/const assembled=buildSailingShip\(1,true\)/,'approved existing ship fallback preserved');
const arena=src('www/proto3d/coliseum-pvp.js');
assert.match(arena,/new THREE\.InstancedMesh\(new THREE\.ConeGeometry/,'spectator torches are instanced');
console.log('Multiplayer, chat, ocean and Coliseum regression checks passed.');
