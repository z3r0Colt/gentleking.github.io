/* Keep course navigation separate from an article's ordinary related reading. */
(function () {
  'use strict';
  var params = new URLSearchParams(location.search);
  if (params.get('course') !== 'foundations') { return; }
  var number = Number(params.get('lesson'));
  if (!Number.isInteger(number) || number < 1 || number > 16) { return; }
  var filename = location.pathname.split('/').pop();
  fetch('assets/foundations.json').then(function (response) {
    if (!response.ok) { throw new Error('Course navigation unavailable'); }
    return response.json();
  }).then(function (lessons) {
    var lesson = lessons[number - 1];
    var index = lesson.readings.findIndex(function (reading) { return reading.href === filename; });
    if (index < 0) { return; }
    var host = document.querySelector('.reading-column') || document.querySelector('main');
    if (!host) { return; }
    function address(reading, lessonNumber) {
      return reading.href + '?course=foundations&lesson=' + lessonNumber;
    }
    function navigation() {
      var nav = document.createElement('nav');
      nav.className = 'course-navigation';
      nav.setAttribute('aria-label', 'Foundations course');
      var heading = document.createElement('p');
      heading.textContent = 'Foundations · Lesson ' + number + ' of ' + lessons.length + ' · ' + lesson.title;
      nav.appendChild(heading);
      var links = document.createElement('div');
      function link(label, href, direction) {
        var item = document.createElement('a');
        item.textContent = label;
        item.href = href;
        if (direction) { item.rel = direction; }
        links.appendChild(item);
      }
      if (index > 0) {
        link('Previous reading', address(lesson.readings[index - 1], number), 'prev');
      } else if (number > 1) {
        var previous = lessons[number - 2];
        link('Previous lesson', address(previous.readings[previous.readings.length - 1], number - 1), 'prev');
      }
      link('Course overview', 'foundations.html#lesson-' + number);
      if (index + 1 < lesson.readings.length) {
        link('Next reading · ' + lesson.readings[index + 1].label, address(lesson.readings[index + 1], number), 'next');
      } else if (number < lessons.length) {
        link('Next lesson · ' + lessons[number].title, address(lessons[number].readings[0], number + 1), 'next');
      } else {
        link('Finish the course', 'foundations.html#reading');
      }
      nav.appendChild(links);
      return nav;
    }
    document.body.classList.add('course-reading');
    host.prepend(navigation());
    host.appendChild(navigation());
  }).catch(function () { /* The article and its static course-return link remain usable. */ });
})();
