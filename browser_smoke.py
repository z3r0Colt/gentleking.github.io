#!/usr/bin/env python3
"""Responsive and basic keyboard smoke checks with Playwright Chromium.

Run after the static site is served at http://127.0.0.1:8755.
Checks emulated device widths, not physical phones or assistive-technology tests.
"""
import base64
import os
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
SCREENSHOT_ROUTES = {
    "index.html", "start-here.html", "doctrine.html", "gospel.html",
    "guide-marriage.html", "comfort-grief.html", "sojourner-features.html",
    "resources.html", "biblehelps/index.html",
}
ISSUES = []

def check(condition, message):
    if not condition:
        ISSUES.append(message)

def main():
    screenshot_path = os.environ.get("GENTLEKING_SCREENSHOTS")
    if screenshot_path:
        Path(screenshot_path).mkdir(parents=True, exist_ok=True)
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
                if width == 1280 and route == "gospel.html":
                    intro = page.locator("#come").bounding_box()
                    reading_time = page.locator("main .reading-time").first.bounding_box()
                    check(intro is not None and reading_time is not None,
                          "Gospel introduction or reading time is missing")
                    if intro and reading_time:
                        gap = intro["y"] - (reading_time["y"] + reading_time["height"])
                        check(gap <= 48, f"Desktop Gospel introduction is displaced by {gap}px below the reading time")
                if route == "gospel.html":
                    quotes = page.locator("main blockquote.confession")
                    check(quotes.count() > 0, "Gospel confessional teaching is missing")
                    for quote in quotes.all():
                        check(quote.is_visible(), f"Gospel confessional teaching is hidden at {width}px")
                if screenshot_path and route in SCREENSHOT_ROUTES:
                    page.evaluate("document.fonts.ready")
                    page.screenshot(path=str(Path(screenshot_path) / f"{width}-{route.replace('/', '-')}.png"))
            page.close()
            if screenshot_path:
                # Return compact contact sheets through read-only job logs as well
                # as artifacts, so reviewers can inspect them without local network.
                cell_width = 375 if width == 375 else 512
                images = sorted(Path(screenshot_path).glob(f"{width}-*.png"))
                cards = []
                for shot in images:
                    data = base64.b64encode(shot.read_bytes()).decode("ascii")
                    cards.append(f'<figure><figcaption>{shot.name}</figcaption><img src="data:image/png;base64,{data}"></figure>')
                sheet = browser.new_page(viewport={"width": cell_width * 3 + 32, "height": 850})
                sheet.set_content(f'<style>body{{margin:8px;display:grid;grid-template-columns:repeat(3,{cell_width}px);gap:8px;background:#ddd}}figure{{margin:0}}figcaption{{font:12px sans-serif;padding:4px}}img{{display:block;width:100%}}</style>' + "".join(cards))
                sheet.evaluate("Promise.all(Array.from(document.images, image => image.decode()))")
                encoded = base64.b64encode(sheet.screenshot(type="jpeg", quality=65, full_page=True)).decode("ascii")
                for part in range(0, len(encoded), 4096):
                    print(f"VISUAL_REVIEW {width} {part // 4096} {encoded[part:part + 4096]}")
                print(f"VISUAL_REVIEW_END {width} {len(encoded)}")
                sheet.close()
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
