#!/usr/bin/env python3
"""Responsive and basic keyboard smoke checks with Playwright Chromium.

Run after the static site is served at http://127.0.0.1:8755.
Checks emulated device widths, not physical phones or assistive-technology tests.
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8755/"
PAGES = [
    "index.html", "start-here.html", "learn.html", "doctrine.html",
    "foundations.html", "westminster-study.html", "guides.html",
    "doctrine-baptism.html", "guide-church-membership.html",
    "corrections.html", "biblehelps/index.html",
]
PAGES += [
    path.name for path in sorted((Path(__file__).resolve().parent / "content").glob("*.html"))
    if path.name not in PAGES
]
ISSUES = []

def check(condition, message):
    if not condition:
        ISSUES.append(message)

def main():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        for width in (375, 768, 1280):
            page = browser.new_page(viewport={"width": width, "height": 850}, reduced_motion="reduce")
            js_errors = []
            page.on("pageerror", lambda error: js_errors.append(str(error)))
            for route in PAGES:
                page.goto(BASE + route, wait_until="domcontentloaded", timeout=25000)
                if route.startswith("biblehelps/"):
                    page.locator("#main").wait_for(state="visible", timeout=18000)
                else:
                    page.locator("main").wait_for(state="visible", timeout=10000)
                overflow = page.evaluate("Math.max(0, document.documentElement.scrollWidth - innerWidth)")
                check(overflow <= 2, f"{route} overflows by {overflow}px at {width}px")
                h1_count = page.locator("h1").count()
                check(h1_count >= 1, f"{route} lacks a page heading at {width}px")
                check(not js_errors, f"{route} has JS errors at {width}px: {js_errors[:2]}")
                js_errors.clear()
            page.close()
        page = browser.new_page(viewport={"width": 375, "height": 850})
        page.goto(BASE + "corrections.html?article=doctrine-baptism.html", wait_until="domcontentloaded")
        page.locator("#correction-page").wait_for()
        check(page.locator("#correction-page").input_value().endswith("/doctrine-baptism.html"),
              "Correction form does not preserve the article address")
        page.goto(BASE + "biblehelps/index.html#standards/wcf/11/1", wait_until="domcontentloaded")
        page.locator("#standard-unit-1").wait_for(state="attached", timeout=18000)
        check(page.locator("#standard-unit-1").count() == 1, "Westminster paragraph deep link did not render")
        check("Justification" in page.locator(".reader.prose.standards-text").inner_text(),
              "Westminster chapter 11 was not loaded")
        page.close()
        browser.close()
    if ISSUES:
        for issue in ISSUES:
            print("ERROR:", issue)
        sys.exit(1)
    print(f"Responsive browser and navigation checks passed for {len(PAGES)} routes at 3 viewport widths.")

if __name__ == "__main__":
    main()
