# 3.2a maintenance branch

## Current maintenance development

The current `dev` branch starts from released master (`512612d`) and prepares
v3.2b. The v3.2a tag remains unchanged. The modular Word implementation lives on
`docxlike`; see BRANCHES.md.

Historical maintenance updates restored here:

- PR #282 (`e4c8096`, `3d51387`): undergraduate design selection and checkbox
  drawing, Shenzhen undergraduate use of Harbin layout, and Weihai chapter spacing.
  This PR originally targeted the old dev, not master.
- `c10c70f`: remove unconditional uppercasing from hitszthesis.bst so the class's
  bibliography controls take effect.
- `f17735d`, `022f6dc`: the Harbin master's interim-report example and cover fields.

`tests/BASELINE_REF` pins `c10c70f`, the original pre-modular implementation with
the official campus updates and bibliography correction. All 63 configurations
match its public values, PDF text/positions and links, including three actual
undergraduate design covers. The Harbin interim-report cover uses the original
`022f6dc` condition/wording changes. All 346 published v3.2a change records remain
in order; two v3.2b records describe these backports.

The original four default complete-example PDFs still match master baseline
`b241065`; eight wiseref configurations and native/public/history checks pass.
The older sections below record v3.2a preparation, not docxlike's v4 feature work.

Git base: upstream/master `b241065a8eb609e16c7004509facc9dda57901ef`.
Document-interface baseline: tag `v3.1e`, commit `366e37f5b3c621242229a8dc20fb41a47699b9a8`.

The release preserves the three original document classes, class options and their
defaults, flat `\hitsetup` keys, metadata commands and argument syntax, generated
fonts, layout, numbering, and bibliography interfaces. Runtime extraction,
namespaced image filenames, README, and example sources retain master's changes.
The three classes, both cfg files and the sample style use continuous expl3
syntax. The agreed accompanying changes are a LaTeX 2023-06-01 minimum and
automatic wiseref loading with template-language/name defaults and user overrides.

The template's public syntax remains the original syntax. This refactor does not
introduce a replacement setup syntax, a compatibility mode or a deprecation period.
The tests compare the refactored implementation against the original interface
and behavior. The historical filename `tests/compatibility.py` names that
equivalence check; it does not represent support for a second user syntax.

## Refactoring provenance

The first pushed candidate `fc504c7` passed the behavioral CI suite, but its
implementation audit was too weak: declarations were changed while numeric
scratch boxes, macro-based metadata and repeated layout policies remained.
That green run does not validate the subsequent implementation changes below.

The follow-up changes use owned `g__hit_info_*_tl` values, a vocabulary property
table, named caption/keyword/measurement boxes, and dimension registers for cover
measurement. Layout bodies read the owned state; the original metadata names
continue to read exported values at the existing document/package boundary.
The rule and page-number policies are shared
functions, and book geometry is applied from a profile table through one setup
function. Kernel and package hooks delegate to named implementation functions.
The original flat keys and their initialization order remain the regression target.

The maintenance source applies the existing local refactoring mechanics to the
original bodies: `50357f1` for conditionals, `1a72988` for token-preserving conversion,
`e1c1303`/`89abb36` for continuous expl3 with third-party catcode bridges, and
`0f34652`/`27b506e`/`26607f9` for command definitions and appendix accumulation.
Vocabulary declaration tables follow `ee0fa6b`/`b2fb0ab`; shared page-rule/number
policies follow `94a3b53`; cover and keyword helper organization follows `7f19d4b`.
The converter retains ordinary spaces, paragraph tokens and nonbreaking spaces.
The original active-tilde token in subfigure label prefixes is retained in aux files.
TikZ bare input and etoolbox rescanning use ordinary catcodes in one dedicated
section; the template implementation stays in expl3 syntax. These internal
wrappers handle third-party parsing, not a transition between user syntaxes.
The generated runtime audit rejects residual 2e definitions and conditionals
outside that third-party catcode section.

