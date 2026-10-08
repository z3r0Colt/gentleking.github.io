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

  /* The icon in the header, and on a phone the row at the foot of the menu,
     which says in words what it will do and so needs no label. The icon's
     label says what a press will do, from the first moment. */
  var toggle = doc.querySelector('.theme-toggle');
  function labelToggle() {
    if (toggle) { toggle.setAttribute('aria-label', currentTheme() === 'dark' ? 'Switch to light' : 'Switch to dark'); }
  }
  Array.prototype.forEach.call(doc.querySelectorAll('.theme-toggle, .menu-theme'), function (button) {
    button.addEventListener('click', function () {
      var next = currentTheme() === 'dark' ? 'light' : 'dark';
      setTheme(next);
      storeTheme(next);
      labelToggle();
    });
  });
  setTheme(readStoredTheme());
  labelToggle();

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
      if (event.target.closest('a')) { closeNav(); }
    });
    doc.addEventListener('keydown', function (event) {
      if (event.key === 'Escape' && nav.getAttribute('data-open') === 'true') {
        closeNav();
        navToggle.focus();
      }
    });
    window.addEventListener('resize', function () {
      if (window.innerWidth > 1024) { closeNav(); }
    });
  }

  /* ----------------------------------------------------------- tools menu */

  /* Tools opens below its button on a wide screen. Escape, a click elsewhere,
     or moving focus out of it closes it again. On a phone site.css shows the
     list open inside the menu, and the button is not drawn. */
  var group = doc.querySelector('.nav-group');
  var groupBtn = group ? group.querySelector('.nav-group-btn') : null;

  function setGroup(open) {
    if (groupBtn) { groupBtn.setAttribute('aria-expanded', open ? 'true' : 'false'); }
  }

  if (group && groupBtn) {
    groupBtn.addEventListener('click', function () {
      setGroup(groupBtn.getAttribute('aria-expanded') !== 'true');
    });
    group.addEventListener('keydown', function (event) {
      if (event.key === 'Escape' && groupBtn.getAttribute('aria-expanded') === 'true') {
        event.stopPropagation();
        setGroup(false);
        groupBtn.focus();
      }
    });
    group.addEventListener('focusout', function (event) {
      if (!group.contains(event.relatedTarget)) { setGroup(false); }
    });
    doc.addEventListener('click', function (event) {
      if (!group.contains(event.target)) { setGroup(false); }
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

  /* Built from the page's sections, the same list build.py writes in. */
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
      var h2 = sec.querySelector('h2');
      // A heading that is a verse gives a shorter name for the list in data-toc.
      if (h2) { headings.push({ id: sec.id, text: h2.getAttribute('data-toc') || h2.textContent.trim(), el: sec }); }
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

  buildToc();

  /* -------------------------------------------------------- moved anchors */

  /* Comfort and Apologetics were once one long page each. A link from before
     they were divided, such as comfort.html#grief, is sent on to the page
     that holds that part now. The page carries the map. */
  var moved = doc.getElementById('moved');

  function followMoved() {
    if (!moved) { return; }
    var id = '';
    try { id = decodeURIComponent(window.location.hash.slice(1)); } catch (e) { return; }
    if (!id || doc.getElementById(id)) { return; }
    var map = {};
    try { map = JSON.parse(moved.textContent); } catch (e) { return; }
    if (map[id]) { window.location.replace(map[id]); }
  }

  followMoved();
  window.addEventListener('hashchange', followMoved);

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
