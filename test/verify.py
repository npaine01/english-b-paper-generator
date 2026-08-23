#!/usr/bin/env python3
"""Regression check for ibenglishb.sty.

Measures compiled PDFs and asserts the layout rules that were established by
measuring the real IB papers. Run it against the torture document (adversarial
content: wrapping options, wrapping matching items, wrapping stems, forced page
breaks) and against the shipped templates.

    make verify

Every tolerance is 0.15 mm unless stated. All targets are measurements taken
off the 2022-2026 papers; see README.md.
"""
import sys, re, glob
import pymupdf

K = 72 / 25.4                      # points per millimetre
TOL = 0.15

# Tick tables (\ibsource) and matching blocks both number their rows in the
# gutter, but have different pitches. The rubric is what distinguishes them.
TICK_RUBRIC = "correct option for each of the following statements"

TARGET = {
    "option pitch (last line -> next option)": 7.16,
    "leading inside a wrapped option":         4.66,
    "matching item pitch (last -> next)":      9.80,
    "square below option baseline":            3.09,
    "square below row baseline":               1.49,
    "answer box height":                      15.01,
    "stem baseline -> box top":                4.39,
    "box top -> dotted line":                  7.53,
    "true/false box height":                  22.24,
    "notes box top":                         222.09,
}

fails, checks = [], 0


def ok(name, got, want, tol=TOL, unit="mm"):
    global checks
    checks += 1
    if got is None:
        fails.append(f"{name}: not found")
    elif abs(got - want) > tol:
        fails.append(f"{name}: {got:.2f}{unit}, expected {want:.2f}{unit}")


BODY_BOTTOM = 280        # reading papers run to the bottom margin
NOTES_TOP   = 221        # listening papers stop above the Notes box


def lines(page, xmin=0, xmax=999, ymax=None):
    """Text lines as (x0, baseline, text), body area only."""
    if ymax is None:
        ymax = BODY_BOTTOM
    out = []
    for b in page.get_text("dict")["blocks"]:
        for l in b.get("lines", []):
            if not l["spans"]:
                continue
            x0 = l["bbox"][0] / K
            y = l["spans"][0]["origin"][1] / K
            t = "".join(s["text"] for s in l["spans"]).strip()
            if t and xmin <= x0 <= xmax and y < ymax:
                out.append((x0, y, t))
    return sorted(out, key=lambda r: r[1])


def rects(page):
    return [d["rect"] for d in page.get_drawings()]


def squares(page, xmin=0, xmax=999):
    """Answer squares, returned as (left, top, bottom) in mm."""
    out = []
    for r in rects(page):
        w, h = (r.x1 - r.x0) / K, (r.y1 - r.y0) / K
        if 5.4 < w < 6.2 and 5.4 < h < 6.2 and xmin <= r.x0 / K <= xmax:
            out.append((r.x0 / K, r.y0 / K, r.y1 / K))
    # framebox squares are drawn as four strokes; pair up the verticals instead
    if not out:
        v = [(round(r.x0 / K, 2), r.y0 / K, r.y1 / K) for r in rects(page)
             if (r.x1 - r.x0) / K < 0.4 and 5.4 < (r.y1 - r.y0) / K < 6.2]
        seen = {}
        for x, y0, y1 in v:
            seen.setdefault(round(y0, 2), []).append(x)
        for y0, xs in seen.items():
            if len(xs) >= 2 and xmin <= min(xs) <= xmax:
                out.append((min(xs), y0, y0 + 5.62))
    return sorted(out, key=lambda s: s[1])


