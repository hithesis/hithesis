"""Audit owned implementation state and explicit third-party catcode boundaries."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_ISLANDS = {
    'hithesisbook.cls': 8, 'hithesisart.cls': 0, 'hithesisartplus.cls': 2,
    'hithesisbook.cfg': 0, 'hithesisart.cfg': 0, 'hithesis.sty': 0,
}
LEGACY = re.compile(r'\\(?:[egx]?def|let|newcommand|renewcommand|newenvironment|renewenvironment|'
    r'newif|ifhit@[A-Za-z]+|ifnum|ifdim|ifcase|newlength|newbox|setlength|addtolength|'
    r'g@addto@macro)(?![A-Za-z@_:])')


def without_bridges(text):
    declaration = re.compile(r'\\csname cs_new_protected:Npn\\endcsname '
        r'\\hit@legacy@patch@[a-z]\{')
    while match := declaration.search(text):
        at, depth = match.end(), 1
        while depth:
            char = text[at]
            if char == '\\':
                at += 2
                continue
            depth += (char == '{') - (char == '}')
            at += 1
        text = text[:match.start()] + text[at:]
    return text


for filename, islands in EXPECTED_ISLANDS.items():
    text = (ROOT / filename).read_text()
    text = '\n'.join(line.split('%', 1)[0] for line in text.splitlines())
    assert re.search(r'\\ProvidesExpl(?:Class|File|Package)', text), filename
    assert text.count('\\ExplSyntaxOff') == text.count('\\ExplSyntaxOn') == islands, filename
    core = without_bridges(text)
    assert not LEGACY.search(core), (filename, 'Unmigrated implementation', LEGACY.search(core)[0])
    assert not re.search(r'\\setbox\s*[012]\b|\\sbox\s*\\@tempboxa', core), (
        filename, 'Borrowed numeric/LaTeX scratch boxes in owned implementation')
    if filename.endswith('.cls'):
        assert r'\NeedsTeXFormat{LaTeX2e}[2023/06/01]' in core, filename
        assert r'\RequirePackage {wiseref} [2026/10/10]' in core, filename
        assert r'\tl_gset:cn {g__hit_info_#1_tl}' in core, filename
        assert r'\prop_new:N \g__hit_terms_prop' in core, filename
        assert r'\box_new:N \l__hit_measure_box' in core, filename
        assert not re.search(r'\\hit@[A-Za-z]+(?:true|false)\b', core), filename
    if filename.endswith('.cfg'):
        assert r'\__hit_terms_set:nn' in core, filename
        assert not re.search(r'\\cs_(?:new|set|gset)(?:_nopar)?:Npn\s*\\hit@', core), (
            filename, 'Vocabulary stored as a series of original-name macros')
    if filename == 'hithesisbook.cls':
        assert r'\box_new:N \l__hit_caption_lines_box' in core
        assert r'\box_new:N \l__hit_keywords_label_box' in core
        assert r'\prop_new:N \c__hit_book_geometry_prop' in core
        assert r'\__hit_page_number_current:' in core
    print(filename, 'Native declarations, minimum kernel and isolated third-party bridges: PASS')
