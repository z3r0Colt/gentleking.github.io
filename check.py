#!/usr/bin/env python3
"""
Gentle King, site check.

Run this after building. It reads the .html files at the top of the repo and
complains about the things that are easy to get wrong and hard to notice.

    python3 build.py && python3 check.py

What it looks for.

  Broken HTML          tags left open, tags closed in the wrong order
  Dead links           a link pointing at a file that is not in the repo
  Unsafe links         an outside link missing target and rel
  Duplicate ids        two sections sharing an id, which breaks the anchors
  Stray classes        a class name the stylesheet does not define
  Punctuation          em dashes, semicolons, and colons in ordinary prose

Quoted Scripture is skipped on the punctuation check. The ESV punctuates the
way it punctuates and nothing here should change it.

An exit code of 0 means everything passed.
"""

import collections
import html
import html.parser
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).parent.resolve()
CSS = ROOT / "assets" / "css" / "site.css"

VOID = {
    "br", "hr", "img", "meta", "link", "input", "source", "area", "col",
    "embed", "param", "track", "wbr",
}


def class_names(css):
    css = re.sub(r"(?s)/\*.*?\*/", " ", css)
    return set(re.findall(r"\.([A-Za-z][\w-]*)", css))


def defined_classes():
    """Every class name the shared stylesheet defines."""
    return class_names(CSS.read_text(encoding="utf-8"))


class Reader(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.problems = []
        self.ids = collections.Counter()
        self.internal = []
        self.external = []
        self.svg_depth = 0
        self.headings = 0

    def handle_starttag(self, tag, attrs):
        attr = dict(attrs)
        if tag == "svg":
            self.svg_depth += 1
        if tag == "h1":
            self.headings += 1
        if not self.svg_depth:
            for name in (attr.get("class") or "").split():
                if name not in KNOWN:
                    self.problems.append(f"class {name!r} is used but not styled")
            if "style" in attr:
                self.problems.append(f"<{tag}> carries an inline style, put it in the stylesheet")
        if attr.get("id"):
            self.ids[attr["id"]] += 1
        if tag == "a" and attr.get("href"):
            href = attr["href"]
            (self.external if href.startswith("http") else self.internal).append((href, attr))
        raw = self.get_starttag_text() or ""
        if tag not in VOID and not raw.endswith("/>") and not self.svg_depth:
            self.stack.append(tag)
        elif tag not in VOID and not raw.endswith("/>"):
            self.stack.append(tag)

    def handle_startendtag(self, tag, attrs):
        """A self closing tag such as <path/> opens and shuts in one go."""
        self.handle_starttag(tag, attrs)
        if tag == "svg":
            self.svg_depth = max(0, self.svg_depth - 1)
        if self.stack and self.stack[-1] == tag:
            self.stack.pop()

    def handle_endtag(self, tag):
        if tag == "svg":
            self.svg_depth = max(0, self.svg_depth - 1)
        if tag in VOID:
            return
        if not self.stack:
            self.problems.append(f"a stray </{tag}> with nothing open")
        elif self.stack[-1] != tag:
            self.problems.append(f"</{tag}> closes <{self.stack[-1]}>, the nesting is wrong")
            if tag in self.stack:
                while self.stack and self.stack.pop() != tag:
                    pass
        else:
            self.stack.pop()


def prose(source):
    """Visible prose, with quoted Scripture and confessions taken out."""
    text = re.sub(r"(?s)<(script|style)\b.*?</\1>", " ", source)
    text = re.sub(r"(?s)<!--.*?-->", " ", text)
    text = re.sub(r'(?s)<blockquote class="scripture">.*?</blockquote>', " ", text)
    text = re.sub(r'(?s)<blockquote class="confession">.*?</blockquote>', " ", text)
    text = re.sub(r'(?s)<p class="(footer-verse|mock-verse|verse)">.*?</p>', " ", text)
    text = re.sub(r"<[^>]+>", "\n", text)
    return html.unescape(text)


SHARED = defined_classes()
KNOWN = SHARED


def check(path):
    global KNOWN
    source = path.read_text(encoding="utf-8")
    # a hand written page may carry its own styles, 404.html does
    inline = " ".join(re.findall(r"(?s)<style\b[^>]*>(.*?)</style>", source))
    KNOWN = SHARED | class_names(inline)
    reader = Reader()
    reader.feed(source)
    reader.close()
    found = list(reader.problems)

    if reader.stack:
        found.append(f"never closed: {', '.join(reader.stack)}")
    if reader.headings != 1:
        found.append(f"{reader.headings} <h1> tags, a page should have exactly one")

    for name, count in reader.ids.items():
        if count > 1:
            found.append(f"id {name!r} is used {count} times, anchors will jump to the wrong place")

    for href, _ in reader.internal:
        target = href.split("#")[0]
        if target and not (ROOT / target).exists():
            found.append(f"link to {href} but that file is not in the repo")

    for href, attr in reader.external:
        if attr.get("target") != "_blank" or "noopener" not in (attr.get("rel") or ""):
            found.append(f'outside link needs target="_blank" rel="noopener": {href}')

    body = prose(source)
    for line in body.split("\n"):
        line = line.strip()
        if not line:
            continue
        if "—" in line:
            found.append(f"em dash: {line[:80]}")
        if ";" in line:
            found.append(f"semicolon: {line[:80]}")
        if re.search(r"[^\d\s]:(?!\d)", line):
            found.append(f"colon in prose: {line[:80]}")

    return found


def main():
    pages = sorted(ROOT.glob("*.html"))
    if not pages:
        print("No html files found. Run python3 build.py first.")
        return 1

    bad = 0
    for page in pages:
        found = check(page)
        print(f"{page.name:<18} {'FAIL' if found else 'ok'}")
        for problem in found[:30]:
            print(f"    {problem}")
        if len(found) > 30:
            print(f"    and {len(found) - 30} more")
        if found:
            bad += 1

    print()
    if bad:
        print(f"{bad} of {len(pages)} pages need attention.")
        return 1
    print(f"All {len(pages)} pages look right.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
