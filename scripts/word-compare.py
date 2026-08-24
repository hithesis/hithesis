#!/usr/bin/env python3
"""与 Word 范例逐字对比字距。

check-line-ends.py 量的是断行落点，这个脚本量的是\u201c一个字到下一个字走了多远\u201d，
用来查中西文胶、标点压缩这类零点几 bp 的偏差。

只取\u003c段末行\u003e：段末行不参与两端对齐，量到的是自然宽；正文行被拉伸过，
拉伸量按整行摊，掺进来就分不清是本征值偏了还是这一行拉得多。

Word 把字形位置量化到 0.25 bp 左右（同一段汉字步进会在 12.492 与 12.240 之间跳），
所以单个读数没有意义，只看同类字对的均值。

三种用法：

  # 一、抽出能在 Word 里如实复刻的段落（整段无宏，\\ref 按 aux 展开）
  word-compare.py corpus --aux tests/work/13-doctor-harbin \\
      examples/demo/thesis/mainmatter/introduction.tex > corpus.tsv

  # 二、把段落灌进范例 docx 的版式（版心、网格、样式原样沿用）
  word-compare.py docx --template 范例.docx --corpus corpus.tsv --out 复刻.docx
  # 然后在 Word 里另存为 PDF

  # 三、逐字对比
  word-compare.py diff --ref 复刻.pdf --pdf tests/work/13-doctor-harbin/main.pdf \\
      --pages 28-47
"""
import argparse, collections, html, os, re, shutil, subprocess, sys, tempfile, unicodedata
from xml.sax.saxutils import escape

PAGE_RE = re.compile(r'<page id="page(\d+)"[^>]*>(.*?)</page>', re.S)
FONT_RE = re.compile(r'<font name="([^"]+)" size="([^"]+)">(.*?)</font>', re.S)
CHAR_RE = re.compile(r'<char quad="[^"]+" x="([^"]+)" y="([^"]+)"[^>]*? c="([^"]*)"/>')
Y_MIN, Y_MAX = 100.0, 770.0          # 排除页眉页脚
MARGIN, INDENT = 84.0, 114.0         # 版心左缘与首行缩进的落点区间
HEADING_RE = re.compile(r'^(\d+(\.\d+)*\s|第)')

PUNCT = set('。，、；：？！“”‘’（）《》〈〉【】—…·～－-,.;:?!()[]"\'')


def stext(path):
    """mutool 的 stext：逐字符带坐标与字体。"""
    tmp = tempfile.mktemp(suffix='.xml')
    try:
        subprocess.run(['mutool', 'draw', '-q', '-F', 'stext', '-o', tmp, path],
                       check=True, capture_output=True)
        return open(tmp, encoding='utf-8').read()
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def rows(xml, lo=1, hi=10 ** 9, minsize=11.5):
    """逐行返回每个字的横坐标、字形、字体与字号，滤掉脚注题注那些小字号的行。"""
    for pm in PAGE_RE.finditer(xml):
        page = int(pm.group(1))
        if not lo <= page <= hi:
            continue
        buckets = {}
        for fm in FONT_RE.finditer(pm.group(2)):
            name, size = fm.group(1), float(fm.group(2))
            for cm in CHAR_RE.finditer(fm.group(3)):
                y = round(float(cm.group(2)), 1)
                if not Y_MIN < y < Y_MAX:
                    continue
                buckets.setdefault(y, []).append(
                    (float(cm.group(1)), html.unescape(cm.group(3)), name, size))
        for y in sorted(buckets):
            seq = sorted(buckets[y])
            if max(s for _, _, _, s in seq) < minsize:
                continue
            yield page, y, seq


def last_lines(xml, lo=1, hi=10 ** 9):
    """段末行：右端明显短于版心右缘，起点在版心左缘或首行缩进处，且不是标题。"""
    out = {}
    for _, _, seq in rows(xml, lo, hi):
        if seq[-1][0] > 490:
            continue
        if not MARGIN <= seq[0][0] <= INDENT:
            continue
        text = ''.join(c for _, c, _, _ in seq)
        if HEADING_RE.match(text.strip()):
            continue
        key = re.sub(r'\s+', '', text)[:10]
        if len(key) >= 6:
            out.setdefault(key, seq)
    return out


