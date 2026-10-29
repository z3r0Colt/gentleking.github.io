# Sitewide content, doctrine, and reference review

This document records the changes made to Gentle King in the 1647 standards
revision. The code checks are reproducible. Editorial judgments still require
the author to read the passages and compare them with Scripture.

## Additional work completed in October 2026

- Added six substantial doctrine guides on baptism, justification, Christ the
  Mediator, the fall and original sin, Christian liberty, and lawful vows.
- Added a sixteen-lesson Foundations pathway and all thirty-three chapters
  of the original Confession in a navigable study index.
- Connected related teaching from the homepage, doctrine, family worship,
  church-finding, and Lord's Supper articles.
- Added two church-membership guides. Current RPCNA procedures are clearly
  distinguished from the historical 1647 Westminster Confession.
- Changed WCF references to link to exact original paragraphs and WLC/WSC
  references to their questions in Bible Reading Helps, which also links to
  the original source at thewestminsterstandard.org.
- Added per-article correction links, a source-verification policy, and a
  report form that prepares a local email without storing submissions.
- Added historical source links to key apologetics and theology articles.
- Added permanent regression checks for the new pages and a reusable Chromium
  browser smoke test. A GitHub Actions run of the browser test passed at
  375px, 768px and 1280px on eleven representative routes.

### Remaining verification limits

The browser run emulates viewport widths and checks basic behavior. It does
not emulate every aspect of touch input, platform accessibility APIs, screen
reader output, or real mobile browsers. External links were selected from
verified public sources but a live crawl of every external destination is
outside this test. Historical claims in other older articles deserve ongoing
primary-source review. Passing CI cannot certify the correctness of every
theological sentence in the full site.

## Nonnegotiable standards

- The original **1647 Westminster Confession of Faith**, Larger Catechism,
  and Shorter Catechism, without silent substitution of American revisions.
- The Westminster wording and Scripture proofs are sourced from
  https://thewestminsterstandard.org/.
- Scripture, not the Confession, is the supreme and infallible rule.
- The writing must remain intelligible to ordinary readers, with natural
  contractions, careful application, and no artificial sermon formulas.
- No images purporting to depict any person of the Trinity.

## Implemented in this revision

1. **Sitewide Bible and confession references.** Generated pages link
   recognized Bible book/chapter/verse references into the KJV reader in
   Bible Reading Helps, and WCF/WLC/WSC citations to the approved original
   source. The build-time linker preserves the authored HTML, doesn't nest
   anchors, and checks that verses are in range. The historical Resources
   library catalogue is excluded because its titles and bibliography must
   remain verbatim.
2. **Direct passage reading.** Bible Reading Helps supports a
   `?ref=John%203%3A16` URL. The passage opens in the existing KJV reader
   without creating an account or sending user data to a third-party service.
3. **Doctrine gaps.** Five complete subjects were added to the doctrine
   collection, covering providence, union with Christ, adoption,
   sanctification, and church government. Their articles distinguish the
   wording of the original Confession from theological explanation.
4. **Apologetics precision.** The God/evidence article no longer presents
   disputed philosophical inferences as uncontested formal proofs. It still
   teaches the biblical witness of creation and the necessity of the Spirit.
   Evangelism counsel now engages actual questions rather than claiming
   to know every questioner's hidden motives.
5. **Editorial consistency.** Common repeated weekly-action headings in
   practical guides were replaced with relevant subject headings, preserving
   the guidance. The homepage doctrine card now goes directly to the doctrine
   collection. The About page clarifies independent lay authorship.
6. **Regression protection.** `audit_site.py` runs in the site's normal
   GitHub Actions check alongside the builder, HTML/link checker,
   Bible Reading Helps source integrity test, and JavaScript syntax check.

## What validation proves

`python3 build.py` produces the static public pages from their source files.
`python3 check.py` checks internal links, anchors, HTML structure,
metadata, and prose punctuation. `python3 check_biblehelps.py` checks Bible
Reading Helps' contents, KJV data, integrity, and exact shared gospel wording.
`python3 audit_site.py` validates generated citation destinations and
checks that the five new doctrine articles are built and linked from the
doctrine library. The companion JavaScript also passes Node's syntax check.

## Limits and ongoing checks

- Automatic linking recognizes **explicit full references** and skips
  ambiguous shorthand such as a bare verse number without a book name.
  Such references should be expanded manually while editing the article.
- Internal link validity is checked. Third-party websites can change and
  should be rechecked periodically.
- A passing build cannot certify that every theological interpretation,
  historical citation, or disputed application is correct. Compare claims
  with Scripture and, for confessional wording, the official original text.
- Browser-level mobile layout, assistive-technology behavior, and dialogue
  interaction still need manual device testing. JavaScript syntax checking
  alone is not a substitute for that.
- A full article-by-article human editorial reading of the complete site remains a distinct editorial task.
  This release improves the whole site's references and build integrity,
  and makes the specific substantive content changes documented above.

Do not disable checks merely to clear a red GitHub status. Investigate the
source mismatch and regenerate the affected pages.
