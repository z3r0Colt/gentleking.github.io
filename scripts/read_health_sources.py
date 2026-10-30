#!/usr/bin/env python3
"""Retrieve fixed public medical sources for editorial review, without editing copy."""
import hashlib
import html
import json
import re
import urllib.error
import urllib.request

SOURCES = {
    'https://988lifeline.org/get-help/': ['24', '988'],
    'https://www.thehotline.org/': ['7233', '88788'],
    'https://www.thehotline.org/plan-for-safety/': ['plan', 'safe'],
    'https://www.thehotline.org/resources/should-i-go-to-couples-therapy-with-my-abusive-partner/': ['recommend', 'therapy'],
    'https://www.childhelphotline.org/': ['reporting', '4453', 'mandated'],
    'https://afsp.org/find-a-support-group/': ['support group'],
    'https://afsp.org/healing-conversations/': ['loss', 'volunteer'],
    'https://www.nimh.nih.gov/health/publications/generalized-anxiety-disorder-gad': ['treatment', 'therapy'],
    'https://www.nimh.nih.gov/health/publications/panic-disorder-when-fear-overwhelms': ['treatment', 'breathing'],
    'https://www.nia.nih.gov/health/frequently-asked-questions-about-caregiving': ['respite'],
    'https://www.nia.nih.gov/health/caregiving/getting-started-caregiving': ['care'],
    'https://211.org/': ['housing', '211'],
    'https://www.usa.gov/avoid-eviction': ['eviction'],
    'https://www.usa.gov/unemployment-benefits': ['state'],
    'https://www.nhs.uk/conditions/miscarriage/symptoms/': ['bleeding', 'fever'],
    'https://optionline.org/': ['24', '800', 'free'],
    'https://www.nhs.uk/conditions/ectopic-pregnancy/': [
        'symptoms', 'rupture', 'save',
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


print('PRIMARY LABEL LOOKUP: DailyMed Plan B One-Step', flush=True)
try:
    query_url = 'https://dailymed.nlm.nih.gov/dailymed/services/v2/spls.json?drug_name=PLAN%20B%20ONE-STEP'
    with urllib.request.urlopen(query_url, timeout=25) as response:
        labels = json.load(response)['data']
    for label in labels:
        print('LABEL RECORD', label, flush=True)
        if 'FOUNDATION CONSUMER HEALTHCARE' not in label.get('title', ''):
            continue
        set_id = label.get('setid', '')
        if not re.fullmatch(r'[0-9a-fA-F-]{36}', set_id):
            continue
        url = 'https://dailymed.nlm.nih.gov/dailymed/services/v2/spls/' + set_id + '.xml'
        with urllib.request.urlopen(url, timeout=25) as response:
            raw = response.read(2_000_001)
        if len(raw) > 2_000_000:
            raise ValueError('Label exceeds the review size limit')
        print('LABEL SOURCE', url, hashlib.sha256(raw).hexdigest(), flush=True)
        body = re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]*>', ' ', raw.decode('utf-8'))))
        print('CURRENT MANUFACTURER LABEL TEXT', body[:16000], flush=True)
        for needle in ['egg', 'ovulation', 'implantation', 'fertilization']:
            for match in list(re.finditer(needle, body, re.I))[:3]:
                print(body[max(0, match.start() - 200):match.end() + 700], flush=True)
except (urllib.error.URLError, UnicodeError, ValueError, KeyError) as error:
    print('VERIFICATION UNAVAILABLE:', type(error).__name__, str(error), flush=True)
