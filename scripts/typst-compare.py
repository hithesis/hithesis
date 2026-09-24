#!/usr/bin/env python3
"""与 typst-with-msword-linebreaks 对拍：同一批段落两边各排一遍，逐行比行末。

docxlike.lua 是照那个 fork 的 msword.rs 抄的，Word 只能量翻转点，两个实现之间
却能逐行比。语料是纯文本（一行一段），两边用同一套字体（Times New Roman + 中易宋体）、
同一个版心（A4，左右 30 mm）、同一个格宽，先用 fork 版 typst 排出参考 PDF，再用类排一遍，
拿 scripts/check-line-ends.py 按段落锚定逐行比（行文本硬性，行首行末坐标带容差）。

用法：typst-compare.py [tests/typst-corpus.txt] [--compat 11|15] [--typst 路径]
      [--out 目录] [--pitch 12.4543] [--tol 0.75] [--max-diff N]
fork 的二进制默认找 ~/typst-with-msword-linebreaks/target/release/typst，
也认环境变量 TYPST；类从仓库根目录（或 --repo）读，先 make cls。
棘轮只数文本差异（断点不同）；行首行末坐标的差只在 -v 时列出。

两边有意不同的几处（都是自己的探针定的，Word 站在这边）：行末闭号先由行内位分担、
不够时原位压半格（fork 一律画成整个挂出，起点在右缘上，所以行末带闭号的行会报位差）；
开号带汉字的单元 2003 档至多两个位（fork 三个）。URL 那边有紧急断点与 // 的规矩，
这里整个下行，也会不同。
"""
import argparse, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
TYPST = os.environ.get('TYPST', os.path.expanduser(
    '~/typst-with-msword-linebreaks/target/release/typst'))
FONT_PATH = os.path.expanduser('~/Library/Fonts')

TEX_ESCAPE = {'\\': r'\textbackslash{}', '#': r'\#', '$': r'\$', '%': r'\%',
              '&': r'\&', '_': r'\_', '{': r'\{', '}': r'\}',
              '~': r'\textasciitilde{}', '^': r'\textasciicircum{}'}


def tex_escape(t):
    return ''.join(TEX_ESCAPE.get(c, c) for c in t)


def typ_escape(t):
    # typst 的标记语法全逃掉：// 是注释、-- 是连接号、... 是省略号、~ 是不断行空格、
    # 引号会变弯，行首的 - + = 是列表与标题
    for c in '\\#*_@<>$`[]"\'~/-=+.':
        t = t.replace(c, '\\' + c)
    return t


def read_corpus(path):
    out = []
    for raw in open(path, encoding='utf-8'):
        t = raw.strip()
        if t and not t.startswith('#'):
            out.append(t)
    return out


def typ_source(paras, compat, pitch):
    # 版心与类一样：A4，左右 30 mm；上下不影响断行
    opts = ['mode: "msword"', 'compat: %d' % compat, 'char-pitch: %.6fpt' % pitch,
            'kern: true']
    if compat != 15:
        # 学校 doc 原件正文段 adjustRightInd=0，类默认也按关着算（M.ari0）
        opts.append('adjust-right-indent: false')
    lines = [
        '#set page(width: 595.3pt, height: 841.9pt, margin: (top: 107.75pt, right: 85.05pt, bottom: 85.05pt, left: 85.05pt))',
        '#set text(font: ((name: "Times New Roman", covers: "msword-latin"), "SimSun"), size: 12pt, lang: "zh", features: (kern: 0))',
        '#set par(justify: true, linebreaks: (%s), first-line-indent: (amount: %.4fpt, all: true), leading: 1.2em, spacing: 1.2em)'
        % (', '.join(opts), 2 * pitch),
        '',
    ]
    for t in paras:
        lines.append(typ_escape(t))
        lines.append('')
    return '\n'.join(lines)


# docx 里 compatibilityMode 的数对到 Word 版本名，docxlike 的 compatibility-mode 收后者
COMPAT_NAME = {11: 'word-2003', 12: 'word-2007', 14: 'word-2010', 15: 'word-2013'}


