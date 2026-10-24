/* Climbable ladders: keyboard/joystick movement only, no prompt/button.
   Walk into a ladder to grab it; hold toward the top to ascend, hold back
   to descend, release to pause. Works on perimeter walls and every building.
   The ladder links existing floor levels without adding new floating floors. */
export function ladderAxis(L) {
  const dx=L.topX-L.baseX,dz=L.topZ-L.baseZ,dist=Math.hypot(dx,dz)||1;
  return {x:dx/dist,z:dz/dist};
}
export function ladderIntent(L,vx,vz) {
  const axis=ladderAxis(L),mag=Math.hypot(vx,vz);
  return mag>.1 ? (vx*axis.x+vz*axis.z)/mag : 0;
}
export function createLadders(env) {
  const { THREE, scene, colliders, state, keys } = env, HS = env.HS;
  const mat = (c, r = 0.9) => new THREE.MeshStandardMaterial({ color: c, roughness: r });
  const wood = mat(0x8a5a2b), dark = mat(0x5a3a1c), plank = mat(0xa8793f), roof = mat(0x7a2e22), rope = mat(0xcfc09a);
  const list = [], SPEED = 2.4;
  let climb = null, hold = 0, near = null;
  // Legacy caller still hides this control when changing zones, but no
  // button is created or attached to the DOM. Climbing is fully hands-free.
  const btn={style:{display:'none'}};
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
    const L={baseLevel:0,y0:0,y1:def.H,...def,wall:true},g=new THREE.Group();
    g.position.set(L.rungX,L.y0,L.rungZ);g.rotation.y=Math.atan2(L.nx,L.nz);
    const H=L.y1-L.y0;
    // Three instanced batches replace dozens of separate draw calls per ladder.
    const cube=new THREE.BoxGeometry(1,1,1),dummy=new THREE.Object3D();
    const batch=(material,parts,name)=>{
      const mesh=new THREE.InstancedMesh(cube,material,parts.length);
      mesh.name=name;mesh.castShadow=true;
      for(let i=0;i<parts.length;i++){
        const [x,y,z,w,h,d]=parts[i];
        dummy.position.set(x,y,z);dummy.scale.set(w,h,d);dummy.updateMatrix();
        mesh.setMatrixAt(i,dummy.matrix);
      }
      g.add(mesh);
    };
    batch(wood,[[-.35,H/2,0,.085,H+.9,.085],[.35,H/2,0,.085,H+.9,.085]],'ladder-rails');
    const rungs=[];for(let y=.3;y<H+.78;y+=.34)rungs.push([0,y,0,.78,.065,.09]);
    batch(rope,rungs,'ladder-rungs');
    batch(dark,[[0,.7,-.2,.82,.095,.3],[0,H-.2,-.2,.82,.095,.3]],'ladder-anchors');
    scene.add(g);L.group=g;list.push(L);return L;
  }
  function addBuilding(def){return addWall(def);}
  const surface = (x, z, level) => { for (const L of list) if (!L.wall && L.level === level && Math.abs(x - L.x) <= L.half + 0.1 && Math.abs(z - L.z) <= L.half + 0.1) return { y: L.H, ladder: L }; return null; };
  const heightOf = level => { for (const L of list) if (L.level === level) return L.H; return 0; };
  function start(L, dir) {
    if (climb) return; const up = dir > 0;
    climb = { L, dir, y: up ? (L.y0??0) : (L.y1??L.H), x: L.wall ? L.rungX : L.x, z: L.wall ? L.rungZ : L.z + L.half + .65 }; state.climbing = true; state.target = null;
    if(L.wall){
      state.heroX=up?L.baseX:L.topX;state.heroZ=up?L.baseZ:L.topZ;
      if(!up)state.level=L.level;
    }else{
      state.heroX=climb.x;state.heroZ=L.z+L.half+1.1;
      if(!up){state.heroX=L.x;state.heroZ=L.topZ;state.level=L.level;}
    }
  }
  /* once per frame, before the normal movement. vx,vz = input direction (world). Returns true while the hero is on the ladder. */
  function update(dt,vx,vz) {
    if(climb){
      const L=climb.L,delta=ladderIntent(L,vx,vz);
      // Hold the joystick/keyboard toward either end. Neutral input pauses
      // at the current rung; reversing moves back down the SAME ladder.
      if(Math.abs(delta)>.22)climb.y+=Math.sign(delta)*SPEED*dt;
      const lo=L.y0??0,hi=L.y1??L.H;
      climb.y=Math.max(lo,Math.min(hi,climb.y));
      const t=Math.max(0,Math.min(1,(climb.y-lo)/(hi-lo||1)));
      if(L.wall){
        // Horizontal entry and exit blend into a vertical climb up the rails.
        // Never slide diagonally through a building or masonry wall.
        const inT=Math.min(1,t/.14),outT=Math.max(0,Math.min(1,(t-.86)/.14));
        state.heroX=L.baseX+(L.rungX-L.baseX)*inT+(L.topX-L.rungX)*outT;
        state.heroZ=L.baseZ+(L.rungZ-L.baseZ)*inT+(L.topZ-L.rungZ)*outT;
        state.yaw=Math.atan2(-L.nx,-L.nz);
      }else{
        // Original independent lookout ladders also follow movement input.
        state.heroX=L.baseX+(L.topX-L.baseX)*t;
        state.heroZ=L.baseZ+(L.topZ-L.baseZ)*t;
        state.yaw=Math.PI;
      }
      state.heroY=climb.y;state.dispY=climb.y;
      state.speed=Math.abs(delta)>.22?SPEED:0;
      if((t>=1 && delta>.22)||(t<=0 && delta<-.22)){
        state.climbing=false;climb=null;
        state.level=t>=1?L.level:(L.baseLevel??0);
        state.heroX=t>=1?L.topX:L.baseX;
        state.heroZ=t>=1?L.topZ:L.baseZ;
        state.speed=0;hold=0;near=null;
      }
      return true;
    }
    // Prefer a valid aligned ladder, rather than grabbing an unrelated
    // ladder at the same height or an adjacent building's upper floor.
    let best=null,score=-Infinity;
    for(const L of list){
      const up=state.level===(L.baseLevel??0);
      if(!up&&state.level!==L.level)continue;
      const px=up?L.baseX:L.topX,pz=up?L.baseZ:L.topZ;
      const d=Math.hypot(state.heroX-px,state.heroZ-pz);
      const limit=L.wall?2.15:1.6;
      if(d>limit)continue;
      const intent=ladderIntent(L,vx,vz)*(up?1:-1);
      if(intent<.55)continue;
      const candidate=intent-d*.1;
      if(candidate>score){score=candidate;best={L,dir:up?1:-1};}
    }
    near=best;
    if(best){
      // ~one movement frame of deliberate approach avoids an involuntary
      // grab when someone merely brushes past the rails.
      hold+=dt;
      if(hold>=.08){start(best.L,best.dir);hold=0;return true;}
    }else hold=0;
    return false;
  }
  return { list, add, addWall, addBuilding, surface, heightOf, update, get climbing() { return !!climb; }, btn };
}
