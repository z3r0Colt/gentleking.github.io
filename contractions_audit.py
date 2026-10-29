#!/usr/bin/env python3
"""Audit or apply natural contractions to original ministry prose.

Only text inside authored paragraphs and subsection headings is eligible.
Bible quotations, Westminster quotations, links, bibliographies and markup
are preserved. This is an editorial aid, not a blanket replacement of 'not'.
Run with --apply to change content/*.html, otherwise only report.
"""
from __future__ import annotations

import argparse
import collections
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent
CONTENT = ROOT / "content"
PROTECTED = frozenset(
    ("blockquote", "cite", "q", "a", "code", "pre", "script", "style",
     "textarea", "button", "svg", "figure", "figcaption", "noscript")
)
EDITABLE = frozenset(("p", "h2", "h3", "h4"))
VOID = frozenset(("br", "hr", "img", "input", "meta", "link", "source", "wbr"))
# Keep the old book catalogue and attributed discernment quotations unchanged.
EXCLUDED = frozenset(("resources.html", "gospel.html"))
RULES = (
    ("cannot", "can't"),
    ("do not", "don't"),
    ("does not", "doesn't"),
    ("did not", "didn't"),
    ("will not", "won't"),
    ("would not", "wouldn't"),
    ("could not", "couldn't"),
    ("should not", "shouldn't"),
    ("must not", "mustn't"),
    ("is not", "isn't"),
    ("are not", "aren't"),
    ("was not", "wasn't"),
    ("were not", "weren't"),
    ("has not", "hasn't"),
    ("have not", "haven't"),
    ("had not", "hadn't"),
    ("you are", "you're"),
    ("we are", "we're"),
    ("they are", "they're"),
    ("there is", "there's"),
    ("that is", "that's"),
    ("it is", "it's"),
    ("you have", "you've"),
    ("we have", "we've"),
    ("they have", "they've"),
    ("you will", "you'll"),
    ("we will", "we'll"),
    ("they will", "they'll"),
    ("I will", "I'll"),
    ("I have", "I've"),
    ("I am", "I'm"),
)
REGEX = re.compile(r"(?i)\b(?:" + "|".join(re.escape(a) for a, _ in RULES) + r")\b")
LOOKUP = {original.lower(): contraction for original, contraction in RULES}
POSITIVE_FORMS = frozenset(
    ("you are", "we are", "they are", "there is", "that is", "it is",
     "you have", "we have", "they have", "you will", "we will",
     "they will", "i will", "i have", "i am")
)
HAVE_PARTICIPLES = frozenset(
    ("been", "had", "done", "seen", "known", "heard", "found",
     "come", "become", "gone", "got", "made", "read", "said",
     "written", "taken", "given", "chosen", "fallen", "grown",
     "lost", "taught", "brought", "thought", "kept", "stood",
     "understood", "held", "met", "built", "put", "left",
     "already", "never", "just", "always", "often", "recently")
)
TOKENS = re.compile(r"(<!--[\s\S]*?-->|<[^>]+>)")
QUOTE = re.compile(r'(&ldquo;.*?&rdquo;|“.*?”|"[^"]*")', re.S)
SCRIPTURE_CITATION = re.compile(
    r"\(\s*(?:(?:[1-3]\s+)?[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})\s+\d{1,3}:\d{1,3}",
)


def changes_in_text(text: str, counter: collections.Counter) -> str:
    # Scriptural extracts embedded within ordinary paragraphs may not use
    # blockquote markup. Never change words inside explicit quotation marks.
    # Be cautious with wording immediately followed by a Bible citation.
    if ("&ldquo;" in text) != ("&rdquo;" in text):
        return text
    if ("“" in text) != ("”" in text):
        return text
    def plain(span: str) -> str:
        def change(match: re.Match) -> str:
            original = match.group(0)
            # Never touch the divine name I AM or all-caps source terminology.
            if original.isupper():
                return original
            after = span[match.end():match.end()+85]
            form = original.lower()
            # English auxiliary contractions need a following complement.
            # "who I am", "where they are", and "what it is" can't be
            # reduced at the end of a clause. Neither can page headings
            # such as "Who I Am".
            if form in POSITIVE_FORMS:
                following = re.match(r"^\s+([A-Za-z][A-Za-z'-]*)", after)
                if not following:
                    return original
                next_word = following.group(1).lower()
                if next_word in ("and", "but", "or", "when", "where",
                                 "whether", "because", "than", "which",
                                 "who", "whom", "whose"):
                    return original
                # In American English "you've a Bible" or "I've to go"
                # is unnatural. Use 'have contractions' only with the
                # auxiliary perfect tense, such as "I've seen".
                if form.endswith(" have") and not (
                    next_word in HAVE_PARTICIPLES
                    or next_word.endswith(("ed", "en"))
                ):
                    return original
            if SCRIPTURE_CITATION.search(after):
                return original
            replacement = LOOKUP[original.lower()]
            if original[0].isupper():
                replacement = replacement[0].upper() + replacement[1:]
            if original == replacement:
                return original
            counter[original.lower()] += 1
            return replacement
        return REGEX.sub(change, span)

    chunks = QUOTE.split(text)
    return "".join(chunk if i % 2 else plain(chunk) for i, chunk in enumerate(chunks))


