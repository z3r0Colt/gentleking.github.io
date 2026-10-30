#!/usr/bin/env python3
"""Retrieve fixed public medical sources for editorial review, without editing copy."""
import hashlib
import html
import re
import urllib.error
import urllib.request

SOURCES = {
    'https://optionline.org/': ['24', '800', 'free'],
    'https://www.nhs.uk/conditions/ectopic-pregnancy/': [
        'symptoms', 'rupture', 'save',
    ],
    'https://www.fda.gov/drugs/postmarket-drug-safety-information-patients-and-providers/plan-b-one-step-15-mg-levonorgestrel-information': [
        'ovulation', 'implantation', 'fertilization',
    ],
    'https://www.healthychildren.org/English/family-life/family-dynamics/communication-discipline/Pages/Disciplining-Your-Child.aspx': [
        'spanking', 'discipline',
    ],
}

for url, needles in SOURCES.items():
    print('PRIMARY HEALTH SOURCE', url, flush=True)
    try:
        request = urllib.request.Request(url, headers={'User-Agent': 'GentleKing-source-review/1.0'})
        with urllib.request.urlopen(request, timeout=25) as response:
            raw = response.read(2_000_001)
        if len(raw) > 2_000_000:
            raise ValueError('Source exceeds the review size limit')
        print('HTML SHA256', hashlib.sha256(raw).hexdigest(), flush=True)
        body = re.sub(r'<(script|style)\b[^>]*>.*?</\1>', ' ', raw.decode('utf-8'), flags=re.S | re.I)
        body = re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]*>', ' ', body)))
        for needle in needles:
            matches = list(re.finditer(re.escape(needle), body, re.I))[:4]
            print('PASSAGE', needle, flush=True)
            if not matches:
                print('Passage not located; manual verification required.', flush=True)
            for match in matches:
                print(body[max(0, match.start() - 250):match.end() + 650], flush=True)
    except (urllib.error.URLError, UnicodeError, ValueError) as error:
        print('VERIFICATION UNAVAILABLE:', type(error).__name__, str(error), flush=True)
