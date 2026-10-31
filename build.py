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

import collections
import datetime
import functools
import hashlib
import html
import itertools
import json
import pathlib
import re
import shutil
import subprocess
import sys
from reference_links import link_references

ROOT = pathlib.Path(__file__).parent.resolve()
CONTENT = ROOT / "content"

# --------------------------------------------------------------------------
# Site settings. Change these and rebuild.
# --------------------------------------------------------------------------

SITE_NAME = "Gentle King"
GOSPEL_SUMMARY = json.loads((ROOT / "biblehelps/assets/content.json").read_text(encoding="utf-8"))["metadata"]["gospelSummary"]
SITE_TAGLINE = "The King who is gentle toward sinners reigns over all things."

# Where the site is actually served from, used for canonical links and for the
# preview card that shows up when someone shares a page. If you point a custom
# domain at this repository, put it here (for example "https://gentleking.org")
# and add the same domain to the CNAME file.
SITE_URL = "https://gentleking.org"

REPO_URL = "https://github.com/z3r0Colt/gentleking.github.io"

# Where the Donate button in the footer goes.
DONATE_URL = "https://buymeacoffee.com/gentlekingministry"

# The Bible study software.
APP_NAME = "Sojourner"
APP_FULL = "Sojourner, Bible Study Companion"
APP_RELEASES = "https://github.com/z3r0Colt/sojourner/releases"
APP_EMAIL = "sojourner@gentleking.org"
APP_REPO = "https://github.com/z3r0Colt/sojourner"
APP_PAGE = "sojourner.html"
# The same app as a web app, for phones, tablets, Macs, and any browser.
APP_WEB_URL = "https://app.gentleking.org/"
APP_WEB_PAGE = "sojourner-web.html"
# The current release. Written into the pages wherever {{version}}, {{size}},
# {{size_deb}}, and {{size_appimage}} appear, into the structured data, and into
# llms.txt, so a new release changes these four lines and nothing else. The sizes
# are the ones the release notes give, for the Windows installer, the Linux .deb,
# and the Linux AppImage.
APP_VERSION = "0.4.3"
APP_SIZE_MB = "594"
APP_SIZE_DEB_MB = "519"
APP_SIZE_APPIMAGE_MB = "626"

# The web app for the fight against sin. It lives at its own address, and the
# Fighting Sin page is its home on this site.
MORTIFY_NAME = "Mortify"
MORTIFY_URL = "https://mortify.gentleking.org/"
MORTIFY_PAGE = "mortify.html"

# The line that points to Mortify's page, on the home page and the Fighting Sin page.
MORTIFY_NOTICE = {
    "label": MORTIFY_NAME,
    "icon": '<img src="assets/img/mortify-icon-64.png" width="64" height="64" alt="">',
    "text": f"<strong>{MORTIFY_NAME}</strong>, a free app for the fight against sin.",
    "go": "See it",
    "href": MORTIFY_PAGE,
}

# The line that points to Sojourner in the browser, on the home page.
SOJOURNER_WEB_NOTICE = {
    "label": "Sojourner on the web",
    "icon": '<img src="assets/img/sojourner-icon-64.png" width="64" height="64" alt="">',
    "text": "<strong>Sojourner</strong> now runs in your browser, on your phone, tablet, or Mac.",
    "go": "See how",
    "href": APP_WEB_PAGE,
}

# Who writes the site, as the About page names him. Search engines and AI tools
# read this from the structured data, so it says only what that page says.
AUTHOR_NAME = "Colt"
AUTHOR_DESCRIPTION = (
    "A layman in the Reformed Presbyterian tradition who writes Gentle King and builds "
    "Sojourner. He isn't a pastor or an elder and holds no office in the church."
)
AUTHOR_GITHUB = "https://github.com/z3r0Colt"

# The writing is under this license, as LICENSE says. The site code is MIT.
LICENSE_URL = "https://creativecommons.org/licenses/by-nc-nd/4.0/"

SCRIPTURE_NOTICE = (
    "Scripture quotations are from the Authorized Version, the King James Bible "
    "of 1611. The KJV is in the public domain in the United States. Crown rights apply "
    "in the United Kingdom. If its older English is hard going, "
    "read the same passages in a careful modern translation such as the ESV or the NASB."
)

COPYRIGHT_YEAR = "2026"

# The ministry's own pages come first, with the gospel at the head of them. The
# two apps are tools of the ministry, so they sit together at the end of the row
# under Tools, a small menu that opens on a click. On a phone every page folds
# into the menu, and the header keeps one link of its own beside the menu
# button, the gospel. The row fits on one line from 1025px. Another item needs
# the 64rem breakpoint in site.css and the 1024 in site.js raised, or belongs in
# the footer.
NAV = [
    ("start-here.html", "Start Here"),
    ("help.html", "Find Help"),
    ("learn.html", "Learn the Faith"),
    ("guides.html", "Guides"),
    ("search.html", "Search"),
]

