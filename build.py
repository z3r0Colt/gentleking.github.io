#!/usr/bin/env python3
"""
Gentle King, site builder.

Every page on this site is plain static HTML. This script exists so the header,
the footer, and all of the <head> metadata live in exactly one place instead of
in every page. It reads a content fragment out of content/ and wraps it in the shell.

    python3 build.py

That writes the .html files at the top of the repo. Commit those files. GitHub
Pages serves them directly and never runs this script.

To change the wording of a page, edit the matching file in content/ and run the
script again. To change the header, the footer, or the metadata, edit this file.
"""

import html
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).parent.resolve()
CONTENT = ROOT / "content"

# --------------------------------------------------------------------------
# Site settings. Change these and rebuild.
# --------------------------------------------------------------------------

SITE_NAME = "Gentle King"
SITE_TAGLINE = "The King who is gentle toward sinners reigns over all things."

# Where the site is actually served from, used for canonical links and for the
# preview card that shows up when someone shares a page. If you point a custom
# domain at this repository, put it here (for example "https://gentleking.org")
# and add the same domain to the CNAME file.
SITE_URL = "https://gentleking.org"

REPO_URL = "https://github.com/z3r0Colt/gentleking.github.io"

# The Bible study software.
APP_NAME = "Sojourner"
APP_FULL = "Sojourner, Bible Study Companion"
APP_RELEASES = "https://github.com/z3r0Colt/sojourner/releases"
APP_EMAIL = "sojourner@gentleking.org"

SCRIPTURE_NOTICE = (
    "Scripture quotations are from the Authorized Version, the King James Bible "
    "of 1611, which is in the public domain. If its older English is hard going, "
    "read the same passages in a careful modern translation such as the ESV or the NASB."
)

COPYRIGHT_YEAR = "2026"

# Eight items is the most the desktop nav holds on one line at 993px.
# A ninth needs the 62rem breakpoint in site.css raised, or belongs in the footer.
NAV = [
    ("index.html", "Home"),
    ("gospel.html", "The Gospel"),
    ("software.html", "Sojourner"),
    ("doctrine.html", "Doctrine"),
    ("apologetics.html", "Apologetics"),
    ("resources.html", "Resources"),
    ("about.html", "About"),
]

# --------------------------------------------------------------------------
# Pages
# --------------------------------------------------------------------------

