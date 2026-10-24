#!/usr/bin/env python3
"""Validate the companion data and on-demand Bible assets before publishing."""
import hashlib
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent
APP = ROOT / 'biblehelps'


def main():
    shell = (APP / 'index.html').read_text()
    data = json.loads((APP / 'assets/content.json').read_text())
    metadata = json.loads(re.search(r'<script type="application/json" id="bibleMetadata">(.*?)</script>', shell, re.S)[1])
    assert len(data['books']) == len(metadata) == 66, 'Expected all 66 Bible books'
    assert len(data['catechismCourse']) == 107, 'Expected all 107 Catechism lessons'
    assert len(data['lessons']) == 24, 'Expected all 24 study lessons'
    assert len(data['standards']) == 8, 'Expected all eight source documents'
    # The main page and companion intentionally teach the same gospel in the same words.
    # The final paragraph describes the reading tool itself rather than gospel doctrine.
    core_paragraphs = [paragraph for section in data['gospel']
                       for paragraph in re.findall(r'<p>[\s\S]*?</p>', section['html'])][:-1]
    main_gospel = (ROOT / 'content/gospel.html').read_text()
    assert all(paragraph in main_gospel for paragraph in core_paragraphs), 'Main and companion gospel wording has drifted'
    for i, book in enumerate(metadata):
        content = json.loads((APP / f'assets/bible/{i + 1:02}.json').read_text())
        assert content['name'] == book['name'], f'Book name differs at {i + 1}'
        assert [len(ch) for ch in content['chapters']] == book['chapters'], f'Verse counts differ in {book["name"]}'
        assert all(isinstance(v, str) and v.strip() for ch in content['chapters'] for v in ch), f'Empty Scripture in {book["name"]}'
    for asset in re.findall(r'(?:src|href)="(assets/[^"?#]+)', shell):
        assert (APP / asset).is_file(), f'Missing asset {asset}'
    manifest = json.loads((APP / 'assets/content-integrity.json').read_text())
    for name, expected in manifest.items():
        actual = hashlib.sha256((APP / 'assets' / name).read_bytes()).hexdigest()
        assert actual == expected, f'Supplied content has changed in {name}'
    print('Bible Reading Helps passes data, asset, and supplied-text integrity checks.')


if __name__ == '__main__':
    main()