def check_options(doc):
    """Option pitch measured last-line -> next first-line, and wrap leading."""
    pitches, leadings = [], []
    for p in doc:
        rows = lines(p, xmin=40, xmax=60)          # option letters at x=41.5
        txt = lines(p, xmin=50, xmax=54)           # option text at x=51.5
        letters = [(y, t) for x, y, t in rows if re.fullmatch(r"[A-J]\.", t)]
        if len(letters) < 2:
            continue
        allt = [(y, t) for x, y, t in lines(p, xmin=50, xmax=53)]
        for i in range(len(letters) - 1):
            y0, y1 = letters[i][0], letters[i + 1][0]
            inner = [y for y, t in allt if y0 < y < y1 - 0.5]
            last = inner[-1] if inner else y0
            gap = y1 - last
            if gap < 12:              # same run of options, not the next question
                pitches.append(round(gap, 2))
            prev = y0
            for y in inner:
                leadings.append(round(y - prev, 2)); prev = y
    return pitches, leadings


def check_items(doc):
    """Matching item pitch, measured last line -> next item's first line.

    Only rows carrying a matching answer square (at \\ibmatchboxx, ~34.1mm)
    are counted. Tick-table rows (\\ibsource) are numbered in the same gutter
    but are a different construct with a different pitch; they are measured
    separately by check_tickrows.
    """
    pitches = []
    for p in doc:
        if TICK_RUBRIC in p.get_text():
            continue                       # tick table, not a matching block

        nums = [(y, t) for x, y, t in lines(p, xmin=14, xmax=16)
                if re.fullmatch(r"\d+\.", t)]
        body = [y for x, y, t in lines(p, xmin=24, xmax=30)]
        if len(nums) < 2:
            continue
        for i in range(len(nums) - 1):
            y0, y1 = nums[i][0], nums[i + 1][0]
            if y1 - y0 > 14:                        # different block
                continue
            inner = [y for y in body if y0 < y < y1 - 0.5]
            last = inner[-1] if inner else y0
            pitches.append(round(y1 - last, 2))
    return pitches


def check_tickrows(doc):
    """Tick-table (\\ibsource) row pitch, baseline to baseline.

    Only consecutive single-line rows are compared: a wrapped row makes the
    following gap depend on its content, so it carries no invariant.
    """
    pitches = []
    for p in doc:
        if TICK_RUBRIC not in p.get_text():
            continue
        nums = sorted((y, t) for x, y, t in lines(p, xmin=14, xmax=16)
                      if re.fullmatch(r"\d+\.", t))
        body = [y for x, y, t in lines(p, xmin=24, xmax=30)]
        for i in range(len(nums) - 1):
            y0, y1 = nums[i][0], nums[i + 1][0]
            if not 8 < y1 - y0 < 20:
                continue
            if any(y0 < y < y1 - 0.5 for y in body):    # row 0 wrapped
                continue
            pitches.append(round(y1 - y0, 2))
    return pitches


def check_summary_gaps(doc):
    """Gap labels inside a gap-fill summary must be real question numbers.

    \\ibsummary takes literal numbers, so reordering a document silently
    leaves the summary pointing at questions that no longer exist.
    """
    bad = []
    for pno, p in enumerate(doc, 1):
        txt = p.get_text()
        if "completes each gap" not in txt:
            continue
        labels = {int(m) for m in re.findall(r"\[\s*[-\u2013]\s*(\d+)\s*[-\u2013]\s*\]", txt)}
        qnums = {int(t[:-1]) for x, y, t in lines(p, xmin=14, xmax=16)
                 if re.fullmatch(r"\d+\.", t)}
        missing = sorted(labels - qnums)
        if missing:
            bad.append((pno, missing, sorted(qnums)))
    return bad



def check_twoanswer(doc):
    """The 'Give two answers' box: (a) and (b) baselines and the label column.

    A distinct set of constants from the single-answer box (20.86mm tall rather
    than 15.01, two writing lines rather than one), so it needs its own check.
    """
    pitches, labelx = [], []
    for p in doc:
        rows = {}
        for x, y, t in lines(p):
            # the label arrives joined to its dotted run, so match the prefix
            lab = t.strip()[:3]
            if lab in ("(a)", "(b)"):
                rows.setdefault(lab, []).append((y, x))
        if "(a)" in rows and "(b)" in rows:
            for (ya, xa), (yb, _) in zip(sorted(rows["(a)"]), sorted(rows["(b)"])):
                pitches.append(round(yb - ya, 2))
                labelx.append(round(xa - 15.0, 2))     # from the left margin
    return pitches, labelx


