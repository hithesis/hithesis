#!/usr/bin/env python3
"""把 dtx 里某个宏的定义改写成 expl3 写法，记号序列不变。

    scripts/convert-macro.py src/hithesis-book.dtx hit@engcover [第几处] [--apply]

不带 --apply 时只打印结果。改完必须跑全量变体逐字节比对。
"""

import re, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from importlib import import_module
convert = import_module("latex-to-expl3".replace("-", "_")) if False else None
_mod = {}
exec(pathlib.Path(__file__).with_name("latex-to-expl3.py").read_text(encoding="utf-8").split('if __name__')[0], _mod)
convert = _mod["convert"]

HEAD = re.compile(r"\\(?:newcommand\*?\{?\\(?P<name>[a-zA-Z@]+)\}?(?:\[(?P<n>\d)\])?(?:\[(?P<d>[^\]]*)\])?|def\\(?P<dname>[a-zA-Z@]+)(?P<dp>(?:#\d)*))(?:[ \t]*(?:%[^\n]*)?\n)?[ \t]*\{")

def find_body(src, start):
    depth, i = 0, start
    while i < len(src):
        if src[i] == "\\": i += 2; continue
        if src[i] == "{": depth += 1
        elif src[i] == "}":
            depth -= 1
            if depth == 0: return i
        i += 1
    raise SystemExit("找不到配对的右花括号")

def run(path, macro, apply=False, nth=1):
    src = pathlib.Path(path).read_text(encoding="utf-8")
    m = None; hit = 0
    for mm in HEAD.finditer(src):
        if (mm.group("name") or mm.group("dname")) == macro:
            hit += 1
            if hit == nth: m = mm; break
    if not m: raise SystemExit(f"没找到 {macro}")
    open_at = m.end() - 1
    close_at = find_body(src, open_at)
    body = src[open_at+1:close_at]
    conv, warn = convert(body)
    for w in warn: print("警告:", w, file=sys.stderr)
    nargs = int(m.group("n") or 0) or len(m.group("dp") or "")//2
    default = m.group("d")
    isdef = m.group("dname") is not None
    if nargs == 0: sig = ""
    elif default is not None: sig = " { O{%s}%s }" % (default, " m"*(nargs-1))
    else: sig = " { %s }" % (" ".join(["m"]*nargs))
    if isdef:
        params = "".join(" #%d" % (k+1) for k in range(nargs))
        head = "\\ExplSyntaxOn\n\\cs_set:Npn \\%s%s\n  {" % (macro, params)
    elif nargs == 0:
        head = "\\ExplSyntaxOn\n\\cs_new_protected:Npn \\%s\n  {" % macro
    else:
        head = "\\ExplSyntaxOn\n\\NewDocumentCommand \\%s%s\n  {" % (macro, sig)
    new = head + "\n" + conv.rstrip("\n") + "\n  }\n\\ExplSyntaxOff"
    out = src[:m.start()] + new + src[close_at+1:]
    if apply: pathlib.Path(path).write_text(out, encoding="utf-8")
    else: print(new[:1200])
    return True

nth = int(sys.argv[3]) if len(sys.argv)>3 and sys.argv[3].isdigit() else 1
run(sys.argv[1], sys.argv[2], "--apply" in sys.argv, nth)
