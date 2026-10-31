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
    books = json.loads((ROOT / "assets/kjv/books.json").read_text(encoding="utf-8"))
    mapping = {book["name"].lower(): book for book in books}
    mapping["psalm"] = mapping["psalms"]
    return mapping

@lru_cache(maxsize=1)
def scripture_pattern():
    choices = sorted(bible_books(), key=len, reverse=True)
    pattern = "|".join(re.escape(book) for book in choices)
    return re.compile(
        r'(?<![\w])(?P<single>(?=(?:Obadiah|Philemon|2 John|3 John|Jude)\s))?'
        r'(?P<book>' + pattern + r')\s+'
        r'(?P<ch>\d{1,3})'
        r'(?::(?P<vs>\d{1,3})(?:\s*[-\u2013]\s*(?P<ve>\d{1,3}))?'
        r'(?P<more>(?:\s*,\s*\d{1,3}(?:\s*[-\u2013]\s*\d{1,3})?)*))?'
        r'(?(single)(?P<shorttail>(?:\s*[-–]\s*\d{1,3})?(?:\s*,\s*\d{1,3}(?:\s*[-–]\s*\d{1,3})?)*))'
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

def scripture_parts(match):
    book = bible_books().get(match.group("book").lower())
    chapter = int(match.group("ch"))
    first = match.group("vs")
    if len(book["chapters"]) == 1 and first is None and (chapter > 1 or match.group("shorttail")):
        first, chapter = str(chapter), 1
    expression = (first or "") + (("-" + match.group("ve")) if match.group("ve") else "") + (match.group("more") or "") + (match.group("shorttail") or "")
    ranges = []
    if expression:
        for part in expression.split(","):
            pair = re.split(r"[-–]", part.strip())
            ranges.append((int(pair[0]), int(pair[-1])))
    return book, chapter, ranges


def valid_scripture(match):
    book, chapter, ranges = scripture_parts(match)
    if chapter < 1 or chapter > len(book["chapters"]):
        return False
    return all(1 <= first <= last <= book["chapters"][chapter - 1] for first, last in ranges)


def scripture_url(match):
    book, chapter, ranges = scripture_parts(match)
    reference = book["name"] + " " + str(chapter)
    if ranges:
        reference += ":" + ",".join(str(a) if a == b else f"{a}-{b}" for a, b in ranges)
    return "bible.html?ref=" + quote(reference, safe="")


def confessional_url(match):
    """Open the preserved original text and proofs on Gentle King itself."""
    name, num = match.group("name").lower(), int(match.group("num"))
    if name in ("wcf", "westminster confession", "westminster confession of faith") and 1 <= num <= 33:
        sub = match.group("sub")
        return f"westminster-confession.html#chapter-{num}" + (f"-paragraph-{int(sub)}" if sub else "")
    if name in ("wlc", "westminster larger catechism") and 1 <= num <= 196:
        return f"larger-catechism.html#question-{num}"
    if name in ("wsc", "westminster shorter catechism") and 1 <= num <= 107:
        return f"shorter-catechism.html#question-{num}"
    return None


def link_proof_references(fragment):
    """Link historical proof abbreviations without changing their printed words."""
    aliases = {book["name"]: book["name"] for book in bible_books().values()}
    names = {
        "Gen": "Genesis", "Ex": "Exodus", "Exod": "Exodus", "Lev": "Leviticus", "Num": "Numbers",
        "Deut": "Deuteronomy", "Josh": "Joshua", "Judg": "Judges", "Sam": "Samuel", "Chr": "Chronicles",
        "Neh": "Nehemiah", "Est": "Esther", "Psa": "Psalms", "Ps": "Psalms", "Prov": "Proverbs",
        "Ecc": "Ecclesiastes", "Songs": "Song of Solomon", "Isa": "Isaiah", "Jer": "Jeremiah",
        "Lam": "Lamentations", "Ezek": "Ezekiel", "Dan": "Daniel", "Hos": "Hosea", "Mic": "Micah",
        "Hab": "Habakkuk", "Hag": "Haggai", "Zec": "Zechariah", "Zech": "Zechariah", "Zeph": "Zephaniah",
        "Mal": "Malachi", "Mat": "Matthew", "Matt": "Matthew", "Rom": "Romans", "Cor": "Corinthians",
        "Gal": "Galatians", "Eph": "Ephesians", "Phil": "Philippians", "Col": "Colossians",
        "Thes": "Thessalonians", "Thess": "Thessalonians", "Tim": "Timothy", "Heb": "Hebrews",
        "Jas": "James", "Pet": "Peter",
    }
    for short, full in names.items():
        if full.lower() in bible_books():
            aliases[short] = full
        for number in (1, 2, 3):
            if f"{number} {full}".lower() in bible_books():
                aliases[f"{number} {short}"] = f"{number} {full}"
    choices = "|".join(re.escape(name) for name in sorted(aliases, key=len, reverse=True))
    verses = r"\d{1,3}(?:[-–]\d{1,3})?(?:,\s*\d{1,3}(?:[-–]\d{1,3})?)*"
    pattern = re.compile(r"(?<![\w])(?:(?P<book>" + choices + r")\.?\s+(?P<ref>" + verses + r"(?::" + verses + r")?)|(?P<implicit>\d{1,3}:" + verses + r"))(?!\d)")
    previous = None
    def link(match):
        nonlocal previous
        if match.group("book"):
            previous = aliases[match.group("book")]
        if previous is None:
            return match.group(0)
        canonical = previous + " " + (match.group("ref") or match.group("implicit"))
        parsed = scripture_pattern().fullmatch(canonical)
        if not parsed or not valid_scripture(parsed):
            return match.group(0)
        return '<a class="source-ref" href="' + scripture_url(parsed) + '" aria-haspopup="dialog">' + match.group(0) + '</a>'
    return pattern.sub(link, fragment)


def link_text(text):
    # Quote only the exact printed reference. We never rewrite its wording,
    # and we never guess when a passage is out of range.
    matches = []
    for match in scripture_pattern().finditer(text):
        if valid_scripture(match):
            passage = match.group(0)
            url = scripture_url(match)
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
        scripture = url.startswith("bible.html?")
        attributes = ' aria-haspopup="dialog"' if scripture else ''
        result.append(
            '<a class="source-ref" href="' + html.escape(url, quote=True)
            + '"' + attributes + ' title="' + html.escape(title, quote=True)
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