## Change history

The original master source contains 341 `\changes` records. All 341 retain their
version, date, description and relative order. A mechanically renamed internal
command in the 2025-03-03 cover record was restored to its original spelling;
historical descriptions refer to the implementation names used at that time.
`tests/change-history.py` checks the full, nested-brace records against the master
base, allowing only comment-prefix and whitespace formatting differences. Both
branch/PR CI and master CI run this check.

This release adds five records, all for v3.2a on 2026-10-11:

1. LaTeX3 internal refactoring and internal-function naming cleanup, preserving
   the original user syntax, defaults and layout.
2. The agreed LaTeX 2023-06-01 minimum.
3. The custom-equation-tag index fix needed with TeX Live 2026.
4. The documentation-only font fallback needed to build the manual.
5. The agreed wiseref loading and template name/language defaults.

Individual private-function renames, test cases and shared helpers do not add
separate change-history entries.

## Shared implementation with local dev

The comparison target is `/Users/wujunhao/hithesis` on local `dev`, HEAD
`a4ec635abffff4c6b1f384c459e1549e00ab3b7c`, including its existing uncommitted
changes. Neither the older upstream dev nor the fork's dev is this target.
The two committed branch tips currently share `v3.1e` (`366e37f`), not the
maintenance branch's master base. Working-tree edits do not change that ancestry.

Eight definitions now have identical parameter texts, protected/expandable status,
and implementation tokens in both trees. The following check ignores comments
and expl3 whitespace, but retains explicit space tokens and function names:

```sh
python3 tests/shared-implementation.py --dev /Users/wujunhao/hithesis
```

| Shared definitions in `hithesis.dtx` | Local dev module | Caller-specific behavior |
| --- | --- | --- |
| `\__hit_info_export:n`, `\__hit_info_set:nn`, `\__hit_info_define:nn` | `src/engine/hit-key-engine.dtx` | Export prefix is `hit@` on maintenance, `hit@info@` on dev; keys, field names and initialization remain branch-specific. |
| `\__hit_keywords_join:NNnnn` | `src/engine/hit-key-engine.dtx` | Maintenance expands input once, preserves item tokens and appends the original separators. Dev trims item edges and maintains distinct typesetting/PDF-metadata separators. |
| `\__hit_month_name:n` | `src/engine/hit-date.dtx` | Maintenance retains its original date punctuation and machine date. Dev retains ISO precision and its East-Asia date policy. |
| `\__hit_caption_separator:nn` | `src/engine/hit-caption.dtx` | Maintenance uses the original undergraduate switch. Dev also uses its Word grid and explicit separator overrides. |
| `\__hit_keywords_typeset:NNnnn` | `src/pages/hit-final-abstract.dtx` | Maintenance uses a normal hbox and mandatory hanging indentation. Dev retains its Word run box and per-abstract hanging switch. |
| `\__hit_clear_empty_double_page:N` | `src/flow/hit-final-matter.dtx` | Both delegate to the saved kernel double-page command. Maintenance retains its trailing space token; dev's independent odd-page policy is unchanged. |

The new metadata storage also serves dev's ordinary fields, raw date fields, and
title segments. Title/date implementations read the owned token lists. Dev's
page-local override machinery saves, restores and temporarily selects both owned
state and the original-name readouts, so cover overrides cannot leak into later pages
or global PDF metadata. The shared export-to-state property records this mapping.

Other modules have substantive dev feature changes. Its conditional vocabulary
resolver, title parser, Word cover/geometry/header implementations, bilingual
caption engine and page-number tristates are not identical maintenance bodies.
Their source locations are `src/engine/hit-key-engine.dtx`,
`src/engine/hit-title.dtx`, `src/pages/hit-final-{cover,titlepage}.dtx`,
`src/flow/hit-flow-geometry.dtx`, `src/flow/hit-final-pagestyle.dtx`, and
`src/engine/hit-caption.dtx`. Maintenance retains the original policies; dev retains
these extensions. The eight-definition check does not certify whole-branch code
identity or establish a Git ancestor relationship.

