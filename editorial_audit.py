#!/usr/bin/env python3
"""Report recurring editorial formulas in authored prose.

This is a review aid, not an AI detector, and never rewrites theological text.
"""
from __future__ import annotations

import collections
import html
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent / "content"
PATTERNS = {
    "not-X-but-Y construction": r"\b(?:not just|not merely|not simply|isn't just|doesn't just|not only)\b",
    "do-not-have-to reassurance": r"\byou (?:don't|do not) have to\b",
    "a-picture-and-it-is-real": r"\bwhat it pictures is real\b|\bwhat the picture shows is real\b",
    "generic weekly checklist": r"\bwhat to do this week\b",
    "abstract signposting": r"\b(?:the point is|in other words|here's the thing|the real question is|this is why)\b",
    "vague fine-words reassurance": r"\b(?:you don't need fine words|you do not need fine words)\b",
    "hedge candidates": r"\b(?:perhaps|might|could|sometimes|often|generally)\b",
}

def readable(fragment):
    fragment = re.sub(r"<blockquote\b[^>]*>[\s\S]*?</blockquote>", "", fragment)
    fragment = re.sub(r"<(?:script|style)\b[^>]*>[\s\S]*?</(?:script|style)>", "", fragment)
    fragment = re.sub(r"<[^>]*>", " ", fragment)
    return html.unescape(fragment)

def main():
    files = sorted(ROOT.glob("*.html"))
    stats = collections.Counter()
    examples = collections.defaultdict(list)
    print(f"Reviewing {len(files)} source articles.")
    for path in files:
        text = readable(path.read_text(encoding="utf-8"))
        for label, pattern in PATTERNS.items():
            found = list(re.finditer(pattern, text, re.IGNORECASE))
            if found:
                stats[label] += len(found)
                for match in found[:4]:
                    context = " ".join(text[max(0, match.start()-55):match.end()+80].split())
                    examples[label].append((path.name, context))
    for label in PATTERNS:
        print(f"\n{label}: {stats[label]} possible instances")
        for name, context in examples[label][:80 if label in ('a-picture-and-it-is-real', 'generic weekly checklist') else 15]:
            print(f"  {name}: {context}")
    print("\nThese are candidates only. Check their context before changing them.")

if __name__ == "__main__":
    main()
