#!/usr/bin/env python3
"""Guard the new learning routes and reader-level access to the original Standards."""
from pathlib import Path
import re
import build

ROOT = Path(__file__).resolve().parent
ERRORS = []

def require(condition, message):
    if not condition:
        ERRORS.append(message)

def page(name):
    p = ROOT / name
    require(p.exists(), "Missing published page " + name)
    return p.read_text(encoding="utf-8") if p.exists() else ""

def main():
    names = [p["file"] for p in build.PAGES]
    require(len(set(names)) == len(names), "Duplicate page registration")
    study = page("westminster-study.html")
    foundations = page("foundations.html")
    for n in range(1, 34):
        require(f'id="chapter-{n}"' in study, f"Chapter {n} missing from study index")
        require(f'westminster-confession.html#chapter-{n}' in study, f"Chapter {n} lacks original text link")
    require(study.count('class="') > 30, "Westminster index structure missing")
    require(foundations.count('class="foundation-step"') == 16, "Expected 16 foundation lessons")
    for name in (
        "doctrine-baptism.html", "doctrine-christ-mediator.html",
        "doctrine-justification.html", "doctrine-fall-and-sin.html",
        "doctrine-christian-liberty.html", "doctrine-oaths-and-vows.html",
        "guide-church-membership.html", "guide-joining-rpc.html",
    ):
        require(f'href="{name}"' in (study + page("doctrine.html") + page("guides.html") + foundations + page("guide-find-a-church.html")),
                name + " has no learning entrance")
        require(name in names, name + " isn't registered")
    require("corrections.html?article=" in page("doctrine-baptism.html"), "Missing per-page report link")
    require('id="correction-form"' in page("corrections.html"), "Missing correction form")
    require("assets/js/corrections.js" in page("corrections.html"), "Correction script not loaded")
    require("westminster-confession.html#chapter-11-paragraph-1" in page("doctrine-justification.html"), "Paragraph deep link not generated")
    require("https://thewestminsterstandard.org/" in study, "Original source not credited")
    if ERRORS:
        for err in ERRORS:
            print("ERROR:", err)
        raise SystemExit(1)
    print("All 33 chapters, 16 lessons, new articles, paragraph references, and correction form pass.")

if __name__ == "__main__":
    main()
