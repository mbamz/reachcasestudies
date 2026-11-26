/* Reach Social free TikTok Shop market analysis: form handler + homepage exit-intent pop-up.
 * ClickUp 1k5bm0zwfm3. Port of amzadvisers.com ExitIntent.jsx + MarketAnalysisHandler.jsx.
 *
 * Loaded on reachsocial.co/ (injected by the reach-ma-popup Cloudflare Worker, homepage only) and on
 * /free-market-analysis/ (this repo). Every form[data-reach-ma] posts to the n8n workflow
 * "Reach Market Analysis Opt-in". Form (Mike 2026-11-26): work email + TikTok Shop name or link,
 * or the "no TikTok Shop yet" box (pre-launch brands are accepted).
 *
 * Pop-up rules, same as AMZ: opens when the pointer leaves the top of the window after 8s (desktop)
 * or on a fast scroll back up after 40% of the page and 15s (touch). Never more than once per 14 days
 * (rs_ei_seen), never after a request (rs_ma_done), never for visitors arriving from an email or a
 * booking link. Cookies only: no localStorage, so a blocked store cannot break it.
 * Kill switch: delete the reach-ma-popup Worker route (the WordPress page itself is untouched).
 */
(function () {
  if (window.__reachMA) return;
  window.__reachMA = true;
  var ENDPOINT = 'https://amzadvisers.app.n8n.cloud/webhook/reach-market-analysis-request';
  var doc = document;

  function cookie(n) { var m = doc.cookie.match(new RegExp('(?:^|; )' + n + '=([^;]*)')); return m ? decodeURIComponent(m[1]) : ''; }
  function setCookie(n, v, days) { doc.cookie = n + '=' + encodeURIComponent(v) + '; max-age=' + Math.round(days * 86400) + '; path=/; SameSite=Lax'; }

  // First / last touch, kept in cookies (a light version of amzadvisers.com's amzTouch).
  function nowTouch() {
    var q = new URLSearchParams(location.search), ref = doc.referrer || '';
    var ext = ref && ref.indexOf(location.hostname) === -1 ? ref : '';
    return { source: q.get('utm_source') || (ext ? ext.replace(/^https?:\/\/(www\.)?/, '').split('/')[0] : ''),
             medium: q.get('utm_medium') || (ext ? 'referral' : ''), campaign: q.get('utm_campaign') || '',
             content: q.get('utm_content') || '', landing: location.pathname, referrer: ext, at: new Date().toISOString() };
  }
  var t0 = nowTouch();
  if (!cookie('rs_ft')) setCookie('rs_ft', JSON.stringify(t0), 365);
  if (t0.source || !cookie('rs_lt')) setCookie('rs_lt', JSON.stringify(t0), 30);
  function touch(n) { try { return JSON.parse(cookie(n)) || {}; } catch (e) { return {}; } }

  function say(form, msg) { var el = form.querySelector('.rsma-status'); if (el) el.textContent = msg; }

  doc.addEventListener('change', function (e) {
    if (!e.target.matches || !e.target.matches('form[data-reach-ma] input[name=prelaunch]')) return;
    var shop = e.target.form.elements.shop;
    if (shop) { shop.disabled = e.target.checked; shop.required = !e.target.checked; shop.removeAttribute('aria-invalid'); if (e.target.checked) shop.value = ''; }
    e.target.form.classList.toggle('rsma-pre', e.target.checked);
  });

  doc.addEventListener('submit', function (e) {
    var form = e.target.closest && e.target.closest('form[data-reach-ma]');
    if (!form) return;
    e.preventDefault();
    var f = function (n) { var el = form.elements[n]; return el ? String(el.value || '').trim() : ''; };
    var email = f('email'), shop = f('shop');
    var pre = form.elements.prelaunch && form.elements.prelaunch.checked;
    var bad = function (n, msg) { var el = form.elements[n]; if (el) { el.setAttribute('aria-invalid', 'true'); el.focus(); } say(form, msg); };
    ['email', 'shop'].forEach(function (n) { if (form.elements[n]) form.elements[n].removeAttribute('aria-invalid'); });
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email)) return bad('email', 'Please enter a valid work email address.');
    if (!shop && !pre) return bad('shop', 'Please enter your TikTok Shop name or link, or tick the box if you do not have a shop yet.');
    var btn = form.querySelector('button[type=submit]');
    if (btn) { btn.disabled = true; btn.dataset.label = btn.textContent; btn.textContent = 'Sending...'; }
    var body = { email: email, name: f('name'), shop: shop, prelaunch: pre ? 'true' : 'false', website: f('website'),
                 form_name: form.getAttribute('data-reach-ma'), page: location.pathname, hutk: cookie('hubspotutk') };
    [['ft', touch('rs_ft')], ['lt', touch('rs_lt')]].forEach(function (p) {
      ['source', 'medium', 'campaign', 'content', 'landing', 'referrer', 'at'].forEach(function (x) { body[p[0] + '_' + x] = p[1][x] || ''; });
    });
    fetch(ENDPOINT, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
      .then(function (r) {
        if (!r.ok) throw new Error('http ' + r.status);
        setCookie('rs_ma_done', '1', 365);  // never offer the pop-up again to someone who already asked
        form.style.display = 'none';
        var done = form.parentNode.querySelector('.rsma-done');
        if (done) done.style.display = 'block';
        if (window.gtag) window.gtag('event', 'market_analysis_request', { placement: body.form_name });
      })
      .catch(function () {
        say(form, 'Something went wrong. Please try again, or email hello@reachsocial.co.');
        if (btn) { btn.disabled = false; btn.textContent = btn.dataset.label || 'Send'; }
      });
  });

  // ---------- the pop-up: homepage only ----------
  if (location.pathname !== '/') return;
  if (cookie('rs_ma_done') || cookie('rs_ei_seen') || /utm_(medium|source)=(email|booking)/i.test(location.search)) return;

  var css = '' +
    '.rsma-ov{position:fixed;inset:0;z-index:2147483000;background:rgba(0,0,0,.78);display:none;align-items:center;justify-content:center;padding:16px}' +
    '.rsma-ov.open{display:flex}' +
    '.rsma-card{position:relative;width:100%;max-width:460px;max-height:calc(100vh - 32px);overflow:auto;background:#0E0E0E;border:1px solid rgba(197,248,95,.45);border-radius:16px;padding:30px 26px 24px;color:#B8B8BC;font-family:Poppins,"DM Sans",Arial,sans-serif;box-shadow:0 24px 70px rgba(0,0,0,.6)}' +
    '.rsma-x{position:absolute;top:10px;right:12px;background:none;border:0;color:#8A8F98;font-size:26px;line-height:1;cursor:pointer;padding:4px}' +
    '.rsma-kick{display:block;font-family:"DM Sans",Arial,sans-serif;font-weight:700;font-size:11px;letter-spacing:.2em;text-transform:uppercase;color:#C5F85F;margin-bottom:8px}' +
    '.rsma-card h2{font-family:"DM Sans",Arial,sans-serif;font-weight:800;color:#fff;font-size:26px;line-height:1.15;margin:0 0 10px}' +
    '.rsma-card h2 em{color:#C5F85F;font-style:italic}' +
    '.rsma-card p{font-size:14.5px;line-height:1.55;margin:0 0 6px}' +
    '.rsma-card label{display:block;color:#fff;font-size:13px;font-weight:600;margin:14px 0 6px}' +
    '.rsma-card .req{color:#C5F85F;margin-left:2px}.rsma-card form.rsma-pre .req-shop{visibility:hidden}.rsma-card input[aria-invalid=true]{border-color:#FF6B6B}' +
    '.rsma-card input[type=email],.rsma-card input[type=text]{width:100%;box-sizing:border-box;padding:12px 14px;border-radius:10px;border:1px solid #2A2A2E;background:#000;color:#fff;font:inherit;font-size:15px}' +
    '.rsma-card input:disabled{opacity:.45}' +
    '.rsma-card .rsma-chk{display:flex;gap:8px;align-items:center;font-weight:400;color:#B8B8BC;margin-top:10px}' +
    '.rsma-card .hp{position:absolute;left:-9999px;width:1px;height:1px;overflow:hidden}' +
    '.rsma-go{width:100%;margin-top:18px;background:#C5F85F;color:#0A0A0A;border:0;border-radius:999px;padding:14px 20px;font-family:"DM Sans",Arial,sans-serif;font-weight:800;font-size:14px;letter-spacing:.02em;text-transform:uppercase;cursor:pointer}' +
    '.rsma-go:hover{background:#9FC84E}.rsma-go:disabled{opacity:.6;cursor:default}' +
    '.rsma-micro{display:block;text-align:center;font-size:12px;color:#8A8F98;margin-top:10px}' +
    '.rsma-status{color:#ff9a9a;font-size:13.5px;min-height:1em;margin:10px 0 0}' +
    '.rsma-done{display:none}.rsma-done h2{margin-top:4px}';
  var html = '' +
    '<div class="rsma-card">' +
    '<button class="rsma-x" type="button" aria-label="Close">&times;</button>' +
    '<div>' +
    '<form data-reach-ma="homepage-exit-intent" novalidate>' +
    '<span class="rsma-kick">Free · Built for your brand</span>' +
    '<h2 id="rsma-title">See where your brand <em>stands on TikTok Shop.</em></h2>' +
    '<p>Tell us your TikTok Shop. We build a market analysis from live TikTok Shop data: your category, who is taking share, and the creators and videos driving sales. A strategist walks you through it.</p>' +
    '<label for="rsma-email">Work email<span class="req" aria-hidden="true">*</span></label>' +
    '<input id="rsma-email" name="email" type="email" autocomplete="email" required>' +
    '<label for="rsma-shop">Your TikTok Shop name or link<span class="req req-shop" aria-hidden="true">*</span></label>' +
    '<input id="rsma-shop" name="shop" type="text" required placeholder="Shop name, or https://www.tiktok.com/@yourbrand">' +
    '<label class="rsma-chk"><input type="checkbox" name="prelaunch" value="true"> I don\'t have a TikTok Shop yet</label>' +
    '<div class="hp" aria-hidden="true"><input name="website" type="text" tabindex="-1" autocomplete="off"></div>' +
    '<button class="rsma-go" type="submit">Get my free analysis →</button>' +
    '<span class="rsma-micro">Free. No account access needed.</span>' +
    '<p class="rsma-status" role="status"></p>' +
    '</form>' +
    '<div class="rsma-done"><h2>We\'re on it.</h2><p>Your analysis is being built. Once a strategist has reviewed it, we\'ll email you a link to pick a time to walk through it together.</p></div>' +
    '</div></div>';

  function mount() {
    var st = doc.createElement('style'); st.textContent = css; doc.head.appendChild(st);
    var el = doc.createElement('div');
    el.className = 'rsma-ov'; el.id = 'rsma'; el.setAttribute('role', 'dialog'); el.setAttribute('aria-modal', 'true');
    el.setAttribute('aria-labelledby', 'rsma-title'); el.setAttribute('aria-hidden', 'true');
    el.innerHTML = html;
    doc.body.appendChild(el);
    var start = Date.now(), shown = false, lastFocus = null;
    function open() {
      if (shown || cookie('rs_ma_done')) return;
      shown = true; setCookie('rs_ei_seen', '1', 14); lastFocus = doc.activeElement;
      el.classList.add('open'); el.setAttribute('aria-hidden', 'false');
      var first = el.querySelector('input[type=email]'); if (first) setTimeout(function () { first.focus(); }, 50);
      if (window.gtag) window.gtag('event', 'exit_intent_shown', { site: 'reachsocial' });
    }
    function close() {
      el.classList.remove('open'); el.setAttribute('aria-hidden', 'true');
      if (lastFocus && lastFocus.focus) lastFocus.focus();
    }
    el.querySelector('.rsma-x').addEventListener('click', close);
    el.addEventListener('click', function (e) { if (e.target === el) close(); });
    doc.addEventListener('keydown', function (e) { if (e.key === 'Escape' && el.classList.contains('open')) close(); });
    doc.addEventListener('mouseout', function (e) {  // desktop: leaving through the top edge
      if (!e.relatedTarget && e.clientY <= 0 && Date.now() - start > 8000) open();
    });
    if ('ontouchstart' in window) {  // touch: a fast scroll back up after reading a good part of the page
      var maxY = 0, lastY = window.scrollY, lastT = Date.now();
      window.addEventListener('scroll', function () {
        var y = window.scrollY, t = Date.now();
        maxY = Math.max(maxY, y);
        var deep = maxY > (doc.body.scrollHeight - window.innerHeight) * 0.4;
        var fastUp = (lastY - y) > 120 && (t - lastT) < 250;
        if (deep && fastUp && t - start > 15000) open();
        lastY = y; lastT = t;
      }, { passive: true });
    }
    // test hook: reachsocial.co/?rsma=open opens it at once (never in normal traffic)
    if (/[?&]rsma=open\b/.test(location.search)) open();
  }
  if (doc.readyState === 'loading') doc.addEventListener('DOMContentLoaded', mount); else mount();
})();
