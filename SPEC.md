# SPEC — building an exam generator for a different subject

This repository generates IB Diploma Programme **English B HL** papers. The
architecture is not specific to English B. This file is the brief you would hand
to an AI assistant (or a colleague) to build the equivalent for another subject
or another examination board.

Read `METHOD.md` first. It contains the working rules and the failure modes.
This file only covers scoping.

---

## Questions to answer before any code is written

An assistant starting this work should ask these, and should not proceed on
assumptions:

1. **Which qualification, subject and level, exactly?**
   HL and SL of the same subject frequently differ in mark totals, question
   counts and sometimes spacing. Treat them as separate targets until measurement
   proves otherwise.

2. **How many real papers can you consult, and from what range of sessions?**
   Fewer than about six is not enough to distinguish a house style from one
   paper's accident. If the range spans a syllabus change, expect two sets of
   constants and plan for a legacy switch from the start (this project needed
   `\ibpaperonelegacy` for a November 2024 change).

3. **What is the exhaustive list of question types, and what does each one carry
   in marks?**
   Get this from the official subject documentation, not by reading papers —
   papers show you what was used, not what exists. This project found two
   documented reading types that never appear in five years of papers.

4. **Which components are in scope?**
   Reading, listening, writing, orals, markschemes, text booklets. Each is a
   different document class with different furniture. Scope creep here is
   expensive.

5. **What languages and scripts must be typeset?**
   This determines the engine. Latin-script subjects can use pdfLaTeX. Anything
   with CJK, right-to-left text, or ruby annotation forces XeLaTeX or LuaLaTeX
   and may break a fixed baseline grid — see the unresolved-issues section of
   `METHOD.md`.

6. **Who operates the finished tool?**
   A teacher clicking buttons needs a browser UI with validation that catches
   the mistakes teachers actually make. A department maintaining a question bank
   needs importable, diffable source files. These lead to different designs.

7. **Does the school require its own cover page, logo or session coding?**
   Cheap if designed in, awkward if bolted on.

---

## The build order that worked

1. **Measure before writing anything.** Extract geometry from real papers into a
   table of candidate constants, with a frequency count per value. Accept the
   modal value.
2. **Write the package.** One named length per constant, no magic numbers.
3. **Write the torture document.** Invented content, every question type, before
   any real paper is reproduced.
4. **Write the verifier.** Assert every constant against the torture document.
   This is what makes later change safe.
5. **Build the sample papers.** Now you can tell whether output is right.
6. **Build the UI last.** It is a front end onto a package that already works;
   building it earlier means debugging two things at once.

## The parts that transfer unchanged

- The deterministic vertical placement approach: struts everywhere, so box
  height and depth do not depend on content.
- `\nobreak` welding to keep a question whole across a page break, in preference
  to anything that measures remaining space.
- Page furniture drawn from the footer with a shortened `\textheight`, so a
  Notes box cannot collide with content.
- Writing answers to a side file at compile time (`\jobname.ans`) so the
  markscheme is generated rather than maintained.
- Accumulator-based two-column layouts.
- A local stdlib-only HTTP server driving `tectonic` for live preview.

## The parts that will not transfer

- Every millimetre in `ibenglishb.sty`. Re-measure all of them.
- Rubric strings.
- Mark totals, question counts, and the rule about which question types may
  follow which.
