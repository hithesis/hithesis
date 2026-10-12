# 深圳研究生报告小样

生成八份 hithesis 排版小样（硕士／博士 × 开题／中期 × 中文／英文）：

```sh
make cls
python3 tests/run-shenzhen-report.py --out tests/output/shenzhen
```

脚本检查封面文种与落款、封面关键行基线、正文版心与行距、页眉位置、中期目录无页眉、
节标题接排、博士与硕士共用版式，以及 Unicode 引擎不加载 ctex 文档类。

## Word 依据

本机原件位于 `~/Downloads/最新版硕博/`：

- `深圳硕士学位论文开题报告模板（2018版）.docx`
- `深圳Template+of+Master's+Thesis+Proposal（for+foreign+students）+ (3).docx`
- `深圳中期中文.doc/.docx`
- `深圳中期英文.doc/.docx`

来源：[开题模板](https://due.hitsz.edu.cn/info/1210/1827.htm)、
[中期模板](https://due.hitsz.edu.cn/info/1210/1828.htm)。
封面与页眉坐标同时参考 iota 的 `check-report-cover.py`、`check-report-shenzhen.py` 所记录的 Word 测量。

## 取舍

- 不排开题模板中的灰色“（模板）”行及填表说明页。
- 目录按样式排版，去掉原件为占页加入的空段、空白页和空标题；保留目录标题自身的段前段后。
- 开题标题采用示例的 18/15/14bp，中期采用示例直接格式的 15/14/14bp；清除粘贴残留的负缩进和旧字体。
- 中英文均使用粗细双线页眉与带短横页码，沿用 iota 的统一取法。
- 目录与正文各从 1 编号，采用原件分节的 `pgNumType start=1`；这与 iota 当前连续计数的实现不同。
- 博士仅替换学位文种，尚无独立博士 Word 原件核验。

已使用 Windows Word 重新导出四份原件，核对页面、封面和首节标题；中期保留
`doNotUseHTMLParagraphAutoSpacing`，正文首节保留新分节后的段前距。
导出程序为 Microsoft Word 16.0，Build 16.0.19929；中文开题的兼容模式为 14，
另三份为 15，模板按各自模式配置。

这些小样使用短正文验证排版参数；未将原 Word 的全文、插图逐页复制进测试。
