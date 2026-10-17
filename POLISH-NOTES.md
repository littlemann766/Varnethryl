# VARNETHRYL polish-1 notes

Branch `polish-1` (local only, nothing pushed, `.github/` untouched). Tested headless Chromium 390x844 @2x, plus a bot playing the Wilds for 60s before/after.

## Findings (prioritized)
1. **Party strip rebuilt every 400ms** (innerHTML) – re-created buttons/images mid-tap, so taps on portraits could be lost and images flickered. FIXED (in-place updates).
2. **No healing anywhere** – HP only dropped; village didn't heal; after a death only the fallen hero was restored. Bot died 2x/min. FIXED.
3. **Combat info far below the game** (target HP and skill cooldown needed scrolling). FIXED with an on-canvas target bar and cooldown on the Skill button.
4. **Enemies were tiny anonymous blobs**, no names, no hit feedback. FIXED (bigger, eyes, name + HP bar, white hit flash, dashed target ring).
5. **Tap targets <44px** (d-pad 40x36, Strike/Skill 40, zone buttons 40, Install 28, Quest 35, dropdown 39). FIXED – audit now reports 0 sub-44px controls on Home.
6. Level-1 Wilds too punishing (5 enemies, 54-86 dmg vs ~440 HP); Ashen Ruins jump too steep (8.4K HP / 340 dmg). Retuned.
7. Header cramped on phones (Online pill, version subtitle). Trimmed.
8. Desktop-only hint text ("WASD", "SPACE") shown on phones. Now touch text on coarse pointers.
9. Combat spam toasts, 300ms-ish tap latency risk. Added `touch-action:manipulation`; Attack/Skill fire on `pointerdown` with a tiny vibration.

## Changed
- **Smoothness:** pointerdown for action buttons, no tap delay, press scale/brightness feedback, eased screen fade-in, eased damage numbers (pop + ease-out rise, outlined text), HP bar width easing, toast slide, `prefers-reduced-motion` respected, layout no longer jumps from rebuilt party DOM.
- **Loop/balance:** out-of-combat regen (1.2%/s in the field, 25%/s in village); whole party healed on defeat; Wilds enemy attack ~-22%; Ruins HP/attack ~-33%/-20%; hits animate.
- **Content (small):** new zone **Frostbite Pass** between Ashen Ruins and Titan Vault (Frost Hound, Ice Wraith, Glacier Brute; icy tiles; unlocks warning below account level 3). Travel buttons and portals update automatically.
- Standalone `PLAY-VARNETHRYL.html` rebuilt; `tools/check_assets.py` passes. Service-worker cache renamed to `varnethryl-pwa-0.3.2` so installed PWAs refresh. The visible version label is now v0.3.2.
- `window.__vn` test hook removed in 0.3.2.

## Save data changes
None. Same key `guildbound_rpg_save_v1`, same `version:1` format, no new fields. (Zone id `frost` can now appear in `state.zone`; older builds loading such a save would fail `ZONES.find` – Lucian's sync should keep builds in step, or we clamp unknown zones to village.)

## Not done / bigger ideas for the boss to pick
- Quest chain for Frostbite Pass and a real mini-boss with its own mechanics; a Frost Warden before the Titan.
- Boss telegraphs (ground warnings), dodge/roll button, hero-specific skill animations and sounds/haptics.
- Quest/XP pacing: level 7 in about a minute is fast; later content needs a slower curve.
- Zone ideas: Sunken Crypt (necromancer boss), Ember Caverns (fire, burn immunity), daily dungeon.
- Equipment armor/charm icons are emoji placeholders; drop notifications; inventory sort/compare; gear auto-equip suggestions.
- Real directional sprite sheets; sound; onboarding tutorial (first 3 minutes); mobile-first layout where the HUD floats and tabs are a drawer.
- Not verified on a real phone or at 60fps on-device; only headless desktop Chromium.
