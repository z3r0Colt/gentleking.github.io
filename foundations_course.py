"""The course inventory shared by the index and contextual article navigation."""
import html
import json
from pathlib import Path

def lessons():
    return json.loads((Path(__file__).parent / 'assets/foundations.json').read_text(encoding='utf-8'))

def render_lessons():
    out = ['<ol class="foundation-steps">']
    for lesson in lessons():
        n = lesson['number']
        out.append(f'<li class="foundation-step" id="lesson-{n}"><h3>{n}. {html.escape(lesson["title"])}</h3>')
        out.append('<p>' + html.escape(lesson['description']) + '</p><p>Read ')
        for i, reading in enumerate(lesson['readings']):
            if i:
                out.append(', then ')
            href = f'{reading["href"]}?course=foundations&lesson={n}'
            out.append(f'<a href="{html.escape(href, quote=True)}">{html.escape(reading["label"])}</a>')
        conf = lesson['confession']
        out.append(f'.</p><p class="small">Scripture <a class="source-ref" aria-haspopup="dialog" href="bible.html?ref={lesson["scripture"]}">')
        from urllib.parse import unquote
        out.append(html.escape(unquote(lesson['scripture'])) + ' (KJV)</a> and ')
        out.append(f'<a href="{conf["href"]}">{conf["label"]}</a>.</p></li>')
    out.append('</ol>')
    return ''.join(out)

def course_return(filename):
    for lesson in lessons():
        if any(r['href'] == filename for r in lesson['readings']):
            return f'<p class="course-return">Studying Foundations? <a href="foundations.html#lesson-{lesson["number"]}">Return to lesson {lesson["number"]}</a>.</p>'
    return ''
