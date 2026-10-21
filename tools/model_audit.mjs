#!/usr/bin/env node
/**
 * Varnethryl model inventory: read GLB metadata without guessing rig readiness.
 * Usage: node tools/model_audit.mjs [--json] [--new] [--self-test]
 *
 * "Skinned" means glTF skin joints exist and a node references a skin.
 * "Animated" means clips contain animation channels.
 * Neither proves deformation quality, correct animation mapping, or in-game use.
 */
import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';
import assert from 'node:assert/strict';

const DIRS = ['models-new', 'models-beth', 'models', 'models-placeholder'];
const base = path.resolve('www/proto3d');

function parseGLB(buffer) {
  if (buffer.length < 20 || buffer.toString('ascii', 0, 4) !== 'glTF')
    throw new Error('not a GLB');
  if (buffer.readUInt32LE(4) !== 2) throw new Error('GLB version is not 2');
  const advertisedSize = buffer.readUInt32LE(8);
  if (advertisedSize !== buffer.length) throw new Error('incorrect GLB byte length');
  let off = 12, json = null;
  while (off + 8 <= buffer.length) {
    const size = buffer.readUInt32LE(off);
    const kind = buffer.readUInt32LE(off + 4);
    off += 8;
    if (off + size > buffer.length) throw new Error('truncated GLB chunk');
    if (kind === 0x4e4f534a && json === null)
      json = JSON.parse(buffer.subarray(off, off + size).toString('utf8').trim());
    off += size;
  }
  if (off !== buffer.length) throw new Error('trailing bytes');
  if (!json || !json.asset) throw new Error('missing glTF JSON metadata');
  return json;
}

function describe(doc, file) {
  const skins = doc.skins || [];
  const nodes = doc.nodes || [];
  const animations = doc.animations || [];
  const meshNodes = nodes.filter(n => Number.isInteger(n.mesh));
  const skinnedNodes = meshNodes.filter(n => Number.isInteger(n.skin));
  const bones = new Set(skins.flatMap(s => s.joints || []));
  const targets = new Set();
  const names = [];
  let channels = 0;
  for (const anim of animations) {
    names.push((anim.name || '(unnamed)').replace(/[\r\n|]/g, ' '));
    channels += (anim.channels || []).length;
    for (const ch of anim.channels || []) if (ch.target?.path) targets.add(ch.target.path);
  }
  const hasSkeleton = bones.size > 0 && skinnedNodes.length > 0;
  const hasAnimation = channels > 0;
  const flags = [];
  if (!meshNodes.length) flags.push('no_mesh_nodes');
  if (!hasSkeleton) flags.push('no_bound_skeleton');
  if (!hasAnimation) flags.push('no_animation_channels');
  if (hasAnimation && !hasSkeleton && !targets.has('weights')) flags.push('rigid_or_node_animation');
  return {
    file, bytes: fs.statSync(file).size,
    meshNodes: meshNodes.length, skinCount: skins.length,
    skinnedNodes: skinnedNodes.length, jointCount: bones.size,
    animationCount: animations.length, channels,
    animationTargets: [...targets].sort(), clipNames: names,
    hasSkeleton, hasAnimation, flags
  };
}

function inventory(onlyNew = false) {
  const rows = [];
  for (const dir of (onlyNew ? DIRS.slice(0, 1) : DIRS)) {
    const folder = path.join(base, dir);
    if (!fs.existsSync(folder)) continue;
    for (const name of fs.readdirSync(folder).sort()) {
      if (!name.toLowerCase().endsWith('.glb')) continue;
      const file = path.join(folder, name);
      const relative = path.relative(process.cwd(), file).replace(/\\/g, '/');
      try {
        const meta = describe(parseGLB(fs.readFileSync(file)), file);
        meta.file = relative;
        rows.push(meta);
      } catch (e) {
        rows.push({file:relative, error:String(e.message || e), flags:['invalid_glb']});
      }
    }
  }
  return rows;
}

