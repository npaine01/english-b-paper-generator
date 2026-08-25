#!/usr/bin/env python3
"""Write a paper as a .docx, from the model the editor holds.

Built from the paper's own structure rather than from the generated LaTeX:
parsing our macros back out would be fragile, and the model already knows
everything the document needs.

A .docx is a zip of XML, so this needs nothing beyond the standard library —
which keeps the server dependency-free.

What this is for: a colleague editing questions, adding an image, reformatting
something in a familiar tool. What it is NOT: a faithful copy of the printed
paper. Word has a different line-breaking algorithm and no fixed baseline grid,
so the measured constants that the LaTeX output guarantees — a 15.01 mm answer
box, a 7.16 mm option pitch — are approximated here in Word's own units and
will not survive editing. Use the PDF for anything a student sits.
"""
import zipfile
from xml.sax.saxutils import escape

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
TWIP = 56.7          # twips per millimetre (1440 per inch)


def _t(s):
    """A run of literal text, with Word's line breaks for newlines."""
    parts = str(s or "").split("\n")
    out = []
    for i, p in enumerate(parts):
        if i:
            out.append("<w:br/>")
        out.append(f'<w:t xml:space="preserve">{escape(p)}</w:t>')
    return "".join(out)


def para(text="", *, bold=False, size=22, before=0, after=60, ind=0,
         align=None, style=None):
    """size is in half-points: 22 = 11pt, matching the paper's body size."""
    rpr = "<w:rPr>" + ("<w:b/>" if bold else "") + \
          f'<w:sz w:val="{size}"/><w:szCs w:val="{size}"/></w:rPr>'
    ppr = ["<w:pPr>"]
    if style:
        ppr.append(f'<w:pStyle w:val="{style}"/>')
    ppr.append(f'<w:spacing w:before="{before}" w:after="{after}"/>')
    if ind:
        ppr.append(f'<w:ind w:left="{int(ind * TWIP)}"/>')
    if align:
        ppr.append(f'<w:jc w:val="{align}"/>')
    ppr.append("</w:pPr>")
    return "".join(ppr) and f'<w:p>{"".join(ppr)}<w:r>{rpr}{_t(text)}</w:r></w:p>'


def rule_box(height_mm=15.0, lines=1):
    """The ruled answer box. A bordered single-cell table is the closest Word
    equivalent, and unlike a drawn shape it stays put when text above it moves."""
    inner = "".join(
        f'<w:p><w:pPr><w:spacing w:before="120" w:after="0"/>'
        f'<w:pBdr><w:bottom w:val="dotted" w:sz="6" w:space="1" w:color="555555"/></w:pBdr>'
        f'</w:pPr><w:r><w:t xml:space="preserve"> </w:t></w:r></w:p>'
        for _ in range(max(1, lines)))
    return (
        '<w:tbl><w:tblPr>'
        '<w:tblW w:w="0" w:type="auto"/>'
        '<w:tblBorders>'
        '<w:top w:val="single" w:sz="4" w:color="000000"/>'
        '<w:left w:val="single" w:sz="4" w:color="000000"/>'
        '<w:bottom w:val="single" w:sz="4" w:color="000000"/>'
        '<w:right w:val="single" w:sz="4" w:color="000000"/>'
        '</w:tblBorders>'
        f'<w:tblCellMar><w:top w:w="60" w:type="dxa"/><w:bottom w:w="60" w:type="dxa"/>'
        f'<w:left w:w="220" w:type="dxa"/><w:right w:w="220" w:type="dxa"/></w:tblCellMar>'
        '</w:tblPr><w:tr><w:tc>'
        f'<w:tcPr><w:tcW w:w="9600" w:type="dxa"/></w:tcPr>{inner}'
        '</w:tc></w:tr></w:tbl>'
        '<w:p><w:pPr><w:spacing w:after="120"/></w:pPr></w:p>')


def tick_box():
    """An empty square for the student to tick, as a bordered inline cell."""
    return ('<w:tbl><w:tblPr><w:tblW w:w="0" w:type="auto"/>'
            '<w:tblBorders>'
            '<w:top w:val="single" w:sz="4" w:color="000000"/>'
            '<w:left w:val="single" w:sz="4" w:color="000000"/>'
            '<w:bottom w:val="single" w:sz="4" w:color="000000"/>'
            '<w:right w:val="single" w:sz="4" w:color="000000"/></w:tblBorders>'
            '</w:tblPr><w:tr><w:tc><w:tcPr><w:tcW w:w="340" w:type="dxa"/></w:tcPr>'
            '<w:p/></w:tc></w:tr></w:tbl>')


LETTERS = "ABCDEFGHIJ"


