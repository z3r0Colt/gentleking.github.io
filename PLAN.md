# PLAN.md - Gentle King full-site editorial overhaul

Status: IN PROGRESS. Phase 0 is complete and the first editorial batch is underway. See EDITORIAL_AUDIT.md. The site-wide overhaul has not been completed.
Scope: the full public-facing content of the gentleking.github.io repository.
Companion instructions: AGENTS.md and EDITORIAL_STYLE.md.
Source of truth: content/, shared partials, and the copy maintained by build.py and related authored data files.
Goal: clear, natural, practical-first writing, with biblical and confessional depth wherever the subject requires it.

## Objective

Bring every part of Gentle King into a consistent editorial standard: answer the reader's actual question, give useful and realistic help when the page calls for action, and teach Scripture accurately wherever it governs the subject. Do not add religious vocabulary or devotional paragraphs merely to make ordinary guidance sound more spiritual. Do not remove essential Christian teaching simply to make the site shorter.

A reader looking for help with money needs usable guidance about bills, necessities, debt, and assistance. A reader looking up justification needs careful biblical and doctrinal teaching. Each page should do the work it was written to do.

This is a complete execution plan, not just a recommendation for another audit. Work through every phase, make the edits, validate them, and merge the finished work through reviewable pull requests. Stop and document a real blocker only when the required verification or a necessary permission is unavailable.

## Non-negotiable rules

1. Read AGENTS.md, EDITORIAL_STYLE.md, README.md, build.py, and relevant testing scripts before starting a batch.
2. Remain confessionally Reformed Presbyterian, using the original 1647 Westminster Standards. For Westminster text and Scripture proofs use https://thewestminsterstandard.org/. Never silently substitute the American revisions.
3. Preserve KJV Scripture, original confessional text, and authentic historical quotations. Correct an existing quotation only after independent verification; mark excerpts accurately. Preserve the divine "I AM".
4. Maintain particular redemption, effectual calling, justification by faith alone, repentance, perseverance, covenant theology, biblical worship and government, and the immediate free gospel offer to every hearer. Do not assume all readers are regenerate.
5. Use natural contractions and ordinary American English in original prose. No em dashes, repetitive formulae, ornamental contrasts, generic spiritual fillers, or automatic lists of three. Avoid colons and semicolons in prose, in keeping with existing checks.
6. Do not depict Christ or persons of the Godhead. Do not replace a serious theological discussion with a superficial practical checklist.
7. In high-stakes topics, do not let pastoral language replace medical, safety, legal, or emergency care. Verify facts and hotline details with authoritative sources.
8. Protect historical anchors, incoming URLs, shared content, Bible reference links, and build contracts. Change generated files through their sources, not by hand.
9. A scripted pattern scan is only a triage tool. Every reviewed page requires a complete read and page-specific judgment.
10. Do not claim anything has been reviewed, validated, merged, or deployed without evidence for that precise step.

## Definition of full coverage

Discover the live repository inventory at the beginning of the project. The repository contained 118 HTML fragments under content/ when this plan was written, but this number is only a baseline. Include newly added, hidden, or unlinked pages. Enumerate all entries in build.py's page registry, the content/ directory, and public-facing authored copy outside it. Cross-check for omissions.

The audit must cover these groups:

- Entry and utility pages: homepage, Start Here, Find Help, Learn, Guides, About, search, corrections, 404, index and landing pages, navigation, menu labels, notices, captions, and footer.
- Comfort: the main landing page and ALL twelve linked articles, including Safety, Depression, Illness, Suicide Loss, Child Loss, Marriage, Grief, Widowhood, Loneliness, Prodigal Children, Loss of Work or Home, and uncertainty about a deceased person's faith.
- Assurance: its landing page and every individual article, including feeling far from God, fear of death, unwanted thoughts, remaining sin, doubt, and perseverance.
- Fighting Sin: all of struggle.html, individual linked topics, Mortify references, and pastoral or urgent-help text.
- Practical life and ethics guides: money, parenting, marriage, work, forgiveness, prayer, church membership, fasting, worship, media, sex, alcohol, gambling, abortion, IVF, birth control, discipline, government, death, and every remaining guide.
- Scripture, gospel, and doctrine: Gospel, Foundations, Westminster Study, all doctrine subpages, biblical reading and interpretation aids, theological articles, and confessional references.
- Apologetics and discernment: all objections, teacher evaluations, citations, claims about named people, and third-party quotations.
- Tools and resources: Sojourner and its feature, web, installation, and library pages; Mortify's site descriptions; resource directories, reading recommendations, source notes, and download copy.
- Bible Reading Helps: authored explanations, tutorials, study copy, navigation instructions, and its integration with the main Gospel page. Do not rewrite the original biblical corpus or historical references.
- Shared and generated presentation: content/partials/, copy in build.py, titles, decks, page descriptions, search indexing, structured descriptions, Open Graph previews, alt text, help text, visible JavaScript and JSON messages, and llms.txt source text.

Related application repositories are not automatically included. Revise their descriptions on Gentle King, but do not claim to modify the applications.

## Page-by-page assessment

For each page or discrete authored resource, answer and record:

- Who is the intended reader and what exact question brought them here?
- Is the answer visible early enough, or buried beneath doctrine, poetic phrasing, warnings, or repeated preliminaries?
- What should the reader understand, decide, or do? If action is involved, can they carry it out in their actual circumstances?
- What might make the recommended action unsafe, unavailable, misleading, or insufficient?
- Which Scripture genuinely teaches the relevant truth? Does the explanation respect its context? Is a doctrinal distinction or historical qualification missing?
- What text is repeated on this page or neighboring pages without adding value?
- Is any claim about medicine, law, finances, software, a contemporary figure, or a church practice unverified or out of date?
- Are headings, anchors, links, metadata, and shared blocks accurate and helpful?
- Should the page be edited, reorganized, cross-linked, shortened, extended, or left unchanged? Record why.

A page can pass with no text change only after it has been read in full and its status recorded. Do not count a pathname grep as a completed review.

## Page-type editorial requirements

### Practical and pastoral care

Name the problem plainly. If a person is in danger or lacks food, shelter, medicine, or safety, give the immediate response first. Offer concrete options: who to call, which details to gather, what questions to ask, how to ask elders or deacons for help, or how to get qualified care.

Explain what the Bible teaches about sin, suffering, responsibility, hope, and the church where that teaching actually bears on the situation. Do not presume a medical diagnosis, promise a timetable for healing, assign divine punishment to a particular tragedy, or confuse inward distress with proof of unbelief.

Distinguish the roles of pastor, elder, deacon, physician, counselor, civil authority, and emergency service. Do not pressure people to remain in danger or to substitute prayer for appropriate treatment or protection.

### Practical Christian-life and ethics guides

Begin with a clear answer or a direct route to the relevant section. Explain the biblical duty, its rationale, and the actual decisions readers face. Use realistic examples and meaningful exceptions; address competing duties without reducing biblical commands to preferences.

For money, put essentials and debt deadlines ahead of generic financial exhortation. For parenting, deal with children, boundaries, protection, listening, and ages. For marriage, distinguish disagreement, adultery, desertion, abuse, and civil protection. For work, explain lawful employment, wages, unjust treatment, household provision, and illness. For prayer, worship, and church life, give clear instruction without inventing checklists for every circumstance.

### Gospel, doctrine, apologetics, and confessions

Teaching is the reader's purpose. Preserve necessary depth, biblical proofs, technical distinctions, and historical source accuracy. Define unfamiliar terms in natural speech. Address objections fairly and distinguish text, interpretation, inference, and evidence.

Never mechanically enforce a practical-steps quota on doctrine. Explain implications for faith and life when the passage supports them. Keep the free gospel invitation unmistakable.

### Software and resources

