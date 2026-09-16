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

  if (mount && main) {
    var headings = [];
    var sections = main.querySelectorAll('section.section[id]');

    for (var i = 0; i < sections.length; i++) {
      var h2 = sections[i].querySelector('h2');
      if (h2) { headings.push({ id: sections[i].id, text: h2.textContent.trim(), el: sections[i] }); }
    }

    if (headings.length >= 3) {
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
        var observer = new IntersectionObserver(function (entries) {
          entries.forEach(function (entry) {
            if (!entry.isIntersecting) { return; }
            links.forEach(function (a) {
              a.classList.toggle('is-active', a.getAttribute('href') === '#' + entry.target.id);
            });
          });
        }, { rootMargin: '-15% 0px -70% 0px', threshold: 0 });

        headings.forEach(function (h) { observer.observe(h.el); });
      }
    }
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
