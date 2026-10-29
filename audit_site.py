#!/usr/bin/env python3
"""Focused sitewide checks for citations, generated content, and source integrity."""
import json
import pathlib
import re
from urllib.parse import parse_qs, unquote, urlsplit

import build
from reference_links import bible_books, scripture_pattern

ROOT = pathlib.Path(__file__).resolve().parent

def main():
    total_bible = 0
    total_westminster = 0
    counts = []
    invalid = []
    for page in build.PAGES:
        path = ROOT / page["file"]
        if not path.is_file():
            invalid.append(f"{page['file']} was not built")
            continue
        page_html = path.read_text(encoding="utf-8")
        found = re.findall(r'<a class="source-ref" href="([^"]+)"[^>]*>(.*?)</a>', page_html, re.S)
        bible, standards = 0, 0
        for href, label in found:
            if href.startswith("biblehelps/index.html?"):
                query = parse_qs(urlsplit(href).query)
                reference = query.get("ref", [""])[0]
                match = scripture_pattern().fullmatch(reference)
                if not match or not __import__("reference_links").valid_scripture(match):
                    invalid.append(f"{page['file']} has invalid reference {reference}")
                bible += 1
            elif href in (
                "https://thewestminsterstandard.org/the-westminster-confession/",
                "https://thewestminsterstandard.org/westminster-larger-catechism/",
                "https://thewestminsterstandard.org/westminster-shorter-catechism/",
            ):
                standards += 1
            else:
                invalid.append(f"{page['file']} has an unsupported source link {href}")
        total_bible += bible
        total_westminster += standards
        if bible or standards:
            counts.append((page["file"], bible, standards))
    print(f"Source links across {len(build.PAGES)} generated pages: {total_bible} Bible references, {total_westminster} Westminster references.")
    for path, bible, standards in sorted(counts, key=lambda r: -(r[1] + r[2]))[:14]:
        print(f"  {path:<43} {bible:>3} Bible  {standards:>3} Westminster")
    if total_bible < 200 or total_westminster < 30:
        invalid.append("Too few references linked. Inspect the citation linker.")
    for path in ["doctrine-providence.html", "doctrine-union-with-christ.html", "doctrine-adoption.html",
                 "doctrine-sanctification.html", "doctrine-church-government.html"]:
        if not (ROOT / path).is_file():
            invalid.append("Missing new doctrine article: " + path)
        if f'href="{path}"' not in (ROOT / "doctrine.html").read_text(encoding="utf-8"):
            invalid.append("Doctrine index does not link to " + path)
    if invalid:
        for issue in invalid:
            print("ERROR:", issue)
        raise SystemExit(1)
    print("Citation and doctrine checks pass.")

if __name__ == "__main__":
    main()
