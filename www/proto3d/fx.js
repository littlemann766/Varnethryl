// Shared living-world shader FX (wind sway, flags, water, flicker). No imports so any module can use it.
// kinds: 'flag' (cloth waves, pinned at the top uv.y=1), 'water' (scrolling flow + glints), 'flicker' (warm torch glow), 'tree' / 'grass' / 'wild' (wind sway by world height).
export const FX = { uTime: { value: 0 }, uWind: { value: 1 } };
{ const t0 = typeof performance !== 'undefined' ? performance.now() : 0; const loop = () => { FX.uTime.value = (performance.now() - t0) / 1000; requestAnimationFrame(loop); }; if (typeof requestAnimationFrame !== 'undefined') requestAnimationFrame(loop); }
const SWAY = 'vec4 fxo = vec4(0.0); \n#ifdef USE_INSTANCING\n fxo = instanceMatrix * vec4(0.0, 0.0, 0.0, 1.0);\n#else\n fxo = vec4(position, 1.0);\n#endif\n vec3 fxOrg = (modelMatrix * vec4(fxo.xyz, 1.0)).xyz; float fxG = sin(fxOrg.x * 0.11 + fxOrg.z * 0.07 + uTime * 0.9) * 0.5 + 0.5; float fxF = sin(uTime * 2.6 + fxOrg.x * 1.7 + fxOrg.z * 1.3) * 0.5 + sin(uTime * 4.1 + fxOrg.z * 2.3) * 0.25;';
export function fx(mat, kind) {
  if (mat.userData.fx) return mat; mat.userData.fx = kind; mat.userData.noVC = true;
  mat.onBeforeCompile = sh => {
    sh.uniforms.uTime = FX.uTime; sh.uniforms.uWind = FX.uWind; let v = sh.vertexShader, f = sh.fragmentShader;
    v = 'uniform float uTime; uniform float uWind;\n' + (kind === 'flicker' ? 'varying float vFl;\n' : '') + v; f = 'uniform float uTime;\n' + (kind === 'flicker' ? 'varying float vFl;\n' : '') + f;
    if (kind === 'flag') v = v.replace('#include <begin_vertex>', `#include <begin_vertex>
      { vec3 wp = (modelMatrix * vec4(position, 1.0)).xyz; float hang = 1.0 - uv.y; float ph = (wp.x + wp.z) * 1.1 + uTime * 3.2 - hang * 2.4; float gust = 0.6 + 0.4 * sin(uTime * 0.7 + wp.x * 0.3);
        float a = (sin(ph) * 0.55 + sin(ph * 1.9 + 1.3) * 0.25) * gust * hang * 0.30 * uWind; transformed += normal * a; transformed.y -= abs(a) * 0.10; transformed.x += cos(ph) * 0.04 * hang * uWind; }`);
    if (kind === 'water') { v = v.replace('#include <uv_vertex>', '#include <uv_vertex>\n#ifdef USE_MAP\n vMapUv += vec2(uTime * 0.020 + sin(uTime * 0.35) * 0.05, uTime * 0.014);\n#endif');
      v = v.replace('#include <begin_vertex>', '#include <begin_vertex>\n { vec3 wp = (modelMatrix * vec4(position, 1.0)).xyz; transformed.y += (sin(wp.x * 1.3 + uTime * 1.5) + sin(wp.z * 1.7 + uTime * 1.2)) * 0.012; }');
      f = f.replace('#include <map_fragment>', `#include <map_fragment>
      #ifdef USE_MAP
      { vec4 s2 = texture2D(map, vMapUv * 1.7 + vec2(-uTime * 0.03, uTime * 0.022)); diffuseColor.rgb = mix(diffuseColor.rgb, diffuseColor.rgb * s2.rgb * 1.7, 0.5);
        float gl = sin(vMapUv.x * 41.0 + uTime * 2.1) * sin(vMapUv.y * 37.0 - uTime * 1.7) * (0.5 + 0.5 * sin(vMapUv.x * 7.0 + vMapUv.y * 5.0 + uTime * 0.6)); diffuseColor.rgb += smoothstep(0.55, 0.9, gl) * 0.26; }
      #endif`); }
    if (kind === 'flicker') { v = v.replace('#include <begin_vertex>', '#include <begin_vertex>\n { vec3 wp = (modelMatrix * vec4(position, 1.0)).xyz; float q = wp.x * 3.1 + wp.z * 1.7; vFl = 1.0 + 0.16 * sin(uTime * 9.0 + q) + 0.10 * sin(uTime * 17.0 + q * 2.3) + 0.06 * sin(uTime * 31.0 + q); }');
      f = f.replace('#include <emissivemap_fragment>', '#include <emissivemap_fragment>\n totalEmissiveRadiance *= vFl; diffuseColor.rgb *= 0.9 + 0.1 * vFl;'); }
    if (kind === 'tree' || kind === 'grass' || kind === 'wild') { const H = kind === 'tree' ? '0.085' : kind === 'wild' ? '0.2' : '0.9', A = kind === 'tree' ? '0.34' : kind === 'wild' ? '0.42' : '0.20';
      v = v.replace('#include <project_vertex>', `vec4 mvPosition = vec4( transformed, 1.0 );
      #ifdef USE_INSTANCING
        mvPosition = instanceMatrix * mvPosition;
      #endif
      vec4 fxw = modelMatrix * mvPosition; ${SWAY} float fxH = clamp(fxw.y * ${H}, 0.0, 1.0); fxH *= fxH;
      fxw.xz += vec2(1.0, 0.45) * ((fxG * 0.65 + 0.15) + fxF * 0.12) * fxH * ${A} * uWind; fxw.y -= fxH * (fxG * 0.05) * uWind;
      mvPosition = viewMatrix * fxw; gl_Position = projectionMatrix * mvPosition;`); }
    sh.vertexShader = v; sh.fragmentShader = f; };
  mat.customProgramCacheKey = () => 'fx_' + kind; return mat;
}
