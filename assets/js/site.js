/* Gentle King. Small, dependency free, progressive.
   Nothing here is required for the site to be readable. */
(function () {
  'use strict';

  var doc = document;
  var root = doc.documentElement;

  /* ---------------------------------------------------------------- theme */

  var THEME_KEY = 'gk-theme';

  function readStoredTheme() {
    try { return localStorage.getItem(THEME_KEY); } catch (e) { return null; }
  }

  function storeTheme(value) {
    try {
      if (value) { localStorage.setItem(THEME_KEY, value); }
      else { localStorage.removeItem(THEME_KEY); }
    } catch (e) { /* private mode, blocked storage, nothing to do */ }
  }

  function systemPrefersDark() {
    return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  }

  function currentTheme() {
    return root.getAttribute('data-theme') || (systemPrefersDark() ? 'dark' : 'light');
  }

  function setTheme(value) {
    if (value) { root.setAttribute('data-theme', value); }
    else { root.removeAttribute('data-theme'); }
    var meta = doc.querySelector('meta[name="theme-color"]');
    if (meta) { meta.setAttribute('content', currentTheme() === 'dark' ? '#151310' : '#fbf8f2'); }
  }

  var toggle = doc.querySelector('.theme-toggle');
  if (toggle) {
    toggle.addEventListener('click', function () {
      var next = currentTheme() === 'dark' ? 'light' : 'dark';
      setTheme(next);
      storeTheme(next);
      toggle.setAttribute('aria-label', next === 'dark' ? 'Switch to light' : 'Switch to dark');
    });
  }
  setTheme(readStoredTheme());

  /* ------------------------------------------------------------ mobile nav */

  var navToggle = doc.querySelector('.nav-toggle');
  var nav = doc.getElementById('primary-nav');

  function closeNav() {
    if (!nav || !navToggle) { return; }
    nav.setAttribute('data-open', 'false');
    navToggle.setAttribute('aria-expanded', 'false');
  }

  if (navToggle && nav) {
    navToggle.addEventListener('click', function () {
      var open = nav.getAttribute('data-open') === 'true';
      nav.setAttribute('data-open', open ? 'false' : 'true');
      navToggle.setAttribute('aria-expanded', open ? 'false' : 'true');
    });
    nav.addEventListener('click', function (event) {
      if (event.target.tagName === 'A') { closeNav(); }
    });
    doc.addEventListener('keydown', function (event) {
      if (event.key === 'Escape') { closeNav(); }
    });
    window.addEventListener('resize', function () {
      if (window.innerWidth > 992) { closeNav(); }
    });
  }

  /* ----------------------------------------------------- sticky header line */

  var header = doc.querySelector('.site-header');
  var toTop = doc.querySelector('.to-top');

  function onScroll() {
    var y = window.pageYOffset || doc.documentElement.scrollTop;
    if (header) { header.classList.toggle('is-stuck', y > 8); }
    if (toTop) { toTop.classList.toggle('is-visible', y > 900); }
  }

  var ticking = false;
  window.addEventListener('scroll', function () {
    if (ticking) { return; }
    ticking = true;
    window.requestAnimationFrame(function () { onScroll(); ticking = false; });
  }, { passive: true });
  onScroll();

  if (toTop) {
    toTop.addEventListener('click', function () {
      var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      window.scrollTo({ top: 0, behavior: reduce ? 'auto' : 'smooth' });
    });
  }

  /* ------------------------------------------------------------ on this page */

  var mount = doc.querySelector('[data-toc]');
  var main = doc.querySelector('main');
  var tocObserver = null;

  /* Built from the sections that are actually showing, so a page that changes
     what it shows can build it again. */
  function buildToc() {
    if (!mount || !main) { return; }
    if (tocObserver) { tocObserver.disconnect(); tocObserver = null; }
    mount.textContent = '';
    mount.className = '';
    mount.removeAttribute('aria-label');

    var headings = [];
    var sections = main.querySelectorAll('section.section[id]');

    for (var i = 0; i < sections.length; i++) {
      var sec = sections[i];
      if (sec.hasAttribute('data-half') && !sec.classList.contains('is-shown')) { continue; }
      var h2 = sec.querySelector('h2');
      if (h2) { headings.push({ id: sec.id, text: h2.textContent.trim(), el: sec }); }
    }

    if (headings.length < 3) { return; }

    var title = doc.createElement('p');
    title.className = 'toc-title';
    title.textContent = 'On this page';

    var list = doc.createElement('ol');
    var links = [];

    headings.forEach(function (h) {
      var li = doc.createElement('li');
      var a = doc.createElement('a');
      a.href = '#' + h.id;
      a.textContent = h.text;
      li.appendChild(a);
      list.appendChild(li);
      links.push(a);
    });

    mount.className = 'toc';
    mount.setAttribute('aria-label', 'On this page');
    mount.appendChild(title);
    mount.appendChild(list);

    if ('IntersectionObserver' in window) {
      tocObserver = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) { return; }
          links.forEach(function (a) {
            a.classList.toggle('is-active', a.getAttribute('href') === '#' + entry.target.id);
          });
        });
      }, { rootMargin: '-15% 0px -70% 0px', threshold: 0 });

      headings.forEach(function (h) { tocObserver.observe(h.el); });
    }
  }

  /* ----------------------------------------------------- one half at a time */

  /* A page can split into halves, each section marked with data-half. Nothing
     in either half shows until the reader chooses, then only the chosen half
     does. The address follows the choice, so back, reload, and a shared link
     all land in the right half. */
  var halfSections = doc.querySelectorAll('[data-half]');
  var choosers = doc.querySelectorAll('[data-choose]');
  var currentHalf = null;

  function hashId() {
    try { return decodeURIComponent(window.location.hash.slice(1)); } catch (e) { return ''; }
  }

  function halfOf(id) {
    var el = id ? doc.getElementById(id) : null;
    var owner = el ? el.closest('[data-half]') : null;
    return owner ? owner.getAttribute('data-half') : null;
  }

  function showHalf(name) {
    currentHalf = name;
    for (var i = 0; i < halfSections.length; i++) {
      halfSections[i].classList.toggle('is-shown', halfSections[i].getAttribute('data-half') === name);
    }
    for (var j = 0; j < choosers.length; j++) {
      if (choosers[j].getAttribute('data-choose') === name) {
        choosers[j].setAttribute('aria-current', 'true');
      } else {
        choosers[j].removeAttribute('aria-current');
      }
    }
    buildToc();
  }

  function goTo(id, smooth, moveFocus) {
    var el = doc.getElementById(id);
    if (!el) { return; }
    var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    var jump = !smooth || reduce;
    /* The stylesheet makes all scrolling smooth, and 'auto' obeys it, so a
       shared link would glide down the whole page. Jump straight there. */
    if (jump) { root.style.scrollBehavior = 'auto'; }
    el.scrollIntoView({ behavior: jump ? 'auto' : 'smooth', block: 'start' });
    if (jump) { root.style.scrollBehavior = ''; }
    if (moveFocus) {
      var heading = el.querySelector('h2') || el;
      heading.setAttribute('tabindex', '-1');
      heading.focus({ preventScroll: true });
    }
  }

  /* Bring the page into line with the address. A link inside one half that
     points into the other switches halves here, since the browser cannot
     scroll to a section it cannot see. */
  function syncToHash() {
    var id = hashId();
    if (!id) { showHalf(null); return; }
    var half = halfOf(id);
    if (half && half !== currentHalf) {
      showHalf(half);
      goTo(id, true, true);
    }
  }

  if (halfSections.length) {
    var startId = hashId();
    var startHalf = halfOf(startId);
    showHalf(startHalf);
    if (startHalf) { goTo(startId, false, false); }

    for (var c = 0; c < choosers.length; c++) {
      choosers[c].addEventListener('click', function (event) {
        var name = this.getAttribute('data-choose');
        var href = this.getAttribute('href') || '';
        var target = href.charAt(0) === '#' && halfOf(href.slice(1)) === name ? href.slice(1) : name;
        event.preventDefault();
        if (hashId() !== target && window.history && history.pushState) {
          history.pushState(null, '', '#' + target);
        }
        showHalf(name);
        goTo(target, true, true);
      });
    }

    window.addEventListener('popstate', syncToHash);
    window.addEventListener('hashchange', syncToHash);
  } else {
    buildToc();
  }

  /* ------------------------------------------------------- email addresses */

  /* Written in two halves in the HTML so a scraper reading the page source does
     not get a usable address. With scripts off the text still reads correctly,
     it just is not clickable. */
  var mails = doc.querySelectorAll('.mail[data-user][data-domain]');
  for (var k = 0; k < mails.length; k++) {
    var span = mails[k];
    var address = span.getAttribute('data-user') + '@' + span.getAttribute('data-domain');
    var link = doc.createElement('a');
    link.href = 'mailto:' + address;
    link.textContent = address;
    span.textContent = '';
    span.appendChild(link);
  }

  /* --------------------------------------------------- mark the current page */

  var here = window.location.pathname.split('/').pop() || 'index.html';
  var navLinks = doc.querySelectorAll('#primary-nav a');
  for (var j = 0; j < navLinks.length; j++) {
    if (navLinks[j].getAttribute('href') === here) {
      navLinks[j].setAttribute('aria-current', 'page');
    }
  }
})();
