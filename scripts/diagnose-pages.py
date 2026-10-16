#!/usr/bin/env python3
"""独立逐页诊断：按全文顺序一对一配行，重复行标歧义，不改变正式棘轮。"""
import argparse
from collections import Counter, defaultdict
import importlib.util
import json
from pathlib import Path
import statistics

spec = importlib.util.spec_from_file_location('page_fixture', Path(__file__).with_name('check-pages.py'))
pages = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pages)


def flatten(document, header_y=105.0):
    rows = []
    for page_number, page in enumerate(document, 1):
        for line_number, (y, x, text) in enumerate(page, 1):
            if pages.is_folio(text) or not text.strip('.…·'):
                continue
            if page_number > 1 and y < header_y:
                continue
            rows.append({'page': page_number, 'line': line_number, 'y': y, 'x': x, 'text': text})
    return rows


def align(reference, actual, tolerance=0.5):
    """Weighted sequence alignment; geometry never influences the matching score."""
    rtexts = Counter(row['text'] for row in reference)
    atexts = Counter(row['text'] for row in actual)
    rkeys = Counter(pages.key(row['text']) for row in reference)
    akeys = Counter(pages.key(row['text']) for row in actual)

    def quality(r, a):
        rt, at = r['text'], a['text']
        # Formula fragments and vertical single-character labels are not anchors.
        if min(len(rt), len(at)) < 4:
            return 0
        if rt == at:
            return 12 if rtexts[rt] == atexts[at] == 1 else 3
        if min(len(rt), len(at)) >= pages.KEY_LEN and pages.key(rt) == pages.key(at):
            return 5 if rkeys[pages.key(rt)] == akeys[pages.key(at)] == 1 else 1
        return 0

    n, m = len(reference), len(actual)
    scores = [[0] * (m + 1) for _ in range(n + 1)]
    choices = [bytearray(m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            weight = quality(reference[i - 1], actual[j - 1])
            paired = scores[i - 1][j - 1] + weight if weight else -1
            skipped_r, skipped_a = scores[i - 1][j], scores[i][j - 1]
            best = max(paired, skipped_r, skipped_a)
            scores[i][j] = best
            choices[i][j] = 3 if paired == best else (1 if skipped_r >= skipped_a else 2)
    pairs = []
    i, j = n, m
    while i and j:
        choice = choices[i][j]
        if choice == 3:
            pairs.append((i - 1, j - 1))
            i -= 1
            j -= 1
        elif choice == 1:
            i -= 1
        else:
            j -= 1
    pairs.reverse()

    matched = []
    for ri, ai in pairs:
        r, a = reference[ri], actual[ai]
        exact = r['text'] == a['text']
        repeated = (rtexts[r['text']] > 1 or atexts[a['text']] > 1) if exact else (
            rkeys[pages.key(r['text'])] > 1 or akeys[pages.key(a['text'])] > 1)
        dy = a['y'] - r['y']
        matched.append({'reference_index': ri, 'actual_index': ai, 'reference': r, 'actual': a,
                        'match': 'exact' if exact else 'prefix-only', 'ambiguous': repeated,
                        'dy': round(dy, 4), 'dx': round(a['x'] - r['x'], 4),
                        'within_tolerance': abs(dy) <= tolerance})
    rmatched = {ri for ri, _ in pairs}
    amatched = {ai for _, ai in pairs}
    page_map = defaultdict(Counter)
    for row in matched:
        if not row['ambiguous']:
            page_map[row['reference']['page']][row['actual']['page']] += 1
    unique_exact = [row for row in matched if row['match'] == 'exact' and not row['ambiguous']]
    return {'method': 'monotone one-to-one weighted text alignment; duplicate matches remain ambiguous',
            'tolerance_bp': tolerance,
            'summary': {'reference_lines': n, 'actual_lines': m, 'matched': len(matched),
                        'ambiguous_matches': sum(row['ambiguous'] for row in matched),
                        'prefix_only_matches': sum(row['match'] == 'prefix-only' for row in matched),
                        'unique_exact_matches': len(unique_exact),
                        'unique_exact_within_tolerance': sum(row['within_tolerance'] for row in unique_exact)},
            'page_map': {str(p): dict(sorted(counts.items())) for p, counts in sorted(page_map.items())},
            'matches': matched,
            'unmatched_reference': [r for k, r in enumerate(reference) if k not in rmatched],
            'unmatched_actual': [a for k, a in enumerate(actual) if k not in amatched]}


def print_report(report):
    print(json.dumps(report['summary'], ensure_ascii=False))
    for page, destinations in report['page_map'].items():
        matches = [r for r in report['matches'] if r['reference']['page'] == int(page) and not r['ambiguous']]
        shifts = [r['dy'] for r in matches if r['match'] == 'exact']
        median = statistics.median(shifts) if shifts else None
        print(f'参考第 {page} 页 → 实际页 {destinations}；唯一完整行 Δy 中位数={median}')
    ending = '独立棘轮另列通过结果。' if 'gate' in report else '结果不是正式棘轮。'
    print('重复行仅按顺序给出候选，仍标歧义；prefix-only 可能来自断行或内容不同。' + ending)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    reference = parser.add_mutually_exclusive_group(required=True)
    reference.add_argument('--fixture', type=Path)
    reference.add_argument('--reference-pdf', type=Path)
    parser.add_argument('--pdf', required=True, type=Path)
    parser.add_argument('--json', required=True, type=Path)
    parser.add_argument('--header-y', type=float, default=105.0,
                        help='除第一页外的页眉排除边界；无页眉受控稿使用 0')
    parser.add_argument('--tol', type=float, default=0.5)
    args = parser.parse_args()
    reference_doc = pages.read_fixture(args.fixture) if args.fixture else pages.pages(str(args.reference_pdf))
    report = align(flatten(reference_doc, args.header_y), flatten(pages.pages(str(args.pdf)), args.header_y), args.tol)
    report['inputs'] = {'fixture': str(args.fixture) if args.fixture else None,
                        'reference_pdf': str(args.reference_pdf) if args.reference_pdf else None,
                        'pdf': str(args.pdf), 'header_y': args.header_y}
    args.json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print_report(report)


if __name__ == '__main__':
    main()
