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

# Where the Donate button in the footer goes.
DONATE_URL = "https://buymeacoffee.com/gentlekingministry"

# The Bible study software.
APP_NAME = "Sojourner"
APP_FULL = "Sojourner, Bible Study Companion"
APP_RELEASES = "https://github.com/z3r0Colt/sojourner/releases"
APP_EMAIL = "sojourner@gentleking.org"
APP_REPO = "https://github.com/z3r0Colt/sojourner"
APP_PAGE = "sojourner.html"
# The current release. Written into the pages wherever {{version}} and {{size}}
# appear, into the structured data, and into llms.txt, so a new release changes
# these two lines and nothing else.
APP_VERSION = "0.4.0"
APP_SIZE_MB = "592"

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

# The ministry's own pages come first, with the gospel at the head of them. The
# two apps are tools of the ministry, so they sit together at the end of the row
# under Tools, a small menu that opens on a click. On a phone every page folds
# into the menu, and the header keeps one link of its own beside the menu
# button, the gospel. The row fits on one line from 1025px. Another item needs
# the 64rem breakpoint in site.css and the 1024 in site.js raised, or belongs in
# the footer.
NAV = [
    ("./", "Home"),
    ("gospel.html", "The Gospel"),
    ("comfort.html", "Comfort"),
    ("struggle.html", "Fighting Sin"),
    ("doctrine.html", "Doctrine"),
    ("apologetics.html", "Apologetics"),
    ("guides.html", "Guides"),
    ("about.html", "About"),
]

