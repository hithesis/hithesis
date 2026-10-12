# 本地对照材料

这里存放人工核对版面时使用的参考文件，不参与模板构建。

- `word-bachelor-experiment.pdf`：从仓库根目录的 `exp.pdf` 移入，包含本科范例及分页实验。
- `hithesis-code-optimal.pdf`：手册切换为贪心断行前的整段优化版，用于比较代码段落的排版。
- `hithesis-code-greedy-overhang.pdf`：贪心断行、保留增强软断点并允许行尾代码借用一半右页边空白的手册。
- `hithesis-code-greedy-no-overhang.pdf`：贪心断行、保留增强软断点，但不借用右页边空白的手册。
- `mono-calibration-latex.pdf`、`mono-calibration-word.pdf`：相同字号、字体及软断点的 LaTeX/Word 对照样例，验证记录在相邻 `latex-docxlike/test/mono-word/`。

PDF 按仓库现有规则忽略，`make tidy` 保留本目录。