Local verification on 2026-10-12 after these shared changes:

- Maintenance: 60 equivalence cases, eight wiseref cases, five invalid-input
  comparisons, native/public-interface audits and all four complete example PDF
  comparisons passed. CTAN/TDS source provenance and contents passed too.
- Dev: all 11 targeted metadata/title/date/abstract/caption/bilingual/page-local
  fixtures passed before the final helper naming/blank-page changes. The final full
  XeTeX suite, including the new owned-state fixture, ran 110 fixtures: 102 passed
  and eight failed. The relevant targeted fixtures also passed in that full run;
  no existing expected `.tlg` was updated.
- The additional `112-shared-info-state` fixture checks owned state during local
  cover overrides, temporary global metadata views and restoration, plus deferred
  keyword tokens, and passed in the final full run. Both demo entries compiled
  successfully with LuaLaTeX
  (final: 32 pages; report: four pages). This is a compile check, not a comparison
  of dev PDFs against the original maintenance layout.
- Remaining dev differences: `25-caption-short-title` and `42-symbols-env` report
  a different font family; `29-stage-midterm` references the absent
  `\hit@if@shenzhen@doctor@interim@TF`; `39-postdoc-stage` references the absent
  `\g__hit_report_body_bool`; `56-format-keys`, `57-format-compute` and
  `61-format-white-skip` differ in Word style defaults/output; `70-tabularray`
  differs in font output and the missing historical `caption-en` key. The full dev
  suite is not green. Logs are `build/dev-shared-final-check.log` in the maintenance
  worktree and the corresponding `.diff` files in local dev's `build/test/`.
- Latest maintenance matrix:
  `/var/folders/g5/r0fc07p15cj0b269wxp0t5440000gn/T/opencode/hithesis-shared-maintenance-matrix/results.json`.
  Supplementary logs: `build/shared-examples.log`, `build/shared-ctan.log` and
  `build/example-regression.json`. Earlier Linux/minimum-kernel runs below precede
  these shared changes and are not fresh verification of this source snapshot.

The latest standalone package is `dist/hithesis-v3.2a-shared.zip`, 2,308,344 bytes,
with archive SHA256
`40f6702696bd2135727015fa4001a3f6668bc215921345aa27f8d39bd920316b`.
It contains the current source's runtime (source SHA256
`50de4812f7372952c3432d9fc072d25f6446e0398562ab430bd842712e1c5fcb`),
the updated manual and all four original example families. Freshly unpacked
examples compiled with empty TEXMFHOME/TEXMFLOCAL, loaded the bundled classes and
wiseref, and matched the master-baseline PDFs. The earlier
`/Users/wujunhao/hithesis/hithesis-v3.2a.zip` remains the first-candidate package.
Forty-two standalone variants and the combined example archive were also rebuilt.

The wording/history correction on 2026-10-12 rebuilt the manual and refreshed
`/Users/wujunhao/Desktop/hithesis-v3.2a-shared.zip`. Compared with the previously
tested shared package, the manual and comments in the class files changed;
class code is identical after stripping TeX comments, and all other payloads are
byte-identical. The 60-case/standalone PDF results above apply to that same runtime
code. The new history audit, public-interface/native audits, shared-definition
check, documentation/CTAN build, archive verification and workflow syntax/routing
checks passed for the wording update.
The internal-function naming cleanup is recorded in the existing refactor entry.
Its subsequent manual refresh leaves every non-manual ZIP member byte-identical
to the wording-corrected package.

