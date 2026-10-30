# Gentle King editorial standard

This ministry teaches from Scripture in the tradition of the original 1647
Westminster Standards. It should sound like a careful layman speaking to another
person, not a generated study-guide template.

## The voice

- State the biblical claim plainly, show where Scripture teaches it, and explain
  what it asks of the reader. Prefer concrete verbs and examples.
- Use natural contractions in original prose. Preserve exact KJV quotations,
  historical quotations, and the wording of the Westminster Standards.
- Let sentences vary in length. Avoid lists of identical three-part sentences,
  artificial oppositions, and repeated one-sentence paragraphs.
- Do not stack "It isn't X. It's Y" or "not merely X, but Y" sentences. Contrast
  matters when the passage itself makes a distinction. Otherwise state the
  positive truth directly.
- Remove introductions that announce what the article will say, transitions
  that restate the heading, and conclusions that repeat earlier paragraphs.
- Don't use vague pastoral fillers such as "you don't need fine words" in
  article after article. Give specific counsel for the reader's actual trouble.
- Avoid a generic weekly checklist when the subject needs different pastoral
  guidance. A practical step should follow from the exposition.
- Use plain words without flattening the doctrine. Define any term an ordinary
  reader might not know.

## Practical-first writing across the whole website

Write for what the reader came to learn or do. A Christian website should teach
Christian truth faithfully, but religious language must serve the question at
hand. Do not add devotional sentences to a paragraph merely to make it sound
spiritual. Neither should practical advice stand apart from biblical duties,
promises, and moral limits when those truly govern the subject.

Choose the approach by page type:

- **Comfort, assurance, safety, and pastoral help:** Name the problem in ordinary
  words. Lead with urgent safety or material needs when they exist. Tell the
  reader who to contact and what to do, with realistic exceptions for illness,
  disability, abuse, and lack of a faithful local church. Give Scripture and
  Christian hope where they actually bear on the reader's trouble. Don't
  mistake medical, financial, or relational problems for proof of spiritual
  failure. Don't imply that prayer replaces treatment, protection, or work.
  Don't prepend a generic crisis banner to every page. Keep full emergency
  contacts on the Safety page and brief, accessible guidance only on pages
  where the reader is at risk. Suicide bereavement articles should begin with
  the survivor's sorrow rather than the sixth commandment or speculation about
  the deceased person's salvation. A person thinking about ending their own
  life needs direct help staying safe, a way to ask someone to stay with them,
  patient attention to their distress, and biblical comfort in its proper
  place. Do not turn a page for someone in crisis into a lecture on the
  sixth commandment or a test of whether they are truly saved.
- **Practical guides on money, parenting, marriage, work, prayer, worship, and
  church life:** Answer the practical question at the start or give a clear
  route to the applicable section. Explain the biblical rule and its reason,
  then show how to apply it in a recognizable situation. Use realistic
  examples, not repeated generic checklists. Explain what to do when the
  ordinary approach is unsafe, unavailable, or insufficient. A duty such as
  giving or attending worship must be explained alongside other real duties
  such as caring for dependents and preserving life. In marriage and sexuality
  guides, teach the whole counsel of Scripture, including the reciprocal duty
  of marital intimacy and the prohibition against defrauding a spouse in
  1 Corinthians 7:3-5. Never replace that duty with only an abuse warning,
  but never present it as permission for coercion either. Distinguish persistent
  unilateral neglect from genuine inability, illness and temporary difficulty.
- **Doctrine, gospel, confessions, and apologetics:** The main subject is
  theological, so substantial biblical teaching belongs there. Explain it
  plainly, with definitions and examples. Don't manufacture practical steps
  for every doctrine or replace precise doctrine with motivational language.
  Show the consequences for belief and life where the passage supports them.
- **Software, download, and resource pages:** Tell readers what the tool
  actually does, what it costs, how to use it, what it cannot do, and where
  to get help. Ministry context may be mentioned, but avoid adding unrelated
  devotional language to feature descriptions or technical instructions.

For every practical page, ask before publishing: What question brought the
reader here? What is the direct answer? What should they do first? Who can help
if that step doesn't work? Which Scripture actually governs the advice?
Would this paragraph still be here if it didn't have religious vocabulary?
If it adds no information or necessary biblical grounding, cut it.

When quoting or paraphrasing Scripture, keep the meaning of its context.
Do not force a Bible story to serve as a modern diagnosis, financial formula,
or promise the passage doesn't make. Use clear speech rather than forcing a
verse or gospel summary into every heading and closing paragraph.

## Contractions and natural speech

Write the way an ordinary believer would speak. Use "don't," "can't,"
"doesn't," "I'm," "you're," and "it's" where the sentence calls for them.
Contractions are not an excuse for clipped or artificial writing.

Never contract an auxiliary stranded at the end of a clause. Write
"Who I Am," "where they are," and "what it is," not "Who I'm,"
"where they're," or "what it's." In American English, "you have a Bible"
is usually more natural than "you've a Bible." Preserve emphasis when
the uncontracted form carries real meaning.

Keep every KJV quotation, historical quotation, and original Westminster
passage exactly as given. Don't rewrite the divine "I AM." The
`contractions_audit.py` and `builder_copy_contractions.py` scripts are
tools for examining possible edits. They do not replace reading the
sentences aloud. For a sensitive revision, use `verify_quoted_text.py`
against a known original branch.

## Precision before force

- "May," "might," "sometimes," and "we don't know" belong where Scripture
  leaves a question open. Don't remove a necessary qualification to sound
  confident.
- Do not promise that grief, depression, conflict, or spiritual darkness will
  disappear on a schedule. Do not presume that every reader is regenerate.
- Distinguish God's revealed promises from theological inferences and from
  historical claims that need sources.
- Keep the offer of the gospel immediate and free, alongside the original
  Confession's particular redemption and effectual calling.
- Maintain the original 1647 Westminster Confession's teaching, especially
  chapters 20, 23, and 31. Do not substitute the American revisions.
- No portraits or other attempted depictions of Christ or persons of the Godhead.

## Revising an article

1. Read the article from beginning to end, including its heading and neighboring
   articles. Find its primary passage and the actual reader's question.
2. Delete paragraphs that merely restate earlier counsel.
3. Replace formulaic comparisons with clear positive explanations where that
   preserves meaning.
4. Check each Scripture reference in context and every confessional attribution
   against the original source at https://thewestminsterstandard.org/.
5. Leave Scripture quotations, legal and medical cautions, historical titles,
   and cited words untouched unless independently verified.
6. Read the prose aloud. Rewrite any passage that sounds like an outline being
   performed rather than a person speaking.
7. Rebuild the site and run all checks. Inspect the rendered result.

The editorial scan is only a prompt for human review. It cannot determine
whether a caveat is doctrinally essential or a sentence sounds human.
