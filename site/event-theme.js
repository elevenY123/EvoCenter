/* A fixed UTC interval, independent of the visitor's time zone. Stock artwork
   remains in place; the explicit preview URL never affects other visitors. */
(() => {
  'use strict';
  const start = Date.parse('2026-11-10T00:00:00+08:00');
  const end = Date.parse('2026-11-20T00:00:00+08:00');
  const root = document.documentElement;
  const base = new URL('../', document.currentScript.src);
  const eventBase = new URL('site/events/gta6-2026/', base);
  const preview = new URL(location.href).searchParams.get('preview') === 'gta6';
  const map = new Map();
  for (const [slug, folder] of [['evocenter',''], ['artmotion','ArtMotion/'], ['islandblur','IslandBlur/']]) {
    for (const source of [folder + 'assets/icon.png', 'site/icons/' + slug + '.png'])
      map.set(new URL(source, base).href, new URL(slug + '-icon-192.png', eventBase).href);
    map.set(new URL(folder + 'assets/banner.png', base).href, new URL(slug + '-banner.jpg', eventBase).href);
  }
  map.set(new URL('ArtMotion/assets/featured.png', base).href, new URL('artmotion-featured.jpg', eventBase).href);
  let active, timer;
  function imageState(img) {
    if (active) {
      const stock = img.getAttribute('data-stock-art') || img.getAttribute('src');
      if (!stock) return;
      const themed = map.get(new URL(stock, location.href).href);
      if (themed) {
        img.setAttribute('data-stock-art', stock);
        if (img.src !== themed) img.src = themed;
      }
    } else if (img.hasAttribute('data-stock-art')) {
      img.src = img.getAttribute('data-stock-art');
      img.removeAttribute('data-stock-art');
    }
  }
  function sync() {
    const now = Date.now();
    const next = preview || (now >= start && now < end);
    if (active !== next) {
      active = next;
      root.classList.toggle('gta6', active);
      root.classList.toggle('gta6-preview', active && preview);
      document.querySelectorAll('img').forEach(imageState);
      document.querySelectorAll('meta[name="theme-color"]').forEach(meta => {
        if (active) { meta.dataset.stockColor ||= meta.content; meta.content = '#140f26'; }
        else if (meta.dataset.stockColor) { meta.content = meta.dataset.stockColor; delete meta.dataset.stockColor; }
      });
    }
    clearTimeout(timer);
    const boundary = now < start ? start : now < end ? end : Infinity;
    timer = setTimeout(sync, Math.max(100, Math.min(60000, boundary - now + 20)));
  }
  sync();
  new MutationObserver(mutations => {
    for (const mutation of mutations) for (const node of mutation.addedNodes) {
      if (node.nodeType !== 1) continue;
      if (node.tagName === 'IMG') imageState(node);
      node.querySelectorAll('img').forEach(imageState);
    }
  }).observe(root, {childList:true, subtree:true});
  document.addEventListener('visibilitychange', sync);
  window.addEventListener('pageshow', sync);
})();
