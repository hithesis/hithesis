# 分节与标题分页检查

从仓库根目录生成类文件后，在一个已经存在的输出目录运行：

```sh
make cls
python3 tests/check-sectionbreak.py --out /path/to/output
python3 tests/check-sectionbreak.py --out /path/to/output --engine xelatex
python3 tests/check-sectionbreak.py --out /path/to/output --engine pdflatex
python3 tests/check-heading-pagebreak.py --out /path/to/output
python3 tests/check-heading-pagebreak.py --out /path/to/output --engine xelatex
```

检查内容：

- 一级标题分页前排出已积压的浮动图表；前后标题页首落点一致。
- continuous 不换页，next 清浮动体并换页，odd/even 补白后页码继续递增。
- 省略选项等于 next；连续分节可切换双栏与单栏。
- 新节可设置页码格式、起始页码、纸张和页边距；章节计数不受分节影响。
- 学位论文章分页保留右开页策略：章在 1/3/5 页，浮动图在第 2 页，第 4 页为空白。
- 深圳四套报告的首节和后续节均保留页首段前计算。连续标题时，开题仍合并前段的 12bp 段后，
  中期仍按 `doNotUseHTMLParagraphAutoSpacing` 相加，不把段距合并误当作吞段前。

独立 docxlike 仓库另有 `test/section-break-top.tex/.py`，检查页首与页中的连续分节：
新节首页页眉、默认页眉、每节页数 1/2/1/1，以及按节重编脚注。

本轮不涉及 JSON 转换。后续转换方向是 iota4web JSON → hithesis。
