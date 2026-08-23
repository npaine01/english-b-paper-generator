# `ibenglishb` — LaTeX templates for IB English B Paper 2

Reproduces the layout of the IB English B Paper 2 question booklets — reading
comprehension and listening comprehension — as a set of macros a generator can
emit. All geometry was measured off the vector PDFs of the 2023–2026 papers in
the parent folder; the generated output lands within ~0.2 mm of the originals.

## Files

| File | What it is |
|---|---|
| `ibenglishb.sty` | The package. All 18 question types, page furniture, mark accounting. |
| `specimens.tex` | One worked example of every question type, all original content. The gallery `make verify` measures against. |
| `reading-question-booklet.tex` | A complete 40-mark reading paper — 37 questions over three texts, original throughout. |
| `reading-text-booklet.tex` | The companion text booklet, with line and paragraph numbering. |
| `listening-booklet.tex` | A complete 25-mark listening paper, original throughout. |
| `paper1.tex` | Paper 1 — productive skills. One page, three tasks, three text-type options each. |
| `markscheme.tex` | The answer key: A4 landscape, one fully ruled table per text with its own total, generated from the booklet's `.ans` file. |

## The generator

```bash
make ui
```

Opens an editor in your browser. Add questions from the palette on the left,
fill them in, hit **Compile** (or Cmd-Enter) and the real PDF renders on the
right. It runs `tectonic` behind the scenes; leave the terminal running while
you work.

- Question numbers and the running mark total update as you type, and the
  total turns green when it matches your target.
- Fields exist for the things the IB always prints, so they cannot be
  forgotten: a line number on every vocabulary word and every referent
  question (typed as `8` or `8-9`, printed as `(line 8)` or `(lines 8–9)`),
  and a True/False choice plus the quotation on every justification question,
  which the markscheme renders as `T: "…"`.
- Stems gain their trailing ellipsis automatically wherever the IB uses one:
  sentence halves (22/22 in the corpus), complete-the-sentence (57/60), and
  multiple choice unless the stem is a direct question (63% ellipsis / 37%
  question mark). Typing `...` normalises to a single `…`, and a trailing full
  stop is replaced. Referent and short-answer stems are left alone — neither is
  consistent enough in the real papers to enforce.
- Each card warns about the things the IB is strict on — four options for
  reading multiple choice and three for listening, twice as many options as
  items in a matching block, a line or paragraph reference on the rubrics that
  need one.
- Rubrics are inserted for you whenever the question type changes, which is how
  the real papers work.
- **Save** / **Open** keep the paper as JSON; your work is also autosaved in
  the browser. **.tex** exports the source if you want to edit it by hand.

The editor covers Paper 2 reading and listening. Paper 1 and the text booklet
are written directly in LaTeX — see `paper1.tex` and `reading-text-booklet.tex`.

## Building

```bash
tectonic -X compile reading-question-booklet.tex
```

Works with XeLaTeX, LuaLaTeX (real Arial via `fontspec`) or pdfLaTeX (Helvetica
clone via `helvet`). The engine is detected automatically.

Compiling a booklet also writes `<jobname>.ans`, which `markscheme.tex` reads.
Compile the booklet first, then the markscheme.

The `.ans` file records where each text begins and what it was worth, so the
markscheme lays itself out the way the IB does: A4 landscape, one fully ruled
table per text starting on its own page, each with its own Total box. Long
tables continue onto the next page with the header row repeated. Add
`Accept` / `Do not accept` guidance with `\ibnote{<q>}{<accept>}{<reject>}`,
and `\ibbullets{\item …\item …}` for the IB's bulleted variants.

## Regression check

```bash
make verify
```

Compiles `test/torture.tex` — adversarial content sharing nothing with the
templates: options wrapping to three lines, matching items long enough to move
the answer-square column, wrapping stems, a tick table with long source labels,
and forced breaks in awkward places — then measures the output and asserts every
layout rule below, in the torture document *and* in all five shipped documents.
62 checks. Run it after any change to the package.

The rules it asserts, all measured off the 2022–2026 papers: option pitch
7.16 mm (last line of one option to the first of the next), 4.66 mm leading
inside a wrapped option, matching item pitch 9.80 mm, answer squares 3.09 mm
below an option baseline and 1.49 mm below a row baseline, answer box 15.01 mm
tall sitting 4.39 mm below the stem with its writing line 7.53 mm down, Notes
box top at 222.09 mm, no question split across a page, no page ending on a
rubric, no hyphenated word breaks, and ragged-right setting.

