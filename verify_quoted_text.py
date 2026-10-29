#!/usr/bin/env python3
"""Check that exact quotation blocks have not changed during prose cleanup.

Compare authored content against origin/main. --restore returns matching
protected blocks to the baseline, and fails if their boundaries changed.
"""
from __future__ import annotations
import argparse
import pathlib
import re
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent
PATTERNS = [
    ("Scripture, confession and historical blockquotes",
     re.compile(r"<blockquote\b[^>]*>[\s\S]*?</blockquote>", re.I)),
    ("verbatim verse or confessional headings",
     re.compile(r'<h[1-6]\b(?=[^>]*class="[^"]*(?:verse-head|scripture|confession|verbatim)[^"]*")[^>]*>[\s\S]*?</h[1-6]>', re.I)),
    ("verbatim Scripture or confession paragraphs",
     re.compile(r'<p\b(?=[^>]*class="[^"]*(?:scripture|confession|verbatim)[^"]*")[^>]*>[\s\S]*?</p>', re.I)),
    ("explicit quotations",
     re.compile(r"<q\b[^>]*>[\s\S]*?</q>", re.I)),
]

def original(path):
    try:
        return subprocess.check_output(
            ["git", "show", "origin/main:" + str(path.relative_to(ROOT))],
            cwd=ROOT, text=True,
        )
    except subprocess.CalledProcessError:
        return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--restore", action="store_true")
    args = ap.parse_args()
    changed_files = 0
    restored = 0
    problems = []
    for path in sorted((ROOT / "content").glob("*.html")):
        base = original(path)
        if base is None:
            continue
        current = path.read_text(encoding="utf-8")
        updated = current
        for label, pattern in PATTERNS:
            originals = pattern.findall(base)
            new = pattern.findall(updated)
            if len(originals) != len(new):
                problems.append(f"{path.name}: changed {label} boundaries")
                continue
            differs = sum(a != b for a, b in zip(originals, new))
            if differs:
                if not args.restore:
                    problems.append(f"{path.name}: {differs} altered {label}")
                else:
                    iterator = iter(originals)
                    updated = pattern.sub(lambda m: next(iterator), updated)
                    restored += differs
        if args.restore and updated != current:
            path.write_text(updated, encoding="utf-8")
            changed_files += 1
    for issue in problems:
        print("ERROR:", issue)
    if problems:
        raise SystemExit(1)
    print(f"Quotation integrity passed; restored {restored} protected blocks in {changed_files} files.")

if __name__ == "__main__":
    main()
