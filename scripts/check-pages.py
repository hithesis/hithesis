#!/usr/bin/env python3
"""逐页对拍：范例的 Word 导出与我们排的整本，按内容配页、按行首文字配行，报每行的基线差。

check-line-ends.py 量的是断点，这个脚本量的是版面：每一行落在页面的哪个高度。
两份 PDF 各自抽出每页的行（同一基线上的字连成一行，页眉页脚不算），先给参考的每一页
在我们这边找最像的一页（行首十字相同的行最多），再把参考页的每一行按行首十字配到那一页
上，报 Δy（我们 − 参考）与 Δx。段落文字相同而落点不同的行才有意义，所以对拍件的内容
要照范例抄，别改成示例。

参考 PDF 不入库，抽成基线文件（tests/pages-*.tsv）比：
  check-pages.py --gen 参考.pdf > tests/pages-doctor.tsv
  check-pages.py --pdf tests/sample/doctor/main.pdf --fixture tests/pages-doctor.tsv --min-ok 60
--min-ok 是棘轮：配上且 |Δy| ≤ 容差的行数不许少于它。-v 逐页列出差的行。
"""
import argparse, html, re, subprocess, sys

PAGE_RE = re.compile(r'<page[^>]*>(.*?)</page>', re.S)
CHAR_RE = re.compile(r'<char quad="[^"]+" x="([-\d.]+)" y="([-\d.]+)"[^>]*? c="([^"]*)"/>')
Y_HEADER = 105.0      # 页眉在这以上，正文页不算；第一页（封面）整页都算
KEY_LEN = 10


def stext(path):
    return subprocess.run(['mutool', 'draw', '-q', '-F', 'stext', '-o', '-', path],
                          capture_output=True, text=True, check=True).stdout


def pages(path):
    """每页的行：(y, x0, 文字)，文字去掉空白。"""
    out = []
    for pm in PAGE_RE.finditer(stext(path)):
        rows = {}
        for cm in CHAR_RE.finditer(pm.group(1)):
            c = html.unescape(cm.group(3))
            if c.strip():
                rows.setdefault(round(float(cm.group(2)), 1), []).append((float(cm.group(1)), c))
        page = []
        for y, v in sorted(rows.items()):
            v.sort()
            t = re.sub(r'[\s​]', '', ''.join(c for _, c in v))
            if t:
                page.append((y, v[0][0], t))
        out.append(page)
    return out


def key(t):
    return re.sub(r'[.…·]+$', '', t)[:KEY_LEN]


def is_folio(t):
    return re.fullmatch(r'-?[\dIVXivx]+-?', t) is not None


def body(page, index):
    """去掉页码行、省略号占位行；除封面外去掉页眉。"""
    return [(y, x, t) for y, x, t in page
            if not is_folio(t) and not re.fullmatch(r'[.…·]+', t)
            and (index == 0 or y >= Y_HEADER)]


def read_fixture(path):
    out, cur = [], None
    for raw in open(path, encoding='utf-8'):
        if raw.startswith('#') or not raw.strip():
            continue
        kind, *rest = raw.rstrip('\n').split('\t')
        if kind == 'PAGE':
            cur = []
            out.append(cur)
        elif kind == 'LINE':
            cur.append((float(rest[0]), float(rest[1]), rest[2]))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--gen', metavar='REF_PDF', help='从参考 PDF 生成基线到 stdout')
    ap.add_argument('--pdf', help='我们的 PDF')
    ap.add_argument('--fixture', help='参考的基线文件')
    ap.add_argument('--tol', type=float, default=0.5)
    ap.add_argument('--min-ok', type=int, default=0, help='棘轮：配上且在容差内的行数下限')
    ap.add_argument('-v', '--verbose', action='store_true')
    a = ap.parse_args()

    if a.gen:
        print('# 逐页基线，由 scripts/check-pages.py --gen 生成')
        print('# 来源：%s' % a.gen.rsplit('/', 1)[-1])
        for i, page in enumerate(pages(a.gen)):
            print('PAGE\t%d' % (i + 1))
            for y, x, t in page:
                print('LINE\t%.2f\t%.2f\t%s' % (y, x, t))
        return 0
    if not (a.pdf and a.fixture):
        ap.error('要么 --gen，要么 --pdf 加 --fixture')

    ref = [body(p, i) for i, p in enumerate(read_fixture(a.fixture))]
    ours = [body(p, i) for i, p in enumerate(pages(a.pdf))]
    okeys = [set(key(t) for _, _, t in p) for p in ours]
    total = matched = ok = 0
    for i, rp in enumerate(ref):
        keys = set(key(t) for _, _, t in rp)
        best = max(range(len(ours)), key=lambda j: len(keys & okeys[j])) if ours else None
        score = len(keys & okeys[best]) if best is not None else 0
        if not rp:
            continue
        total += len(rp)
        if score < max(2, 0.25 * len(keys)):
            print('参考第 %2d 页：%d 行，没配上页（最像我们第 %s 页，同 %d 行）'
                  % (i + 1, len(rp), best + 1 if best is not None else '—', score))
            continue
        op = {}
        for y, x, t in ours[best]:
            op.setdefault(key(t), []).append((y, x))
        bad, miss, good = [], [], 0
        for y, x, t in rp:
            k = key(t)
            if k not in op:
                miss.append(t[:14])
                continue
            cy, cx = min(op[k], key=lambda c: abs(c[0] - y))
            matched += 1
            dy, dx = cy - y, cx - x
            if abs(dy) <= a.tol:
                good += 1
            else:
                bad.append('      %-16s 参考 %7.2f 我们 %7.2f Δy %+6.2f  Δx %+6.2f' % (t[:16], y, cy, dy, dx))
        ok += good
        print('参考第 %2d 页 ← 我们第 %2d 页：%d 行，配上 %d，其中 ≤%.1f 的 %d；没配上 %d'
              % (i + 1, best + 1, len(rp), good + len(bad), a.tol, good, len(miss)))
        if a.verbose:
            for b in bad:
                print(b)
            if miss:
                print('      没配上：' + '；'.join(miss[:8]) + ('…' if len(miss) > 8 else ''))
    print('—— 参考 %d 行，配上 %d（%.0f%%），配上且 |Δy| ≤ %.1f 的 %d（%.0f%%，下限 %d）'
          % (total, matched, 100 * matched / max(total, 1), a.tol, ok, 100 * ok / max(total, 1), a.min_ok))
    return 1 if ok < a.min_ok else 0


if __name__ == '__main__':
    sys.exit(main())
