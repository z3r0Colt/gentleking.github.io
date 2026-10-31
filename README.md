# Gentle King

The ministry site for Gentle King. The gospel of Jesus Christ, Scripture for hard
hours, help in the fight against sin, Reformed doctrine, and answers to objections.
It also gives away two tools, Sojourner, a Bible study app for the browser, Windows, and Linux, and
Mortify, an app for the fight against sin.

It is a plain static site. No framework, no npm, no dependencies. GitHub Pages
serves the `.html` files at the top of this repository exactly as they are.

---

## Foundations and Westminster study

The ministry now includes `foundations.html`, a sixteen-lesson pathway from the
gospel to the life of the church, and `westminster-study.html`, an index of all
thirty-three chapters of the original Confession. Each chapter opens the
specific historical text and Scripture proofs within Bible Reading Helps.

Six doctrine guides cover baptism, the person and work of Christ, justification,
the fall and original sin, Christian liberty, and lawful oaths and vows.
Two practical guides explain church membership and visiting an RP congregation.
They distinguish the original 1647 Standards from current denominational rules.

`reference_links.py` now opens exact WCF paragraphs and Catechism answers in
the local original-text reader. The same reader has links to
thewestminsterstandard.org, the sole original Westminster text source used here.
`check_foundations.py` guards these links and the learning pages in normal CI.

Each authored article contains a link to `corrections.html` with its page address.
The form opens the user's email app and transmits nothing to the site itself.
The sources and corrections policy explains the verification process.

`browser_smoke.py` uses Playwright and Chromium to test representative pages
at phone, tablet, and desktop viewport widths, the correction form, and
confessional paragraph navigation. Run the on-demand GitHub Actions
`Browser smoke test` workflow from the Actions tab. It was checked in CI
for this release, but it is **not** a substitute for physical-device testing,
manual screen-reader testing, or a full WCAG audit.

## Editing the site

There is one small build script so that the header, the footer, and all the page
metadata live in a single place instead of being copied into every page.

**To change the words on a page**, edit the matching file in `content/`, then run:

```
python3 build.py
```

That rewrites the `.html` files at the top of the repo. Commit those files and push.
GitHub Pages never runs the script, it only serves what you commit.

**To change the header, the footer, the navigation, the page titles, or the social
preview text**, edit `build.py` and run it again.

**To change how the site looks**, edit `assets/css/site.css`. The colors, the fonts,
and the spacing are all set as variables near the top of that file, so a small edit
there changes the whole site at once.

### Source references and confessional texts

