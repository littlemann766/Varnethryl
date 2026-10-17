# Varnethryl RPG — v0.5.0

This is a **separate game project** from PayAviator. It includes the same 20 original hero portraits and sprite cutouts, the playable single-player prototype, quest and boss systems, equipment RNG, Mystic Forge, and local progress backups.

**Game rules:** regular equipment +0 to +15 (rarity every three upgrades); each substat can be upgraded up to +10, each class relic up to +10. The multiplayer tab is a preview only; actual networked multiplayer is NOT implemented.

**IMPORTANT PROGRESS WARNING:** Android app storage and website storage are separate. Saves do **not** automatically synchronize. Before moving between them or updating the app, use **Guild > Export JSON backup**, then import that backup into the other edition. Never uninstall the Android app before saving your backup. The internal `guildbound_rpg_save_v1` storage key is intentionally unchanged to preserve compatible existing saves.

**Offline:** Both versions bundle the gameplay artwork locally. The web edition caches assets after its first hosted HTTPS visit. Online multiplayer, cross-device save syncing and a production Play Store release still require additional development.

**Please don't confuse** the Android APK with the PWA home-screen installation. Both show a Varnethryl icon, but Android uses a native app package built via Capacitor; the web edition is served over HTTPS and can be installed from a browser.

## Both distributions from one repository

- **Web App:** GitHub **Actions > Publish Varnethryl Web App**, then open the HTTPS URL. The site is installable as a PWA.
- **Android App:** GitHub **Actions > Build Varnethryl Android APK**, then download the generated debug APK artifact.

Both builds use the **exact same `www/` folder**. The Android Capacitor bridge hides the PWA install prompt in native mode. See the separate Android and WebApp ZIPs for dedicated repos and detailed steps. The Android APK needs a GitHub Actions build; it is not precompiled inside this ZIP.


## GitHub repository setup (both versions)

This repository's workflow files MUST be at these exact paths on the `main` branch:

- `.github/workflows/build-android.yml` — produces a **debug** APK in Actions artifacts.
- `.github/workflows/deploy-pages.yml` — publishes the `www/` web app to GitHub Pages.

The directory starts with a dot (`.github`); make sure hidden folders are uploaded.
Do NOT upload the ZIP archive itself to GitHub: extract it, then upload the files and folders INSIDE `Varnethryl-main/` to the repository root.
The game assets remain in `www/`, next to `package.json` at the repository root.

To publish the website: open **Settings → Pages → Build and deployment → Source: GitHub Actions**, then open **Actions → Publish Varnethryl Web App**. The published site should appear under `https://littlemann766.github.io/Varnethryl/` after successful deployment, unless you configure a custom domain.

To install a test Android APK: open **Actions → Build Varnethryl Android APK**, run the workflow if necessary, then download the `Varnethryl-RPG-debug-APK` artifact. This is a debug build for testing, not a production-signed Play Store release.

If Actions instead says **Get started with GitHub Actions**, the `.github/workflows/` files are still missing or are in the wrong directory. If the workflows appear but don't run, check **Settings → Actions → General** for repository Actions settings.