# The apps under Tools, each with a line saying what it is for.
TOOLS = [
    (APP_PAGE, APP_NAME, "Bible study for Windows"),
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
            "Gentle King is a free Reformed ministry site. The gospel of Jesus Christ, Scripture "
            "for grief, help against sin, and Sojourner, a Bible study app for Windows."
        ),
        "hero": True,
        "toc": False,
    },
    {
        "file": "sojourner.html",
        "content": "sojourner.html",
        "title": "Sojourner",
        "full_title": "Sojourner Bible Study Software \u00b7 Free and Offline for Windows",
        "eyebrow": "Bible Study Companion",
        "h1": "Sojourner",
        "logo": "sojourner-logo",
        "logo_alt": "Sojourner, Bible Study Companion",
        "og_image": "og-sojourner.png",
        "og_alt": "Sojourner, Bible Study Companion. A free, offline Bible study companion for Windows.",
        "deck": (
            "A free Bible study program for Windows, for the pastor, the family, and the "
            "student. Scripture beside the commentaries, confessions, and reference works of the "
            "Reformed church, on your own computer, with no account and no internet needed."
        ),
        "description": (
            "Sojourner is free, offline Bible study software for Windows. Thirteen translations, "
            "the Hebrew and Greek, Matthew Henry, Calvin, and the Westminster Standards."
        ),
        "schema": "ItemPage",
        # The first screen says what it is, for whom, and where to get it.
        "facts": ["Free", "Windows 10 and 11", "Works offline", "No account", "No telemetry"],
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
        "deck": (
            "The gospel is the good news that God sent his Son, Jesus Christ, who died for sinners "
            "and rose again, and that everyone who trusts in him alone is forgiven and counted "
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
            "one who holds it with a shaking hand. Each has pages of his own."
        ),
        "description": (
            "Honest answers to common objections to Christianity, from God and the Bible to evil "
            "and hell, and Scripture for the believer who fears he is not really saved."
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
            "How to pray, read the Bible, keep the Lord\u2019s Day, share the gospel, and examine "
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
        ('The house is quiet, or it is full of people, and either way the one you want is not '
         'in it. You do not have to be strong tonight. Christ has stood where you are '
         'standing.'),
        ('Scripture and plain counsel for the night someone you love has died. Christ wept at '
         'a grave, and he will not hurry you past your grief.'),
        ['Grief'],
        parent="comfort.html", crisis=True, close="comfort-close",
    ),
    _child(
        'comfort-widowed.html',
        'When Your Husband or Wife Has Died',
        'When Your Husband or Wife Has Died · Scripture for the Widowed · Gentle King',
        'Widowhood',
        'When Your Husband or Wife Has Died',
        ('The one who knew you best is gone, and half of every habit in the house went with '
         'them. There is no timetable for this. Christ saw to those left behind even while he '
         'was dying.'),
        ('King James Scripture and plain counsel for a widow or widower. The one who saw to '
         'his mother from the cross still sees the one left behind.'),
        ['The death of a husband or wife'],
        parent="comfort.html", crisis=True, close="comfort-close",
    ),
    _child(
        'comfort-death-of-a-child.html',
        'When Your Child Has Died',
        'When Your Child Has Died · Comfort for Grieving Parents · Gentle King',
        'A child',
        'When Your Child Has Died',
        ('No parent should outlive a child, and every part of you knows it. Whether you lost a'
         ' baby you barely held, or never held at all, or a son or daughter you raised, Christ'
         ' has not looked away.'),
        ('Scripture for parents who have lost a child, before birth, as a baby, or grown. '
         'Christ took little children in his arms, and he holds the keys of death.'),
        ['The death of a child', 'Miscarriage'],
        parent="comfort.html", crisis=True, close="comfort-close", cites=[{"@type": "CreativeWork", "name": "Canons of Dort"}],
    ),
    _child(
        'comfort-did-they-know-christ.html',
        'When You Fear They Did Not Know Christ',
        'When You Fear They Did Not Know Christ · Gentle King',
        'The hardest question',
        'When You Fear They Did Not Know Christ',
        ('Some of us bury people we love without knowing whether they knew Christ. Some of you'
         ' are not unsure. You fear you know. This is for you too, and you are not asked to '
         'settle anything tonight.'),
        ('Grieving someone who may not have known Christ? Leave them with the Judge of all the'
         ' earth, who will do right, and bring your own soul to him.'),
        ['Grief for an unbeliever'],
        parent="comfort.html", crisis=True, close="comfort-close",
    ),
    _child(
        'comfort-suicide-loss.html',
        'When Someone You Love Took Their Own Life',
        'When Someone You Love Took Their Own Life · Gentle King',
        'Loss by suicide',
        'When Someone You Love Took Their Own Life',
        ('A death like this leaves questions no other death leaves. You may be carrying grief '
         'and guilt and fear all at once. God saw what you could not see, and he is near you '
         'now.'),
        ('For those left behind after a suicide. Scripture on grief, false guilt, and the '
         'keeping of Christ. If you are in danger, call or text 988 now.'),
        ['Suicide loss'],
        parent="comfort.html", close="comfort-close",
    ),
    _child(
        'comfort-illness.html',
        'When Serious Illness Comes',
        'When Serious Illness Comes · Scripture for the Sick and Dying · Gentle King',
        'Sickness',
        'When Serious Illness Comes',
        ('One conversation in a small room, and the future looks different than it did this '
         'morning, for you or for someone you love. Or it has looked this way for years. You '
         'do not have to be brave tonight. Your times are in God’s hand.'),
        ('King James Scripture for a hard diagnosis, a long illness, caring for someone, and '
         'the end of life. Your times are in the hand of God.'),
        ['Serious illness', 'Caregiving', 'The end of life'],
        parent="comfort.html", crisis=True, close="comfort-close",
    ),
    _child(
        'comfort-marriage.html',
        'When Your Marriage Is Breaking',
        'When Your Marriage Is Breaking · Betrayal, Divorce, and Hope · Gentle King',
        'A broken marriage',
        'When Your Marriage Is Breaking',
        ('You were left, or betrayed, or handed papers you did not want. The one who promised '
         'to stay did not. Whether you are the husband or the wife, Christ knows what it is to'
         ' be betrayed.'),
        ('Scripture for the betrayed and the deserted, what God has said about divorce, a word'
         ' for the one who broke faith, and a word for children of divorce.'),
        ['A breaking marriage and divorce'],
        parent="comfort.html", crisis=True, close="comfort-close",
    ),
    _child(
        'comfort-prodigal.html',
        'When Your Child Walks Away From the Lord',
        'When Your Child Walks Away From the Lord · Gentle King',
        'A wandering child',
        'When Your Child Walks Away From the Lord',
        ('You taught them to pray, and now they want nothing to do with Christ. You cannot '
         'give anyone a new heart. Only God can, and he has done it for sons and daughters as '
         'far off as yours.'),
        ('For parents of a prodigal. Only God gives a new heart, and he has done it for sons '
         'and daughters as far off as yours. Pray, wait, and keep the door open.'),
        ['A child who turns from the Lord'],
        parent="comfort.html", crisis=True, close="comfort-close",
    ),
    _child(
        'comfort-work-and-home.html',
        'When the Work or the Home Is Gone',
        'When the Work or the Home Is Gone · Scripture for Hard Times · Gentle King',
        'Want',
        'When the Work or the Home Is Gone',
        ('The job or the business is gone, or the savings, or a fire or a flood took the '
         'house. It is hard to be the one who is supposed to provide. If you are his, your '
         'Father knows what you need.'),
        ('For a lost job, a failed business, or a house taken by fire or flood. Your Father '
         'knows what you need, and his church is bound to help.'),
        ['Loss of work or home'],
        parent="comfort.html", crisis=True, close="comfort-close",
    ),
    _child(
        'comfort-loneliness.html',
        'When You Are Alone',
        'When You Are Alone \u00b7 Scripture for the Lonely Christian \u00b7 Gentle King',
        'Loneliness',
        'When You Are Alone',
        ('The house is quiet, or the room is full and no one knows you. You may have been '
         'alone for years. Christ knew what it was to be left, and he has not left you.'),
        ('For the single, the divorced, the newly moved, and the lonely in a crowded church. '
         'Christ was left alone, and God setteth the solitary in families.'),
        ['Loneliness'],
        parent="comfort.html", crisis=True, close="comfort-close",
    ),
    _child(
        'comfort-depression.html',
        'When Your Own Mind Has Gone Dark',
        'When Your Own Mind Has Gone Dark · Depression and the Christian · Gentle King',
        'Darkness',
        'When Your Own Mind Has Gone Dark',
        ('For weeks or years the heaviness has not lifted, or it keeps coming back. Sleep does'
         ' not rest you, and the promises you once loved seem to belong to someone else. '
         'Christ has been in the dark before you.'),
        ('For the Christian under depression. Christ was very heavy in Gethsemane, and he will'
         ' not break a bruised reed. Scripture, care for the body, and help.'),
        ['Depression'],
        parent="comfort.html", close="comfort-close",
    ),
    _child(
        'comfort-safety.html',
        'If You Are Not Safe',
        'If You Are Not Safe · Abuse, Danger, and Thoughts of Suicide · Gentle King',
        'Safety',
        'If You Are Not Safe',
        ('Some hard hours are dangerous. If yours is, the first faithful thing to do is to get'
         ' safe. Read the rest later.'),
        ('In danger now? Call 911. Thinking of ending your life? Call or text 988. Being hurt '
         'at home? Call 1-800-799-7233. Leaving to be safe is not a sin.'),
        ['Safety from violence at home', 'Suicide prevention'],
        parent="comfort.html", close="comfort-close",
    ),
]

