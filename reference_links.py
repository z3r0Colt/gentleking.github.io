#!/usr/bin/env python3
"""Link Scripture and Westminster citations in rendered Gentle King article prose.

This operates on the article fragment at build time, not on the source words.
It skips existing links, controls, and code. Scripture references open the
site's own KJV reader; Westminster references use the original source at
thewestminsterstandard.org. No third-party Bible tracking service is needed.
"""
from __future__ import annotations

import html
import json
import pathlib
import re
from functools import lru_cache
from urllib.parse import quote

ROOT = pathlib.Path(__file__).resolve().parent
CONFESSION = "https://thewestminsterstandard.org/the-westminster-confession/"
LARGER = "https://thewestminsterstandard.org/westminster-larger-catechism/"
SHORTER = "https://thewestminsterstandard.org/westminster-shorter-catechism/"

@lru_cache(maxsize=1)
def bible_books():
    index = (ROOT / "biblehelps" / "index.html").read_text(encoding="utf-8")
    m = re.search(r'<script type="application/json" id="bibleMetadata">([\s\S]*?)</script>', index)
    if not m:
        raise RuntimeError("Cannot find the Bible book metadata")
    books = json.loads(m.group(1))
    mapping = {book["name"].lower(): book for book in books}
    mapping["psalm"] = mapping["psalms"]
    return mapping

@lru_cache(maxsize=1)
def scripture_pattern():
    choices = sorted(bible_books(), key=len, reverse=True)
    pattern = "|".join(re.escape(book) for book in choices)
    return re.compile(
        r'(?<![\w])(?P<book>' + pattern + r')\s+'
        r'(?P<ch>\d{1,3})'
        r'(?::(?P<vs>\d{1,3})(?:\s*[-\u2013]\s*(?P<ve>\d{1,3}))?)?'
        r'(?!\d)', re.I
    )

CONFESSIONAL = re.compile(
    r'(?<![\w])(?P<name>Westminster Confession of Faith|Westminster Confession|Westminster Larger Catechism|'
    r'Westminster Shorter Catechism|WCF|WLC|WSC)'
    r'\s+(?:(?:Q(?:&amp;|&)A|Q\.)\s*)?'
    r'(?P<num>\d{1,3})(?:\.(?P<sub>\d{1,2}))?'
    r'(?:\s*[-\u2013]\s*(?P<to>\d{1,3})(?:\.(?P<tosub>\d{1,2}))?)?',
    re.I
)

def valid_scripture(match):
    book = bible_books().get(match.group("book").lower())
    if not book:
        return False
    chapter = int(match.group("ch"))
    counts = book["chapters"]
    if chapter < 1 or chapter > len(counts):
        return False
    if match.group("vs"):
        verse = int(match.group("vs"))
        last = int(match.group("ve") or verse)
        if verse < 1 or last < verse or last > counts[chapter - 1]:
            return False
    return True

def confessional_url(match):
    """Open the exact original section and proof texts in Bible Reading Helps.

    Its Westminster data comes solely from thewestminsterstandard.org and
    each document provides a link back to that original source.
    """
    name, num = match.group("name").lower(), int(match.group("num"))
    if name in ("wcf", "westminster confession", "westminster confession of faith") and 1 <= num <= 33:
        sub = match.group("sub")
        return f"biblehelps/index.html#standards/wcf/{num}" + (f"/{int(sub)}" if sub else "")
    if name in ("wlc", "westminster larger catechism") and 1 <= num <= 196:
        return f"biblehelps/index.html#standards/wlc/{num}"
    if name in ("wsc", "westminster shorter catechism") and 1 <= num <= 107:
        return f"biblehelps/index.html#standards/wsc/{num}"
    return None

def link_text(text):
    # Quote only the exact printed reference. We never rewrite its wording,
    # and we never guess when a passage is out of range.
    matches = []
    for match in scripture_pattern().finditer(text):
        if valid_scripture(match):
            passage = match.group(0)
            url = "biblehelps/index.html?ref=" + quote(html.unescape(passage), safe="")
            matches.append((match.start(), match.end(), url, "Read " + passage + " in the KJV"))
    for match in CONFESSIONAL.finditer(text):
        url = confessional_url(match)
        if url:
            matches.append((match.start(), match.end(), url, "Read the original Westminster text and Scripture proofs"))
    if not matches:
        return text
    matches.sort(key=lambda t: (t[0], -(t[1] - t[0])))
    result, pos = [], 0
    for start, end, url, title in matches:
        if start < pos:
            continue
        result.append(text[pos:start])
        result.append(
            '<a class="source-ref" href="' + html.escape(url, quote=True)
            + '" target="_blank" rel="noopener" title="' + html.escape(title, quote=True)
            + '">' + text[start:end] + '</a>'
        )
        pos = end
    result.append(text[pos:])
    return "".join(result)

def link_references(fragment):
    """Leave all existing HTML tags unchanged; link text outside interactive tags."""
    pieces = re.split(r'(<[^>]+>)', fragment)
    prohibited = {"a", "button", "script", "style", "code", "pre", "textarea", "option", "svg"}
    depth = {name: 0 for name in prohibited}
    out = []
    for part in pieces:
        if part.startswith("<") and part.endswith(">"):
            m = re.match(r'<\s*(/?)\s*([\w:-]+)\b', part)
            if m and m.group(2).lower() in prohibited:
                name = m.group(2).lower()
                if m.group(1):
                    depth[name] = max(0, depth[name] - 1)
                elif not part.endswith("/>"):
                    depth[name] += 1
            out.append(part)
        elif any(depth.values()):
            out.append(part)
        else:
            out.append(link_text(part))
    return "".join(out)