The latest user-distribution update removes `wiseref.dtx` and `wiseref.ins` from
each of the four example families: eight files removed, with all 105 retained
files byte-identical to the naming-corrected package. Fresh standalone compilation
with empty TEXMFHOME/TEXMFLOCAL again passed for all four families and matched the
master-baseline PDFs. The 42 per-variant ZIPs, combined example ZIP and both
four-family ZIP names in `dist/` follow the same runtime/license-only policy.

## wiseref dependency

`scripts/dependencies.py` downloads the published v1.2026a source from the fixed
upstream commit `a2bf5597726c7e954c81f6afb2cb66b2e9334c49`, checks SHA256 for the
source, installer and license, extracts the runtime, and checks its SHA256 too.
CI uses `texlive/texlive:latest` and installs this checked dependency before testing.
The unmodified package retains Junhao Wu's copyright and LPPL 1.3c license.

The CTAN/TDS hithesis archive relies on the separately distributed wiseref package.
Standalone example archives include only `wiseref.sty` and `wiseref-LICENSE` for
this dependency. `make examples` copies the same checked payload and removes
verified source copies left by the earlier distribution rules. `wiseref.dtx` and
`wiseref.ins` remain in the build dependency cache, not in user archives.
The wiseref implementation is not embedded in `hithesis.dtx` or extracted by
`hithesis.ins`. The generated classes load the independently published package
with `\RequirePackage{wiseref}[2026/10/10]` and set template defaults through its
public setup command. The runtime and license in standalone bundles are unmodified
copies, kept beside each example entry so older TeX Live installations that lack
the package can find it locally. The LaTeX 2023-06-01 minimum still applies.
Template defaults use the actual figure, table, equation, appendix, algorithm and
listing names. English gaps and upright equation parentheses follow the template
language; explicit subsequent `\wiserefsetup` remains effective.

## Regression check

```sh
python3 -m pip install -r tests/requirements.txt
make dependencies
export TEXMFLOCAL="$PWD/build/dependencies/texmf"
make cls
python3 scripts/release.py baseline --destination build/baseline
python3 tests/native-runtime.py
python3 tests/public-interface.py --baseline build/baseline
python3 tests/change-history.py
python3 tests/error-cases.py --baseline build/baseline --work build/error-cases
make check BASELINE=build/baseline WORK=build/compatibility
python3 tests/wiseref.py --work build/wiseref
python3 scripts/release.py baseline --ref b241065a8eb609e16c7004509facc9dda57901ef --destination build/master-baseline
make compile-examples
python3 tests/compare-examples.py --baseline build/master-baseline
```

The baseline is an independently extracted v3.1e snapshot. The 60 configurations
cover the original 42 class/campus/degree/language combinations, math and geometry
options, boolean defaults and overrides, unknown class options forwarded to ctex,
the original sample style, custom equation tags, and last-line caption centering.
The fixture includes narrow multiline/color captions and a longtable caption.
Compare ordinary labels,
actual PDF text and character boxes, link targets, option values, and metadata.
For custom tags only, the baseline receives the documented local equation-index
workaround; the candidate must compile and retain the index entry without it.
Any failed or blocked configuration makes the check fail.

This is an interface/layout probe, supplemented by compiling the four complete
original example families. It does not test every possible user option combination.

## Packaging and publication

Local follow-up verification on 2026-10-11: all 60 configurations passed, as did the native
runtime audit, public argument/default checks and five invalid-input comparisons. Unknown setup keys
still fail; unsupported boolean values still warn and preserve the prior state,
matching 3.1e. Complete example PDFs match the unmodified master baseline for Chinese
book (58 pages), English book (14 pages), reports (3 pages), and reportplus
(5 pages). Character boxes and annotation rectangles are compared to four decimal
places; extracted text and link targets are compared exactly.

The original Chinese example has six unresolved glossary links, along with
existing example/font warnings. The comparison records those baseline links and
requires the candidate's links to remain identical; it does not treat the old
example as a warning-free document. The smaller interface probes require every
reference link target to exist.