PAGES = [
    {
        "file": "index.html",
        "content": "index.html",
        "title": SITE_NAME,
        "full_title": "Gentle King · The gospel of Jesus Christ and the Reformed faith",
        "description": (
            "Jesus Christ, the gentle King, calls the weary to come to him for rest. Read his "
            "gospel and the Reformed faith here, and find Sojourner, a free Bible study companion."
        ),
        "hero": True,
        "toc": False,
    },
    {
        "file": "software.html",
        "content": "software.html",
        "title": "Sojourner",
        "full_title": "Sojourner \u00b7 A Bible study companion for Windows",
        "eyebrow": "Bible Study Companion",
        "h1": "Sojourner",
        "logo": "sojourner-logo",
        "logo_alt": "Sojourner, Bible Study Companion",
        "og_image": "og-sojourner.png",
        "og_alt": "Sojourner, Bible Study Companion. A free, offline Bible study companion for Windows.",
        "deck": (
            "Scripture beside the commentaries, confessions, and reference works of the "
            "Reformed church. It runs on your own Windows machine, it works with the network off, "
            "and it is free."
        ),
        "description": (
            "Sojourner is a free offline Bible study companion for Windows. Ten translations, "
            "Calvin and Henry and Spurgeon, the Westminster Standards, a word-by-word interlinear "
            "in Hebrew and Greek, and a 9,349 article encyclopedia, all on your own machine."
        ),
        "toc": True,
    },
    {
        "file": "gospel.html",
        "content": "gospel.html",
        "title": "The Gospel",
        "eyebrow": "The Gospel",
        "h1": "The Gospel of Jesus Christ",
        "deck": (
            "Who God is, what sin has done, what Christ has accomplished, and what he "
            "calls you to do about it. Read it slowly. Nothing matters more."
        ),
        "description": (
            "The full gospel from a confessional Reformed position. God, sin, the wrath to come, "
            "the person and work of Christ, grace alone, repentance and faith, and justification."
        ),
        "toc": True,
    },
    {
        "file": "comfort.html",
        "content": "comfort.html",
        "title": "Scripture for the Hard Hour",
        "eyebrow": "Comfort",
        "h1": "Scripture for the Hard Hour",
        "deck": "For the day the hard news comes, and the long days after.",
        "description": (
            "Christ-centered Scripture for the hard hour. King James passages for grief, loss by "
            "suicide, serious illness, a broken marriage, a wandering child, lost work, depression, "
            "and danger at home."
        ),
        "toc": False,
    },
    {
        # Kept out of NAV and the footer for now, like Comfort. Reached by link.
        "file": "struggle.html",
        "content": "struggle.html",
        "title": "Struggling With Sin",
        "eyebrow": "Fighting Sin",
        "h1": "A Greater Affection",
        "deck": (
            "For anyone worn down by a sin that will not let go. A heart gives up an old love "
            "only for a stronger one, and Christ is the one love strong enough to drive the others out."
        ),
        "description": (
            "Help from Scripture and the Westminster Standards for anyone struggling with sin. "
            "A greater love for Christ, the daily work of putting sin to death by the Spirit, and "
            "an assurance that rests on Christ and not on a winning streak."
        ),
        "toc": True,
    },
    {
        "file": "doctrine.html",
        "content": "doctrine.html",
        "title": "Doctrine",
        "eyebrow": "Doctrine",
        "h1": "What the Reformed Have Confessed",
        "deck": (
            "Scripture, the Trinity, the five solas, the doctrines of grace, covenant "
            "theology, the law and the gospel, the church, and the things to come."
        ),
        "description": (
            "A plain tour of Reformed doctrine held to the Westminster Confession of Faith. "
            "The solas, the doctrines of grace, covenant theology, and last things."
        ),
        "toc": True,
    },
    {
        "file": "apologetics.html",
        "content": "apologetics.html",
        "title": "Apologetics",
        "eyebrow": "Apologetics",
        "h1": "A Reason for the Hope",
        "deck": (
            "Straight answers for the one who objects to the faith, and comfort for the "
            "one who holds it with a shaking hand. Each has his own half of this page."
        ),
        "description": (
            "Reformed apologetics in plain words. Honest answers to the common objections "
            "to Christianity, and comfort from Scripture and the Westminster Confession for "
            "the believer who doubts."
        ),
        "toc": True,
    },
    {
        "file": "resources.html",
        "content": "resources.html",
        "title": "Resources",
        "eyebrow": "Reading and Study",
        "h1": "Where to Begin, and Where to Go Next",
        "deck": (
            "The confessions, the books worth your first year, the books worth the rest "
            "of your life, and the free tools that will help you read better."
        ),
        "description": (
            "Curated Reformed reading and study resources. Confessions and catechisms, books "
            "for beginners and for going deeper, free study tools, and faithful preaching."
        ),
        "toc": True,
    },
    {
        "file": "about.html",
        "content": "about.html",
        "title": "About",
        "eyebrow": "About",
        "h1": "About Gentle King",
        "deck": (
            "What this site is, what it is not, what is believed here, and how to reach out."
        ),
        "description": (
            "About the Gentle King ministry site, its statement of faith, and how to get in touch."
        ),
        "toc": True,
    },
]

# --------------------------------------------------------------------------
# Shell pieces
# --------------------------------------------------------------------------

MARK_SVG = (
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" '
    'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">'
    '<path d="M3.9 18.4V6.9l4.2 4.8L12 5.4l3.9 6.3 4.2-4.8v11.5z"/>'
    '<path d="M3.9 15.1h16.2" stroke-width="1.2"/>'
    '<circle cx="12" cy="8.7" r=".85" fill="currentColor" stroke="none"/>'
    "</svg>"
)

HEAD = """<!DOCTYPE html>
<html lang="en" prefix="og: https://ogp.me/ns#">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{full_title}</title>
<meta name="description" content="{description}">
<link rel="canonical" href="{canonical}">
<meta name="theme-color" content="#fbf8f2" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#151310" media="(prefers-color-scheme: dark)">
<meta name="color-scheme" content="light dark">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{site_name}">
<meta property="og:title" content="{full_title}">
<meta property="og:description" content="{description}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{site_url}/assets/img/{og_image}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{og_alt}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{full_title}">
<meta name="twitter:description" content="{description}">
<meta name="twitter:image" content="{site_url}/assets/img/{og_image}">
<link rel="icon" href="assets/img/favicon.svg" type="image/svg+xml">
<link rel="alternate icon" href="assets/img/favicon.ico" sizes="any">
<link rel="apple-touch-icon" href="assets/img/apple-touch-icon.png">
<link rel="preload" href="assets/fonts/ebgaramond-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="assets/css/site.css">
<script>
/* Applied before paint. The js class lets a page hide what script will reveal,
   so nothing flashes, and a reader who chose a theme never sees the other one. */
document.documentElement.classList.add('js');
(function(){try{var t=localStorage.getItem('gk-theme');if(t){document.documentElement.setAttribute('data-theme',t);}}catch(e){}})();
</script>
{structured_data}</head>
<body>
<a class="skip-link" href="#main">Skip to content</a>
"""

