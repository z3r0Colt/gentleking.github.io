"""Render the preserved original Westminster text without loading the companion app."""
import html
import json
from pathlib import Path
from reference_links import link_proof_references

ROOT = Path(__file__).resolve().parent
FILES = {'wcf': 'westminster-confession.html', 'wlc': 'larger-catechism.html', 'wsc': 'shorter-catechism.html'}

def render_standard(doc_id):
    document = json.loads((ROOT / f'assets/standards/{doc_id}.json').read_text(encoding='utf-8'))
    out = ['<div class="standards-text">', '<p>This historical text and its Scripture proofs come from '
           f'<a href="{html.escape(document["source"])}" target="_blank" rel="noopener">The Westminster Standard</a>. '
           'The original wording is preserved.</p>', '<nav class="standards-index" aria-label="Westminster documents">']
    for key, name in [('wcf', 'Confession'), ('wlc', 'Larger Catechism'), ('wsc', 'Shorter Catechism')]:
        out.append(f'<a href="{FILES[key]}">{name}</a>')
    out.append('</nav><details class="supporting-text"><summary>Jump to a chapter or question</summary><nav class="standards-index" aria-label="Document sections">')
    for section in document['sections']:
        number = section['number']
        anchor = f'chapter-{number}' if doc_id == 'wcf' else f'question-{number}'
        out.append(f'<a href="#{anchor}">{number}</a>')
    out.append('</nav></details>')
    for section in document['sections']:
        number = section['number']
        anchor = f'chapter-{number}' if doc_id == 'wcf' else f'question-{number}'
        title = f'Chapter {number}. {section["title"]}' if doc_id == 'wcf' else section['title']
        out.append(f'<section class="section" id="{anchor}"><h2>{html.escape(title)}</h2>')
        for unit in section['units']:
            if doc_id == 'wcf':
                out.append(f'<div id="chapter-{number}-paragraph-{unit["number"]}"><h3>{document["short"]} {number}.{unit["number"]}</h3>')
            else:
                out.append('<div>')
            out.append('<blockquote class="confession">')
            if unit.get('question'):
                out.append('<p><strong>' + html.escape(unit['question']) + '</strong></p>')
            out.append(unit['html'])
            out.append('</blockquote>')
            if unit.get('proofHtml'):
                out.append('<details class="supporting-text"><summary>Scripture proofs</summary><blockquote class="confession">')
                out.append(link_proof_references(unit['proofHtml']))
                out.append('</blockquote></details>')
            out.append('</div>')
        out.append('</section>')
    out.append('</div>')
    return '\n'.join(out)