The site uses the **original 1647 Westminster Confession and Catechisms**. Its
source for all Westminster wording and Scripture proofs is
[The Westminster Standard](https://thewestminsterstandard.org/).
Do not silently substitute the American Presbyterian revision of 1788, later
denominational amendments, or quotations taken from other editions.

When an article is built, `reference_links.py` turns recognizable full Bible
references into KJV reading links to `bible.html?ref=...`. A normal click opens
the passage in a dialog on the current article. The full reader uses Gentle
King’s shared layout, and its text and metadata live under `assets/kjv/`.
It does not load Bible Reading Helps. Modified clicks still open the full reader.
It links WCF, WLC, and WSC citations to the relevant original document on
The Westminster Standard. It skips any existing link, code, or interactive
control. The historical book catalogue on Resources is excluded to preserve
its verbatim titles and bibliographies. Authoring files under `content/`
remain plain HTML without machine-generated source-link markup.

The companion supports a one-time `?ref=John%203%3A16` reader link, opening
the requested KJV passage. Keep this contract stable when changing its UI.
The CI checks include `python3 audit_site.py`, which validates the generated
reference links and confirms that doctrine pages are reachable.

**Before you push**, run the checker. It catches broken HTML, links pointing at
files that are not there, duplicate section ids, and stray punctuation.

```
python3 check.py
```

Phone links must be written with digits only, like `tel:988`, or the checker will
stop you. A number with dashes in it may not dial.

Urgent-help phone numbers belong primarily on `content/comfort-safety.html`, with
short, appropriate references in individual articles and `build.py` for llms.txt.
They are not injected as a generic banner into the Comfort articles. The Option
Line number for pregnant mothers is in `content/guide-abortion.html`. Verify
service details on the providers' own sites annually and update the note at the
top of `content/comfort.html` when you do.

---

## How the pages fit together

Comfort, Apologetics, and Guides are each a short landing page with a page of its
own for every sorrow, every question, and every guide under it. Sojourner has a short main page and three
pages under it for the full feature account, the library, and installing.

- **A page under another** names its parent with `parent` in `PAGES`. It then gets
  a breadcrumb above its heading, a link back at its foot, and its parent is marked
  in the menu while you are on it.
- **A series** is a set of pages meant to be read in order, such as the answers to
  objections. Each page in one gets Previous and Next at its foot, and the list on
  the parent page is written from the series, so it can never disagree with it.
- **Shared blocks** live in `content/partials/`. A page asks for one at its foot with
  `close` in `PAGES`, or anywhere in its words with `<!-- include name -->`. The
  church and gospel closing block is intentionally shared across Comfort
  articles. A grieving reader may land directly on one page. The full emergency
  contacts live on the dedicated Safety page, with concise help linked in
  articles where it is needed. No generic danger banner is inserted at the top.
- **Old links still work.** Comfort and Apologetics were once one long page each.
  `MOVED` in `build.py` lists where each part went, and a link such as
  `comfort.html#grief` is sent on to `comfort-grief.html`.

To add a sorrow or a question, write its file in `content/`, add it to the right
list in `build.py` (`COMFORT_PAGES`, `OBJECTOR_PAGES`, `BELIEVER_PAGES`, or
`GUIDE_PAGES` with its series, `life` or `discern`), add it
to the list on `content/comfort.html` if it is a sorrow, and rebuild.

---

## What is where

```
build.py                the builder. Wraps content in the shell.
check.py                looks over the built pages for mistakes.
.github/workflows/      rebuilds and checks the site on every push to main.
content/                the words. One file per page. Edit these.
content/partials/       blocks shared by several pages.
assets/css/site.css     the whole design. Colors and fonts at the top.
assets/js/site.js       theme switch, menus, on-this-page links, old links.
assets/img/             the crown mark, the favicons, the social card.
brand/                  the logo files to use elsewhere, light and dark. See its README.
resources/              files to keep and share, such as PDFs and handouts. Public.
index.html …            generated. Do not hand edit, they get overwritten.
404.html                hand written and self contained. Edit directly.
sitemap.xml  robots.txt generated by build.py.
llms.txt                generated by build.py. A plain map of the site for AI tools.
content/dates.json      when each page last really changed. build.py keeps it.
f64863….txt             the IndexNow key. Leave it be. See "Being found" below.
favicon.ico             a copy of the tab icon, for tools that only look at the root.
                        build.py copies it from assets/img/ each time.
.nojekyll               tells GitHub Pages to serve the files as they are.
```

---

## Releasing a new version of Sojourner

The download button points at the releases page, not at a specific file, so it
keeps working when you post a new build. After a release, change `APP_VERSION`,
`APP_SIZE_MB`, `APP_SIZE_DEB_MB`, and `APP_SIZE_APPIMAGE_MB` near the top of
`build.py`, using the sizes the release notes give for the Windows installer, the
Linux .deb, and the AppImage. Those four lines fill in every place the pages show
the version or a size, written as `{{version}}`, `{{size}}`, `{{size_deb}}`, and
`{{size_appimage}}` in `content/`, along with the structured data and llms.txt. If the release brings
something new, say so in the Updating part of `content/sojourner-install.html`.

If the release changes which systems Sojourner runs on, look over the System line on
`content/sojourner.html` and the Installing It part of `content/sojourner-install.html`.

If the release adds, removes, or renames translations, shelves, or reference works,
the counts and names in `content/sojourner.html`, `content/sojourner-library.html`,
the description for `sojourner.html` in `build.py`, and the one paragraph about
Sojourner on the home page want updating too. If it adds or drops a whole kind of
feature, look over `APP_FEATURES` in `build.py`, the six features on
`content/sojourner.html`, and `content/sojourner-features.html`.

Then run `python3 build.py`, check it, commit and push.

The screenshots live in `assets/img/` as `sojourner-*.webp`, each with a 1000px copy
beside it for the page itself. Each one has alt text and a caption in the Sojourner
pages in `content/` that describe what it shows. The picture at the top of the main
page is in `content/partials/sojourner-shot.html`. When the app looks meaningfully
different, replace both copies and check that the alt text and the caption still
match the picture.

---

## How it goes live

GitHub Pages serves this repository straight from the `main` branch, so the
`.html` files sitting at the top of the repo are exactly what readers get.
Pushing to `main` puts them live within a minute.

That means one habit matters. **After you change anything in `content/`, run
`python3 build.py` and commit the pages it writes.** If you skip it, the repo
and the live site will disagree, and readers will still see the old words.

A workflow guards that for you. On every push it rebuilds from `content/` and
fails if the committed pages do not match, so a forgotten build shows up as a
red mark in the **Actions** tab instead of going unnoticed. It runs `check.py`
in the same job.

If you ever want the workflow to do the publishing itself instead, change
**Settings**, then **Pages**, then **Source** to **GitHub Actions**, and say so.
The setup for that is a small change to the workflow file.

The site is served at **gentleking.org**. `build.py` writes the `CNAME` file from
`SITE_URL`, so those two can never drift apart. To move the site to a different
domain, change `SITE_URL` near the top of `build.py` and rebuild. Every link inside
the site is relative, so nothing else has to change.

---

## Being found

Search engines and AI tools read the site from the same pages readers see.
`build.py` adds what they look for on top of that.

- **Titles and descriptions.** Each page in `PAGES` has a `full_title` and a
  `description`, written in the words people actually search with. They show in
  search results and when a link is shared. `check.py` fails a description over
  160 characters, since search results cut it off there.
- **Structured data.** Every page carries a small JSON-LD block that tells
  machines who publishes the site, who writes it, what the page is, and on the
  Sojourner page what the app is. It says nothing the pages do not say. Never add
  ratings or reviews to it. `check.py` fails the build if any appear.
- **Dates.** `content/dates.json` holds when each page was first published and
  last really changed. A page's date moves only when its words or its heading
  change, not its title. The sitemap and the structured data read it.
- **robots.txt** lets every search engine and AI tool in by name, and keeps them
  out of the files that build the site. To shut one of them out, take its name
  off `WELCOME_CRAWLERS` in `build.py` and give it a group of its own.
- **llms.txt** is a plain map of the site for AI tools, written from the pages.
- **IndexNow.** After a push to `main` changes a page, a workflow waits until
  the page is live and then tells Bing and the engines that share with it. The
  key file at the top of the repo proves the ping came from here.

Google does not take IndexNow pings. It finds changes through the sitemap once
the site is added in Google Search Console.

---

## A note on the words

Scripture quotations are from the Authorized Version, the King James Bible of
1611, which is in the public domain. The site quotes it rather than a modern
translation so that nothing here is under anyone's copyright. The footer points
readers who find the older English hard to the ESV or the NASB, but the site
itself quotes neither. That is also why there is no side-by-side modern text.
Printing one would put the pages under a publisher's terms.

Everything written here may be copied, printed, and shared freely. Please do not
sell it and please do not alter it.


## Finding teaching and guides

The main menu begins with `start-here.html`, `help.html`, and `learn.html`.
Assurance has its own entrance at `assurance.html`. Doctrine is an overview
linking to individual subjects, with old section addresses redirected by `MOVED`.

`build.py` generates `assets/search-index.json` from public page content and
section anchors. `assets/js/search.js` searches that index in the browser, with
no external service. Hidden pages are excluded. `check.py` validates its links.

The Guides directory keeps every guide in the HTML. `assets/js/guides.js` adds
topic filters. All guides appear in six native collapsible topic groups, open by
default, with no featured subset or pagination. Search opens matching groups and
restores the reader's previous open or closed choices when cleared. Set a guide's
topic in `guide_topic()` and group order in `GUIDE_TOPIC_GROUPS`.
Reading estimates use 200 words per minute. Articles include an overview and
related reading. Long confessional quotations can be expanded in place.

On smaller screens, the contents list becomes a sticky expandable control.
The full list and every guide remain readable without JavaScript.


## Bible Reading Helps

The interactive companion lives at `/biblehelps/`. GitHub Pages redirects
`/biblehelps` to that directory. It keeps its own layout, with a return link to
Gentle King. Find it under Tools, Learn the Faith, and the Bible-reading guide.

`biblehelps/index.html` is its shell. `biblehelps/assets/companion.css` and
`companion.js` provide the interface. `content.json` preserves the supplied
teaching. The 66 files under `assets/bible/` preserve the supplied KJV text.
Only the Bible book being opened is downloaded. Verse counts in the shell
allow reference links to be checked before that book loads.

The companion saves reading progress and settings in browser storage, using
the original `brh-v2` key. It does not require an account. No service worker
or full offline download is installed. Keep cache-version strings current
when changing its CSS, JavaScript, or teaching data.


The main Gospel page shares the companion's core gospel paragraphs and Scripture quotations
verbatim, with additional Scripture quotations and explanations. The companion's
closing note about the reading tool is omitted. `check_biblehelps.py` checks this
agreement so future edits cannot silently give the two pages different wording.
When revising a shared paragraph, update both copies and the content integrity
manifest for the companion data.

The short Gospel summary is shared through `metadata.gospelSummary` in the
companion content data. Both presentations put an immediate call to Christ near
the beginning, and quote Romans 3:25 and 1 John 4:10 on propitiation.
