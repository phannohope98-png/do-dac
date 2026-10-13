/* Solar Journey: anonymous website interaction analytics. No form values or replay. */
(() => {
  'use strict';
  const script = document.currentScript;
  const endpoint = script?.dataset.endpoint;
  const site = script?.dataset.site || 'website';
  if (!endpoint || window.SolarAnalytics) return;
  const blocked = navigator.globalPrivacyControl || navigator.doNotTrack === '1';
  let enabled = false, queue = [], timer, session, lastActivity = Date.now(), active = 0;
  let page = location.pathname, milestones = new Set(), lastTick = Date.now(), hiddenReported = false;
  const uuid = () => crypto.randomUUID();
  const safePath = value => { try { const u = new URL(value, location.href); return u.origin === location.origin ? u.pathname.slice(0, 300) : u.hostname; } catch { return ''; } };
  const label = value => String(value || '').replace(/[^\p{L}\p{N}_ .-]/gu, '').slice(0, 80);
  const storage = { get(k) { try { return sessionStorage.getItem(k); } catch { return null; } }, set(k,v) { try { sessionStorage.setItem(k,v); } catch {} } };
  function identify() {
    const old = storage.get('sj-session');
    try { session = JSON.parse(old); } catch { session = null; }
    if (!session || Date.now() - session.at > 1800000) session = { id: uuid(), at: Date.now() };
    session.at = Date.now(); storage.set('sj-session', JSON.stringify(session));
  }
  function event(type, data = {}) {
    if (!enabled) return;
    if (Date.now() - session.at > 1800000) identify();
    session.at = Date.now(); storage.set('sj-session', JSON.stringify(session));
    queue.push({ id: uuid(), session: session.id, type, page, at: new Date().toISOString(), data });
    if (queue.length >= 15) flush();
  }
  async function flush() {
    if (!enabled || !queue.length) return;
    const batch = queue.splice(0, 30);
    const body = JSON.stringify({ site, events: batch });
    try {
      const result = await fetch(endpoint, { method: 'POST', body, headers: {'Content-Type':'text/plain'}, credentials:'omit', keepalive:true });
      if (!result.ok) throw new Error('collector');
    } catch { queue = [...batch, ...queue].slice(-100); }
  }
  function view() {
    page = location.pathname; milestones = new Set(); active = 0; hiddenReported = false;
    const params = new URLSearchParams(location.search);
    const browser = /Edg\//.test(navigator.userAgent) ? 'Edge' : /Firefox\//.test(navigator.userAgent) ? 'Firefox' : /Chrome\//.test(navigator.userAgent) ? 'Chrome' : /Safari\//.test(navigator.userAgent) ? 'Safari' : 'Other';
    event('page_view', {referrer: document.referrer ? safePath(document.referrer) : '', device: /Mobi|Android/i.test(navigator.userAgent) ? 'Mobile' : 'Desktop', browser, source:label(params.get('utm_source')), medium:label(params.get('utm_medium')), campaign:label(params.get('utm_campaign'))});
  }
  function engagement() { if (active > 0) { event('engagement', {seconds:Math.round(active / 1000)}); active = 0; } }
  function grant() {
    if (enabled || blocked) return;
    enabled = true; identify(); lastTick = lastActivity = Date.now(); view();
    timer = setInterval(() => { const now = Date.now(); if (!document.hidden && now - lastActivity < 60000) active += Math.min(now-lastTick, 5000); lastTick = now; engagement(); flush(); }, 5000);
  }
  function revoke() { enabled = false; clearInterval(timer); queue = []; storage.set('sj-session',''); storage.set('sj-disabled','1'); }
  window.SolarAnalytics = { start() { storage.set('sj-disabled',''); grant(); }, stop:revoke, grantConsent:grant, revokeConsent:revoke, track(name) { event('goal', {name:label(name)}); } };
  ['pointerdown','keydown','scroll','touchstart'].forEach(type => addEventListener(type, () => { lastActivity = Date.now(); }, {passive:true}));
  document.addEventListener('click', e => {
    const el = e.target.closest?.('a,button,[data-analytics]'); if (!el || el.id === 'sj-yes' || el.id === 'sj-no' || el.closest('[data-analytics-ignore]')) return;
    const href = el.getAttribute('href') || '';
    const target = /^(tel:|mailto:)/i.test(href) ? href.split(':')[0] : safePath(href);
    event('click', {name:label(el.dataset.analytics) || (target === 'tel' ? 'Bấm gọi điện' : target === 'mailto' ? 'Bấm email' : el.tagName === 'A' ? 'link' : 'button'), target:href ? target : ''});
    if (el.dataset.analyticsGoal) event('goal', {name:label(el.dataset.analyticsGoal)});
  });
  document.addEventListener('submit', e => { if (e.target.dataset.analytics) event('form_submit', {name:label(e.target.dataset.analytics)}); });
  addEventListener('scroll', () => { const total = document.documentElement.scrollHeight - innerHeight; const depth = total > 0 ? Math.round(scrollY / total * 100) : 100; [25,50,75,100].forEach(percent => { if (depth >= percent && !milestones.has(percent)) {milestones.add(percent); event('scroll', {percent});} }); }, {passive:true});
  function hide() { engagement(); if (!hiddenReported) { event('page_hidden'); hiddenReported = true; } }
  document.addEventListener('visibilitychange', () => { if (document.hidden && enabled) { hide(); flush(); } else {lastTick = Date.now(); hiddenReported = false;} });
  addEventListener('pagehide', () => { if (!enabled) return; hide(); const batch = queue.splice(0,30); if (batch.length && !navigator.sendBeacon(endpoint, JSON.stringify({site,events:batch}))) queue.unshift(...batch); });
  let previous = location.pathname;
  function route() { if (location.pathname !== previous) {engagement(); flush(); previous = location.pathname; view();} }
  ['pushState','replaceState'].forEach(name => { const original = history[name]; history[name] = function(...args) { const result = original.apply(this,args); route(); return result; }; });
  addEventListener('popstate',route);
  if (script.dataset.consent === 'external' || blocked || storage.get('sj-disabled') === '1') return;
  grant();
})();
