#!/usr/bin/env python3
"""Contractions in authored page titles, descriptions, and introductions.

Only editable Python string literals in the page-metadata sections of build.py
are examined. HTML templates, KJV Scripture, licenses, and app code are skipped.
This is an explicit one-time editorial helper, not a builder dependency.
"""
from __future__ import annotations
import argparse
import ast
import collections
import io
import pathlib
import tokenize

from contractions_audit import changes_in_text

ROOT = pathlib.Path(__file__).resolve().parent
FILE = ROOT / "build.py"
COPY_RANGES = ((70, 109), (160, 1100), (1190, 1430))

def in_copy(line: int) -> bool:
    return any(start <= line <= end for start, end in COPY_RANGES)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    original = FILE.read_text(encoding="utf-8")
    lines = original.splitlines(keepends=True)
    offsets = [0]
    for line in lines:
        offsets.append(offsets[-1] + len(line))
    edits = []
    counter = collections.Counter()
    for token in tokenize.generate_tokens(io.StringIO(original).readline):
        if token.type != tokenize.STRING or not in_copy(token.start[0]):
            continue
        # Triple-quoted pages and Python's own string directives are excluded.
        literal = token.string
        if literal.startswith(("f", "F", "r", "R", "b", "B", "u", "U")) and literal[0] not in ("'", '"'):
            continue
        if literal.startswith(('"""', "'''")):
            continue
        try:
            raw = ast.literal_eval(literal)
        except (SyntaxError, ValueError):
            continue
        if not isinstance(raw, str):
            continue
        revised = changes_in_text(raw, counter)
        if revised == raw:
            continue
        # repr() uses a valid Python string literal even when a new
        # apostrophe appears inside a previously single-quoted title.
        start = offsets[token.start[0]-1] + token.start[1]
        end = offsets[token.end[0]-1] + token.end[1]
        edits.append((start, end, repr(revised), raw, revised))
    edited = original
    for start, end, replacement, _, _ in reversed(edits):
        edited = edited[:start] + replacement + edited[end:]
    # The resulting source must still be syntactically valid Python.
    compile(edited, str(FILE), "exec")
    for _, _, _, before, after in edits[:35]:
        print("  " + before[:105] + "  =>  " + after[:105])
    print(f"Page titles, descriptions and deck text: {sum(counter.values())} contractions in {len(edits)} Python string literals.")
    if args.apply and edited != original:
        FILE.write_text(edited, encoding="utf-8")
    else:
        print("No builder copy was written. Pass --apply to update.")

if __name__ == "__main__":
    main()