Eight wiseref configurations passed: all three classes, both book languages,
the sample style, preloading, renamed captions, subsequent overrides, custom
equation tags, and starred references with no link annotations. Named link targets
are checked in the generated PDFs. A cached arm64 Linux TL2026 image additionally
passed the eight wiseref configurations and six interface/PDF comparisons.
The four class/language fixtures also passed with TL2023 historic
(LaTeX 2023-11-01, expl3 2024-02-20); that snapshot is newer than the exact declared
minimum. GitHub CI pulls and validates `texlive/texlive:latest` on each workflow run.

The follow-up also passed eight wiseref configurations and six targeted
interface/PDF cases in the cached arm64 Linux TL2026 image, including multiline
caption centering. Its four TL2023 fixtures passed with the same kernel dates
listed above. It needs its own hosted CI run after submission. Follow-up results:
`build/example-regression.json`,
`build/implementation-linux.log`, `build/lower-runtime/results.json`, and
`/var/folders/g5/r0fc07p15cj0b269wxp0t5440000gn/T/opencode/hithesis-l3-implementation-final/results.json`.
First-candidate supplementary records: `build/linux-regression.log`,
`build/lower-runtime/results.json`, and
`/var/folders/g5/r0fc07p15cj0b269wxp0t5440000gn/T/opencode/hithesis-32a-expl3-final-matrix/results.json`.
The follow-up CTAN/TDS contents and source provenance passed local checks.
The first candidate's `l3build upload --dry-run` passed CTAN remote validation.
The follow-up has only been built and checked locally; master CI performs its
upload validation as part of publication.

```sh
make ctan
make compile-examples
make changes
python3 scripts/release.py examples
l3build upload --dry-run
```

`make ctan` prepares a whitelist of source-only inputs and verifies runtime
filenames, version banners, source provenance and CTAN/TDS contents. Generated
files in examples, build outputs and Git metadata are excluded from CTAN inputs.
The installer extracts shared runtime files only; `make examples` distributes
them, as in master. CI uses the original `make_release_pkg.sh` for standalone
release archives; the Python packager allows equivalent local checks on macOS.
Release announcements are generated from the current-version `\\changes` entries.

The original Linux packaging script produced 42 standalone variants and one
combined archive. Dependency contents, CTAN/TDS source provenance and six runtime
version updates passed checks. The QQ archive preserves v3.1c's top-level layout:
`examples/`, `hithesis.pdf`, `README.md`. Its four independently extracted examples
compile with empty TEXMFHOME/TEXMFLOCAL and match the master-baseline PDFs; recorder
files confirm the bundled classes and wiseref runtime are used.

`.github/workflows/test_dev.yml` runs independently on pushes to `dev`,
`l3refactor` and every other non-master branch, on pull requests targeting master,
and on manual dispatch. It builds documentation and archives as test artifacts
with read-only repository permissions. It runs the existing dev branch's l3build
fixtures or the master-based maintenance equivalence suite as supplied by that
branch. It recognizes modular dev's `examples/demo/{final,report}.tex` entries and
builds them with LuaLaTeX; historical dev still uses the four older example paths.
The pull-request checkout tests the proposed merge with master.

`.github/workflows/test_texlive_latest.yml` follows master's publication sequence
and runs only on pushes to master. A push to `master`
with a new version passes the same checks, validates the CTAN payload, creates the
version tag and GitHub Release, and executes `l3build upload` with
`CTAN_UPLOAD=true`. Branch/tag/release changes happen only when that workflow is
actually run on master. CTAN confirmation email goes to
`andrew.junhao.wu@gmail.com`; author remains Chu Yanshuo. CTAN's current update
path is `/macros/xetex/latex/hithesis`.

CTAN upload success is distinct from CTAN approval and distribution availability.
If an upload fails after the GitHub tag/release exists, retry the failed upload
step or use `l3build upload` locally; do not bump the version merely to retry.

## Issue references

