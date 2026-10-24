/* Climbable ladders (1.1.8): small wooden towers/lofts you climb with a ladder instead of stairs.
   Each structure has its own level number (10+i) with a platform surface at height H. Walk into the ladder (keyboard / joystick), or press E / the Climb button
   when close, to climb up; do the same at the top edge to climb down. Vertical movement + walk animation. Followers use the hero's breadcrumb trail (see main.js). */
export function createLadders(env) {
  const { THREE, scene, colliders, state, keys } = env, HS = env.HS;
  const mat = (c, r = 0.9) => new THREE.MeshStandardMaterial({ color: c, roughness: r });
  const wood = mat(0x8a5a2b), dark = mat(0x5a3a1c), plank = mat(0xa8793f), roof = mat(0x7a2e22), rope = mat(0xcfc09a);
  const list = [], SPEED = 2.4;
  let climb = null, hold = 0, ePrev = false, near = null;
  const btn = document.createElement('button'); btn.id = 'climbBtn'; btn.type = 'button'; btn.textContent = 'Climb';
  btn.style.cssText = 'position:fixed;right:max(14px,env(safe-area-inset-right));bottom:max(250px,calc(env(safe-area-inset-bottom) + 244px));z-index:45;display:none;min-width:76px;height:44px;border-radius:22px;border:2px solid #ffe9a8;background:#6a3d12e6;color:#fff;font:700 14px system-ui;touch-action:none';
  document.body.appendChild(btn); btn.addEventListener('pointerdown', e => { e.preventDefault(); e.stopPropagation(); if (near) start(near.L, near.dir); });
  function box(g, w, h, d, m, x, y, z) { const o = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), m); o.position.set(x, y, z); o.castShadow = true; g.add(o); return o; }
  /* def: {id, x, z, half, H, roof} ladder on the +z face. */
  function add(def) {
    const L = Object.assign({ level: 10 + list.length, half: 1.8, H: 4.6, roofed: true }, def), g = new THREE.Group(), h = L.half, H = L.H, lv0 = [0], lvL = [L.level];
    g.position.set(L.x, 0, L.z);
    for (const sx of [-1, 1]) for (const sz of [-1, 1]) { box(g, 0.28, H, 0.28, wood, sx * (h - 0.15), H / 2, sz * (h - 0.15)); colliders.push({ type: 'circle', x: L.x + sx * (h - 0.15), z: L.z + sz * (h - 0.15), r: 0.3, lv: lv0 }); }
    for (const sx of [-1, 1]) box(g, 0.1, H * 0.5, 0.1, dark, sx * h * 0.5, H * 0.25, 0), 0;
    box(g, 2 * h + 0.3, 0.22, 2 * h + 0.3, plank, 0, H, 0);                       // platform
    // rails: back + both sides full, front with a 1.1 m gap at the ladder
    box(g, 2 * h, 0.9, 0.08, dark, 0, H + 0.55, -h + 0.04); box(g, 0.08, 0.9, 2 * h, dark, -h + 0.04, H + 0.55, 0); box(g, 0.08, 0.9, 2 * h, dark, h - 0.04, H + 0.55, 0);
    const seg = h - 0.55; for (const sx of [-1, 1]) box(g, seg, 0.9, 0.08, dark, sx * (0.55 + seg / 2), H + 0.55, h - 0.04);
    const C = (x0, x1, z0, z1) => colliders.push({ type: 'box', minX: L.x + x0, maxX: L.x + x1, minZ: L.z + z0, maxZ: L.z + z1, lv: lvL });
    C(-h, h, -h, -h + 0.14); C(-h, -h + 0.14, -h, h); C(h - 0.14, h, -h, h); C(-h, -0.55, h - 0.14, h); C(0.55, h, h - 0.14, h);
    if (L.roofed) { for (const sx of [-1, 1]) for (const sz of [-1, 1]) box(g, 0.12, 1.9, 0.12, wood, sx * (h - 0.1), H + 1.05, sz * (h - 0.1)); const r = new THREE.Mesh(new THREE.ConeGeometry(h * 1.55, 1.2, 4), roof); r.rotation.y = Math.PI / 4; r.position.y = H + 2.5; r.castShadow = true; g.add(r); }
    // ladder on the +z face: two rails + rungs, reaches 0.9 m above the platform
    const lz = h + 0.1, top = H + 0.9; for (const sx of [-0.28, 0.28]) box(g, 0.07, top, 0.07, wood, sx, top / 2, lz);
    for (let y = 0.3; y < top - 0.1; y += 0.32) box(g, 0.56, 0.05, 0.06, rope, 0, y, lz);
    colliders.push({ type: 'box', minX: L.x - 0.45, maxX: L.x + 0.45, minZ: L.z + h - 0.05, maxZ: L.z + lz + 0.12, lv: lv0 });   // ladder foot blocks walking through; the trigger stands in front of it
    L.baseX = L.x; L.baseZ = L.z + lz + 0.95;      // where the hero stands to climb (ground)
    L.topX = L.x; L.topZ = L.z + h - 0.45;         // where the hero stands on the platform
    scene.add(g); L.group = g; list.push(L); return L;
  }
  // Perimeter ladders connect the actual wall-walk surface (level 1) to
  // ground without any new platform or floor collision over the masonry.
  function addWall(def){
    const L={...def,wall:true},g=new THREE.Group();
    g.position.set(L.rungX,0,L.rungZ);g.rotation.y=Math.atan2(L.nx,L.nz);
    const H=L.H;
    for(const side of [-1,1])box(g,.085,H+.9,.085,wood,side*.35,(H+.9)/2,0);
    for(let y=.3;y<H+.78;y+=.34)box(g,.78,.065,.09,rope,0,y,0);
    for(const y of [.7,H-.2])box(g,.82,.095,.3,dark,0,y,-.2);
    scene.add(g);L.group=g;list.push(L);return L;
  }
  const surface = (x, z, level) => { for (const L of list) if (!L.wall && L.level === level && Math.abs(x - L.x) <= L.half + 0.1 && Math.abs(z - L.z) <= L.half + 0.1) return { y: L.H, ladder: L }; return null; };
  const heightOf = level => { for (const L of list) if (L.level === level) return L.H; return 0; };
  function start(L, dir) {
    if (climb) return; const up = dir > 0;
    climb = { L, dir, y: up ? 0 : L.H, x: L.wall ? L.rungX : L.x, z: L.wall ? L.rungZ : L.z + L.half + .65 }; state.climbing = true; state.target = null;
    if(L.wall){
      state.heroX=up?L.baseX:L.topX;state.heroZ=up?L.baseZ:L.topZ;
      if(!up)state.level=L.level;
    }else{
      state.heroX=climb.x;state.heroZ=L.z+L.half+1.1;
      if(!up){state.heroX=L.x;state.heroZ=L.topZ;state.level=L.level;}
    }
  }
  /* once per frame, before the normal movement. vx,vz = input direction (world). Returns true while the hero is on the ladder. */
  function update(dt, vx, vz) {
    const e = keys.has('e'), ePress = e && !ePrev; ePrev = e;
    if (climb) {
      const L = climb.L, up = climb.dir > 0; climb.y += climb.dir * SPEED * dt;
      if(L.wall){
        const progress=Math.max(0,Math.min(1,climb.y/L.H));
        state.heroX=L.baseX+(L.topX-L.baseX)*progress;
        state.heroZ=L.baseZ+(L.topZ-L.baseZ)*progress;
        state.yaw=Math.atan2(-L.nx,-L.nz);
      }else{state.heroX=L.x;state.heroZ=L.z+L.half+.55;state.yaw=Math.PI;}
      state.heroY=Math.max(0,Math.min(L.H,climb.y));state.speed=2.5;state.dispY=state.heroY;
      if ((up && climb.y >= L.H) || (!up && climb.y <= 0)) { state.climbing = false; climb = null; state.level = up ? L.level : 0; state.heroX = up ? L.topX : L.baseX; state.heroZ = up ? L.topZ : L.baseZ; state.heroY = up ? L.H : 0; state.speed = 0; hold = -0.7; btn.style.display = 'none'; near = null; }
      return !!climb;
    }
    // proximity: ground level -> up, on a ladder platform -> down
    let best = null;
    for (const L of list) {
      if (state.level === 0) { const d = Math.hypot(state.heroX - L.baseX, state.heroZ - L.baseZ); if (d < (L.wall?2.7:2.0)) { best = { L, dir: 1, d, ax: L.wall?-L.nx:0, az: L.wall?-L.nz:-1 }; break; } }
      else if (state.level === L.level) { const d = Math.hypot(state.heroX - L.topX, state.heroZ - L.topZ); if (d < (L.wall?2.1:1.6)) { best = { L, dir: -1, d, ax: L.wall?L.nx:0, az: L.wall?L.nz:1 }; break; } }
    }
    near = best; const sh = best ? 'block' : 'none'; if (btn.style.display !== sh) { btn.style.display = sh; if (best) btn.textContent = best.dir > 0 ? 'Climb \u25B2' : 'Down \u25BC'; }
    if (best) {
      const mag = Math.hypot(vx, vz), into = mag > 0.1 && (vx * best.ax + vz * best.az) / mag > 0.45 && best.d < 1.5;
      hold = into ? hold + dt : 0;
      if (hold > 0.18 || (ePress && best.d < 2.0)) { start(best.L, best.dir); hold = 0; }
    } else hold = 0;
    return false;
  }
  return { list, add, addWall, surface, heightOf, update, get climbing() { return !!climb; }, btn };
}
