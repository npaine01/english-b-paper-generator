# NOTICE — provenance and what is safe to share

## Short version

Every `.tex` file in this repository contains **original content**. No IB past
paper text is reproduced here, and no past paper PDFs are committed.

## The source material

The layout constants in `ibenglishb.sty` were derived by measuring real IB
Diploma Programme English B examination papers. Those papers were consulted
locally and are **not** part of this repository.

That distinction matters, because **IB past papers are not redistributable by
anyone.** Each paper carries a notice restricting reproduction and prohibiting
supply to third parties. A school or teacher who holds copies — through the
programme resource centre, a subscription service, or a departmental archive —
holds them for their own teaching use. That does not confer any right to
redistribute them, and it does not become a right merely because the papers are
old, widely circulated, or already available elsewhere. Nobody in the ordinary
chain of custody has distribution rights, so nothing derived from the papers'
*content* belongs in a shared repository.

## What is in this repository, and why it is fine

**The package, the UI, the tests and the build system.** Original code.

**The measurements.** `\ibboxside{5.8mm}`, a 7.53 mm dotted rule offset, a
222.09 mm Notes box, and the rest are *facts about a physical layout*. Facts are
not copyrightable, and a measurement is not a reproduction. `METHOD.md` records
how they were obtained.

**The rubric wording** — "Choose the correct answer", "The following statements
are either true or false", and so on. These are short functional instructions
that the IB itself publishes in its own subject documentation, and they are
necessary for the output to be recognisable as an English B paper. Their
inclusion is deliberate and, in our judgement, defensible.

**The sample papers.** `specimens.tex`, `reading-question-booklet.tex`,
`reading-text-booklet.tex`, `listening-booklet.tex` and `test/torture.tex` are
written for this project. The passages, the people, the places and the works
they cite are invented. Any resemblance to a real publication, person or work is
coincidental.

## History

Earlier revisions of the four sample files transcribed questions and texts from
real papers. That content served one purpose — it allowed generated output to be
diffed word-for-word against the original PDFs while the geometry was being
calibrated. Once the constants were locked into `ibenglishb.sty` and
`test/verify.py`, verification no longer depended on it, and it was replaced.

If you need to check output against a real paper, do it locally with your own
copy. Do not commit the result.