The original audit verified the existing README link update for
`hithesis/hithesis#274`. The issue is now closed (rechecked on 2026-10-11), so the
replacement commit can reference it with `Refs hithesis/hithesis#274`.
The runtime fixes have no matching verified open issue in the checked snapshot.
Details and the remaining open issues are recorded in
[tests/ISSUE-AUDIT.md](tests/ISSUE-AUDIT.md).

## Prepare l3refactor, test, then merge through a pull request

The original single-commit preparation commands below were used to create
`fc504c7`. At the user's request, the complete implementation, wording/history and
runtime-only distribution updates replace that candidate by amending the same
commit on `l3refactor`. The replacement keeps master base `b241065` as its parent
and is submitted with an explicit force-with-lease against the old remote SHA.
Require a fresh branch/PR CI run for this replacement. Use a squash merge to keep
the final complete migration as one commit on master.

Before the original single-commit preparation, upstream master had returned to the original
`b241065a8eb609e16c7004509facc9dda57901ef`; the four partial maintenance commits
are no longer on that branch and `v3.2a` has no remote tag. The prepared local
worktree then started at `17b1f0fa7a7ac6d2488bcbcaccaf69f6a18a934a` on
`l3refactor`; the first candidate was `fc504c7`, superseded by this replacement.
The historical preparation commands retained all prepared files, created one commit with the original
base as its parent, and push only the test branch. The checks stop if the local
HEAD, index, upstream HEAD or remote tag has changed. The branch push starts
the independent test workflow. After it passes, open a pull request to master;
the proposed merge receives the same test check before review and merging.
Merging into master starts the publication workflow automatically.

Replacement submission (amend and explicit lease authorized on 2026-10-12):

```sh
bash <<'SCRIPT'
set -e
W=/Users/wujunhao/hithesis/.claude/worktrees/3.2a-complete
OLD=fc504c772aee85e10b4eb8d773bf4fba56b95d9a
BASE=b241065a8eb609e16c7004509facc9dda57901ef
test "$(git -C "$W" branch --show-current)" = l3refactor
test "$(git -C "$W" rev-parse HEAD)" = "$OLD"
test "$(git -C "$W" rev-parse HEAD^)" = "$BASE"
test -z "$(git -C "$W" diff --cached --name-only)"
git -C "$W" status --short
git -C "$W" diff --stat
git -C "$W" log --oneline -10
git -C "$W" add -- hithesis.dtx MAINTENANCE.md \
  Makefile scripts/dependencies.py scripts/release.py \
  tests/compatibility.py tests/compatibility.tex \
  tests/native-runtime.py tests/public-interface.py tests/shared-implementation.py \
  tests/change-history.py .github/workflows/test_dev.yml \
  .github/workflows/test_texlive_latest.yml tests/error-cases.py
git -C "$W" diff --cached --check
git -C "$W" diff --cached --stat
git -C "$W" commit --amend --no-edit
test "$(git -C "$W" rev-parse HEAD^)" = "$BASE"
test "$(git -C "$W" rev-list --count "$BASE"..HEAD)" = 1
git -C "$W" push --force-with-lease="refs/heads/l3refactor:$OLD" \
  upstream HEAD:refs/heads/l3refactor
SCRIPT
```

Original single-commit preparation (historical instructions, already executed):

