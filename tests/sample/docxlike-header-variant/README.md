# 公开段落 variant 放入页眉的反例

目标冻结为 `page-settings-4abb23ce5ab3-5a91afb5`，source SHA256
`4abb23ce5ab31dfe67edd1818af1049aa5ba08c0b82a7ed415e7203b29065df5`。
原审查时学校接受的 mixed-note 尚未提供 `docxlike_setup:n` / `docxlike_par:nn`，
不能用那份旧 vendor 的“未定义命令”作为本反例结果。

在新的输出目录中，将 `TEXINPUTS`、`LUAINPUTS` 指向上述冻结，以 LuaLaTeX 或
XeLaTeX 编译本目录的 `main.tex`。例如，当前工作目录为新的临时输出目录时：

```sh
FROZEN=/Users/wujunhao/latex-docxlike/build/handoffs/page-settings-4abb23ce5ab3-5a91afb5
REPRO=/Users/wujunhao/hithesis/tests/sample/docxlike-header-variant/main.tex
TEXINPUTS="$FROZEN:" LUAINPUTS="$FROZEN:" \
  lualatex -interaction=nonstopmode -halt-on-error "$REPRO"
```

预期复现 `You can't use \prevdepth in horizontal mode`。通过控制只更换页眉段落调用：

```sh
TEXINPUTS="$FROZEN:" LUAINPUTS="$FROZEN:" \
  lualatex -interaction=nonstopmode -halt-on-error -jobname=control \
  "\def\HeaderVariantControl{1}\input{$REPRO}"
```

使用 TeX Live 自带字体，无需安装或复制 Word 字体。两引擎均应验证失败输入和通过控制。
另有同 VM 字体的完整接口探针：页眉中的 `:Vn`、`:nV`、`:VV` 六项失败；
正文 variant 与常量声明负控制八项全部通过，坐标与原 `:nn` 版本完全一致。
这些结果不改变当前学校已接受的冻结，也不表示原六组双层接口测试失败。

定位：目标冻结 `docxlike-headfoot.dtx:1088–1107` 的页眉段落分派只识别
`docxpar` 和 `docxlike_par:nn`，公开 variant 进入了外层自动段落包装。
完整审查及库侧提示词见 [`../../reference/docxlike-author-api-audit.md`](../../reference/docxlike-author-api-audit.md)。

## 修复后的交付

`header-variants-9aa1869a9e1f-d44b89ec` 已由消费方独立核验。把上面命令的 `FROZEN` 改成该冻结，
本最小稿及 `HeaderVariantControl` 在 Lua/Xe 均通过；原 6 份崩溃输入、8 控制和新增 32 组合
也已全部通过，完整字形坐标差 0。保留上面的旧冻结复现方法及原错误。
当时该修复未导入学校：页面 owner 输入历史问题仍在，详情见
`build/reports/header-variants-consumer-feedback.md`。

当前已导入完整冻结 `author-api-9561e82bd7d3-5b3501b2`，包含页眉及页面 owner 修复。
本轮在同一冻结重跑的 46 项页眉组合全部通过；学校页眉也已改用公开 `docxlike_par:nn`。
最新学校功能、整本门槛和接口验收见 `build/reports/author-api-consumer-feedback.md`。
