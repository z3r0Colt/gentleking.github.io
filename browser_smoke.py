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
    "corrections.html", "bible.html", "westminster-confession.html", "larger-catechism.html", "shorter-catechism.html", "biblehelps/index.html",
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
        browser = playwright.chromium.launch(headless=True, executable_path=os.environ.get("CHROMIUM_EXECUTABLE"))
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
        # Scripture must work even when the separate companion app is unavailable.
        for width in (375, 768, 1280):
            page = browser.new_page(viewport={"width": width, "height": 850}, reduced_motion="reduce")
            page.route("**/biblehelps/**", lambda route: route.abort())
            page.goto(BASE + "gospel.html", wait_until="domcontentloaded")
            reference = page.locator('a.source-ref[href^="bible.html?ref="]').first
            reference.scroll_into_view_if_needed()
            before = page.evaluate("scrollY")
            address = page.url
            reference.click()
            page.locator(".kjv-dialog .kjv-passage p").first.wait_for()
            check(page.url == address, "Scripture click leaves the article")
            check("Come unto me" in page.locator(".kjv-dialog").inner_text(), "KJV passage did not load independently")
            check(page.locator(".kjv-dialog .kjv-passage p").count() == 3, "Scripture range did not show exactly three verses")
            check(page.evaluate("document.documentElement.scrollWidth <= innerWidth + 2"), "Scripture dialog overflows at " + str(width))
            if screenshot_path:
                page.screenshot(path=str(Path(screenshot_path) / f"kjv-dialog-{width}.png"))
            page.keyboard.press("Escape")
            check(not page.locator(".kjv-dialog").is_visible(), "Escape did not close Scripture")
            check(reference.evaluate("element => element === document.activeElement"), "Closing Scripture did not restore focus")
            check(abs(page.evaluate("scrollY") - before) <= 2, "Closing Scripture lost article position")
            page.goto(BASE + "bible.html?ref=John%203%3A16-18", wait_until="domcontentloaded")
            page.locator("#kjv-verse-36").wait_for()
            check(page.locator("#kjv-passage .kjv-selected").count() == 3, "Full chapter did not highlight the requested range")
            check("For God so loved the world" in page.locator("#kjv-verse-16").inner_text(), "Full reader has wrong KJV text")
            page.locator("#kjv-previous").click()
            page.wait_for_url("**ref=John%202")
            check(page.locator("#kjv-passage h2").inner_text() == "John 2", "Previous chapter failed")
            page.go_back()
            page.locator("#kjv-verse-36").wait_for()
            check(page.locator("#kjv-passage .kjv-selected").count() == 3, "Browser Back lost the Scripture range")
            page.locator("#kjv-book").select_option("0")
            page.locator("#kjv-chapter").select_option("50")
            page.locator("#kjv-form").get_by_role("button", name="Read", exact=True).click()
            page.wait_for_url("**ref=Genesis%2050")
            page.locator("#kjv-next").click()
            page.wait_for_url("**ref=Exodus%201")
            check(page.locator("#kjv-passage h2").inner_text() == "Exodus 1", "Next chapter failed at book boundary")
            page.goto(BASE + "bible.html?ref=John%20999", wait_until="domcontentloaded")
            page.wait_for_function("document.getElementById('kjv-status').textContent.includes('valid Bible reference')")
            check(page.locator("#kjv-passage p").count() == 0, "Invalid Scripture request displayed an unrelated passage")
            page.close()

        page = browser.new_page(viewport={"width": 375, "height": 850}, reduced_motion="reduce")
        page.route("**/biblehelps/**", lambda route: route.abort())
        page.goto(BASE + "foundations.html", wait_until="domcontentloaded")
        assignments = page.locator('.foundation-step a[href^="bible.html?ref="]')
        check(assignments.count() == 16, "Foundations must use 16 native Scripture links")
        assignments.first.click()
        page.locator(".kjv-dialog .kjv-passage p").first.wait_for()
        check(page.url.endswith("foundations.html"), "Foundations Scripture leaves Gentle King")
        page.keyboard.press("Escape")
        page.goto(BASE + "guide-repentance.html?course=foundations&lesson=6", wait_until="domcontentloaded")
        page.locator(".course-navigation").first.wait_for()
        page.locator('.course-navigation a[rel="next"]').first.click()
        page.wait_for_url("**/doctrine-justification.html?course=foundations&lesson=7")
        check(not page.locator(".pager").is_visible(), "Generic article navigation competes with the course")
        page.locator('.source-ref[href="westminster-confession.html#chapter-11-paragraph-1"]').first.click()
        page.wait_for_url("**/westminster-confession.html#chapter-11-paragraph-1")
        check("freely justifieth" in page.locator("#chapter-11-paragraph-1").inner_text(), "Native original WCF paragraph missing")
        page.locator('#chapter-11-paragraph-1 details summary').click()
        proof = page.locator('#chapter-11-paragraph-1 a[href^="bible.html?ref="]').first
        check(proof.count() == 1, "Native Scripture proofs lack reading links")
        proof.click()
        page.locator(".kjv-dialog .kjv-passage p").first.wait_for()
        page.keyboard.press("Escape")
        for reference, verses in [("John%204%3A21%2C23", 2), ("Jude%203", 1), ("2%20John%209-10", 2)]:
            page.goto(BASE + "bible.html?ref=" + reference, wait_until="domcontentloaded")
            page.wait_for_function("document.getElementById('kjv-status').textContent === ''")
            check(page.locator("#kjv-passage .kjv-selected").count() == verses, "Disjoint or single-chapter Scripture reference failed")
        page.goto(BASE + "guide-family-worship.html?course=foundations&lesson=15", wait_until="domcontentloaded")
        page.locator(".course-navigation").first.wait_for()
        page.locator('.course-navigation a[rel="next"]').first.click()
        page.wait_for_url("**/guide-work.html?course=foundations&lesson=15")
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
