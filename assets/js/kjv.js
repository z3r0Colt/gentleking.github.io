/* Gentle King's KJV reader. Scripture stays beside the article. */
(function () {
  'use strict';
  var booksPromise;
  var bookCache = {};
  var dialog;
  var dialogRequest = 0;
  var trigger;

  function json(path) {
    return fetch(path).then(function (response) {
      if (!response.ok) { throw new Error('Could not load Scripture.'); }
      return response.json();
    });
  }
  function books() {
    if (!booksPromise) {
      booksPromise = json('assets/kjv/books.json').catch(function (error) {
        booksPromise = null;
        throw error;
      });
    }
    return booksPromise;
  }
  function bookText(index) {
    if (!bookCache[index]) {
      bookCache[index] = json('assets/kjv/' + String(index + 1).padStart(2, '0') + '.json').catch(function (error) {
        delete bookCache[index];
        throw error;
      });
    }
    return bookCache[index];
  }
  function parse(reference, metadata) {
    var match = /^(.+?)\s+(\d{1,3})(?::(\d{1,3})(?:\s*[-\u2013]\s*(\d{1,3}))?)?$/.exec(reference.trim());
    if (!match) { throw new Error('Choose a valid Bible reference.'); }
    var name = match[1].toLowerCase();
    if (name === 'psalm') { name = 'psalms'; }
    var index = metadata.findIndex(function (item) { return item.name.toLowerCase() === name; });
    var chapter = Number(match[2]);
    var start = match[3] ? Number(match[3]) : null;
    var end = match[4] ? Number(match[4]) : start;
    if (index < 0 || chapter < 1 || chapter > metadata[index].chapters.length ||
        (start !== null && (start < 1 || end < start || end > metadata[index].chapters[chapter - 1]))) {
      throw new Error('Choose a valid Bible reference.');
    }
    return { index: index, chapter: chapter, start: start, end: end };
  }
  function referenceFor(place, metadata) {
    return metadata[place.index].name + ' ' + place.chapter +
      (place.start === null ? '' : ':' + place.start + (place.end === place.start ? '' : '-' + place.end));
  }
  function render(host, data, place, selectedOnly) {
    host.replaceChildren();
    var heading = document.createElement('h2');
    heading.textContent = data.name + ' ' + place.chapter;
    host.appendChild(heading);
    var chapter = data.chapters[place.chapter - 1];
    chapter.forEach(function (text, index) {
      var number = index + 1;
      var selected = place.start !== null && number >= place.start && number <= place.end;
      if (selectedOnly && place.start !== null && !selected) { return; }
      var line = document.createElement('p');
      line.id = (selectedOnly ? 'kjv-dialog-verse-' : 'kjv-verse-') + number;
      if (selected) { line.className = 'kjv-selected'; }
      var verse = document.createElement('sup');
      verse.className = 'kjv-verse-number';
      verse.textContent = number + ' ';
      line.append(verse, document.createTextNode(text));
      host.appendChild(line);
    });
  }
  function ensureDialog() {
    if (dialog) { return; }
    dialog = document.createElement('dialog');
    dialog.className = 'kjv-dialog';
    dialog.setAttribute('aria-labelledby', 'kjv-dialog-title');
    dialog.innerHTML = '<div class="kjv-dialog-head"><h2 id="kjv-dialog-title">King James Bible</h2>' +
      '<button class="btn" type="button" autofocus>Close</button></div>' +
      '<p class="kjv-dialog-status" role="status"></p><div class="kjv-passage"></div>' +
      '<p class="kjv-dialog-foot"><a href="bible.html">Read the full chapter</a></p>';
    document.body.appendChild(dialog);
    dialog.querySelector('button').addEventListener('click', function () { dialog.close(); });
    dialog.addEventListener('close', function () {
      dialogRequest += 1;
      document.body.classList.remove('kjv-open');
      if (trigger) { trigger.focus({ preventScroll: true }); }
    });
    dialog.addEventListener('click', function (event) {
      var rect = dialog.getBoundingClientRect();
      if (event.target === dialog && (event.clientX < rect.left || event.clientX > rect.right ||
          event.clientY < rect.top || event.clientY > rect.bottom)) { dialog.close(); }
    });
  }
  document.addEventListener('click', function (event) {
    var link = event.target.closest('a.source-ref[href^="bible.html?ref="]');
    if (!link || event.defaultPrevented || event.button !== 0 || event.ctrlKey || event.metaKey ||
        event.shiftKey || event.altKey || !window.HTMLDialogElement ||
        !HTMLDialogElement.prototype.showModal) { return; }
    event.preventDefault();
    ensureDialog();
    trigger = link;
    var request = ++dialogRequest;
    var reference = new URL(link.href).searchParams.get('ref');
    var status = dialog.querySelector('[role="status"]');
    var passage = dialog.querySelector('.kjv-passage');
    var fullChapter = dialog.querySelector('a');
    dialog.querySelector('h2').textContent = reference + ' (KJV)';
    passage.replaceChildren();
    status.textContent = 'Loading Scripture.';
    fullChapter.href = link.href;
    if (!dialog.open) { dialog.showModal(); }
    document.body.classList.add('kjv-open');
    books().then(function (metadata) {
      var place = parse(reference, metadata);
      return bookText(place.index).then(function (data) {
        if (request !== dialogRequest) { return; }
        render(passage, data, place, true);
        status.textContent = '';
      });
    }).catch(function () {
      if (request === dialogRequest) {
        status.textContent = 'Scripture could not load. Close and try again, or open the full reader below.';
      }
    });
  });

  var reader = document.getElementById('kjv-reader');
  if (!reader) { return; }
  var status = document.getElementById('kjv-status');
  var passage = document.getElementById('kjv-passage');
  var form = document.getElementById('kjv-form');
  var bookSelect = document.getElementById('kjv-book');
  var chapterSelect = document.getElementById('kjv-chapter');
  var navigation = document.getElementById('kjv-navigation');
  var current;
  var readerRequest = 0;
  function chapterOptions(metadata, index, selected) {
    chapterSelect.replaceChildren();
    metadata[index].chapters.forEach(function (_, i) {
      chapterSelect.add(new Option(String(i + 1), String(i + 1)));
    });
    chapterSelect.value = String(selected);
  }
  function load(reference, metadata, updateUrl) {
    var request = ++readerRequest;
    passage.replaceChildren();
    status.textContent = 'Loading Scripture.';
    navigation.hidden = true;
    var place;
    try { place = parse(reference, metadata); }
    catch (error) { status.textContent = error.message; return; }
    bookSelect.value = String(place.index);
    chapterOptions(metadata, place.index, place.chapter);
    bookText(place.index).then(function (data) {
      if (request !== readerRequest) { return; }
      current = place;
      render(passage, data, place, false);
      status.textContent = '';
      navigation.hidden = false;
      document.getElementById('kjv-previous').disabled = place.index === 0 && place.chapter === 1;
      document.getElementById('kjv-next').disabled = place.index === 65 && place.chapter === metadata[65].chapters.length;
      if (updateUrl) {
        history.pushState(null, '', 'bible.html?ref=' + encodeURIComponent(referenceFor(place, metadata)));
      }
      document.title = referenceFor(place, metadata) + ' (KJV) · Gentle King';
      if (place.start !== null) {
        document.getElementById('kjv-verse-' + place.start).scrollIntoView({ block: 'center' });
      }
    }).catch(function () {
      if (request === readerRequest) { status.textContent = 'Scripture could not load. Choose Read to try again.'; }
    });
  }
  books().then(function (metadata) {
    metadata.forEach(function (item, i) { bookSelect.add(new Option(item.name, String(i))); });
    bookSelect.addEventListener('change', function () { chapterOptions(metadata, Number(bookSelect.value), 1); });
    chapterOptions(metadata, 0, 1);
    form.hidden = false;
    form.addEventListener('submit', function (event) {
      event.preventDefault();
      load(metadata[Number(bookSelect.value)].name + ' ' + chapterSelect.value, metadata, true);
    });
    function turn(direction) {
      if (!current) { return; }
      var index = current.index;
      var chapter = current.chapter + direction;
      if (chapter < 1) { index -= 1; chapter = metadata[index].chapters.length; }
      if (chapter > metadata[index].chapters.length) { index += 1; chapter = 1; }
      load(metadata[index].name + ' ' + chapter, metadata, true);
    }
    document.getElementById('kjv-previous').addEventListener('click', function () { turn(-1); });
    document.getElementById('kjv-next').addEventListener('click', function () { turn(1); });
    function fromUrl() { load(new URL(location.href).searchParams.get('ref') || 'John 1', metadata, false); }
    window.addEventListener('popstate', fromUrl);
    fromUrl();
  }).catch(function () {
    status.textContent = 'The Bible reader could not load. Refresh to try again, or use the EPUB link below.';
  });
})();
