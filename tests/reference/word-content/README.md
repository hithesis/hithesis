# 同文 Word 参考（content-v6）

- `doctor.tsv` / `bachelor.tsv`：真实 Windows Word PDF 的文字与基线；空白页保留。
- `manifest.json`：Word 输入/输出、字体、内容来源、生成及导出脚本 SHA256。
- 旧 `tests/pages-*.tsv` 不变；新计数只确认不歧义的完整相同行，见 `make pages-word-content`。

本次补齐本科结论、中英摘要末尾与关键词空段、当前声明/授权文字。修复 Word 输入中
错误的字符网格、缺失的本科结论书签目标、中文省略号的字体提示。

字体记录 `../word-fonts.json` 钉住 Windows Word 的真实字体文件。当前 LaTeX 端的同名字体
文件摘要与 Word 不同：这是回归参考，不是同字节字体的独立引擎认证。两端实际摘要见
`build/reports/word-content-latex-fonts.json`，剩余字距/断行差需要先控制字体版本再归因。

仍保留封面教学文字、静态目录页码、文献/成果著录差异及 LaTeX 数学内部差异。
图页来自按 LaTeX 布局规范化的种子，不当作通用 Word 原生排版的独立证据。
完整报告：`build/reports/word-content-reference-feedback.md`。
