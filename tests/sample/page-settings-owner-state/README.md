# 页面范围恢复后的扩展设置丢失

目标：`page-settings-4abb23ce5ab3-5a91afb5`，source SHA256
`4abb23ce5ab31dfe67edd1818af1049aa5ba08c0b82a7ed415e7203b29065df5`。
这是历史失败冻结；复现原错误时须显式加载该版本。
学校当前已接受 `author-api-9561e82bd7d3-5b3501b2`，修复状态见文末。

## 最小复现

`main.tex` 只加载 article 和 docxlike，不加载 hithesis。通过公开 compute/save 钩子登记一个
`owner` 扩展设置，依次建立 11 → 22 → 33 的嵌套页面，弹出内层恢复为 22。
随后只更改上边距，owner 却从 22 回退到最外层的 11。LuaLaTeX 和 XeLaTeX 都复现：

```text
OWNER-STATE expected=22 actual=22
OWNER-STATE expected=22 actual=11
! Owner state lost after partial page setup.
```

在新的临时输出目录中运行：

```sh
FROZEN=/Users/wujunhao/latex-docxlike/build/handoffs/page-settings-4abb23ce5ab3-5a91afb5
REPRO=/Users/wujunhao/hithesis/tests/sample/page-settings-owner-state/main.tex
TEXINPUTS="$FROZEN:" LUAINPUTS="$FROZEN:" \
  lualatex -interaction=nonstopmode -halt-on-error "$REPRO"
```

通过控制只省略嵌套恢复后的增量设置，push/pop 与其余内容不变：

```sh
TEXINPUTS="$FROZEN:" LUAINPUTS="$FROZEN:" \
  lualatex -interaction=nonstopmode -halt-on-error -jobname=control \
  "\def\OwnerStateControl{1}\input{$REPRO}"
```

将引擎换成 `xelatex` 得到同样的一失败、一通过。使用 TeX Live 自带字体，不需要 Word 字体或 VM。

## 学校中的对应表现

实际学校类的隔离测试使用 `header-rule-width=1bp/2bp/3bp`：
弹出最内层后全局宽度正确恢复为 2bp；只修改 `margins/top` 后宽度变成 1bp。
纯库 owner 反例排除了学校页眉实现和字体差异。

定位：冻结 `docxlike-page.dtx:552–567,1226–1248`。
canonical 输入以前一份 `g__docxlike_page_input_tl` 为前缀，push 本次新设置的扩展键没有加入该历史；
内建几何由 canonical 尾部字段保留，扩展键则在后续重算时重新采用外层旧值。
现有 `test/page-stack-state.py` 的增量设置发生在两个范围都弹出之后，未覆盖仍位于中间范围的重算。

当时消费方保留 mixed-note 接受基线，等待库侧修复和新不可变交付。
完整验证见 `build/reports/page-settings-consumer-feedback.md`，证据为同名 `*-evidence.zip`。

后续只修页眉的 `header-variants-9aa1869a9e1f-d44b89ec` 页面源码与该版本相同。
消费方已在这份新冻结重跑：Lua/Xe 仍出现 owner 22→11，两个省略增量设置的控制仍通过。
页眉 variant 修复已单独验证关闭，不应将两项问题混为一个修复状态。

## 当前接受状态

`author-api-9561e82bd7d3-5b3501b2` 包含页面 owner 修复。消费方在新冻结重跑本原失败输入、
省略增量设置的控制及真实学校横线宽度输入：Lua/Xe 共六项全部通过。
原输入两次均保持 owner=22；学校弹出内层后及仅改上边距后均保持 2bp。
该冻结的完整学校集成已接受；上面的旧冻结复现命令和失败日志继续保留。
完整结果见 `build/reports/author-api-consumer-feedback.md`。
