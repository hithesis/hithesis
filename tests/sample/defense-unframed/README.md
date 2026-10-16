# 可选无框名单

```latex
\defense[unframed, ...]       % 等同于 unframed=true
\defense[unframed=false, ...] % 有框兼容版
\defense[unframed=auto, ...]  % 当前模板默认：有框
```

`main.tex` 是可编译的简短例子，字体使用随 TeX Live 分发的 Fandol。
从本目录编译时，将仓库根目录放入 `TEXINPUTS`；模板文件先由 `make cls` 提取。

无框名单只排填写的人员，不补旧纸表的预留空行；匿名评阅不填写 `reviewers`。
每名人员保持一行记录，字段过长可折行，也可用 `\\` 明确换行；跨页重复表头。
决议使用正常正文段落，在名单之后续排；不消耗表号，不增加表格目录条目。

## 依据及范围

研究生院 [2025-03-31 通知](https://hitgs.hit.edu.cn/2025/0331/c17373a365618/page.htm)
附件 1–4 明确要求无框线名单、无需签名、匿名评阅不列，并将决议放在委员会之后。
指南要求博士增加该部分；硕士按实际要求调用。本选项不改变现有部件的显示规则。

**学校现有书写范例仍为有框样表。** 这里是依据指南文字新增的可选排版模式，
五列、列宽比例、留白和分页方式是模板实现选择，不是学校提供的无框样表复刻。
`file=...` 插入扫描件时不重排其内容。

可通过 `overrides={defense={unframed-name={姓名}[Name], ...}}` 覆盖无框标签。
其他词条包括 `unframed-role`、`unframed-column-title`、`unframed-affiliation`、
`unframed-discipline`、`unframed-reviewer`、`unframed-chair`、`unframed-member`、
`unframed-secretary`、`unframed-text`。双语输入顺序遵循文档的主/副语言规则。
