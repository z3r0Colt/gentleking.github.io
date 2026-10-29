/* Gentle King correction reports. No server collection or tracking. */
(function () {
  'use strict';
  var form = document.getElementById('correction-form');
  if (!form) return;
  var page = document.getElementById('correction-page');
  var note = document.getElementById('correction-note');
  var kind = document.getElementById('correction-kind');
  var requested = new URLSearchParams(window.location.search).get('article');
  if (requested && /^[a-z0-9-]+\.html$/i.test(requested)) {
    page.value = new URL(requested, window.location.origin + '/').href;
  }
  form.addEventListener('submit', function (event) {
    if (!form.reportValidity()) return;
    event.preventDefault();
    var subject = 'Gentle King correction: ' + kind.value;
    var body = [
      'Page: ' + page.value.trim(),
      'Concern: ' + kind.value,
      '',
      note.value.trim(),
      '',
      'Supporting reference or suggested correction:'
    ].join('\n');
    window.location.href = 'mailto:colt@gentleking.org?subject=' +
      encodeURIComponent(subject) + '&body=' + encodeURIComponent(body);
  });
})();