def numbering(items, kind):
    """Question numbers and marks — mirrors the rules in ui/index.html so the
    .docx numbers a paper exactly as the PDF does."""
    q = 0
    out = []
    for it in items:
        t = it.get("t")
        if t in ("text", "brk", "task"):
            out.append((None, None, 0)); continue
        if t == "true":
            q += 1; out.append((q, q, int(it.get("marks") or 0)))
        elif t == "short" and it.get("two"):
            q += 1; out.append((q, q, 2))
        elif t == "match":
            n = len(it.get("items") or []); out.append((q + 1, q + n, n)); q += n
        elif t == "source":
            n = len(it.get("rows") or []); out.append((q + 1, q + n, n)); q += n
        elif t == "gapfill":
            n = len([m for m in (it.get("stimulus") or "").split("[]")]) - 1
            n = max(0, n); out.append((q + 1, q + n, n)); q += n
        else:
            q += 1; out.append((q, q, 1))
    return out


RUBRIC = {
    "mcq": "Choose the correct answer.",
    "short": "Answer the following questions.",
    "tf": "The following statements are either true or false. Tick the correct "
          "option, then justify it using words as they appear in the text.",
    "refer": "To whom or to what do the underlined words refer? Answer using "
             "words as they appear in the text.",
    "findword": "Find the word or phrase in {ref} which means the following:",
    "complete": "Find the words that complete the following sentences. Answer "
                "using the words as they appear in {ref}.",
    "headings": "Choose an appropriate heading from the list that completes each "
                "gap in the text.",
    "vocab": "What do the following words mean in the text? Choose the "
             "appropriate word from the list.",
    "halves": "Choose an appropriate ending from the list that completes each "
              "sentence.",
    "people": "Choose the appropriate statement from the list for each person.",
    "matchq": "Choose an appropriate question from the list that completes each "
              "gap in the text.",
    "gapsummary": "Choose the appropriate word from the list that completes each "
                  "gap in the following text.",
    "source": "Tick one correct option for each of the following statements.",
    "gapfill": "Complete the following gaps. Use no more than three words for "
               "each gap.",
    "task": "Complete one task. Use an appropriate text type from the options "
            "below the task you choose. Write 450 to 600 words.",
}


def qlabel(a, b):
    return f"{a}." if a == b else f"{a}–{b}"


def body(paper):
    """The document body, item by item."""
    items = paper.get("items") or []
    nums = numbering(items, paper.get("kind"))
    out = []
    last_rubric = None

    for it, (a, b, marks) in zip(items, nums):
        t = it.get("t")

        if t == "text":
            last_rubric = None
            lead = "Audio text" if paper.get("kind") == "listening" else "Text"
            head = f'{lead} {it.get("label", "")}'
            if it.get("title"):
                head += f' — {it["title"]}'
            out.append(para(head, bold=True, size=26, before=320, after=140))
            continue

        if t == "brk":
            out.append('<w:p><w:r><w:br w:type="page"/></w:r></w:p>')
            continue

        if t == "task":
            out.append(para(it.get("scenario", ""), after=120, ind=8))
            three = sorted(it.get("types") or [])
            out.append(para("      ".join(three), bold=True, after=260, ind=8))
            continue

        # the rubric, once per run of like questions
        key = t if t != "match" else "match:" + str(it.get("kind"))
        rub = RUBRIC.get(it.get("kind") if t == "match" else t)
        if t in ("findword", "complete"):
            key += "|" + str(it.get("ref", ""))
            rub = (rub or "").replace("{ref}", str(it.get("ref") or "the text"))
        if rub and key != last_rubric:
            out.append(para(rub, after=140, before=200))
            last_rubric = key

        mk = "" if not marks or marks == 1 else f"   [{marks} marks]"
        stem = it.get("stem") or ""

        if t == "mcq":
            out.append(para(f"{qlabel(a, b)}   {stem}{mk}", after=80))
            for k, o in enumerate(it.get("opts") or []):
                out.append(para(f"{LETTERS[k]}.   {o}", ind=14, after=40))
            out.append(para("", after=100))

        elif t == "true":
            out.append(para(f"{qlabel(a, b)}   Choose the {marks} true statements."
                            f"{mk}", after=80))
            for k, o in enumerate(it.get("opts") or []):
                out.append(para(f"{LETTERS[k]}.   {o}", ind=14, after=40))
            out.append(para("", after=100))

        elif t == "match":
            out.append(para(qlabel(a, b), bold=True, after=60))
            for k, m in enumerate(it.get("items") or []):
                lab = m.get("text") or f"[ – {a + k} – ]"
                if it.get("kind") == "vocab" and m.get("line"):
                    lab += f'  (line {m["line"]})'
                out.append(para(f"{a + k}.   {lab}", ind=8, after=40))
            out.append(para("Options:", bold=True, ind=8, before=80, after=40))
            for k, o in enumerate(it.get("opts") or []):
                out.append(para(f"{LETTERS[k]}.   {o}", ind=14, after=40))
            out.append(para("", after=100))

        elif t == "tf":
            out.append(para(f"{qlabel(a, b)}   {stem}{mk}", after=60))
            out.append(para("True  ☐          False  ☐", ind=8, after=40))
            out.append(rule_box(lines=2))

        elif t == "gapfill":
            out.append(para(it.get("caption") or "", bold=True, after=60))
            for line in (it.get("stimulus") or "").split("\n"):
                s = line.strip()
                if not s:
                    continue
                bold = s.startswith("#")
                s = s.lstrip("#").strip()
                s = s.replace("[]", "__________")
                out.append(para(s, bold=bold, ind=8 if not bold else 4, after=40))
            for k in range(b - a + 1):
                out.append(para(f"{a + k}.", after=40))
                out.append(rule_box())

        elif t == "source":
            out.append(para(it.get("header") or "", bold=True, after=60))
            cols = it.get("cols") or []
            out.append(para("            ".join(c for c in cols), bold=True,
                            ind=60, after=60))
            for k, r in enumerate(it.get("rows") or []):
                out.append(para(f'{a + k}.   {r.get("text", "")}', after=40))
                out.append(para("   ".join("☐" for _ in cols), ind=60, after=80))

        else:
            # the written-answer family: short, findword, complete, refer
            body_text = stem
            if t == "refer" and it.get("line"):
                body_text += f'  (line {it["line"]})'
            out.append(para(f"{qlabel(a, b)}   {body_text}{mk}", after=60))
            out.append(rule_box(lines=2 if (t == "short" and it.get("two")) else 1))

    return "".join(out)