## Setting

The IB never splits a word across a line and never justifies. Both checked
against the corpus: of 4156 lines in the 2022–2026 papers, every hyphenated
line ending falls at a hyphen already in the text (URLs, and compounds like
pre-hyphenated compounds) — not one discretionary break. And measured line endings on
an image-free text page run 184.09–195.92 mm, with some overshooting the
measure, which justified setting cannot do.

So the package sets everything ragged right with word splitting off. Existing
hyphens remain legal break points, which is what the papers do with URLs.

## The three rules the package enforces for you

1. **Question numbers are automatic.** Never type a number. `\ibq` runs across
   the whole paper, so inserting a question renumbers everything below it.
2. **Marks are counted.** Declare the total with `\ibsetmaxmarks{40}`; if the
   questions don't add up you get a warning at the end of the log.
3. **Matching blocks need twice as many options as items.** The package warns
   if they don't — this is the IB's rule for every matching type and for
   identify-true-statements.

## Paper 1

```latex
\ibrubricpaperone
\ibtask{You recently completed an online course… Write a text in which you
  describe the course, evaluate what you learned, and make a recommendation.}
  {Email}{Interview}{Social media posting}
```

Three tasks, auto-numbered, each with its three text types centred in three
equal columns across the task's text block. Paper 1 is marked against three
assessment criteria rather than question by question, so nothing is added to
the mark total; the `.ans` file still records each task's text types.

Spacing follows the November 2024 revision — the IB widened the task blocks
that session, from 10.42/14.04 mm to 11.42/15.21 mm. `\ibpaperonelegacy`
restores the earlier values.

## Question types

### Reading (13 types)

| # | Type | Macro |
|---|---|---|
| 1 | Multiple choice | `\ibrubricmcq` + `ibmcq` env, four `\opt` |
| 2 | Identify true statements | `ibtrue` env, `2n` `\opt` |
| 3 | Matching questions with answers in the text | `\ibrubricmatchq` + `ibmatch` with `\mgap` |
| 4 | Matching headings with paragraphs | `\ibrubricheadings` + `ibmatch` with `\mgap` |
| 5 | Matching vocabulary | `\ibrubricvocab` + `ibmatch` with `\mitem` |
| 6 | Matching statements with people | `\ibrubricpeople` + `ibmatch` with `\mitem` |
| 7 | Matching two halves of a sentence | `\ibrubrichalves` + `ibmatch` with `\mitem` |
| 8 | Gap-filling exercise | `\ibrubricgapsummary` + `\ibsummary` + `ibmatch` with `\mgap` |
| 9 | Short answer | `\ibrubricshort` + `\ibshortq` |
| 10 | Finding words in the text | `\ibrubricfindword{…}` + `\ibfindwordq` |
| 11 | True or false with justification | `\ibrubrictf` + `\ibtfq` |
| 12 | Complete sentences using words from the text | `\ibrubriccomplete{…}` + `\ibcompleteq` |
| 13 | Identify to whom or to what words refer | `\ibrubricrefer` + `\ibreferq` |

### Listening (5 types)

| # | Type | Macro |
|---|---|---|
| 1 | Multiple choice | `\ibrubricmcq` + `ibmcq` env, **three** `\opt` |
| 2 | Identify true statements | `ibtrue` env |
| 3 | Matching statements with their sources | `\ibrubricsource` + `ibsource` env, `\srow` |
| 4 | Short answer | `\ibrubricshort` + `\ibshortq` |
| 5 | Gap-filling exercise | `\ibrubricgapfill` + `ibstimulus` + `\ibgapq` |

Reading types 9–13 and listening type 4 all produce the same 15.01 mm answer
box; they are separate macros only so the markscheme records which type each
question was.

## Writing questions

Every question macro takes the answer as an optional first argument. It is
never printed in the paper — it goes to the `.ans` file for the markscheme.

```latex
\ibrubricmcq
\begin{ibmcq}[D]{What is the text mainly about?}
  \opt{How Roda came to accept her disability}
  \opt{Roda's work as a Programme Officer}
  \opt{Roda's enjoyment of being a volunteer}
  \opt{How Roda's life experiences shaped her}
\end{ibmcq}
```

Identify-true-statements takes the number of marks as its second argument and
sets the rubric, the mark tag and the stack of answer boxes from it:

```latex
\begin{ibtrue}[A, B, D, H]{4}
  \opt{…}   % eight options for four marks
\end{ibtrue}
```