def revise(source: str, counter: collections.Counter) -> str:
    tags = []
    out = []
    for token in TOKENS.split(source):
        if token.startswith("<!--") and token.endswith("-->"):
            out.append(token)
            continue
        if token.startswith("<") and token.endswith(">"):
            m = re.match(r"<\s*(/?)\s*([\w:-]+)\b", token)
            if m:
                closing, name = m.group(1), m.group(2).lower()
                if closing:
                    if name in tags:
                        idx = len(tags) - 1 - tags[::-1].index(name)
                        del tags[idx:]
                elif not token.rstrip().endswith("/>") and name not in VOID:
                    tags.append(name)
            out.append(token)
        elif any(name in EDITABLE for name in tags) and not any(name in PROTECTED for name in tags):
            out.append(changes_in_text(token, counter))
        else:
            out.append(token)
    return "".join(out)


def self_test() -> None:
    tests = [
        ("<p>Do not wait. You are welcome.</p>",
         "<p>Don't wait. You're welcome.</p>"),
        ("<h2>Who I Am</h2>", "<h2>Who I Am</h2>"),
        ("<p>Leave them where they are.</p>",
         "<p>Leave them where they are.</p>"),
        ("<p>It is what it is.</p>", "<p>It's what it is.</p>"),
        ("<p>You have to tell them.</p>", "<p>You have to tell them.</p>"),
        ("<p>I have a Bible. I have read it.</p>",
         "<p>I have a Bible. I've read it.</p>"),
        ("<h2>I do not know if I am saved</h2>",
         "<h2>I don't know if I'm saved</h2>"),
        ("<blockquote class=\"scripture\"><p>Do not be afraid.</p></blockquote>",
         "<blockquote class=\"scripture\"><p>Do not be afraid.</p></blockquote>"),
        ("<p>&ldquo;Do not go.&rdquo; Do not remain.</p>",
         "<p>&ldquo;Do not go.&rdquo; Don't remain.</p>"),
        ("<p>If I regard iniquity, the Lord will not hear me (Psalm 66:18).</p>",
         "<p>If I regard iniquity, the Lord will not hear me (Psalm 66:18).</p>"),
        ("<p><a href=\"doctrine.html\">Do not change the label</a>. It is helpful.</p>",
         "<p><a href=\"doctrine.html\">Do not change the label</a>. It's helpful.</p>"),
    ]
    for original, desired in tests:
        actual = revise(original, collections.Counter())
        if actual != desired:
            raise AssertionError(f"Unexpected contraction: {actual!r} != {desired!r}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    self_test()
    totals = collections.Counter()
    files = 0
    for path in sorted(CONTENT.glob("*.html")):
        if path.name in EXCLUDED or path.name.startswith("teacher-"):
            continue
        source = path.read_text(encoding="utf-8")
        counts = collections.Counter()
        revised = revise(source, counts)
        if revised != source:
            files += 1
            totals.update(counts)
            if args.apply:
                path.write_text(revised, encoding="utf-8")
            print(f"{path.name}: {sum(counts.values())} contractions", flush=True)
    print(f"TOTAL: {sum(totals.values())} careful contractions across {files} authored fragments.")
    for phrase, count in totals.most_common():
        print(f"  {phrase}: {count}")
    if not args.apply:
        print("Preview only. Use --apply to write changes.")
    else:
        print("Quoted text and the historical Resources catalogue were excluded.")


if __name__ == "__main__":
    main()
