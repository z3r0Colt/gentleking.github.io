#!/usr/bin/env python3
"""Read fixed public evidence for the site review; never edit application data."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import html
import re
import urllib.error
import urllib.request

SOURCES = {
    'https://www.2819church.org/about': ['believe', 'Jesus', 'elders'],
    'https://podscripts.co/podcasts/2819-church/entry-end-times-stay-awake-matthew-2436-51-philip-anthony-mitchell': ['divine nature', 'probably knows'],
    'https://podscripts.co/podcasts/2819-church/so-we-fasted-ezra-821-23-philip-anthony-mitchell': ['move God', 'bodies are going', 'spirit inside'],
    'https://podscripts.co/podcasts/2819-church/expectations-for-access': ['portal', 'demand'],
    'https://podcastrex.com/shows/2819-church/in-christ-blessed-in-christ-ephesians-13-6-philip-anthony-mitchell/transcript': ['so long as', 'adopted'],
    'https://www.wabe.org/young-adults-are-waiting-in-line-to-worship-at-this-fast-growing-atlanta-church/': ['notes', 'smoke', '6,000'],
    'https://www.rodparsley.com/atonement/': ['offering', 'blessings'],
    'https://www.nhs.uk/medicines/diazepam/how-and-when-to-take-diazepam/': ['seizures', 'stop'],
    'https://www.organdonation.nhs.uk/become-a-living-donor/donating-your-kidney/': ['risk', 'kidney'],
    'https://www.nhs.uk/conditions/miscarriage/afterwards/': ['fever', 'temperature'],
    'https://www.churchofengland.org/prayer-and-worship/worship-texts-and-resources/common-worship/copyright': ['King James', 'Crown'],
}

def read_source(item):
    url, needles = item
    lines = ['EDITORIAL SOURCE ' + url]
    try:
        request = urllib.request.Request(url, headers={'User-Agent': 'GentleKing-source-review/1.0'})
        with urllib.request.urlopen(request, timeout=25) as response:
            raw = response.read(2_000_001)
        if len(raw) > 2_000_000:
            raise ValueError('Source exceeds review size limit')
        lines.append('SHA256 ' + hashlib.sha256(raw).hexdigest())
        body = re.sub(r'<(script|style)\b[^>]*>.*?</\1>', ' ', raw.decode('utf-8'), flags=re.S | re.I)
        body = re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]*>', ' ', body)))
        for needle in needles:
            matches = list(re.finditer(re.escape(needle), body, re.I))[:2]
            lines.append('PASSAGE ' + needle)
            if not matches:
                lines.append('Passage not located; manual verification required.')
            for match in matches:
                lines.append(body[max(0, match.start()-450):match.end()+1100])
    except (urllib.error.URLError, UnicodeError, ValueError) as error:
        lines.append('VERIFICATION UNAVAILABLE: ' + type(error).__name__ + ' ' + str(error))
    return '\n'.join(lines)

if __name__ == '__main__':
    with ThreadPoolExecutor(max_workers=4) as pool:
        for result in pool.map(read_source, SOURCES.items()):
            print(result, flush=True)