def char_class(ch):
    if ch == ' ':
        return 'SP'
    code = ord(ch)
    wide = code > 0x2E7F
    if ch in PUNCT or (wide and unicodedata.category(ch).startswith('P')):
        return 'FP' if wide else 'HP'
    if wide:
        return 'CJK'
    return 'NUM' if ch.isdigit() else 'LET'


def cmd_diff(a):
    lo, hi = (1, 10 ** 9)
    if a.pages:
        lo, hi = (int(x) for x in a.pages.split('-'))
    ref = last_lines(stext(a.ref))
    ours = last_lines(stext(a.pdf), lo, hi)
    agg, n = collections.defaultdict(list), 0
    for key, want in ref.items():
        got = ours.get(key)
        if got is None:
            continue
        if ''.join(c for _, c, _, _ in want) != ''.join(c for _, c, _, _ in got):
            continue
        n += 1
        for i in range(1, len(want)):
            pair = (char_class(want[i - 1][1]), char_class(want[i][1]))
            agg[pair].append((want[i][0] - want[i - 1][0], got[i][0] - got[i - 1][0],
                              want[i - 1][1], want[i][1]))
    print('可比的段末行 %d 条' % n)
    print('%-12s %4s %8s %8s %7s' % ('字对', 'n', 'Word', '我们', '差'))
    for pair in sorted(agg, key=lambda p: -len(agg[p])):
        rec = agg[pair]
        if len(rec) < a.min_samples:
            continue
        mw = sum(x[0] for x in rec) / len(rec)
        mo = sum(x[1] for x in rec) / len(rec)
        flag = ' <<<' if abs(mo - mw) > a.tol else ''
        print('%-12s %4d %8.3f %8.3f %+7.3f%s'
              % (pair[0] + '→' + pair[1], len(rec), mw, mo, mo - mw, flag))
        if a.verbose and flag:
            for w, o, c1, c2 in sorted(rec)[:a.verbose]:
                print('      «%s»«%s»  %7.3f / %7.3f  %+6.3f' % (c1, c2, w, o, o - w))
    return 0


HEAD_TEX = re.compile(r'^\\(chapter|section|subsection|subsubsection)\*?'
                      r'(?:\[[^\]]*\])?\{(.*?)\}(?:\[.*\])?\s*$')
DROP_TEX = re.compile(r'^\\(label|clearpage|newpage|vspace\*?|par|noindent)\b.*$')
LEVEL = {'chapter': 1, 'section': 2, 'subsection': 3, 'subsubsection': 3}


def cmd_corpus(a):
    """整段不含宏才收：\\verb、\\textbf、logo、\\num 这些在 Word 里没法如实复刻，
    收进来只会把比对变成噪声。\\ref 例外，按 aux 展开成字面。"""
    labels = {}
    for root, _, files in os.walk(a.aux or '.'):
        for f in files:
            if not f.endswith('.aux'):
                continue
            body = open(os.path.join(root, f), encoding='utf-8', errors='replace').read()
            for m in re.finditer(r'\\newlabel\{([^}]+)\}\{\{([^}]*)\}', body):
                labels.setdefault(m.group(1), m.group(2))
    counter = [0, 0, 0]
    for path in a.tex:
        text = re.sub(r'(?m)^%.*$', '', open(path, encoding='utf-8').read())
        for block in re.split(r'\n\s*\n', text):
            lines = [l for l in block.split('\n') if l.strip()]
            while lines:
                m = HEAD_TEX.match(lines[0].strip())
                if m:
                    if '\\' not in m.group(2):
                        lvl = LEVEL[m.group(1)]
                        counter[lvl - 1] += 1
                        for k in range(lvl, 3):
                            counter[k] = 0
                        num = '第%d章  ' % counter[0] if lvl == 1 else \
                              '.'.join(str(c) for c in counter[:lvl]) + '  '
                        print('H%d\t%s%s' % (lvl, num, m.group(2)))
                    lines = lines[1:]
                    continue
                if DROP_TEX.match(lines[0].strip()):
                    lines = lines[1:]
                    continue
                break
            while lines and DROP_TEX.match(lines[-1].strip()):
                lines = lines[:-1]
            if not lines:
                continue
            # 源码换行：两侧只要有一边是汉字就不产生空格，西文之间产生一个
            s = lines[0].strip()
            for nxt in lines[1:]:
                nxt = nxt.strip()
                if s and nxt and (ord(s[-1]) > 0x2E7F or ord(nxt[0]) > 0x2E7F):
                    s += nxt
                else:
                    s += ' ' + nxt
            s = re.sub(r'\\ref\{([^}]+)\}', lambda m: labels.get(m.group(1), '\\REF'), s)
            s = s.replace('~', ' ')
            if re.search(r'[\\${}&_^]', s):
                continue
            print('P\t%s' % s)
    return 0


