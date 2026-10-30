#!/usr/bin/env python3
"""Read fixed primary-source passages for an editor; never modify the corpus.

HTTP errors are reported as unavailable verification, independently of the
browser checks. Successful retrieval is evidence of wording, not exegesis.
"""
import hashlib
import html
import re
import urllib.error
import urllib.request

SOURCES = {
    'https://thewestminsterstandard.org/the-westminster-confession/': [
        'Man by his fall having made himself incapable',
        'sin to refuse an oath',
        'The efficacy of baptism',
    ],
    'https://thewestminsterstandard.org/westminster-shorter-catechism/': [
        'Q. 37.', 'Q. 38.',
    ],
}

for url, needles in SOURCES.items():
    print('PRIMARY SOURCE', url, flush=True)
    try:
        request = urllib.request.Request(url, headers={'User-Agent': 'GentleKing-source-review/1.0'})
        with urllib.request.urlopen(request, timeout=25) as response:
            raw = response.read(2_000_001)
        if len(raw) > 2_000_000:
            raise ValueError('Source exceeds the review size limit')
        print('HTML SHA256', hashlib.sha256(raw).hexdigest(), flush=True)
        text = html.unescape(re.sub(r'<[^>]*>', ' ', raw.decode('utf-8')))
        text = re.sub(r'\s+', ' ', text)
        for needle in needles:
            at = text.lower().find(needle.lower())
            print('PASSAGE', needle, flush=True)
            print(text[max(0, at - 80):at + 1300] if at >= 0 else 'Passage not located; manual verification required.', flush=True)
    except (urllib.error.URLError, UnicodeError, ValueError) as error:
        print('VERIFICATION UNAVAILABLE:', type(error).__name__, str(error), flush=True)
