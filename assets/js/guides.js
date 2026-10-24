/* Keep the complete directory readable when scripts are unavailable. */
(function () {
  'use strict';
  var finder = document.getElementById('guide-finder');
  if (!finder) return;
  var query = document.getElementById('guide-query');
  var topic = document.getElementById('guide-topic');
  var status = document.getElementById('guide-status');
  var all = document.getElementById('guide-all');
  var groups = Array.from(document.querySelectorAll('section.section')).filter(function (s) { return s.querySelector('.paths'); });
  var rows = Array.from(document.querySelectorAll('.paths > li'));
  var expanded = Boolean(location.hash);
  var featured = ['guide-prayer.html', 'guide-bible-reading.html', 'guide-repentance.html', 'guide-reading-scripture.html', 'guide-find-a-church.html', 'guide-marriage.html', 'guide-parenting.html', 'guide-work.html'];
  function update() {
    var terms = query.value.toLowerCase().trim().split(/\s+/).filter(Boolean);
    var matches = rows.filter(function (row) {
      return (topic.value === 'all' || row.dataset.topic === topic.value) && terms.every(function (term) { return row.textContent.toLowerCase().includes(term); });
    });
    var filtering = terms.length || topic.value !== 'all';
    rows.forEach(function (row) { row.hidden = !matches.includes(row) || (!expanded && !filtering && !featured.includes(row.querySelector('a').getAttribute('href'))); });
    groups.forEach(function (group) { group.hidden = !Array.from(group.querySelectorAll('.paths > li')).some(function (row) { return !row.hidden; }); if (group.previousElementSibling && group.previousElementSibling.matches('hr')) group.previousElementSibling.hidden = group.hidden; });
    status.textContent = matches.length ? ((expanded || filtering ? matches.length : Math.min(8, matches.length)) + ' of ' + matches.length + ' guides shown') : 'No guides match. Try another word or topic.';
    all.hidden = Boolean(expanded || filtering || matches.length <= 8);
  }
  finder.hidden = false;
  query.addEventListener('input', update);
  topic.addEventListener('change', update);
  all.addEventListener('click', function () { expanded = true; update(); });
  window.addEventListener('hashchange', function () { expanded = true; query.value = ''; topic.value = 'all'; update(); var target = document.getElementById(location.hash.slice(1)); if (target) target.scrollIntoView(); });
  update();
})();
