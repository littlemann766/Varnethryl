/* One reusable, live 3D character-preview viewport inside the in-game roster.
 * Android-friendly: one WebGL context, one active GLB, no per-row canvases.
 * Does not change the player's avatar until Choose is pressed. */
export function createRosterPreview({ THREE, mount, status, load, release }) {
  let renderer, scene, camera, stage, actor, ticket = 0, frame = 0, running = false;
  let yaw = 0.28, pitch = 0.17, distance = 6, targetY = 1, last = 0;
  let dragging = false, px = 0, py = 0, lastWidth = 0, lastHeight = 0;
  const clamp = (x,a,b) => Math.max(a, Math.min(b,x));
  const say = message => { status.textContent = message; };
  function init() {
    if (renderer) return true;
    try {
      renderer = new THREE.WebGLRenderer({ antialias: false, alpha: true, powerPreference: 'low-power' });
      renderer.setPixelRatio(Math.min(1.25, window.devicePixelRatio || 1));
      renderer.outputColorSpace = THREE.SRGBColorSpace;
      renderer.shadowMap.enabled = false;
      renderer.domElement.setAttribute('aria-label','Rotatable 3D model');
      renderer.domElement.style.touchAction = 'none';
      mount.prepend(renderer.domElement);
      scene = new THREE.Scene();
      scene.background = new THREE.Color(0x101422);
      const ambient = new THREE.HemisphereLight(0xe6e8ff,0x26334d,2.1); scene.add(ambient);
      const key = new THREE.DirectionalLight(0xffdfb1,2.5); key.position.set(5,9,7); scene.add(key);
      const rim = new THREE.DirectionalLight(0x9766ef,2.4); rim.position.set(-6,4,-5); scene.add(rim);
      const pad = new THREE.Mesh(new THREE.CylinderGeometry(1,1.16,.12,48),
        new THREE.MeshStandardMaterial({color:0x322944,metalness:.47,roughness:.46}));
      pad.name='vn-roster-pedestal'; pad.position.y=-.07; scene.add(pad);
      const ring = new THREE.Mesh(new THREE.TorusGeometry(1.04,.025,6,56),
        new THREE.MeshBasicMaterial({color:0xc59a56})); ring.rotation.x=Math.PI/2; ring.position.y=.005; scene.add(ring);
      stage = new THREE.Group(); scene.add(stage);
      camera = new THREE.PerspectiveCamera(36,1,.01,10000);
      const canvas = renderer.domElement;
      canvas.addEventListener('pointerdown', e => { dragging=true; px=e.clientX; py=e.clientY; canvas.setPointerCapture?.(e.pointerId); e.stopPropagation(); });
      canvas.addEventListener('pointermove', e => { if (!dragging) return; yaw += (e.clientX-px)*.012; pitch=clamp(pitch+(e.clientY-py)*.005,-.25,.55); px=e.clientX; py=e.clientY; e.stopPropagation(); });
      const end=e=>{dragging=false; e.stopPropagation();};
      canvas.addEventListener('pointerup',end); canvas.addEventListener('pointercancel',end);
      canvas.addEventListener('wheel', e => { distance=clamp(distance*(e.deltaY>0?1.11:.90),.7,1000); e.preventDefault(); }, { passive:false });
      return true;
    } catch (err) { say('3D preview unavailable: '+(err?.message || err)); return false; }
  }
  function clear() {
    if (!actor) return;
    stage.remove(actor.group);
    release(actor.model);
    actor = null;
  }
  function size() {
    const w=Math.max(1,Math.floor(mount.clientWidth)),h=Math.max(1,Math.floor(mount.clientHeight));
    if(w!==lastWidth||h!==lastHeight){
      lastWidth=w;lastHeight=h;
      renderer.setSize(w,h,false); camera.aspect=w/h; camera.updateProjectionMatrix();
    }
  }
  function tick(now) {
    if (!running || !renderer) return;
    frame=requestAnimationFrame(tick);
    const dt=Math.min(.05,Math.max(0,(now-last)/1000||0)); last=now;
    if (!mount.isConnected||!mount.offsetWidth) return;
    size();
    if (actor?.model.userData?.mixer) {
      actor.model.userData.mixer.update(dt);
      // Boss preview must show the same full-body serpentine motion as gameplay.
      // Use a demonstration travel speed without moving the preview pedestal.
      // The approved Balthrix slither bones are fully animated by the authored clip.
      // Never rotate them a second time: it corkscrews the model.
    }
    if (!dragging) yaw += dt*.15;
    camera.position.set(Math.sin(yaw)*Math.cos(pitch)*distance,
      targetY+Math.sin(pitch)*distance, Math.cos(yaw)*Math.cos(pitch)*distance);
    camera.lookAt(0,targetY,0);
    renderer.render(scene,camera);
  }
  function open() {
    if (!init()) return false;
    if (!running) { running=true; last=0; frame=requestAnimationFrame(tick); }
    return true;
  }
  async function show(id,mode,name) {
    if (!open()) return false;
    const n=++ticket;
    clear(); say('Loading '+name+'…');
    try {
      const model=await load(id,mode);
      if(n!==ticket||!running) { if(model)release(model);return false; }
      if(!model)throw new Error('Model unavailable');
      // Stage never moves the live in-game avatar. Every preview owns its model.
      const group=new THREE.Group(); group.add(model); stage.add(group);
      model.updateMatrixWorld(true);
      let box=new THREE.Box3().setFromObject(model);
      const fallback=Math.max(1,model.userData.heightW||3);
      const sizeV=box.getSize(new THREE.Vector3());
      if(!Number.isFinite(sizeV.y)||sizeV.y<.01){
        box=new THREE.Box3(new THREE.Vector3(-fallback*.24,0,-fallback*.24),
          new THREE.Vector3(fallback*.24,fallback,fallback*.24));
        box.getSize(sizeV);
      }
      const center=box.getCenter(new THREE.Vector3());
      group.position.set(-center.x,-box.min.y,-center.z);
      const h=Math.max(.6,sizeV.y);
      const widest=Math.max(sizeV.x,sizeV.z,h*.5,1);
      targetY=h*.47;
      distance=Math.max(2.4, h*1.65, widest*2.25);
      yaw=.28;pitch=.10;
      actor={group,model};
      const actions=model.userData?.act || {};
      const idle=/vaelthryx/i.test(id)
        ? (actions.slither || actions.walk || actions.idle || actions.run)
        : (actions.idle || actions.walk || actions.run);
      if(idle){
        // Wren and Balthrix have multiple clips already started by wrapGLB.
        // Stop old idle weighting before showing the newly chosen 3D pose:
        // simultaneous idle + slither at full weight makes Balthrix look stiff.
        for(const other of new Set(Object.values(actions)))
          if(other && other!==idle && typeof other.setEffectiveWeight==='function')
            other.setEffectiveWeight(0);
        idle.reset();idle.setLoop(THREE.LoopRepeat);idle.play();
        idle.setEffectiveWeight(1);
        idle.timeScale=/vaelthryx/i.test(id)?0.78:(actions.idle===idle?1:.65);
      }
      say(name+' · drag to rotate · scroll to zoom');
      return true;
    } catch(e) { if(n===ticket) { console.warn('Varnethryl roster 3D model failed',id,e); say(name+' · 3D unavailable: '+String(e?.message || e).slice(0,130)); } return false; }
  }
  function hide() {
    ++ticket;running=false;cancelAnimationFrame(frame);dragging=false;clear();
    say('Select a character to preview');
  }
  return {show,open,hide,get active(){return running;}};
}
