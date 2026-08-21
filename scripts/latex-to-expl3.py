#!/usr/bin/env python3
"""把一段普通 LaTeX 代码改写成在 \\ExplSyntaxOn 下记号序列完全相同的形式。

expl3 里空格被忽略、`~` 是空格，所以照抄一段代码进去记号序列就变了。这个脚本
按 TeX 的记号化状态机（N 行首 / M 行中 / S 跳空白）走一遍源码，把会产生空格记号
的位置写成 `~`，会产生分段的位置写成 \\par，其余原样保留。

处理的几种情形：

- 控制字后面的空格被跳过，输出里保留字面空格（expl3 会忽略，但仍然终结名字）
- 行尾没有 % 的一行，换行产生一个空格记号，写成 `~`
- 空行产生 \\par
- 原文里的 `~` 是不断行空格，改写成 \\nobreakspace{}
- 行尾孤零零一个反斜杠是 \\^^M，展开成控制空格，写成 `\\ %`
- dtx 的注释行（行首 %）原样保留，不参与状态：docstrip 会先删掉它们

用法::

    scripts/latex-to-expl3.py < 片段.tex

配套的 scripts/convert-macro.py 可以直接改写 dtx 里某个宏的定义。
改完必须跑全量变体逐字节比对。
"""

import re, sys
LETTER = re.compile(r"[A-Za-z@]")

def convert(src):
    """按 TeX 记号化状态机改写；dtx 的注释行（行首 %）原样保留，
    docstrip 会先把它们删掉，TeX 根本看不到，所以不参与状态。"""
    out, state, warn = [], "M", []
    for line in src.splitlines(True):
        nl = line.endswith("\n")
        body = line[:-1] if nl else line
        if body.startswith("%"):
            out.append(line); continue          # dtx 注释：原样过，不动状态
        i, n = 0, len(body); commented = False
        while i < n:
            c = body[i]
            if c in " \t":
                # 空格即使不产生记号，也要留一个：expl3 下它被忽略，
                # 但仍然终结控制字的名字，去掉就把 \noindent Classified 粘成一个名字了
                if state == "M": out.append("~"); state = "S"
                else: out.append(" ")
                i += 1
                while i < n and body[i] in " \t": i += 1
                continue
            if c == "%":
                out.append(body[i:]); commented = True; break
            if c == "~":
                out.append("\\nobreakspace{}"); state = "M"; i += 1; continue
            if c == "\\":
                if i + 1 < n and LETTER.match(body[i+1]):
                    j = i + 1
                    while j < n and LETTER.match(body[j]): j += 1
                    out.append(body[i:j]); state = "S"
                    if j < n and body[j] in ":_":
                        warn.append(f"{body[i:j]} 后面紧跟 {body[j]!r}")
                    i = j; continue
                if i + 1 >= n:                     # 行尾孤零零一个反斜杠
                    out.append("\\ %")               # 就是 \^^M，展开成控制空格
                    state = "S"; i += 1; continue
                out.append(body[i:i+2])
                state = "S" if body[i+1] == " " else "M"
                i += 2; continue
            out.append(c); state = "M"; i += 1
        if nl:
            if commented: state = "N"
            elif state == "N": out.append("\\par")
            elif state == "M": out.append("~"); state = "N"
            else: state = "N"
            out.append("\n")
    return "".join(out), warn

if __name__ == "__main__":
    r, w = convert(sys.stdin.read())
    for x in w: print("警告:", x, file=sys.stderr)
    sys.stdout.write(r)
