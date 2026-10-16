# 多段长注混排与旧模式断行反例

基线：`mixed-note-a76d465467ca-b5d3909d`。

学校功能探针见 `tests/feature/cases/footnote-multipar-mixed*.{tex,lua}`：两条注，一条两行短注，
另一条含“短段—超页自动折行段—短段”；覆盖短注在前和长注在前。
可在 `\documentclass[degree-level=master,fontset=fandol]{hithesis}` 后定义以下开关，再输入主 case：

- `\def\ProbeMode{word-2003}`：也可选 word-2007、word-2010、word-2013。
- `\def\ProbeReverse{}`：长注在前。
- `\def\ProbeOwned{}`：显式 docxpar；缺省为普通正文。
- `\def\ProbeDefault{}`：允许注段拆页；缺省沿用学校每注段保持策略。
- `\def\ProbeTrial{}`：先试排，再正式输出。

本地四模式 × 两种顺序 × 两入口 × 两策略 × live/trial 为 64/64，32 对可见分页结果相同。
每份 6971 个字母/汉字的注文字及顺序完整；这不是完整 Word 几何认证。

## 保留的 Word 反例

新 64 份 DOCX、256 次重放中，模式 15 为 64/64，模式 11/12/14 各 0/64。
页数、标记、图片、分隔线及注顺序均通过；失败来自旧模式多段注中后续段落的逐行折行。
代表例：`multipar-note-11-single-before-after-short-long-default-plain-paragraph`。
中段第一行 Word 结束于“与续页”，TeX 多放一个“顺”；没有丢字或重排注的证据。

模式 11 的独立控制已确认：删去另一条短注仍失败，把长注改回单段后通过。
单独显式关闭 FootnoteText 的 kerning 也没有消除旧模式差异。

永久证据位于 `build/reports/multipar-mixed-note-evidence.zip`。解包后路径：

```text
consumer/suite/build/boundary-inputs/boundary-11-default-only-long.{docx,tex}
consumer/suite/build/boundary-word/boundary-11-default-only-long.pdf
consumer/suite/build/boundary-replays/11/comparison.json
```

可用包内 `consumer/suite/test/native-note-flow.py`，指向上述输入、Word 导出目录、具有记录摘要的
私用字体目录及一个全新的 `consumer/suite/build/` 子目录，附加
`--runtime /path/to/hithesis --manifest multipar-note-manifest.json --name boundary-11-default-only-long` 重放。
字体 Times/TimesBold/SimSun 的文件 SHA256 记录在包内；私用字体二进制不随证据分发。

详细结果及首处逐字位置差异见 `build/reports/multipar-mixed-note-feedback.md`。

## 后续冻结的隔离复验

`page-settings-4abb23ce5ab3-5a91afb5` 的消费方隔离重放已全部 256/256（各模式 64），
另 32 个边界控制通过，12288 条注行最大基线差 0.152bp；学校 64 项控制也保持。
这是候选版本的修复结果，不覆盖上述 mixed-note 原失败和输入。
该候选因另一个页面扩展设置恢复问题尚未导入；学校默认仍是开头所列基线。
新阻塞和交接材料见 [`../page-settings-owner-state/`](../page-settings-owner-state/)
及 `build/reports/page-settings-consumer-feedback.md`。