function checkFixtures() {
  const data = {
    asset:{version:'2.0'}, meshes:[{primitives:[{attributes:{POSITION:0}}]}],
    nodes:[{mesh:0,skin:0},{name:'Root Bone'}],
    skins:[{joints:[1]}], animations:[{name:'Walking',channels:[{target:{node:1,path:'rotation'}}]}]
  };
  const json = Buffer.from(JSON.stringify(data));
  const pad = Buffer.alloc((4 - json.length % 4) % 4, 32);
  const body = Buffer.concat([json,pad]), glb = Buffer.alloc(20 + body.length);
  glb.write('glTF',0,'ascii');glb.writeUInt32LE(2,4);glb.writeUInt32LE(glb.length,8);
  glb.writeUInt32LE(body.length,12);glb.writeUInt32LE(0x4e4f534a,16);body.copy(glb,20);
  const doc = parseGLB(glb);
  const meta = describeFromFixture(doc);
  assert.equal(meta.hasSkeleton, true);
  assert.equal(meta.hasAnimation, true);
  assert.equal(meta.jointCount, 1);
  assert.deepEqual(meta.clipNames, ['Walking']);
  assert.throws(() => parseGLB(Buffer.from('wrong')), /not a GLB/);
  const noRig = describeFromFixture({asset:{version:'2.0'},nodes:[{mesh:0}],meshes:[{}]});
  assert.equal(noRig.hasSkeleton,false);
  assert.equal(noRig.hasAnimation,false);
  console.log('PASS: GLB header, skeleton and animation metadata classification');
}
function describeFromFixture(doc) {
  // Fixture helper: describe normally uses stat for real repository files.
  const fake = path.join(base,'models','__fixture.glb');
  const original = fs.statSync;
  try { fs.statSync = () => ({size:1});return describe(doc,fake); }
  finally { fs.statSync = original; }
}

function table(rows) {
  const total = rows.length, invalid = rows.filter(x=>x.error).length;
  const skinned = rows.filter(x=>x.hasSkeleton).length;
  const animated = rows.filter(x=>x.hasAnimation).length;
  const both = rows.filter(x=>x.hasSkeleton && x.hasAnimation).length;
  const lines = [
    '# Varnethryl GLB asset audit',
    '',
    'Metadata only: skeletons and animation channels are **not** proof of good motion, approved appearance, working AI, or gameplay integration.',
    '',
    'Assets: ' + total + ' | valid: ' + (total-invalid) + ' | bound skeleton: ' + skinned + ' | animated: ' + animated + ' | both: ' + both,
    '',
    '| Model asset | Joints | Skinned meshes | Animation clips | Clip names | Flags |',
    '| --- | ---: | ---: | ---: | --- | --- |'
  ];
  for (const r of rows) {
    const clips = (r.clipNames||[]).join(', ').replace(/\|/g,'/').slice(0,150);
    lines.push('| ' + r.file.replace('www/proto3d/','') + ' | ' + (r.jointCount ?? '—') + ' | ' + (r.skinnedNodes ?? '—') + ' | ' + (r.animationCount ?? '—') + ' | ' + clips + ' | ' + (r.error || (r.flags||[]).join(', ') || 'metadata OK') + ' |');
  }
  lines.push('', 'Next checks requiring game runtime: skin deformation, foot sliding, attack/death clips, scale, collision, approved appearance, spawn/AI and animation transitions.', '');
  return lines.join('\n');
}

if (process.argv.includes('--self-test')) {
  checkFixtures();
} else {
  const rows = inventory(process.argv.includes('--new'));
  if (!rows.length) {
    console.error('No GLB files found; run from the repository root.');
    process.exitCode = 1;
  } else {
    process.stdout.write(process.argv.includes('--json') ? JSON.stringify(rows,null,2) + '\n' : table(rows));
    if (rows.some(r=>r.error)) process.exitCode = 2;
  }
}