Tell the visitor what the tool does, how to get and use it, what it costs, what platforms it supports, privacy and connectivity requirements, limitations, and how to report problems. Check claims against the relevant implementation, release, or documentation. Do not invent features, prices, compatibility, or promotional statistics. Keep technical help technical.

## Work sequence and completion gates

Use these as reviewable pull-request batches, adjusting boundaries when a shared component or dependency makes a different grouping safer. Do not let completed earlier edits exempt a page from a fresh full review.

### Phase 0. Repository inventory and baseline
- [x] Read the repository instructions and inspect its build, page registry, content sources, and published output.
- [x] Enumerate all pages and separately authored public-facing copy.
- [x] Establish an EDITORIAL_AUDIT.md register with one row per item, category, reader question, priority, change status, review status, verification, PR reference, and open concerns.
- [x] Record all existing shared-copy dependencies, historical anchor mappings, and high-stakes pages.
- [x] Establish baseline checks and known failures without masking them.

### Phase 1. Entry points, site-wide navigation, and common copy
- [ ] Homepage, landing pages, Start Here, Find Help, Learn, search, About, and corrections.
- [ ] Header, menus, breadcrumbs, page metadata, notice text, footer, common warnings, links, labels, and generated descriptions.
- [ ] Confirm that visitors can reach the most useful answer without exploring an overwhelming directory.

### Phase 2. Comfort and crisis resources
- [ ] Read and individually revise the Comfort landing page and each of its twelve child pages.
- [ ] Review shared crisis and closing partials for redundant text or misleading claims.
- [ ] Verify urgent numbers, safety wording, trauma and loss counsel, role boundaries, and medical or legal claims.
- [ ] Retain a genuinely usable route to immediate assistance and to further pastoral support.

### Phase 3. Assurance and Fighting Sin
- [ ] Review all Assurance articles and related links.
- [ ] Review the entire Fighting Sin guide and its linked cases.
- [ ] Preserve real biblical teaching about sin and repentance without fueling obsessive self-examination or claiming every intrusive thought is sin.
- [ ] Ensure practical help comes before unnecessary devotional buildup when the reader is unsafe or overwhelmed.

### Phase 4. Household, work, money, and ethics guides
- [ ] Review all household and real-world guides one at a time.
- [ ] Give each its own practical structure, grounded examples, and relevant qualifications.
- [ ] Correct inaccurate financial, medical, civil, historical, or professional guidance.
- [ ] Test links to overlapping Comfort, Assurance, and Doctrine material.

### Phase 5. Church and devotional practice guides
- [ ] Prayer, family worship, Lord's Day, public worship, hearing sermons, sacraments, church membership and joining, church discipline, and related practice.
- [ ] Explain how a person actually carries out each duty and the role of the local church.
- [ ] Maintain the original Westminster doctrine and Reformed Presbyterian convictions, including the regulative principle and exclusive psalmody.

### Phase 6. Gospel, foundations, biblical learning, and doctrine
- [ ] Preserve the complete gospel and its free offer.
- [ ] Read every Foundations lesson and doctrine page in full.
- [ ] Review catechetical and confessional references against the original 1647 source.
- [ ] Resolve duplicated explanations, weak context, inconsistent terminology, and broken proof links.
- [ ] Maintain Gospel / Bible Reading Helps shared-text and integrity contracts.

### Phase 7. Apologetics, teachers, and discernment
- [ ] Review every objection and response.
- [ ] Review teacher reports for attribution, documented quotations, fairness, and sourcing.
- [ ] Distinguish direct evidence from speculation and remove unsupported claims.

### Phase 8. Software, libraries, and resources
- [ ] Review Sojourner, Mortify, and Bible Reading Helps copy hosted in this repository.
- [ ] Check downloads, supported devices, privacy and offline claims, installation instructions, accessibility and limitations.
- [ ] Review resource lists, book and source descriptions, hidden/unlisted content, and other public files.
- [ ] Do not change app feature claims without project evidence.

