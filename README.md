# Varnethryl RPG — v0.3.1

This is a **separate game project** from PayAviator. It includes the same 20 original hero portraits and sprite cutouts, the playable single-player prototype, quest and boss systems, equipment RNG, Mystic Forge, and local progress backups.

**Game rules:** regular equipment +0 to +15 (rarity every three upgrades); each substat can be upgraded up to +10, each class relic up to +10. The multiplayer tab is a preview only; actual networked multiplayer is NOT implemented.

**IMPORTANT PROGRESS WARNING:** Android app storage and website storage are separate. Saves do **not** automatically synchronize. Before moving between them or updating the app, use **Guild > Export JSON backup**, then import that backup into the other edition. Never uninstall the Android app before saving your backup. The internal `guildbound_rpg_save_v1` storage key is intentionally unchanged to preserve compatible existing saves.

**Offline:** Both versions bundle the gameplay artwork locally. The web edition caches assets after its first hosted HTTPS visit. Online multiplayer, cross-device save syncing and a production Play Store release still require additional development.

**Please don't confuse** the Android APK with the PWA home-screen installation. Both show a Varnethryl icon, but Android uses a native app package built via Capacitor; the web edition is served over HTTPS and can be installed from a browser.

## Both distributions from one repository

- **Web App:** GitHub **Actions > Publish Varnethryl Web App**, then open the HTTPS URL. The site is installable as a PWA.
- **Android App:** GitHub **Actions > Build Varnethryl Android APK**, then download the generated debug APK artifact.

Both builds use the **exact same `www/` folder**. The Android Capacitor bridge hides the PWA install prompt in native mode. See the separate Android and WebApp ZIPs for dedicated repos and detailed steps. The Android APK needs a GitHub Actions build; it is not precompiled inside this ZIP.