Matching blocks accumulate two independent columns, so items and options can
appear in any order. `\mgap` numbers itself and prints `[ – n – ]`; `\mitem`
takes its own left-hand text:

```latex
\ibrubricvocab
\begin{ibmatch}
  \mitem[C]{tempting \ibline{31}}
  \mitem[E]{promoting \ibline{38}}
  \mitem[A]{interacting \ibline{41}}
  \mopt{connecting} \mopt{interesting} \mopt{inviting}
  \mopt{employing}  \mopt{supporting}  \mopt{playing}
\end{ibmatch}
```

The square column positions itself just clear of the widest item, or at the
IB's usual 49.1 mm, whichever is further right.

The listening tick table:

```latex
\ibrubricsource
\begin{ibsource}{Whose opinion?}{Ali}{Stephanie}{Both}
  \srow[Both]{The issue requires immediate attention.}
  \srow[Ali]{Language is a big challenge.}
\end{ibsource}
```

Listening gap-fill is a stimulus document followed by numbered answer boxes.
Write `\ibgapnext` in the stimulus — it numbers itself from the question
counter, so the markers can never drift out of step with the boxes below —
and one `\ibgapq` per gap, in the same order:

```latex
\ibrubricgapfill
\ibstimcaption{Gamer profile:}
\begin{ibstimulus}          % [wavy] for the IB's wavy-bordered frame
  \item 2025 (ongoing): just completed her \ibgapnext
\end{ibstimulus}
\ibgapq[semi-final]
```

The package warns if a stimulus has a different number of `\ibgapnext` markers
than `\ibgapq` boxes. Use `\ibgap{7}` only if you need to force a number.

The "Give two answers" variant takes **two** optional answers and sets an (a)/(b)
pair inside a taller box:

```latex
\ibshortqtwo[mastery of skills][social recognition]%
  {What motivates people at the middle stage? Give two answers.}
```

## Cross-references into the text

| Macro | Output |
|---|---|
| `\ibpara{5}` | **paragraph** ▪5▪ (reverse-video badge) |
| `\ibparas{5}{6}` | **paragraphs** ▪5▪–▪6▪ |
| `\iblines{12}{23}` | **lines 12–23** |
| `\iblinesto{12}{23}` | **lines 12 to 23** |
| `\ibline{27}` | (line 27) |
| `\ibu{them}` | <u>them</u>, for referent questions |
| `\ibgap{7}` | **[ – 7 – ]** |

Whichever you use must match how the text booklet is numbered: `ibtextbody`
numbers every fifth line by default, or `ibtextbody[paragraphs]` leaves the
gutter to `\ibparnum{n}`.

## Text booklet

```latex
\ibtextlabel{A}
\ibtexttitle{The dos and don'ts of your first semester at university}
\begin{ibtextbody}[paragraphs]     % omit [paragraphs] to number lines by 5
  \ibparnum{1}
  Starting university is an exciting time…
\end{ibtextbody}
\ibglossnote{freshers}{students who have just started at a university}
```

Body text is indented 15 mm; the gutter carries either right-aligned line
numbers or the reverse-video paragraph badges. Close a booklet with the
bottom-anchored back matter:

```latex
\ibdisclaimer
\ibreferences{%
  \ibrefentry{Text B}{Music \& Arts, n.d. …\url{https://…}. Source adapted.}
  \ibrefentry{}{NikonShutterman, 2017. …}}
```

Put URLs in `\url{}` so they can break; they stay in Arial.

## Page furniture

```latex
\ibsetsession{2225\,--\,2258}   % top-right code on every page
\ibsetfootcode{08EP02}          % the paper's internal page code
\ibturnover                     % "Turn over / Tournez la page / Véase al dorso"
                                % on the page being finished
\ibnotesonall                   % listening: reserve the Notes box on every page
\ibblankpage                    % "Please do not write on this page."
```

`\ibcover{titles}{date}{duration}{instructions}{pages}{session}` sets an
IB-style cover; `ibinstructions` is the bulleted list environment it expects.

### Page breaks

Three guarantees, and one control.

**A question never splits.** A stem is welded to its answer area with an
infinite penalty; option lists, matching blocks, T/F boxes and tick tables are
each a single unbreakable box. A question that doesn't fit moves whole to the
next page. A rubric is welded to the questions it introduces, so it can never
be stranded at the foot of a page either. Verified by compiling every question
type at 24 different page offsets (90 pages): zero splits, zero orphaned
rubrics.

