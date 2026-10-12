# 3.2a issue closure audit

Checked on 2026-10-11 against the open issues in `hithesis/hithesis` and the
`release/3.2a` worktree based on tag `v3.1e`. The API returned 26 open issues and
two pull requests (#289 and #302). This audit concerns the maintenance branch.

## Verified README issue

### #274 — README links to the writing guidelines and examples

The issue specifies five replacement URLs. All five are already present in the
v3.1e README and remain present in 3.2a. On the audit date each URL was fetched
successfully and returned the expected official page title/content:

| Content | Verified URL |
| --- | --- |
| Graduate thesis/practice writing guidelines | https://hitgs.hit.edu.cn/2025/0331/c17373a365618/page.htm |
| Master's example, science/engineering | https://hitgs.hit.edu.cn/2021/0513/c17373a317228/page.htm |
| Master's example, humanities/social sciences | https://hitgs.hit.edu.cn/2021/0508/c17373a317224/page.htm |
| Doctoral example, science/engineering | https://hitgs.hit.edu.cn/2021/0513/c17461a318415/page.htm |
| Doctoral example, humanities/social sciences | https://hitgs.hit.edu.cn/2021/0508/c17461a318413/page.htm |

There are no additional requirements in the issue comments (the comments endpoint
returned an empty list). This is verification and closure of an existing document
update, not a newly fixed LaTeX3/runtime defect. The school's attachment contents
were not downloaded or validated; the reported issue concerns the README links.

Rechecked after preparing the complete migration: the upstream API reports
`state=closed`, `state_reason=completed`, and `closed_at=2026-10-11T09:41:21Z`.
The replacement commit can use `Refs hithesis/hithesis#274`; a new closing action
is unnecessary. Use the fully qualified reference because local `origin` is a fork.

## Other issues from the initial open-issue snapshot

These are not resolved by the current maintenance diff. Existing fixes on the
feature-heavy development branch do not establish closure for this branch.

| Issue | Subject | Reason to keep open for this release |
| --- | --- | --- |
| #127 | General formatting discrepancy tracker | Ongoing aggregate tracker, not a single defect fixed here |
| #147 | Anonymous review mode | No anonymous-review interface added |
| #171 | Subfigure title spacing | Original subfigure implementation and spacing retained |
| #183 | Replace ntheorem with thmtools | ntheorem retained |
| #206 | Figure caption/body spacing | Original float/caption layout retained |
| #235 | Shenzhen master's proposal figure/table numbering | Existing opening-report numbering retained |
| #236 | Online/web bibliography entries | Original BibTeX styles and examples retained |
| #239 | Index alignment | Index layout not changed |
| #247 | Contents/bibliography/declaration formatting | Multi-part request not completed by this diff |
| #248 | Graduate thesis formatting update | Original headers, title pages and metadata formatting retained |
| #252 | Undergraduate formatting update | Original defaults/layout retained; full request not implemented |
| #265 | Shenzhen master's proposal header gap | Existing geometry retained |
| #273 | Shenzhen undergraduate proposal/interim templates | Updated school-template adaptation not included |
| #281 | Manually typed small-number alignment on TL2026 | Original paragraph/font layout retained; no targeted fix |
| #284 | Replace subfigure with subcaption | subfigure retained |
| #290 | Text area, lines/characters per page | Original geometry and spacing retained |
| #291 | Harbin undergraduate proposal/interim formatting | School-format corrections not included |
| #292 | Proof end symbols | ntheorem/enumitem end-list interaction not repaired |
| #293 | autoref theorem names | No new per-theorem autorefname definitions |
| #294 | Title-page table horizontal offset | Table end spacing retained; complete example character positions match baseline |
| #295 | LuaTeX support | XeLaTeX remains the supported engine |
| #296 | biblatex support | Original BibTeX/natbib path retained |
| #298 | Professional-degree title-page category label | Original degree/subject labels retained |
| #299 | tabularray recommendation | No table implementation/example migration |
| #300 | Graduate report heading formats | Original heading styles retained |

The two open pull requests (#289 originality/AI disclosure wording, #302 Shenzhen
undergraduate 2026 report adaptation) are not issue closure candidates.

The custom equation-tag index fix and documentation-font fallback have no
matching open issue in this snapshot. Describe them in the release notes without
attaching unrelated closing references such as #292 or #294.
