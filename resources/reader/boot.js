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