BODY_P = ('<w:p><w:pPr><w:snapToGrid w:val="0"/><w:spacing w:line="300" w:lineRule="auto"/>'
          '<w:ind w:firstLineChars="200" w:firstLine="498"/></w:pPr>'
          '<w:r><w:rPr><w:rFonts w:hint="eastAsia"/></w:rPr>'
          '<w:t xml:space="preserve">%s</w:t></w:r></w:p>')
HEAD_P = ('<w:p><w:pPr><w:pStyle w:val="%s"/><w:spacing w:before="%s" w:after="%s"/></w:pPr>'
          '<w:r><w:rPr><w:rFonts w:hint="eastAsia"/></w:rPr>'
          '<w:t xml:space="preserve">%s</w:t></w:r></w:p>')
HEAD_STYLE = {'H1': ('1', '383', '306'), 'H2': ('2', '191', '191'), 'H3': ('3', '191', '191')}


def cmd_docx(a):
    work = tempfile.mkdtemp()
    try:
        subprocess.run(['unzip', '-q', '-o', a.template, '-d', work], check=True)
        parts = []
        for line in open(a.corpus, encoding='utf-8'):
            kind, text = line.rstrip('\n').split('\t', 1)
            if kind == 'P':
                parts.append(BODY_P % escape(text))
            else:
                sid, before, after = HEAD_STYLE[kind]
                parts.append(HEAD_P % (sid, before, after, escape(text)))
        doc = os.path.join(work, 'word', 'document.xml')
        s = open(doc, encoding='utf-8').read()
        m = re.search(r'(<w:body>)(.*)(</w:body>)', s, re.S)
        sect = re.search(r'<w:sectPr[^>]*>.*?</w:sectPr>', m.group(2), re.S).group(0)
        open(doc, 'w', encoding='utf-8').write(
            s[:m.start(2)] + ''.join(parts) + sect + s[m.end(2):])
        out = os.path.abspath(a.out)
        if os.path.exists(out):
            os.unlink(out)
        subprocess.run(['zip', '-q', '-r', '-X', out, '.'], cwd=work, check=True)
        print('写出 %s' % out)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)

    d = sub.add_parser('diff', help='逐字对比两份 PDF 的字距')
    d.add_argument('--ref', required=True, help='Word 导出的 PDF')
    d.add_argument('--pdf', required=True, help='我们的 PDF')
    d.add_argument('--pages', help='我们这侧只看这个页码区间，如 28-47')
    d.add_argument('--tol', type=float, default=0.08, help='标记阈值，默认 0.08 bp')
    d.add_argument('--min-samples', type=int, default=3)
    d.add_argument('--verbose', type=int, default=0, metavar='N', help='超阈值的字对列 N 个样本')
    d.set_defaults(run=cmd_diff)

    c = sub.add_parser('corpus', help='抽出能在 Word 里如实复刻的段落')
    c.add_argument('tex', nargs='+')
    c.add_argument('--aux', help='找 .aux 的目录，用来展开 \\ref')
    c.set_defaults(run=cmd_corpus)

    x = sub.add_parser('docx', help='把段落灌进范例 docx 的版式')
    x.add_argument('--template', required=True, help='范例 docx，版心与样式从它继承')
    x.add_argument('--corpus', required=True)
    x.add_argument('--out', required=True)
    x.set_defaults(run=cmd_docx)

    a = ap.parse_args()
    return a.run(a)


if __name__ == '__main__':
    sys.exit(main())
