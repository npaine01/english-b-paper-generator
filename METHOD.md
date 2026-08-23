# METHOD — how this package was built, and how to extend it safely

This file exists because the hard-won part of this project is not the LaTeX.
It is the **method** used to arrive at the numbers in `ibenglishb.sty`, and the
list of ways that method can quietly fail. Anyone extending this — a new
question type, an SL variant, another subject — should read this first.

---

## 1. Standing rules

These are ordered. Rule 7 is the one that mattered most.

1. **The specification is the paper, not the description of the paper.**
   Documents that describe the exam (subject guides, "assessment question
   types" summaries) are authoritative for *what questions exist* and *how many
   marks they carry*. They are not authoritative for layout. Layout comes from
   measuring real papers.

2. **One source of truth per constant.** Every measurement lives once, as a
   named length in `ibenglishb.sty`. No magic numbers at the call site. If a
   value appears in two places, one of them will drift.

3. **Structural fixes only.** When something is wrong in one document, fix it
   in the package so it is right in every document. A fix applied to a `.tex`
   file is not a fix; it is a workaround that hides the defect.

4. **Validate against the corpus, not against one paper.** A constant is
   accepted when it is the modal value across many booklets. A value taken from
   a single paper may be that paper's accident.

5. **Every invariant gets an assertion.** If you measured it, encode it in
   `test/verify.py`. The measurement is worthless the moment someone changes a
   length and nothing complains.

6. **Test on invented content.** `test/torture.tex` exercises every question
   type using content written for the purpose. If the package only looks right
   with the original text in it, the package is wrong.

7. **Never accept a measurement taken by eye.**
   This is the rule that repeatedly saved the project, because rendering
   *looks* correct far more often than it *is* correct. Screenshots, PDF
   viewers and intuition all agreed with wrong answers at least six separate
   times (see §3). If a number is going into the package, extract it
   programmatically from the PDF.

8. **A clean compile proves nothing.** Zero errors and zero overfull boxes
   means TeX was satisfied. It does not mean the output says what you meant.
   Always read back the rendered text.

---

## 2. How to measure a PDF properly

Use PyMuPDF. The environment for this is `test/.venv`.

**Use `span["origin"]`, not `span["bbox"]`.** `origin` is the true text
baseline. `bbox` is a bounding box whose conventions differ between producers,
so comparing a bbox from a real paper against a bbox from our output compares
two different things. Several early conclusions were wrong for exactly this
reason.

**Measure pitch baseline-to-baseline.** Not top-of-glyph to top-of-glyph, and
not gap-between-boxes. For wrapped text, the pitch that matters is *last line of
one item → first line of the next*.

**Convert to millimetres immediately.** `mm = pt * 25.4 / 72`. Every constant in
this package is in millimetres so it can be compared to a ruler and to the
paper.

**Boxes are often not rectangles.** In these papers a framed answer box is drawn
as four separate stroked lines, not a `re` operator. A probe that only looks for
rectangles will conclude, wrongly, that there is no box at all. Collect drawing
primitives and reconstruct.

**Measure rendered ink when position is not enough.** Some spans begin with a
figure space (U+2007) or similar invisible padding. Coordinate measurement says
the column starts where the span starts; the reader sees it start 3 mm later.
When a column "looks" too tight but measures correct, render to a bitmap and
find the first inked column.

---

## 3. The failure modes, and what each one taught

Grouped by cause, because the individual bugs matter less than the pattern.

### Measuring the wrong thing
- Bounding boxes compared against baselines → offsets that were confidently
  wrong. *Fixed by standardising on `origin`.*
- Whole-page vertical offset of 0.95 mm in two booklets, invisible until
  baselines were compared. Header and body were both shifted.
- Body leading set to 13.2 pt when the paper uses 13.25 pt. Under 1 pt of error
  per line; several millimetres of drift by the bottom of a page.
- One square offset used for two different contexts. A tick box beside an
  option list sits 3.09 mm below the baseline; the same box on its own row sits
  1.49 mm below. Using one number for both put half the boxes 2.4 mm out.
- A dotted rule placed 3.48 mm below the box top when the real one sits at
  7.53 mm — the vertical centre of the box.
- Extraction that read only the first line of a wrapped stem, which made a
  survey of trailing ellipses report 55% and 93% instead of the true 100% and
  95%.

### Believing the render
- "The text booklet is justified" — it is not. Line-end positions spread from
  184.09 to 195.92 mm with overshoots, which is ragged right. It merely *looked*
  justified.
- "The 2025 papers have no framed box" — they do. The probe filtered out
  four-line boxes.
- Markschemes rebuilt from extracted text lost their vertical rules and their
  landscape orientation, because the extraction returned words and not the grid.

### TeX doing something other than what was asked
- `\Needspace*` **ejects the page itself**, which stranded rubrics at the bottom
  of pages while trying to prevent exactly that. Replaced entirely by `\nobreak`
  welding.
- `\RaggedRight` from *ragged2e* silently does nothing inside a box or an array
  preamble. Bit this project twice. Set `\rightskip` directly.
- `\newcommand` cannot take two optional arguments. `\ibshortqtwo[a][b]{stem}`
  silently absorbed the second answer into the stem.
- A space leak from `\if#3T` at end of line shifted a whole block 0.7 mm right.
  Terminate such lines with `%`.
- `\prevdepth` is not meaningful after a multi-line `\parbox[t]`, so wrapped
  stems placed their box 4.14 mm below instead of 4.39 mm. Use struts to make
  box height and depth deterministic regardless of content.
- `%` inside `\write` starts a comment and unbalances braces. Use a
  `\catcode`-switched `\ibeb@pct`.
- Environments cannot be nested inside `\savebox`/`lrbox` across a group
  boundary. The two-column matching layout was rebuilt using **accumulators**
  (token lists replayed at `\end`), which also allowed the option column to
  size itself.

### Clean compile, wrong output
- **`\ibtfq` takes one mandatory argument, not two.** Calling
  `\ibtfq[F]{quote}{statement}` compiled with zero errors and zero bad boxes,
  rendered the *justification quote* as the statement, and dropped the real
  statement into the page as loose text. Caught only by reading the extracted
  text back. The correct form is `\ibtfq[F: ``quote'']{statement}`.
- Tick-table columns hard-coded to 20 mm overflowed for long source labels.
  Found by the torture test, not by any real document.
- `.gitignore` entries with trailing comments (`path  # note`) match nothing,
  so build artefacts were staged.

---

## 4. The verification harness

```bash
make verify
```

Runs ~80 checks over `test/torture.tex` plus the shipped documents. It asserts,
among others:

| Invariant | Value |
|---|---|
| Option pitch (baseline→baseline) | 7.16 mm |
| Wrapped-line leading | 4.66 mm |
| Item pitch | 9.80 mm |
| Answer box height | 15.01 mm |
| Stem → box top | 4.39 mm |
| Box top → dotted rule | 7.53 mm |
| Notes box top edge | 222.09 mm |

and structurally: no question split across a page, no rubric orphaned from its
questions, no hyphenation, ragged-right body, Paper 1 geometry.

**When you add a question type, add its assertions in the same commit.**

---

## 5. Things known to be unresolved

- **Furigana breaks the baseline grid.** `xeCJK` + `ruby` + Hiragino Sans
  compiles under tectonic with no extra installation, but ruby annotations
  perturb line spacing — measured gaps of 3.20 / 2.32 / 3.21 / 4.78 mm where the
  grid requires a constant. Any Japanese variant needs this solved before it can
  claim to match a real paper.
- **SL is untested.** No SL papers were available, so no SL constants have been
  measured. Do not assume HL values transfer.
- **Two reading question types were never observed.** Matching questions to gaps
  (R3) and matching statements to people (R6) do not appear in twelve reading
  papers across five years. They are implemented from the specification, not
  from measurement, and their spacing is therefore unverified.
- **Paper 1 spacing changed at November 2024.** `\ibpaperonelegacy` restores the
  earlier values. If you are reproducing an older paper, you need it.
- **The `paragraphs N–M` badge pair may sit ~0.5 mm right of the real one.**
  Observed while comparing generated output against May 2021. The *internal*
  spacing of the pair matches to 0.03 mm, so the badge itself is right; the
  lead-in from the word "paragraphs" is what differs, and the extracted text
  shows a space before the dash that the real paper does not have. Five
  different probes gave inconsistent readings and none was trustworthy, so this
  is an observation, not a measurement. Affects one rubric form. If you pick it
  up, rasterise both lines and compare inked columns rather than span origins —
  see §2 on measuring rendered ink.