### Phase 9. Final cross-site review and publication
- [ ] Re-read related pages side by side for contradictions, repetition, and inconsistent wording.
- [ ] Confirm every inventory entry has a defensible reviewed status and disposition.
- [ ] Validate every build contract, generated description, cross-link, and old anchor.
- [ ] Run technical and rendered checks at desktop, tablet, and phone widths.
- [ ] Confirm all planned changes are merged and the latest generated site has been deployed successfully.
- [ ] Publish a final audit summary including changes, open issues, validation evidence, and coverage counts.

## Shared-content and source rules

The content/ files are the primary authored HTML sources. Root-level pages are generated by build.py and served by GitHub Pages from main. Update templates and authored metadata in build.py, not only the generated HTML. Review content/partials/ before revising page-specific wording. Keep the redirects and old deep links defined by build.py and associated scripts.

The main Gospel and Bible Reading Helps share teaching data; changing one source may require synchronized changes and integrity updates in biblehelps/assets/content.json and its related checks. Do not break the reader's Bible reference URL contract, KJV source corpus, or original proof links.

Do not manually edit third-party historical works, quoted books, or original Standards to satisfy readability criteria. Edit the site's explanations instead.

## Safety and fact-checking gate

Pay special attention to suicide and self-harm, domestic violence, abuse of children, pregnancy loss, mental illness, addiction, sexual abuse, medical decisions, hospice and end-of-life care, eviction, debt, and bankruptcy.

Verify hotline capabilities and phone numbers on providers' current authoritative pages. Treat eligibility, legal reporting duties, medical advice, treatment outcomes, and jurisdictional rules as specific claims needing evidence. Distinguish imminent danger from non-emergency needs. Do not make confident pronouncements about a particular deceased person's salvation, causes of death, God's undisclosed intentions, or a child's election.

Where facts cannot be checked, make a precise note in EDITORIAL_AUDIT.md and avoid guessing. Scripture may govern moral principles without providing medical or legal determinations.

## Technical validation per batch

Required commands, from the repository root:

    python3 build.py
    python3 check.py
    python3 check_biblehelps.py
    python3 audit_site.py
    python3 check_foundations.py
    python3 contractions_audit.py
    node --check biblehelps/assets/companion.js
    node --check assets/js/corrections.js

Use verify_quoted_text.py where appropriate, comparing against the known pre-edit revision. Also use any relevant browser smoke tests, including browser_smoke.py and the on-demand Browser smoke test workflow, when browser tooling is available. Check that quote text and the 1647 standards have not changed accidentally. Make sure page titles, section IDs, references, links, search results, and mobile layouts work. Review generated pages after building, including long and difficult pages; automated green checks are not a substitute for reading.

If a check fails, investigate and correct the root cause. Do not remove checks or silently suppress warnings to get a passing result. Document environmental restrictions honestly.

## Pull requests, merges, and deployment

- Start each batch from current main, or deliberately reconcile shared edits.
- Keep branches coherent, descriptive, and limited enough to review.
- Include an explanation of page categories covered, factual verification, proof checks, risks, and testing in the PR.
- Update the audit for every page that was truly reviewed, including those needing no edit.
- Merge only when applicable checks pass. Do not overwrite unrelated changes or force-push.
- On merge, confirm the GitHub workflow rebuilds generated root-level HTML on main and commits it as designed.
- Confirm the actual final GitHub Pages deployment for the generated commit. A merged PR alone does not prove the public content is updated.
- Report unfinished issues accurately rather than marking the project complete.

## Acceptance criteria

The full editorial project is done only when every discovered content page and meaningful public-facing authored string has been reviewed in full; issues have been corrected or explicitly justified; KJV and historical quotations remain accurate; confessional language and theological claims remain faithful to the original Westminster text; practical information is useful and safe; navigation and metadata are consistent; all required validation succeeds; all changes are merged; generated pages are current; the latest GitHub Pages deployment succeeds; and EDITORIAL_AUDIT.md records a truthful full-coverage summary.

Do not use a simple ratio of practical words to theological words. Relevance and fidelity determine how much biblical exposition a particular subject needs.