HEADER = """<header class="site-header">
  <div class="wrap">
    <a class="brand" href="index.html">
      {mark}
      <span class="brand-name">Gentle King</span>
    </a>
    <nav class="nav" id="primary-nav" data-open="false" aria-label="Primary">
{nav_links}
    </nav>
    <div class="nav-tools">
      <button class="icon-btn theme-toggle" type="button" aria-label="Switch between light and dark">
        <svg class="sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>
        <svg class="moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>
      </button>
      <button class="icon-btn nav-toggle" type="button" aria-label="Menu" aria-expanded="false" aria-controls="primary-nav">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h16"/></svg>
      </button>
    </div>
  </div>
</header>
"""

HERO = """<section class="hero hero-word">
  <div class="wrap">
    <p class="eyebrow">The Lord Jesus Christ</p>
    <h1>Come unto me, all ye that labour and are heavy laden, and I will give you rest.</h1>
    <p class="hero-ref">Matthew 11:28 (KJV)</p>
    <p class="hero-deck">He is the eternal Son of God, made man. On the cross he bore the wrath of
      God in the place of sinners, and on the third day he rose from the dead. He is speaking to
      you, and he means every word.</p>
    <div class="btn-row">
      <a class="btn btn-primary" href="#the-gospel">Hear the gospel</a>
    </div>
  </div>
</section>
"""

PAGE_HEAD = """<div class="page-head">
  <div class="wrap">
    <p class="eyebrow">{eyebrow}</p>
    <h1>{h1}</h1>
    <p class="page-deck">{deck}</p>
  </div>
</div>
"""

# A page with its own mark shows it in place of a typeset name. The name still
# sits in the heading for screen readers and for search, just not drawn twice.
PAGE_HEAD_LOGO = """<div class="page-head page-head-logo">
  <div class="wrap">
    <h1 class="brandmark">
      <img class="brandmark-light" src="assets/img/{logo}.webp" width="620" height="462"
           alt="" decoding="async">
      <img class="brandmark-dark" src="assets/img/{logo}-dark.webp" width="620" height="461"
           alt="" decoding="async">
      <span class="visually-hidden">{logo_alt}</span>
    </h1>
    <p class="page-deck">{deck}</p>
  </div>
</div>
"""

FOOTER = """<footer class="site-footer">
  <div class="wrap">
    <div class="footer-grid">
      <div>
        <p class="footer-verse">Take my yoke upon you, and learn of me; for I am meek and lowly
          in heart: and ye shall find rest unto your souls.</p>
        <p class="footer-verse-ref">Matthew 11:29 (KJV)</p>
      </div>
      <div>
        <p class="footer-head">Read</p>
        <ul class="footer-links">
          <li><a href="gospel.html">The Gospel</a></li>
          <li><a href="doctrine.html">Doctrine</a></li>
          <li><a href="apologetics.html">Apologetics</a></li>
          <li><a href="resources.html">Resources</a></li>
        </ul>
      </div>
      <div>
        <p class="footer-head">Get</p>
        <ul class="footer-links">
          <li><a href="software.html">Sojourner</a></li>
          <li><a href="about.html#contact">Contact</a></li>
        </ul>
      </div>
      <div>
        <p class="footer-head">Elsewhere</p>
        <ul class="footer-links">
          <li><a href="https://thewestminsterstandard.org/the-westminster-confession/" target="_blank" rel="noopener">Westminster Confession</a></li>
        </ul>
      </div>
    </div>
    <div class="footer-base">
      <p>&copy; {year} Gentle King. Everything written here may be copied and shared freely.</p>
      <p><a href="about.html">About this site</a></p>
    </div>
    <p class="footer-fineprint">{scripture_notice}</p>
  </div>
</footer>

<button class="to-top" type="button" aria-label="Back to top">
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 19V5M5 12l7-7 7 7"/></svg>
</button>

<script src="assets/js/site.js" defer></script>
</body>
</html>
"""


def render(template, **fields):
    """Fill {name} slots by plain replacement.

    Python's own str.format is not used here because the templates contain
    JavaScript, and every brace in that script would have to be doubled.
    """
    out = template
    for key, value in fields.items():
        out = out.replace("{" + key + "}", value)
    return out


