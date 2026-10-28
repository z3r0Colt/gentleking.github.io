(function () {
  'use strict';
  var form = document.getElementById('site-search');
  if (!form) return;
  var field = document.getElementById('search-query');
  var status = document.getElementById('search-status');
  var results = document.getElementById('search-results');
  var pending;
  var stop = new Set('a an the i me my we our you your is am are was be been to of for in on and or but it do does can how what why when with that this have has keep keeps into same'.split(' '));
  var synonyms = { saved: 'assurance salvation', salvation: 'gospel grace', doubt: 'assurance afraid', doubts: 'assurance afraid', falling: 'sin repentance', porn: 'sin temptation', pornography: 'sin temptation', grieving: 'grief sorrow', died: 'death grief', depressed: 'depression', praying: 'prayer', pray: 'prayer', reading: 'bible scripture', calvinism: 'election grace', afraid: 'fear assurance' };
  function normalize(text) { return text.toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim(); }
  function tokens(text) { return normalize(text).split(/\s+/).filter(function (t) { return t && !stop.has(t); }); }
  function run(query) {
    results.replaceChildren();
    if (!query.trim()) { status.textContent = 'Enter a subject or question to search.'; return; }
    status.textContent = 'Searching…';
    if (!pending) pending = fetch('assets/search-index.json').then(function (r) { if (!r.ok) throw new Error('index'); return r.json(); }).catch(function (e) { pending = null; throw e; });
    pending.then(function (records) {
      if (field.value.trim() !== query.trim()) return;
      var original = tokens(query);
      var expanded = tokens(original.map(function (t) { return synonyms[t] || ''; }).join(' '));
      if (!original.length) { status.textContent = 'Try a subject such as prayer or assurance.'; return; }
      var ranked = records.map(function (record) {
        var title = normalize(record.title + ' ' + record.section);
        var body = normalize(record.text);
        function has(text, term) { return (' ' + text + ' ').includes(' ' + term + ' ') || (' ' + text + ' ').includes(' ' + term + 's '); }
        var score = 0;
        original.forEach(function (t) { score += has(title, t) ? 12 : has(body, t) ? 3 : 0; });
        expanded.forEach(function (t) { score += has(title, t) ? 4 : has(body, t) ? 1 : 0; });
        if (original.includes('sin') && /struggle|assurance-remaining-sin|guide-repentance/.test(record.url)) score += 10;
        return { record: record, score: score };
      }).filter(function (x) { return x.score > 0; }).sort(function (a, b) { return b.score - a.score; });
      var seen = new Set();
      ranked = ranked.filter(function (x) { var page = x.record.url.split('#')[0]; if (seen.has(page)) return false; seen.add(page); return true; });
      status.textContent = ranked.length ? ranked.length + ' pages found. Showing the closest matches.' : 'No matches. Try fewer words, or browse Find Help and Guides.';
      ranked.slice(0, 20).forEach(function (hit) {
        var record = hit.record;
        var article = document.createElement('article'); article.className = 'search-result';
        var h = document.createElement('h2'); var a = document.createElement('a'); a.href = record.url;
        a.textContent = record.title + (record.section && record.section !== record.title ? ' · ' + record.section : ''); h.appendChild(a);
        var p = document.createElement('p'); var text = record.text;
        var positions = original.map(function (t) { return text.toLowerCase().indexOf(t); }).filter(function (i) { return i >= 0; });
        var start = positions.length ? Math.max(0, Math.min.apply(null, positions) - 65) : 0;
        if (start) { var space = text.indexOf(' ', start); if (space >= 0) start = space + 1; }
        p.textContent = (start ? '…' : '') + text.slice(start, start + 240) + (text.length > start + 240 ? '…' : '');
        article.append(h, p); results.appendChild(article);
      });
    }).catch(function () { status.textContent = 'Search could not load. Please try again, or browse Find Help and Guides.'; });
  }
  form.addEventListener('submit', function (e) { e.preventDefault(); var query = field.value.trim(); history.replaceState(null, '', 'search.html?q=' + encodeURIComponent(query)); run(query); });
  field.value = new URLSearchParams(location.search).get('q') || '';
  if (field.value) run(field.value.trim());
})();
