# hithesis 3.1e compatibility

## Result

**Wiseref works with hithesis 3.1e when the reference language is selected
explicitly.** XeLaTeX is required by the legacy classes themselves.

TeX Live 2026: **46 configurations inspected, 44 PASS, 2 BLOCKED_BASELINE,
0 wiseref regressions**. The two blocked cases are the original book class's
custom equation tags; a separately tested local equation-index configuration
passes. No release cls/cfg file was modified.

Revalidated on **2026-10-11** with wiseref **v1.2026a (2026-10-10)**,
repository commit `a2bf559`, XeTeX `0.999998` / TeX Live 2026,
LaTeX `2026-06-01`, and expl3 `2026-07-20`. The candidate's SHA-256 was
`10c1be20c0c28fca6c66200f91cb885a15c7597639ca4d7192d7031632909d2f`.
The source snapshot was freshly exported and extracted for this run. Coverage
and matching source/candidate hashes were verified across both result batches.

| Configuration | Cases | Result |
| --- | ---: | --- |
| hithesisbook: bachelor/master/doctor/postdoc, three campuses, Chinese/English | 24 | PASS |
| hithesisart: representative opening/midterm reports, all three campuses | 9 | PASS |
| hithesisartplus: Shenzhen doctoral midterm, its supported configuration | 1 | PASS |
| Wiseref before documentclass, all three legacy class families | 4 | PASS |
| Book newtxmath=false, Chinese/English | 2 | PASS |
| Book with the original hithesis.sty, including algorithms/listings | 2 | PASS |
| Book custom tags, original configuration, Chinese/English | 2 | BLOCKED_BASELINE |
| Book custom tags with the local equation-index fix, Chinese/English | 2 | PASS |

## Version and isolation

Source is the local upstream tag `v3.1e`, commit
`366e37f5b3c621242229a8dc20fb41a47699b9a8`, exported with `git archive`.
Its `hithesis.ins` was extracted with XeTeX. The actual class banner says v3.1e;
results also record source hashes and verify the loaded class matches the
isolated generated file. Modern hithesis.cls and docxlike are rejected.

The legacy classes are `hithesisbook`, `hithesisart`, and `hithesisartplus`.
They explicitly reject non-XeTeX engines. Unicode fonts use the supported
`fontset=fandol`; Western/math fonts follow the original class defaults.

## What was checked

Each configuration has four builds: ordinary baseline, wiseref loaded but unused,
default-auto wref calls, and explicitly configured wref calls.

Baseline and observation must have identical ordinary auxiliary labels, PDF text,
character boxes and ordinary links. Configured references preserve raw numbers,
including hyphenated figure/equation numbers and `1-4 (a)` legacy subfigure forms.
Types are checked for figures, tables, equations, ntheorem declarations, unnumbered
proofs/headings, list items and footnotes; book appendices are also checked.
Linked numbers must point to existing targets, starred/none references have no
links, and range/mixed references have expected text. The original sample sty
is separately exercised with real algorithm2e and listings counters.

This is a reference-integration matrix, not a build of every complete thesis or
cover page. The report-class configurations respect their actual limitations;
artplus is only tested in its supported Shenzhen doctoral midterm configuration.

## Recommended setup

Chinese book:

```latex
\documentclass[fontset=fandol,type=master,campus=harbin]{hithesisbook}
\usepackage{wiseref}
\wiserefsetup{lang=zh}
```

To use the book class's own equation name (usually `公式`) rather than the
Chinese profile's `式`, add:

```latex
\wiserefsetup{equation={prefix={\equationname}}}
```

Chinese reports likewise use `lang=zh`. English books use the legacy class option
`language=english` and wiseref's `lang=en`:

```latex
\documentclass[fontset=fandol,type=master,campus=shenzhen,language=english]{hithesisbook}
\usepackage{wiseref}
\wiserefsetup{lang=en}
```

3.1e loads ctex with `scheme=plain` and does not contain the modern hithesis wiseref
adapter. Default `lang=auto` therefore selects the English fallback even in a
Chinese thesis. Existing Chinese figure/table/theorem names can still be borrowed,
but connectors, ranges, chapter names and list/footnote terms can remain English.
For example, the recorded Chinese default-auto output included
`图1-1,表1-1and公式(1-1)` and `Chapter1`; explicit language configuration resolves
these inconsistencies. This is a setup requirement, not automatic 3.1e language
detection.

## Original custom-tag issue

Without wiseref, a book equation using `\tag{S}` fails while the equation index
expands a hyperref anchor command inside a protected write. The trace mentions
`\Hy@raisedlink`, `\HyperRaiseLinkLength`, and `\equcaption`.

The following local preamble wrapper, applied equally to baseline and wiseref
builds, prevents the anchor command from entering the equation index:

```latex
\makeatletter
\let\WiseOriginalEqucaption\equcaption
\renewcommand\equcaption[1]{%
  \begingroup
  \let\Hy@make@anchor\@empty
  \WiseOriginalEqucaption{#1}%
  \endgroup}
\makeatother
```

It preserves index entries (the `S` entry was checked), numbers and equation
links; it does not remove equation-index generation or modify installed classes.
With this configuration, custom tags and tag* references passed in Chinese and
English. The rendered 3.1e tag* displays have no parentheses and wiseref retains
that form. This workaround is specific to the inspected 3.1e/hyperref environment.

## Reproduction

From the hithesis repository, after exporting v3.1e and running
`xetex hithesis.ins` in that snapshot (the runner uses the sibling latex-wiseref repository):

```sh
python3 tests/wiseref/legacy-3.1e.py --source /path/to/extracted-v3.1e \
  --work /tmp/wiseref-hithesis-31e
# Focused ordinary-numbering check:
python3 tests/wiseref/legacy-3.1e.py --source /path/to/extracted-v3.1e \
  --work /tmp/wiseref-hithesis-31e-smoke \
  --cases book-master-harbin-zh book-master-shenzhen-en \
          art-bachelor-weihai-opening artplus-doctor-shenzhen-midterm
```

Work directories must not exist. The full matrix exits nonzero for the two raw
custom-tag baseline failures; statuses distinguish those from wiseref failures.
The 2026-10-11 recorded matrix is at
`/var/folders/g5/r0fc07p15cj0b269wxp0t5440000gn/T/opencode/wiseref-hithesis-31e-20261011-current/results.json`.
Its sibling `matrix/` and `remaining/` directories contain the isolated builds,
PDFs, auxiliary records, input manifests, and logs. The first invocation reached
the command timeout after recording 27 passes; the remaining 19 configurations
were completed in a second invocation (17 PASS, 2 BLOCKED_BASELINE). The merged
record verifies all 46 configurations are present exactly once.
Other TeX Live releases and every possible 3.1e setting were not tested.