def structured_data(page, canonical):
    """A small JSON-LD block so search engines and link previews read the site right."""
    if page["file"] != "index.html":
        return ""
    return (
        '<script type="application/ld+json">'
        '{"@context":"https://schema.org","@type":"WebSite",'
        f'"name":"{SITE_NAME}","url":"{SITE_URL}/",'
        f'"description":"{html.escape(page["description"], quote=False)}",'
        '"publisher":{"@type":"Organization","name":"Gentle King",'
        f'"url":"{SITE_URL}/","logo":"{SITE_URL}/assets/img/apple-touch-icon.png"}}'
        "}</script>\n"
    )


def nav_links(current):
    out = []
    for href, label in NAV:
        mark = ' aria-current="page"' if href == current else ""
        out.append(f'      <a href="{href}"{mark}>{label}</a>')
    return "\n".join(out)


def build_page(page):
    fragment_path = CONTENT / page["content"]
    if not fragment_path.exists():
        raise SystemExit(f"missing content fragment: {fragment_path}")
    body = fragment_path.read_text(encoding="utf-8").strip()

    canonical = f"{SITE_URL}/" if page["file"] == "index.html" else f"{SITE_URL}/{page['file']}"
    full_title = page.get("full_title") or f"{page['title']} · {SITE_NAME}"

    parts = [
        render(
            HEAD,
            full_title=html.escape(full_title, quote=True),
            description=html.escape(page["description"], quote=True),
            canonical=canonical,
            site_url=SITE_URL,
            site_name=SITE_NAME,
            og_image=page.get("og_image", "og-cover.png?v=2"),
            og_alt=html.escape(
                page.get(
                    "og_alt",
                    "Gentle King. Come unto me, all ye that labour and are heavy laden, "
                    "and I will give you rest. Matthew 11:28.",
                ),
                quote=True,
            ),
            structured_data=structured_data(page, canonical),
        ),
        render(HEADER, mark=MARK_SVG, nav_links=nav_links(page["file"])),
    ]

    if page.get("hero"):
        parts.append(HERO)
    elif page.get("logo"):
        parts.append(
            render(
                PAGE_HEAD_LOGO,
                logo=page["logo"],
                logo_alt=html.escape(page["logo_alt"], quote=True),
                deck=html.escape(page["deck"], quote=False),
            )
        )
    else:
        parts.append(
            render(
                PAGE_HEAD,
                eyebrow=html.escape(page["eyebrow"], quote=False),
                h1=html.escape(page["h1"], quote=False),
                deck=html.escape(page["deck"], quote=False),
            )
        )

    main_class = "wrap page-body has-toc" if page.get("toc") else "wrap page-body"
    parts.append(f'<main id="main" class="{main_class}">\n')
    if page.get("toc"):
        parts.append('<nav data-toc></nav>\n')
    parts.append(body)
    parts.append("\n</main>\n\n")
    parts.append(render(FOOTER, year=COPYRIGHT_YEAR, scripture_notice=SCRIPTURE_NOTICE))

    (ROOT / page["file"]).write_text("".join(parts), encoding="utf-8")
    words = len(re.sub(r"<[^>]+>", " ", body).split())
    return page["file"], words


def build_cname():
    """The custom domain, written from SITE_URL so the two cannot drift apart."""
    host = SITE_URL.split("//", 1)[-1].rstrip("/")
    (ROOT / "CNAME").write_text(host + "\n", encoding="utf-8")
    return host


def build_sitemap():
    urls = []
    for page in PAGES:
        loc = f"{SITE_URL}/" if page["file"] == "index.html" else f"{SITE_URL}/{page['file']}"
        priority = "1.0" if page["file"] == "index.html" else "0.8"
        urls.append(
            f"  <url>\n    <loc>{loc}</loc>\n"
            f"    <changefreq>monthly</changefreq>\n"
            f"    <priority>{priority}</priority>\n  </url>"
        )
    (ROOT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(urls)
        + "\n</urlset>\n",
        encoding="utf-8",
    )

    # Pages serves this repository as it stands, so the source folders sit next
    # to the site. Keep search engines out of them, since a raw content fragment
    # is half a page and would only confuse anyone who landed on it.
    (ROOT / "robots.txt").write_text(
        "User-agent: *\n"
        "Allow: /\n"
        "Disallow: /content/\n"
        "Disallow: /.github/\n"
        f"\nSitemap: {SITE_URL}/sitemap.xml\n",
        encoding="utf-8",
    )


def main():
    total = 0
    for page in PAGES:
        name, words = build_page(page)
        total += words
        print(f"  {name:<18} {words:>6,} words")
    build_sitemap()
    host = build_cname()
    print(f"  {'sitemap.xml':<18} {'':>6}")
    print(f"  {'robots.txt':<18} {'':>6}")
    print(f"  {'CNAME':<18} {host:>6}")
    print(f"\nBuilt {len(PAGES)} pages, {total:,} words.")


if __name__ == "__main__":
    sys.exit(main())
