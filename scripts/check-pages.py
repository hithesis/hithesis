#!/usr/bin/env python3
"""逐页对拍：两份 PDF 各页的行数、首末行文本与基线，以及标题前后的基线距分布。

用法：check-pages.py 参考.pdf 我们.pdf [--pages 17-27] [--ours-pages 17-27]
      check-pages.py --headings 参考.pdf 我们.pdf     # 只看标题前后的基线距分布

页面单位是 bp。页眉页脚（y 在 100 以下、770 以上）不算。标题按字号认：18 章、15 节、
14 条、12 正文（本科与硕博范例都是这套字号）。
"""
import argparse, html, re, subprocess
from collections import Counter, defaultdict

CHAR_RE = re.compile(r'<char quad="([\d.]+) [\d.]+ [\d.]+ [\d.]+ [\d.]+ [\d.]+ [\d.]+ [\d.]+" x="([\d.]+)" y="([\d.]+)"[^>]*c="([^"]*)"')
FONT_RE = re.compile(r'<font name="([^"]+)" size="([\d.]+)">(.*?)</font>', re.S)
PAGE_RE = re.compile(r'<page[^>]*>(.*?)</page>', re.S)
KIND = {18.0: 'H1', 15.0: 'H2', 14.0: 'H3', 12.0: 'body', 10.5: 'small', 9.0: 'foot'}


def lines(pdf, lo=100.0, hi=770.0):
    out = subprocess.run(['mutool', 'draw', '-q', '-F', 'stext', '-o', '-', pdf],
                         capture_output=True, text=True).stdout
    res = []
    for pi, pm in enumerate(PAGE_RE.finditer(out), 1):
        rows = {}
        for fm in FONT_RE.finditer(pm.group(1)):
            fs = round(float(fm.group(2)), 1)
            for cm in CHAR_RE.finditer(fm.group(3)):
                y = round(float(cm.group(3)), 1)
                rows.setdefault(y, []).append((float(cm.group(2)), html.unescape(cm.group(4)), fs))
        body = []
        for y, v in sorted(rows.items()):
            if not (lo < y < hi) or len(v) < 2:
                continue
            v.sort()
            text = ''.join(c for _, c, _ in v).replace(' ', '')
            sz = Counter(s for _, _, s in v).most_common(1)[0][0]
            body.append((y, sz, text))
        res.append(body)
    return res


def prange(s, n):
    if not s:
        return range(1, n + 1)
    a, b = s.split('-') if '-' in s else (s, s)
    return range(int(a), int(b) + 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('ref')
    ap.add_argument('ours')
    ap.add_argument('--pages', default='')
    ap.add_argument('--ours-pages', default='')
    ap.add_argument('--headings', action='store_true')
    a = ap.parse_args()
    R, O = lines(a.ref), lines(a.ours)
    if a.headings:
        for name, L in (('参考', R), ('我们', O)):
            tab = defaultdict(Counter)
            for body in L:
                prev = None
                for y, sz, t in body:
                    if prev is not None:
                        k = KIND.get(prev[1], str(prev[1])) + '->' + KIND.get(sz, str(sz))
                        if 'H' in k:
                            tab[k][round(y - prev[0], 1)] += 1
                    prev = (y, sz, t)
            print('==', name)
            for k in sorted(tab):
                print('  %-10s' % k, ' '.join('%.1f×%d' % (d, c) for d, c in
                                            sorted(tab[k].items(), key=lambda x: -x[1])[:6]))
        return
    rp, op = list(prange(a.pages, len(R))), list(prange(a.ours_pages, len(O)))
    for i in range(max(len(rp), len(op))):
        for name, L, pages in (('参考', R, rp), ('我们', O, op)):
            if i >= len(pages) or pages[i] > len(L):
                continue
            body = L[pages[i] - 1]
            if not body:
                print('%s p%-3d 空' % (name, pages[i]))
                continue
            print('%s p%-3d n=%2d 首 %6.1f %-14s 末 %6.1f %s' % (
                name, pages[i], len(body), body[0][0], body[0][2][:14], body[-1][0], body[-1][2][:14]))
        print()


if __name__ == '__main__':
    main()