def check_boxes(doc):
    """Answer boxes: height, offset below the stem, dotted-line position."""
    heights, gaps, dots = [], [], []
    for p in doc:
        # full-measure boxes only: the listening gap-fill box is 150 mm wide
        # and carries its label beside it rather than above it
        hor = sorted(r.y0 / K for r in rects(p)
                     if (r.x1 - r.x0) / K > 175 and (r.y1 - r.y0) / K < 0.6
                     and r.y0 / K < BODY_BOTTOM)
        ln = lines(p)
        i = 0
        while i < len(hor) - 1:
            top, bot = hor[i], hor[i + 1]
            h = bot - top + 0.18
            if 14 < h < 16:                          # a written-answer box
                heights.append(round(h, 2))
                # the last line of the stem, which for a wrapped stem is not
                # the line carrying the question number
                above = [(x, y) for x, y, t in ln if y < top - 0.5]
                numbered = [y for x, y, t in ln
                            if y < top - 0.5 and x < 20 and re.fullmatch(r"\d+\.", t)]
                if above and numbered:
                    gaps.append(round(top - max(y for _, y in above), 2))
                dd = [y for x, y, t in ln if top < y < bot
                      and set(t) <= set(". ")]
                if dd:
                    dots.append(round(dd[0] - top, 2))
                i += 2
            else:
                i += 1
    return heights, gaps, dots


def check_no_split(doc):
    """No stem may be separated from its answer structure by a page break."""
    bad = []
    for pno, p in enumerate(doc, 1):
        reach = [r.y1 / K for r in rects(p) if r.y1 / K < BODY_BOTTOM]
        for x, y, t in lines(p):
            if re.fullmatch(r"\d+\.", t) and x < 20:
                if not any(m > y - 4 for m in reach):
                    bad.append(f"p{pno} stem {t}")
    return bad


def check_orphan_rubric(doc):
    RUB = ("Answer the following", "The following statements", "Choose the",
           "Complete the following", "Tick [", "Find the word", "To whom")
    bad = []
    for pno, p in enumerate(doc, 1):
        ln = lines(p)
        if ln and any(ln[-1][2].startswith(r) for r in RUB):
            bad.append(f"p{pno}")
    return bad


def check_hyphens(doc):
    bad = []
    for pno, p in enumerate(doc, 1):
        for b in p.get_text("dict")["blocks"]:
            for l in b.get("lines", []):
                t = "".join(s["text"] for s in l["spans"]).rstrip()
                if re.search(r"[a-z]-$", t) and "http" not in t:
                    bad.append(f"p{pno} …{t[-24:]!r}")
    return bad


def check_ragged(doc):
    """Ragged right: wrapped lines must not all end at the same x."""
    ends = []
    for p in doc:
        for b in p.get_text("dict")["blocks"]:
            ls = b.get("lines", [])
            for i, l in enumerate(ls):
                t = "".join(s["text"] for s in l["spans"]).strip()
                if len(t) > 45 and i < len(ls) - 1:
                    ends.append(l["bbox"][2] / K)
    return (max(ends) - min(ends)) if len(ends) > 3 else None


def check_paper1(doc):
    """Paper 1: rubric and task baselines, three centred text-type columns."""
    from collections import defaultdict
    out = []
    for p in doc:
        rows = defaultdict(list)
        for b in p.get_text("dict")["blocks"]:
            for l in b.get("lines", []):
                for s in l["spans"]:
                    t = s["text"].strip()
                    if t:
                        rows[round(s["origin"][1] / K, 2)].append(
                            (s["bbox"][0] / K, s["bbox"][2] / K, t,
                             "Bold" in s["font"]))
        ys = sorted(rows)
        tn = [y for y in ys
              if any(bo and re.fullmatch(r"[123]\.", t) for _, _, t, bo in rows[y])]
        opt = [y for y in ys if len(rows[y]) == 3
               and all(a > 40 for a, _, _, _ in rows[y])]
        for y in opt:
            prev = [z for z in ys if z < y - 1]
            if prev:
                out.append(("task text -> options", round(y - prev[-1], 2), 11.42))
            nxt = [z for z in tn if z > y]
            if nxt:
                out.append(("options -> next task", round(nxt[0] - y, 2), 15.21))
            for i, (a, b2, t, _) in enumerate(sorted(rows[y])):
                out.append((f"text-type column {i+1} centre",
                            round((a + b2) / 2, 1), (53.4, 110.1, 166.8)[i]))
        if tn:
            out.append(("task 1 baseline", tn[0], 41.74))
    return out


