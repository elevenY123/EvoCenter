(() => {
  'use strict';
  const cards = [...document.querySelectorAll('.tweak')];
  const search = document.querySelector('#search');
  const empty = document.querySelector('#empty');
  const count = document.querySelector('#result-count');
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
  const sourceURL = document.documentElement.dataset.source;
  function filterCards() {
    const query = search.value.trim().toLocaleLowerCase();
    let matches = 0;
    cards.forEach(card => {
      card.hidden = !card.dataset.search.toLocaleLowerCase().includes(query);
      if (!card.hidden) matches++;
    });
    empty.hidden = matches > 0;
    count.textContent = query ? `找到 ${matches} 款插件` : `${cards.length} 款插件`;
  }
  search.addEventListener('input', filterCards);
  document.querySelector('#clear-search').addEventListener('click', () => {
    search.value = ''; filterCards(); search.focus();
  });
  document.querySelectorAll('.gallery').forEach(gallery => {
    const scroller = gallery.querySelector('.shots');
    const previous = gallery.querySelector('[data-direction="-1"]');
    const next = gallery.querySelector('[data-direction="1"]');
    const controls = gallery.querySelector('.gallery-controls');
    function update() {
      previous.disabled = scroller.scrollLeft < 2;
      next.disabled = scroller.scrollWidth - scroller.clientWidth - scroller.scrollLeft < 3;
    }
    function move(direction) {
      scroller.scrollBy({left: direction * Math.max(scroller.clientWidth * .75, 180), behavior: reduced.matches ? 'instant' : 'smooth'});
    }
    previous.addEventListener('click', () => move(-1));
    next.addEventListener('click', () => move(1));
    scroller.addEventListener('scroll', update, {passive:true});
    scroller.addEventListener('keydown', event => {
      if (event.target !== scroller || !['ArrowLeft', 'ArrowRight'].includes(event.key)) return;
      event.preventDefault(); move(event.key === 'ArrowRight' ? 1 : -1);
    });
    scroller.querySelectorAll('img').forEach(img => img.addEventListener('load', update));
    if ('ResizeObserver' in window) new ResizeObserver(update).observe(scroller);
    window.addEventListener('resize', update, {passive:true});
    controls.classList.add('ready'); update();
  });
  const toast = document.querySelector('#toast');
  let toastTimer;
  function notify(message) {
    clearTimeout(toastTimer); toast.textContent = message; toast.hidden = false;
    toastTimer = setTimeout(() => { toast.hidden = true; }, 3000);
  }
  document.querySelector('#copy-source').addEventListener('click', async () => {
    try {
      if (!navigator.clipboard?.writeText) throw new Error('Clipboard unavailable');
      await navigator.clipboard.writeText(sourceURL);
      notify('源地址已复制');
    } catch {
      const field = document.createElement('textarea');
      field.value = sourceURL; field.setAttribute('readonly', '');
      field.style.cssText = 'position:fixed;left:-9999px;top:0';
      document.body.append(field); field.select();
      let copied = false;
      try { copied = document.execCommand('copy'); } catch { /* The visible URL remains available. */ }
      field.remove(); notify(copied ? '源地址已复制' : sourceURL);
    }
  });
  const dialog = document.querySelector('#lightbox');
  if (typeof dialog.showModal !== 'function') return;
  const image = dialog.querySelector('img');
  const title = dialog.querySelector('#lightbox-title');
  const caption = dialog.querySelector('#lightbox-caption');
  let shots = [], selected = 0, trigger = null;
  function display(index) {
    selected = (index + shots.length) % shots.length;
    const item = shots[selected];
    image.src = item.href; image.alt = item.querySelector('img').alt;
    title.textContent = item.closest('.tweak').querySelector('h2').textContent;
    caption.textContent = `实机截图 ${selected + 1} / ${shots.length}`;
  }
  document.querySelectorAll('.shot').forEach(link => link.addEventListener('click', event => {
    event.preventDefault(); trigger = link;
    shots = [...link.closest('.shots').querySelectorAll('.shot')];
    display(shots.indexOf(link)); dialog.showModal();
    document.body.style.overflow = 'hidden';
  }));
  function restorePage() {
    if (dialog.open) return;
    document.body.style.overflow = ''; image.removeAttribute('src'); trigger?.focus();
  }
  function closeLightbox() { dialog.close(); restorePage(); }
  dialog.querySelector('[data-close]').addEventListener('click', closeLightbox);
  dialog.addEventListener('cancel', event => { event.preventDefault(); closeLightbox(); });
  dialog.querySelector('[data-previous]').addEventListener('click', () => display(selected - 1));
  dialog.querySelector('[data-next]').addEventListener('click', () => display(selected + 1));
  dialog.addEventListener('keydown', event => {
    if (!['ArrowLeft', 'ArrowRight'].includes(event.key)) return;
    event.preventDefault(); display(selected + (event.key === 'ArrowRight' ? 1 : -1));
  });
  dialog.addEventListener('click', event => {
    if (event.target !== dialog) return;
    const bounds = dialog.getBoundingClientRect();
    if (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom) closeLightbox();
  });
  dialog.addEventListener('close', restorePage);
})();
