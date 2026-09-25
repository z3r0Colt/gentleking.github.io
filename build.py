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

import datetime
import hashlib
import html
import json
import pathlib
import re
import subprocess
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
APP_REPO = "https://github.com/z3r0Colt/sojourner"

# Who writes the site, as the About page names him. Search engines and AI tools
# read this from the structured data, so it says only what that page says.
AUTHOR_NAME = "Colt"
AUTHOR_DESCRIPTION = (
    "A layman in the Reformed Presbyterian tradition who writes Gentle King and builds "
    "Sojourner. He is not a pastor or an elder and holds no office in the church."
)
AUTHOR_GITHUB = "https://github.com/z3r0Colt"

# The writing is under this license, as LICENSE says. The site code is MIT.
LICENSE_URL = "https://creativecommons.org/licenses/by-nc-nd/4.0/"

SCRIPTURE_NOTICE = (
    "Scripture quotations are from the Authorized Version, the King James Bible "
    "of 1611, which is in the public domain. If its older English is hard going, "
    "read the same passages in a careful modern translation such as the ESV or the NASB."
)

COPYRIGHT_YEAR = "2026"

# Nine items is the most the desktop nav holds on one line at 1025px.
# A tenth needs the 64rem breakpoint in site.css and the 1024 in site.js raised,
# or belongs in the footer.
NAV = [
    ("./", "Home"),
    ("gospel.html", "The Gospel"),
    ("comfort.html", "Comfort"),
    ("struggle.html", "Fighting Sin"),
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
            "Gentle King is a free Reformed ministry site. The gospel of Jesus Christ, Scripture "
            "for grief, help against sin, and Sojourner, a Bible study app for Windows."
        ),
        "hero": True,
        "toc": False,
    },
    {
        "file": "software.html",
        "content": "software.html",
        "title": "Sojourner",
        "full_title": "Sojourner \u00b7 Free Offline Bible Study Software for Windows",
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
            "Free offline Bible study software for Windows. Thirteen translations, the Hebrew and "
            "Greek, Matthew Henry, Calvin, Spurgeon, and the Westminster Standards."
        ),
        "schema": "ItemPage",
        "toc": True,
    },
    {
        "file": "gospel.html",
        "content": "gospel.html",
        "title": "The Gospel",
        "full_title": "The Gospel of Jesus Christ and How to Be Saved \u00b7 Gentle King",
        "eyebrow": "The Gospel",
        "h1": "The Gospel of Jesus Christ",
        "deck": (
            "The gospel is the good news that Jesus Christ, the Son of God, died for sinners and "
            "rose again, and that everyone who trusts in him alone is forgiven and counted "
            "righteous before God. Read it slowly. Nothing matters more."
        ),
        "description": (
            "What is the gospel? Who God is, what sin has done, how Christ died and rose for "
            "sinners, and how you are forgiven and made right with God by faith alone."
        ),
        "schema": "Article",
        "about": [
            "The gospel of Jesus Christ", "Sin", "The wrath of God",
            "The person and work of Christ", "Grace", "Repentance and faith",
            "Justification by faith alone",
        ],
        "toc": True,
    },
    {
        "file": "comfort.html",
        "content": "comfort.html",
        "title": "Scripture for the Hard Hour",
        "full_title": "Bible Verses for Grief and Hard Times (KJV) \u00b7 Gentle King",
        "eyebrow": "Comfort",
        "h1": "Scripture for the Hard Hour",
        "deck": (
            "For the day the hard news comes, and the long days after. King James Scripture and "
            "plain counsel for grief, loss by suicide, serious illness, a breaking marriage, a "
            "wandering child, lost work, a mind gone dark, and danger at home."
        ),
        "description": (
            "King James Bible verses and plain counsel for grief, the death of a spouse or child, "
            "suicide loss, illness, divorce, a prodigal child, depression, and danger."
        ),
        "schema": "Article",
        "about": [
            "Grief", "The death of a husband or wife", "The death of a child", "Suicide loss",
            "Serious illness", "A breaking marriage and divorce", "A child who turns from the Lord",
            "Loss of work or home", "Depression", "Safety from violence at home",
        ],
        "toc": False,
    },
    {
        "file": "struggle.html",
        "content": "struggle.html",
        "title": "Struggling With Sin",
        "full_title": "Struggling With Sin? How to Put It to Death \u00b7 Gentle King",
        "eyebrow": "Fighting Sin",
        "h1": "A Greater Affection",
        "deck": (
            "For anyone worn down by a sin that will not let go. A heart gives up an old love "
            "only for a stronger one, and Christ is the one love strong enough to drive the others out."
        ),
        "description": (
            "Worn down by the same sin? Scripture, John Owen, and the Westminster Standards on "
            "putting sin to death by the Spirit, and on assurance that rests on Christ."
        ),
        "schema": "Article",
        "about": [
            "Struggling with sin", "Mortification of sin", "Love for Christ",
            "Assurance of salvation",
        ],
        "toc": True,
    },
    {
        "file": "doctrine.html",
        "content": "doctrine.html",
        "title": "Doctrine",
        "full_title": "Reformed Theology and the Westminster Confession \u00b7 Gentle King",
        "eyebrow": "Doctrine",
        "h1": "What the Reformed Have Confessed",
        "deck": (
            "Scripture, the Trinity, the five solas, the doctrines of grace, covenant "
            "theology, the law and the gospel, the church, and the things to come."
        ),
        "description": (
            "What do Reformed Christians believe? The five solas, the doctrines of grace, covenant "
            "theology, and the last things, held to the Westminster Confession."
        ),
        "schema": "Article",
        "about": [
            "Reformed theology", "Westminster Confession of Faith", "The Trinity",
            "The five solas", "The doctrines of grace", "Covenant theology", "Law and gospel",
            "The church and the sacraments", "The last things",
        ],
        "toc": True,
    },
    {
        "file": "apologetics.html",
        "content": "apologetics.html",
        "title": "Apologetics",
        "full_title": "Christian Apologetics for Skeptics and Doubters \u00b7 Gentle King",
        "eyebrow": "Apologetics",
        "h1": "A Reason for the Hope",
        "deck": (
            "Straight answers for the one who objects to the faith, and comfort for the "
            "one who holds it with a shaking hand. Each has his own half of this page."
        ),
        "description": (
            "Honest answers to common objections to Christianity, from God and the Bible to evil "
            "and hell, and Scripture for the believer who fears he is not really saved."
        ),
        "schema": "Article",
        "about": [
            "Christian apologetics", "The existence of God", "The reliability of the Bible",
            "The resurrection of Jesus", "The problem of evil", "Hell", "Election",
            "Assurance of salvation", "Doubt",
        ],
        "toc": True,
    },
    {
        "file": "resources.html",
        "content": "resources.html",
        "title": "Resources",
        "full_title": "Reformed and Puritan Books, Where to Begin \u00b7 Gentle King",
        "eyebrow": "Reading and Study",
        "h1": "Where to Begin, and Where to Go Next",
        "deck": (
            "The confessions, the books worth your first year, the books worth the rest "
            "of your life, and the free tools that will help you read better."
        ),
        "description": (
            "Reformed and Puritan books for beginners and for going deeper, the Westminster "
            "Standards, free Bible study tools, and faithful preachers worth hearing."
        ),
        "schema": "CollectionPage",
        "about": [
            "Reformed books", "Puritan books", "Bible study tools", "Reformed preaching",
        ],
        "toc": True,
    },
    {
        "file": "about.html",
        "content": "about.html",
        "title": "About",
        "full_title": "About Gentle King \u00b7 Who Writes It and What It Believes",
        "eyebrow": "About",
        "h1": "About Gentle King",
        "deck": (
            "What this site is, what it is not, what is believed here, and how to reach out."
        ),
        "description": (
            "Gentle King is written by Colt, a layman in the Reformed Presbyterian tradition who "
            "also made Sojourner. What is believed here, and how to get in touch."
        ),
        "schema": "AboutPage",
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
<meta name="robots" content="max-image-preview:large">
<meta name="theme-color" content="#fbf8f2" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#151310" media="(prefers-color-scheme: dark)">
<meta name="color-scheme" content="light dark">
<meta property="og:type" content="{og_type}">
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
    <a class="brand" href="./">
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
          <li><a href="comfort.html">Comfort</a></li>
          <li><a href="struggle.html">Fighting Sin</a></li>
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


# --------------------------------------------------------------------------
# When each page last changed
#
# The sitemap and the structured data give each page a date. Search engines only
# trust a date that tells the truth, so a page's date moves only when its words
# move. The dates live in content/dates.json, which is committed. That way the
# rebuild in the Actions check writes the very same sitemap, even though it has
# none of the git history. A page the ledger has never seen starts from git.
# --------------------------------------------------------------------------

DATES = CONTENT / "dates.json"


def fingerprint(page):
    """The words a reader sees on the page. The title and description are left
    out, so tuning them for search does not pretend the page was rewritten."""
    body = (CONTENT / page["content"]).read_text(encoding="utf-8")
    shown = [str(page.get(key, "")) for key in ("h1", "deck")]
    return hashlib.sha256("\n".join(shown + [body]).encode("utf-8")).hexdigest()[:16]


def git_date(page, first):
    """The date of the first or the last commit that touched the page's words."""
    args = ["git", "log", "--format=%cI"]
    if first:
        args += ["--diff-filter=A", "--follow"]
    args += ["--", f"content/{page['content']}"]
    try:
        out = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return ""
    lines = out.split()
    return (lines[-1] if first else lines[0]) if lines else ""


def page_dates():
    """Read the ledger, move the date of any page whose words changed, save it."""
    try:
        ledger = json.loads(DATES.read_text(encoding="utf-8"))
    except FileNotFoundError:
        ledger = {}
    now = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()
    for page in PAGES:
        mark = fingerprint(page)
        seen = ledger.get(page["file"])
        if seen is None:
            ledger[page["file"]] = {
                "hash": mark,
                "published": git_date(page, first=True) or now,
                "modified": git_date(page, first=False) or now,
            }
        elif seen["hash"] != mark:
            seen["hash"] = mark
            seen["modified"] = now
    DATES.write_text(json.dumps(ledger, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return ledger


# --------------------------------------------------------------------------
# Structured data (JSON-LD)
#
# One connected graph per page, so search engines and AI tools can tell who
# publishes the site, who writes it, what each page is, and what Sojourner is.
# Say nothing here the pages do not say. No ratings, no reviews, no guessed
# dates. The Sojourner version, size, and screenshots are read from
# content/software.html, so they cannot drift from the page. The email
# addresses are left out on purpose, since the pages keep them from harvesters.
# --------------------------------------------------------------------------

ORG_ID = f"{SITE_URL}/#organization"
SITE_ID = f"{SITE_URL}/#website"
PERSON_ID = f"{SITE_URL}/#colt"
APP_ID = f"{SITE_URL}/software.html#app"
LOGO_URL = f"{SITE_URL}/brand/gentle-king-icon-512.png"

ORG_DESCRIPTION = (
    "A confessionally Reformed and Presbyterian ministry website. It sets out the gospel of "
    "Jesus Christ, Scripture for hard hours, help in the fight against sin, Reformed doctrine "
    "held to the Westminster Confession of Faith, apologetics, and reading resources, and it "
    "gives away Sojourner, a free Bible study app for Windows. It is the work of one layman "
    "and is not a church."
)

# Each line must match something software.html says. No counts here, so a
# release that changes a number only has to change the page.
APP_FEATURES = [
    "Works offline, with no account, no subscription, and no telemetry",
    "English Bible translations that are public domain or free to share, among them the King James of 1769 and the Geneva of 1599",
    "The Hebrew Old Testament, five editions of the Greek New Testament, the Septuagint, and the Vulgate",
    "Hebrew and Greek lexicons, an interlinear, word studies, and search by grammar",
    "Commentaries by Matthew Henry and John Calvin, and Spurgeon's Treasury of David",
    "The Westminster Confession and Catechisms with their Scripture proofs, and the Three Forms of Unity",
    "An encyclopedia, a Bible dictionary, cross references, a Factbook, an atlas, and a timeline",
    "Optional book shelves of Puritan and Reformed works, the Church Fathers, and more",
    "Linked panes that turn to the same verse together, and one search box for everything",
    "Notes, highlights, a prayer journal, reading plans, and Scripture and catechism memory",
    "A sermon editor with templates, a preaching mode, slides, handouts, and a podium file for phones",
    "A guided family worship page with a reading, a psalm, a catechism question, and prayer",
    "The 1650 Scottish Metrical Psalter with tunes that play",
]

CONFESSION_WORKS = [
    "Westminster Confession of Faith",
    "Westminster Larger Catechism",
    "Westminster Shorter Catechism",
]


def page_url(page):
    return f"{SITE_URL}/" if page["file"] == "index.html" else f"{SITE_URL}/{page['file']}"


def page_title(page):
    return page.get("full_title") or f"{page['title']} · {SITE_NAME}"


def og_image(page):
    return page.get("og_image", "og-cover.png?v=2")


def plain(fragment):
    """Visible text from a bit of HTML."""
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", fragment)).split())


def app_facts(body):
    """The version and download size, read from the Get Sojourner block."""
    version = re.search(r"<h3>Sojourner ([0-9][0-9.]*)</h3>", body)
    size = re.search(r'class="get-meta">[^<]*?About ([0-9,]+) MB', body)
    if not version or not size:
        raise SystemExit("software.html no longer shows the version and size where build.py looks")
    return version.group(1), size.group(1).replace(",", "")


def screenshots(body):
    """Each screenshot on the page, full size, with its caption."""
    shots = []
    for href, caption in re.findall(
        r'(?s)<figure class="shot[^"]*">\s*<a href="([^"]+)".*?<figcaption>(.*?)</figcaption>', body
    ):
        url = f"{SITE_URL}/{href}"
        shots.append({"@type": "ImageObject", "url": url, "contentUrl": url, "caption": plain(caption)})
    return shots


def citations(body):
    """The works a page actually quotes, found from its own quotation blocks."""
    found = []
    if 'class="scripture"' in body:
        found.append({"@type": "Book", "name": "The Holy Bible, King James Version"})
    cited = " ".join(re.findall(r'(?s)<blockquote class="confession">.*?<cite>(.*?)</cite>', body))
    for work in CONFESSION_WORKS:
        if work in cited:
            found.append({"@type": "CreativeWork", "name": work})
    return found


def shared_nodes():
    """The site, its publisher, and its writer, the same on every page."""
    return [
        {
            "@type": "WebSite",
            "@id": SITE_ID,
            "url": f"{SITE_URL}/",
            "name": SITE_NAME,
            "alternateName": "gentleking.org",
            "description": PAGES[0]["description"],
            "inLanguage": "en",
            "publisher": {"@id": ORG_ID},
        },
        {
            "@type": "Organization",
            "@id": ORG_ID,
            "name": SITE_NAME,
            "url": f"{SITE_URL}/",
            "description": ORG_DESCRIPTION,
            "logo": {
                "@type": "ImageObject",
                "@id": f"{SITE_URL}/#logo",
                "url": LOGO_URL,
                "contentUrl": LOGO_URL,
                "width": 512,
                "height": 512,
                "caption": SITE_NAME,
            },
            "image": {"@id": f"{SITE_URL}/#logo"},
            "founder": {"@id": PERSON_ID},
        },
        {
            "@type": "Person",
            "@id": PERSON_ID,
            "name": AUTHOR_NAME,
            "url": f"{SITE_URL}/about.html#who",
            "description": AUTHOR_DESCRIPTION,
            "sameAs": [AUTHOR_GITHUB],
        },
    ]


def software_node(page, canonical, body):
    version, size_mb = app_facts(body)
    return {
        "@type": "SoftwareApplication",
        "@id": APP_ID,
        "name": APP_NAME,
        "alternateName": APP_FULL,
        "description": page["description"],
        "url": canonical,
        "mainEntityOfPage": {"@id": f"{canonical}#webpage"},
        "image": f"{SITE_URL}/assets/img/sojourner-logo.png",
        "applicationCategory": "ReferenceApplication",
        "applicationSubCategory": "Bible study",
        "operatingSystem": "Windows 10, Windows 11",
        "processorRequirements": "64-bit",
        "softwareVersion": version,
        "fileSize": f"{size_mb}MB",
        "downloadUrl": APP_RELEASES,
        "isAccessibleForFree": True,
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD", "url": APP_RELEASES},
        "featureList": APP_FEATURES,
        "screenshot": screenshots(body),
        "inLanguage": "en",
        "author": {"@id": PERSON_ID},
        "publisher": {"@id": ORG_ID},
        "sameAs": APP_REPO,
    }


def structured_data(page, canonical, body, dates):
    """One JSON-LD graph for the page."""
    kind = page.get("schema", "WebPage")
    is_home = page["file"] == "index.html"
    webpage_id = f"{canonical}#webpage"
    when = dates[page["file"]]

    webpage = {
        "@type": kind if kind in ("ItemPage", "AboutPage", "CollectionPage") else "WebPage",
        "@id": webpage_id,
        "url": canonical,
        "name": page_title(page),
        "description": page["description"],
        "inLanguage": "en",
        "isPartOf": {"@id": SITE_ID},
        "primaryImageOfPage": {
            "@type": "ImageObject", "url": f"{SITE_URL}/assets/img/{og_image(page)}",
            "width": 1200, "height": 630,
        },
        "datePublished": when["published"],
        "dateModified": when["modified"],
        "license": LICENSE_URL,
    }
    graph = shared_nodes() + [webpage]

    if not is_home:
        webpage["breadcrumb"] = {"@id": f"{canonical}#breadcrumb"}
        graph.append({
            "@type": "BreadcrumbList",
            "@id": f"{canonical}#breadcrumb",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{SITE_URL}/"},
                {"@type": "ListItem", "position": 2, "name": page["title"], "item": canonical},
            ],
        })

    if is_home:
        webpage["about"] = {"@id": ORG_ID}
        webpage["mentions"] = {"@id": APP_ID}
    elif kind == "Article":
        webpage["mainEntity"] = {"@id": f"{canonical}#article"}
        article = {
            "@type": "Article",
            "@id": f"{canonical}#article",
            "headline": page["h1"],
            "description": page["description"],
            "image": [f"{SITE_URL}/assets/img/{og_image(page)}"],
            "author": {"@id": PERSON_ID},
            "publisher": {"@id": ORG_ID},
            "datePublished": when["published"],
            "dateModified": when["modified"],
            "inLanguage": "en",
            "mainEntityOfPage": {"@id": webpage_id},
            "isAccessibleForFree": True,
            "license": LICENSE_URL,
        }
        if page.get("about"):
            article["about"] = [{"@type": "Thing", "name": t} for t in page["about"]]
        cites = citations(body)
        if cites:
            article["citation"] = cites
        graph.append(article)
    elif kind == "ItemPage":
        webpage["mainEntity"] = {"@id": APP_ID}
        graph.append(software_node(page, canonical, body))
    else:
        webpage["author"] = {"@id": PERSON_ID}
        if kind == "AboutPage":
            webpage["about"] = {"@id": ORG_ID}
            webpage["mainEntity"] = {"@id": ORG_ID}
        elif page.get("about"):
            webpage["about"] = [{"@type": "Thing", "name": t} for t in page["about"]]

    text = json.dumps({"@context": "https://schema.org", "@graph": graph},
                      ensure_ascii=False, separators=(",", ":"))
    # A "</" inside the script block could end it early. JSON allows "<\/".
    text = text.replace("</", "<\\/")
    return f'<script type="application/ld+json">{text}</script>\n'


def nav_links(current):
    out = []
    for href, label in NAV:
        here = href == current or (href == "./" and current == "index.html")
        mark = ' aria-current="page"' if here else ""
        out.append(f'      <a href="{href}"{mark}>{label}</a>')
    return "\n".join(out)


def sections(body):
    """Each top level section of a page that has an h2, as (id, heading text)."""
    found = []
    for sid, inner in re.findall(r'(?s)<section class="section" id="([^"]+)"[^>]*>(.*?)</section>', body):
        h2 = re.search(r"(?s)<h2[^>]*>(.*?)</h2>", inner)
        if h2:
            found.append((sid, " ".join(re.sub(r"<[^>]+>", "", h2.group(1)).split())))
    return found


def toc_html(body):
    """The On this page list, written into the HTML so a reader without script,
    a search engine, or an AI tool sees the page's sections at the top. site.js
    builds the same list again on load. A page that shows one half at a time is
    left to the script, since its list depends on the half the reader chose."""
    empty = "<nav data-toc></nav>\n"
    found = sections(body)
    if "data-half" in body or len(found) < 3:
        return empty
    items = "".join(f'<li><a href="#{sid}">{text}</a></li>' for sid, text in found)
    return (
        '<nav data-toc class="toc" aria-label="On this page">'
        f'<p class="toc-title">On this page</p><ol>{items}</ol></nav>\n'
    )


def build_page(page, dates):
    fragment_path = CONTENT / page["content"]
    if not fragment_path.exists():
        raise SystemExit(f"missing content fragment: {fragment_path}")
    body = fragment_path.read_text(encoding="utf-8").strip()

    canonical = page_url(page)
    full_title = page_title(page)

    parts = [
        render(
            HEAD,
            full_title=html.escape(full_title, quote=True),
            description=html.escape(page["description"], quote=True),
            canonical=canonical,
            site_url=SITE_URL,
            site_name=SITE_NAME,
            og_type="article" if page.get("schema") == "Article" else "website",
            og_image=og_image(page),
            og_alt=html.escape(
                page.get(
                    "og_alt",
                    "Gentle King. Come unto me, all ye that labour and are heavy laden, "
                    "and I will give you rest. Matthew 11:28.",
                ),
                quote=True,
            ),
            structured_data=structured_data(page, canonical, body, dates),
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
        parts.append(toc_html(body))
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


# Named so the welcome is on the record, for search engines and for the AI
# tools that read the web on someone's behalf. They share one group with *,
# because a crawler that finds its own name obeys only that group, and one
# shared group means the Disallow lines can never be left off for any of them.
WELCOME_CRAWLERS = [
    "Googlebot", "Google-Extended", "bingbot", "Applebot", "Applebot-Extended",
    "DuckDuckBot", "DuckAssistBot", "OAI-SearchBot", "ChatGPT-User", "GPTBot",
    "Claude-SearchBot", "Claude-User", "ClaudeBot", "PerplexityBot", "Perplexity-User",
    "MistralAI-User", "Meta-WebIndexer", "Meta-ExternalAgent", "Meta-ExternalFetcher",
    "Amzn-SearchBot", "Amzn-User", "Amazonbot", "CCBot",
]

# Pages serves this repository as it stands, so the files that build the site
# sit next to it. A raw content fragment is half a page, and the README is
# notes for whoever edits the site, so keep crawlers on the pages themselves.
NOT_PAGES = ["/content/", "/.github/", "/README.md", "/build.py", "/check.py"]


def build_sitemap(dates):
    urls = []
    for page in PAGES:
        urls.append(
            f"  <url>\n    <loc>{page_url(page)}</loc>\n"
            f"    <lastmod>{dates[page['file']]['modified']}</lastmod>\n  </url>"
        )
    (ROOT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(urls)
        + "\n</urlset>\n",
        encoding="utf-8",
    )

    lines = [
        "# Gentle King welcomes search engines and AI assistants.",
        "# The paths below are the files that build the site, not pages.",
        "",
        "User-agent: *",
        *[f"User-agent: {name}" for name in WELCOME_CRAWLERS],
        "Allow: /",
        *[f"Disallow: {path}" for path in NOT_PAGES],
        "",
        f"Sitemap: {SITE_URL}/sitemap.xml",
    ]
    (ROOT / "robots.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


# The groups llms.txt sorts the pages into, in order. The ministry writing comes
# before the app, because it matters as much or more.
LLMS_GROUPS = [
    ("The gospel", ["gospel.html"]),
    ("Comfort in hard hours", ["comfort.html"]),
    ("Fighting sin", ["struggle.html"]),
    ("Doctrine", ["doctrine.html"]),
    ("Apologetics", ["apologetics.html"]),
    ("Reading and study", ["resources.html"]),
]


def build_llms_txt():
    """A plain map of the site for AI assistants, in the llms.txt format
    (https://llmstxt.org). Written from PAGES and from each page's own section
    headings, so it can never disagree with the pages."""
    by_file = {p["file"]: p for p in PAGES}
    app_body = (CONTENT / "software.html").read_text(encoding="utf-8")
    version, size_mb = app_facts(app_body)

    def entry(page):
        url = page_url(page)
        out = [f"- [{page['h1'] if page.get('h1') else page['title']}]({url}): {page['description']}"]
        body = (CONTENT / page["content"]).read_text(encoding="utf-8")
        out += [f"- [{text}]({url}#{sid})" for sid, text in sections(body)]
        return out

    lines = [
        f"# {SITE_NAME}",
        "",
        f"> {SITE_NAME} ({SITE_URL.split('//')[-1]}) is a free ministry site, confessionally "
        "Reformed and Presbyterian. It sets out the gospel of Jesus Christ, Scripture for grief "
        "and other hard hours, help for the fight against sin, Reformed doctrine held to the "
        "Westminster Confession of Faith, answers to objections against Christianity, and "
        f"{APP_NAME}, a free offline Bible study app for Windows.",
        "",
        f"The site is written by {AUTHOR_NAME}, a layman in the Reformed Presbyterian tradition. "
        "He is not a pastor or an elder, and the site is no substitute for a local church. "
        "Scripture is quoted from the King James Version. The Westminster Standards are quoted "
        "from the text of 1647. The writing may be copied and shared freely under the Creative "
        "Commons Attribution-NonCommercial-NoDerivatives 4.0 license. Please do not sell it, and "
        "please do not change the words and keep the name on it.",
        "",
        "Anyone in danger or thinking of ending their life can call 911, or call or text 988, in "
        "the United States. Outside the United States, call the local emergency number. The "
        "comfort page gives these numbers and more.",
        "",
    ]
    for heading, files in LLMS_GROUPS:
        lines += [f"## {heading}", ""]
        for name in files:
            lines += entry(by_file[name])
        lines.append("")

    app = by_file["software.html"]
    lines += [
        f"## {APP_NAME}, a free Bible study app",
        "",
        f"{APP_NAME} {version} is free Bible study software for Windows 10 and 11, 64-bit. "
        f"It needs no account, works with the network off, and sends no telemetry. The "
        f"installer is about {size_mb} MB. It is made by the same writer and given away free.",
        "",
    ]
    lines += entry(app)
    lines += [
        f"- [Download {APP_NAME}]({APP_RELEASES}): The Windows installer and the four optional "
        "book shelves, on GitHub",
        "",
        "## Optional",
        "",
        f"- [Home]({SITE_URL}/): The gospel in brief, why the site is called Gentle King, "
        "and what it holds",
    ]
    lines += entry(by_file["about.html"])
    lines += [
        f"- [License]({REPO_URL}/blob/main/LICENSE): The terms for the writing and the site code",
        "",
    ]
    (ROOT / "llms.txt").write_text("\n".join(lines), encoding="utf-8")


def main():
    dates = page_dates()
    total = 0
    for page in PAGES:
        name, words = build_page(page, dates)
        total += words
        print(f"  {name:<18} {words:>6,} words")
    build_sitemap(dates)
    build_llms_txt()
    host = build_cname()
    print(f"  {'sitemap.xml':<18} {'':>6}")
    print(f"  {'robots.txt':<18} {'':>6}")
    print(f"  {'llms.txt':<18} {'':>6}")
    print(f"  {'CNAME':<18} {host:>6}")
    print(f"\nBuilt {len(PAGES)} pages, {total:,} words.")


if __name__ == "__main__":
    sys.exit(main())
