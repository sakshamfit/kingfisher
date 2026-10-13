(() => {
  'use strict';
  const $ = (s, root = document) => root.querySelector(s);
  const $$ = (s, root = document) => [...root.querySelectorAll(s)];
  const clamp = (n, a = 0, b = 1) => Math.min(b, Math.max(a, n));
  const smooth = n => { n = clamp(n); return n * n * (3 - 2 * n); };
  const lerp = (a, b, t) => a + (b - a) * t;
  const motionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
  let reducedMotion = motionQuery.matches;
  const root = document.documentElement;
  const products = [
    {id:'premium-grain',name:'Premium Grain Vodka',hi:'प्रीमियम ग्रेन वोदका',type:'Premium grain vodka',group:'lager',tone:'#1f4b8f',file:'mm-premium-grain.webp',size:[234,886],box:[0,0,234,886],description:'The original Saksham Moments. A triple-distilled grain vodka with a clean, smooth character, from Radico Khaitan.',style:'Premium grain vodka',character:'Clean & smooth'},
    {id:'triple-distilled',name:'Triple Distilled',hi:'ट्रिपल डिस्टिल्ड',type:'Triple distilled vodka',group:'lager',tone:'#1b3f7a',file:'mm-triple-distilled.webp',size:[1999,2999],box:[627,124,745,2751],description:'Triple distilled from fine grain for a soft, almost weightless character. The everyday pour that anchors the table.',style:'Triple distilled vodka',character:'Soft & clean'},
    {id:'dazzle-gold',name:'Dazzle Gold',hi:'डैज़ल गोल्ड',type:'Special edition grain vodka',group:'strong',tone:'#c9a227',file:'mm-dazzle-gold.webp',size:[1000,1406],box:[315,150,350,1165],description:'The special-edition expression of the family, dressed in gold. A grain vodka with a distinctly premium identity.',style:'Special edition grain vodka',character:'Gold & premium'},
    {id:'verve-super',name:'Verve Super Premium',hi:'वर्व सुपर प्रीमियम',type:'Super premium vodka',group:'strong',tone:'#274b86',file:'mm-verve-super.webp',size:[600,600],box:[229,55,142,506],description:'The super-premium chapter of Saksham Moments. A smoother, more considered pour for the occasions that ask for one.',style:'Super premium vodka',character:'Smooth & refined'},
    {id:'verve-cranberry',name:'Verve Cranberry',hi:'वर्व क्रैनबेरी',type:'Cranberry flavoured vodka',group:'wheat',tone:'#b8224a',file:'mm-verve-cranberry.webp',size:[293,1113],box:[0,0,293,1113],description:'Cranberry, bright and lightly tart, naturally infused for a flavoured vodka that stays clean rather than sweet.',style:'Cranberry flavoured vodka',character:'Bright & lightly tart'},
    {id:'verve-orange',name:'Verve Orange',hi:'वर्व ऑरेंज',type:'Orange flavoured vodka',group:'wheat',tone:'#e06a1f',file:'mm-verve-orange.webp',size:[369,1394],box:[0,0,369,1394],description:'Sun-ripe orange over a triple-distilled base. A clean flavoured pour that works neat, long or over ice.',style:'Orange flavoured vodka',character:'Bright & citrus'},
    {id:'remix-green-apple',name:'Remix Green Apple',hi:'रीमिक्स ग्रीन एप्पल',type:'Green apple flavoured vodka',group:'flavour',tone:'#5a9e2f',file:'mm-remix-green-apple.webp',size:[2188,3283],box:[656,0,874,3283],description:'The flavour that made Remix a household name. Tart green apple, naturally infused and refreshingly crisp.',style:'Green apple flavoured vodka',character:'Crisp & tart'},
    {id:'remix-lemongrass',name:'Remix Lemongrass & Ginger',hi:'रीमिक्स लेमनग्रास एंड जिंजर',type:'Lemongrass & ginger flavoured vodka',group:'flavour',tone:'#7d8f2a',file:'mm-remix-lemongrass.webp',size:[934,1625],box:[303,348,335,1230],description:'Lemongrass and ginger over grain vodka, an Indian flavour pairing that is infused rather than sweetened.',style:'Lemongrass & ginger flavoured vodka',character:'Warm & aromatic'},
    {id:'remix-raspberry',name:'Remix Raspberry',hi:'रीमिक्स रास्पबेरी',type:'Raspberry flavoured vodka',group:'flavour',tone:'#c02b52',file:'mm-remix-raspberry.webp',size:[934,1625],box:[305,346,336,1230],description:'Raspberry, naturally infused for a soft, rounded flavoured vodka that keeps its bite at the finish.',style:'Raspberry flavoured vodka',character:'Soft & rounded'}
  ];
  const productById = id => products.find(p => p.id === id);
  let svgIndex = 0;
  function bottle(p, label = '') {
    const id = `bottle-clip-${++svgIndex}`;
    return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="${p.box.join(' ')}" width="${p.box[2]}" height="${p.box[3]}" role="img" aria-label="${label || `Saksham Moments ${p.name} bottle`}">${p.path ? `<defs><clipPath id="${id}"><path d="${p.path}"/></clipPath></defs>` : ''}<image href="assets/${p.file}" width="${p.size[0]}" height="${p.size[1]}" ${p.path ? `clip-path="url(#${id})"` : ''}/></svg>`;
  }

  // Shared drawings: a genda (marigold), an aam patta (mango leaf) and the gradients for diya flames.
  const petalRing = (n, r, rx, ry, fill, turn) => Array.from({length:n}, (_, i) => `<ellipse cx="0" cy="${-r}" rx="${rx}" ry="${ry}" transform="rotate(${(i * 360 / n + turn).toFixed(1)})" style="fill:${fill}"/>`).join('');
  document.body.insertAdjacentHTML('afterbegin', `<svg class="sprite" aria-hidden="true" focusable="false"><defs>
    <linearGradient id="flame-grad" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="#fff6c4"/><stop offset=".45" stop-color="#ffc22e"/><stop offset="1" stop-color="#ff6200"/></linearGradient>
    <radialGradient id="diya-glow-grad"><stop offset="0" stop-color="#ffcf5a" stop-opacity=".75"/><stop offset="1" stop-color="#ffcf5a" stop-opacity="0"/></radialGradient>
    <symbol id="genda" viewBox="-20 -20 40 40"><g stroke="#7a3300" stroke-opacity=".22" stroke-width=".6">${petalRing(16, 11, 5, 8, 'var(--p1,#ee7d11)', 0)}${petalRing(13, 7.5, 4.2, 6, 'var(--p2,#f6a123)', 9)}${petalRing(9, 4, 3, 4, 'var(--p1,#ee7d11)', 4)}</g><circle r="2.6" style="fill:var(--p3,#b9500b)"/></symbol>
    <symbol id="aam-patta" viewBox="0 0 16 42"><path d="M8 0C14.5 8 15.5 25 8 42C.5 25 1.5 8 8 0Z" style="fill:var(--leaf,#3d7a2c)"/><path d="M8 2V39" stroke="#1f4a17" stroke-width="1" opacity=".5"/></symbol>
  </defs></svg>`);
  const diyaSvg = () => `<svg class="diya-svg" viewBox="0 -8 64 56" aria-hidden="true" focusable="false"><circle class="diya-glow" cx="54" cy="12" r="18" fill="url(#diya-glow-grad)"/><path class="diya-flame" d="M54 19C59.5 14 58.5 6 54 -3C49.5 6 48.5 14 54 19Z" fill="url(#flame-grad)"/><path d="M4 24C8 41 40 47 55 31L63 22C50 25.5 18 26.5 4 24Z" fill="#a9451c"/><path d="M4 24C18 26.5 50 25.5 63 22C50 19.5 18 20 4 24Z" fill="#4d1f0c"/><path d="M8 27C14 37 38 41 50 32" fill="none" stroke="#d2703f" stroke-width="1.4" opacity=".7"/><g fill="#f6c04a"><circle cx="15" cy="32.5" r="1.6"/><circle cx="24" cy="36" r="1.6"/><circle cx="33" cy="37" r="1.6"/><circle cx="42" cy="35" r="1.6"/></g><path d="M51.5 22.5Q53.5 20.5 54 18.5" fill="none" stroke="#2a1608" stroke-width="1.6" stroke-linecap="round"/></svg>`;

  $('#hero-bottle').innerHTML = bottle(products[0]);
  $('#product-grid').innerHTML = products.map(p => `<button class="product" data-product="${p.id}" data-group="${p.group}" style="--product-color:${p.tone}" aria-label="Explore Saksham Moments ${p.name}"><span class="product-visual">${bottle(p)}</span><span class="product-name">${p.name}</span><span class="product-type">${p.type}</span><span class="product-arrow" aria-hidden="true">↗</span></button>`).join('');
  $('#flavour-art').innerHTML = bottle(products[8]) + bottle(products[7]);

  // The artwork remains intact; SVG viewBoxes and clipping paths only control page presentation.
  const modal = $('#detail-dialog');
  const modalContent = $('#dialog-content');
  let lastFocus = null;
  function openDialog(content) {
    closeMenu();
    lastFocus = document.activeElement;
    modalContent.innerHTML = content;
    modal.showModal();
    document.body.style.overflow = 'hidden';
    modal.scrollTop = 0;
    $('.dialog-close').focus();
  }
  function closeDialog() { modal.close(); }
  $('.dialog-close').addEventListener('click', closeDialog);
  modal.addEventListener('close', () => { document.body.style.overflow = ''; lastFocus?.focus({preventScroll:true}); });
  modal.addEventListener('click', e => { if (e.target === modal) { const r = modal.getBoundingClientRect(); if (e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom) closeDialog(); } });
  function showProduct(id) {
    const p = productById(id);
    if (!p) return;
    openDialog(`<div class="detail-layout"><div class="detail-art" data-hi="${p.hi}">${bottle(p)}</div><div class="detail-copy"><span class="eyebrow">THE MAGIC MOMENTS FAMILY</span><h2 class="display">${p.name}.</h2><p>${p.description}</p><div class="detail-meta"><div><small>STYLE</small><strong>${p.style}</strong></div><div><small>CHARACTER</small><strong>${p.character}</strong></div></div><p class="detail-fine">Availability, pack design and alcohol content vary by region. Check the local product label. This is a brand showcase; products cannot be purchased here.</p><button class="button dark" data-back-range>Back to the family <span>↗</span></button></div></div>`);
    $('[data-back-range]', modal).addEventListener('click', closeDialog);
  }
  $$('.product').forEach(el => el.addEventListener('click', () => showProduct(el.dataset.product)));
  function filterProducts(group) {
    $$('.filters button').forEach(b => { const active = b.dataset.filter === group; b.classList.toggle('active', active); b.setAttribute('aria-pressed', String(active)); });
    $$('.product').forEach(el => { el.hidden = group !== 'all' && el.dataset.group !== group; });
    metricsDirty = true;
    requestTick();
  }
  $$('.filters button').forEach(b => b.addEventListener('click', () => filterProducts(b.dataset.filter)));
  $('[data-show-flavours]').addEventListener('click', () => { filterProducts('flavour'); $('#range').scrollIntoView({behavior:reducedMotion?'instant':'smooth'}); });

  const menu = $('#menu'), menuButton = $('.menu-toggle');
  function closeMenu() {
    document.body.classList.remove('menu-open'); menuButton.setAttribute('aria-expanded','false'); menuButton.setAttribute('aria-label','Open navigation'); menu.inert = true;
  }
  menuButton.addEventListener('click', () => {
    const open = !document.body.classList.contains('menu-open');
    document.body.classList.toggle('menu-open', open); menuButton.setAttribute('aria-expanded', String(open)); menuButton.setAttribute('aria-label', open?'Close navigation':'Open navigation'); menu.inert = !open;
    if (open) $('a',menu).focus({preventScroll:true});
  });
  $$('a',menu).forEach(a => a.addEventListener('click', closeMenu));
  document.addEventListener('keydown', e => { if (e.key === 'Escape' && document.body.classList.contains('menu-open')) {closeMenu(); menuButton.focus();} });
  $$('[data-open-story]').forEach(b => b.addEventListener('click', () => openDialog(`<article class="dialog-text"><span class="script">The story behind the bottle.</span><h2 class="display">A MODERN INDIAN<br>ORIGINAL.</h2><p>Saksham Moments was launched by Radico Khaitan in 2006 and grew into India’s best-selling vodka. It is distilled at the historic Rampur distillery, triple distilled from fine grain for a clean, soft character.</p><h3>ONE FAMILY. MANY EXPRESSIONS.</h3><p>The family runs from the original Premium Grain Vodka and Triple Distilled to Verve Super Premium, Dazzle Gold and the Verve flavours, with the Remix range bringing Green Apple, Raspberry, Orange and Lemongrass &amp; Ginger to the table.</p><h3>A PLACE AT THE TABLE.</h3><p>This concept celebrates the familiar things: food with character, conversations that wander, and the distinctly Indian spirit behind the brand.</p><a href="https://www.radicokhaitan.com/" target="_blank" rel="noopener">Explore Radico Khaitan ↗</a></article>`)));
  $('#sources-button').addEventListener('click', () => openDialog(`<article class="dialog-text"><span class="eyebrow">CREDITS &amp; PRODUCT INFORMATION</span><h2 class="display">BEHIND<br>THE CONCEPT.</h2><p>An independent website design concept, adapted from the supplied motion reference. This is not the official Saksham Moments website. It does not sell alcohol.</p><div class="credit-list"><p><a href="https://www.radicokhaitan.com/" target="_blank" rel="noopener">Radico Khaitan</a> — Saksham Moments brand and product information, distillation and tasting notes.</p><p><a href="https://sipdirect.com/products/magic-moments-grain-vodka" target="_blank" rel="noopener">SipDirect</a> — Premium Grain Vodka, Triple Distilled, Remix Green Apple, Raspberry and Orange pack photography.</p><p><a href="https://www.liquorvaultgoa.com/product/magic-moments-vodka-750ml/" target="_blank" rel="noopener">Liquor Vault Goa</a> — Dazzle Gold and Verve Super Premium pack photography. <a href="https://www.gbiexpress.com/magic-moments-cranberry-vodka-75-cl-bottle" target="_blank" rel="noopener">GBI Express</a> — Verve Cranberry. <a href="https://www.livcheers.com/" target="_blank" rel="noopener">LivCheers</a> — Remix Lemongrass &amp; Ginger. Pack appearance and specifications may differ by market.</p><p><a href="https://www.hotpepper.jp/strJ001273019/" target="_blank" rel="noopener">Curry India Tabla / Hot Pepper Gourmet</a> — food photograph. <a href="https://www.365drinks.co.uk/collections/pints" target="_blank" rel="noopener">365 Drinks</a> — glass photograph.</p><p>The toran, diyas, station sign, glass and truck panel are original illustrations drawn for this concept.</p><p>Fonts: Anton, Barlow Condensed, DM Sans, Yatra One and Noto Sans (Bengali, Devanagari, Kannada, Malayalam, Tamil, Telugu), distributed through Google Fonts.</p></div><p class="detail-fine">All trademarks and product imagery remain the property of their respective owners. No prices, live availability or universal alcohol percentages are asserted. Pack design and product names differ by market. Check your local pack for current information.</p></article>`));

  const toastEl = $('.toast');
  let toastTimer = 0;
  function toast(message) {
    toastEl.textContent = message;
    toastEl.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toastEl.classList.remove('show'), 3200);
  }

  // Petals: one shared layer so bursts can fall past the section they started in.
  const petalLayer = $('.petal-layer');
  const petals = [];
  const PETAL_COLOURS = {genda:['#ee7d11','#f6a123','#f5b301'], spark:['#ffd34d','#fff1b8','#ff9a1f']};
  let petalsRunning = false, petalClock = 0;
  function burst(x, y, count, kind = 'genda') {
    if (reducedMotion) return;
    for (let i = 0; i < count; i++) {
      if (petals.length > 90) petals.shift().el.remove();
      const el = document.createElement('span');
      el.className = `petal ${kind}`;
      el.style.setProperty('--petal', PETAL_COLOURS[kind][i % 3]);
      petalLayer.append(el);
      const angle = -Math.PI / 2 + (Math.random() - .5) * Math.PI * 1.5;
      const speed = 140 + Math.random() * 280;
      petals.push({el, x, y, vx:Math.cos(angle) * speed, vy:Math.sin(angle) * speed, r:Math.random() * 360, vr:(Math.random() - .5) * 720, t:0, life:1.5 + Math.random() * .9, phase:Math.random() * 6});
    }
    if (!petalsRunning) { petalsRunning = true; petalClock = performance.now(); requestAnimationFrame(petalTick); }
  }
  function petalTick(now) {
    const dt = Math.min(.033, (now - petalClock) / 1000);
    petalClock = now;
    for (let i = petals.length - 1; i >= 0; i--) {
      const p = petals[i];
      p.t += dt; p.vy += 520 * dt; p.vx *= 1 - 1.8 * dt; p.vy *= 1 - 1.1 * dt;
      p.x += (p.vx + Math.sin(p.t * 5 + p.phase) * 40) * dt; p.y += p.vy * dt; p.r += p.vr * dt;
      p.el.style.transform = `translate3d(${p.x.toFixed(1)}px,${p.y.toFixed(1)}px,0) rotate(${p.r.toFixed(0)}deg)`;
      p.el.style.opacity = String(1 - smooth((p.t - p.life + .5) / .5));
      if (p.t > p.life || p.y > window.innerHeight + 30) { p.el.remove(); petals.splice(i, 1); }
    }
    if (petals.length) requestAnimationFrame(petalTick); else petalsRunning = false;
  }

  // Toran: marigold strings and mango leaves that swing like pendulums when the pointer brushes past.
  const toran = $('.toran');
  let strands = [], toranRunning = false, toranClock = 0, lastPointer = null;
  function buildToran() {
    const W = toran.clientWidth;
    const mobile = W < 640;
    const count = Math.max(8, Math.round(W / (mobile ? 27 : 38)));
    const gap = W / count, sag = mobile ? 10 : 18;
    const ropeY = x => 8 + sag * 4 * (x / W) * (1 - x / W);
    let html = `<svg class="toran-rope" width="${W}" height="${sag + 20}" viewBox="0 0 ${W} ${sag + 20}"><path d="M0 8Q${W / 2} ${8 + sag * 2} ${W} 8"/><path class="twist" d="M0 8Q${W / 2} ${8 + sag * 2} ${W} 8"/></svg>`;
    const specs = [];
    for (let i = 0; i < count; i++) {
      const x = (i + .5) * gap, y = ropeY(x);
      if (i % 3 === 1) {
        const flowers = mobile ? 2 + (i % 2) : 3 + ((i * 7) % 3);
        const colours = Array.from({length:flowers}, (_, j) => (i + j) % 2 ? '--p1:#f5b301;--p2:#ffd34d;--p3:#c77a00' : '--p1:#ee7d11;--p2:#f6a123;--p3:#b9500b');
        html += `<div class="toran-strand genda" style="left:${x.toFixed(1)}px;top:${y.toFixed(1)}px">${colours.map(c => `<svg style="${c}"><use href="#genda"/></svg>`).join('')}<i></i></div>`;
        specs.push({len:flowers * 16 + 14, kind:'genda'});
      } else {
        html += `<div class="toran-strand leaf" style="left:${x.toFixed(1)}px;top:${(y - 2).toFixed(1)}px;--leaf:${i % 2 ? '#3d7a2c' : '#4f8f33'}"><svg><use href="#aam-patta"/></svg></div>`;
        specs.push({len:40, kind:'leaf'});
      }
    }
    toran.innerHTML = html;
    strands = $$('.toran-strand', toran).map((el, i) => {
      const s = specs[i];
      return {el, x:parseFloat(el.style.left), top:parseFloat(el.style.top), len:s.len, kind:s.kind, a:0, v:0, k:s.kind === 'leaf' ? 2600 / s.len : 900 / s.len, c:s.kind === 'leaf' ? 4 : 1.5};
    });
  }
  function toranTick(now) {
    const dt = Math.min(.033, (now - toranClock) / 1000);
    toranClock = now;
    let active = false;
    for (const s of strands) {
      s.v += (-s.k * s.a - s.c * s.v) * dt;
      s.a = clamp(s.a + s.v * dt, -40, 40);
      if (Math.abs(s.a) > .03 || Math.abs(s.v) > .08) active = true;
      s.el.style.transform = `rotate(${s.a.toFixed(2)}deg)`;
    }
    if (active) requestAnimationFrame(toranTick);
    else { toranRunning = false; strands.forEach(s => { s.a = s.v = 0; s.el.style.transform = ''; }); }
  }
  function swingToran() { if (!toranRunning) { toranRunning = true; toranClock = performance.now(); requestAnimationFrame(toranTick); } }
  if (toran) {
    buildToran();
    toran.addEventListener('pointermove', e => {
      if (reducedMotion) return;
      const r = toran.getBoundingClientRect(), x = e.clientX - r.left, y = e.clientY - r.top, now = performance.now();
      if (lastPointer && now - lastPointer.t < 120) {
        const vx = clamp((x - lastPointer.x) / Math.max(8, now - lastPointer.t) * 1000, -3000, 3000);
        let touched = false;
        for (const s of strands) {
          const d = Math.abs(s.x - x);
          if (d < 60 && y > s.top - 12 && y < s.top + s.len + 16) { s.v = clamp(s.v - vx * .028 * (1 - d / 60) * (s.kind === 'leaf' ? .6 : 1), -240, 240); touched = true; }
        }
        if (touched) swingToran();
      }
      lastPointer = {x, y, t:now};
    });
    toran.addEventListener('pointerleave', () => { lastPointer = null; });
    toran.addEventListener('pointerdown', e => {
      if (reducedMotion) return;
      const r = toran.getBoundingClientRect(), x = e.clientX - r.left;
      strands.forEach(s => { const d = Math.abs(s.x - x); if (d < 80) s.v += (Math.random() - .5) * 160 * (1 - d / 80); });
      swingToran();
      burst(e.clientX, e.clientY, 16);
    });
    if (!reducedMotion) setTimeout(() => { strands.forEach((s, i) => { s.v = 46 * Math.sin(i * .55); }); swingToran(); }, 450);
  }

  // Diyas appear on Diwali night; light all six for a shower of sparks.
  const diyaRow = $('.diyas'), DIYAS = 6;
  diyaRow.innerHTML = Array.from({length:DIYAS}, (_, i) => `${i === DIYAS / 2 ? '<span class="diya-gap"></span>' : ''}<button class="diya" aria-pressed="false" aria-label="Diya ${i + 1} of ${DIYAS}">${diyaSvg()}</button>`).join('');
  let allLit = false;
  $$('.diya', diyaRow).forEach(button => button.addEventListener('click', () => {
    const lit = button.getAttribute('aria-pressed') !== 'true';
    button.setAttribute('aria-pressed', String(lit));
    const count = $$('.diya[aria-pressed="true"]', diyaRow).length;
    if (count === DIYAS && !allLit) {
      allLit = true;
      toast('Shubh Deepavali! Every diya is lit.');
      $$('.diya', diyaRow).forEach((d, i) => setTimeout(() => { const r = d.getBoundingClientRect(); burst(r.left + r.width * .84, r.top + r.height * .3, 9, 'spark'); }, i * 90));
    } else if (count < DIYAS) allLit = false;
  }));

  // Ladi: the string of lights along the top edge on Diwali night.
  const ladi = $('.ladi');
  function buildLadi() {
    const W = window.innerWidth, step = 30, n = Math.ceil(W / step) + 1;
    const colours = ['#ffd34d', '#ff8a3d', '#ff4f6d', '#fff1b8'];
    const points = [];
    let bulbs = '';
    for (let i = 0; i < n; i++) {
      const x = i * step, y = 3 + 10 * Math.sin(Math.PI * (i % 9) / 9);
      points.push(`${x},${y.toFixed(1)}`);
      bulbs += `<span style="left:${x}px;top:${(y + 1).toFixed(1)}px;--c:${colours[i % 4]};--d:${((i * 0.37) % 2).toFixed(2)}s"></span>`;
    }
    ladi.innerHTML = `<svg width="${W}" height="20"><polyline points="${points.join(' ')}"/></svg>${bulbs}`;
  }
  buildLadi();

  // Theme: daylight or Diwali night, revealed as a circle spreading from the switch.
  const themeButton = $('.theme-toggle'), themeColour = $('meta[name="theme-color"]');
  themeButton.insertAdjacentHTML('afterbegin', diyaSvg());
  function applyTheme(night) {
    if (night) root.dataset.theme = 'night'; else delete root.dataset.theme;
    themeButton.setAttribute('aria-pressed', String(night));
    themeColour.content = night ? '#191530' : '#c8102e';
  }
  applyTheme(root.dataset.theme === 'night');
  themeButton.addEventListener('click', () => {
    const night = root.dataset.theme !== 'night';
    try { localStorage.setItem('kf-theme', night ? 'night' : 'day'); } catch (err) {}
    if (!document.startViewTransition || reducedMotion) applyTheme(night);
    else {
      const r = themeButton.getBoundingClientRect(), x = r.left + r.width / 2, y = r.top + r.height / 2;
      const radius = Math.hypot(Math.max(x, window.innerWidth - x), Math.max(y, window.innerHeight - y));
      const transition = document.startViewTransition(() => applyTheme(night));
      transition.ready.then(() => root.animate({clipPath:[`circle(0px at ${x}px ${y}px)`, `circle(${radius}px at ${x}px ${y}px)`]}, {duration:800, easing:'cubic-bezier(.76,0,.24,1)', pseudoElement:'::view-transition-new(root)'})).catch(() => {});
    }
    const heroVisible = $('.hero').getBoundingClientRect().bottom > 120;
    toast(night ? (heroVisible ? 'Diwali night is on. Tap the diyas to light them.' : 'Diwali night is on. Light the diyas at the top of the page.') : 'Daylight is back.');
  });

  // Pour it right: lift the bottle (or hold the button) and beer falls from the neck as a real stream.
  // Steeper tilt pours faster and foams more; the fill line and gauge react live as the glass fills.
  const pourSection = $('#pour'), pourStage = $('.pour-stage');
  const pour = {liquid:0, foam:0, spilled:0, angle:-78, target:-78, holding:false, done:false, overflowed:false};
  const P = {x:214, y:128}, REST = -78, HOLD_TILT = -124, MAX_TILT = -140;
  const GLASS_TOP = 214, GLASS_BOTTOM = 490, GLASS_H = GLASS_BOTTOM - GLASS_TOP, FILL_LINE = .8, GLASS_ML = 500;
  const RATE = .21, GRAVITY = 1500, TABLE = 500;
  const levelY = level => GLASS_BOTTOM - level * GLASS_H;
  const wallX = (y, side) => { const t = clamp((y - GLASS_TOP) / (486 - GLASS_TOP)); return side < 0 ? lerp(97, 112.5, t) : lerp(243, 227.5, t); };
  const flowAt = angle => Math.pow(clamp((-angle - 100) / 34), .75);
  const fillY = levelY(FILL_LINE);
  const strong = products[0], bw = 62, bh = bw * strong.size[1] / strong.size[0];
  const glassInside = 'M97 214H243L227.5 486Q227 490 222 490H118Q113 490 112.5 486Z';
  const ticks = Array.from({length:9}, (_, i) => { const y = levelY((i + 1) / 10).toFixed(1); return `<line x1="${i % 2 ? 70 : 76}" x2="84" y1="${y}" y2="${y}"/>`; }).join('');
  const bubbles = Array.from({length:14}, (_, i) => `<circle class="bubble" cx="${120 + ((i * 53) % 100)}" cy="${GLASS_BOTTOM + 4}" r="${(1.1 + (i * 37 % 10) / 6).toFixed(1)}" style="animation-duration:${(2.1 + (i % 4) * .55).toFixed(2)}s;animation-delay:${(-(i * .41) % 3).toFixed(2)}s"/>`).join('');
  pourStage.innerHTML = `<svg class="pour-svg" viewBox="0 -40 460 580">
    <defs>
      <clipPath id="glass-clip"><path d="${glassInside}"/></clipPath>
      <clipPath id="beer-clip"><rect id="beer-clip-rect" x="80" y="${GLASS_BOTTOM}" width="180" height="0"/></clipPath>
      <linearGradient id="beer-grad" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#f9c84f"/><stop offset="1" stop-color="#d07c0a"/></linearGradient>
      <linearGradient id="stream-grad" gradientUnits="userSpaceOnUse" x1="0" y1="${P.y}" x2="0" y2="${GLASS_BOTTOM}"><stop offset="0" stop-color="#f7bd45"/><stop offset="1" stop-color="#df8d10"/></linearGradient>
      <linearGradient id="sheen-grad" x1="0" x2="1"><stop offset=".08" stop-color="#fff" stop-opacity="0"/><stop offset=".16" stop-color="#fff" stop-opacity=".45"/><stop offset=".26" stop-color="#fff" stop-opacity="0"/></linearGradient>
    </defs>
    <ellipse class="glass-shadow" cx="170" cy="502" rx="92" ry="8"/>
    <ellipse id="puddle" class="puddle" cx="150" cy="503" rx="0" ry="0"/>
    <g class="pour-ruler">${ticks}<line x1="84" x2="84" y1="${GLASS_TOP + 8}" y2="${GLASS_BOTTOM}"/></g>
    <g id="level-tag" class="level-tag"><rect x="0" y="-11" width="62" height="22" rx="11"/><text x="31" y="4.5">0 ml</text></g>
    <g clip-path="url(#glass-clip)">
      <rect class="glass-tint" x="80" y="200" width="180" height="300"/>
      <rect id="beer-fill" x="80" y="${GLASS_BOTTOM}" width="180" height="0" fill="url(#beer-grad)"/>
      <g clip-path="url(#beer-clip)">${bubbles}</g>
      <path id="foam" class="foam" d=""/>
      <g id="splash"></g>
    </g>
    <path d="${glassInside}" fill="url(#sheen-grad)"/>
    <path class="glass-outline" d="M91 208H249L233 490Q232 498 224 498H116Q108 498 107 490Z"/>
    <g class="fill-line" id="fill-line"><line x1="101" x2="240" y1="${fillY}" y2="${fillY}"/><text x="254" y="${fillY + 1}" id="fill-label">fill line</text><text class="fill-ml" x="254" y="${fillY + 17}">${Math.round(FILL_LINE * GLASS_ML)} ml</text></g>
    <g id="spill" class="spill"><path d="M84 211Q170 184 256 211L251 216Q170 200 89 216Z"/><path d="M91 210C80 218 86 246 81 268C79 279 89 281 88 268C90 246 97 226 99 214Z"/><path d="M249 210C260 218 254 240 259 258C261 269 251 271 252 258C250 240 243 226 241 214Z"/><ellipse cx="170" cy="503" rx="128" ry="9"/></g>
    <path id="stream" class="stream" d="" fill="url(#stream-grad)"/>
    <path id="stream-shine" class="stream-shine" d=""/>
    <g id="drops"></g>
    <g id="pour-bottle" class="pour-grab" transform="translate(${P.x} ${P.y}) rotate(${REST})"><line class="grab-zone" x1="0" y1="16" x2="0" y2="${(bh - 12).toFixed(1)}"/><image href="assets/${strong.file}" x="${-bw / 2}" y="-3" width="${bw}" height="${bh.toFixed(1)}"/></g>
    <g class="pour-hint" id="pour-hint"><path d="M440 222C462 204 466 168 450 138"/><path d="M440 150L450 136L459 150"/><text x="458" y="250">lift to pour</text></g>
  </svg>`;
  const pourSvg = $('.pour-svg', pourStage);
  const beerRect = $('#beer-fill'), beerClip = $('#beer-clip-rect'), foamPath = $('#foam'), streamPath = $('#stream'), shinePath = $('#stream-shine');
  const pourBottle = $('#pour-bottle'), spill = $('#spill'), puddle = $('#puddle'), dropLayer = $('#drops'), splashLayer = $('#splash');
  const levelTag = $('#level-tag'), levelText = $('text', levelTag), fillLine = $('#fill-line'), fillLabel = $('#fill-label'), pourHint = $('#pour-hint');
  const holdButton = $('#pour-hold'), serveButton = $('#pour-serve'), soundButton = $('#pour-sound'), pourResult = $('#pour-result'), pourStatus = $('#pour-status');
  const parcels = [], drops = [];
  const impact = {x:170, amp:0, landing:0};
  let pourFrame = 0, pourClock = 0, pourTime = 0, dragging = null, lastSpillAt = -9, lineState = '', statusText = '';

  let audio = null; // shared by the pour sound and the horn
  // Sound: filtered noise whose pitch rises as the glass fills, the way a real pour does.
  let pourAudio = null, soundOn = true;
  function ensurePourAudio() {
    if (!soundOn || pourAudio) { pourAudio?.ctx.resume?.(); return; }
    try {
      audio = audio || new (window.AudioContext || window.webkitAudioContext)();
      const ctx = audio, buffer = ctx.createBuffer(1, ctx.sampleRate * 2, ctx.sampleRate), data = buffer.getChannelData(0);
      for (let i = 0; i < data.length; i++) data[i] = Math.random() * 2 - 1;
      const source = ctx.createBufferSource(), band = ctx.createBiquadFilter(), gain = ctx.createGain();
      source.buffer = buffer; source.loop = true; band.type = 'bandpass'; band.Q.value = 4.5; gain.gain.value = 0;
      source.connect(band); band.connect(gain); gain.connect(ctx.destination); source.start();
      pourAudio = {ctx, band, gain};
      ctx.resume?.();
    } catch (err) { pourAudio = null; }
  }
  function pourSound(level) {
    if (!pourAudio) return;
    const t = pourAudio.ctx.currentTime;
    pourAudio.band.frequency.setTargetAtTime(300 + 1150 * Math.pow(clamp(level), 1.4), t, .05);
    pourAudio.gain.gain.setTargetAtTime(soundOn ? .2 * impact.landing : 0, t, .04);
  }
  soundButton.addEventListener('click', () => {
    soundOn = !soundOn;
    soundButton.setAttribute('aria-pressed', String(soundOn));
    if (soundOn) ensurePourAudio(); else pourSound(0);
  });

  function emitParcel(fe, dt) {
    const a = pour.angle * Math.PI / 180, nx = Math.sin(a), ny = -Math.cos(a), v0 = 40 + 110 * fe;
    parcels.push({x:P.x + nx * 3, y:P.y + ny * 3, vx:nx * v0 + (Math.random() - .5) * 5, vy:ny * v0, v0, w:4 + 11 * fe, fe, vol:RATE * fe * dt, born:pourTime, outside:false});
  }
  function land(p, surface) {
    const drop = clamp((surface - P.y) / (GLASS_BOTTOM - P.y));
    pour.liquid += p.vol;
    pour.foam += p.vol * (.1 + 1.05 * p.fe * p.fe) * (.5 + .8 * drop);
    impact.x = lerp(impact.x, p.x, .35);
    impact.landing = Math.max(impact.landing, p.fe);
    if (!reducedMotion && drops.length < 26 && Math.random() < .08 + .3 * p.fe) {
      const el = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
      el.setAttribute('r', (1.2 + Math.random() * 1.6).toFixed(1));
      el.setAttribute('class', 'drop');
      splashLayer.append(el);
      drops.push({el, x:p.x, y:surface, vx:(Math.random() - .5) * 110, vy:-(50 + Math.random() * 150) * (.4 + p.fe), floor:surface});
    }
  }
  function stepParcels(dt) {
    const surface = levelY(pour.liquid + pour.foam);
    for (let i = parcels.length - 1; i >= 0; i--) {
      const p = parcels[i], prevY = p.y;
      p.vy += GRAVITY * dt; p.x += p.vx * dt; p.y += p.vy * dt;
      if (!p.outside && prevY < GLASS_TOP && p.y >= GLASS_TOP && (p.x < wallX(GLASS_TOP, -1) || p.x > wallX(GLASS_TOP, 1))) p.outside = true;
      if (!p.outside && p.y >= surface) { land(p, surface); parcels.splice(i, 1); }
      else if (p.outside && p.y >= TABLE) { pour.spilled += p.vol; lastSpillAt = pourTime; puddle.setAttribute('cx', p.x.toFixed(1)); parcels.splice(i, 1); }
    }
    for (let i = drops.length - 1; i >= 0; i--) {
      const d = drops[i];
      d.vy += GRAVITY * .8 * dt; d.x += d.vx * dt; d.y += d.vy * dt;
      d.el.setAttribute('cx', d.x.toFixed(1)); d.el.setAttribute('cy', d.y.toFixed(1));
      if (d.y > d.floor + 2 && d.vy > 0) { d.el.remove(); drops.splice(i, 1); }
    }
  }
  // The stream is a ribbon through the falling parcels; it thins as it speeds up, like a real pour.
  function streamShapes(flowing) {
    let body = '', shine = '', run = [];
    const flush = withNeck => {
      if (withNeck && run.length) { const last = run[run.length - 1]; const a = pour.angle * Math.PI / 180; run.push({x:P.x, y:P.y, vx:Math.sin(a) * last.v0, vy:-Math.cos(a) * last.v0, v0:last.v0, w:last.w}); }
      if (run.length >= 2) {
        const left = [], right = [], glint = [];
        run.forEach((p, i) => {
          const a = run[Math.max(0, i - 1)], b = run[Math.min(run.length - 1, i + 1)];
          let tx = b.x - a.x, ty = b.y - a.y;
          const len = Math.hypot(tx, ty) || 1; tx /= len; ty /= len;
          const w = Math.max(1.1, p.w * Math.sqrt(p.v0 / Math.max(p.v0, Math.hypot(p.vx, p.vy)))) / 2;
          left.push(`${(p.x - ty * w).toFixed(1)} ${(p.y + tx * w).toFixed(1)}`);
          right.push(`${(p.x + ty * w).toFixed(1)} ${(p.y - tx * w).toFixed(1)}`);
          glint.push(`${(p.x - ty * w * .45).toFixed(1)} ${(p.y + tx * w * .45).toFixed(1)}`);
        });
        body += `M${left.join('L')}L${right.reverse().join('L')}Z`;
        shine += `M${glint.join('L')}`;
      }
      run = [];
    };
    parcels.forEach(p => { if (run.length && p.born - run[run.length - 1].born > .05) flush(false); run.push(p); });
    flush(flowing);
    streamPath.setAttribute('d', body);
    shinePath.setAttribute('d', shine);
  }
  function foamShape(top, base) {
    let d = `M80 ${base.toFixed(1)}V${top.toFixed(1)}`;
    for (let x = 80; x <= 260; x += 6) {
      const bump = impact.amp * Math.exp(-(((x - impact.x) / 15) ** 2));
      const ripple = (Math.sin(x * .32 + pourTime * 3.2) + 1) * 1.4 + (Math.sin(x * .9 - pourTime * 5) + 1) * .6;
      d += `L${x} ${(top - bump - ripple).toFixed(1)}`;
    }
    return `${d}V${base.toFixed(1)}Z`;
  }
  function drawPour(flowing) {
    const beerY = levelY(pour.liquid), foamY = beerY - pour.foam * GLASS_H;
    beerRect.setAttribute('y', beerY.toFixed(1)); beerRect.setAttribute('height', (GLASS_BOTTOM - beerY + 2).toFixed(1));
    beerClip.setAttribute('y', beerY.toFixed(1)); beerClip.setAttribute('height', (GLASS_BOTTOM - beerY + 6).toFixed(1));
    foamPath.setAttribute('d', pour.foam > .004 ? foamShape(foamY, beerY + 1) : '');
    pourBottle.setAttribute('transform', `translate(${P.x} ${P.y}) rotate(${pour.angle.toFixed(2)})`);
    streamShapes(flowing);
    const rx = pour.spilled > .002 ? Math.min(70, 16 + pour.spilled * 900) : 0;
    puddle.setAttribute('rx', rx.toFixed(1)); puddle.setAttribute('ry', (rx * .12).toFixed(1));
    levelTag.setAttribute('transform', `translate(4 ${Math.max(GLASS_TOP + 4, beerY).toFixed(1)})`);
    levelTag.classList.toggle('on', pour.liquid > .015);
    levelText.textContent = `${Math.round(pour.liquid * GLASS_ML)} ml`;
  }
  function updateFeedback(pouring) {
    const l = pour.liquid;
    const state = pour.overflowed ? 'spilt' : l > .84 ? 'over' : l >= .77 ? 'on' : l >= .66 ? 'near' : '';
    if (state !== lineState) {
      if (state === 'on' && pouring && navigator.userActivation?.hasBeenActive !== false) navigator.vibrate?.(30);
      lineState = state;
      fillLine.setAttribute('class', `fill-line ${state === 'spilt' ? 'over' : state}`);
      fillLabel.textContent = {spilt:'overflow!', over:'over the line', on:'bas! on the line', near:'almost…', '':'fill line'}[state];
    }
    let text;
    if (pour.done) text = '';
    else if (pourTime - lastSpillAt < .6) text = 'Arre! Aim for the glass.';
    else if (pour.foam > .19) text = 'Itna jhaag! Pause and let the foam settle.';
    else if (state === 'over') text = 'Over the line. Serve it, or pour another.';
    else if (state === 'on') text = pouring ? 'Bas! Stop pouring, you’re on the line.' : 'On the line. Let it settle, then serve.';
    else if (state === 'near') text = 'Aaram se. Nearly at the line.';
    else if (pouring) text = 'Keep pouring…';
    else text = l > .01 ? 'Lift the bottle again to top up.' : 'Lift the bottle by its base to pour.';
    if (text !== statusText) { statusText = text; pourStatus.textContent = text; }
  }
  function pourLoop(now) {
    const dt = Math.min(.05, (now - pourClock) / 1000 || .016);
    pourClock = now; pourTime += dt;
    const target = pour.done ? REST : pour.holding ? HOLD_TILT : pour.target;
    pour.angle += (target - pour.angle) * (1 - Math.exp(-dt * (dragging !== null ? 16 : 9)));
    const flow = pour.done ? 0 : flowAt(pour.angle);
    const glug = smooth((flow - .55) / .35);
    const fe = flow * (1 - .22 * glug * (.5 + .5 * Math.sin(pourTime * Math.PI * 11)));
    if (fe > .005) { emitParcel(fe, dt); pourHint.classList.add('gone'); }
    impact.landing *= Math.exp(-dt * 10);
    stepParcels(dt);
    impact.amp += ((impact.landing > .02 ? 3 + 9 * impact.landing : 0) - impact.amp) * (1 - Math.exp(-dt * 7));
    const settled = pour.foam > .05 ? (pour.foam - .05) * (1 - Math.exp(-dt / 1.5)) : pour.foam * (1 - Math.exp(-dt / 40));
    pour.foam -= settled; pour.liquid += settled * .2;
    if (!pour.done && pour.liquid + pour.foam >= 1) overflow();
    drawPour(fe > .005);
    updateFeedback(fe > .005 || parcels.length > 0);
    pourSound(pour.liquid + pour.foam * .5);
    serveButton.disabled = pour.done || pour.holding || dragging !== null || parcels.length > 0 || pour.liquid < .15;
    const active = Math.abs(target - pour.angle) > .1 || flow > 0 || parcels.length || drops.length || impact.amp > .05 || (pour.foam > .052 && !pour.done);
    pourFrame = active ? requestAnimationFrame(pourLoop) : 0;
  }
  function runPour() { if (!pourFrame) { pourClock = performance.now(); pourFrame = requestAnimationFrame(pourLoop); } }
  function showPourResult(title, gloss, body, finished) {
    pourResult.innerHTML = `<strong>${title}${gloss ? ` <span class="gloss">${gloss}</span>` : ''}</strong><p>${body}</p>${finished ? '<button class="text-link" data-pour-reset>Pour another <span aria-hidden="true">↻</span></button>' : ''}`;
    pourResult.classList.toggle('finished', finished);
    if (finished) $('[data-pour-reset]', pourResult).addEventListener('click', resetPour);
  }
  function finishPour() {
    pour.done = true; pour.holding = false; pour.target = REST; dragging = null;
    holdButton.classList.remove('is-pouring'); pourStage.classList.remove('dragging');
    holdButton.disabled = true; serveButton.disabled = true;
    updateFeedback(false); runPour();
  }
  function overflow() {
    pour.overflowed = true;
    finishPour();
    spill.classList.add('on');
    showPourResult('Arre, overflow!', '', 'The foam ran over the rim. Wipe the table and pour again.', true);
  }
  function servePour() {
    if (pour.done || pour.liquid < .15) return;
    const foamMiss = Math.max(0, .08 - pour.foam, pour.foam - .16);
    const score = Math.round(clamp(100 - Math.abs(pour.liquid - FILL_LINE) * 250 - foamMiss * 350 - pour.spilled * 400, 0, 100));
    finishPour();
    if (pour.liquid < .66) showPourResult('Bas itna?', 'That’s it?', `${score}/100. Fill the glass up to the line before you serve.`, true);
    else if (pour.foam > .18) showPourResult('Itna jhaag?', 'So much foam?', `${score}/100. Pause between pours so the head can settle.`, true);
    else if (pour.foam < .06) showPourResult('Thoda jhaag bhi.', 'Some foam too.', `${score}/100. Finish with a short, steep pour to raise a head.`, true);
    else if (pour.spilled > .03) showPourResult('Table pe bhi?', 'On the table too?', `${score}/100. Keep the stream inside the glass.`, true);
    else if (score >= 88) showPourResult('Ekdum perfect!', 'Absolutely perfect!', `${score}/100. Cold, clear and two fingers of foam. Cheers!`, true);
    else showPourResult('Sahi hai.', 'Nicely done.', `${score}/100. A good pour. Get closer to the line for full marks.`, true);
    if (score >= 88) { const r = pourStage.getBoundingClientRect(); burst(r.left + r.width * .37, r.top + r.height * .42, 18); }
  }
  function resetPour() {
    Object.assign(pour, {liquid:0, foam:0, spilled:0, holding:false, done:false, overflowed:false, target:REST});
    parcels.length = 0; drops.splice(0).forEach(d => d.el.remove());
    spill.classList.remove('on');
    holdButton.disabled = false;
    showPourResult('Glass ready.', '', 'Tip: tilt gently to fill, then finish with a short, steep pour for the foam.', false);
    drawPour(false); updateFeedback(false); runPour();
    holdButton.focus({preventScroll:true});
  }

  // Lifting the bottle: its body points from the neck towards the pointer, clamped between resting and fully tipped.
  function aimBottle(e) {
    const pt = pourSvg.createSVGPoint(); pt.x = e.clientX; pt.y = e.clientY;
    const p = pt.matrixTransform(pourSvg.getScreenCTM().inverse());
    let angle = Math.atan2(-(p.x - P.x), p.y - P.y) * 180 / Math.PI;
    if (angle > 90) angle -= 360;
    pour.target = clamp(angle, MAX_TILT, REST);
  }
  pourBottle.addEventListener('pointerdown', e => {
    if (pour.done || e.button !== 0) return;
    e.preventDefault();
    try { pourBottle.setPointerCapture(e.pointerId); } catch (err) {}
    dragging = e.pointerId;
    pourStage.classList.add('dragging');
    ensurePourAudio(); aimBottle(e); runPour();
  });
  pourBottle.addEventListener('pointermove', e => { if (dragging === e.pointerId) { aimBottle(e); runPour(); } });
  const releaseBottle = e => { if (dragging !== e.pointerId) return; dragging = null; pour.target = REST; pourStage.classList.remove('dragging'); runPour(); };
  ['pointerup', 'pointercancel', 'lostpointercapture'].forEach(type => pourBottle.addEventListener(type, releaseBottle));

  const startPour = () => { if (pour.done) return; pour.holding = true; holdButton.classList.add('is-pouring'); ensurePourAudio(); runPour(); };
  const stopPour = () => { if (!pour.holding) return; pour.holding = false; holdButton.classList.remove('is-pouring'); runPour(); };
  holdButton.addEventListener('pointerdown', e => { if (e.button !== 0) return; e.preventDefault(); try { holdButton.setPointerCapture(e.pointerId); } catch (err) {} startPour(); });
  ['pointerup', 'pointercancel', 'lostpointercapture', 'blur'].forEach(type => holdButton.addEventListener(type, stopPour));
  holdButton.addEventListener('keydown', e => { if (e.key === ' ' || e.key === 'Enter') { e.preventDefault(); if (!e.repeat) startPour(); } });
  holdButton.addEventListener('keyup', e => { if (e.key === ' ' || e.key === 'Enter') { e.preventDefault(); stopPour(); } });
  holdButton.addEventListener('contextmenu', e => e.preventDefault());
  window.addEventListener('blur', () => { stopPour(); if (dragging !== null) { dragging = null; pour.target = REST; pourStage.classList.remove('dragging'); runPour(); } });
  serveButton.addEventListener('click', servePour);
  showPourResult('Glass ready.', '', 'Tip: tilt gently to fill, then finish with a short, steep pour for the foam.', false);
  drawPour(false); updateFeedback(false);

  // Good company: a departures board drives a railway station sign in the city's own script.
  const stations = [
    {id:'delhi', city:'New Delhi', lines:[['नई दिल्ली','hi'],['NEW DELHI','en']], short:'Chole bhature', dish:'Chole bhature & papdi chaat', beer:'remix-lemongrass', text:'Spiced chickpeas, puffed bhature and tangy chaat. Lemongrass and ginger over ice meet flavours Delhi already loves.'},
    {id:'mumbai', city:'Mumbai', lines:[['मुंबई','mr'],['MUMBAI','en']], short:'Vada pav', dish:'Vada pav & monsoon bhajiyas', beer:'verve-cranberry', text:'Rain on the window and a hot vada pav in hand. Bright cranberry keeps the evening going long after the fryer cools.'},
    {id:'kolkata', city:'Kolkata', lines:[['কলকাতা','bn'],['कोलकाता','hi'],['KOLKATA','en']], short:'Kosha mangsho', dish:'Kosha mangsho & fish fry', beer:'dazzle-gold', text:'Slow-cooked mutton, dark with mustard oil and spice, wants a golden, special-edition pour with plenty of character.'},
    {id:'chennai', city:'Chennai', lines:[['சென்னை','ta'],['चेन्नई','hi'],['CHENNAI','en']], short:'Chettinad chicken', dish:'Chettinad pepper chicken', beer:'triple-distilled', text:'Black pepper, curry leaves and roasted spice. A clean, triple-distilled pour keeps the heat in check.'},
    {id:'hyderabad', city:'Hyderabad', lines:[['హైదరాబాద్','te'],['हैदराबाद','hi'],['HYDERABAD','en']], short:'Apollo fish', dish:'Apollo fish & chilli chicken', beer:'premium-grain', text:'Fiery, fried and made for sharing. The original Saksham Moments has the body to stand up to it.'},
    {id:'bengaluru', city:'Bengaluru', lines:[['ಬೆಂಗಳೂರು','kn'],['बेंगलुरु','hi'],['BENGALURU','en']], short:'Pandi curry', dish:'Kodava pandi curry', beer:'remix-green-apple', text:'Tangy Kodava pork curry next to India\u2019s best-selling vodka, distilled by Radico Khaitan in Rampur.'},
    {id:'kochi', city:'Kochi', lines:[['കൊച്ചി','ml'],['कोच्चि','hi'],['KOCHI','en']], short:'Karimeen', dish:'Karimeen pollichathu', beer:'verve-orange', text:'Pearl spot fish, rubbed with masala and roasted in banana leaf. Pour something bright, citrusy and long.'},
    {id:'goa', city:'Goa', lines:[['गोंय','kok'],['गोवा','hi'],['GOA','en']], short:'Prawn balchão', dish:'Prawn balchão & rava fish fry', beer:'remix-green-apple', text:'Hot, tangy prawns at a beach shack at sunset. A crisp green apple pour matches the mood.'}
  ];
  const departureList = $('#departures'), stationPanel = $('#station-panel'), stationSign = $('#station-sign'), stationPlate = $('#station-plate');
  departureList.innerHTML = stations.map((s, i) => `<button class="departure" role="tab" id="dep-${s.id}" aria-controls="station-panel" aria-selected="${i === 0}" tabindex="${i === 0 ? 0 : -1}"><span class="dep-pf">${i + 1}</span><span class="dep-city">${s.city}</span><span class="dep-dish">${s.short}</span></button>`).join('');
  const departures = $$('.departure', departureList);
  let flipTimer = 0;
  function renderStation(s) {
    const p = productById(s.beer);
    stationSign.innerHTML = s.lines.map(([text, lang]) => `<span class="sign-line" lang="${lang}">${text}</span>`).join('');
    stationSign.dataset.lines = String(s.lines.length);
    stationPlate.innerHTML = `<div class="plate-bottle">${bottle(p)}</div><div class="plate-copy"><small>Aaj ka special</small><strong>${s.dish}</strong><p>${s.text}</p><p class="plate-pair">Pair it with <b>Saksham Moments ${p.name}</b></p><button class="text-link" data-station-beer="${p.id}">See this bottle <span>↗</span></button></div>`;
    $('[data-station-beer]', stationPlate).addEventListener('click', () => showProduct(p.id));
  }
  function selectStation(index, focus) {
    departures.forEach((tab, i) => { tab.setAttribute('aria-selected', String(i === index)); tab.tabIndex = i === index ? 0 : -1; });
    stationPanel.setAttribute('aria-labelledby', departures[index].id);
    if (focus) departures[index].focus();
    const swap = () => renderStation(stations[index]);
    clearTimeout(flipTimer);
    if (reducedMotion || !stationSign.animate) { swap(); return; }
    // One flip: the sign turns edge-on, its text changes while hidden, then it swings back past level and settles.
    stationSign.getAnimations().forEach(a => a.cancel());
    stationSign.animate([{transform:'rotateX(0deg)', easing:'cubic-bezier(.5,0,1,.6)'}, {transform:'rotateX(88deg)', offset:.27}, {transform:'rotateX(-75deg)', offset:.2701, easing:'ease-out'}, {transform:'rotateX(9deg)', offset:.8}, {transform:'rotateX(0deg)'}], {duration:630});
    flipTimer = setTimeout(swap, 170);
  }
  departures.forEach((tab, i) => {
    tab.addEventListener('click', () => { if (tab.getAttribute('aria-selected') !== 'true') selectStation(i, false); });
    tab.addEventListener('keydown', e => {
      const keys = {ArrowDown:i + 1, ArrowRight:i + 1, ArrowUp:i - 1, ArrowLeft:i - 1, Home:0, End:departures.length - 1};
      if (!(e.key in keys)) return;
      e.preventDefault();
      selectStation((keys[e.key] + departures.length) % departures.length, true);
    });
  });
  stationPanel.setAttribute('aria-labelledby', departures[0].id);
  renderStation(stations[0]);

  // Horn OK Please: a two-tone truck horn, synthesised on demand.
  function honk() {
    try {
      audio = audio || new (window.AudioContext || window.webkitAudioContext)();
      const t = audio.currentTime, out = audio.createGain(), tone = audio.createBiquadFilter();
      tone.type = 'lowpass'; tone.frequency.value = 1500;
      tone.connect(out); out.connect(audio.destination);
      [370, 466].forEach(f => { const o = audio.createOscillator(); o.type = 'sawtooth'; o.frequency.value = f; o.connect(tone); o.start(t); o.stop(t + .9); });
      const g = out.gain;
      g.setValueAtTime(.0001, t);
      g.exponentialRampToValueAtTime(.09, t + .02); g.setValueAtTime(.09, t + .15); g.exponentialRampToValueAtTime(.0001, t + .2);
      g.setValueAtTime(.0001, t + .27); g.exponentialRampToValueAtTime(.09, t + .3); g.setValueAtTime(.09, t + .74); g.exponentialRampToValueAtTime(.0001, t + .86);
    } catch (err) {}
  }
  const truck = $('.truck');
  $('#horn').addEventListener('click', () => {
    honk();
    if (reducedMotion) return;
    truck.classList.remove('honking'); void truck.offsetWidth; truck.classList.add('honking');
  });

  // One scroll coordinator handles the bottle, its move into the lineup, and rail progress.
  const heroBottle = $('#hero-bottle'), header = $('.header'), railProgress = $('.rail-progress span');
  const range = $('#range'), details = $('#beer'), story = $('#story'), notes = $('.notes');
  const scenes = $$('.scene[data-page]');
  let metricsDirty = true, metrics = {}, ticking = false;
  function readMetrics() {
    const y = window.scrollY;
    const mobile = window.innerWidth <= 700;
    metrics = {
      h:window.innerHeight,w:window.innerWidth,mobile,rail:mobile?38:54,
      details:details.getBoundingClientRect().top+y,story:story.getBoundingClientRect().top+y,
      notes:notes.getBoundingClientRect().top+y,range:range.getBoundingClientRect().top+y,
      bottleH:heroBottle.offsetHeight,
      sectionPositions:scenes.map(s=>({top:s.getBoundingClientRect().top+y,page:s.dataset.page})),
      maxScroll:Math.max(1,document.documentElement.scrollHeight-window.innerHeight)
    };
    metricsDirty=false;
  }
  function render() {
    ticking=false;
    if(metricsDirty)readMetrics();
    const m=metrics,y=window.scrollY;
    const first=smooth(y/(m.details*.75));
    let x=0,dy=0,scale=1,rotation=lerp(14,0,first);
    if(m.mobile){
      const inStory=smooth((y-m.story+m.h*.25)/(m.h*.75));
      const inNotes=smooth((y-m.notes+m.h*.3)/(m.h*.7));
      x=lerp((m.w-m.rail)*.235,-(m.w-m.rail)*.20,inStory)*first;
      x=lerp(x,0,inNotes);
      dy=lerp(-m.h*.12,0,inStory)*first;
      scale=lerp(1,.77,first);
      rotation=lerp(rotation,lerp(-3,5,inNotes),inStory);
    }
    const entry=smooth((y-m.range+m.h*.7)/(m.h*.65));
    let opacity=1;
    const flagship=products[0].id,destination=$(`[data-product="${flagship}"] .product-visual`);
    const targetProduct=$(`[data-product="${flagship}"]`);
    if(entry>0){
      if(!targetProduct.hidden){
        const r=destination.getBoundingClientRect();
        const centerX=m.rail+(m.w-m.rail)/2;
        const centerY=m.h*(m.mobile?.46:.5);
        x=lerp(x,r.left+r.width/2-centerX,entry);
        dy=lerp(dy,r.top+r.height/2-centerY,entry);
        scale=lerp(scale,r.height/m.bottleH,entry);
        rotation=lerp(rotation,0,entry);
      }
      opacity=1-smooth((entry-.88)/.12);
    }
    if(y>m.range+m.h)opacity=0;
    heroBottle.style.transform=`translate3d(${x.toFixed(2)}px,${dy.toFixed(2)}px,0) rotate(${rotation.toFixed(2)}deg) scale(${scale.toFixed(4)})`;
    heroBottle.style.opacity=String(opacity);
    destination.style.opacity=entry>0&&entry<.99?String(1-opacity):'1';
    header.classList.toggle('scrolled',y>60);
    railProgress.style.transform=`scaleY(${clamp(y/m.maxScroll)})`;
    let page='01';for(const s of m.sectionPositions){if(y+m.h*.4>=s.top)page=s.page;}
    $('.page-number').textContent=page;
  }
  function requestTick(){if(!ticking){ticking=true;requestAnimationFrame(render);}}
  let resizeFrame = 0;
  window.addEventListener('scroll',requestTick,{passive:true});
  window.addEventListener('resize',()=>{
    metricsDirty=true;requestTick();
    cancelAnimationFrame(resizeFrame);
    resizeFrame=requestAnimationFrame(()=>{ if(toran&&Math.abs(toran.clientWidth-(strands.length?parseFloat(toran.querySelector('svg').getAttribute('width')):0))>2)buildToran(); buildLadi(); });
  },{passive:true});
  window.addEventListener('load',()=>{metricsDirty=true;requestTick();});
  document.fonts.ready.then(()=>{metricsDirty=true;requestTick();});
  motionQuery.addEventListener('change',e=>{reducedMotion=e.matches;requestTick();});
  if('IntersectionObserver' in window){
    const observer=new IntersectionObserver(entries=>{entries.forEach(entry=>{if(entry.isIntersecting){entry.target.classList.add('visible');observer.unobserve(entry.target);}});},{threshold:.08,rootMargin:'0px 0px 25px 0px'});
    $$('.reveal').forEach(el=>observer.observe(el));
    new IntersectionObserver(([entry])=>pourSection.classList.toggle('in-view',entry.isIntersecting)).observe(pourSection);
    document.documentElement.classList.add('js');
  }
  requestTick();
})();
