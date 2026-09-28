/* Set the page color before anything paints, so a reader who chose dark or
   sepia never sees a flash of white. The reader's own choice wins, then the
   choice made on the rest of the site, then the system's. */
(function () {
  var theme = null;
  try {
    var saved = JSON.parse(localStorage.getItem('gk-reader') || '{}');
    theme = saved.theme || localStorage.getItem('gk-theme');
  } catch (e) { /* storage blocked, fall through to the system */ }
  if (!theme) {
    theme = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }
  document.documentElement.setAttribute('data-theme', theme);
})();

/* The reader's book engine groups things with Object.groupBy and Map.groupBy,
   which Safari gained only in 17.4. These stand in for them on older phones. */
if (!Object.groupBy) {
  Object.groupBy = function (items, fn) {
    var out = Object.create(null), i = 0;
    for (var x of items) { var k = fn(x, i++); (out[k] || (out[k] = [])).push(x); }
    return out;
  };
}
if (!Map.groupBy) {
  Map.groupBy = function (items, fn) {
    var out = new Map(), i = 0;
    for (var x of items) { var k = fn(x, i++); if (!out.has(k)) { out.set(k, []); } out.get(k).push(x); }
    return out;
  };
}