TITLES = {
    "reading":   "English B – Higher level – Paper 2 – Reading comprehension",
    "listening": "English B – Higher level – Paper 2 – Listening comprehension",
    "paper1":    "English B – Higher level – Paper 1",
}

INSTRUCTIONS = {
    "reading": ["Write your session number in the boxes above.",
                "Do not open this examination paper until instructed to do so.",
                "Answer all questions. Each question is allocated [1 mark] unless "
                "otherwise stated.",
                "Answers must be written within the answer boxes provided.",
                "All answers must be based on the appropriate texts in the "
                "accompanying text booklet."],
    "listening": ["Write your session number in the boxes above.",
                  "Do not open this examination paper until instructed to do so.",
                  "Answer all questions. Each question is allocated [1 mark] "
                  "unless otherwise stated.",
                  "Answers must be written within the answer boxes provided.",
                  "Each audio text will be played twice."],
    "paper1": ["Do not turn over this examination paper until instructed to do so.",
               "Complete one task."],
}

DOC = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
       f'<w:document xmlns:w="{W}"><w:body>{{body}}'
       '<w:sectPr>'
       '<w:pgSz w:w="11906" w:h="16838"/>'          # A4 portrait, in twips
       '<w:pgMar w:top="1358" w:right="839" w:bottom="1077" w:left="850"'
       ' w:header="0" w:footer="0" w:gutter="0"/>'
       '</w:sectPr></w:body></w:document>')

STYLES = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
          f'<w:styles xmlns:w="{W}"><w:docDefaults><w:rPrDefault><w:rPr>'
          '<w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:cs="Arial"/>'
          '<w:sz w:val="22"/><w:szCs w:val="22"/>'
          '</w:rPr></w:rPrDefault></w:docDefaults></w:styles>')

CONTENT_TYPES = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                 '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                 '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                 '<Default Extension="xml" ContentType="application/xml"/>'
                 '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
                 '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
                 '</Types>')

RELS = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
        '</Relationships>')

DOC_RELS = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
            '</Relationships>')


def build(paper, out_path):
    """Write `paper` (the editor's model, as a dict) to out_path as a .docx."""
    kind = paper.get("kind", "reading")
    head = []
    if paper.get("title"):
        head.append(para(paper["title"], bold=True, size=24, after=60))
    head.append(para(TITLES.get(kind, TITLES["reading"]), bold=True, size=28,
                     after=80))
    meta = " · ".join(x for x in (paper.get("session"), paper.get("date"),
                                  "1 h 30 m" if kind == "paper1" else "1 h") if x)
    head.append(para(meta, size=20, after=200))

    head.append(para("Instructions to students", bold=True, after=80))
    marks = 30 if kind == "paper1" else int(paper.get("target") or 0)
    for line in INSTRUCTIONS.get(kind, INSTRUCTIONS["reading"]):
        head.append(para("•   " + line, ind=6, after=50))
    head.append(para(f"•   The maximum mark for this examination paper is "
                     f"[{marks} marks].", ind=6, after=60))
    head.append('<w:p><w:r><w:br w:type="page"/></w:r></w:p>')

    xml = DOC.format(body="".join(head) + body(paper))

    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", CONTENT_TYPES)
        z.writestr("_rels/.rels", RELS)
        z.writestr("word/_rels/document.xml.rels", DOC_RELS)
        z.writestr("word/styles.xml", STYLES)
        z.writestr("word/document.xml", xml)
    return out_path
