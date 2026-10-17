/* Varnethryl install / offline / update helper. No analytics, accounts or external services. */
(() => {
  const install = document.getElementById('installAppBtn');
  const update = document.getElementById('updateAppBtn');
  const status = document.getElementById('offlineStatus');
  const dialog = document.getElementById('pwaHelp');
  const instructions = document.getElementById('pwaInstructions');
  const close = document.getElementById('closePwaHelp');
  if (!install || !update || !status || !dialog || !instructions || !close) return;
  // Native Capacitor APK and PWA share these files. Never prompt Android APK users to install the PWA.
  if (window.Capacitor?.isNativePlatform?.()) {
    install.hidden = true;
    update.hidden = true;
    status.textContent = 'Android app';
    return;
  }
  let pendingInstall = null;
  const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
  const isStandalone = () => window.matchMedia('(display-mode: standalone)').matches || navigator.standalone === true;
  const supportedOrigin = window.isSecureContext && (location.protocol === 'https:' || ['localhost','127.0.0.1'].includes(location.hostname));
  const showHelp = message => { instructions.textContent = message; if (dialog.showModal) dialog.showModal(); else dialog.setAttribute('open',''); };
  close.addEventListener('click', () => dialog.close ? dialog.close() : dialog.removeAttribute('open'));
  const redraw = () => {
    const online = navigator.onLine;
    status.textContent = online ? 'Online' : 'Offline';
    status.classList.toggle('offline', !online);
    install.hidden = isStandalone();
  };
  window.addEventListener('online', redraw);
  window.addEventListener('offline', redraw);
  window.addEventListener('appinstalled', () => { pendingInstall = null; redraw(); });
  window.addEventListener('beforeinstallprompt', e => {e.preventDefault(); pendingInstall = e; install.hidden = isStandalone();});
  install.addEventListener('click', async () => {
    if (isStandalone()) return;
    if (pendingInstall) {
      const prompt = pendingInstall; pendingInstall = null;
      try { await prompt.prompt(); await prompt.userChoice; } catch (_) { showHelp('Use your browser menu and choose Install app or Add to Home screen.'); }
      return;
    }
    if (location.protocol === 'file:') {
      showHelp('This downloaded HTML preview runs without a web server, but installation requires the Varnethryl website opened over HTTPS. Publish the www/ folder to GitHub Pages, then open its URL.');
    } else if (!supportedOrigin) {
      showHelp('Install Varnethryl from its HTTPS website. The current connection is not secure enough for web-app installation.');
    } else if (isIOS) {
      showHelp('On iPhone or iPad, open this page in Safari, tap Share, choose Add to Home Screen, then tap Add.');
    } else {
      showHelp('In Chrome or Edge, open the browser menu (⋮) and choose Install app or Add to Home screen. If that option is missing, refresh once and try again.');
    }
  });
  redraw();
  if (!supportedOrigin || !('serviceWorker' in navigator)) return;
  let initialController = navigator.serviceWorker.controller;
  let updateReady = false;
  navigator.serviceWorker.addEventListener('controllerchange', () => {
    if (initialController && navigator.serviceWorker.controller !== initialController) {
      updateReady = true;
      update.hidden = false;
    }
    initialController = navigator.serviceWorker.controller;
  });
  update.addEventListener('click', () => {
    if (updateReady) location.reload();
  });
  navigator.serviceWorker.register('./sw.js', {updateViaCache:'none'}).then(reg => {
    window.addEventListener('focus', () => reg.update().catch(() => {}));
    navigator.serviceWorker.ready.then(() => {
      status.title = 'Game files cached for offline use on this device. Progress is saved locally to this browser profile.';
    });
  }).catch(err => {status.title = 'Offline installation unavailable: ' + err.message;});
})();
