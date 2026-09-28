/* Gentle King. The finder for the free library on the Resources page.
   Every book is already in the page, shelf by shelf. This adds the search box,
   the filters, and the list of books read lately, and it only hides and shows
   what is there. Nothing here is required for the list to be read. */
(function () {
  'use strict';

  var doc = document;
  var finder = doc.getElementById('lib-finder');
  var shelvesBox = doc.getElementById('lib-shelves');
  if (!finder || !shelvesBox) { return; }

  var $ = function (id) { return doc.getElementById(id); };
  var input = $('lib-q');
  var catSelect = $('lib-cat');
  var bookSelect = $('lib-book');
  var tradSelect = $('lib-trad');
  var startBox = $('lib-start');
  var topicsBox = $('lib-topics');
  var countText = $('lib-count');
  var clearBtn = $('lib-clear');
  var emptyNote = $('lib-empty');
  var shelves = Array.prototype.slice.call(shelvesBox.querySelectorAll('.lib-shelf'));
  var chips = Array.prototype.slice.call(finder.querySelectorAll('.lib-topic'));

  var NEW_TESTAMENT = ['Matthew', 'Mark', 'Luke', 'John', 'Acts', 'Romans', '1 Corinthians',
    '2 Corinthians', 'Galatians', 'Ephesians', 'Philippians', 'Colossians', '1 Thessalonians',
    '2 Thessalonians', '1 Timothy', '2 Timothy', 'Titus', 'Philemon', 'Hebrews', 'James',
    '1 Peter', '2 Peter', '1 John', '2 John', '3 John', 'Jude', 'Revelation'];

  // letters with accents match the same letters without them
  function fold(text) {
    return text.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[’']/g, '');
  }

  function text(el, sel) {
    var found = el.querySelector(sel);
    return found ? found.textContent : '';
  }

  /* ------------------------------------------------------------ the books */

  var items = [];
  shelves.forEach(function (shelf) {
    var cat = shelf.getAttribute('data-cat');
    Array.prototype.forEach.call(shelf.querySelectorAll('.lib-item'), function (li) {
      var tagLine = li.querySelector('.lib-tags');
      var topics = tagLine ? tagLine.textContent.split(' · ') : [];
      // the topic line becomes a row of buttons, each one a filter
      if (tagLine) {
        tagLine.textContent = '';
        topics.forEach(function (t) {
          var b = doc.createElement('button');
          b.type = 'button';
          b.className = 'lib-tag';
          b.textContent = t;
          b.setAttribute('aria-label', 'Show every book on ' + t);
          b.addEventListener('click', function () { chooseTopic(t, true, true); });
          tagLine.appendChild(b);
        });
      }
      items.push({
        el: li,
        shelf: shelf,
        cat: cat,
        topics: topics,
        books: (li.getAttribute('data-books') || '').split('|').filter(Boolean),
        trad: text(li, '.lib-trad'),
        start: !!li.querySelector('.lib-start'),
        // the title without its badges, and what the volumes hold without the
        // words on their buttons, so a search for "read" or "start" finds books
        // that are about those things
        words: fold([text(li, '.lib-title > span'), text(li, '.lib-by'), text(li, '.lib-blurb'),
          text(li, '.lib-passage'), topics.join(' '),
          Array.prototype.map.call(li.querySelectorAll('.lib-vol-name, .lib-vol-contents'),
            function (n) { return n.textContent; }).join(' ')].join(' ')),
        list: li.parentNode,
        index: items.length
      });
    });
  });
  var total = items.length;

  /* ---------------------------------------------------------- the filters */

  var state = { q: '', topic: '', cat: '', book: '', trad: '', start: false };
  var PARAMS = { q: 'q', topic: 'topic', cat: 'kind', book: 'bible', trad: 'tradition', start: 'start' };
  var userOpen = [];

  // one letter matches nearly every book, so a search starts at two
  function query() {
    return state.q.length >= 2 ? state.q : '';
  }

  function active() {
    return !!(query() || state.topic || state.cat || state.book || state.trad || state.start);
  }

  function matchesBook(item, book) {
    if (item.books.indexOf(book) !== -1) { return true; }
    // a Bible holds every book, so it would match them all and tell the reader nothing
    if (item.cat === 'Bibles') { return false; }
    var testament = NEW_TESTAMENT.indexOf(book) !== -1 ? 'New Testament' : 'Old Testament';
    return item.books.indexOf('Whole Bible') !== -1 || item.books.indexOf(testament) !== -1;
  }

  function matches(item, words) {
    if (state.cat && item.cat !== state.cat) { return false; }
    if (state.topic && item.topics.indexOf(state.topic) === -1) { return false; }
    if (state.trad && item.trad !== state.trad) { return false; }
    if (state.start && !item.start) { return false; }
    if (state.book && !matchesBook(item, state.book)) { return false; }
    for (var i = 0; i < words.length; i++) {
      if (item.words.indexOf(words[i]) === -1) { return false; }
    }
    return true;
  }

  function apply(fromUser) {
    var words = fold(query()).split(/\s+/).filter(Boolean);
    var filtering = active();
    var shown = 0;
    var perShelf = new Map();

    items.forEach(function (item) {
      var ok = !filtering || matches(item, words);
      item.el.hidden = !ok;
      if (ok) {
        shown++;
        perShelf.set(item.shelf, (perShelf.get(item.shelf) || 0) + 1);
      }
    });

    arrange();

    shelves.forEach(function (shelf) {
      var n = perShelf.get(shelf) || 0;
      var count = shelf.querySelector('.lib-shelf-count');
      var all = count.getAttribute('data-total');
      count.textContent = filtering ? n + ' of ' + all : all;
      shelf.hidden = filtering && n === 0;
      shelf.open = filtering ? n > 0 : userOpen.indexOf(shelf) !== -1;
    });

    countText.textContent = !filtering ? 'All ' + total + ' books'
      : shown === 1 ? 'One book found' : shown + ' books found';
    emptyNote.hidden = !(filtering && shown === 0);
    clearBtn.hidden = !filtering;

    chips.forEach(function (chip) {
      chip.setAttribute('aria-pressed', String(chip.getAttribute('data-topic') === state.topic));
    });

    if (fromUser) { saveToAddress(); }
  }

  // the address carries the search, so a reader can share it or come back to it
  function saveToAddress() {
    var params = new URLSearchParams();
    Object.keys(PARAMS).forEach(function (key) {
      if (state[key]) { params.set(PARAMS[key], key === 'start' ? '1' : state[key]); }
    });
    var query = params.toString();
    var url = location.pathname + (query ? '?' + query : '') + (location.hash || '');
    try { history.replaceState(null, '', url); } catch (e) { /* a file opened from disk */ }
  }

  function readAddress() {
    var params = new URLSearchParams(location.search);
    state.q = params.get(PARAMS.q) || '';
    state.topic = params.get(PARAMS.topic) || '';
    state.cat = params.get(PARAMS.cat) || '';
    state.book = params.get(PARAMS.book) || '';
    state.trad = params.get(PARAMS.trad) || '';
    state.start = params.get(PARAMS.start) === '1';
    // only a value the page offers counts
    [[catSelect, 'cat'], [bookSelect, 'book'], [tradSelect, 'trad']].forEach(function (pair) {
      var ok = Array.prototype.some.call(pair[0].options, function (o) { return o.value === state[pair[1]]; });
      if (!ok) { state[pair[1]] = ''; }
    });
    if (!chips.some(function (c) { return c.getAttribute('data-topic') === state.topic; })) { state.topic = ''; }
    input.value = state.q;
    catSelect.value = state.cat;
    bookSelect.value = state.book;
    tradSelect.value = state.trad;
    startBox.checked = state.start;
  }

  // With a book of the Bible chosen, the books on that book itself come before
  // the ones on the whole Bible. The list itself is put in that order, not
  // only drawn so, so the keyboard and a screen reader meet them in it too.
  var arranged = false;
  function arrange() {
    if (!state.book && !arranged) { return; }
    var first = [], rest = [];
    items.forEach(function (item) {
      (state.book && item.books.indexOf(state.book) !== -1 ? first : rest).push(item);
    });
    first.concat(rest).forEach(function (item) { item.list.appendChild(item.el); });
    arranged = !!state.book;
  }

  // A chip turns its topic on and off. A topic on a book always turns it on,
  // and brings the reader up to the chip, so it can be seen and turned off.
  function chooseTopic(topic, fromBook, set) {
    state.topic = set || state.topic !== topic ? topic : '';
    if (state.topic) { topicsBox.open = true; }
    apply(true);
    if (fromBook) {
      finder.scrollIntoView({ block: 'start', behavior: 'smooth' });
      var chip = chips.filter(function (c) { return c.getAttribute('data-topic') === topic; })[0];
      if (chip) { chip.focus({ preventScroll: true }); }
    }
  }

  var typing = null;
  input.addEventListener('input', function () {
    clearTimeout(typing);
    typing = setTimeout(function () { state.q = input.value.trim(); apply(true); }, 150);
  });
  input.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && input.value) { input.value = ''; state.q = ''; apply(true); }
  });
  catSelect.addEventListener('change', function () { state.cat = catSelect.value; apply(true); });
  bookSelect.addEventListener('change', function () { state.book = bookSelect.value; apply(true); });
  tradSelect.addEventListener('change', function () { state.trad = tradSelect.value; apply(true); });
  startBox.addEventListener('change', function () { state.start = startBox.checked; apply(true); });
  chips.forEach(function (chip) {
    chip.addEventListener('click', function () { chooseTopic(chip.getAttribute('data-topic'), false); });
  });
  clearBtn.addEventListener('click', function () {
    state = { q: '', topic: '', cat: '', book: '', trad: '', start: false };
    input.value = ''; catSelect.value = ''; bookSelect.value = ''; tradSelect.value = ''; startBox.checked = false;
    apply(true);
    input.focus();
  });

  // remember which shelves the reader opened by hand, so clearing a search
  // puts the shelves back the way the reader had them. A search opens and
  // shuts shelves too, but only while it is on, so those are not counted.
  shelves.forEach(function (shelf) {
    shelf.addEventListener('toggle', function () {
      if (active()) { return; }
      var at = userOpen.indexOf(shelf);
      if (shelf.open && at === -1) { userOpen.push(shelf); }
      if (!shelf.open && at !== -1) { userOpen.splice(at, 1); }
    });
  });

  /* ------------------------------------------------- going to one book */

  // a link to one book, from a card or from another book, opens its shelf first
  function reveal(id) {
    var target = id && doc.getElementById(id);
    if (!target || !shelvesBox.contains(target)) { return; }
    if (target.hidden || (target.closest('.lib-shelf') || {}).hidden) {
      clearBtn.click();
    }
    for (var d = target.closest('details'); d; d = d.parentElement.closest('details')) {
      if (d.classList.contains('lib-shelf') && userOpen.indexOf(d) === -1) { userOpen.push(d); }
      d.open = true;
    }
  }

  doc.addEventListener('click', function (e) {
    var a = e.target.closest && e.target.closest('a[href^="#book-"], a[href^="#shelf-"]');
    if (a) { reveal(a.getAttribute('href').slice(1)); }
  });
  window.addEventListener('hashchange', function () {
    reveal(location.hash.slice(1));
    var el = doc.getElementById(location.hash.slice(1));
    if (el) { el.scrollIntoView(); }
  });

  /* ------------------------------------------------- books read lately */

  var READ_KEY = 'gk-recent';
  var VALID = /^library\/[a-z0-9][a-z0-9\-\/]*\.epub$/;

  function showRecent() {
    var box = $('lib-recent');
    var list = [];
    try { list = JSON.parse(localStorage.getItem(READ_KEY) || '[]'); } catch (e) { list = []; }
    list = (Array.isArray(list) ? list : []).filter(function (r) {
      return r && typeof r.book === 'string' && VALID.test(r.book) && typeof r.title === 'string';
    }).slice(0, 3);
    box.textContent = '';
    if (!list.length) { box.hidden = true; return; }

    var head = doc.createElement('p');
    head.className = 'lib-recent-head';
    head.appendChild(doc.createTextNode('Pick up where you left off'));
    var forget = doc.createElement('button');
    forget.type = 'button';
    forget.className = 'lib-forget';
    forget.textContent = 'Forget these';
    forget.addEventListener('click', function () {
      try { localStorage.removeItem(READ_KEY); } catch (e) { /* nothing to do */ }
      showRecent();
    });
    head.appendChild(forget);

    var ol = doc.createElement('ol');
    ol.className = 'lib-recent-list';
    list.forEach(function (r) {
      var li = doc.createElement('li');
      var a = doc.createElement('a');
      a.href = 'resources/read.html?book=' + r.book;
      a.textContent = r.title;
      var note = doc.createElement('span');
      var pct = Math.max(0, Math.min(100, Math.round(Number(r.pct) || 0)));
      note.textContent = [r.author, pct ? pct + '% read' : 'just begun'].filter(Boolean).join(' · ');
      li.appendChild(a);
      li.appendChild(note);
      ol.appendChild(li);
    });
    box.appendChild(head);
    box.appendChild(ol);
    box.hidden = false;
  }

  /* --------------------------------------------------------------- start */

  if (window.matchMedia && window.matchMedia('(min-width: 48rem)').matches) { topicsBox.open = true; }
  readAddress();
  if (state.topic) { topicsBox.open = true; }
  apply(false);
  showRecent();
  if (location.hash) { reveal(location.hash.slice(1)); }
  // coming back to the page from the reader, the list may have changed
  window.addEventListener('pageshow', function (e) { if (e.persisted) { showRecent(); } });
})();