def run(path, notes_expected):
    global BODY_BOTTOM
    BODY_BOTTOM = NOTES_TOP if notes_expected else 280
    doc = pymupdf.open(path)
    print(f"\n  {path}  ({doc.page_count} pages)")
    paper1 = "paper1" in path      # writing paper: tasks, no answer boxes

    pit, lead = check_options(doc)
    if pit:
        ok("option pitch (last line -> next option)", sum(pit) / len(pit), 7.16)
    if lead:
        ok("leading inside a wrapped option", sum(lead) / len(lead), 4.66)

    ip = check_items(doc)
    if ip:
        ok("matching item pitch (last -> next)", sum(ip) / len(ip), 9.80)

    tp, tx = check_twoanswer(doc)
    if tp:
        ok("two-answer box: (a) -> (b) pitch", sum(tp) / len(tp), 7.16)
        ok("two-answer box: label column", sum(tx) / len(tx), 10.80)

    tr = check_tickrows(doc)
    if tr:
        ok("tick-table row pitch", sum(tr) / len(tr), 12.71)

    for pno, missing, qnums in check_summary_gaps(doc):
        ok(f"summary gap labels are real questions (p{pno}: {missing} not in {qnums})",
           0, 1, unit="")

    if not paper1:
        h, g, d = check_boxes(doc)
        if h: ok("answer box height", sum(h) / len(h), 15.01)
        if g: ok("stem baseline -> box top", sum(g) / len(g), 4.39)
        if d: ok("box top -> dotted line", sum(d) / len(d), 7.53)

    checkset = (("pages ending on a rubric", check_orphan_rubric),
                ("hyphenated word breaks", check_hyphens))
    if not paper1:
        checkset = (("questions split across a page", check_no_split),) + checkset
    for label, fn in checkset:
        global checks
        checks += 1
        bad = fn(doc)
        if bad:
            fails.append(f"{label}: {len(bad)} — {bad[:3]}")

    spread = check_ragged(doc)
    if spread is not None:
        checks += 1
        if spread < 3:
            fails.append(f"text appears justified (line-end spread {spread:.2f} mm)")

    if "paper1" in path:
        for label, got, want in check_paper1(doc):
            ok(label, got, want)

    if notes_expected:
        for pno, p in enumerate(doc, 1):
            if pno == 1:
                continue
            ys = sorted({round(r.y0 / K, 2) for r in rects(p)
                         if (r.x1 - r.x0) / K > 150 and (r.y1 - r.y0) / K < 0.6})
            top = [y for y in ys if 221 < y < 224]
            ok(f"notes box top (p{pno})", (top[0] - 0.09) if top else None, 222.09)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: verify.py <pdf> [<pdf> ...]", file=sys.stderr)
        sys.exit(2)
    targets = [(f, "listening" in f or "torture" in f) for f in sys.argv[1:]]
    for path, notes in targets:
        run(path, notes)
    print(f"\n  {checks} checks")
    if checks == 0:
        # "0 checks / all passed" is a false pass: it looks identical to success
        # while proving nothing. Anything that finds no work is a failure.
        print("  FAILED: no checks ran — wrong paths, or the PDFs were not built")
        sys.exit(1)
    if fails:
        print(f"  FAILED ({len(fails)}):")
        for f in fails:
            print(f"    - {f}")
        sys.exit(1)
    print("  all passed")
