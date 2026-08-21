#!/usr/bin/env bash
# Package hithesis example templates into per-variant folders for release.
#
# Produces (under dist/):
#   <variant>.zip               # one zip per template, version-independent name
#   hithesis-examples.zip       # all templates in one zip, version-independent
#   hithesis-examples.zip.md5   # checksum of the combined zip
#   MD5SUMS                     # checksums of every *.zip
#
# Variants (the folder inside each <variant>.zip is <variant>-<version>):
#   chinese-<campus>-<type>                     (12)
#   english-<campus>-<type>                     (12)
#   reports-<campus>-<type>-<stage>             (17)
#   reportplus-shenzhen-doctor-midterm          (1)
#
# Zip names are version-independent so that
#   https://github.com/hithesis/hithesis/releases/latest/download/<name>.zip
# always points at the newest release, letting the GitHub Page stay static.
#
# Usage: bash make_release_pkg.sh <version>   # e.g. v3.2.1

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VERSION="${1:?usage: $0 <version>}"

STAGE_DIR="${ROOT}/dist"
DIST_DIR="${STAGE_DIR}/hithesis-examples"

rm -rf "${STAGE_DIR}"
mkdir -p "${DIST_DIR}"

# package <src-dir> <main-tex> <stable-name> <type> <campus> [<stage>]
#   Copies the example source into dist/hithesis-examples/<stable-name>-<version>,
#   rewrites the \documentclass options, then strips build artifacts.
package() {
  local src="$1" main_tex="$2" dst="$3" type="$4" campus="$5" stage="${6:-}"
  local folder="${dst}-${VERSION}"

  cp -a "${ROOT}/${src}" "${DIST_DIR}/${folder}"

  local tex="${DIST_DIR}/${folder}/${main_tex}"
  # Values are matched as "any run of chars that are not `]`, `,` or `}`" so
  # that the option being the last one before `]{...}` does not swallow the
  # class name (e.g. `campus=harbin]{hithesisbook}`).
  sed -i \
    -e "s/type=[^],}]*/type=${type}/" \
    -e "s/campus=[^],}]*/campus=${campus}/" \
    -e "s/stage=[^],}]*/stage=${stage}/" \
    "${tex}"

  # Strip AUCTeX auto/ dirs (and any stray *.el files).
  find "${DIST_DIR}/${folder}" -type d -name auto -prune -exec rm -rf {} + 2>/dev/null || true
  # Strip LaTeX build artifacts.
  find "${DIST_DIR}/${folder}" -type f \( \
      -name '*.aux' -o -name '*.log' -o -name '*.out' -o -name '*.toc' \
      -o -name '*.bbl' -o -name '*.blg' -o -name '*.idx' -o -name '*.ind' \
      -o -name '*.ilg' -o -name '*.glo' -o -name '*.gls' -o -name '*.glg' \
      -o -name '*.thm' -o -name '*.toe' -o -name '*.hd' \
      -o -name '*.fdb_latexmk' -o -name '*.fls' -o -name '*.synctex.gz' \
      -o -name '*.xdv' -o -name '*.vrb' -o -name '*.lof' -o -name '*.lot' \
      -o -name '*.loe' -o -name '*.el' -o -name '*.run.xml' -o -name '*.bcf' \
    \) -delete
  # Compiled PDFs, but keep the placeholder scan empty-resolution.pdf.
  find "${DIST_DIR}/${folder}" -type f -name '*.pdf' ! -name 'empty-resolution.pdf' -delete
  # Stray makeindex/splitindex style copies.
  find "${DIST_DIR}/${folder}" -type f \( -name 'thesis.ist' -o -name 'report.ist' \) -delete
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
        "${lang}-${campus}-${type}" "${type}" "${campus}"
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
        "reports-${campus}-${type}-${stage}" "${type}" "${campus}" "${stage}"
    done
  done
done

# ---------------------------------------------------------------------------
# hitart: reportplus (hithesisartplus) — only doctor+midterm+shenzhen
# ---------------------------------------------------------------------------
package "examples/hitart/reportplus" "report.tex" \
  "reportplus-shenzhen-doctor-midterm" doctor shenzhen midterm

# ---------------------------------------------------------------------------
# zip: one per variant (stable name) + one combined (stable name) + checksums
# ---------------------------------------------------------------------------
for folder in "${DIST_DIR}"/*/; do
  folder="${folder%/}"
  name="${folder#"${DIST_DIR}"/}"        # e.g. chinese-harbin-doctor-v3.2.1
  stable="${name%-${VERSION}}"           # e.g. chinese-harbin-doctor
  ( cd "${DIST_DIR}" && zip -r "${STAGE_DIR}/${stable}.zip" "${name}" )
done

( cd "${STAGE_DIR}" && zip -r "hithesis-examples.zip" "hithesis-examples" )
( cd "${STAGE_DIR}" && md5sum "hithesis-examples.zip" > "hithesis-examples.zip.md5" )
( cd "${STAGE_DIR}" && md5sum *.zip > MD5SUMS )

echo "Created ${STAGE_DIR}:"
ls "${STAGE_DIR}"/*.zip | sed "s#${STAGE_DIR}/##" | sort
echo
echo "Total zips: $(ls "${STAGE_DIR}"/*.zip | wc -l)"
