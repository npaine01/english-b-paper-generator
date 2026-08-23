#!/usr/bin/env python3
"""Question breakdown from a compiled paper's .ans file.

Shows which question types each text uses and how many marks each carries, so a
paper can be checked against the shape real papers take. Reads the answer file
the package writes at compile time; no LaTeX involved.

    python3 tools/breakdown.py reading-question-booklet.ans
    make breakdown
"""
import re
import sys
from collections import Counter

# Names as the IB prints them, keyed by the token \ibanswerrow records.
NAMES = {
    "mcq":      "multiple choice",
    "true":     "identify true statements",
    "match":    "matching",
    "headings": "match headings to paragraphs",
    "vocab":    "match vocabulary",
    "halves":   "match sentence halves",
    "people":   "match statements to people",
    "matchq":   "match questions to gaps",
    "gapsummary": "match words into a summary",
    "gapfill":  "gap fill",
    "findword": "find the word or phrase",
    "tf":       "true/false + justification",
    "complete": "complete the sentence",
    "refer":    "identify referents",
    "short":    "short answer",
    "short2":   "short answer, two answers",
    "source":   "matching to sources (tick table)",
    "task":     "writing task",
}

# What the corpus says a paper should look like. See METHOD.md and the analysis.
TARGETS = {"reading": (40, 3), "listening": (25, 3), "paper1": (30, None)}


def parse(path):
    """-> (sections, total). sections is [(title, [(qnum, marks, type)])]."""
    sections, cur, total = [], None, None
    for line in open(path, encoding="utf-8"):
        if m := re.match(r"\\ibanswersection\{(.*)\}\s*$", line):
            cur = (clean(m.group(1)), [])
            sections.append(cur)
        elif m := re.match(r"\\ibanswerrow\{(\d+)\}\{.*\}\{(\d+)\}\{(\w+)\}\s*$", line):
            if cur is None:                       # a paper with no text headings
                cur = ("(no section)", [])
                sections.append(cur)
            cur[1].append((int(m.group(1)), int(m.group(2)), m.group(3)))
        elif m := re.match(r"\\ibanswertotal\{(\d+)\}", line):
            total = int(m.group(1))
    return sections, total


def clean(s):
    s = re.sub(r"\\textit\s*\{([^}]*)\}", r"\1", s)
    s = re.sub(r"\\[a-zA-Z]+\s*", "", s)
    return s.replace("{", "").replace("}", "").strip()


def kind_of(sections, total):
    if any(t == "task" for _, rows in sections for _, _, t in rows):
        return "paper1"
    return "listening" if total and total <= 30 and any(
        t in ("source", "gapfill") for _, rows in sections for _, _, t in rows
    ) and total != 40 else "reading" if total == 40 else "listening"


def main(path):
    sections, total = parse(path)
    if not sections:
        sys.exit(f"{path}: no answers recorded — has the paper been compiled?")
    kind = kind_of(sections, total)
    want_marks, want_texts = TARGETS.get(kind, (None, None))

    print(f"\n  {path}")
    print(f"  {'─' * 66}")

    grand_q = grand_m = 0
    for title, rows in sections:
        marks = sum(m for _, m, _ in rows)
        grand_q += len(rows)
        grand_m += marks
        share = f"{100 * marks / total:.0f}%" if total else "—"
        print(f"\n  {title}")
        print(f"    {len(rows)} questions · {marks} marks · {share} of the paper")
        # count blocks: a run of one type, the way the IB groups them
        blocks, prev = [], None
        for _, m, t in rows:
            if t != prev:
                blocks.append([t, 0, 0])
                prev = t
            blocks[-1][1] += 1
            blocks[-1][2] += m
        for t, n, m in blocks:
            print(f"      {NAMES.get(t, t):34} {n:2} × {m // n if n else 0} = {m:2}")

    print(f"\n  {'─' * 66}")
    print(f"  TOTAL  {grand_q} questions · {grand_m} marks · {len(sections)} texts\n")

    types = Counter(t for _, rows in sections for _, _, t in rows)
    print("  Types used: " + ", ".join(
        f"{NAMES.get(t, t)} ({n})" for t, n in types.most_common()))

    print("\n  Balance")
    ok = lambda c: "  ok " if c else "  !! "
    if want_marks:
        print(f"  {ok(grand_m == want_marks)}{grand_m} marks"
              f" (HL {kind} is {want_marks})")
    if want_texts:
        print(f"  {ok(len(sections) == want_texts)}{len(sections)} texts"
              f" (HL {kind} uses {want_texts})")
    if total is not None and total != grand_m:
        print(f"  !! recorded total {total} disagrees with the sum {grand_m}")

    # Corpus rules worth flagging. See the analysis in local/ and METHOD.md.
    if kind == "reading" and not types["true"]:
        print("  note  no identify-true-statements question, so every question here"
              "\n        carries one mark and the paper needs a full 40 of them."
              "\n        That is a real shape: 4 of 12 reading booklets do exactly"
              "\n        this. The alternative is a 35-37 question paper with an"
              "\n        identify-true-statements block worth 3-5 marks.")
    if kind == "listening":
        for title, rows in sections:
            distinct = len({t for _, _, t in rows})
            letter = title.split()[-1] if len(title.split()) < 3 else title
            if sections.index((title, rows)) == 0 and distinct != 1:
                print(f"  !!  {title}: audio text A takes one question type,"
                      f" found {distinct}")
            elif sections.index((title, rows)) > 0 and distinct != 2:
                print(f"  !!  {title}: audio texts B and C each take two"
                      f" different types, found {distinct}")
        if types["source"]:
            print("  note  tick table (L3) last appeared Nov 2023 and has not"
                  "\n        been used since. A practice paper probably should"
                  "\n        not include one.")

    print()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    for p in sys.argv[1:]:
        main(p)
