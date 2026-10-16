# 中文字体视觉基线检查

从仓库根目录运行 `make cls`，随后：

```sh
lualatex -interaction=nonstopmode -halt-on-error tests/font-baseline.tex
```

日志必须出现 `BASELINE ALL PASS: 15`。检查包含：

- 宋、黑、楷、仿宋的角色与位移；中西文、数学混排。
- `\documentclass[fontset={preset=fandol,baseline-correction=false}]` 实际关闭校正，
  `\hitsetup{fontset={baseline-correction=auto}}` 可重新启用。
- 常规、粗体、斜体、强调、大字号与代码中文缩放。
- 局部关闭及分组恢复；同一字体承担宋体、楷体时分别使用参考值。
- 缺少两个探针字的字体跳过；装有 SimSun 时检查其位移为零。
- 二次处理不累加位移；开关前后节点的字宽、行盒、胶、断行结果完全一致。

报告路径可用 `\PassOptionsToClass{stage=proposal,degree-level=master,campus=shenzhen}{hithesis}`
后输入同一测试文件，覆盖报告路径；Unicode 引擎的报告现已统一使用自有中文层。

测试以 Fandol 为实际字体，依赖 TeX Live 字体包。它验证视觉位置校正，不等同于不同字体的字形完全相同。

实际 PDF 对照（需要 Python 的 pdfplumber）：

```sh
lualatex -interaction=nonstopmode -halt-on-error -jobname=baseline-off '\def\BaselineCorrectionOff{1}\input{tests/font-baseline-pages.tex}'
lualatex -interaction=nonstopmode -halt-on-error -jobname=baseline-on tests/font-baseline-pages.tex
python3 tests/check-font-baseline-pdf.py baseline-off.pdf baseline-on.pdf
```

预期输出为 `BASELINE PDF PASS: 3 pages`：720 个中文 glyph 按参考差值移动，
855 个西文／数学 glyph 不移动。文字、字体、字号、横坐标及页数保持一致，PDF 坐标容差为 0.002bp。
