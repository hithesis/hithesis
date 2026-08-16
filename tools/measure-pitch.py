#!/usr/bin/env python3
"""量一份 PDF 的汉字步进，用来跟 Word 范例对字距。

    python3 tools/measure-pitch.py 某份.pdf [页码范围]

按字号分组，报每个汉字到下一个汉字的水平步进中位数，以及它减去标称字号的
增量。增量就是 \\CJKglue，也就是字符网格那一格的余量。

只取右端没有顶到版心边的行：两端对齐会把胶拉开，那些行量出来偏大。
"""
import sys, subprocess, statistics as st
import xml.etree.ElementTree as ET
from collections import defaultdict

CJK = lambda c: len(c) == 1 and '一' <= c <= '鿿'
NOMINAL = [9, 10.5, 12, 14, 15, 16, 18, 22]

def main(pdf, rng="1-N"):
    subprocess.run(["mutool", "draw", "-F", "stext", "-o", "/tmp/_pitch.xml", pdf, rng],
                   capture_output=True, text=True, check=True)
    root = ET.parse("/tmp/_pitch.xml").getroot()
    rights = []
    for ln in root.iter('line'):
        ch = [c for c in ln.iter('char')]
        if ch:
            q = [float(v) for v in ch[-1].get('quad').split()]
            rights.append(max(q[2], q[6]))
    if not rights:
        sys.exit("没有取到文字")
    rights.sort()
    rmax = rights[int(len(rights) * 0.97)]
    out = defaultdict(list)
    for ln in root.iter('line'):
        ch = [c for c in ln.iter('char')]
        if not ch:
            continue
        q = [float(v) for v in ch[-1].get('quad').split()]
        if max(q[2], q[6]) > rmax - 30:      # 顶到右边界的行被拉伸过，丢掉
            continue
        for f in ln.iter('font'):
            fc = [c for c in f.iter('char')]
            sz = float(f.get('size'))
            nom = min(NOMINAL, key=lambda n: abs(n - sz))
            for a, b in zip(fc, fc[1:]):
                if CJK(a.get('c', '')) and CJK(b.get('c', '')):
                    d = float(b.get('x')) - float(a.get('x'))
                    if 0 < d < 40 and abs(d - nom) < 3:
                        out[nom].append(d)
    print(f"{pdf}  {rng}")
    print("  标称字号      样本    步进中位数      增量")
    for n in sorted(out):
        v = out[n]
        if len(v) < 6:
            continue
        m = st.median(v)
        print(f"  {n:>6}bp  {len(v):8d}  {m:12.4f}  {m - n:+8.4f}")

if __name__ == '__main__':
    main(*sys.argv[1:])
