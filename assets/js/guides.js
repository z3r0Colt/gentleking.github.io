/* Every guide is present in native, open-by-default topic groups. */
(function () {
  'use strict';
  var finder = document.getElementById('guide-finder');
  if (!finder) return;
  var query = document.getElementById('guide-query');
  var topic = document.getElementById('guide-topic');
  var status = document.getElementById('guide-status');
  var groups = Array.from(document.querySelectorAll('.guide-group'));
  var rows = Array.from(document.querySelectorAll('.guide-group .paths > li'));
  var filtering = false;
  var previousOpen = new Map();
  function update() {
    var terms = query.value.toLowerCase().trim().split(/\s+/).filter(Boolean);
    var active = Boolean(terms.length || topic.value !== 'all');
    if (active && !filtering) groups.forEach(function (group) { previousOpen.set(group, group.open); });
    var count = 0;
    rows.forEach(function (row) {
      var match = (topic.value === 'all' || row.dataset.topic === topic.value) && terms.every(function (term) { return row.textContent.toLowerCase().includes(term); });
      row.hidden = !match;
      if (match) count++;
    });
    groups.forEach(function (group) {
      var matches = Array.from(group.querySelectorAll('.paths > li')).filter(function (row) { return !row.hidden; }).length;
      group.hidden = matches === 0;
      group.querySelector('[data-guide-count]').textContent = matches + (matches === 1 ? ' guide' : ' guides');
      if (active && matches) group.open = true;
      else if (!active && filtering) group.open = previousOpen.get(group) !== false;
    });
    status.textContent = active ? (count ? count + ' of ' + rows.length + ' guides match' : 'No guides match. Try another word or topic.') : rows.length + ' guides in ' + groups.length + ' topics';
    filtering = active;
  }
  function followTopicLink() {
    query.value = ''; topic.value = 'all'; update();
    var id;
    try { id = decodeURIComponent(location.hash.slice(1)); } catch (e) { return; }
    var target = document.getElementById(id);
    if (!target) return;
    var group = target.matches('.guide-group') ? target : target.closest('.guide-group') || target.nextElementSibling;
    if (group && group.matches('.guide-group')) group.open = true;
    target.scrollIntoView({block: 'start'});
  }
  finder.hidden = false;
  query.addEventListener('input', update);
  topic.addEventListener('change', update);
  document.getElementById('guide-expand').addEventListener('click', function () { groups.forEach(function (group) { if (!group.hidden) group.open = true; }); });
  document.getElementById('guide-collapse').addEventListener('click', function () { groups.forEach(function (group) { if (!group.hidden) group.open = false; }); });
  window.addEventListener('hashchange', followTopicLink);
  update();
  if (location.hash) followTopicLink();
})();
