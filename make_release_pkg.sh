#!/usr/bin/env bash
# Package hithesis example templates into per-variant folders for release.
#
# Produces (under dist/):
#   chinese-<campus>-<type>-<version>
#   english-<campus>-<type>-<version>
#   reports-<campus>-<type>-<stage>-<version>
#   reportplus-<campus>-<type>-<stage>-<version>
#
# Each copy is the source template with the \documentclass `type`, `campus`
# (and `stage` where applicable) options rewritten to the variant, and with
# all build artifacts stripped. No recompilation happens here — the compiled
# PDF is intentionally excluded; run `make thesis` / `make report` first only
# as a build sanity check.
#
# Usage: bash make_release_pkg.sh <version>   # e.g. v3.2.1

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VERSION="${1:?usage: $0 <version>}"

STAGE_DIR="${ROOT}/dist"
DIST_NAME="hithesis-examples-${VERSION}"
DIST_DIR="${STAGE_DIR}/${DIST_NAME}"

rm -rf "${DIST_DIR}"
mkdir -p "${DIST_DIR}"

# package <src-dir> <main-tex> <dst-basename> <type> <campus> [<stage>]
#   Copies the example source into dist/<dst-basename>, rewrites the
#   \documentclass options, then strips build artifacts.
package() {
  local src="$1" main_tex="$2" dst="$3" type="$4" campus="$5" stage="${6:-}"

  cp -a "${ROOT}/${src}" "${DIST_DIR}/${dst}"

  local tex="${DIST_DIR}/${dst}/${main_tex}"
  # Values are matched as "any run of chars that are not `]`, `,` or `}`" so
  # that the option being the last one before `]{...}` does not swallow the
  # class name (e.g. `campus=harbin]{hithesisbook}`).
  sed -i \
    -e "s/type=[^],}]*/type=${type}/" \
    -e "s/campus=[^],}]*/campus=${campus}/" \
    -e "s/stage=[^],}]*/stage=${stage}/" \
    "${tex}"

  # Strip AUCTeX auto/ dirs (and any stray *.el files).
  find "${DIST_DIR}/${dst}" -type d -name auto -prune -exec rm -rf {} + 2>/dev/null || true
  # Strip LaTeX build artifacts.
  find "${DIST_DIR}/${dst}" -type f \( \
      -name '*.aux' -o -name '*.log' -o -name '*.out' -o -name '*.toc' \
      -o -name '*.bbl' -o -name '*.blg' -o -name '*.idx' -o -name '*.ind' \
      -o -name '*.ilg' -o -name '*.glo' -o -name '*.gls' -o -name '*.glg' \
      -o -name '*.thm' -o -name '*.toe' -o -name '*.hd' \
      -o -name '*.fdb_latexmk' -o -name '*.fls' -o -name '*.synctex.gz' \
      -o -name '*.xdv' -o -name '*.vrb' -o -name '*.lof' -o -name '*.lot' \
      -o -name '*.loe' -o -name '*.el' -o -name '*.run.xml' -o -name '*.bcf' \
    \) -delete
  # Compiled PDFs, but keep the placeholder scan empty-resolution.pdf.
  find "${DIST_DIR}/${dst}" -type f -name '*.pdf' ! -name 'empty-resolution.pdf' -delete
  # Stray makeindex/splitindex style copies.
  find "${DIST_DIR}/${dst}" -type f \( -name 'thesis.ist' -o -name 'report.ist' \) -delete
}

# ---------------------------------------------------------------------------
# hitbook: chinese / english (hithesisbook)
#   type    = doctor | master | bachelor | postdoc
#   campus  = shenzhen | weihai | harbin
# ---------------------------------------------------------------------------
for lang in chinese english; do
  for campus in shenzhen weihai harbin; do
    for type in doctor master bachelor postdoc; do
      package "examples/hitbook/${lang}" "thesis.tex" \
        "${lang}-${campus}-${type}-${VERSION}" "${type}" "${campus}"
    done
  done
done

# ---------------------------------------------------------------------------
# hitart: reports (hithesisart)
#   type   = doctor | master | bachelor
#   stage  = opening | midterm
#   campus = shenzhen | weihai | harbin
#   hithesisart does NOT support doctor+midterm+shenzhen -> that goes to
#   hithesisartplus below.
# ---------------------------------------------------------------------------
for campus in shenzhen weihai harbin; do
  for type in doctor master bachelor; do
    for stage in opening midterm; do
      if [ "${type}" = doctor ] && [ "${stage}" = midterm ] && [ "${campus}" = shenzhen ]; then
        continue
      fi
      package "examples/hitart/reports" "report.tex" \
        "reports-${campus}-${type}-${stage}-${VERSION}" "${type}" "${campus}" "${stage}"
    done
  done
done

# ---------------------------------------------------------------------------
# hitart: reportplus (hithesisartplus) — only doctor+midterm+shenzhen
# ---------------------------------------------------------------------------
package "examples/hitart/reportplus" "report.tex" \
  "reportplus-shenzhen-doctor-midterm-${VERSION}" doctor shenzhen midterm

# ---------------------------------------------------------------------------
# zip + checksum (checksum references the bare filename so `md5sum -c` works
# for anyone who downloads the pair into the same directory)
# ---------------------------------------------------------------------------
( cd "${STAGE_DIR}" && zip -r "${DIST_NAME}.zip" "${DIST_NAME}" )
( cd "${STAGE_DIR}" && md5sum "${DIST_NAME}.zip" > "${DIST_NAME}.zip.md5" )

echo "Created ${STAGE_DIR}/${DIST_NAME}.zip"
ls -l "${STAGE_DIR}/${DIST_NAME}.zip" "${STAGE_DIR}/${DIST_NAME}.zip.md5"
