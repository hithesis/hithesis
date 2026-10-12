#!/usr/bin/env python3
"""iota-calligraphy.py：从 iota-hit 取封面美术字的轮廓，生成 src/assets/hit-calligraphy-data.dtx。

三样东西，都是 iota-hit 那边已经做好的数据，这里只换成 PDF 的路径算子：
- 校名字标（报告首页的“哈尔滨工业大学”书法字），iota-hit 的 src/pages/report/wordmark.typ，
  那边是从学校官方 SVG 抽的，每个字一段路径，带平移与缩放；
- 隶书（本科报告首页落款“哈尔滨工业大学教务处制”），src/glyphs/lishu.typ；
- 华文新魏（深圳本科报告首页的校名与文种），src/glyphs/xinwei.typ。
后两样是按字存的字体轮廓（字体单位，基线在 0，y 向上），TrueType 的二次曲线在这里换成
PDF 的三次曲线。

用法：python3 scripts/iota-calligraphy.py [iota-hit 目录]，默认 ~/Documents/Typst 包/iota-hit。
iota-hit 那边的数据改了再跑一遍，生成的文件不要手改。
"""
import os
import re
import sys

IOTA = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/Documents/Typst 包/iota-hit")
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "src", "assets", "hit-calligraphy-data.dtx")


def num(v, nd=2):
    s = f"{v:.{nd}f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def tokens(d):
    return re.findall(r"[A-Za-z]|-?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?", d)


def svg_to_pdf(d, tf, nd):
    """SVG 路径 d 转成 PDF 路径算子；tf(x, y) 把 SVG 坐标换成 PDF 坐标，保留 nd 位小数。
    字形是 256 单位一个 em，小初 36 磅时一个单位 0.14 磅，一位小数够；字标 516 单位排成
    167.8 磅宽，一个单位 0.33 磅，两位小数。"""
    t = tokens(d)
    i = 0
    out = []
    cx = cy = 0.0      # 当前点（SVG 坐标）
    sx = sy = 0.0      # 子路径起点
    last_c2 = None     # 上一段三次曲线的第二控制点（S 用）
    last_q = None      # 上一段二次曲线的控制点（T 用）
    cmd = None

    def emit(op, *pts):
        coords = []
        for (x, y) in pts:
            px, py = tf(x, y)
            coords += [num(px, nd), num(py, nd)]
        out.append(" ".join(coords + [op]))

    def nums(n):
        nonlocal i
        vals = [float(t[i + k]) for k in range(n)]
        i += n
        return vals

    while i < len(t):
        if re.match(r"[A-Za-z]", t[i]):
            cmd = t[i]
            i += 1
            if cmd in "Zz":
                out.append("h")
                cx, cy = sx, sy
                last_c2 = last_q = None
                continue
        rel = cmd.islower()
        c = cmd.upper()
        ox, oy = (cx, cy) if rel else (0.0, 0.0)
        if c == "M":
            x, y = nums(2)
            cx, cy = ox + x, oy + y
            sx, sy = cx, cy
            emit("m", (cx, cy))
            cmd = "l" if rel else "L"   # M 后面接着的坐标对当作 L
            last_c2 = last_q = None
        elif c == "L":
            x, y = nums(2)
            cx, cy = ox + x, oy + y
            emit("l", (cx, cy))
            last_c2 = last_q = None
        elif c == "H":
            (x,) = nums(1)
            cx = ox + x if rel else x
            emit("l", (cx, cy))
            last_c2 = last_q = None
        elif c == "V":
            (y,) = nums(1)
            cy = oy + y if rel else y
            emit("l", (cx, cy))
            last_c2 = last_q = None
        elif c == "C":
            x1, y1, x2, y2, x, y = nums(6)
            p1 = (ox + x1, oy + y1); p2 = (ox + x2, oy + y2); p = (ox + x, oy + y)
            emit("c", p1, p2, p)
            last_c2 = p2; last_q = None
            cx, cy = p
        elif c == "S":
            x2, y2, x, y = nums(4)
            p1 = (2 * cx - last_c2[0], 2 * cy - last_c2[1]) if last_c2 else (cx, cy)
            p2 = (ox + x2, oy + y2); p = (ox + x, oy + y)
            emit("c", p1, p2, p)
            last_c2 = p2; last_q = None
            cx, cy = p
        elif c in "QT":
            if c == "Q":
                qx, qy, x, y = nums(4)
                q = (ox + qx, oy + qy)
            else:
                x, y = nums(2)
                q = (2 * cx - last_q[0], 2 * cy - last_q[1]) if last_q else (cx, cy)
            p = (ox + x, oy + y)
            p1 = (cx + 2 / 3 * (q[0] - cx), cy + 2 / 3 * (q[1] - cy))
            p2 = (p[0] + 2 / 3 * (q[0] - p[0]), p[1] + 2 / 3 * (q[1] - p[1]))
            emit("c", p1, p2, p)
            last_q = q; last_c2 = None
            cx, cy = p
        else:
            raise SystemExit(f"不认识的路径命令 {cmd}")
    return " ".join(out)