```sh
set -e
W=/Users/wujunhao/hithesis/.claude/worktrees/3.2a-complete
BASE=b241065a8eb609e16c7004509facc9dda57901ef
LOCAL_HEAD=17b1f0fa7a7ac6d2488bcbcaccaf69f6a18a934a
test "$(git -C "$W" branch --show-current)" = l3refactor
test "$(git -C "$W" rev-parse HEAD)" = "$LOCAL_HEAD"
test -z "$(git -C "$W" diff --cached --name-only)"
REMOTE=$(git -C "$W" ls-remote upstream refs/heads/master)
test "${REMOTE%%[[:space:]]*}" = "$BASE"
test -z "$(git -C "$W" ls-remote upstream refs/tags/v3.2a)"
git -C "$W" status --short
git -C "$W" diff --stat "$BASE"
git -C "$W" log --oneline -10
git -C "$W" reset --soft "$BASE"
git -C "$W" add -- .github/workflows/test_texlive_latest.yml \
  .github/workflows/test_dev.yml .gitignore \
  MAINTENANCE.md Makefile build.lua hithesis.dtx \
  scripts/release.py scripts/dependencies.py \
  tests/ISSUE-AUDIT.md tests/compare-examples.py tests/compatibility.py \
  tests/compatibility.tex tests/error-cases.py tests/public-interface.py \
  tests/requirements.txt tests/native-runtime.py tests/wiseref.py tests/wiseref.tex
git -C "$W" diff --cached --check
git -C "$W" diff --cached --stat
git -C "$W" commit -m "refactor: 完成 v3.2a LaTeX3 等价迁移并接入 wiseref" \
  -m "Refs hithesis/hithesis#274"
test "$(git -C "$W" rev-list --count "$BASE"..HEAD)" = 1
test "$(git -C "$W" rev-parse HEAD^)" = "$BASE"
test -z "$(git -C "$W" ls-remote upstream refs/tags/v3.2a)"
git -C "$W" push -u upstream HEAD:refs/heads/l3refactor
```

After the branch check succeeds, create the pull request with GitHub or:

```sh
gh pr create --repo hithesis/hithesis --base master --head l3refactor \
  --title "refactor: 完成 v3.2a LaTeX3 等价迁移并接入 wiseref" \
  --body "Refactor internal implementation while preserving the original public syntax and behavior; integrate wiseref as agreed. See MAINTENANCE.md for provenance and regression results."
```

Require the `TeX Live latest branch tests` check to pass on the proposed merge.
Choose squash merge to keep the complete migration as one new commit on master.
Updates to the PR rerun its tests.

## Make the released baseline an ancestor of dev

After the reviewed PR is squash-merged, call the resulting master commit `R`.
Save and review local dev's existing uncommitted work before merging; several
files also contain this shared-implementation update, and staging those whole
files includes the pre-existing user edits. Do not apply the maintenance branch's
submission command to the dev worktree.

With the intended dev changes committed and the worktree clean, fetch master and
merge it into dev. This keeps the published dev history while making `R` a real
ancestor of the new dev HEAD. Existing dev commits retain their existing parents.
Do not use an `ours` merge or resolve every conflict wholesale in favor of one
branch: keep the modular source assembly and dev features, port the tested shared
definitions, and reconcile CI/build changes against the actual dev layout.
Root-monolith deletion versus modification is an expected structural conflict.

Commands after the PR is merged and local dev work is saved:

```sh
bash <<'SCRIPT'
set -e
D=/Users/wujunhao/hithesis
test "$(git -C "$D" branch --show-current)" = dev
test -z "$(git -C "$D" status --porcelain)"
git -C "$D" fetch upstream master
R=$(git -C "$D" rev-parse upstream/master)
git -C "$D" show --stat "$R"
git -C "$D" merge --no-ff --no-commit "$R"
SCRIPT
```

The merge may stop for conflicts. Resolve and review them, run the shared
definition check against an extraction of commit `R`, run dev's regression and
feature checks, then commit the merge. The shared-definition checker belongs to
the maintained source checkout; pass the resulting dev tree with `--dev`.
Finally verify the exact reviewed baseline:

```sh
git merge-base --is-ancestor <R-sha> dev
git log --graph --oneline --decorate -20 dev
```

A zero exit status from `merge-base --is-ancestor` proves ancestry; it does not
replace source comparison or testing. Delete the merged `l3refactor` branch name
only after the PR is complete; deletion does not remove `R` or its descendants.