def tex_source(paras, compat):
    lines = [
        r'\documentclass[stage=final,degree-level=doctor,campus=harbin,fontset=windows]{hithesis}',
        r'\hitsetup{struct={frontmatter={cover=false,abstract=false,table-of-contents=false},backmatter={}}}',
        r'\hitsetup{layout={compatibility-mode=%s}}' % COMPAT_NAME[compat],
        r'\begin{document}',
        # 没写摘要的文档在文末补前置时会报 \hit@abstract@zh 未定义，给两个空摘要
        r'\begin{abstract-zh}\end{abstract-zh}\begin{abstract-en}\end{abstract-en}',
        r'\hitfrontmatter\hitmainmatter',
        r'\chapter{测}',
    ]
    for t in paras:
        lines.append(tex_escape(t))
        lines.append('')
    lines.append(r'\end{document}')
    return '\n'.join(lines) + '\n'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('corpus', nargs='?', default=os.path.join(REPO, 'tests', 'typst-corpus.txt'))
    ap.add_argument('--compat', type=int, default=11, choices=(11, 12, 14, 15))
    ap.add_argument('--typst', default=TYPST)
    ap.add_argument('--repo', default=REPO)
    ap.add_argument('--out', default=None, help='工作目录，默认 build/typst-compare')
    ap.add_argument('--pitch', type=float, default=12.4543, help='格宽（bp），类默认 12.4543')
    ap.add_argument('--tol', type=float, default=0.75)
    ap.add_argument('--max-diff', type=int, default=0, help='允许的行差上限（棘轮）')
    ap.add_argument('-v', '--verbose', action='store_true')
    a = ap.parse_args()

    if not os.access(a.typst, os.X_OK):
        sys.stderr.write('找不到 fork 版 typst：%s（--typst 或环境变量 TYPST 指一下）\n' % a.typst)
        return 2
    out = a.out or os.path.join(a.repo, 'build', 'typst-compare')
    os.makedirs(out, exist_ok=True)
    paras = read_corpus(a.corpus)
    base = 'tc-%d' % a.compat
    typ = os.path.join(out, base + '.typ')
    tex = os.path.join(out, base + '.tex')
    open(typ, 'w', encoding='utf-8').write(typ_source(paras, a.compat, a.pitch))
    open(tex, 'w', encoding='utf-8').write(tex_source(paras, a.compat))

    r = subprocess.run([a.typst, 'compile', '--font-path', FONT_PATH, typ, typ[:-4] + '-typst.pdf'],
                       capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write(r.stderr)
        return 2
    env = dict(os.environ, TEXINPUTS=a.repo + ':')
    r = subprocess.run(['lualatex', '-interaction=nonstopmode', '-halt-on-error', base + '.tex'],
                       cwd=out, env=env, capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write(r.stdout[-3000:])
        return 2
    os.replace(os.path.join(out, base + '.pdf'), os.path.join(out, base + '-hit.pdf'))

    checker = os.path.join(HERE, 'check-line-ends.py')
    fixture = os.path.join(out, base + '.tsv')
    r = subprocess.run([sys.executable, checker, '--gen', typ[:-4] + '-typst.pdf'],
                       capture_output=True, text=True, check=True)
    open(fixture, 'w', encoding='utf-8').write(r.stdout)
    r = subprocess.run([sys.executable, checker, '--pdf', os.path.join(out, base + '-hit.pdf'),
                        '--fixture', fixture, '--tol', str(a.tol), '--max-diff', '999999'],
                       capture_output=True, text=True)
    # 棘轮只数文本差异（文异、多行、少行、缺段）：行末闭号的画法两边有意不同，位差
    # 只在 -v 时列出来看
    text_bad = miss = pos = 0
    for line in r.stdout.splitlines():
        if line.startswith(('文异', '多行', '少行')):
            text_bad += 1
        elif line.startswith('缺段'):
            miss += 1
        elif line.startswith('位差'):
            pos += 1
            if not a.verbose:
                continue
        elif line.startswith('——'):
            continue
        print(line)
    print('—— 模式 %d，%d 段，缺段 %d，文本行差 %d（上限 %d），位差 %d'
          % (a.compat, len(paras), miss, text_bad, a.max_diff, pos))
    return 1 if text_bad > a.max_diff or miss else 0


if __name__ == '__main__':
    sys.exit(main())
