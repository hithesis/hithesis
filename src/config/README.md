# 配置文件中的命名

`hithesis.cfg` 由本目录的 dtx 文件生成。默认值在源文件中修改，用户文档通常通过
`\hitsetup` 覆盖，不直接编辑生成的 cfg。

## 设置的位置

| 内容 | 设置族 | 源文件 |
| --- | --- | --- |
| 作者填写的信息 | `info` | `hit-info.dtx` |
| 固定名称、字段标签、说明文字 | `overrides` | `hit-terms.dtx` |
| 字号、段落、题注等元素格式 | `styles` | `hit-layout.dtx` |
| 页面、网格、页眉页脚距离 | `layout` | `hit-layout.dtx` |
| 定理环境、名称与样式 | `thm` | `hit-thm.dtx` |

字体预设在 `hit-font-presets.dtx` 中，直接编入类文件；`hit-names.dtx` 保存类初始化时
需要的编号后间距及模板名称，也不属于生成 cfg 中的用户信息。

## 词条按用途分组

新增词条采用 `部件 = { 字段 = 值 }` 的写法。部件内不重复写部件前缀。
`title` 表示该部分的标题，清单中的 `image`、`table`、`equation` 分别表示图、表、公式的
条目类型名；`imprint` 表示制作单位落款，`in-english-toc` 表示英文目录中的文字。
`base` 存放跨部件共用的词条。`Heading 1` 等样式名不属于这些文字词条。
`algorithm` 配置算法关键字，`degree-type` 配置学位类型的显示文字；
`number-separator` 配置编号后的内容，如 `section={\quad}`，沿用原先
`after-section-number` 的取值规则。这些分组均位于 `overrides` 中。

```latex
\hitsetup{overrides={
  caption={figure={图}[Figure], table={表}[Table], equation={式}[Equation]},
  list-of-equations={title={公式清单}[List of Equations],
                     equation={公式}[Equation]},
  references={title={参考文献}[References]},
}}
```

正文引用的“式”与公式清单的“公式”分别配置，不互相覆盖。图、表名称同时供标准
LaTeX 名称命令和 `\autoref` 使用；英文副题注的 `caption/figure-prefix`、
`caption/table-prefix` 则保留各自的格式取值。
图表清单的类型名默认引用题注名称；单独设置 `list-of-figures/image` 或
`list-of-tables/table` 后，仅改变清单，不改变题注。

## 标准名称的分组入口

| 分组写法（相对于 `overrides`） | 原有写法 |
| --- | --- |
| `caption/figure` | `figurename` |
| `caption/table` | `tablename` |
| `mainmatter/chapter-name` | `chapter-name` |
| `appendix/title` | `appendixname` |
| `table-of-contents/title` | `contentsname` |
| `list-of-figures/title` | `listfigurename` |
| `list-of-tables/title` | `listtablename` |
| `list-of-equations/title` | `listequationname` |
| `list-of-equations/equation` | `equationname` |

两种入口更新同一个名称，不另存一份副本。旧入口用于已有文档，新配置采用分组写法。
标准名称保存当前文档语言的值：单个值直接使用，双语值按正文语言选取。
用户的双语输入沿用 `{主语言}[副语言]`，包括已有的双语方向切换规则。
cfg 内的双语对固定按 `{中文}[英文]` 书写。

值中也可以引用新名称，如 `<caption-figure>`；它会在使用时读取 `\figurename`，
后续改名无需再同步引用它的词条。普通词条引用仍使用完整的连字符键名，如
`<base-campus>`、`<bibliography-heading-zh>`。

封面上的完整文种统一使用 `cover/document-type`，终稿、开题、中期和博士后报告共用这一入口。
默认值在 cfg 中按阶段、校区、学位等条件组合；排版处只取完整文字，不再追加学位或阶段。
中文封面取中文值，需要英文文种的封面取英文值。

```latex
\hitsetup{
  info={title={研究题目}[Research Title]},
  overrides={cover={
    document-type={硕士学位论文开题报告}[Master's Thesis Proposal],
    title={题目：}[Title:],
  }},
}
```

`cover/title` 是“题目：”这类字段标签，`info/title` 才是用户填写的研究题目。
没有题目标签的封面不会因此增加一行。`report-title`、`final-title` 不作为配置入口，
旧的报告标题键及题目标签专用键已经移除，不提供别名或转发。

深圳研究生报告的其他词条保留校区后缀，例如 `cover/report-student-id-shenzhen`、
`cover/report-imprint-shenzhen` 和 `header/report-text-shenzhen`。

参考文献和索引标题使用 `references/title`、`index/title`；设值时同时更新
标准的 `\bibname`、`\indexname`，cfg 不再重复写一组标准名称绑定。

答辩页的 `defense/title` 是页面标题，职称列表头使用 `defense/column-title`。
原扁平键 `resolution-title` 仍表示职称列表头。部件标题的旧 `heading`、公式清单的
`entry-name` 以及落款的 `bottommark` 写法保留转接，内部旧名称也不另存一套值。

章号名称沿用前后两部分的写法，例如 `{第,章}`。若在双语值的方括号内包含逗号，
应加一层分组，如 `{第,章}[{Chapter\enskip,}]`。

## 条件后缀

用户词条的条件后缀允许乱序，存储时按 stage、campus、degree-level、degree-type、category、form
排序；语言由双语接口处理，内部语种后缀独立置于最后。例如 `university-bachelor-shenzhen`
与 `university-shenzhen-bachelor` 指向同一个变体。内置配置仍采用规范顺序。

同轴重复、互相矛盾、未知条件、不完整的 `!` 否定条件，以及同一组 overrides 中规范化后
重名的设置均报错。不同 overrides 调用仍可以依次覆盖。正条件权重为 2、否定条件为 1，
最具体的匹配生效；同等权重歧义仍报错。可对已登记词条增加合法变体，取值后重新绑定当前档。

加载 wiseref 后，模板使用公开的 `\wiserefsetup` 配置这些词条，不加载或复制引用实现。
名称以宏形式保留，修改 cfg 词条会跟随更新；用户在加载之后的 wiseref 设置优先于模板初始化。
