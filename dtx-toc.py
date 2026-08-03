#!/usr/bin/env python3
"""Print or embed a live table of contents for hithesis.dtx.

Scans existing anchors (no markers added to source):
  1. Major section dividers: `% %%%%%%%%` followed by `% name`
  2. Module guards: `%<*name>` ... `%</name>`

Usage:
    python3 dtx-toc.py                    # print full TOC to stdout
    python3 dtx-toc.py modules            # print only module guards
    python3 dtx-toc.py sections           # print only major sections
    python3 dtx-toc.py write              # embed TOC block at top of dtx
    make toc          (= print)
    make toc-update   (= write)

The embed block uses `% ^^A` comment-of-comment lines, invisible to both LaTeX
(when rendering the manual) and docstrip (when generating .cls/.sty). Wrapped
in `<<<BEGIN-DTX-TOC>>>` / `<<<END-DTX-TOC>>>` sentinels for idempotent rewrite.

Runs on macOS / Linux / Windows (Python 3.6+, no external dependencies).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DTX = ROOT / "src" / "hithesis.dtx"

BEGIN_SENTINEL = "% ^^A <<<BEGIN-DTX-TOC>>>"
END_SENTINEL = "% ^^A <<<END-DTX-TOC>>>"


def collect_sections(lines):
    """Find banner-marked major sections (% %%%%% line followed by % title)."""
    banner = re.compile(r"^% %%%%+\s*$")
    # Reject titles that are themselves rule lines (^^A or %%%%)
    title = re.compile(r"^% ([^%^\\\s]\S*(?: \S+)*)\s*$")
    out = []
    for i in range(len(lines) - 1):
        if banner.match(lines[i]):
            m = title.match(lines[i + 1])
            if not m:
                continue
            t = m.group(1).strip()
            if t.startswith("^^A") or t.startswith("%") or "\\end{macrocode}" in t:
                continue
            out.append((i + 2, t))
    return out


def collect_modules(lines):
    """Find module guards. (first_open, name, last_close, block_count)."""
    open_re = re.compile(r"^%<\*([a-z][a-zA-Z0-9-]*)>\s*$")
    close_re = re.compile(r"^%</([a-z][a-zA-Z0-9-]*)>\s*$")
    first = {}
    last = {}
    count = {}
    for i, line in enumerate(lines, start=1):
        mo = open_re.match(line)
        if mo:
            name = mo.group(1)
            if name not in first:
                first[name] = i
            count[name] = count.get(name, 0) + 1
            continue
        mc = close_re.match(line)
        if mc:
            last[mc.group(1)] = i
    return sorted(
        ((first[n], n, last.get(n, first[n]), count[n]) for n in first),
        key=lambda r: r[0],
    )


def format_toc(lines, prefix="% ^^A "):
    """Build the TOC text as a list of lines (no trailing newlines), with prefix."""
    out = []
    rule = prefix + "=" * 70
    out.append(BEGIN_SENTINEL)
    out.append(rule)
    out.append(prefix + "AUTO-GENERATED TOC for hithesis.dtx")
    out.append(prefix + "  refresh with: make toc-update  (or: python3 dtx-toc.py write)")
    out.append(prefix + "  invisible to LaTeX/docstrip (uses ^^A comment-of-comment)")
    out.append(rule)
    out.append(prefix.rstrip())
    out.append(prefix + "Major sections")
    for ln, title in collect_sections(lines):
        out.append(prefix + f"  {ln:>6}   {title}")
    out.append(prefix.rstrip())
    out.append(prefix + "Modules (first .. last; block count)")
    for first_ln, name, last_ln, n in collect_modules(lines):
        suffix = "block" if n == 1 else "blocks"
        out.append(prefix + f"  {first_ln:>6}   {name:<24} {first_ln}-{last_ln} ({n} {suffix})")
    out.append(prefix.rstrip())
    out.append(prefix + f"Total: {len(lines)} lines.")
    companion = companion_summary()
    if companion:
        out.append(prefix + f"Companion: {companion}")
    out.append(rule)
    out.append(END_SENTINEL)
    return out


def find_insertion_point(lines):
    """Where to insert TOC when no existing sentinels: right after the license `% \\fi`."""
    for i, line in enumerate(lines):
        if line.strip() == "% \\fi":
            return i + 1
    # Fallback: very top
    return 0


def write_toc(lines):
    """Insert or replace the TOC block in `lines`, return new list of lines."""
    toc_block = format_toc(lines)
    begin_idx = end_idx = None
    for i, line in enumerate(lines):
        if line.rstrip() == BEGIN_SENTINEL:
            begin_idx = i
        elif line.rstrip() == END_SENTINEL:
            end_idx = i
            break
    if begin_idx is not None and end_idx is not None:
        return lines[:begin_idx] + toc_block + lines[end_idx + 1:]
    if begin_idx is not None or end_idx is not None:
        raise RuntimeError(
            "Found only one TOC sentinel; refuse to proceed. Remove the orphan sentinel and retry."
        )
    insert = find_insertion_point(lines)
    return lines[:insert] + [""] + toc_block + [""] + lines[insert:]


def companion_summary():
    """One-line summary of hithesis-eps.dtx if it exists."""
    eps = ROOT / "hithesis-eps.dtx"
    if not eps.exists():
        return None
    eps_lines = eps.read_text(encoding="utf-8").splitlines()
    eps_mods = collect_modules(eps_lines)
    names = ", ".join(m[1] for m in eps_mods)
    return f"hithesis-eps.dtx ({len(eps_lines)} lines): {names}"


def main():
    if not DTX.exists():
        print(f"FATAL: {DTX} not found", file=sys.stderr)
        return 1

    text = DTX.read_text(encoding="utf-8")
    # Preserve trailing newline state
    keep_trailing_nl = text.endswith("\n")
    lines = text.splitlines(keepends=False)

    mode = sys.argv[1] if len(sys.argv) > 1 else "full"

    if mode == "write":
        new_lines = write_toc(lines)
        out = "\n".join(new_lines)
        if keep_trailing_nl:
            out += "\n"
        DTX.write_text(out, encoding="utf-8")
        # Re-read for accurate count
        new_total = len(new_lines)
        print(f"TOC embedded into hithesis.dtx (now {new_total} lines).")
        return 0

    if mode == "sections":
        for ln, title in collect_sections(lines):
            print(f"{ln:>6}  {title}")
    elif mode == "modules":
        for first_ln, name, last_ln, n in collect_modules(lines):
            suffix = "block" if n == 1 else "blocks"
            print(f"{first_ln:>6}  {name:<24}  {first_ln}-{last_ln}  ({n} {suffix})")
    elif mode == "full":
        print("==== Major sections ====")
        for ln, title in collect_sections(lines):
            print(f"{ln:>6}  {title}")
        print()
        print("==== Modules (first .. last; block count) ====")
        for first_ln, name, last_ln, n in collect_modules(lines):
            suffix = "block" if n == 1 else "blocks"
            print(f"{first_ln:>6}  {name:<24}  {first_ln}-{last_ln}  ({n} {suffix})")
        print()
        print(f"Total: {len(lines)} lines.")
        companion = companion_summary()
        if companion:
            print(f"Companion: {companion}")
    else:
        print(f"Usage: {sys.argv[0]} [full|sections|modules|write]", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
