#!/usr/bin/env python3
"""行末距离：demo 与 Word 范例逐行比对，报出还差多少行。

模板不自己接管断行，断行交给 TeX，所以与 Word 的逐行结果不会归零。
本脚本量的是“离 Word 还有多远”，用 --max-diff 钉一个上限当棘轮：
现状不许变坏，几何或标点改进把数字压下去之后再把上限调低。

基线 tests/lineends-regu.tsv 来自《本科毕业论文书写范例》的 Word 导出 PDF
（mutool stext 逐字符抽取，按段落锚定）。本脚本把 demo 的 main.pdf 用同一套
逻辑抽行，按段首文本对齐段落，逐行比：行文本（硬性）、行首/行末 x 坐标
（容差默认 0.6bp）。任何一行差异即失败。
LINE 行可带第四列 waive-pos：文本仍硬性比对，只豁免坐标（用于已论证
不可再收的 Word/TeX 断行经济学差异，豁免原因写在基线注释里）。

用法：check-line-ends.py [--pdf examples/demo/main.pdf] [--fixture tests/lineends-regu.tsv]
      check-line-ends.py --max-diff 84            # 棘轮：超过上限才算失败
      check-line-ends.py --gen 参考.pdf > tests/lineends-regu.tsv   # 重制基线
"""
import argparse, html, re, subprocess, sys, tempfile, os

CHAR_RE = re.compile(r'<char quad="[^"]+" x="([^"]+)" y="([^"]+)"[^>]*? c="([^"]*)"/>')
PAGE_RE = re.compile(r'<page id="page(\d+)"[^>]*>(.*?)</page>', re.S)
Y_MIN, Y_MAX = 100.0, 770.0     # 排除页眉页脚
MARGIN, INDENT_MIN = 84.0, 15.0  # 版心左缘与段首缩进判据


def stext(path):
    if path.endswith('.xml'):
        return open(path, encoding='utf-8').read()
    with tempfile.NamedTemporaryFile(suffix='.xml', delete=False) as f:
        tmp = f.name
    try:
        subprocess.run(['mutool', 'draw', '-q', '-F', 'stext', '-o', tmp, path],
                       check=True, capture_output=True)
        return open(tmp, encoding='utf-8').read()
    finally:
        os.unlink(tmp)


def body_lines(xml):
    for pm in PAGE_RE.finditer(xml):
        page = int(pm.group(1))
        rows = {}
        for cm in CHAR_RE.finditer(pm.group(2)):
            y = round(float(cm.group(2)), 1)
            if not (Y_MIN < y < Y_MAX):
                continue
            rows.setdefault(y, []).append((float(cm.group(1)), html.unescape(cm.group(3))))
        for y in sorted(rows):
            seq = sorted(rows[y])
            text = ''.join(c for _, c in seq).strip()
            if text:
                yield page, y, seq[0][0], seq[-1][0], ''.join(c for _, c in seq)


HEADING_RE = re.compile(r'^\d+(\.\d+)*\s*\S{0,14}$')


def paragraphs(xml):
    """段落 = 首行缩进的行开头，续行贴左缘；章节标题行当分隔符。
    只收段首缩进两格的段落（居中标题、表格行的 x0 对不上，自然排除）。"""
    paras, cur = [], None
    for page, y, x0, xl, text in body_lines(xml):
        if HEADING_RE.match(re.sub(r'\s+', '', text)):
            cur = None
            continue
        if x0 > MARGIN + INDENT_MIN or cur is None:
            cur = []
            paras.append(cur)
        cur.append((text, x0, xl))
    out = {}
    for lines in paras:
        if not 106.0 < lines[0][1] < 114.0:
            continue
        anchor = re.sub(r'\s+', '', lines[0][0])[:12]
        if len(anchor) >= 6 and anchor not in out:
            out[anchor] = lines
    return out


def norm(s):
    return re.sub(r'\s+', '', s)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--pdf', default='examples/demo/main.pdf')
    ap.add_argument('--fixture', default='tests/lineends-regu.tsv')
    ap.add_argument('--tol', type=float, default=0.75)
    ap.add_argument('--max-diff', type=int, default=0, help='允许的行差上限（棘轮）')
    ap.add_argument('--gen', metavar='REF_PDF', help='从参考 PDF 生成基线到 stdout')
    a = ap.parse_args()

    if a.gen:
        print('# 行末基线，由 scripts/check-line-ends.py --gen 生成')
        print('# 来源：%s' % os.path.basename(a.gen))
        for anchor, lines in paragraphs(stext(a.gen)).items():
            print('PARA\t%s' % anchor)
            for text, x0, xl in lines:
                print('LINE\t%s\t%.1f\t%.1f' % (norm(text), x0, xl))
        return 0

    fixture, cur = {}, None
    for raw in open(a.fixture, encoding='utf-8'):
        if raw.startswith('#') or not raw.strip():
            continue
        kind, *rest = raw.rstrip('\n').split('\t')
        if kind == 'PARA':
            cur = fixture.setdefault(rest[0], [])
        elif kind == 'LINE':
            cur.append((rest[0], float(rest[1]), float(rest[2]),
                        rest[3] if len(rest) > 3 else ''))

    ours = paragraphs(stext(a.pdf))
    bad = miss = 0
    for anchor, want in fixture.items():
        got = ours.get(anchor)
        if got is None:
            print('缺段  %s…' % anchor)
            miss += 1
            continue
        for i in range(max(len(want), len(got))):
            if i >= len(want):
                print('多行  %s… L%d: %s' % (anchor, i + 1, norm(got[i][0])))
                bad += 1
                continue
            if i >= len(got):
                print('少行  %s… L%d: %s' % (anchor, i + 1, want[i][0]))
                bad += 1
                continue
            wt, wx0, wxl, wflag = want[i]
            gt, gx0, gxl = norm(got[i][0]), got[i][1], got[i][2]
            if gt != wt:
                print('文异  %s… L%d\n  们: %s\n  例: %s' % (anchor, i + 1, gt, wt))
                bad += 1
            elif abs(gx0 - wx0) > a.tol or abs(gxl - wxl) > a.tol:
                if wflag == 'waive-pos':
                    print('豁免  %s… L%d  位差 %.1f（基线注释记档）'
                          % (anchor, i + 1, max(abs(gx0 - wx0), abs(gxl - wxl))))
                else:
                    print('位差  %s… L%d  x0 %.1f/%.1f  末 %.1f/%.1f  «%s»'
                          % (anchor, i + 1, gx0, wx0, gxl, wxl, wt[-6:]))
                    bad += 1
    print('—— 段 %d，缺段 %d，行差 %d（上限 %d）' % (len(fixture), miss, bad, a.max_diff))
    return 1 if bad > a.max_diff or miss else 0


if __name__ == '__main__':
    sys.exit(main())
