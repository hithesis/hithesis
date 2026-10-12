"""Check actual PDF positions, text, line breaks and pagination with correction off/on."""
import sys
import pdfplumber

off_path, on_path = sys.argv[1:]
deltas = {
    'FandolSong-Regular': 0.361328125 - 0.297,
    'FandolHei-Regular': 0.337890625 - 0.276,
    'FandolKai-Regular': 0.328125 - 0.287,
    'FandolFang-Regular': 0.341796875 - 0.296,
}
moved = unchanged = 0
with pdfplumber.open(off_path) as off, pdfplumber.open(on_path) as on:
    assert len(off.pages) == len(on.pages) >= 3, 'pagination changed'
    for p, q in zip(off.pages, on.pages):
        assert len(p.chars) == len(q.chars), 'glyph count changed'
        for a, b in zip(p.chars, q.chars):
            fa, fb = a['fontname'].split('+')[-1], b['fontname'].split('+')[-1]
            assert a['text'] == b['text'] and fa == fb, 'text or font changed'
            for key in ('x0', 'x1', 'size'):
                assert abs(a[key] - b[key]) < 0.002, f'{key} changed'
            actual = b['matrix'][5] - a['matrix'][5]
            expected = deltas.get(fa, 0) * a['size']
            assert abs(actual - expected) < 0.002, (a['text'], fa, actual, expected)
            if expected:
                moved += 1
            else:
                unchanged += 1
    assert moved > 100 and unchanged > 100, 'incomplete samples'
    print(f'BASELINE PDF PASS: {len(off.pages)} pages, {moved} shifted CJK glyphs, '
          f'{unchanged} unchanged Latin/math glyphs; positions within 0.002bp')