OBJECTOR_PAGES = [
    _child(
        'apologetics-god.html',
        'Is God There',
        'Is God There? Answering the Objections to God · Gentle King',
        'God',
        'Is God There',
        ('Every argument against God is made with tools that only work if he is there.'),
        ('Is there no evidence for God? Who made God? Has science replaced him? Every argument'
         ' against God is made with tools that only work if he is there.'),
        ['The existence of God'],
        parent="apologetics.html", series="objector", close="apologetics-close",
    ),
    _child(
        'apologetics-bible.html',
        'Can the Bible Be Trusted',
        'Can the Bible Be Trusted? Answers to Common Objections · Gentle King',
        'Scripture',
        'Can the Bible Be Trusted',
        ('The Bible claims that when it speaks, God speaks. It does not wait on your verdict '
         'to be true, and it has nothing to fear from your questions.'),
        ('Men wrote it, men chose the books, it contradicts itself, it was changed. Plain '
         'answers on the authority of the Bible, its canon, and its manuscripts.'),
        ['The reliability of the Bible'],
        parent="apologetics.html", series="objector", close="apologetics-close",
    ),
    _child(
        'apologetics-resurrection.html',
        'Did Jesus Rise',
        'Did Jesus Rise From the Dead? The Evidence and the Objections · Gentle King',
        'The resurrection',
        'Did Jesus Rise',
        ('The faith rests on an event at a real time and place. If Jesus did not rise, set it '
         'all aside. If he did, you will have to deal with him.'),
        ('Did Jesus live? Is the resurrection a legend? Did the disciples lie, or were they '
         'fooled? The faith rests on an event at a real time and place.'),
        ['The resurrection of Jesus'],
        parent="apologetics.html", series="objector", close="apologetics-close",
    ),
    _child(
        'apologetics-evil.html',
        'Why Is There Evil',
        'Why Does God Allow Evil and Suffering? · Gentle King',
        'The problem of evil',
        'Why Is There Evil',
        ('Many who ask this are carrying a grief of their own, and they should be answered '
         'with care.'),
        ('The problem of evil, whether God is to blame, the conquest of Canaan, and slavery in'
         ' the Bible, answered with care for those who carry a grief of their own.'),
        ['The problem of evil'],
        parent="apologetics.html", series="objector", close="apologetics-close",
    ),
    _child(
        'apologetics-morality.html',
        'Who Decides What Is Good',
        'Can You Be Good Without God? Who Decides What Is Good · Gentle King',
        'The moral law',
        'Who Decides What Is Good',
        ('Nearly everyone is sure that some things are really wrong. Very few ask what makes '
         'them so.'),
        ('Is morality only evolution or culture? Nearly everyone is sure that some things are '
         'really wrong. Very few ask what makes them so.'),
        ['The moral law'],
        parent="apologetics.html", series="objector", close="apologetics-close",
    ),
    _child(
        'apologetics-hell.html',
        'Is Hell Just',
        'Is Hell Just? Why a Loving God Judges Sin · Gentle King',
        'Judgment',
        'Is Hell Just',
        ('Hell is real, and it is felt without end. It should never be spoken of lightly, and '
         'never left out.'),
        ('Would a loving God send anyone to hell? Is forever too long for a short life of sin?'
         ' Hell is real, and it should never be spoken of lightly or left out.'),
        ['Hell'],
        parent="apologetics.html", series="objector", close="apologetics-close",
    ),
    _child(
        'apologetics-only-jesus.html',
        'Why Only Jesus',
        'Why Is Jesus the Only Way to God? · Gentle King',
        'Other religions',
        'Why Only Jesus',
        ('Few things Christians say offend more in our day than that Jesus is the only way to '
         'God.'),
        ('Do all religions lead to God? What about those who never heard? Is it arrogant to '
         'say you are right? Why Christians say Jesus is the only way.'),
        ['The exclusivity of Christ'],
        parent="apologetics.html", series="objector", close="apologetics-close",
    ),
    _child(
        'apologetics-christians.html',
        'What About the Christians',
        'What About the Hypocrites in the Church? · Gentle King',
        'The church',
        'What About the Christians',
        ('Some of the strongest arguments against Christ come from people who carry his name, '
         'and they deserve an honest answer.'),
        ('The church is full of hypocrites, and religion has done great harm. Some of the '
         'strongest arguments against Christ come from people who carry his name.'),
        ['Hypocrisy', 'Religion and harm'],
        parent="apologetics.html", series="objector", close="apologetics-close",
    ),
    _child(
        'apologetics-election.html',
        'Is Election Fair',
        'Is Election Fair? If God Chooses, How Can He Blame Me · Gentle King',
        'Election',
        'Is Election Fair',
        ('The Bible teaches that God chooses whom he will save. Some hear that as a way off '
         'the hook.'),
        ('The Bible teaches that God chooses whom he will save. Is that fair, and is there any'
         ' point in trying? Paul raised the objection himself.'),
        ['Election'],
        parent="apologetics.html", series="objector", close="apologetics-close",
    ),
    _child(
        'apologetics-the-real-objection.html',
        'The Objection Under the Others',
        'The Objection Under the Others · Am I a Good Person · Gentle King',
        'The heart of it',
        'The Objection Under the Others',
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
        'Am I Really His',
        'Am I Really Saved? Assurance of Salvation · Gentle King',
        'Assurance',
        'Am I Really His',
        ('God does not want his children living on guesses. John wrote his first letter to '
         'believers so that they would know they have eternal life (1 John 5:13).'),
        ('Not sure you are saved? Afraid your faith was never real, or that you were not '
         'chosen? The Westminster Confession on the grounds of assurance.'),
        ['Assurance of salvation'],
        parent="apologetics.html", series="believer", close="assurance-close",
    ),
    _child(
        'assurance-remaining-sin.html',
        'When Sin Will Not Leave',
        'When Sin Will Not Leave · Assurance for the Struggling Christian · Gentle King',
        'Remaining sin',
        'When Sin Will Not Leave',
        ('Few things shake a Christian like meeting the same sin again, years after he first '
         'wept over it. Your fear draws one conclusion from that. God has drawn another, and '
         'he has written it down.'),
        ('The same sin again, a sin too great to forgive, a God surely tired of forgiving. '
         'What God has written for the believer who keeps falling.'),
        ['Remaining sin', 'Forgiveness'],
        parent="apologetics.html", series="believer", close="assurance-close",
    ),
    _child(
        'assurance-night-fears.html',
        'Fears That Keep You Awake',
        'The Unpardonable Sin, Hebrews 6, and Losing Your Salvation · Gentle King',
        'Night fears',
        'Fears That Keep You Awake',
        ('Some fears come back at night, when the house is quiet and there is nothing to do '
         'but think. Each of these has an answer that will not give way under you.'),
        ('Afraid you committed the unpardonable sin, frightened by Hebrews 6 and 10, or afraid'
         ' you could lose your salvation? Answers that will not give way.'),
        ['The unpardonable sin', 'Perseverance of the saints'],
        parent="apologetics.html", series="believer", close="assurance-close",
    ),
    _child(
        'assurance-god-feels-far.html',
        'When God Feels Far',
        'When God Feels Far Away · Spiritual Darkness · Gentle King',
        'In the dark',
        'When God Feels Far',
        ('There are seasons when prayer feels like talking to the ceiling and the Bible is '
         'only ink. They do not mean that God has gone.'),
        ('Prayer feels like talking to the ceiling and the Bible is only ink. Scripture for '
         'the believer who fears the Lord and still walks in darkness.'),
        ['Spiritual darkness'],
        parent="apologetics.html", series="believer", close="assurance-close",
    ),
    _child(
        'assurance-doubts-and-thoughts.html',
        'Doubts and Unwanted Thoughts',
        'Doubts and Unwanted Thoughts · For the Doubting Christian · Gentle King',
        'Doubt',
        'Doubts and Unwanted Thoughts',
        ('Some believers are afraid it is not true, and the question will not leave them '
         'alone. Others are afraid of what their own minds keep saying to them.'),
        ('For the believer who wonders if any of it is true, and for one troubled by '
         'blasphemous thoughts that will not stop. Lord, I believe, help thou mine unbelief.'),
        ['Doubt', 'Intrusive thoughts'],
        parent="apologetics.html", series="believer", close="assurance-close",
    ),
    _child(
        'assurance-affliction.html',
        'When Life Breaks',
        'Is God Against Me? Is He Punishing Me? · Gentle King',
        'Affliction',
        'When Life Breaks',
        ('The diagnosis comes, or the child dies, or the marriage comes apart. Under the grief'
         ' a harder question rises, about what God thinks of you.'),
        ('When life breaks, a harder question rises about what God thinks of you. Romans 8, '
         'Hebrews 12, and the difference between punishment and chastening.'),
        ['Affliction', 'Chastening'],
        parent="apologetics.html", series="believer", close="assurance-close",
    ),
    _child(
        'assurance-death.html',
        'When Death Comes Near',
        'Afraid of Dying? Comfort for the Christian Facing Death · Gentle King',
        'The last enemy',
        'When Death Comes Near',
        ('Christians still die, and many of them dread it. Hebrews says the Son of God took '
         'flesh and blood for this very reason.'),
        ('Christians still die, and many dread it. Christ took flesh to deliver those who '
         'through fear of death were all their lifetime subject to bondage.'),
        ['The fear of death'],
        parent="apologetics.html", series="believer", close="assurance-close",
    ),
    _child(
        'assurance-kept.html',
        'Safe in His Keeping',
        'Safe in His Keeping · Perseverance and Assurance · Gentle King',
        'Rest',
        'Safe in His Keeping',
        ('Underneath all these fears is the same suspicion, that in the end it all hangs on '
         'you. Paul closes Romans 8 by naming everything that could come between a believer '
         'and God.'),
        ('Underneath every fear is the suspicion that it all hangs on you. Nothing can '
         'separate a believer from the love of God in Christ Jesus our Lord.'),
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
        "file": "sojourner-library.html",
        "content": "sojourner-library.html",
        "title": "What Comes With Sojourner",
        "full_title": "What Comes With Sojourner · Bibles, Commentaries, Confessions · Gentle King",
        "eyebrow": "Sojourner",
        "h1": "What Comes in the Box",
        "deck": (
            "The translations, the original texts, the lexicons, the commentaries and "
            "confessions, the four book shelves, and where every one of them came from."
        ),
        "description": (
            "The Bibles, Hebrew and Greek texts, lexicons, commentaries, Westminster Standards, "
            "and book shelves that come with Sojourner, and where each one came from."
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
            "How to install Sojourner on Windows, what the SmartScreen warning means, how to "
            "update without losing your notes, and how to add the book shelves and map packs."
        ),
        "about": ["Installing Sojourner"],
        "parent": APP_PAGE,
        "toc": True,
    },
]

