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
        found = []
        for attrs, label in re.findall(r'<a\b([^>]*)>(.*?)</a>', page_html, re.S):
            match = re.search(r'\bhref="([^"]+)"', attrs)
            if not match:
                continue
            href = match.group(1)
            if 'class="source-ref"' in attrs or href.startswith((
                "bible.html?", "westminster-confession.html#", "larger-catechism.html#", "shorter-catechism.html#",
                "biblehelps/index.html?ref=", "biblehelps/index.html#standards/",
            )):
                found.append((href, label))
        bible, standards = 0, 0
        for href, label in found:
            if href.startswith("bible.html?"):
                query = parse_qs(urlsplit(href).query)
                reference = query.get("ref", [""])[0]
                match = scripture_pattern().fullmatch(reference)
                if not match or not __import__("reference_links").valid_scripture(match):
                    invalid.append(f"{page['file']} has invalid reference {reference}")
                bible += 1
            elif re.fullmatch(r"(?:westminster-confession\.html#chapter-\d+(?:-paragraph-\d+)?|(?:larger|shorter)-catechism\.html#question-\d+)", href):
                standards += 1
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
    # Validate the independent main-site KJV corpus and catch accidental app links.
    books = json.loads((ROOT / "assets/kjv/books.json").read_text(encoding="utf-8"))
    if len(books) != 66:
        invalid.append("The main-site KJV must contain all 66 books")
    for index, book in enumerate(books, 1):
        text = json.loads((ROOT / f"assets/kjv/{index:02d}.json").read_text(encoding="utf-8"))
        if text["name"] != book["name"] or [len(chapter) for chapter in text["chapters"]] != book["chapters"]:
            invalid.append("KJV book metadata mismatch: " + book["name"])
    for page in build.PAGES:
        if re.search(r'href="biblehelps/index\.html(?:\?ref=|#standards/)', (ROOT / page["file"]).read_text(encoding="utf-8")):
            invalid.append(page["file"] + " still sends reference reading to the companion app")
    source_docs = {d["id"]: d for d in json.loads((ROOT / "biblehelps/assets/content.json").read_text())["standards"]}
    for doc_id in ("wcf", "wlc", "wsc"):
        native = json.loads((ROOT / f"assets/standards/{doc_id}.json").read_text())
        if native != source_docs[doc_id]:
            invalid.append("Preserved original Westminster document changed: " + doc_id)
    retired = ["teachers.html", "teacher-philip-anthony-mitchell.html", "resources/discernment/philip-anthony-mitchell-discernment-report.pdf"]
    for name in retired:
        if (ROOT / name).exists():
            invalid.append("Retired teacher review still published: " + name)
    for published in [*(ROOT.glob("*.html")), ROOT / "assets/search-index.json", ROOT / "sitemap.xml", ROOT / "llms.txt"]:
        if any(re.search(r"(?<![\w-])" + re.escape(name) + r'(?=["?#\s<]|$)', published.read_text(encoding="utf-8")) for name in retired):
            invalid.append("Retired review reference in " + published.name)
    if invalid:
        for issue in invalid:
            print("ERROR:", issue)
        raise SystemExit(1)
    print("Citation and doctrine checks pass.")

if __name__ == "__main__":
    main()