def read_font(path):
    s = open(path, encoding="utf8").read()
    head = re.search(r'name:\s*"(\w+)",\s*upm:\s*(\d+),\s*asc:\s*(-?\d+),\s*desc:\s*(-?\d+)', s)
    name, upm, asc, desc = head.group(1), int(head.group(2)), int(head.group(3)), int(head.group(4))
    glyphs = []
    for m in re.finditer(r'"(.)":\s*\(adv:\s*(\d+),\s*d:\s*"([^"]*)"\)', s):
        ch, adv, d = m.group(1), int(m.group(2)), m.group(3)
        ops = svg_to_pdf(d, lambda x, y: (x, y), 1) if d else ""
        glyphs.append((ch, adv, ops))
    return name, upm, asc, desc, glyphs


def read_wordmark(path):
    s = open(path, encoding="utf8").read()
    vw, vh = map(float, re.search(r"_viewbox\s*=\s*\(([\d.]+),\s*([\d.]+)\)", s).groups())
    parts = []
    for m in re.finditer(r'\(scale:\s*([-\d.]+),\s*dx:\s*([-\d.]+),\s*dy:\s*([-\d.]+),\s*d:\s*"([^"]*)"\)', s, re.S):
        sc, dx, dy, d = float(m.group(1)), float(m.group(2)), float(m.group(3)), m.group(4)
        parts.append(svg_to_pdf(d, lambda x, y, sc=sc, dx=dx, dy=dy: (dx + sc * x, vh - (dy + sc * y)), 2))
    return vw, vh, " ".join(parts)


def utf16hex(ch):
    return ch.encode("utf-16-be").hex().upper()


def tl(s, indent):
    """空格写成 ~（这份数据在 expl3 语法下读），按 ~ 折行，每行不过 100 个字符。
    expl3 语法下行尾不产生记号，折在哪里都一样。"""
    lines, cur = [], indent
    for word in s.split(" "):
        piece = word if cur == indent else "~" + word
        if len(cur) + len(piece) > 100 and cur != indent:
            lines.append(cur + "~")
            cur = indent + word
        else:
            cur += piece
    lines.append(cur)
    return "\n".join(lines)


def main():
    lines = []
    w = lines.append
    w("% \\iffalse meta-comment")
    w("%")
    w("% 校名字标及美术字轮廓数据，由 scripts/iota-calligraphy.py 生成，不手工修改。")
    w("%")
    w("% \\fi")
    w("%<*shared-calligraphy-data>")
    vw, vh, ops = read_wordmark(os.path.join(IOTA, "src/pages/report/wordmark.typ"))
    w(f"\\tl_const:Nn \\c__hit_calligraphy_wordmark_box_tl {{ {{{num(vw)}}} {{{num(vh)}}} }}")
    w(f"\\tl_const:Nn \\c__hit_calligraphy_wordmark_text_tl {{ {''.join(utf16hex(c) for c in '哈尔滨工业大学')} }}")
    w("\\tl_const:Nn \\c__hit_calligraphy_wordmark_tl")
    w("  {")
    w(tl(ops, "    "))
    w("  }")
    for fn in ("lishu", "xinwei"):
        name, upm, asc, desc, glyphs = read_font(os.path.join(IOTA, f"src/glyphs/{fn}.typ"))
        w(f"\\tl_const:cn {{ c__hit_calligraphy_{name}_metrics_tl }} {{ {{{upm}}} {{{asc}}} {{{desc}}} }}")
        w(f"\\prop_const_from_keyval:cn {{ c__hit_calligraphy_{name}_prop }}")
        w("  {")
        for ch, adv, ops in glyphs:
            w(f"    {ch} = {{{adv}}} {{{utf16hex(ch)}}}")
            w("      {")
            w(tl(ops, "        "))
            w("      } ,")
        w("  }")
    w("%</shared-calligraphy-data>")
    open(OUT, "w", encoding="utf8").write("\n".join(lines) + "\n")
    print("写好", OUT, os.path.getsize(OUT), "字节")


main()