GUIDE_PAGES = [
    _child('guide-prayer.html', 'How to Pray', 'How to Pray in a Way That Pleases God · Gentle King', 'Guide', 'How to Pray',
           'What prayer is, how to pray through Christ, the Lord’s Prayer as a pattern, and the habits that keep a believer praying.',
           'What prayer is, how to pray in the name of Christ, how to use the Lord’s Prayer as a pattern, what displeases God in prayer, and how to make it a habit.',
           ['How to Pray'], parent="guides.html", series='life'),
    _child('guide-bible-reading.html', 'How to Read the Bible', 'How to Read the Bible for Yourself · Gentle King', 'Guide', 'How to Read the Bible',
           'How to read Scripture with understanding, where to start, and which helps are worth having.',
           'How to read the Bible for yourself with prayer and understanding, where a new reader should start, a plan for the whole Bible, and helps worth having.',
           ['How to Read the Bible'], parent="guides.html", series='life'),
    _child('guide-examine-yourself.html', 'How to Examine Yourself', 'How to Examine Yourself Biblically · Gentle King', 'Guide', 'How to Examine Yourself',
           'Questions from Scripture and the Larger Catechism to ask yourself, how to do it each day, and how not to drown in it.',
           'How to examine yourself as Scripture commands, with questions from the Larger Catechism, a short daily habit, and a caution for the anxious.',
           ['How to Examine Yourself'], parent="guides.html", series='life'),
    _child('guide-ten-commandments.html', 'The Ten Commandments for a Believer', 'The Ten Commandments for a Believer · What Each One Requires · Gentle King', 'Guide', 'The Ten Commandments for a Believer',
           'Why a forgiven Christian still keeps God’s law, how to read it, what each commandment requires and forbids, and how to use them this week.',
           'Why a Christian keeps the Ten Commandments, how to read them, what each one requires and forbids by the Shorter Catechism, and how to use them.',
           ['The Ten Commandments for a Believer'], parent="guides.html", series='life'),
    _child('guide-worship.html', 'How God Is to Be Worshiped', 'The Regulative Principle of Worship \u00b7 How God Is to Be Worshiped \u00b7 Gentle King', 'Guide', 'How God Is to Be Worshiped',
           'The regulative principle in plain words. God decides how he is worshiped, what he has commanded, what that rules out, and why it matters.',
           'The regulative principle of worship explained plainly. What God commands in worship, elements and circumstances, psalm singing, and why it matters.',
           ['The regulative principle of worship'], parent="guides.html", series='life'),
    _child('guide-lords-day.html', 'How to Keep the Lord’s Day', 'How to Keep the Lord’s Day, the Christian Sabbath · Gentle King', 'Guide', 'How to Keep the Lord’s Day',
           'Why God set apart one day in seven, how to keep it, what counts as necessity and mercy, and how to make it a delight for children.',
           'Why the Lord’s Day is the Christian Sabbath, how to keep it holy, works of necessity and mercy, and how to make it a delight for a family.',
           ['How to Keep the Lord’s Day'], parent="guides.html", series='life'),
    _child('guide-family-worship.html', 'How to Lead Family Worship', 'How to Lead Family Worship · Gentle King', 'Guide', 'How to Lead Family Worship',
           'Read, sing, and pray. A few minutes a day, the way Reformed households have done it for centuries.',
           'How to lead family worship in a few minutes a day. Read the Bible, sing a psalm, and pray, with plain counsel for starting and keeping on.',
           ['How to Lead Family Worship'], parent="guides.html", series='life'),
    _child('guide-evangelism.html', 'How to Share the Gospel', 'How to Share the Gospel With Others · Gentle King', 'Guide', 'How to Share the Gospel',
           'Know the message, pray for people by name, tell the bad news and the good, call for repentance and faith, and bring them to church.',
           'How an ordinary Christian shares the gospel. Know the message, pray, ask questions, call for repentance and faith, and invite people to church.',
           ['How to Share the Gospel'], parent="guides.html", series='life'),
    _child('guide-false-teachers.html', 'How to Spot a False Teacher', 'How to Spot a False Teacher · Gentle King', 'Guide', 'How to Spot a False Teacher',
           'Seven questions to test any teacher by Scripture, the common warning signs today, and what to do when you find one.',
           'How to spot a false teacher. Seven questions to test any preacher by Scripture, common warning signs today, and what to do about it.',
           ['How to Spot a False Teacher'], parent="guides.html", series='discern'),
    _child('guide-heresy.html', 'How to Spot Real Heresy', 'How to Spot Real Heresy · Heresy, Error, and Disagreement · Gentle King', 'Guide', 'How to Spot Real Heresy',
           'The difference between heresy, serious error, and honest disagreement, the truths that mark the line, and how to respond.',
           'The difference between heresy, serious error, and disagreement among the faithful, the truths that mark the line, and how to respond.',
           ['How to Spot Real Heresy'], parent="guides.html", series='discern'),
    _child('guide-false-church.html', 'How to Tell a True Church From a False One', 'How to Tell a True Church From a False One · Gentle King', 'Guide', 'How to Tell a True Church From a False One',
           'The marks of a true church, what makes a church false and why, the warning signs, and what to do.',
           'The three marks of a true church, what makes a church false and why, warning signs to look for, and when you must leave.',
           ['How to Tell a True Church From a False One'], parent="guides.html", series='discern'),
    _child('guide-find-a-church.html', 'How to Find a Faithful Church', 'How to Find a Reformed Presbyterian (RPCNA) Church · Gentle King', 'Guide', 'How to Find a Faithful Church',
           'How to find a Reformed Presbyterian congregation, what to expect when you visit, what to do if none is near, and the questions to ask any church.',
           'How to find an RPCNA Reformed Presbyterian church near you, what to expect when you visit, what to do if none is near, and questions to ask any church.',
           ['How to Find a Faithful Church'], parent="guides.html", series='discern'),
    _child('guide-marriage.html', 'What the Bible Says About Marriage', 'What the Bible Says About Marriage · Gentle King', 'What the Bible says', 'What the Bible Says About Marriage',
           'God made marriage before sin entered the world. What it is, what it pictures, what husbands and wives owe each other, and when it may end.',
           'What the Bible says about marriage. One man and one woman for life, headship and submission, marrying in the Lord, divorce, and singleness.',
           ['Marriage'], parent="guides.html", series='says'),
    _child('guide-sex.html', 'What the Bible Says About Sex', 'What the Bible Says About Sex and Purity · Gentle King', 'What the Bible says', 'What the Bible Says About Sex',
           'Sex is a good gift of God, made for marriage. What Scripture gives, what it forbids, and the cleansing Christ gives the guilty.',
           'What the Bible says about sex. A good gift for marriage alone, what the seventh commandment forbids, purity for the single, and pardon in Christ.',
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
           'Children are a heritage of the Lord. Teaching them, disciplining them, praying for them, and walking with them through the teen years.',
           'What the Bible says about parenting. Covenant children, teaching the faith at home, fathers and mothers, the teen years, and Proverbs 22:6.',
           ['Parenting', 'Christian family'], parent="guides.html", series='says'),
    _child('guide-spanking.html', 'What the Bible Says About Spanking and Discipline', 'What the Bible Says About Spanking and Discipline · Gentle King', 'What the Bible says', 'What the Bible Says About Spanking and Discipline',
           'What the rod in Proverbs means, how to correct a child in love and never in anger, and where discipline ends and abuse begins.',
           'What the Bible says about spanking and disciplining children. The rod in Proverbs, guardrails against anger and abuse, and discipline as love.',
           ['Discipline of children', 'Corporal punishment'], parent="guides.html", series='says'),
    _child('guide-abortion.html', 'What the Bible Says About Abortion', 'What the Bible Says About Abortion and the Unborn · Gentle King', 'What the Bible says', 'What the Bible Says About Abortion',
           'The unborn child bears the image of God. What Scripture says, the hard cases, help for a mother who is afraid, and mercy for the guilty.',
           'What the Bible says about abortion and the unborn child, answers to common objections, help if you are pregnant and afraid, and forgiveness in Christ.',
           ['Abortion', 'The sanctity of human life'], parent="guides.html", series='says'),
    _child('guide-work.html', 'What the Bible Says About Work', 'What the Bible Says About Work · Gentle King', 'What the Bible says', 'What the Bible Says About Work',
           'God gave work before the fall. Working as to the Lord, a hard boss, laziness and overwork, providing for a family, and resting in Christ.',
           'What the Bible says about work. Every lawful calling as service to God, diligence, a hard boss, overwork and rest, and losing a job.',
           ['Work and vocation'], parent="guides.html", series='says'),
    _child('guide-money.html', 'What the Bible Says About Money and Debt', 'What the Bible Says About Money and Debt · Gentle King', 'What the Bible says', 'What the Bible Says About Money and Debt',
           'God owns it all. Contentment, giving, the tithe, borrowing and debt, cosigning, saving, taxes, and help when debt has you under.',
           'What the Bible says about money and debt. Stewardship, contentment, giving and the tithe, credit and loans, cosigning, and getting out from under.',
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
      <a class="btn btn-primary" href="#the-gospel">Hear the gospel</a>
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
      <a class="btn btn-primary" href="{releases}" target="_blank" rel="noopener">Download for Windows</a>
      <a class="btn" href="#features">See what it does</a>
    </div>
    <p class="head-meta">Version {version} &middot; About {size} MB &middot; 64-bit</p>
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
      </div>
      <nav aria-label="Read">
        <p class="footer-head">Read</p>
        <ul class="footer-links">
          <li><a href="gospel.html">The Gospel</a></li>
          <li><a href="comfort.html">Comfort in hard hours</a></li>
          <li><a href="struggle.html">Fighting sin</a></li>
          <li><a href="doctrine.html">Doctrine</a></li>
          <li><a href="apologetics.html#objector">Answers to objections</a></li>
          <li><a href="apologetics.html#believer">Fear and doubt</a></li>
          <li><a href="guides.html">Practical guides</a></li>
        </ul>
      </nav>
      <nav aria-label="Tools">
        <p class="footer-head">Tools</p>
        <ul class="footer-links">
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
      <p>&copy; {year} Gentle King. Everything written here may be copied and shared freely.</p>
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


def paths_html(series):
    """The list of a series' pages on its parent, each with its deck, so the list
    can never disagree with the pages it points to."""
    rows = []
    for page in SERIES[series]:
        rows.append(
            f'    <li><a href="{page["file"]}"><span class="paths-title">{html.escape(page["h1"])}</span>'
            f'<span class="paths-desc">{html.escape(page["deck"])}</span></a></li>'
        )
    return "\n".join(rows)


def fragment(page):
    """A page's words, as content/ holds them, with the shared blocks, the
    library list, and the Sojourner version written in where it asks for them."""
    body = (CONTENT / page["content"]).read_text(encoding="utf-8")
    if LIBRARY_MARK in body:
        body = body.replace(LIBRARY_MARK, library_html())
    body = re.sub(r"<!-- include ([a-z-]+) -->", lambda m: include(m.group(1)), body)
    body = re.sub(r"<!-- paths ([a-z]+) -->", lambda m: paths_html(m.group(1)), body)
    return tokens(body)


def tokens(text):
    return text.replace("{{version}}", APP_VERSION).replace("{{size}}", APP_SIZE_MB)


def fingerprint(page):
    """The words a reader sees on the page. The title and description are left
    out, so tuning them for search does not pretend the page was rewritten."""
    body = fragment(page)
    shown = [str(page.get(key, "")) for key in ("eyebrow", "h1", "deck")]
    if page.get("head_shot"):
        shown.append(include(page["head_shot"]))
    for key in ("crisis", "close", "facts"):
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
    args += ["--", f"content/{page['content']}"]
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
    "gives away Sojourner, a free Bible study app for Windows, and Mortify, a free app for the "
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
        "keywords": "free Bible software, offline Bible, Bible study app for Windows, Reformed Bible study, Matthew Henry commentary, Westminster Confession",
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
        "keywords": "free Bible software, offline Bible, Bible study app for Windows, Reformed Bible study, Matthew Henry commentary, Westminster Confession",
            "url": f"{SITE_URL}/sojourner.html",
            "applicationCategory": "ReferenceApplication",
            "operatingSystem": "Windows 10, Windows 11",
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
                    "Public domain Puritan and Reformed classics in clean text, with the King James "
                    "and the Berean Standard Bible, free to read in the browser or to download as EPUB."
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
APP_ICONS = {APP_PAGE: BOOK_SVG, MORTIFY_PAGE: MORTIFY_ICON}


def section_of(current):
    """The top page a page belongs under, for marking its place in the menu."""
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
        up = {"objector": "apologetics.html#objector", "believer": "apologetics.html#believer",
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


def build_page(page, dates):
    fragment_path = CONTENT / page["content"]
    if not fragment_path.exists():
        raise SystemExit(f"missing content fragment: {fragment_path}")
    body = fragment(page).strip()
    if page.get("close"):
        body += "\n\n<hr class=\"rule\">\n\n" + tokens(include(page["close"]))

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
                    releases=APP_RELEASES, version=APP_VERSION, size=APP_SIZE_MB,
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
    # The numbers to call come before anything else, the page's own list included.
    if page.get("crisis"):
        parts.append(include("crisis") + "\n\n")
    if page.get("toc"):
        parts.append(toc_html(body))
    parts.append(body)
    parts.append("\n" + pager_html(page) if page.get("parent") else "")
    if page.get("moved"):
        # Where each part of the old long page went, for site.js to follow.
        moved = MOVED[page["moved"]]
        parts.append('\n<script type="application/json" id="moved">'
                     + json.dumps(moved, separators=(",", ":")) + "</script>")
    parts.append("\n</main>\n\n")
    site_js = f'<script src="{asset("assets/js/site.js")}" defer></script>\n'
    footer = render(FOOTER, year=COPYRIGHT_YEAR, scripture_notice=SCRIPTURE_NOTICE,
                    donate_url=DONATE_URL, site_js=asset("assets/js/site.js"))
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
    urls = []
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
        f"{APP_NAME}, a free offline Bible study app for Windows.",
        "",
        f"The site is written by {AUTHOR_NAME}, a layman in the Reformed Presbyterian tradition. "
        "He is not a pastor or an elder, and the site is no substitute for a local church. "
        "Scripture is quoted from the King James Version. The Westminster Standards are quoted "
        "from the text of 1647. The writing may be copied and shared freely under the Creative "
        "Commons Attribution-NonCommercial-NoDerivatives 4.0 license. Please do not sell it, and "
        "please do not change the words and keep the name on it.",
        "",
        f"{APP_NAME} {version} is free Bible study software for Windows 10 and 11, 64-bit, made "
        "by the same writer and given away free. It needs no account, works with the network "
        f"off, and sends no telemetry. The installer is about {size_mb} MB.",
        "",
        f"{MORTIFY_NAME} ({MORTIFY_URL}) is a free web app by the same writer for putting sin to "
        "death by the Spirit. It works in the browser on a phone or a computer, and it needs a "
        "free account made with an email address.",
        "",
        "Anyone in danger or thinking of ending their life can call 911, or call or text 988, in "
        "the United States. Anyone being hurt at home can call the National Domestic Violence "
        "Hotline at 1-800-799-7233, or text START to 88788. If a child is being hurt, call 911. "
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
                    f"under {SITE_URL}/resources/library/. Every one is in the public domain."
                )
        lines.append("")

    lines += [f"## {APP_NAME}, a free Bible study app", ""]
    lines += entry(by_file["sojourner.html"], APP_NAME)
    for page in SOJOURNER_PAGES:
        lines += entry(page)
    lines += [
        f"- [Download {APP_NAME}]({APP_RELEASES}): The Windows installer and the four optional "
        "book shelves, on GitHub",
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


def main():
    dates = page_dates()
    total = 0
    for page in PAGES:
        name, words = build_page(page, dates)
        total += words
        print(f"  {name:<18} {words:>6,} words")
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