# The apps under Tools, each with a line saying what it is for.
TOOLS = [
    ("bible.html", "KJV Bible", "Read Scripture on Gentle King"),
    ("biblehelps/", "Bible Reading Helps", "Book guides and study lessons"),
    (APP_PAGE, APP_NAME, "Bible study on any device"),
    (MORTIFY_PAGE, MORTIFY_NAME, "For the fight against sin"),
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
            "Gentle King, a free Reformed ministry. The gospel of Jesus Christ, Scripture for "
            "grief, help against sin, and Sojourner, Bible study on any device."
        ),
        "hero": True,
        "notice": SOJOURNER_WEB_NOTICE,
        "toc": False,
    },
    {
        "file": "sojourner.html",
        "content": "sojourner.html",
        "title": "Sojourner",
        "full_title": "Sojourner Bible Study \u00b7 Free for Phone, Tablet, Windows, Mac, and Linux",
        "eyebrow": "Bible Study Companion",
        "h1": "Sojourner",
        "logo": "sojourner-logo",
        "logo_alt": "Sojourner, Bible Study Companion",
        "og_image": "og-sojourner.png",
        "og_alt": "Sojourner, Bible Study Companion. A free, private Bible study companion for any device.",
        "deck": (
            "A free Bible study program for your phone, tablet, or computer, for the pastor, the "
            "family, and the student. Scripture beside the commentaries, confessions, and reference "
            "works of the Reformed church, with no account and nothing to buy."
        ),
        "description": (
            "Free Bible study for phone, tablet, and computer. Thirteen translations, the Hebrew "
            "and Greek, Matthew Henry, Calvin, and the Westminster Standards."
        ),
        "schema": "ItemPage",
        # The first screen says what it is, for whom, and where to get it.
        "facts": ["Free", "Phone, tablet, and computer", "Works offline", "No account", "No telemetry"],
        "head_shot": "sojourner-shot",
        "toc": True,
    },
    {
        "file": MORTIFY_PAGE,
        "content": "mortify.html",
        "title": MORTIFY_NAME,
        "full_title": "Mortify \u00b7 A Free App for Putting Sin to Death by the Spirit",
        "h1": MORTIFY_NAME,
        # The page leads with the app's own mark, Jeremiah 3:22, and a way in.
        "app_head": {
            "icon": "mortify-icon-512.png",
            "verse": (
                "Return, ye backsliding children, and I will heal your backslidings. Behold, "
                "we come unto thee; for thou art the LORD our God."
            ),
            "ref": "Jeremiah 3:22 (KJV)",
            "href": MORTIFY_URL,
            "go": "Open Mortify",
        },
        "deck": (
            "A free app for the daily work of putting sin to death by the Spirit. It meets you "
            "in the hour of temptation, morning and evening, and after a fall, and it sends you "
            "back to Christ every time."
        ),
        "description": (
            "Mortify is a free app for putting sin to death by the Spirit. Flee in temptation, "
            "a morning reading, an evening examination, and help after a fall."
        ),
        "og_image": "og-mortify.png",
        "og_alt": "Mortify. A free app for putting sin to death by the Spirit.",
        "schema": "ItemPage",
        "app": "mortify",
        "toc": True,
    },
    {
        "file": "gospel.html",
        "content": "gospel.html",
        "title": "The Gospel",
        "full_title": "The Gospel of Jesus Christ and How to Be Saved \u00b7 Gentle King",
        "eyebrow": "The Gospel",
        "h1": "The Gospel of Jesus Christ",
        "deck": GOSPEL_SUMMARY,
        "description": (
            "What is the gospel? Who God is, what sin has done, how Christ died and rose for "
            "sinners, and how you're forgiven and made right with God by faith alone."
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
        "title": "Grief and Hard Times",
        "full_title": "Bible Verses for Grief and Hard Times (KJV) \u00b7 Gentle King",
        "eyebrow": "Comfort",
        "h1": "Grief and Hard Times",
        "crumb": "Comfort",
        "deck": (
            "For the day the hard news comes, and the long days after. King James Scripture and "
            "plain counsel, gathered by sorrow. Find yours below."
        ),
        "description": (
            "King James Bible verses and plain counsel for grief, the death of a spouse or child, "
            "suicide loss, illness, divorce, a prodigal child, depression, and danger."
        ),
        "schema": "CollectionPage",
        # Old links into the one long page this used to be still land on the
        # right part. site.js follows them.
        "moved": "comfort",
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
        "h1": "Struggling With Sin",
        "deck": (
            "For anyone worn down by a sin that won't let go. A heart gives up an old love "
            "only for a stronger one, and Christ is the one love strong enough to drive the others out."
        ),
        "description": (
            "Worn down by the same sin? Scripture, John Owen, and the Westminster Standards on "
            "putting sin to death by the Spirit, and on assurance that rests on Christ."
        ),
        "schema": "Article",
        # A line under the page head, so a reader in temptation finds Mortify on
        # the first screen. It goes to Mortify's own page.
        "notice": MORTIFY_NOTICE,
        "about": [
            "Struggling with sin", "Mortification of sin", "Love for Christ",
            "Assurance of salvation",
        ],
        "cites": [
            {"@type": "Book", "name": "Of the Mortification of Sin in Believers",
             "author": {"@type": "Person", "name": "John Owen"}},
            {"@type": "Book", "name": "Indwelling Sin",
             "author": {"@type": "Person", "name": "John Owen"}},
            {"@type": "CreativeWork", "name": "The Expulsive Power of a New Affection",
             "author": {"@type": "Person", "name": "Thomas Chalmers"}},
            {"@type": "Book", "name": "The Bruised Reed",
             "author": {"@type": "Person", "name": "Richard Sibbes"}},
        ],
        "toc": True,
    },
    {
        "file": "doctrine.html",
        "content": "doctrine.html",
        "title": "Doctrine",
        "full_title": "Reformed Theology and the Westminster Confession \u00b7 Gentle King",
        "eyebrow": "Doctrine",
        "h1": "What We Believe",
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
        "h1": "Questions About Christianity",
        "deck": (
            "Answers to questions about God, Scripture, suffering, and the resurrection. "
            "For fears about your own salvation, follow the links to Assurance and Doubt."
        ),
        "description": (
            "Honest answers to common objections to Christianity, from God and the Bible to evil "
            "and hell, and Scripture for the believer who fears he isn't really saved."
        ),
        "schema": "CollectionPage",
        "about": [
            "Christian apologetics", "The existence of God", "The reliability of the Bible",
            "The resurrection of Jesus", "The problem of evil", "Hell", "Election",
            "Assurance of salvation", "Doubt",
        ],
        "moved": "apologetics",
        "toc": False,
    },
    {
        "file": "guides.html",
        "content": "guides.html",
        "title": "Guides",
        "full_title": "Practical Guides for the Christian Life \u00b7 Gentle King",
        "eyebrow": "Guides",
        "h1": "Plain Guides for the Christian Life",
        "deck": (
            "How to pray, read the Bible, repent, forgive, prepare for the Lord\u2019s Supper, and examine "
            "yourself. How to test a teacher, a doctrine, and a church. And what the Bible says "
            "about marriage, sex, children, work, money, drink, government, death, and the hard questions."
        ),
        "description": (
            "What the Bible says about marriage, sex, abortion, IVF, money, alcohol, gambling, tattoos, government, and death, and practical guides for prayer and church."
        ),
        "schema": "CollectionPage",
        "about": ["Christian living", "Discernment", "The church", "Christian ethics"],
        "toc": False,
    },
    {
        "file": "resources.html",
        "content": "resources.html",
        "title": "Resources",
        "full_title": "Free Puritan and Reformed Library, Read Online or Download \u00b7 Gentle King",
        "eyebrow": "Reading and Study",
        "h1": "A Free Puritan and Reformed Library",
        "deck": (
            "The Puritan and Reformed classics worth reading today, free to read here or to "
            "take with you. After them come the newer books, the tools, and the preachers worth "
            "knowing, and where to begin."
        ),
        "description": (
            "Read Puritan and Reformed classics by Owen, Bunyan, and Calvin free in "
            "your browser, or download them. Plus where to begin, free tools, and good preaching."
        ),
        "schema": "CollectionPage",
        "about": [
            "Puritan books", "Reformed books", "Public domain Christian books", "Reformation Bibles",
            "Westminster Standards", "Bible commentaries", "Reformed preaching",
        ],
        "toc": True,
        "scripts": ["assets/js/library.js"],
        # Hidden for now. The page is still built and can be opened by its
        # address, but no menu, footer, or other page links to it, and search
        # engines are asked to leave it out. To bring it back, delete this
        # line, put it back in NAV and the footer, and restore the links in
        # content/ (see the git history of the commit that hid it).
        "hidden": True,
    },
    {
        "file": "about.html",
        "content": "about.html",
        "title": "About",
        "full_title": "About Gentle King \u00b7 Who Writes It and What It Believes",
        "eyebrow": "About",
        "h1": "About Gentle King",
        "deck": (
            "Who writes Gentle King, what the site teaches, and how to get in touch."
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
# The pages under Comfort and Apologetics, one for each sorrow and each question.
# Each was once a part of its parent page. They are listed here in the order
# they stand on the parent, and child_pages() puts each group after its parent.
# A series reads in order, so its pages carry Previous and Next at the foot.
# --------------------------------------------------------------------------

def _child(file, title, full_title, eyebrow, h1, deck, description, about, **more):
    page = {
        "file": file, "content": file, "title": title, "full_title": full_title,
        "eyebrow": eyebrow, "h1": h1, "deck": deck, "description": description,
        "schema": "Article", "about": about, "toc": True,
    }
    page.update(more)
    return page


COMFORT_PAGES = [
    _child(
        'comfort-grief.html',
        'When Someone You Love Has Died',
        'When Someone You Love Has Died · Bible Verses for Grief (KJV) · Gentle King',
        'Grief',
        'When Someone You Love Has Died',
        ("Help with the first days after a death, the weeks after the funeral, and grief that returns. Scripture explains the hope of resurrection in Christ."),
        ("Help after someone dies. Practical support, grief that returns, and KJV Scripture on mourning and the resurrection of believers."),
        ['Grief'],
        parent="comfort.html", close="comfort-close",
    ),
    _child(
        'comfort-widowed.html',
        'When Your Husband or Wife Has Died',
        'When Your Husband or Wife Has Died · Scripture for the Widowed · Gentle King',
        'Widowhood',
        'When Your Husband or Wife Has Died',
        ("Help after the death of a husband or wife, including daily tasks, children, and urgent paperwork. Scripture gives believers hope in Christ beyond death."),
        ("Help for widows and widowers with grief, children, daily tasks, bills, and the Christian hope of resurrection."),
        ['The death of a husband or wife'],
        parent="comfort.html", close="comfort-close",
    ),
    _child(
        'comfort-death-of-a-child.html',
        'When Your Child Has Died',
        'When Your Child Has Died · Comfort for Grieving Parents · Gentle King',
        'A child',
        'When Your Child Has Died',
        ("For parents grieving a miscarriage, stillbirth, or the death of a child. Find practical care and biblical teaching without guesses about your child's election."),
        ("Care after miscarriage, stillbirth, or a child's death. Grief, self-blame, practical support, and what Scripture teaches about children and salvation."),
        ['The death of a child', 'Miscarriage'],
        parent="comfort.html", close="comfort-close", cites=[{"@type": "CreativeWork", "name": "Canons of Dort"}],
    ),
    _child(
        'comfort-did-they-know-christ.html',
        "When You Fear They Didn't Know Christ",
        "When You Fear They Didn't Know Christ · Gentle King",
        'The hardest question',
        "When You Fear They Didn't Know Christ",
        ("You can grieve without pretending to know your loved one's final state. Read what Scripture reveals about salvation, judgment, and the things God keeps hidden."),
        ("Grieving someone whose faith was uncertain? Scripture on judgment, last-hour mercy, regret, and the limits of what we can know."),
        ['Grief for an unbeliever'],
        parent="comfort.html", close="comfort-close",
    ),
    _child(
        'comfort-suicide-loss.html',
        'When Someone You Love Took Their Own Life',
        'When Someone You Love Took Their Own Life · Gentle King',
        'Loss by suicide',
        'When Someone You Love Took Their Own Life',
        ("For those grieving a death by suicide. Find support for the first days, questions about guilt, and what Scripture says about Christ keeping his people."),
        ("Support after a death by suicide. Scripture on grief and perseverance, help with painful questions, and routes to urgent care."),
        ['Suicide loss'],
        parent="comfort.html", close="comfort-close",
    ),
    _child(
        'comfort-caregiving.html',
        'When You Are Caring for Someone',
        'When You Are Caring for Someone · Caregiving and Exhaustion · Gentle King',
        'Caregiving',
        'When You Are Caring for Someone',
        ("Practical help when caring for an ill or aging family member. Organize daily care, find respite, and ask others to share the burden."),
        ("Caregiving help for family illness, disability, dementia, exhaustion and respite, with practical church support."),
        ['Caregiving', 'Respite care', 'Caring for an aging parent'],
        parent="comfort.html",
    ),
    _child(
        'comfort-illness.html',
        'When Serious Illness Comes',
        'When Serious Illness Comes · Scripture for the Sick and Dying · Gentle King',
        'Sickness',
        'When Serious Illness Comes',
        ("Bring your questions to your care team and ask for help with daily needs. Scripture and counsel for a new diagnosis, long illness, caregiving, and dying."),
        ("Help with serious illness, caregiving, and end-of-life questions. Medical care, practical support, prayer, and biblical hope without promises of healing now."),
        ['Serious illness', 'Caregiving', 'The end of life'],
        parent="comfort.html", close="comfort-close",
    ),
    _child(
        'comfort-marriage.html',
        'When Your Marriage Is Breaking',
        'When Your Marriage Is Breaking · Betrayal, Divorce, and Hope · Gentle King',
        'A broken marriage',
        'When Your Marriage Is Breaking',
        ("Practical help if your marriage is breaking. Understand betrayal, separation, reconciliation and safety before making major decisions."),
        ("Help for a breaking marriage with betrayal, counseling, separation, children, practical decisions and Westminster teaching on divorce."),
        ['A breaking marriage and divorce'],
        parent="comfort.html", close="comfort-close",
    ),
    _child(
        'comfort-church-hurt.html',
        'When Your Church Has Hurt You',
        'When Your Church Has Hurt You · Abuse and Betrayal · Gentle King',
        'Church hurt',
        'When Your Church Has Hurt You',
        ("If you have been mistreated or betrayed by church leaders, find practical help with safety, reporting, accountability, and faithful pastoral care."),
        ("Help after church wrongdoing, abuse or betrayal. Safety, outside counsel, reporting, appeals and finding a faithful congregation."),
        ['Church hurt', 'Spiritual abuse', 'Church accountability'],
        parent="comfort.html",
    ),
    _child(
        'comfort-prodigal.html',
        'When Your Child Walks Away From the Lord',
        'When Your Child Walks Away From the Lord · Gentle King',
        'A wandering child',
        'When Your Child Walks Away From the Lord',
        ("Love your child without approving destructive behavior. Find help with conversation, boundaries, and prayer without claiming God has promised every child will return."),
        ("Help when a child rejects the faith. Honest conversation, household safety, boundaries, repentance, and prayer for God's grace."),
        ['A child who turns from the Lord'],
        parent="comfort.html", close="comfort-close",
    ),
    _child(
        'comfort-work-and-home.html',
        'When You Lose Your Job or Home',
        'When You Lose Your Job or Home · Scripture for Hard Times · Gentle King',
        'Job or home loss',
        'When You Lose Your Job or Home',
        ("Food, necessary medicine, and somewhere safe to sleep come first. Ask for practical help, keep track of deadlines, and read what Scripture teaches about need."),
        ("Lost work or housing? Help with immediate needs, assistance, deadlines, and seeking work, with Scripture on provision and the church's care."),
        ['Loss of work or home'],
        parent="comfort.html", close="comfort-close",
    ),
    _child(
        'comfort-loneliness.html',
        "When You're Lonely",
        "When You're Lonely · Scripture for the Lonely Christian · Gentle King",
        'Loneliness',
        "When You're Lonely",
        ("Ask for a definite visit, call, or shared meal. Find counsel for isolation, being overlooked at church, and receiving care when you can't get out."),
        ("Help for loneliness, isolation, and being overlooked at church. Ways to ask for company and care, with Scripture for single and married readers."),
        ['Loneliness'],
        parent="comfort.html", close="comfort-close",
    ),
    _child(
        'comfort-anxiety.html',
        'When Anxiety or Panic Takes Over',
        'When Anxiety or Panic Takes Over · Gentle King',
        'Anxiety and panic',
        'When Anxiety or Panic Takes Over',
        ("When worry or panic interrupts daily life, learn what help to seek and how to deal with frightening symptoms without treating them as unbelief."),
        ("Practical help with anxiety and panic, medical assessment, treatment, daily responsibilities and Christian hope."),
        ['Anxiety', 'Panic attacks'],
        parent="comfort.html",
    ),
    _child(
        'comfort-depression.html',
        "When You're Depressed",
        "When You're Depressed · Depression and the Christian · Gentle King",
        'Depression',
        "When You're Depressed",
        ("Tell a health professional about symptoms affecting your daily life. Find help seeking care and biblical counsel that doesn't treat depression as proof of unbelief."),
        ("Depression and Christian faith. Seeking professional care, asking for support, continuing treatment, and reading Scripture without self-diagnosis."),
        ['Depression'],
        parent="comfort.html", close="comfort-close",
    ),
    _child(
        'comfort-suicidal-thoughts.html',
        "When You're Thinking of Ending Your Life",
        "I'm Thinking of Ending My Life · Help and Christian Comfort · Gentle King",
        'Suicide crisis',
        "I'm Thinking of Ending My Life",
        ("If you're thinking of suicide, find immediate safety support, words to ask someone for help, and patient Christian counsel that takes your suffering seriously."),
        ("Help when you're thinking of suicide. Immediate safety, 988 and emergency care, asking someone to stay, and Christian hope."),
        ['Suicidal thoughts', 'Safety planning', 'Crisis support'],
        parent="comfort.html",
    ),
    _child(
        'comfort-safety.html',
        "If You're Not Safe",
        "If You're Not Safe · Abuse, Danger, and Thoughts of Suicide · Gentle King",
        'Safety',
        "If You're Not Safe",
        ("Use the urgent contacts first. Find help for thoughts of suicide, violence at home, and child abuse, with guidance on safety, reporting, and pastoral care."),
        ("Urgent help in the United States for danger, suicidal thoughts, domestic violence, and child abuse. Safety, reporting, and church care."),
        ['Safety from violence at home', 'Suicide prevention'],
        parent="comfort.html", close="comfort-close",
    ),
]

OBJECTOR_PAGES = [
    _child(
        'apologetics-god.html',
        'Is God Real?',
        'Is God Real? Answering the Objections to God · Gentle King',
        'God',
        'Is God Real?',
        ('Every argument against God is made with tools that only work if he is there.'),
        ('Is there no evidence for God? Who made God? Has science replaced him? Every argument'
         ' against God is made with tools that only work if he is there.'),
        ['The existence of God'],
        parent="apologetics.html", series="objector", close="apologetics-close",
    ),
    _child(
        'apologetics-bible.html',
        'Can the Bible Be Trusted?',
        'Can the Bible Be Trusted? Answers to Common Objections · Gentle King',
        'Scripture',
        'Can the Bible Be Trusted?',
        ("The Bible claims that when it speaks, God speaks. It doesn't wait on your verdict "
         'to be true, and it has nothing to fear from your questions.'),
        ('Men wrote it, men chose the books, it contradicts itself, it was changed. Plain '
         'answers on the authority of the Bible, its canon, and its manuscripts.'),
        ['The reliability of the Bible'],
        parent="apologetics.html", series="objector", close="apologetics-close",
    ),
    _child(
        'apologetics-resurrection.html',
        'Did Jesus Rise From the Dead?',
        'Did Jesus Rise From the Dead? The Evidence and the Objections · Gentle King',
        'The resurrection',
        'Did Jesus Rise From the Dead?',
        ("The faith rests on an event at a real time and place. If Jesus didn't rise, set it "
         "all aside. If he did, you'll have to deal with him."),
        ('Did Jesus live? Is the resurrection a legend? Did the disciples lie, or were they '
         'fooled? The faith rests on an event at a real time and place.'),
        ['The resurrection of Jesus'],
        parent="apologetics.html", series="objector", close="apologetics-close",
    ),
    _child(
        'apologetics-evil.html',
        'Why Does God Allow Evil?',
        'Why Does God Allow Evil and Suffering? · Gentle King',
        'The problem of evil',
        'Why Does God Allow Evil?',
        ('Many who ask this are carrying a grief of their own, and they should be answered '
         'with care.'),
        ('The problem of evil, whether God is to blame, the conquest of Canaan, and slavery in'
         ' the Bible, answered with care for those who carry a grief of their own.'),
        ['The problem of evil'],
        parent="apologetics.html", series="objector", close="apologetics-close",
    ),
    _child(
        'apologetics-morality.html',
        'Can You Be Good Without God?',
        'Can You Be Good Without God? Who Decides What Is Good · Gentle King',
        'The moral law',
        'Can You Be Good Without God?',
        ('Nearly everyone is sure that some things are really wrong. Very few ask what makes '
         'them so.'),
        ('Is morality only evolution or culture? Nearly everyone is sure that some things are '
         'really wrong. Very few ask what makes them so.'),
        ['The moral law'],
        parent="apologetics.html", series="objector", close="apologetics-close",
    ),
    _child(
        'apologetics-hell.html',
        'Is Hell Fair?',
        'Is Hell Fair? Why a Loving God Judges Sin · Gentle King',
        'Judgment',
        'Is Hell Fair?',
        ("Hell is real, and it's felt without end. It should never be spoken of lightly, and "
         'never left out.'),
        ('Would a loving God send anyone to hell? Is forever too long for a short life of sin?'
         ' Hell is real, and it should never be spoken of lightly or left out.'),
        ['Hell'],
        parent="apologetics.html", series="objector", close="apologetics-close",
    ),
    _child(
        'apologetics-only-jesus.html',
        'Is Jesus the Only Way?',
        'Why Is Jesus the Only Way to God? · Gentle King',
        'Other religions',
        'Is Jesus the Only Way?',
        ('Few things Christians say offend more in our day than that Jesus is the only way to '
         'God.'),
        ('Do all religions lead to God? What about those who never heard? Is it arrogant to '
         "say you're right? Why Christians say Jesus is the only way."),
        ['The exclusivity of Christ'],
        parent="apologetics.html", series="objector", close="apologetics-close",
    ),
    _child(
        'apologetics-christians.html',
        'What About the Hypocrites?',
        'What About the Hypocrites in the Church? · Gentle King',
        'The church',
        'What About the Hypocrites?',
        ('Some of the strongest arguments against Christ come from people who carry his name, '
         'and they deserve an honest answer.'),
        ('The church is full of hypocrites, and religion has done great harm. Some of the '
         'strongest arguments against Christ come from people who carry his name.'),
        ['Hypocrisy', 'Religion and harm'],
        parent="apologetics.html", series="objector", close="apologetics-close",
    ),
    _child(
        'apologetics-election.html',
        'Is It Fair That God Chooses?',
        'Is Election Fair? If God Chooses, How Can He Blame Me · Gentle King',
        'Election',
        'Is It Fair That God Chooses?',
        ('The Bible teaches that God chooses whom he will save. Some hear that as a way off '
         'the hook.'),
        ('The Bible teaches that God chooses whom he will save. Is that fair, and is there any'
         ' point in trying? Paul raised the objection himself.'),
        ['Election'],
        parent="apologetics.html", series="objector", close="apologetics-close",
    ),
    _child(
        'apologetics-the-real-objection.html',
        'Am I a Good Person?',
        'Am I a Good Person? The Real Reason People Reject Christ · Gentle King',
        'The real issue',
        'Am I a Good Person?',
        ('Every objection on these pages has had an answer. Jesus said the reason men stay away '
         'from him lies somewhere else.'),
        ('Every objection has an answer. Jesus said the reason men stay away from him lies '
         'somewhere else. The law, the human heart, and the hope for sinners.'),
        ['Sin', 'Repentance and faith'],
        parent="apologetics.html", series="objector",
    ),
]

BELIEVER_PAGES = [
    _child(
        'assurance-am-i-his.html',
        'Am I Really Saved?',
        'Am I Really Saved? Assurance of Salvation · Gentle King',
        'Assurance',
        'Am I Really Saved?',
        ("Come to Christ while your doubts remain. Scripture and the Westminster Standards explain assurance, weak faith, self-examination, and the fear of not being chosen."),
        ("Not sure you are saved? Scripture and the Westminster Confession on assurance, weak faith, election, and receiving help without repeated self-checking."),
        ['Assurance of salvation'],
        parent="apologetics.html", series="believer", close="assurance-close",
    ),
    _child(
        'assurance-remaining-sin.html',
        'When the Same Sin Keeps Coming Back',
        'When the Same Sin Keeps Coming Back · Assurance for the Struggling Christian · Gentle King',
        'Remaining sin',
        'When the Same Sin Keeps Coming Back',
        ("Remaining sin calls for repentance and help. It does not overturn the justification of those who trust Christ. Read how Scripture holds warning and pardon together."),
        ("Recurring sin, repentance, and forgiveness. Biblical warnings against excusing sin alongside Christ's promise of pardon to those who turn to him."),
        ['Remaining sin', 'Forgiveness'],
        parent="apologetics.html", series="believer", close="assurance-close",
    ),
    _child(
        'assurance-night-fears.html',
        'The Unpardonable Sin and Falling Away',
        'The Unpardonable Sin, Hebrews 6, and Losing Your Salvation · Gentle King',
        'Fears',
        'The Unpardonable Sin and Falling Away',
        ("Read the warnings about blasphemy and apostasy in their context. Christ calls you to come to him rather than settle every fear by checking your feelings."),
        ("The unpardonable sin, Hebrews 6 and 10, and fear of losing salvation. Read warnings in context without using repeated prayer as a test."),
        ['The unpardonable sin', 'Perseverance of the saints'],
        parent="apologetics.html", series="believer", close="assurance-close",
    ),
    _child(
        'assurance-god-feels-far.html',
        'When God Feels Far',
        'When God Feels Far Away · Spiritual Darkness · Gentle King',
        'Spiritual dryness',
        'When God Feels Far',
        ("A loss of comfort does not by itself prove that God has forsaken you. Seek pastoral care, attend to health needs, and read what Scripture says to troubled believers."),
        ("When God feels far away. Scripture on assurance, known sin, prayer, and receiving pastoral and medical care during spiritual distress."),
        ['Spiritual darkness'],
        parent="apologetics.html", series="believer", close="assurance-close",
    ),
    _child(
        'assurance-doubts-and-thoughts.html',
        'Doubts and Unwanted Thoughts',
        'Doubts and Unwanted Thoughts · For the Doubting Christian · Gentle King',
        'Doubt',
        'Doubts and Unwanted Thoughts',
        ("Doubting an argument and experiencing an unwanted thought call for different kinds of help. Find biblical counsel and guidance on seeking a clinical assessment."),
        ("Questions about Christianity and distressing unwanted thoughts. Biblical counsel, the difference between temptation and consent, and professional assessment."),
        ['Doubt', 'Intrusive thoughts'],
        parent="apologetics.html", series="believer", close="assurance-close",
    ),
    _child(
        'assurance-affliction.html',
        'Is God Punishing Me?',
        'Is God Against Me? Is He Punishing Me? · Gentle King',
        'Affliction',
        'Is God Punishing Me?',
        ("Illness, loss, or a breaking marriage does not reveal a secret verdict against you. Read about fatherly discipline and the freedom from condemnation believers have in Christ."),
        ("Does suffering mean God is punishing you? Romans 8, Hebrews 12, and the difference between fatherly discipline and condemnation."),
        ['Affliction', 'Chastening'],
        parent="apologetics.html", series="believer", close="assurance-close",
    ),
    _child(
        'assurance-death.html',
        'Afraid of Dying',
        'Afraid of Dying? Comfort for the Christian Facing Death · Gentle King',
        'Facing death',
        'Afraid of Dying',
        ("Tell your care team and someone you trust what frightens you. Scripture explains Christ's victory over death and the resurrection believers await."),
        ("Fear of death, practical preparation, and the Christian hope. Care-team questions, local advice about documents, and Scripture on resurrection."),
        ['The fear of death'],
        parent="apologetics.html", series="believer", close="assurance-close",
    ),
    _child(
        'assurance-kept.html',
        'Will God Keep Me to the End?',
        'Will God Keep Me to the End? Perseverance and Assurance · Gentle King',
        'Perseverance',
        'Will God Keep Me to the End?',
        ("Christ keeps his people through faith, repentance, and the means he gives. His promise sustains obedience while believers seek assurance."),
        ("How Christ keeps believers to the end. Perseverance, assurance, the Lord's Table, prayer, and access to church care during illness or disability."),
        ['Perseverance of the saints'],
        parent="apologetics.html", series="believer",
    ),
]

SOJOURNER_PAGES = [
    {
        "file": "sojourner-features.html",
        "content": "sojourner-features.html",
        "title": "Everything Sojourner Does",
        "full_title": "Sojourner Features · Color Text, Interlinear, Sermons, Atlas · Gentle King",
        "eyebrow": "Sojourner",
        "h1": "Everything Sojourner Does",
        "deck": (
            "The whole account, with pictures. Start with the panes, since the rest of the "
            "program hangs on them, or go straight to the part you came for."
        ),
        "description": (
            "Everything Sojourner does, with pictures. Linked panes, Color text, the Hebrew and "
            "Greek, the atlas and timeline, search, sermons, and family worship."
        ),
        "about": ["Bible study software", "Interlinear Bible", "Sermon preparation", "Family worship"],
        "parent": APP_PAGE,
        "close": "sojourner-get",
        "toc": True,
    },
    {
        "file": APP_WEB_PAGE,
        "content": APP_WEB_PAGE,
        "title": "Sojourner on Your Phone",
        "full_title": "Sojourner on Your Phone, Tablet, or Mac · Free Bible App in the Browser · Gentle King",
        "eyebrow": "Sojourner",
        "h1": "Sojourner on Your Phone",
        "deck": (
            "The same Bible study companion, in your browser. Open it on an iPhone, an Android, an "
            "iPad, or a Mac, put it on your home screen, and take it offline if you like."
        ),
        "description": (
            "A free Bible study app for iPhone, Android, iPad, and Mac, in the browser. The "
            "commentaries, confessions, Greek and Hebrew, with no account and no store."
        ),
        "about": ["Bible app for iPhone", "Bible app for Android", "Progressive web app"],
        "parent": APP_PAGE,
        "toc": True,
    },
    {
        "file": "sojourner-library.html",
        "content": "sojourner-library.html",
        "title": "What Comes With Sojourner",
        "full_title": "What Comes With Sojourner · Bibles, Commentaries, Confessions · Gentle King",
        "eyebrow": "Sojourner",
        "h1": "What Comes With Sojourner",
        "deck": (
            "The translations, the original texts, the lexicons, the commentaries and "
            "confessions, the four optional book shelves, and where every one of them came from."
        ),
        "description": (
            "The Bibles, Hebrew and Greek texts, lexicons, commentaries, Westminster Standards, "
            "and optional book shelves for Sojourner, with the source of each text."
        ),
        "about": ["Bible translations", "Bible commentaries", "Westminster Standards", "Public domain Christian books"],
        "parent": APP_PAGE,
        "close": "sojourner-get",
        "toc": True,
    },
    {
        "file": "sojourner-install.html",
        "content": "sojourner-install.html",
        "title": "Installing and Updating Sojourner",
        "full_title": "Installing and Updating Sojourner · Gentle King",
        "eyebrow": "Sojourner",
        "h1": "Installing and Updating",
        "deck": (
            "What to expect when you install it, how to update without losing anything, and how "
            "to add the book shelves and the map packs."
        ),
        "description": (
            "Installing Sojourner on Windows or Linux, the Windows warning, updating without "
            "losing your notes, and adding the book shelves and map packs."
        ),
        "about": ["Installing Sojourner"],
        "parent": APP_PAGE,
        "toc": True,
    },
]

GUIDE_PAGES = [
    _child('guide-prayer.html', 'How to Pray', 'How to Pray in a Way That Pleases God · Gentle King', 'Guide', 'How to Pray',
           "Bring your needs to God through Christ. Use the Lord\u2019s Prayer as a pattern, confess sin, give thanks, and begin with words you understand.",
           "How to pray through Christ, use the Lord\u2019s Prayer, confess sin, give thanks, and form a habit that accounts for illness and daily responsibilities.",
           ['How to Pray'], parent="guides.html", series='life'),
    _child('guide-bible-reading.html', 'How to Read the Bible', 'How to Read the Bible for Yourself · Gentle King', 'Guide', 'How to Read the Bible',
           'How to read Scripture with understanding, where to start, and which helps are worth having.',
           'How to read the Bible for yourself with prayer and understanding, where a new reader should start, a plan for the whole Bible, and helps worth having.',
           ['How to Read the Bible'], parent="guides.html", series='life'),
    _child('guide-meditation.html', 'How to Meditate on and Memorize Scripture', 'How to Meditate on Scripture and Memorize It · Gentle King', 'Guide', 'How to Meditate on and Memorize Scripture',
           'What biblical meditation is, a simple way to think a verse through, and how a busy believer can hide God’s Word in his heart.',
           'How to meditate on Scripture with understanding, prayer, and obedience, with a worked example and a plan to memorize in small moments.',
           ['How to Meditate on and Memorize Scripture'], parent="guides.html", series='life'),
    _child('guide-examine-yourself.html', 'How to Examine Yourself', 'How to Examine Yourself Biblically · Gentle King', 'Guide', 'How to Examine Yourself',
           'Questions from Scripture and the Larger Catechism to ask yourself, how to do it each day, and how not to drown in it.',
           'How to examine yourself as Scripture commands, with questions from the Larger Catechism, a short daily habit, and a caution for the anxious.',
           ['How to Examine Yourself'], parent="guides.html", series='life'),
    _child('guide-repentance.html', 'How to Repent', 'How to Repent · What True Repentance Is · Gentle King', 'Guide', 'How to Repent',
           'What repentance unto life is, godly and worldly sorrow, confessing sins by name, making things right, and coming home again.',
           'How to repent of sin, by the Shorter Catechism. Godly sorrow, confessing sins by name, restitution, and the Father who runs to meet the prodigal.',
           ['How to Repent'], parent="guides.html", series='life'),
    _child('guide-ten-commandments.html', 'The Ten Commandments for a Believer', 'The Ten Commandments for a Believer · What Each One Requires · Gentle King', 'Guide', 'The Ten Commandments for a Believer',
           'Why a forgiven Christian still keeps God’s law, how to read it, what each commandment requires and forbids, and how to use them this week.',
           'Why a Christian keeps the Ten Commandments, how to read them, what each one requires and forbids by the Shorter Catechism, and how to use them.',
           ['The Ten Commandments for a Believer'], parent="guides.html", series='life'),
    _child('guide-worship.html', 'How God Wants to Be Worshiped', 'The Regulative Principle of Worship \u00b7 How God Is to Be Worshiped \u00b7 Gentle King', 'Guide', 'How God Wants to Be Worshiped',
           "Join the congregation in hearing Scripture, prayer, and psalm singing. Understand the biblical warrant for worship and ask about the service when you visit.",
           "Reformed Presbyterian public worship, the regulative principle, elements and circumstances, psalm singing, and practical guidance for visitors.",
           ['The regulative principle of worship'], parent="guides.html", series='life'),
    _child('guide-hearing-sermons.html', 'How to Hear a Sermon', 'How to Hear a Sermon and Profit From It · Gentle King', 'Guide', 'How to Hear a Sermon',
           "Follow the passage, test the teaching by Scripture, and return to its truth during the week. Ask for help when language, hearing, or attention makes listening hard.",
           "How to prepare for a sermon, follow Scripture, test teaching, seek accessibility help, discuss concerns, and put biblical truth into practice.",
           ['How to Hear a Sermon'], parent="guides.html", series='life'),
    _child('guide-lords-supper.html', 'How to Prepare for the Lord’s Supper', 'How to Prepare for the Lord’s Supper · Gentle King', 'Guide', 'How to Prepare for the Lord’s Supper',
           "Speak with your elders about admission and questions. Prepare with faith, repentance, and prayer, then receive Christ by faith as the church celebrates his Supper.",
           "Preparing for communion, church admission, self-examination, doubts, accessibility needs, and receiving Christ spiritually by faith.",
           ['How to Prepare for the Lord’s Supper'], parent="guides.html", series='life'),
    _child('guide-lords-day.html', 'How to Keep the Lord’s Day', 'How to Keep the Lord’s Day, the Christian Sabbath · Gentle King', 'Guide', 'How to Keep the Lord’s Day',
           "Set Sunday apart for worship and rest. Prepare for gathering with the church, care for dependents, and distinguish ordinary work from necessity and mercy.",
           "Keeping the Christian Sabbath through worship, rest, preparation, and works of necessity and mercy, with help for caregiving, illness, and work conflicts.",
           ['How to Keep the Lord’s Day'], parent="guides.html", series='life'),
    _child('guide-fasting.html', 'How to Fast', 'How to Fast as a Christian · Gentle King', 'Guide', 'How to Fast',
           "Why Christians fast, how it joins prayer, what it's not, how to begin, and when not to fast from food.",
           "How to fast biblically. Fasting with prayer, what Isaiah 58 says it's not, how to begin with one meal, and health cautions.",
           ['How to Fast'], parent="guides.html", series='life'),
    _child('guide-family-worship.html', 'How to Lead Family Worship', 'How to Lead Family Worship · Gentle King', 'Guide', 'How to Lead Family Worship',
           "Gather at a workable time, read a short Bible passage, sing a psalm, and pray. Adapt the length and participation to the people in your home.",
           "How to begin family worship with a Bible, psalter, and prayer. Help for young children, changing schedules, disability, and households that differ in faith.",
           ['How to Lead Family Worship'], parent="guides.html", series='life'),
    _child('guide-forgiveness.html', 'How to Forgive and Seek Forgiveness', 'How to Forgive and Seek Forgiveness · Gentle King', 'Guide', 'How to Forgive and Seek Forgiveness',
           "Forgive as Christ commands, seek forgiveness for your own wrongs, and receive the repentant in love. Truthful reporting and protective boundaries still matter.",
           "Forgiveness, repentance, reconciliation, and receiving a repentant brother in love, with truthful reporting, restitution, and lawful protective boundaries.",
           ['How to Forgive and Seek Forgiveness'], parent="guides.html", series='life'),
    _child('guide-evangelism.html', 'How to Share the Gospel', 'How to Share the Gospel With Others · Gentle King', 'Guide', 'How to Share the Gospel',
           'Know the message, pray for people by name, tell the bad news and the good, call for repentance and faith, and bring them to church.',
           'How an ordinary Christian shares the gospel. Know the message, pray, ask questions, call for repentance and faith, and invite people to church.',
           ['How to Share the Gospel'], parent="guides.html", series='life'),
    _child('guide-reading-scripture.html', 'How to Read the Bible Rightly', 'How to Read the Bible Rightly · Literal and Figurative · Gentle King', 'Guide', 'How to Read the Bible Rightly',
           "All of it's true. What reading literally means, the kinds of writing in Scripture, how to tell a figure of speech, and Christ at the center.",
           'How to tell what in the Bible is literal and what is figurative. Kinds of biblical writing, Scripture interpreting Scripture, and Christ at the center.',
           ['How to Read the Bible Rightly'], parent="guides.html", series='discern'),
    _child('guide-prophecy.html', 'How to Read Prophecy and Revelation', 'How to Read Prophecy, Revelation, and the Millennium · Gentle King', 'Guide', 'How to Read Prophecy and Revelation',
           'What all Reformed believers hold about the end, how prophecy works, how to read Revelation, and the thousand years.',
           'How to read Bible prophecy and Revelation. Amillennialism and postmillennialism set out fairly, premillennialism, and why not to set dates.',
           ['How to Read Prophecy and Revelation'], parent="guides.html", series='discern'),
    _child('guide-false-teachers.html', 'How to Spot a False Teacher', 'How to Spot a False Teacher · Gentle King', 'Guide', 'How to Spot a False Teacher',
           'Seven questions to test any teacher by Scripture, the common warning signs today, and what to do when you find one.',
           'How to spot a false teacher. Seven questions to test any preacher by Scripture, common warning signs today, and what to do about it.',
           ['How to Spot a False Teacher'], parent="guides.html", series='discern'),
    _child('guide-heresy.html', 'How to Spot Real Heresy', 'How to Spot Real Heresy · Heresy, Error, and Disagreement · Gentle King', 'Guide', 'How to Spot Real Heresy',
           'The difference between heresy, serious error, and honest disagreement, the truths that mark the line, and how to respond.',
           'The difference between heresy, serious error, and disagreement among the faithful, the truths that mark the line, and how to respond.',
           ['How to Spot Real Heresy'], parent="guides.html", series='discern'),
    _child('guide-free-will.html', 'How to Answer Arminianism and Pelagianism', 'How to Answer Arminianism and Pelagianism · Free Will and Grace · Gentle King', 'Guide', 'How to Answer Arminianism and Pelagianism',
           'Who makes the difference when a sinner is saved? Both views set out fairly, answered from Scripture, and how to talk with a brother who disagrees.',
           'A Reformed answer to Arminianism and Pelagianism. Free will, election, the atonement, and grace from Scripture, and how to talk with an Arminian friend.',
           ['Arminianism', 'Pelagianism', 'Free will', 'The doctrines of grace'], parent="guides.html", series='discern'),
    _child('guide-new-revelation.html', 'How to Weigh “God Told Me”', 'How to Weigh “God Told Me” · Prophecy, Tongues, and Guidance · Gentle King', 'Guide', 'How to Weigh “God Told Me”',
           'God has spoken in his Son. How God guides you now, how to test a claimed word, and how to answer a friend kindly.',
           'Does God still speak today? The sufficiency of Scripture, prophecy and tongues, how God guides believers, and how to test a claimed word.',
           ['How to Weigh “God Told Me”'], parent="guides.html", series='discern'),
    _child('guide-media.html', 'How to Test Books, Music, and Preachers Online', 'How to Test Books, Music, and Preachers Online · Gentle King', 'Guide', 'How to Test Books, Music, and Preachers Online',
           'Testing teaching online, your own elders, worship music, books and films, and your time and attention.',
           'Christian discernment for books, podcasts, music, films, and online preachers. Testing by Scripture, your own elders, and guarding your time.',
           ['How to Test Books, Music, and Preachers Online'], parent="guides.html", series='discern'),
    _child('guide-disagreeing.html', 'How to Disagree With Another Christian', 'How to Disagree With a Christian Brother · Gentle King', 'Guide', 'How to Disagree With Another Christian',
           'Three kinds of difference, Romans 14 in practice, how to disagree well, and when to let it go.',
           'How Christians should disagree. Matters of faith, serious error, and liberty, Romans 14, online arguments, and church disputes.',
           ['How to Disagree With Another Christian'], parent="guides.html", series='discern'),
    _child('guide-false-church.html', 'How to Tell a True Church From a False One', 'How to Tell a True Church From a False One · Gentle King', 'Guide', 'How to Tell a True Church From a False One',
           'The marks of a true church, what makes a church false and why, the warning signs, and what to do.',
           'The three marks of a true church, what makes a church false and why, warning signs to look for, and when you must leave.',
           ['How to Tell a True Church From a False One'], parent="guides.html", series='discern'),
    _child('guide-leaving-a-church.html', 'How to Leave a Church Well', 'How to Leave a Church Well · Gentle King', 'Guide', 'How to Leave a Church Well',
           "For an ordinary transfer, discuss your reasons and seek continuing care. If there is abuse or danger, protection comes first and does not require church permission.",
           "Leaving a church, transfers, disputed discipline, appeals, accessibility barriers, safe boundaries, and protection when leaders or members cause harm.",
           ['How to Leave a Church Well'], parent="guides.html", series='discern'),
    _child('guide-find-a-church.html', 'How to Find a Faithful Church', 'How to Find a Reformed Presbyterian (RPCNA) Church · Gentle King', 'Guide', 'How to Find a Faithful Church',
           "Find a congregation, confirm service times, and ask about visiting. Consider its teaching, worship, care, accessibility, and what to do when none is near.",
           "Finding a faithful church, using the RPCNA directory, visiting, asking about teaching and care, and addressing distance, disability, or transport barriers.",
           ['How to Find a Faithful Church'], parent="guides.html", series='discern'),
    _child('guide-marriage.html', 'What the Bible Says About Marriage', 'What the Bible Says About Marriage · Gentle King', 'What the Bible says', 'What the Bible Says About Marriage',
           "Husband and wife owe faithful love, mutual marital duty, and their distinct biblical responsibilities. Guidance on headship, submission, disagreement, singleness, and protection from abuse.",
           "Biblical marriage, lawful headship and submission, mutual sexual duty, shared responsibilities, divorce, singleness, and protection from abuse.",
           ['Marriage'], parent="guides.html", series='says'),
    _child('guide-sex.html', 'What the Bible Says About Sex', 'What the Bible Says About Sex and Purity · Gentle King', 'What the Bible says', 'What the Bible Says About Sex',
           "Sexual faithfulness, mutual marital duty and tenderness, and pardon for those who repent. If you have been assaulted or coerced, seek safety and medical care first.",
           "Scripture on sex, chastity, mutual marital duty, and forgiveness, with guidance on health, sexual assault, and receiving appropriate care.",
           ['Sexual purity', 'The seventh commandment'], parent="guides.html", series='says'),
    _child('guide-homosexuality.html', 'What the Bible Says About Homosexuality and Gender', 'What the Bible Says About Homosexuality and Transgender Identity · Gentle King', 'What the Bible says', 'What the Bible Says About Homosexuality and Gender',
           'God made us male and female. What Scripture says, plainly and kindly, to the curious, the struggling, and the families who love them.',
           'What the Bible says about homosexuality and transgender identity, help for Christians who struggle, and how to love a gay or trans family member.',
           ['Homosexuality', 'Gender'], parent="guides.html", series='says'),
    _child('guide-birth-control.html', 'What the Bible Says About Birth Control', 'What the Bible Says About Birth Control and Contraception · Gentle King', 'What the Bible says', 'What the Bible Says About Birth Control',
           'Children are a blessing. Where Scripture is plain, where faithful believers differ, and why no method may end a life.',
           'What the Bible says about birth control. Children as a blessing, where Reformed believers differ, Onan, motives, and methods that can end a life.',
           ['Birth control', 'Contraception'], parent="guides.html", series='says'),
    _child('guide-ivf.html', 'What the Bible Says About IVF and Infertility', 'What the Bible Says About IVF and Infertility · Gentle King', 'What the Bible says', 'What the Bible Says About IVF and Infertility',
           'The grief of an empty cradle, what is wrong in IVF as commonly done, frozen embryos, and the hope of the childless in Christ.',
           'What the Bible says about infertility and IVF. Comfort for the childless, the moral problems in IVF, frozen embryos, donors, and adoption.',
           ['Infertility', 'In vitro fertilization'], parent="guides.html", series='says'),
    _child('guide-parenting.html', 'What the Bible Says About Raising Children', 'What the Bible Says About Raising Children · Gentle King', 'What the Bible says', 'What the Bible Says About Raising Children',
           "Teach the faith, require lawful obedience, and correct wrongdoing with patient care. Apply parental duties with attention to each child\u2019s age and ability.",
           "Christian parenting, lawful obedience, correction, covenant children, baptism, family worship, and guidance suited to age, ability, and household needs.",
           ['Parenting', 'Christian family'], parent="guides.html", series='says'),
    _child('guide-spanking.html', 'What the Bible Says About Spanking and Discipline', 'What the Bible Says About Spanking and Discipline · Gentle King', 'What the Bible says', 'What the Bible Says About Spanking and Discipline',
           "Parents must teach and correct children. Read the rod passages in context, apply fitting correction without cruelty, and seek help when a child has been harmed.",
           "The rod in Proverbs, parents\u2019 duty to correct, children\u2019s lawful obedience, nonviolent practical guidance, child protection, and care after harm.",
           ['Discipline of children', 'Corporal punishment'], parent="guides.html", series='says'),
    _child('guide-abortion.html', 'What the Bible Says About Abortion', 'What the Bible Says About Abortion and the Unborn · Gentle King', 'What the Bible says', 'What the Bible Says About Abortion',
           'The unborn child bears the image of God. What Scripture says, the hard cases, help for a mother who is afraid, and mercy for the guilty.',
           "What the Bible says about abortion and the unborn child, answers to common objections, help if you're pregnant and afraid, and forgiveness in Christ.",
           ['Abortion', 'The sanctity of human life'], parent="guides.html", series='says'),
    _child('guide-work.html', 'What the Bible Says About Work', 'What the Bible Says About Work · Gentle King', 'What the Bible says', 'What the Bible Says About Work',
           "Work honestly in a lawful calling, seek help with unjust treatment, and plan for rest and household care. Illness or disability is not unwillingness to work.",
           "Christian guidance on work, wages, unfair treatment, rest, household provision, and inability to work through illness or disability.",
           ['Work and vocation'], parent="guides.html", series='says'),
    _child('guide-money.html', 'What the Bible Says About Money and Debt', 'What the Bible Says About Money and Debt · Gentle King', 'What the Bible says', 'What the Bible Says About Money and Debt',
           'Protect basic needs, know what you owe, and ask for help before deadlines. Scripture on earning, giving, borrowing, saving, and responsibility toward others.',
           'Christian guidance on money, giving, debt, and essential needs. Payment plans, qualified advice, contentment, and support for the church and dependents.',
           ['Money', 'Debt', 'Christian giving'], parent="guides.html", series='says'),
    _child('guide-gambling.html', 'What the Bible Says About Gambling', 'What the Bible Says About Gambling · Gentle King', 'What the Bible says', 'What the Bible Says About Gambling',
           'No verse says thou shalt not gamble. What the commandments do say, about lotteries, betting apps, lots, and the way out.',
           'What the Bible says about gambling. Covetousness, lotteries and betting apps, casting lots, friendly bets, and help when gambling has hold of you.',
           ['Gambling'], parent="guides.html", series='says'),
    _child('guide-alcohol.html', 'What the Bible Says About Alcohol', 'What the Bible Says About Alcohol and Drinking · Gentle King', 'What the Bible says', 'What the Bible Says About Alcohol',
           'Wine is a gift and drunkenness is sin. Christian liberty, the weaker brother, when to abstain, drugs, and help when drink has hold.',
           'What the Bible says about alcohol. Wine as a gift, drunkenness as sin, freedom to drink or abstain, marijuana and drugs, and help for the addicted.',
           ['Alcohol', 'Christian liberty'], parent="guides.html", series='says'),
    _child('guide-tattoos.html', 'What the Bible Says About Tattoos', 'What the Bible Says About Tattoos and Piercings · Gentle King', 'What the Bible says', 'What the Bible Says About Tattoos',
           'What Leviticus 19:28 meant, how Old Testament laws bind now, Christian liberty, and a word for those who already have them.',
           'What the Bible says about tattoos. Leviticus 19:28 in its setting, moral and ceremonial law, Christian liberty, piercings, and parents.',
           ['Tattoos', 'Old Testament law'], parent="guides.html", series='says'),
    _child('guide-government.html', 'What the Bible Says About Government', 'What the Bible Says About Government and Christ the King · Gentle King', 'What the Bible says', 'What the Bible Says About Government',
           'Rulers are ordained of God and owe allegiance to his Son. Obeying, praying, paying taxes, and when to obey God rather than men.',
           'What the Bible says about government. Rulers as God’s ministers, the kingship of Christ over nations, taxes, and obeying God rather than men.',
           ['Civil government', 'The kingship of Christ'], parent="guides.html", series='says'),
    _child('guide-death.html', 'What the Bible Says About Death, Burial, and Cremation', 'What the Bible Says About Death, Burial, and Cremation · Gentle King', 'What the Bible says', 'What the Bible Says About Death, Burial, and Cremation',
           'Death is an enemy Christ has beaten. What happens when we die, the resurrection, burial and cremation, and the end of life.',
           'What the Bible says about death. What happens when we die, the resurrection of the body, burial and cremation, euthanasia, and preparing to die.',
           ['Death', 'Burial', 'Cremation'], parent="guides.html", series='says'),
]

# Where each part of the two old long pages went. A link from before the split,
# such as comfort.html#grief, is sent on by site.js to the page that holds it now.
MOVED = {
    'comfort': {
        'baby': 'comfort-death-of-a-child.html#baby',
        'caregiver': 'comfort-illness.html#caregiver',
        'child': 'comfort-death-of-a-child.html',
        'child-hurt': 'comfort-safety.html#child-hurt',
        'child-search': 'comfort-death-of-a-child.html#child-search',
        'darkness': 'comfort-depression.html',
        'darkness-search': 'comfort-depression.html#darkness-search',
        'divorce': 'comfort-marriage.html#divorce',
        'dying': 'comfort-illness.html#dying',
        'ending-your-life': 'comfort-safety.html#ending-your-life',
        'every-parent': 'comfort-death-of-a-child.html#every-parent',
        'grief': 'comfort-grief.html',
        'grief-search': 'comfort-grief.html#grief-search',
        'help': 'comfort-safety.html',
        'if-it-was-me': 'comfort-marriage.html#if-it-was-me',
        'illness': 'comfort-illness.html',
        'illness-search': 'comfort-illness.html#illness-search',
        'long-illness': 'comfort-illness.html#long-illness',
        'marriage': 'comfort-marriage.html',
        'marriage-search': 'comfort-marriage.html#marriage-search',
        'older-child': 'comfort-death-of-a-child.html#older-child',
        'parents': 'comfort-marriage.html#parents',
        'prodigal': 'comfort-prodigal.html',
        'prodigal-search': 'comfort-prodigal.html#prodigal-search',
        'someone-hurting-you': 'comfort-safety.html#someone-hurting-you',
        'suicide-loss': 'comfort-suicide-loss.html',
        'suicide-loss-search': 'comfort-suicide-loss.html#suicide-loss-search',
        'unsure': 'comfort-did-they-know-christ.html',
        'unsure-search': 'comfort-did-they-know-christ.html#unsure-search',
        'want': 'comfort-work-and-home.html',
        'want-search': 'comfort-work-and-home.html#want-search',
        'widowed': 'comfort-widowed.html',
        'widowed-heaven': 'comfort-widowed.html#widowed-heaven',
        'widowed-search': 'comfort-widowed.html#widowed-search',
    },
    'apologetics': {
        'am-i-his': 'assurance-am-i-his.html',
        'bible': 'apologetics-bible.html',
        'christians': 'apologetics-christians.html',
        'dark': 'assurance-god-feels-far.html',
        'death': 'assurance-death.html',
        'evil': 'apologetics-evil.html',
        'fairness': 'apologetics-election.html',
        'fears': 'assurance-night-fears.html',
        'god': 'apologetics-god.html',
        'hell': 'apologetics-hell.html',
        'jesus': 'apologetics-resurrection.html',
        'kept': 'assurance-kept.html',
        'mind': 'assurance-doubts-and-thoughts.html',
        'one-way': 'apologetics-only-jesus.html',
        'right-and-wrong': 'apologetics-morality.html',
        'sin-remains': 'assurance-remaining-sin.html',
        'suffering': 'assurance-affliction.html',
        'the-real-objection': 'apologetics-the-real-objection.html',
    },
}

SERIES = {
    "objector": OBJECTOR_PAGES, "believer": BELIEVER_PAGES,
    "life": [p for p in GUIDE_PAGES if p["series"] == "life"],
    "discern": [p for p in GUIDE_PAGES if p["series"] == "discern"],
    "says": [p for p in GUIDE_PAGES if p["series"] == "says"],
}
CHILDREN = {
    "comfort.html": COMFORT_PAGES,
    "apologetics.html": OBJECTOR_PAGES + BELIEVER_PAGES,
    APP_PAGE: SOJOURNER_PAGES,
    "guides.html": GUIDE_PAGES,
}

# Reader entrances and individual doctrine subjects.
PAGES.extend([{'file': 'start-here.html',
  'content': 'start-here.html',
  'title': 'Start Here',
  'full_title': 'Start Here · Gentle King',
  'eyebrow': 'Start Here',
  'h1': 'A Place to Begin',
  'deck': 'Read the gospel, begin a course, or find guidance for a particular need.',
  'description': 'New to Gentle King? Read the gospel, begin the Foundations course, or find help with Bible reading, prayer, and finding a church.',
  'schema': 'CollectionPage',
  'toc': False},
 {'file': 'help.html',
  'content': 'help.html',
  'title': 'Find Help',
  'full_title': 'Find Help · Gentle King',
  'eyebrow': 'Find Help',
  'h1': 'Help for Where You Are',
  'deck': 'Find urgent help, support with basic needs, or teaching for the trouble you face.',
  'description': 'Find help for danger, grief, basic needs, money, recurring sin, and fears about salvation. Choose the situation that brought you here.',
  'schema': 'CollectionPage',
  'toc': False},
 {'file': 'learn.html',
  'content': 'learn.html',
  'title': 'Learn the Faith',
  'full_title': 'Learn the Faith · Gentle King',
  'eyebrow': 'Learn the Faith',
  'h1': 'Learn the Christian Faith',
  'deck': 'Begin with an overview, or follow the question you have today.',
  'description': 'Begin with an overview, or follow the question you have today.',
  'schema': 'CollectionPage',
  'toc': False},
 {'file': 'assurance.html',
  'content': 'assurance.html',
  'title': 'Assurance and Doubt',
  'full_title': 'Assurance and Doubt · Gentle King',
  'eyebrow': 'Assurance and Doubt',
  'h1': 'Assurance and Doubt',
  'deck': "For those who trust Christ but fear they're not really his.",
  'description': "For those who trust Christ but fear they're not really his.",
  'schema': 'CollectionPage',
  'toc': False},
 {'file': 'search.html',
  'content': 'search.html',
  'title': 'Search',
  'full_title': 'Search · Gentle King',
  'eyebrow': 'Search',
  'h1': 'Search Gentle King',
  'deck': 'Search the teaching and guides by subject or words from your question.',
  'description': 'Search Gentle King articles and guides by subject. Find teaching on prayer, money, Scripture, assurance, and Christian life.',
  'schema': 'WebPage',
  'toc': False,
  'scripts': ['assets/js/search.js']},
 {'file': 'doctrine-why-doctrine.html',
  'content': 'doctrine-why-doctrine.html',
  'title': 'Why Doctrine Matters',
  'full_title': 'Why Doctrine Matters · Gentle King',
  'eyebrow': 'Doctrine',
  'h1': 'Why Doctrine Matters',
  'deck': 'Why sound teaching belongs to the Christian life.',
  'description': 'Why sound teaching belongs to the Christian life.',
  'schema': 'Article',
  'parent': 'doctrine.html',
  'toc': True},
 {'file': 'doctrine-scripture.html',
  'content': 'doctrine-scripture.html',
  'title': 'The Bible',
  'full_title': 'The Bible · Gentle King',
  'eyebrow': 'Doctrine',
  'h1': 'The Bible',
  'deck': "God\u2019s inspired and preserved Word, the sufficient and final rule of faith and life.",
  'description': "Scripture\u2019s inspiration, inerrancy, providential preservation, sufficiency, clarity, interpretation, and final authority under original WCF 1.",
  'schema': 'Article',
  'parent': 'doctrine.html',
  'toc': True},
 {'file': 'doctrine-god-and-trinity.html',
  'content': 'doctrine-god-and-trinity.html',
  'title': 'God and the Trinity',
  'full_title': 'God and the Trinity · Gentle King',
  'eyebrow': 'Doctrine',
  'h1': 'God and the Trinity',
  'deck': 'The one living God, Father, Son, and Holy Ghost.',
  'description': 'The one living God, Father, Son, and Holy Ghost.',
  'schema': 'Article',
  'parent': 'doctrine.html',
  'toc': True},
 {'file': 'doctrine-five-solas.html',
  'content': 'doctrine-five-solas.html',
  'title': 'The Five Solas',
  'full_title': 'The Five Solas · Gentle King',
  'eyebrow': 'Doctrine',
  'h1': 'The Five Solas',
  'deck': 'Salvation by grace alone through faith alone in Christ alone.',
  'description': 'Salvation by grace alone through faith alone in Christ alone.',
  'schema': 'Article',
  'parent': 'doctrine.html',
  'toc': True},
 {'file': 'doctrine-doctrines-of-grace.html',
  'content': 'doctrine-doctrines-of-grace.html',
  'title': 'The Doctrines of Grace',
  'full_title': 'The Doctrines of Grace · Gentle King',
  'eyebrow': 'Doctrine',
  'h1': 'The Doctrines of Grace',
  'deck': 'How God brings sinners to Christ and keeps them.',
  'description': 'How God brings sinners to Christ and keeps them.',
  'schema': 'Article',
  'parent': 'doctrine.html',
  'toc': True},
 {'file': 'doctrine-covenant.html',
  'content': 'doctrine-covenant.html',
  'title': 'Covenant Theology',
  'full_title': 'Covenant Theology · Gentle King',
  'eyebrow': 'Doctrine',
  'h1': 'Covenant Theology',
  'deck': 'One covenant of grace across the Old and New Testaments.',
  'description': 'One covenant of grace across the Old and New Testaments.',
  'schema': 'Article',
  'parent': 'doctrine.html',
  'toc': True},
 {'file': 'doctrine-law-and-gospel.html',
  'content': 'doctrine-law-and-gospel.html',
  'title': 'Law and Gospel',
  'full_title': 'Law and Gospel · Gentle King',
  'eyebrow': 'Doctrine',
  'h1': 'Law and Gospel',
  'deck': 'What God commands and what he gives in Christ.',
  'description': 'What God commands and what he gives in Christ.',
  'schema': 'Article',
  'parent': 'doctrine.html',
  'toc': True},
 {'file': 'doctrine-church-and-worship.html',
  'content': 'doctrine-church-and-worship.html',
  'title': 'The Church and Worship',
  'full_title': 'The Church and Worship · Gentle King',
  'eyebrow': 'Doctrine',
  'h1': 'The Church and Worship',
  'deck': 'The church, worship, and the ordinary means of grace.',
  'description': 'The church, worship, and the ordinary means of grace.',
  'schema': 'Article',
  'parent': 'doctrine.html',
  'toc': True},
 {'file': 'doctrine-last-things.html',
  'content': 'doctrine-last-things.html',
  'title': 'The End Times',
  'full_title': 'The End Times · Gentle King',
  'eyebrow': 'Doctrine',
  'h1': 'The End Times',
  'deck': 'Christ’s return, the resurrection, and the judgment.',
  'description': 'Christ’s return, the resurrection, and the judgment.',
  'schema': 'Article',
  'parent': 'doctrine.html',
  'toc': True},
 {'file': 'doctrine-standards.html',
  'content': 'doctrine-standards.html',
  'title': 'The Westminster Standards',
  'full_title': 'The Westminster Standards · Gentle King',
  'eyebrow': 'Doctrine',
  'h1': 'The Westminster Standards',
  'deck': 'Where to begin with the Westminster Standards.',
  'description': 'Where to begin with the Westminster Standards.',
  'schema': 'Article',
  'parent': 'doctrine.html',
  'toc': True}])
# Further doctrines taught from the original 1647 Westminster Standards.
PAGES.extend([
    {"file": "doctrine-providence.html", "content": "doctrine-providence.html",
     "title": "Providence", "full_title": "Providence · Gentle King",
     "eyebrow": "Doctrine", "h1": "Providence",
     "deck": "The Lord preserves and governs all he has made, including the hard things we can't explain.", "description": "The Lord preserves and governs all he has made, including the hard things we can't explain.",
     "schema": "Article", "parent": "doctrine.html", "toc": True},
    {"file": "doctrine-union-with-christ.html", "content": "doctrine-union-with-christ.html",
     "title": "Union With Christ", "full_title": "Union With Christ · Gentle King",
     "eyebrow": "Doctrine", "h1": "Union With Christ",
     "deck": "How believers are joined to Christ and receive every saving benefit in him.", "description": "How believers are joined to Christ and receive every saving benefit in him.",
     "schema": "Article", "parent": "doctrine.html", "toc": True},
    {"file": "doctrine-adoption.html", "content": "doctrine-adoption.html",
     "title": "Adoption", "full_title": "Adoption · Gentle King",
     "eyebrow": "Doctrine", "h1": "Adoption",
     "deck": "What it means to belong to the Father's family through Christ.", "description": "What it means to belong to the Father's family through Christ.",
     "schema": "Article", "parent": "doctrine.html", "toc": True},
    {"file": "doctrine-sanctification.html", "content": "doctrine-sanctification.html",
     "title": "Sanctification", "full_title": "Sanctification · Gentle King",
     "eyebrow": "Doctrine", "h1": "Sanctification",
     "deck": "Why sin remains in believers and how the Spirit renews their lives.", "description": "Why sin remains in believers and how the Spirit renews their lives.",
     "schema": "Article", "parent": "doctrine.html", "toc": True},
    {"file": "doctrine-church-government.html", "content": "doctrine-church-government.html",
     "title": "Church Government", "full_title": "Church Government · Gentle King",
     "eyebrow": "Doctrine", "h1": "Church Government",
     "deck": "The keys, elders, church courts, and discipline in the 1647 Westminster Confession.", "description": "The keys, elders, church courts, and discipline in the 1647 Westminster Confession.",
     "schema": "Article", "parent": "doctrine.html", "toc": True},
])

PAGES.append({
    "file": "bible.html", "content": "bible.html", "title": "KJV Bible",
    "full_title": "King James Bible · Gentle King", "eyebrow": "The Holy Bible",
    "h1": "King James Bible", "deck": "Read the Authorized Version here on Gentle King.",
    "description": "Read the King James Bible on Gentle King. Choose a book and chapter or open a Scripture reference beside the article you are reading.",
    "schema": "WebPage", "toc": False,
})

for filename, doc, title in [
    ("westminster-confession.html", "wcf", "Westminster Confession of Faith"),
    ("larger-catechism.html", "wlc", "Westminster Larger Catechism"),
    ("shorter-catechism.html", "wsc", "Westminster Shorter Catechism"),
]:
    PAGES.append({"file": filename, "content": filename, "title": title,
                  "full_title": title + " · Gentle King", "h1": title,
                  "eyebrow": "The original Westminster Standards",
                  "deck": "The historical text and Scripture proofs from The Westminster Standard.",
                  "description": "Read the original " + title + " and its Scripture proofs on Gentle King.",
                  "schema": "WebPage", "parent": "westminster-study.html", "standard": doc, "toc": False})

# Original Westminster doctrine and discipleship pages.
PAGES.extend([
    {"file": "doctrine-baptism.html", "content": "doctrine-baptism.html", "title": "Baptism", "full_title": "Baptism · Gentle King", "eyebrow": "Doctrine and discipleship", "h1": "Baptism", "deck": "Christ\u2019s covenant sign and seal, with promised grace truly conferred by the Spirit in God\u2019s appointed time.", "description": "Baptism as a sign and seal of the covenant of grace, infant baptism, and the Spirit\u2019s real efficacy without automatic regeneration.", "schema": "Article", "parent": "doctrine.html", "toc": True},
    {"file": "doctrine-justification.html", "content": "doctrine-justification.html", "title": "Justification", "full_title": "Justification · Gentle King", "eyebrow": "Doctrine and discipleship", "h1": "Justification", "deck": "Pardoned and accepted through Christ's righteousness alone.", "description": "Pardoned and accepted through Christ's righteousness alone.", "schema": "Article", "parent": "doctrine.html", "toc": True},
    {"file": "doctrine-christ-mediator.html", "content": "doctrine-christ-mediator.html", "title": "Christ the Mediator", "full_title": "Christ the Mediator · Gentle King", "eyebrow": "Doctrine and discipleship", "h1": "Christ the Mediator", "deck": "True God and true man, our Prophet, Priest and King.", "description": "True God and true man, our Prophet, Priest and King.", "schema": "Article", "parent": "doctrine.html", "toc": True},
    {"file": "doctrine-fall-and-sin.html", "content": "doctrine-fall-and-sin.html", "title": "The Fall and Original Sin", "full_title": "The Fall and Original Sin · Gentle King", "eyebrow": "Doctrine and discipleship", "h1": "The Fall and Original Sin", "deck": "Adam's headship and humanity's need for grace.", "description": "Adam's headship and humanity's need for grace.", "schema": "Article", "parent": "doctrine.html", "toc": True},
    {"file": "doctrine-christian-liberty.html", "content": "doctrine-christian-liberty.html", "title": "Christian Liberty", "full_title": "Christian Liberty · Gentle King", "eyebrow": "Doctrine and discipleship", "h1": "Christian Liberty", "deck": "Conscience and obedience in the 1647 Confession.", "description": "Conscience and obedience in the 1647 Confession.", "schema": "Article", "parent": "doctrine.html", "toc": True},
    {"file": "doctrine-oaths-and-vows.html", "content": "doctrine-oaths-and-vows.html", "title": "Oaths and Vows", "full_title": "Oaths and Vows · Gentle King", "eyebrow": "Doctrine and discipleship", "h1": "Oaths and Vows", "deck": "The duty to take lawful oaths when rightly required, keep them faithfully, and refuse promises that require sin.", "description": "Original Westminster teaching on taking and keeping lawful oaths, truthful testimony, vows to God, and promises that cannot bind anyone to sin.", "schema": "Article", "parent": "doctrine.html", "toc": True},
    {"file": "foundations.html", "content": "foundations.html", "title": "Foundations of the Christian Faith", "full_title": "Foundations of the Christian Faith · Gentle King", "eyebrow": "Doctrine and discipleship", "h1": "Foundations of the Christian Faith", "deck": "Sixteen lessons through the Christian faith.", "description": "Sixteen lessons through the Christian faith.", "schema": "CollectionPage", "parent": "start-here.html", "toc": True},
    {"file": "westminster-study.html", "content": "westminster-study.html", "title": "Westminster Study Center", "full_title": "Westminster Study Center · Gentle King", "eyebrow": "Doctrine and discipleship", "h1": "Westminster Study Center", "deck": "The 33 chapters of the original Confession with proofs.", "description": "The 33 chapters of the original Confession with proofs.", "schema": "CollectionPage", "parent": "doctrine.html", "toc": True},
    {"file": "corrections.html", "content": "corrections.html", "title": "Corrections and Sources", "full_title": "Corrections and Sources · Gentle King", "eyebrow": "Doctrine and discipleship", "h1": "Corrections and Sources", "deck": "Sources and the process for reporting errors.", "description": "Sources and the process for reporting errors.", "schema": "Article", "parent": "about.html", "toc": True},
])

MOVED["doctrine"] = {'why-doctrine': 'doctrine-why-doctrine.html#why-doctrine',
 'scripture': 'doctrine-scripture.html#scripture',
 'god-and-trinity': 'doctrine-god-and-trinity.html#god-and-trinity',
 'five-solas': 'doctrine-five-solas.html#five-solas',
 'doctrines-of-grace': 'doctrine-doctrines-of-grace.html#doctrines-of-grace',
 'covenant': 'doctrine-covenant.html#covenant',
 'law-and-gospel': 'doctrine-law-and-gospel.html#law-and-gospel',
 'church-and-worship': 'doctrine-church-and-worship.html#church-and-worship',
 'last-things': 'doctrine-last-things.html#last-things',
 'standards': 'doctrine-standards.html#standards'}
for page in PAGES:
    if page["file"] == "doctrine.html":
        page.update(schema="CollectionPage", toc=False, moved="doctrine")
        page["deck"] = "Explore Reformed doctrine one subject at a time, from Scripture to the things to come."
    if page["file"] == "guides.html":
        page["deck"] = "Find help for daily Christian life. Choose a topic or search the guides below."
        page["scripts"] = ["assets/js/guides.js"]
        page["styles"] = ["assets/css/guides.css"]
    if page["file"] == "index.html":
        page.pop("notice", None)
    if page["file"] == "corrections.html":
        page["scripts"] = ["assets/js/corrections.js"]
for page in BELIEVER_PAGES:
    page["parent"] = "assurance.html"

# Include the practical church guides in the existing visible topic finder.
GUIDE_PAGES.extend([
    _child('guide-church-membership.html', 'Church Membership',
           'Church Membership · Gentle King', 'Church and Worship',
           'Church Membership', "Ask a pastor or elder about joining, request the vows, and discuss baptism, profession of faith, or transfer. Learn what membership asks and what care to expect.",
           "How to seek church membership, understand vows, meet with elders, distinguish communicant membership, and receive accountable pastoral care.",
           ['Church Membership'], parent='guides.html'),
    _child('guide-joining-rpc.html', 'Visiting and Joining an RP Church',
           'Visiting and Joining an RP Church · Gentle King', 'Church and Worship',
           'Visiting and Joining an RP Church', "Find a congregation, ask about visiting, and speak with the elders about membership. Read the actual vows and distinguish original Standards from current procedures.",
           "Visiting and joining an RPCNA congregation, worship, communion admission, baptism, membership conversations, and current denominational requirements.",
           ['RPCNA Membership'], parent='guides.html'),
])
PAGES = [p for page in PAGES for p in [page] + CHILDREN.get(page["file"], [])]
BY_FILE = {p["file"]: p for p in PAGES}


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

# An open book, drawn like the crown. It marks the way to Sojourner in the
# header and under the verse on the home page, so the two read as one signpost.
BOOK_SVG = (
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" '
    'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">'
    '<path d="M12 7.1C10 5.6 7.2 5 3.6 5.2v12.7c3.6-.2 6.4.4 8.4 1.9 2-1.5 4.8-2.1 8.4-1.9V5.2'
    'C16.8 5 14 5.6 12 7.1z"/>'
    '<path d="M12 7.1v12.7"/>'
    "</svg>"
)

# Mortify's own icon, shown small with rounded corners beside its name. The name
# is always there for a screen reader, so the picture says nothing.
MORTIFY_ICON = (
    '<img src="assets/img/mortify-icon-64.png" width="64" height="64" alt="" decoding="async">'
)

# On a phone every page folds into the menu, so the gospel keeps a link of its
# own beside the menu button. On a wide screen site.css hides it, since the row
# of pages already holds it.
HEADER_GOSPEL = '<a class="header-gospel" href="gospel.html"{current}>The Gospel</a>'

# The two apps under Tools. With script the list opens from its button, and
# without it the list simply shows.
NAV_TOOLS = """      <div class="nav-group">
        <button class="nav-group-btn{current}" type="button" aria-expanded="false" aria-controls="nav-tools">Tools<span class="nav-group-caret" aria-hidden="true"></span></button>
        <ul class="nav-group-list" id="nav-tools" aria-label="Tools">
{items}
        </ul>
      </div>"""
NAV_TOOL = (
    '          <li><a href="{href}"{current}>{icon}<span class="nav-tool-name">{name}</span>'
    '<span class="nav-tool-note">{note}</span></a></li>'
)

# The light and dark switch as a row at the foot of the menu. On a phone the
# header has room for the two apps or for the switch, not both, and the switch
# is the one a reader sets once and leaves. site.css shows this row only there.
MENU_THEME = """      <button class="menu-theme" type="button">
        <span class="menu-theme-dark"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>Switch to dark</span>
        <span class="menu-theme-light"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>Switch to light</span>
      </button>"""

HEAD = """<!DOCTYPE html>
<html lang="en" prefix="og: https://ogp.me/ns#">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{full_title}</title>
<meta name="description" content="{description}">
<link rel="canonical" href="{canonical}">
<meta name="robots" content="{robots}">
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
<link rel="stylesheet" href="{css}">
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
{nav_tools}
{menu_theme}
    </nav>
    <div class="nav-tools">
      {header_gospel}
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
      <a class="btn btn-primary" href="gospel.html">Hear the gospel</a>
      <a class="btn" href="#where-to-turn">Find help for where you are</a>
    </div>
  </div>
</section>
"""

# A quiet line under a page head, the same as the Sojourner line under the
# hero on the home page. A page asks for one with "notice" in PAGES.
NOTICE = """<aside class="app-notice" aria-label="{label}">
  <div class="wrap">
    <a href="{href}"{target}>{icon}{text}
      <span class="app-notice-go"><span class="app-notice-label">{go}</span></span></a>
  </div>
</aside>
"""

PAGE_HEAD = """<div class="page-head">
  <div class="wrap">
{crumbs}    <p class="eyebrow">{eyebrow}</p>
    <h1>{h1}</h1>
    <p class="page-deck">{deck}</p>
  </div>
</div>
"""

# A web app's page leads with its icon, its name, a verse, and the way in.
PAGE_HEAD_APP = """<div class="page-head page-head-app">
  <div class="wrap">
    <img class="app-mark" src="assets/img/{icon}" width="512" height="512" alt="" decoding="async">
    <h1>{h1}</h1>
    <blockquote class="scripture app-verse">
      <p>{verse}</p>
      <cite>{ref}</cite>
    </blockquote>
    <p class="page-deck">{deck}</p>
    <div class="btn-row">
      <a class="btn btn-primary" href="{href}" target="_blank" rel="noopener">{go}</a>
      <a class="btn" href="#open">How to begin</a>
    </div>
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
{actions}  </div>
</div>
"""

# Under a software page's mark, the plain facts and the way to get it, so the
# first screen says what it is, what it runs on, and where the download is.
HEAD_ACTIONS = """    <ul class="facts" aria-label="At a glance">
{facts}
    </ul>
    <div class="btn-row">
      <a class="btn btn-primary" href="{web}" target="_blank" rel="noopener">Open in your browser</a>
      <a class="btn" href="{releases}" target="_blank" rel="noopener">Download for Windows or Linux</a>
    </div>
    <p class="head-meta">Version {version} &middot; In any browser, or on Windows and Linux</p>
{shot}"""

# Where a page sits, above its eyebrow, for a page that belongs under another.
CRUMBS = """    <nav class="crumbs" aria-label="Breadcrumb"><ol>{items}</ol></nav>
"""

# The foot of a page in a series or under a parent. Previous and Next for a
# series that reads in order, and the way back up for every child page.
PAGER = """<nav class="pager" aria-label="{label}">
{links}
</nav>
"""

FOOTER = """<footer class="site-footer">
  <div class="wrap">
    <div class="footer-grid">
      <div>
        <p class="footer-verse">Take my yoke upon you, and learn of me; for I am meek and lowly
          in heart: and ye shall find rest unto your souls.</p>
        <p class="footer-verse-ref">Matthew 11:29 (KJV)</p>
        <p class="footer-head footer-give">Abolish Abortion</p>
        <p class="footer-abolish">Protect unborn children and help mothers in need.</p>
        <ul class="footer-links">
          <li><a href="guide-abortion.html">What the Bible says</a></li>
          <li><a href="https://abolishabortionindiana.org/" target="_blank" rel="noopener">Abolish Abortion Indiana</a></li>
        </ul>
      </div>
      <nav aria-label="Read">
        <p class="footer-head">Read</p>
        <ul class="footer-links">
          <li><a href="start-here.html">Start here</a></li>
          <li><a href="gospel.html">The Gospel</a></li>
          <li><a href="search.html">Search all teaching</a></li>
          <li><a href="comfort.html">Grief and hard times</a></li>
          <li><a href="struggle.html">Fighting sin</a></li>
          <li><a href="doctrine.html">Doctrine</a></li>
          <li><a href="apologetics.html#objector">Answers to objections</a></li>
          <li><a href="assurance.html">Assurance and doubt</a></li>
          <li><a href="guides.html">Practical guides</a></li>
        </ul>
      </nav>
      <nav aria-label="Tools">
        <p class="footer-head">Tools</p>
        <ul class="footer-links">
          <li><a href="bible.html">King James Bible</a></li>
          <li><a href="biblehelps/">Bible Reading Helps</a></li>
          <li><a href="sojourner.html">Sojourner</a></li>
          <li><a href="mortify.html">Mortify</a></li>
        </ul>
        <p class="footer-head footer-give">Give</p>
        <a class="btn btn-primary" href="{donate_url}" target="_blank" rel="noopener">Donate</a>
      </nav>
      <nav aria-label="About">
        <p class="footer-head">About</p>
        <ul class="footer-links">
          <li><a href="about.html">About this site</a></li>
          <li><a href="about.html#contact">Contact</a></li>
          <li><a href="https://thewestminsterstandard.org/the-westminster-confession/" target="_blank" rel="noopener">The Westminster Confession</a></li>
        </ul>
      </nav>
    </div>
    <div class="footer-base">
      <p>&copy; {year} Gentle King. You may share the original writing unchanged and noncommercially with attribution under <a href="https://creativecommons.org/licenses/by-nc-nd/4.0/" target="_blank" rel="noopener">CC BY-NC-ND 4.0</a>.</p>
      <p><a href="about.html#what-this-is">This site is no substitute for a local church</a></p>
    </div>
    <p class="footer-fineprint">{scripture_notice}</p>
  </div>
</footer>

<button class="to-top" type="button" aria-label="Back to top">
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 19V5M5 12l7-7 7 7"/></svg>
</button>

<script src="{site_js}" defer></script>
</body>
</html>
"""


def asset(path):
    """A stylesheet or script address that changes whenever the file does.

    GitHub Pages lets a browser keep a file for ten minutes. Without this, a
    reader who came by just before a push gets the new page with the old
    stylesheet, and anything new on the page is drawn unstyled.
    """
    digest = hashlib.sha256((ROOT / path).read_bytes()).hexdigest()[:10]
    return f"{path}?v={digest}"


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


PARTIALS = CONTENT / "partials"


def include(name):
    """A block shared by several pages, from content/partials/."""
    path = PARTIALS / f"{name}.html"
    if not path.exists():
        raise SystemExit(f"missing partial: {path}")
    return path.read_text(encoding="utf-8").strip()


def guide_topic(page):
    name = page["file"]
    if any(x in name for x in ("bible", "reading-scripture", "prophecy", "meditation")):
        return "Bible Study"
    if any(x in name for x in ("marriage", "sex", "homosexuality", "birth-control", "ivf", "parenting", "spanking", "abortion", "family-worship")):
        return "Family"
    if any(x in name for x in ("prayer", "repentance", "examine", "forgiveness", "fasting", "evangelism")):
        return "Prayer and Growth"
    if any(x in name for x in ("worship", "church", "lords", "sermons")):
        return "Church and Worship"
    return "Discernment" if page.get("series") == "discern" else "Daily Life"


def reading_minutes(page):
    body = fragment(page)
    if page.get("close"):
        body += include(page["close"])
    return max(1, (len(plain(body).split()) + 199) // 200)


def related_html(page):
    if page.get("schema") != "Article":
        return ""
    name = page["file"]
    choices = {
        "guide-bible-reading.html": ["guide-reading-scripture.html", "guide-meditation.html"],
        "guide-free-will.html": ["doctrine-doctrines-of-grace.html", "guide-disagreeing.html"],
        "struggle.html": ["guide-repentance.html", "assurance-remaining-sin.html"],
        "gospel.html": ["guide-bible-reading.html", "guide-find-a-church.html"],
    }.get(name)
    if not choices:
        if name.startswith("assurance-"):
            choices = ["assurance-am-i-his.html", "assurance-kept.html", "struggle.html"]
        elif name.startswith("comfort-"):
            choices = ["assurance-affliction.html", "guide-prayer.html"]
        elif name.startswith("doctrine-"):
            choices = ["guide-bible-reading.html", "doctrine-standards.html", "gospel.html"]
        elif name.startswith("guide-"):
            topic = guide_topic(page)
            choices = [p["file"] for p in GUIDE_PAGES if guide_topic(p) == topic and p["file"] != name]
        else:
            choices = ["gospel.html", "guide-reading-scripture.html"]
    choices = [x for x in choices if x != name][:2]
    links = "".join(f'<li><a href="{x}">{html.escape(BY_FILE[x]["h1"])}</a></li>' for x in choices)
    return f'<aside class="related-reading" aria-label="Related reading"><h2>Read Next</h2><ul>{links}</ul></aside>'


def paths_html(series, pages=None):
    """The list of a series' pages on its parent, each with its deck, so the list
    can never disagree with the pages it points to."""
    rows = []
    for page in (SERIES[series] if pages is None else pages):
        rows.append(
            f'    <li data-topic="{guide_topic(page)}"><a href="{page["file"]}"><span class="paths-title">{html.escape(page["h1"])}</span>'
            f'<span class="paths-desc">{html.escape(page["description"] if pages is not None or series in ("life", "discern", "says") else page["deck"])}</span><span class="reading-time">{reading_minutes(page)} min read</span></a></li>'
        )
    return "\n".join(rows)


GUIDE_TOPIC_GROUPS = (
    ("Bible Study", "bible-study", None),
    ("Prayer and Growth", "prayer-and-growth", "christian-life"),
    ("Church and Worship", "church-and-worship", None),
    ("Discernment", "discernment", "discernment"),
    ("Family", "family", "bible-says"),
    ("Daily Life", "daily-life", None),
)


def guide_topics_html():
    groups = []
    for title, slug, legacy in GUIDE_TOPIC_GROUPS:
        pages = [page for page in GUIDE_PAGES if guide_topic(page) == title]
        anchor = f'<span class="guide-anchor" id="{legacy}" aria-hidden="true"></span>' if legacy else ""
        groups.append(anchor + f'<details class="guide-group" id="topic-{slug}" open>'
                      f'<summary><h2>{title}</h2><span class="guide-count" data-guide-count>{len(pages)} guides</span></summary>'
                      f'<ol class="paths">{paths_html("topics", pages)}</ol></details>')
    return "\n".join(groups)


def fragment(page):
    """A page's words, as content/ holds them, with the shared blocks, the
    library list, and the Sojourner version written in where it asks for them."""
    if page.get("standard"):
        from standards_reader import render_standard
        return render_standard(page["standard"])
    body = (CONTENT / page["content"]).read_text(encoding="utf-8")
    if "<!-- foundations-lessons -->" in body:
        from foundations_course import render_lessons
        body = body.replace("<!-- foundations-lessons -->", render_lessons())
    if "<!-- guide-topics -->" in body:
        body = body.replace("<!-- guide-topics -->", guide_topics_html())
    if LIBRARY_MARK in body:
        body = body.replace(LIBRARY_MARK, library_html())
    body = re.sub(r"<!-- include ([a-z-]+) -->", lambda m: include(m.group(1)), body)
    body = re.sub(r"<!-- paths ([a-z]+) -->", lambda m: paths_html(m.group(1)), body)
    # The Resources catalogue contains verbatim historical book titles and lists.
    # Keep its archival text untouched; article and guide references are linked.
    return tokens(body) if page["file"] == "resources.html" else link_references(tokens(body))


def tokens(text):
    return (text.replace("{{version}}", APP_VERSION).replace("{{size}}", APP_SIZE_MB)
            .replace("{{size_deb}}", APP_SIZE_DEB_MB).replace("{{size_appimage}}", APP_SIZE_APPIMAGE_MB))


def fingerprint(page):
    """The words a reader sees on the page. The title and description are left
    out, so tuning them for search does not pretend the page was rewritten."""
    body = fragment(page)
    shown = [str(page.get(key, "")) for key in ("eyebrow", "h1", "deck")]
    if page.get("head_shot"):
        shown.append(include(page["head_shot"]))
    for key in ("close", "facts"):
        if page.get(key):
            shown.append(json.dumps(page[key]))
    if page.get("close"):
        shown.append(include(page["close"]))
    if page.get("hero"):
        shown.append(HERO)
    if page.get("notice"):
        shown.append(json.dumps(page["notice"], sort_keys=True))
    if page.get("app_head"):
        shown.append(json.dumps(page["app_head"], sort_keys=True))
    return hashlib.sha256("\n".join(shown + [body]).encode("utf-8")).hexdigest()[:16]


def git_date(page, first):
    """The date of the first or the last commit that touched the page's words.
    The author date, since a rebase moves the other one."""
    args = ["git", "log", "--format=%aI"]
    if first:
        args += ["--diff-filter=A", "--follow"]
    args += ["--", f"assets/standards/{page['standard']}.json" if page.get("standard") else f"content/{page['content']}"]
    try:
        out = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return ""
    lines = out.split()
    return (lines[-1] if first else lines[0]) if lines else ""


def page_dates():
    """Read the ledger, move the date of any page whose words changed, save it.
    A page carved out of its parent keeps the parent's first date, since its
    words were published then."""
    try:
        ledger = json.loads(DATES.read_text(encoding="utf-8"))
    except FileNotFoundError:
        ledger = {}
    ledger = {name: entry for name, entry in ledger.items() if name in BY_FILE}
    now = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()
    for page in PAGES:
        mark = fingerprint(page)
        seen = ledger.get(page["file"])
        if seen is None:
            parent = ledger.get(page.get("parent", ""))
            ledger[page["file"]] = {
                "hash": mark,
                "published": (parent or {}).get("published") or git_date(page, first=True) or now,
                "modified": now if parent else (git_date(page, first=False) or now),
            }
        elif seen["hash"] != mark:
            seen["hash"] = mark
            seen["modified"] = now
    for gone in set(ledger) - {page["file"] for page in PAGES}:
        del ledger[gone]
    DATES.write_text(json.dumps(ledger, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return ledger


# --------------------------------------------------------------------------
# Structured data (JSON-LD)
#
# One connected graph per page, so search engines and AI tools can tell who
# publishes the site, who writes it, what each page is, and what Sojourner is.
# Say nothing here the pages do not say. No ratings, no reviews, no guessed
# dates. The Sojourner version, size, and screenshots are read from
# content/sojourner.html, so they cannot drift from the page. The email
# addresses are left out on purpose, since the pages keep them from harvesters.
# --------------------------------------------------------------------------

ORG_ID = f"{SITE_URL}/#organization"
SITE_ID = f"{SITE_URL}/#website"
PERSON_ID = f"{SITE_URL}/#colt"
APP_ID = f"{SITE_URL}/sojourner.html#app"
MORTIFY_ID = f"{SITE_URL}/{MORTIFY_PAGE}#app"
LOGO_URL = f"{SITE_URL}/brand/gentle-king-icon-512.png"

ORG_DESCRIPTION = (
    "A confessionally Reformed and Presbyterian ministry website. It sets out the gospel of "
    "Jesus Christ, Scripture for hard hours, help in the fight against sin, Reformed doctrine "
    "held to the Westminster Confession of Faith, and apologetics, and it "
    "gives away Sojourner, a free Bible study app for the browser, Windows, and Linux, and Mortify, a free app for the "
    "fight against sin. It is the work of one layman "
    "and is not a church."
)

# Each line must match something sojourner.html says. No counts here, so a
# release that changes a number only has to change the page.
APP_FEATURES = [
    "Works offline, with no account, no subscription, and no telemetry",
    "English Bible translations that are public domain or free to share, among them the King James of 1769 and the Geneva of 1599",
    "The Hebrew Old Testament, five editions of the Greek New Testament, the Septuagint, and the Vulgate",
    "Hebrew and Greek lexicons, an interlinear with the grammar of every word in plain English, word studies, and search by grammar",
    "Commentaries by Matthew Henry and John Calvin, and Spurgeon's Treasury of David",
    "The Westminster Confession and Catechisms with their Scripture proofs, and the Three Forms of Unity",
    "An encyclopedia, a Bible dictionary, Webster's dictionary of 1828, cross references, a Factbook, an atlas, and a timeline with the history of the church",
    "Optional book shelves of Puritan and Reformed works, the Church Fathers, and more",
    "Optional map packs that give the atlas its hills, a 3D view of the land, and a view from the sky",
    "Linked panes that turn to the same verse together, and one search box for everything",
    "Notes, highlights, a prayer journal, reading plans, and Scripture and catechism memory",
    "A sermon editor with templates, a preaching mode, slides, handouts, and a podium file for phones",
    "A guided family worship page with a reading, a psalm, a catechism question, and prayer",
    "The 1650 Scottish Metrical Psalter on a page of its own, with tunes that play",
    "Color text, with every person, place, time, and number in the Bible in its own color, and God's own words set apart",
]

CONFESSION_WORKS = [
    "Westminster Confession of Faith",
    "Westminster Larger Catechism",
    "Westminster Shorter Catechism",
]


def page_url(page):
    return f"{SITE_URL}/" if page["file"] == "index.html" else f"{SITE_URL}/{page['file']}"


def ancestors(page):
    """The pages above this one, the highest first."""
    up = []
    while page.get("parent"):
        page = BY_FILE[page["parent"]]
        up.insert(0, page)
    return up


def page_title(page):
    return page.get("full_title") or f"{page['title']} · {SITE_NAME}"


def og_image(page):
    return page.get("og_image", "og-cover.png?v=2")


def plain(fragment):
    """Visible text from a bit of HTML."""
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", fragment)).split())


def app_facts(body=None):
    """The version and download size of the current release."""
    return APP_VERSION, APP_SIZE_MB


def screenshots(body):
    """Each screenshot on the Sojourner pages, full size, with its caption. The
    pictures on the main page come first."""
    bodies = [include("sojourner-shot"), body] + [fragment(p) for p in SOJOURNER_PAGES]
    shots, seen = [], set()
    for text in bodies:
        for href, caption in re.findall(
            r'(?s)<figure class="shot[^"]*">\s*<a href="([^"]+)".*?<figcaption>(.*?)</figcaption>', text
        ):
            if href in seen:
                continue
            seen.add(href)
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
        "alternateName": [APP_FULL, "Sojourner Bible Study Software", "Sojourner Bible app"],
        "keywords": "free Bible software, offline Bible, Bible study app for Windows, Bible software for Linux, free Bible app for iPhone and Android, Reformed Bible study, Matthew Henry commentary, Westminster Confession",
        "description": page["description"],
        "url": canonical,
        "mainEntityOfPage": {"@id": f"{canonical}#webpage"},
        "image": f"{SITE_URL}/assets/img/sojourner-logo.png",
        "applicationCategory": "ReferenceApplication",
        "applicationSubCategory": "Bible study",
        "operatingSystem": "Windows 10, Windows 11, Linux, and any modern web browser on iOS, Android, or macOS",
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


def mortify_node(own_page=True):
    """Mortify as its own page describes it. Nothing here the page does not say.
    Graphs do not join up across pages, so another page that mentions it names
    the app in brief, without pointing back to a page it does not describe."""
    if not own_page:
        return {
            "@type": "WebApplication",
            "@id": MORTIFY_ID,
            "name": MORTIFY_NAME,
            "url": f"{SITE_URL}/{MORTIFY_PAGE}",
            "applicationCategory": "LifestyleApplication",
            "isAccessibleForFree": True,
            "author": {"@id": PERSON_ID},
            "publisher": {"@id": ORG_ID},
        }
    return {
        "@type": "WebApplication",
        "@id": MORTIFY_ID,
        "name": MORTIFY_NAME,
        "description": (
            "A free web app for putting sin to death by the Spirit. Scripture, Puritan counsel, "
            "and prayer in the hour of temptation, a morning reading, an evening examination, "
            "help after a fall, and a few brethren from your own church to pray for you."
        ),
        "url": MORTIFY_URL,
        "image": f"{SITE_URL}/assets/img/mortify-icon-512.png",
        "screenshot": {
            "@type": "ImageObject",
            "url": f"{SITE_URL}/assets/img/mortify-home.webp",
            "caption": "Mortify on a phone. Flee is the first thing on its home page, with the day's word under it.",
        },
        "applicationCategory": "LifestyleApplication",
        "operatingSystem": "Any",
        "browserRequirements": "A current web browser",
        "isAccessibleForFree": True,
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD", "url": MORTIFY_URL},
        "inLanguage": "en",
        "mainEntityOfPage": {"@id": f"{SITE_URL}/{MORTIFY_PAGE}#webpage"},
        "author": {"@id": PERSON_ID},
        "publisher": {"@id": ORG_ID},
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
        trail = [("Home", f"{SITE_URL}/")]
        trail += [(p["title"], page_url(p)) for p in ancestors(page)]
        trail.append((page["title"], canonical))
        graph.append({
            "@type": "BreadcrumbList",
            "@id": f"{canonical}#breadcrumb",
            "itemListElement": [
                {"@type": "ListItem", "position": i, "name": name, "item": url}
                for i, (name, url) in enumerate(trail, 1)
            ],
        })
    if page.get("parent"):
        parent = BY_FILE[page["parent"]]
        webpage["isPartOf"] = [{"@id": SITE_ID}, {
            "@type": "CollectionPage" if parent.get("schema") == "CollectionPage" else "WebPage",
            "@id": f"{page_url(parent)}#webpage",
            "url": page_url(parent),
            "name": page_title(parent),
        }]

    if is_home:
        webpage["about"] = {"@id": ORG_ID}
        webpage["mentions"] = {"@id": APP_ID}
        # Graphs do not join up across pages, so the home page names the app
        # itself. The full description is on sojourner.html.
        graph.append({
            "@type": "SoftwareApplication",
            "@id": APP_ID,
            "name": APP_NAME,
            "alternateName": [APP_FULL, "Sojourner Bible Study Software", "Sojourner Bible app"],
        "keywords": "free Bible software, offline Bible, Bible study app for Windows, Bible software for Linux, free Bible app for iPhone and Android, Reformed Bible study, Matthew Henry commentary, Westminster Confession",
            "url": f"{SITE_URL}/sojourner.html",
            "applicationCategory": "ReferenceApplication",
            "operatingSystem": "Windows 10, Windows 11, Linux, and any modern web browser on iOS, Android, or macOS",
            "isAccessibleForFree": True,
            "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
            "author": {"@id": PERSON_ID},
            "publisher": {"@id": ORG_ID},
        })
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
        if page.get("parent"):
            article["isPartOf"] = {"@id": f"{page_url(BY_FILE[page['parent']])}#webpage"}
        if MORTIFY_PAGE in body or MORTIFY_URL in body:
            article["mentions"] = {"@id": MORTIFY_ID}
            graph.append(mortify_node(own_page=False))
        cites = citations(body) + page.get("cites", [])
        if cites:
            article["citation"] = cites
        graph.append(article)
    elif kind == "ItemPage" and page.get("app") == "mortify":
        webpage["mainEntity"] = {"@id": MORTIFY_ID}
        graph.append(mortify_node())
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
        if 'id="lib-shelves"' in body:
            count, _ = library_counts()
            webpage["mainEntity"] = {
                "@type": "ItemList",
                "@id": f"{canonical}#library",
                "name": "The Gentle King Library",
                "description": (
                    "Puritan and Reformed classics, with the King James "
                    "and the Berean Standard Bible. Read available text editions in the browser, download EPUBs, or follow links to historical scans. Rights vary by edition and country."
                ),
                "numberOfItems": count,
                "url": f"{canonical}#library",
            }

    text = json.dumps({"@context": "https://schema.org", "@graph": graph},
                      ensure_ascii=False, separators=(",", ":"))
    # A "</" inside the script block could end it early. JSON allows "<\/".
    text = text.replace("</", "<\\/")
    return f'<script type="application/ld+json">{text}</script>\n'


# Each app's page and the mark that goes beside its name.
APP_ICONS = {"bible.html": BOOK_SVG, APP_PAGE: BOOK_SVG, MORTIFY_PAGE: MORTIFY_ICON, "biblehelps/": BOOK_SVG}


def section_of(current):
    """The top page a page belongs under, for marking its place in the menu."""
    if current.startswith(("assurance", "comfort")) or current == "struggle.html":
        return "help.html"
    if current.startswith(("doctrine", "apologetics")):
        return "learn.html"
    if current == "gospel.html":
        return "start-here.html"
    page = BY_FILE.get(current, {})
    up = ancestors(page)
    return up[0]["file"] if up else current


def mark(href, current):
    """The page itself is the current page. Its parent is the current section."""
    if href == current or (href == "./" and current == "index.html"):
        return ' aria-current="page"'
    if href == section_of(current):
        return ' aria-current="true"'
    return ""


def nav_links(current):
    return "\n".join(f'      <a href="{href}"{mark(href, current)}>{label}</a>' for href, label in NAV)


def nav_tools(current):
    items = "\n".join(
        render(NAV_TOOL, href=href, current=mark(href, current), icon=APP_ICONS[href],
               name=name, note=note)
        for href, name, note in TOOLS
    )
    here = any(mark(href, current) for href, _, _ in TOOLS)
    return render(NAV_TOOLS, items=items, current=" is-current" if here else "")


def header_gospel(current):
    return render(HEADER_GOSPEL, current=' aria-current="page"' if current == "gospel.html" else "")


def crumbs_html(page):
    up = ancestors(page)
    if not up:
        return ""
    items = '<li><a href="./">Home</a></li>' + "".join(
        f'<li><a href="{p["file"]}">{html.escape(p.get("crumb", p["title"]))}</a></li>' for p in up
    )
    return render(CRUMBS, items=items)


def pager_html(page):
    """Previous and Next through a series, and the way back to the parent."""
    if not page.get("parent"):
        return ""
    parent = BY_FILE[page["parent"]]
    links = []
    series = SERIES.get(page.get("series"))
    if series:
        i = series.index(page)
        if i > 0:
            prev = series[i - 1]
            links.append(f'  <a class="pager-prev" href="{prev["file"]}" rel="prev"><span class="pager-dir">Previous</span>'
                         f'<span class="pager-title">{html.escape(prev["h1"])}</span></a>')
        if i < len(series) - 1:
            nxt = series[i + 1]
            links.append(f'  <a class="pager-next" href="{nxt["file"]}" rel="next"><span class="pager-dir">Next</span>'
                         f'<span class="pager-title">{html.escape(nxt["h1"])}</span></a>')
        up = {"objector": "apologetics.html#objector", "believer": "assurance.html#begin",
              "life": "guides.html#christian-life", "discern": "guides.html#discernment",
              "says": "guides.html#bible-says"}[page["series"]]
        word = {"objector": "All the questions", "believer": "All the fears",
                "life": "All the guides", "discern": "All the guides", "says": "All the guides"}[page["series"]]
    else:
        up = parent["file"]
        word = {"comfort.html": "Every sorrow on Comfort"}.get(parent["file"], f"Back to {parent['title']}")
    links.append(f'  <a class="pager-up" href="{up}">{html.escape(word)}</a>')
    return render(PAGER, label="More pages like this", links="\n".join(links))


def new_tab_note(text):
    """A link that opens a new tab says so to a screen reader, which cannot see
    the tab appear."""
    def note(m):
        if "opens in a new tab" in m.group(2):
            return m.group(0)
        return f'{m.group(1)}{m.group(2)}<span class="visually-hidden"> (opens in a new tab)</span></a>'
    return re.sub(r'(?s)(<a [^>]*target="_blank"[^>]*>)(.*?)</a>', note, text)


def sections(body):
    """Each top level section of a page that has an h2, as (id, heading). The
    heading keeps its HTML entities, so it can go straight back into a page.
    Run it through plain() for anything that is not HTML."""
    found = []
    for sid, inner in re.findall(r'(?s)<section class="section" id="([^"]+)"[^>]*>(.*?)</section>', body):
        h2 = re.search(r"(?s)<h2([^>]*)>(.*?)</h2>", inner)
        if h2:
            # A heading that is a verse names itself shorter in data-toc.
            short = re.search(r'data-toc="([^"]+)"', h2.group(1))
            text = short.group(1) if short else re.sub(r"<[^>]+>", "", h2.group(2))
            found.append((sid, " ".join(text.split())))
    return found


def toc_html(body):
    """The On this page list, written into the HTML so a reader without script,
    a search engine, or an AI tool sees the page's sections at the top. site.js
    builds the same list again on load."""
    empty = "<nav data-toc></nav>\n"
    found = sections(body)
    if len(found) < 3:
        return empty
    items = "".join(f'<li><a href="#{sid}">{text}</a></li>' for sid, text in found)
    return (
        '<nav data-toc class="toc" aria-label="On this page">'
        f'<p class="toc-title">On this page</p><ol>{items}</ol></nav>\n'
    )


# --------------------------------------------------------------------------
# The library on the Resources page
#
# resources/library/catalog.json lists every book in the free library. The
# Resources page carries the whole list, written into the HTML here, so a reader
# with scripts off, a search engine, or an AI tool sees every book, with its
# links. assets/js/library.js then adds the search box and the filters, working
# from what each book shows. To add a book, add it to the catalog and rebuild.
# The content fragment marks where the list goes with <!-- library -->.
# --------------------------------------------------------------------------

LIBRARY = ROOT / "resources" / "library"
LIBRARY_MARK = "<!-- library -->"
READER = "resources/read.html"

# The shelves in the order they stand, each with a line to say what is on it.
# A category the catalog has and this list lacks still shows, at the end.
SHELVES = {
    "Bibles": "The King James Version, and the Berean Standard Bible for a modern English translation.",
    "Study Bibles": "Bibles printed with notes, and notes on the whole Bible to read beside it.",
    "Confessions & Catechisms": "The Westminster Standards, the Three Forms of Unity, the confessions that stand beside them, and the books that open them.",
    "Systematic Theology": "The whole body of divinity set out in order.",
    "Doctrine": "Treatises that take one doctrine at a time and go deep.",
    "Christian Life": "Practical books for the life of faith, for holiness and comfort and the fight with sin.",
    "Sermons": "Sermons first preached and then printed.",
    "Commentaries": "Expositions of the books of the Bible, set in the order of the Bible.",
    "Worship & Prayer": "Public and family worship, prayer, the Lord's Day, and the sacraments.",
    "Church & Ministry": "The government of the church, the work of the pastor, and preaching.",
    "History & Biography": "The story of the Reformation and the lives of those God used in it.",
    "Letters & Diaries": "Letters and private journals, where the old saints speak plainly.",
    "Poetry & Allegory": "Psalms, hymns, poems, and the allegories.",
    "Apologetics & Controversy": "The faith defended, and the debates the Reformed churches fought through.",
    "Collected Works": "The works of one author gathered together, most of them in several volumes.",
}

BIBLE_BOOKS = [
    "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy", "Joshua", "Judges", "Ruth",
    "1 Samuel", "2 Samuel", "1 Kings", "2 Kings", "1 Chronicles", "2 Chronicles", "Ezra",
    "Nehemiah", "Esther", "Job", "Psalms", "Proverbs", "Ecclesiastes", "Song of Solomon",
    "Isaiah", "Jeremiah", "Lamentations", "Ezekiel", "Daniel", "Hosea", "Joel", "Amos",
    "Obadiah", "Jonah", "Micah", "Nahum", "Habakkuk", "Zephaniah", "Haggai", "Zechariah",
    "Malachi", "Matthew", "Mark", "Luke", "John", "Acts", "Romans", "1 Corinthians",
    "2 Corinthians", "Galatians", "Ephesians", "Philippians", "Colossians", "1 Thessalonians",
    "2 Thessalonians", "1 Timothy", "2 Timothy", "Titus", "Philemon", "Hebrews", "James",
    "1 Peter", "2 Peter", "1 John", "2 John", "3 John", "Jude", "Revelation",
]
WHOLE = ["Whole Bible", "Old Testament", "New Testament"]
BOOK_ALIASES = {"Psalm": "Psalms", "Song of Songs": "Song of Solomon", "Canticles": "Song of Solomon",
                "Revelations": "Revelation", "Apocalypse": "Revelation"}

# Where a book came from decides a word or two the reader should know.
OLD_SPELLING = "Text Creation Partnership"


def display_name(category):
    return category.replace(" & ", " and ")


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def size_label(size):
    mb = size / 1048576
    return f"{mb:.1f} MB" if mb >= 0.95 else f"{max(1, round(size / 1024))} KB"


def scripture_of(work):
    found = []
    for name in work.get("scripture") or []:
        name = BOOK_ALIASES.get(name.strip(), name.strip())
        if (name in BIBLE_BOOKS or name in WHOLE) and name not in found:
            found.append(name)
    return found


@functools.lru_cache(maxsize=None)
def library_catalog():
    catalog = json.loads((LIBRARY / "catalog.json").read_text(encoding="utf-8"))
    for work in catalog["works"]:
        for f in work["files"]:
            if f["format"] == "epub" and not re.fullmatch(r"[a-z0-9][a-z0-9\-/]*\.epub", f["path"]):
                raise SystemExit(f"library path the reader will refuse: {f['path']}")
            if not (LIBRARY / f["path"]).exists():
                raise SystemExit(f"catalog lists a file that is not there: {f['path']}")
    return catalog


def library_counts():
    works = library_catalog()["works"]
    files = sum(len(w["files"]) for w in works)
    return len(works), files


def read_href(path):
    if path.endswith(".pdf"):
        return f"resources/library/{path}"
    return f"{READER}?book=library/{path}"


# A book made by machine from a scan comes out jumbled and misread too often to
# hand out. For those, Read opens the scanned pages themselves at the Internet
# Archive, and no download is offered. The reader and the downloads are kept for
# the clean texts.
SCANNED = "Internet Archive"


def file_links(f, described_by, scanned=False):
    """The Read and Download links for one file. A screen reader hears the
    book's title with each, from the ids given, since a page of links all
    called Read tells it nothing."""
    e = html.escape
    kind = f["format"].upper()
    size = size_label(f["size_bytes"])
    if scanned and f.get("source"):
        return (
            f'<a class="lib-read" href="{e(f["source"])}" target="_blank" rel="noopener" '
            f'aria-describedby="{described_by}">Read the scan</a>'
        )
    read_word = "Open PDF" if f["format"] == "pdf" else "Read"
    return (
        f'<a class="lib-read" href="{e(read_href(f["path"]))}" aria-describedby="{described_by}">{read_word}</a>'
        f'<a class="lib-dl" href="resources/library/{e(f["path"])}" download aria-describedby="{described_by}">'
        f'Download {kind} <span>{size}</span></a>'
    )


def scan_link(link, described_by, text="Scan at the Internet Archive"):
    e = html.escape
    return (
        f'<a class="lib-dl" href="{e(link["url"])}" target="_blank" rel="noopener" '
        f'aria-describedby="{described_by}">{text}</a>'
    )


def volume_rows(entries, tid, scanned=False):
    """A list of volumes, each a file to read or a scan kept at the Internet
    Archive, in volume order. Past four it folds away behind a summary."""
    e = html.escape
    rows = []
    for i, (kind, item) in enumerate(entries, 1):
        label = item["label"] or (f"Volume {item['volume']}" if item.get("volume") else "The book")
        vid = f"{tid}v{i}"
        contents = f' <span class="lib-vol-contents">{e(item["contents"])}</span>' if item.get("contents") else ""
        action = file_links(item, f"{tid} {vid}", scanned) if kind == "file" else scan_link(item, f"{tid} {vid}")
        rows.append(
            f'<li class="lib-vol"><span class="lib-vol-name" id="{vid}">{e(label)}</span>{contents}'
            f'<span class="lib-actions">{action}</span></li>'
        )
    vols = f'<ol class="lib-vols">{"".join(rows)}</ol>'
    if len(entries) > 4:
        vols = f'<details class="lib-more"><summary>{len(entries)} volumes</summary>{vols}</details>'
    return vols


def library_item(work, by_id, n):
    """One book. The finder in library.js reads what it filters on from here,
    the shelf from the details around it, the topics from their line, and the
    books of the Bible from data-books, which is the one thing not shown."""
    e = html.escape
    title = work["title"]
    books = scripture_of(work)
    topics = work.get("topics") or []
    tid = f"t{n}"
    attrs = f' data-books="{e("|".join(books))}"' if books else ""
    out = [f'<li class="lib-item" id="book-{e(work["id"])}"{attrs}>']

    marks = []
    if work.get("start"):
        marks.append('<span class="lib-mark lib-start">A good place to start</span>')
    if work.get("source") == OLD_SPELLING:
        marks.append('<span class="lib-mark">Old spelling</span>')
    out.append(f'<p class="lib-title"><span id="{tid}">{e(title)}</span>{"".join(marks)}</p>')

    by = e(work["author"])
    if work.get("author_dates"):
        by += f' ({e(work["author_dates"])})'
    # A Bible belongs to no one tradition, so it carries none, and a year
    # before printing is the year of a manuscript, which its dates already give.
    bible = work["category"] == "Bibles"
    trad = "" if bible else f'<span class="lib-trad">{e(work["tradition"])}</span>'
    year = work.get("first_published")
    year = f'<span class="lib-year">first published {year}</span>' if year and year >= 1450 else ""
    out.append(f'<p class="lib-by">{by}{trad}{year}</p>')

    if work.get("blurb"):
        out.append(f'<p class="lib-blurb">{e(work["blurb"])}</p>')
    if work.get("passage") and work["category"] in ("Commentaries", "Sermons", "Study Bibles"):
        out.append(f'<p class="lib-passage">On {e(work["passage"])}</p>')
    if work.get("notes"):
        out.append(f'<p class="lib-note">{e(work["notes"])}</p>')

    files, links = work["files"], work["links"]
    scanned = work.get("source") == SCANNED
    if len(files) == 1 and not links:
        out.append(f'<p class="lib-actions">{file_links(files[0], tid, scanned)}</p>')
    elif files:
        # A volume or some pages kept only as a scan sit among the files,
        # in volume order, so a missing part is found where it belongs.
        entries = [("file", f) for f in files] + [("scan", l) for l in links]
        entries.sort(key=lambda kv: kv[1].get("volume") or 0)
        out.append(volume_rows(entries, tid, scanned))
    elif len(links) == 1:
        out.append(
            '<p class="lib-scan">Only a scan of an old printing is online for now. '
            + scan_link(links[0], tid, "Read the scan at the Internet Archive") + "</p>"
        )
    elif links:
        out.append('<p class="lib-scan">Only scans of an old printing are online for now.</p>'
                   + volume_rows([("scan", l) for l in links], tid))

    parent = work.get("found_in")
    if not files and parent and parent.get("id") in by_id:
        vols = parent.get("volumes") or []
        where = ""
        if len(vols) == 1:
            where = f", volume {vols[0]}"
        elif vols:
            where = ", volumes " + " and ".join(str(v) for v in vols)
        out.append(
            f'<p class="lib-in">Printed in <a href="#book-{e(parent["id"])}">{e(parent["title"])}</a>{where}.</p>'
        )
        host = by_id[parent["id"]]
        host_scanned = host.get("source") == SCANNED
        parent_files = {f["path"]: f for f in host["files"]}
        found = [parent_files[p] for p in parent.get("paths", []) if p in parent_files]
        if len(found) == 1:
            out.append(f'<p class="lib-actions">{file_links(found[0], tid, host_scanned)}</p>')
        elif found:
            out.append(volume_rows([("file", f) for f in found], tid, host_scanned))

    if topics:
        out.append(f'<p class="lib-tags">{" · ".join(e(t) for t in topics)}</p>')
    out.append("</li>")
    return "".join(out)


def shelf_order(category, works):
    if category in ("Bibles", "Study Bibles"):
        return sorted(works, key=lambda w: (w.get("first_published") or 9999, w["title"]))
    if category == "Commentaries":
        def place(w):
            books = scripture_of(w)
            first = min((BIBLE_BOOKS.index(b) for b in books if b in BIBLE_BOOKS), default=None)
            if first is None:
                first = -3 + WHOLE.index(books[0]) if books and books[0] in WHOLE else 999
            return (first, w.get("first_published") or 9999, w["author_sort"])
        return sorted(works, key=place)
    tier = {"core": 0, "standard": 1, "further": 2}
    return sorted(works, key=lambda w: (not w.get("start"), tier.get(w["tier"], 3), w["author_sort"],
                                        w.get("first_published") or 0))


@functools.lru_cache(maxsize=None)
def library_html():
    e = html.escape
    catalog = library_catalog()
    works = catalog["works"]
    by_id = {w["id"]: w for w in works}
    order = list(SHELVES) + [c for c in dict.fromkeys(catalog["categories"] + [w["category"] for w in works])
                             if c not in SHELVES]
    shelves = {c: [w for w in works if w["category"] == c] for c in order}

    topics = collections.Counter(t for w in works for t in (w.get("topics") or []))
    # A book of the Bible is offered when some work speaks to it, directly or
    # as part of a work on the whole Bible or a whole Testament, the same rule
    # library.js filters by. The Bibles themselves are left out of that.
    books_used = set()
    for w in works:
        named = scripture_of(w)
        books_used.update(b for b in named if b in BIBLE_BOOKS)
        if w["category"] != "Bibles":
            if "Whole Bible" in named:
                books_used.update(BIBLE_BOOKS)
            if "Old Testament" in named:
                books_used.update(BIBLE_BOOKS[:39])
            if "New Testament" in named:
                books_used.update(BIBLE_BOOKS[39:])
    traditions = sorted({w["tradition"] for w in works if w["category"] != "Bibles"})

    def options(values, every, counts=None):
        opts = [f'<option value="">{every}</option>']
        for v in values:
            label = display_name(v) + (f" ({counts[v]})" if counts else "")
            opts.append(f'<option value="{e(v)}">{e(label)}</option>')
        return "".join(opts)

    cat_counts = {c: len(ws) for c, ws in shelves.items() if ws}
    book_values = [b for b in BIBLE_BOOKS if b in books_used]
    finder = f"""<div class="lib-finder" id="lib-finder" role="search" aria-label="Search the library">
  <label class="visually-hidden" for="lib-q">Search the library</label>
  <input class="lib-q" id="lib-q" type="search" placeholder="Search by title, author, or subject" autocomplete="off" enterkeyhint="search">
  <div class="lib-filters">
    <label class="lib-field"><span>Kind of book</span><select id="lib-cat">{options([c for c in order if cat_counts.get(c)], "Every kind", cat_counts)}</select></label>
    <label class="lib-field"><span>Book of the Bible</span><select id="lib-book">{options(book_values, "Any book")}</select></label>
    <label class="lib-field"><span>Tradition</span><select id="lib-trad">{options(traditions, "Every tradition")}</select></label>
  </div>
  <label class="lib-check"><input type="checkbox" id="lib-start"> Only the best places to start</label>
  <details class="lib-topics" id="lib-topics"><summary>Browse by topic</summary>
    <div class="lib-topic-list" role="group" aria-label="Topics">{"".join(f'<button type="button" class="lib-topic" data-topic="{e(t)}" aria-pressed="false">{e(t)} <span>{n}</span></button>' for t, n in sorted(topics.items(), key=lambda tn: tn[0].removeprefix("The ")))}</div>
  </details>
  <p class="lib-status"><span id="lib-count" aria-live="polite"></span><button type="button" class="lib-clear" id="lib-clear" hidden>Clear the search</button></p>
</div>
"""
    counter = itertools.count(1)
    out = ['<div class="lib-recent" id="lib-recent" hidden></div>', finder, '<div class="lib-shelves" id="lib-shelves">']
    for category in order:
        items = shelves.get(category) or []
        if not items:
            continue
        note = SHELVES.get(category, "")
        out.append(
            f'<details class="lib-shelf" id="shelf-{slug(category)}" data-cat="{e(category)}">'
            f'<summary><h3 class="lib-shelf-name">{e(display_name(category))}</h3>'
            f'<span class="lib-shelf-count" data-total="{len(items)}">{len(items)}</span></summary>'
            + (f'<p class="lib-shelf-note">{e(note)}</p>' if note else "")
            + '<ol class="lib-list">'
            + "".join(library_item(w, by_id, next(counter)) for w in shelf_order(category, items))
            + "</ol></details>"
        )
    out.append('</div>\n<p class="lib-empty" id="lib-empty" hidden>No book matches all of that. Try fewer words, or clear the search.</p>')
    return "\n".join(out)


def whole_card_links(body):
    """Use one semantic link for a card with one destination and no other controls."""
    def convert(match):
        attrs, content = match.group(1), match.group(2)
        classes = re.search(r'class="([^"]*)"', attrs)
        if not classes or "card" not in classes.group(1).split():
            return match.group(0)
        links = list(re.finditer(r'<a\b([^>]*)>([\s\S]*?)</a>', content))
        if len(links) != 1 or re.search(r'<(?:button|input|select|textarea|details)\b', content):
            return match.group(0)
        link = links[0]
        if re.search(r'\bid=', attrs + link.group(1)):
            return match.group(0)
        content = content[:link.start()] + '<span class="card-action">' + link.group(2) + '</span>' + content[link.end():]
        attrs = attrs[:classes.start()] + 'class="' + classes.group(1) + ' card-link"' + attrs[classes.end():]
        return '<a' + attrs + link.group(1) + '>' + content + '</a>'
    return re.sub(r'<article([^>]*)>([\s\S]*?)</article>', convert, body)


def build_page(page, dates):
    fragment_path = CONTENT / page["content"]
    if not fragment_path.exists() and not page.get("standard"):
        raise SystemExit(f"missing content fragment: {fragment_path}")
    body = whole_card_links(fragment(page).strip())
    if page.get("close"):
        body += "\n\n<hr class=\"rule\">\n\n" + tokens(include(page["close"]))

    if page.get("schema") == "Article" and page["file"] != "corrections.html":
        article = html.escape(page["file"], quote=True)
        body += ('\n<p class="article-correction">Notice something that needs correcting? '
                 '<a href="corrections.html?article=' + article + '">Report an issue with this page</a>.</p>')

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
            css=asset("assets/css/site.css"),
            robots="noindex" if page.get("hidden") else "max-image-preview:large",
        ),
        render(HEADER, mark=MARK_SVG, nav_links=nav_links(page["file"]),
               nav_tools=nav_tools(page["file"]), menu_theme=MENU_THEME,
               header_gospel=header_gospel(page["file"])),
    ]

    if page.get("styles"):
        styles = "".join(f'<link rel="stylesheet" href="{asset(path)}">\n' for path in page["styles"])
        parts[0] = parts[0].replace("</head>", styles + "</head>")
    if page.get("hero"):
        parts.append(render(HERO, app_page=APP_PAGE, app_name=APP_NAME, book=BOOK_SVG,
                            mortify_page=MORTIFY_PAGE, mortify_name=MORTIFY_NAME,
                            mortify_icon=MORTIFY_ICON))
    elif page.get("app_head"):
        head = page["app_head"]
        parts.append(
            render(
                PAGE_HEAD_APP,
                icon=head["icon"],
                h1=html.escape(page["h1"], quote=False),
                verse=html.escape(head["verse"], quote=False),
                ref=html.escape(head["ref"], quote=False),
                deck=html.escape(page["deck"], quote=False),
                href=head["href"],
                go=html.escape(head["go"], quote=False),
            )
        )
    elif page.get("logo"):
        parts.append(
            render(
                PAGE_HEAD_LOGO,
                logo=page["logo"],
                logo_alt=html.escape(page["logo_alt"], quote=True),
                deck=html.escape(page["deck"], quote=False),
                actions=render(
                    HEAD_ACTIONS,
                    facts="\n".join(f"      <li>{html.escape(f)}</li>" for f in page["facts"]),
                    releases=APP_RELEASES, web=APP_WEB_URL, version=APP_VERSION, size=APP_SIZE_MB,
                    shot=include(page["head_shot"]) + "\n" if page.get("head_shot") else "",
                ) if page.get("facts") else "",
            )
        )
    else:
        parts.append(
            render(
                PAGE_HEAD,
                crumbs=crumbs_html(page),
                eyebrow=html.escape(page["eyebrow"], quote=False),
                h1=html.escape(page["h1"], quote=False),
                deck=html.escape(page["deck"], quote=False),
            )
        )
    if page.get("notice"):
        notice = page["notice"]
        outside = notice["href"].startswith("http")
        parts.append(render(
            NOTICE,
            label=html.escape(notice["label"], quote=True),
            href=notice["href"],
            target=' target="_blank" rel="noopener"' if outside else "",
            icon=notice["icon"],
            text=notice["text"],
            go=notice["go"],
        ))

    main_class = "wrap page-body has-toc" if page.get("toc") else "wrap page-body"
    parts.append(f'<main id="main" class="{main_class}">\n')
    # Urgent contacts live in the Safety page and in topic-specific advice.
    if page.get("toc"):
        parts.append(toc_html(body))
        parts.append('<div class="reading-column">\n')
    if page.get("schema") == "Article":
        parts.append(f'<p class="reading-time">About {reading_minutes(page)} minutes to read</p>')
        answers = {
            "guide-free-will.html": "God gives the new heart and the faith by which a sinner freely comes to Christ. Salvation rests on his mercy, not on a better choice made by one sinner than another.",
            "guide-prophecy.html": "Christ will return bodily, the dead will rise, and God will judge the world. Read symbolic passages in light of clear teaching elsewhere in Scripture.",
            "guide-reading-scripture.html": "Read a passage according to its context and kind of writing. Figures of speech communicate truth, and clear passages help explain difficult ones.",
            "struggle.html": "If anyone is in danger, use the urgent help below first. Stop harm and seek appropriate care. Turn from sin to Christ and fight it by the Spirit, with the help of his Word and your church.",
            "guide-heresy.html": "Test teaching by Scripture. Denying a truth essential to the Christian faith is different from a serious error or a disagreement between faithful believers.",
        }
        if page["file"] in answers:
            parts.append(f'<aside class="quick-answer"><h2>The Short Answer</h2><p>{html.escape(answers[page["file"]])}</p></aside>')
    parts.append(body)
    from foundations_course import course_return
    parts.append(course_return(page["file"]))
    parts.append(related_html(page))
    parts.append("\n" + pager_html(page) if page.get("parent") else "")
    if page.get("moved"):
        # Where each part of the old long page went, for site.js to follow.
        moved = MOVED[page["moved"]]
        parts.append('\n<script type="application/json" id="moved">'
                     + json.dumps(moved, separators=(",", ":")) + "</script>")
    if page.get("toc"):
        parts.append("\n</div>")
    parts.append("\n</main>\n\n")
    site_js = f'<script src="{asset("assets/js/site.js")}" defer></script>\n'
    footer = render(FOOTER, year=COPYRIGHT_YEAR, scripture_notice=SCRIPTURE_NOTICE,
                    donate_url=DONATE_URL, site_js=asset("assets/js/site.js"))
    footer = footer.replace(site_js, site_js + f'<script src="{asset("assets/js/kjv.js")}" defer></script>\n')
    footer = footer.replace(site_js, site_js + f'<script src="{asset("assets/js/foundations.js")}" defer></script>\n')
    for script in page.get("scripts", []):
        footer = footer.replace(site_js, site_js + f'<script src="{asset(script)}" defer></script>\n')
    parts.append(footer)

    (ROOT / page["file"]).write_text(new_tab_note("".join(parts)), encoding="utf-8")
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
# To shut one of them out, take its name off this list and give it a group of
# its own.
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
NOT_PAGES = [
    "/content/", "/.github/", "/README.md", "/brand/README.md", "/resources/README.md",
    "/build.py", "/check.py",
]


def build_sitemap(dates):
    urls = [f"  <url>\n    <loc>{SITE_URL}/biblehelps/</loc>\n  </url>"]
    for page in PAGES:
        if page.get("hidden"):
            continue
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
        *[f"Disallow: {path}" for path in NOT_PAGES],
        "",
        f"Sitemap: {SITE_URL}/sitemap.xml",
    ]
    (ROOT / "robots.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


# The groups llms.txt sorts the pages into, in order. The ministry writing comes
# before the app, because it matters as much or more.
LLMS_GROUPS = [
    ("The gospel", ["gospel.html"]),
    ("Comfort in hard hours", ["comfort.html"] + [p["file"] for p in COMFORT_PAGES]),
    ("Fighting sin", ["struggle.html"]),
    ("Doctrine", ["doctrine.html"]),
    ("Answers to objections", ["apologetics.html"] + [p["file"] for p in OBJECTOR_PAGES]),
    ("Fear, doubt, and assurance, for believers", [p["file"] for p in BELIEVER_PAGES]),
    ("Practical guides", ["guides.html"] + [p["file"] for p in GUIDE_PAGES]),
]


def build_llms_txt():
    """A plain map of the site for AI assistants, in the llms.txt format
    (https://llmstxt.org). Written from PAGES and from each page's own section
    headings, so it can never disagree with the pages. Each page is listed once,
    since a tool that follows the list fetches every link in it. Its sections
    go in the note, where a reader can still follow them."""
    by_file = {p["file"]: p for p in PAGES}
    app_body = (CONTENT / "sojourner.html").read_text(encoding="utf-8")
    version, size_mb = app_facts(app_body)

    def entry(page, label=None):
        url = page_url(page)
        body = fragment(page)
        parts = [f"[{plain(text)}]({url}#{sid})" for sid, text in sections(body)]
        note = page["description"]
        if len(parts) == 1:
            note += f" Its one part is {parts[0]}."
        elif len(parts) == 2:
            note += f" Its parts are {parts[0]} and {parts[1]}."
        elif parts:
            note += " Its parts are " + ", ".join(parts[:-1]) + ", and " + parts[-1] + "."
        return [f"- [{label or page.get('h1') or page['title']}]({url}): {note}"]

    lines = [
        f"# {SITE_NAME}",
        "",
        f"> {SITE_NAME} ({SITE_URL.split('//')[-1]}) is a free ministry site, confessionally "
        "Reformed and Presbyterian. It sets out the gospel of Jesus Christ, Scripture for grief "
        "and other hard hours, help for the fight against sin, Reformed doctrine held to the "
        "Westminster Confession of Faith, answers to objections against Christianity, and "
        f"{APP_NAME}, a free Bible study app for the browser, Windows, and Linux.",
        "",
        f"The site is written by {AUTHOR_NAME}, a layman in the Reformed Presbyterian tradition. "
        "He is not a pastor or an elder, and the site is no substitute for a local church. "
        "Scripture is quoted from the King James Version. The Westminster Standards are quoted "
        "from the text of 1647. The writing may be copied and shared freely under the Creative "
        "Commons Attribution-NonCommercial-NoDerivatives 4.0 license. Please do not sell it, and "
        "please do not change the words and keep the name on it.",
        "",
        f"{APP_NAME} {version} is free Bible study software for Windows 10 and 11 and for Linux, "
        "64-bit, made by the same writer and given away free. On Linux it comes as a .deb for "
        "Ubuntu 24.04, Linux Mint 22, and Debian 13 or newer, and as an AppImage for most other "
        "systems from 2024 on. It needs no account, works with the network off, and sends no "
        f"telemetry. The Windows installer is about {size_mb} MB, the .deb about "
        f"{APP_SIZE_DEB_MB} MB, and the AppImage about {APP_SIZE_APPIMAGE_MB} MB. The same app "
        f"runs in any modern browser at {APP_WEB_URL}, on phones, tablets, and computers, and "
        "can be installed to the home screen as a progressive web app.",
        "",
        f"{MORTIFY_NAME} ({MORTIFY_URL}) is a free web app by the same writer for putting sin to "
        "death by the Spirit. It works in the browser on a phone or a computer, and it needs a "
        "free account made with an email address.",
        "",
        "In the United States, call 911 for immediate danger. For thoughts of suicide or emotional "
        "distress, call or text 988. Anyone being hurt at home can call the National Domestic Violence "
        "Hotline at 1-800-799-7233, or text START to 88788. If a child is in immediate danger, call 911. "
        "Outside the United States, call the local emergency number. The page If You Are Not "
        f"Safe ({SITE_URL}/comfort-safety.html) gives these numbers and more.",
        "",
    ]
    for heading, files in LLMS_GROUPS:
        lines += [f"## {heading}", ""]
        for name in files:
            lines += entry(by_file[name])
            if name == "resources.html":
                count, files_n = library_counts()
                lines.append(
                    f"- [The library catalog]({SITE_URL}/resources/library/catalog.json): All {count} "
                    "works in the free library as JSON, each with its author, dates, category, "
                    f"topics, and the paths of its {files_n} EPUB and PDF files, which sit beside it "
                    f"under {SITE_URL}/resources/library/. Consult the catalog rights and edition notes, especially outside the United States."
                )
        lines.append("")

    # Include every remaining visible registered page once, including entry
    # pages, Foundations, individual doctrines, and correction/source guidance.
    listed = {name for _, files in LLMS_GROUPS for name in files}
    listed.update([APP_PAGE, MORTIFY_PAGE, "about.html", "index.html"])
    listed.update(page["file"] for page in SOJOURNER_PAGES)
    remaining = [page for page in PAGES if page["file"] not in listed and not page.get("hidden")]
    lines += ["## Further teaching and study", ""]
    lines += [f"- [Bible Reading Helps]({SITE_URL}/biblehelps/): All 66 book guides, interpretation lessons, the catechism course, original Westminster texts, and KJV passage reading."]
    for page in remaining:
        lines += entry(page)
    lines.append("")

    lines += [f"## {APP_NAME}, a free Bible study app", ""]
    lines += entry(by_file["sojourner.html"], APP_NAME)
    for page in SOJOURNER_PAGES:
        lines += entry(page)
    lines += [
        f"- [Open {APP_NAME} in the browser]({APP_WEB_URL}): The web app, for any device",
        f"- [Download {APP_NAME}]({APP_RELEASES}): The Windows installer, the Linux .deb and "
        "AppImage, and the four optional book shelves, on GitHub",
        "",
    ]
    lines += [f"## {MORTIFY_NAME}, a free app for the fight against sin", ""]
    lines += entry(by_file[MORTIFY_PAGE], MORTIFY_NAME)
    lines += [
        f"- [Open {MORTIFY_NAME}]({MORTIFY_URL}): The app itself, in the browser",
        "",
        "## About the site",
        "",
    ]
    lines += entry(by_file["about.html"])
    lines += [
        "",
        "## Optional",
        "",
        f"- [Home]({SITE_URL}/): The gospel in brief, why the site is called Gentle King, "
        "and what it holds",
        f"- [License]({REPO_URL}/blob/main/LICENSE): The terms for the writing and the site code",
        "",
    ]
    (ROOT / "llms.txt").write_text("\n".join(lines), encoding="utf-8")



def build_search_index():
    records = [dict(url="biblehelps/index.html", title="Bible Reading Helps", section="",
                    text="Interactive Bible reading companion. Guides to all 66 books, 24 study lessons, 107 Shorter Catechism lessons, Westminster Confession and Catechisms, Scripture memory, worked examples, and KJV passage reading.")]

    for page in PAGES:
        if page.get("hidden") or page["file"] == "search.html":
            continue
        body = fragment(page)
        records.append(dict(url=page["file"], title=page["title"],
                            section="", text=page.get("deck", page["description"])+(" "+plain(body) if len(sections(body)) < 1 else "")))
        for sid, inner in re.findall(r'<section class="section" id="([^"]+)"[^>]*>([\s\S]*?)</section>', body):
            heading = re.search(r'<h2[^>]*>(.*?)</h2>', inner, re.S)
            if heading:
                records.append(dict(url=page["file"]+"#"+sid, title=page["title"],
                                    section=plain(heading.group(1)), text=plain(inner)))
    (ROOT / "assets" / "search-index.json").write_text(json.dumps(records, ensure_ascii=False, separators=(",", ":"))+"\n", encoding="utf-8")


def main():
    dates = page_dates()
    total = 0
    for page in PAGES:
        name, words = build_page(page, dates)
        total += words
        print(f"  {name:<18} {words:>6,} words")
    build_search_index()
    build_sitemap(dates)
    build_llms_txt()
    # Some tools ask for the icon at the root without reading the page's links.
    shutil.copyfile(ROOT / "assets" / "img" / "favicon.ico", ROOT / "favicon.ico")
    host = build_cname()
    print(f"  {'sitemap.xml':<18} {'':>6}")
    print(f"  {'robots.txt':<18} {'':>6}")
    print(f"  {'llms.txt':<18} {'':>6}")
    print(f"  {'CNAME':<18} {host:>6}")
    print(f"\nBuilt {len(PAGES)} pages, {total:,} words.")


if __name__ == "__main__":
    sys.exit(main())