**Nothing collides with the Notes box.** `\ibnotesonall` makes it page
furniture — drawn on every page at the fixed IB position (222.09 mm) with the
body text block shortened to stop above it, so content cannot reach it.

**Each text starts a new page.** `\ibtextheading` and `\ibaudiotext` eject the
page themselves (the first one doesn't, since it is already on a fresh page).

**`\ibpagebreak`** forces a break wherever you want one — at the end of a
section, say. It only ever moves a break earlier than LaTeX would have chosen.

The paper's internal page code (`08EP01`, `08EP02`, …) numbers itself from the
page counter, so it can't drift. `\ibsetfootprefix{12EP}` changes the prefix;
`\ibsetfootcode{}` switches it off.

## Retuning

Every measured dimension is a length you can reset in the preamble, e.g.

```latex
\setlength\ibwboxheight{18mm}   % taller answer boxes for handwriting practice
\setlength\ibtfboxheight{26mm}
```

Rubric wording is configurable too, since the IB itself varies it between
sessions (`word`/`words`, `lines 12–23`/`lines 12 to 23`, colon or full stop):

```latex
\ibsetrubric{vocab}{What do the following words mean in the text?
  Choose the appropriate words from the list.}
```

## Package options

| Option | Effect |
|---|---|
| `answers` | Prints each answer in red beside its question — proofing mode. |
| `font=heros` | Use TeX Gyre Heros instead of Arial. |
| `nogeometry` | Don't set page geometry; the document supplies its own. |
| `decorations=false` | Don't load TikZ (disables the `wavy` stimulus frame). |

## Known gaps

- The cover page is IB-styled but English-only; the real papers repeat every
  instruction in French and Spanish. Add them to the `\ibcover` instructions
  argument if you want the full trilingual cover.
- Images inside texts and stimuli are not handled specially — use `graphicx`
  as normal.
- The wavy stimulus border approximates the IB's; it is a TikZ `snake`
  decoration, not the exact house shape.

## Engines and fonts

The package runs under **XeLaTeX**, **LuaLaTeX** or **pdfLaTeX**, and detects
which via `iftex`. Development and all measurement used
[Tectonic](https://tectonic-typesetting.github.io/) (a self-contained XeTeX),
which is the easiest to reproduce because it downloads what it needs:

```bash
brew install tectonic
tectonic -X compile reading-question-booklet.tex
```

**Font.** Real IB papers are set in Arial 11 pt. The package tries, in order:

| Engine | Font used |
|---|---|
| XeLaTeX / LuaLaTeX, Arial installed | Arial — matches the real papers exactly |
| XeLaTeX / LuaLaTeX, no Arial | TeX Gyre Heros, automatically, with a warning |
| pdfLaTeX | URW Nimbus Sans, via `helvet` |
| any, forced | `\usepackage[font=heros]{ibenglishb}` |

Arial ships with macOS and with Microsoft Office; a bare Linux box usually has
neither, and gets the fallback.

**The fallback is safe.** Heros and Nimbus Sans are Helvetica clones, and Arial
is metrically compatible with Helvetica, so character widths agree. Compiling
the same 10-page booklet both ways gives the same page count, the same number of
lines and the same line breaks — nothing reflows. Every vertical constant is
identical, because the grid comes from explicit lengths and struts rather than
from glyph metrics. What differs is under 0.6 mm of horizontal drift in
columns that size themselves to their content, and the glyph shapes themselves
(Arial's angled terminals versus Helvetica's horizontal ones).

**All three engines are tested, not just assumed.** Building every document
under pdfLaTeX (TeX Live 2026) and under XeTeX gives the same page counts, the
same line counts and the same 82 passing checks. Measured side by side:

| | XeTeX + Arial | pdfLaTeX + Nimbus Sans |
|---|---|---|
| Option pitch | 7.150 mm | 7.150 mm |
| Item pitch | 9.800 mm | 9.800 mm |
| Tick-table row pitch | 12.713 mm | 12.737 mm |
| Markscheme | 4 pp, landscape | 4 pp, landscape |

The `.ans` answer file is byte-identical between engines, so a booklet compiled
with one and keyed with the other works.

Use Arial if you want output indistinguishable from a real paper. Use the
fallback if you just want a correct exam.

## Licence

MIT — see [`LICENSE`](LICENSE).

It covers the code, the templates and the original sample papers. It grants no
rights over IB material (none is included), and implies no affiliation with or
endorsement by the International Baccalaureate Organization. See
[`NOTICE.md`](NOTICE.md).
