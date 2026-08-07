# 贡献指南

本文写给要改代码的人：修 bug、加功能、调整文档结构。只是提 issue 或反馈样式问题的模板用户不必读。

---

## 1. 项目结构

```
hithesis/
├── src/
│   ├── hithesis.dtx            <- 入口：driver、三类共用的文件头、索引样式、dtx-style
│   ├── hit-thesis.dtx          <- 毕业论文类 hithesisbook
│   ├── hit-config.dtx         <- 各个类的配置（改学校规范先看这里）
│   ├── hit-thesis-config.dtx   <- 只剩一句回放调用与几条固定词汇
│   ├── hit-report.dtx          <- 开题中期类 hithesisart
│   ├── hitsz-midterm-report.dtx <- 深圳博士中期类 hithesisartplus
│   ├── hit-bst.dtx             <- 参考文献样式 hithesis.bst / hitszthesis.bst
│   ├── hit-doc.dtx             <- 用户手册
│   ├── hit-eps.dtx             <- EPS 图像数据（校徽、封面、示例插图）
│   └── shared/                 <- 各个类共用的底层模块，见 §4.2
├── hithesis.ins          <- docstrip 驱动文件，留在根目录：它的输出路径都相对于此
├── build.lua             <- l3build 配置：unpack / distribute / doc / check / ctan
├── Makefile              <- 构建与测试入口
├── latexmkrc             <- latexmk 配置
├── scripts/              <- 打包、依赖清单、回归测试、changes 提取、标点检查
├── tools/                <- 排版测试脚本
├── tests/                <- 变体定义与测试说明
├── testfiles/            <- l3build 的宏级测试：*.lvt 用例与 *.tlg 基线
├── examples/
│   ├── hitbook/{chinese,english}/   <- 毕业论文示例
│   └── hitart/{reports,reportplus}/ <- 开题/中期/博士中期示例
└── .github/              <- Issue / PR 模板、CI 配置
```

构建产物（`*.cls`、`*.bst`、`*.ist`、`*.eps`、`*.pdf`）都由源文件生成，不进版本库。

## 2. 开发环境

| 工具 | 用途 | 必需性 |
|---|---|---|
| TeX Live ≥ 2022 | 编译模板与示例 | 必需 |
| Python 3.8+ | changes 提取、标点检查、回归测试、变体编译 | 必需 |
| Make | 走 Makefile 的测试目标 | 推荐 |
| l3build | 构建与打包，随 TeX Live 发行 | 可选 |
| Ghostscript | 排版比对时把 PDF 渲染成 PNG | 跑测试才需要 |
| ImageMagick | 生成逐页差异图 | 可选 |

测试脚本用 bash 写，只保证在 Linux 和 macOS 下可执行。Windows 下走 WSL 或 Git Bash。

### 常用命令

构建有两条等价路径。`make` 这条还负责把生成物分发到示例目录：

```shell
make cls          # 生成 cls/bst/ist/eps，并分发到四个示例目录
make doc          # 编译用户手册 hithesis.pdf
make distribute   # 只做分发（cls 已经生成过时用）
make clean        # 清理生成产物
make changes       # 从 \changes 生成 RELEASE_NOTES.md
make changes-check # 校验 \changes 的日期约定
make changes-fix   # 自动修正能修的部分
```

测试相关：

```shell
make baseline        # 42 个变体全编一遍，渲染结果存成本地基线
make smoke           # 重编并与本地基线逐页比
make regression-test # 与参照版本逐页比，发版前跑
make doc-baseline    # 改动前存一份手册 PDF
make doc-check       # 改完与之比对
```

l3build 这条随 TeX Live 发行，不依赖 make / bash，三平台原生：

```shell
l3build unpack     # 等价于 make cls 的生成部分，不含分发
l3build distribute # 把生成物拷进四个示例目录，等价于 make distribute
l3build doc        # 编译手册
l3build ctan       # 打 CTAN 包（源码 + 手册，不含示例）
l3build install    # 装进本地 TEXMFHOME
l3build check      # 跑 testfiles/ 里的宏级测试
```

### 宏级测试

`testfiles/*.lvt` 是测试用例，`*.tlg` 是它编出来的日志基线，CI 在五个 TeX Live
版本上都比对。它管的是排版比对看不见的那一层：选项解析出来的标志位、`\hitsetup`
存进去的字段、对外宏还在不在。加一个用例：

```shell
# 写好 testfiles/08-xxx.lvt 之后
l3build save 08-xxx    # 生成 testfiles/08-xxx.tlg
l3build check          # 确认全绿
```

`support/` 放测试夹具，`checksuppfiles` 列出的文件会在检查时拷进测试目录。现在只有
一份 `hithesis.sty`——假冒的旧版宏包，用来验证类文件里那条重定向确实挡住了它
（见 `testfiles/21-legacy-document.lvt`）。它是源文件不是产物，`.gitignore` 里为它
开了例外。

`l3build save` 生成的基线**必须逐行读一遍再提交**。它只是把当前行为拍下来，行为
本来就是错的它照样存；漏写 `\makeatletter` 之类的失误也会被原样固化成基线。

两个写用例时容易踩的坑：

- 测试体里要用 `@` 开头的内部命令，得自己在 `\START` 之后写 `\makeatletter`。
- **含中文的基线行要明显短于 79 字节。** 超了会被 TeX 折行，而 l3build 靠「行长
  恰好等于 `maxprintline`」来识别并拼回折断的行，中文一个字三字节、字节数对不上
  就拼不回来，老版本 TeX Live 上这条会直接失败。纯 ASCII 的行不受影响。
  想复验就临时在 `build.lua` 末尾加一行 `maxprintline = 79` 再 `l3build check`。

面向用户的完整模板包（含示例）由 `scripts/package.sh` 打，跟 CTAN 包是两个东西。

在示例目录里：

```shell
cd examples/hitbook/chinese && make thesis
cd examples/hitart/reports  && make report
```

## 3. dtx 导航

先按家族找文件，再在文件里按 docstrip 守卫找模块：

| 要改什么 | 打开哪个 |
|---|---|
| 毕业论文的任何行为 | `src/hit-thesis.dtx` |
| 各个类的配置 | `src/hit-config.dtx` |

| 开题、中期报告 | `src/hit-report.dtx` |
| 深圳博士中期 | `src/hitsz-midterm-report.dtx` |
| 各个类共用的底层 | `src/shared/hit-*.dtx` |
| 参考文献样式 | `src/hit-bst.dtx` |
| 用户手册文字 | `src/hit-doc.dtx` |
| 类的公共文件头、索引样式 | `src/hithesis.dtx` |

文件内用 `grep -n '%<\*thesis-' src/hit-thesis.dtx` 之类列出模块起点。模块用注释标出：

```
% ^^A ======================================================================
% ^^A Module thesis-footnote: 脚注样式与编号（thesis）
% ^^A ======================================================================
```

这些 `^^A` 行必须待在 macrocode 之外，否则会被当成代码原样印进手册。

同一个模块在 dtx 里可能被切成多段、与别的模块交替排布。例如 `report-deps` 有 9 段，因为
`hyperlink` 和 `geometry` 要插在它中间才能保持原有的加载顺序。这是有意为之，不要合并整理。

## 4. 硬性约定

不遵守的 PR 不会被合并。

### 4.1 用户接口不得改变

模板已有数千篇论文在用。任何 PR 不得改动：

- `\documentclass` 接受的选项名与默认值
- `\hitsetup{}` 接受的 key 名
- 已对外暴露的命令名（`\inlinecite`、`\bicaption`、`\rcell` 等）
- 已对外暴露的环境名（`cabstract`、`publist`、`appendix` 等）

新增是允许的。重命名、删除、改默认值并非完全禁止，但要先开 issue 讨论，或者走完 §9 的废弃期。

### 4.2 版式各写各的，底层机制共用

各个 cls 的版式代码物理隔离，由各自的 `<类>-*` 模块承载。当前是三个：`thesis-*` 在 `src/hit-thesis.dtx`、`report-*` 在 `src/hit-report.dtx`、`szmidterm-*` 在 `src/hitsz-midterm-report.dtx`。每个类对应一套学校规范，各自演化，碰巧相似的版式不要合并，规范一独立变动就会变成维护负担。新增一个类就是新增一个 `hit-<名>.dtx` 加一组 `<名>-*` 模块。

底层机制是另一回事。字号、数学、表格、脚注这些各套规范要求一致的东西，共用一份放在 `src/shared/hit-*.dtx`，守卫叫 `shared-*`：

| 文件 | 管什么 |
|---|---|
| `hit-fonts.dtx` | 中西文字体与字号阶梯 |
| `hit-math.dtx` | amsmath/thmtools、定理环境、`eqdenote` |
| `hit-table.dtx` | 长表格字号 |
| `hit-footnote.dtx` | 带圈脚注号与脚注版式 |
| `hit-list.dtx` | `enumitem` 加载、列表间距、`publist` |
| `hit-meta.dtx` | `\hitsetup` 的键机制与旧名兼容 |
| `hit-hyperlink.dtx` | hyperref 配置（书签、链接边框、url 字体） |
| `hit-title.dtx` | `title` 键的解析与三种取用 |
| `hit-caption.dtx` | 双语题注（`\caption{中}[英]`）与 `\bicaption` 兼容 |
| `hit-subfigure.dtx` | `\subfigure` 兼容层，整个文件到 v4.1 可删 |
| `hit-options.dtx` | 选项声明助手与读标志位的判断函数 |

判断标准是“各套规范会不会分开改”。会分开改的（封面、页眉、章节标题、目录）留在各自的类文件里；不会的（`\hitsetup` 怎么解析键、字号阶梯怎么定义）才进 `shared/`。

共享层的写法与类模块不同：文件里只放定义，需要在特定时机执行的部分包成 `\hit@setup@<名>`，由各个类在原来那段代码所在的位置调用。这样共享之后生成物的执行顺序不变，能用“生成的 cls 逐字节不变”来验收。

例外：`hithesis.bst`（或将废弃并切换到 biblatex-gb7714）和 `hit-eps.dtx` 也跨类共享，但它们不走 `shared/`，因为不是拼进 cls 的模块。

### 4.3 一个模块一个职责

模块名要能反映它唯一的职责：

模块名的形式是“类-职责”，类的前缀是 `thesis` / `report` / `szmidterm` / `shared`：

- √ `thesis-chapter` 只管毕业论文的章节标题格式
- √ `thesis-bib` 只管毕业论文的参考文献加载与样式
- × `thesis-floats` 兼管列表、定理、段落、引用

加代码前先问这段代码语义上属于哪个模块，找到答案再写。找不到就考虑拆一个新的出来，见 §5。

### 4.4 模块内不写 `\ProvidesPackage`

v3.2a 起模块内容直接拼进 `.cls`，不再生成独立的 `.sty`。在类文件里写 `\ProvidesPackage` 会声明一个并不存在的宏包，日志里出现的身份信息也是假的。

模块开头只写注释标识：

```
% ^^A ======================================================================
% ^^A Module thesis-footnote: 脚注样式与编号（thesis）
% ^^A ======================================================================
%<*thesis-footnote>
...实际代码...
%</thesis-footnote>
```

### 4.5 `\changes` 历史条目

新增模块、迁移代码、语义有明显变化，都要写 `\changes`：

```latex
% \changes{v3.2a}{0000/00/00}{某段代码从某处迁到某处，理由}
```

- 版本号 `v3.2a` 是当前开发版，合入 master 后由维护者改成正式版本号
- 日期填占位符 `0000/00/00`，发版时由 `scripts/changes.py --stamp` 统一替换成发布日期
- 描述要写为什么这么做，不只写做了什么

CI 会校验这三条，不合规直接失败：开发版条目必须是 `0000/00/00`，已发布版本不得留占位符，
日期格式必须 `YYYY/MM/DD`。本地跑 `make changes-check` 看结果，`make changes-fix` 自动修
补零和写错的开发版日期。

### 4.6 expl3 迁移

底层实现正在逐模块迁到 expl3，对外接口不跟着变。

**迁移单位是整个模块，不是单个语句。** expl3 的函数名带 `:` 和 `_`，这两个字符
只有在 `\ExplSyntaxOn` 下才算字母，所以没法零散替换某一处写法，只能一个模块整体
切过去，前后用 `\ExplSyntaxOn` / `\ExplSyntaxOff` 圈起来。

**`\gdef` 要配 `\cs_gset_nopar:cpn`，不是 `\cs_gset:cpn`。** 后者是 `\long\gdef`，
而 `\ifx\hit@X\@empty` 这种判断连 `\long` 前缀一起比，加了前缀空值就不再等于
`\@empty`。踩过一次：封面上空的副导师栏被印了出来，12 个变体有差异。同理
`\newcommand*` 对应 `\cs_set_nopar:Npn`。

**选项与标志位已改用 l3keys。** 类选项在 `hit/class` 族里声明，`\ProcessKeyOptions` 解析，
未知选项转给 `ctexbook`/`ctexart`；标志位是 `\g__hit_<名>_bool`，读用 `\hit@if@option@TF` 或
`\bool_if:N`，写用 `\bool_gset_true:N`。
模块内部要读旧标志位，用 expl3 的桥接函数：

```latex
\legacy_if:nTF { hit@debug } { 真 } { 假 }
\bool_lazy_and:nnT { \legacy_if_p:n { hit@harbin } } { \legacy_if_p:n { hit@bachelor } } { ... }
```

**`\ExplSyntaxOn` 会改变空格与 `~` 的含义。** 两件事，方向相反，容易搞混：

- 字面文本里的空格被吞。`text={150true mm}` 直接照抄会变成 `150truemm`，要写 `~`。
- **`~` 在两种语法下含义不同。** LaTeX 里它是活动字符，表示不断行空格；expl3 里
  它是普通空格（catcode 10）。原有代码里的 `~` 照抄进 `\ExplSyntaxOn`，不断行空格
  就退化成了普通空格。`thesis-pagestyle` 的 `\fancyfoot[C]{\xiaowu-~\thepage~-}` 这样
  照抄之后，42 个变体里有 21 个的 PDF 变了。要保持原意就写 `\nobreakspace{}`。

一句话：**要空格时写 `~`，原文里已有的 `~` 要改写成 `\nobreakspace{}`。**

控制空格 `\ ` 不在此列。它在两种语法下是同一个控制序列，`\meaning` 查出来都是
`\ `，`\begin{tabular}{l@{\ \ }c}` 写在 expl3 里排出来的结果与写在外面完全一样，
实测确认过。曾经以为它没有等价写法，那是把 `{\ }` 后面被吞掉的那个字面空格
误当成了控制空格本身的问题。

行尾孤零零一个反斜杠是控制序列 `\^^M`，`\meaning` 是 `macro:->\ `。进 expl3 要写成
显式的 `\ `，后面跟个 `%` 保住那个空格不被编辑器裁掉。

**被跳过的空格也不能删。** `\noindent Classified` 里那个空格不产生记号，但它终结
控制字的名字。删掉就粘成 `\noindentClassified` 了。expl3 下字面空格被忽略，所以
原样留着就行——只有需要产生空格记号的地方才换成 `~`。

挑对应的 expl3 定义命令，别一律用 `\NewDocumentCommand`——它是 protected 的。
`\longbionenumcaption` 原本是 `\renewcommand*`，改成 `\NewDocumentCommand` 之后
它在 `\caption` 这类会移动的参数里不再展开，四十二个变体全变。对应关系：

| 原写法 | expl3 写法 |
| --- | --- |
| `\newcommand` / `\renewcommand` | `\cs_set:Npn`（long，不 protected） |
| `\newcommand*` / `\renewcommand*` | `\cs_set_nopar:Npn` |
| `\def` | `\cs_set:Npn`（按需 `_nopar`） |
| 带可选参数的 | 只能用 `\NewDocumentCommand`，改完要单独验 |

空格规则不必手工数。`scripts/latex-to-expl3.py` 按 TeX 的记号化状态机把一段代码
改写成 expl3 下记号序列相同的形式，`scripts/convert-macro.py` 直接改写 dtx 里某个
宏的定义：

```
scripts/convert-macro.py src/hit-thesis.dtx hit@engcover --apply
```

八个封面版式宏就是这么转的。脚本不是万能的，改完照样要跑全量变体逐字节比对。

**内容与控制流分开**是另一条路：把大段字面排版内容留在 expl3 之外定义成宏，
再由 expl3 的条件调用它。适合内容整块、判断在外层的情形：

```latex
\ExplSyntaxOff
\def\hit@report@shenzhenmaster@sectionset{\ctexset{ ...原样照抄... }}
\ExplSyntaxOn
\bool_lazy_and:nnT { ... } { ... } { \hit@report@shenzhenmaster@sectionset }
```

**大段排版内容里的判断走助手函数。** 上面那条把内容留在 expl3 之外的做法，遇到
判断散落在内容各处时不好用。这时反过来：判断本身定义成 expl3 函数，放在模块顶层，
内容里只写函数调用。参数是在 expl3 之外记号化的，里面的空格照原样保留。

现有的一批助手（`thesis-options` 与两个 `*-options` 模块里各有一份）：

| 函数 | 作用 |
| --- | --- |
| `\hit@if@option@TF{flag}{真}{假}` | 按标志位二选一 |
| `\hit@if@option@T{flag}{真}` | 只有真分支 |
| `\hit@if@both@options@TF{f1}{f2}{真}{假}` | 两个标志位同时成立 |
| `\hit@if@not@empty@T\宏{真}` | 宏非空时执行 |
| `\hit@if@wider@TF{长度}{阈值}{真}{假}` | 比长度 |
| `\hit@if@greater@T{整数}{阈值}{真}` | 比整数 |
| `\hit@if@same@TF{甲}{乙}{真}{假}` | 展开后比字符串 |
| `\hit@glue@skip{基准}{伸缩}` | `style/glue` 决定要不要给伸缩量 |
| `\hit@glue@font@size{字号}{行距}{伸缩}` | 同上，用于 `\fontsize` |

这批定义在 `src/shared/hit-options.dtx`，各个类共用。

另有若干针对具体组合的具名函数，由 `\hit@define@condition{名}{布尔表达式}` 生成，
名字读下来就是条件本身：`\hit@if@harbin@master@or@doctor@or@shenzhen@master`、
`\hit@if@harbin@master@opening@or@midterm`。末尾带 `@TF` 的要给两个分支。

已迁移：`thesis-geometry`、`report-geometry`、`thesis-mainmatter`、`report-chapter`、
`report-pagestyle`、`report-toc`、`thesis-toc`、`thesis-pagestyle`、`report-floats`、`thesis-deps-c`、
`thesis-glossary`、`report-deps-a`、`thesis-deps-a`、`report-options` 与
`szmidterm-options`、`thesis-options`、
`thesis-meta`、`report-meta`、`szmidterm-meta`、`thesis-floats`、`thesis-hyperlink`、
`thesis-frontmatter`、`report-frontmatter`、`thesis-chapter`、`thesis-appendix`、`thesis-bib`、
`report-bib`、`thesis-footnote`、`report-deps-c`。

生成的类文件里，`\ifhit@…` 与 `\ifboolexpr` 只剩三十处，全在 `thesiscfg` 与
`reportcfg` 那两段固定词汇的顶层分支里。那些分支的两侧各是几十行 `\gdef` 与
`\newtheorem`，内容里有大量带空格的英文串；把它们塞进宏参数只会让 dtx 更难读，
所以留着不动。`\ifthenelse{\equal{#1}{...}}` 比较章标题的两处也留着——`\equal`
与 `\str_if_eq:nn` 对健壮命令的处理不完全一样，换了不保险。

错误信息这类不会被四十二变体覆盖的代码，改完要单独比。做法是把改前改后的两份
类文件各自改名加载，故意传错选项，把 `\ClassError` 的输出 diff 一遍。第一次改完
`\MessageBreak` 后面多了个空格、行尾少了个空格，全靠这个比出来的。

`\ExplSyntaxOn` 不能写进任何在调用处记号化的参数里。`\hit@if@option@TF{english}{\ExplSyntaxOn
\cs_new:Npn …}` 看着像能用，其实参数读进来的时候 `_` 和 `:` 还不是字母，`\cs_new:Npn`
被拆成 `\cs` 加一串杂字符，`\ExplSyntaxOn` 执行时已经晚了三步。整份类文件编不过，
二十四个变体直接没有产物。`\fancypagestyle` 的第二个参数、`\newcommand` 的宏体也一样。
判断依据：这段代码是不是要先被当成参数或宏体读进去。是的话，开关必须放在外面，
或者把这段抽成一个在模块顶层用 expl3 定义好的函数，参数里只写函数名。

表格前导不能靠展开传进去。`\begin{longtable}{@{\hskip 1cm}p{3.5cm}…}` 里的
`\hskip 1cm` 有字面空格，想把前导抽成宏再 `\exp_args:No \begin{longtable}\宏`
是行不通的，array 的前导解析器不认。这类环境整个留在 expl3 之外。

有些宏不能转，转了行为就变。`\@afterheading` 里 `\clubpenalty 1` 后面紧跟
`\if@afterindent`，TeX 扫描惩罚值时会把这个可展开的条件一起展开，条件是在扫描
过程中求值的。换成 protected 的 `\legacy_if:nF` 之后扫描立刻结束，求值时机变了，
四十二个变体全变。判断依据：分支紧跟在一个待扫描的数值/长度后面，就别动。

别在宏体里写 `\ExplSyntaxOn`。定义时catcode 确实会切过去，但那对 `\ExplSyntaxOff`
两侧的换行与缩进影响很难数清，art 封面上试过一次，六个变体全变了。多条件判断
在模块顶层定义成具名函数，宏体里只写函数名。

分支里带 `#1` 的，别用 `\newcommand` 把它包成宏——那样 `#` 要加倍，漏了就是
“Illegal parameter number”。当成 `\hit@if@option@TF` 的参数传进去就没这个问题，参数里的
`#` 原样通过。

判断分支末尾的空格按同一条规则数：以控制字结尾的分支，后面的空格被跳过；
以 `}` 或普通字符结尾的分支，那个空格是真的。`\ifhit@opening {\ } \else \enspace \fi`
的真分支是 `{\ }` 加一个空格，写成 `\hit@if@option@TF{opening}{{\ } }{\enspace}` 才对。

把 `\ifhit@X A\else B\fi` 换成 `\hit@if@option@TF{X}{A}{B}` 时，要看原写法 `\fi` 后面
有没有空格。`\fi` 是控制字，后面的空格在记号化时就被跳过了；换成以 `}` 结尾之后
那个空格变成真的空格。图表题注里 `\fi }#3` 就是这样，六处里有三处踩了这个。

行尾没有 `%` 的一行，换行会带出一个空格记号；这个空格在水平模式下是真的
词间距。`\l@chapter` 里 `{...#1}` 之后那一行就是这样，进 expl3 之后空格被吃掉，
目录里引导点的起始位置就变了。改写前先按 TeX 的记号化规则数一遍哪些换行会留下
空格：行尾是控制字的不留，行尾是 `}` 或字符的留。

抽公共函数时先查同名宏。`\hit@toc@font` 在 `thesis-toc` 里只在 `toc/sans-font`
打开时才定义，关着的时候故意保持未定义，用处是 `\csname hit@toc@font\endcsname`
取到 `\relax`。在别处用 `\cs_new:Npn` 定义同名函数不会报错（那边用的是
`\cs_set:Npn`），但会让目录每一行都多出一个 `\heiti`。四十二变体比对能查出来，
逐字节差异出现在第一个内容流，`.toc` 与 `.aux` 反而完全一致。

评估后跳过：`report-hyperlink`（零条件）、`thesis-bib`（含 natbib 补丁需逐字保留）、
`thesis-appendix`（条件几乎全嵌在含字面空格的排版内容里，按本节规则该留在 expl3 之外，
而模块本身几乎全是这类内容）。

迁移一个模块的验收三步，缺一不可：

1. `make doc` 要过。手册会把 dtx 的注释排印出来，注释里写错宏名不会影响 `.cls`
   的生成，只在这一步暴露。已经踩过：`\opt{}` 本项目没有（应为 `\option{}`），
   `\cs{}` 的参数里 `_` 会被当成数学下标（要写 `\_`）。
2. `l3build check` 全过。
3. 与改动前的 PDF 逐字节比对。挑变体容易漏，`thesis-pagestyle` 那次 42 个里有 21 个
   变了，只挑几个未必抽中，所以跑全量。建参照树用
   `git worktree add --detach <目录> <上一个提交>`，比在原地 `git stash` 安全。

命名向 fduthesis 与 BIThesis 看齐：内部函数 `\__hit_模块_动作:参数签名`，变量
`\g__hit_描述_类型` / `\l__hit_描述_类型`。等有成规模的 expl3 代码之后再引入
`l3docstrip` 的 `%<@@=hit>` 前缀替换，那之前先写全名。

**底层名字一律写全称，不缩写。** 长一点没关系，看不懂才要命。`caption@separator`
不写 `capsep`，`page@number@main` 不写 `pagenum@main`，`theorem` 不写 `thm`，
连 `or` 这样的虚词也留着。分隔符：`\hit@…` 这层用 `@`（控制序列里不能有连字符，
`-` 是 catcode 12，控制词读到就断），expl3 那层用 `_`。

三种情况例外：

- **接管第三方定义时**，用 `\hit@original@…` 保存原定义，后半截照样写全称，别抄内核
  的缩写：存 `\@makefnmark` 的叫 `\hit@original@make@footnote@mark`，存 `\LT@array`
  的叫 `\hit@original@longtable@array`，存 `\def@NAT@last@yr` 的叫
  `\hit@original@natbib@last@year`。存的是谁，写在紧跟的注释里。
- **标志位对应用户选项时**，名字跟着选项键走，别另起。`g__hit_arialtitle_bool` 对
  选项 `arialtitle`，改成别的反而断了对应关系。选择型选项的标志位是
  `g__hit_<键名>_<取值>_bool`，前缀必须与键名一致。
- **拼音名**（`cxueke`、`ziju` 这些）暂时保留，等元信息字段那轮统一处理。

## 5. 新增模块的步骤

以给 `thesiscls` 加 `thesis-footnote` 为例（这个模块已经存在，仅作示范）：

1. 在 dtx 里加守卫块。位置按现有 cls 的内部顺序选：

   ```
   % ^^A ======================================================================
   % ^^A Module thesis-footnote: 脚注样式与编号（thesis）
   % ^^A ======================================================================
   %<*thesis-footnote>
   ...实际代码...
   %</thesis-footnote>
   ```

2. 在 `hithesis.ins` 的对应 `\file{...book.cls}` 里插一条 `\from`：

   ```
   \from{hit-thesis.dtx}{thesis-footnote}
   ```

   位置就是它要被执行的位置。docstrip 严格按 `\from` 的书写顺序输出，与守卫块在 dtx 里的位置无关。三处 `\file`（根目录、chinese、english）都要改。

   加载顺序敏感：如果新模块依赖 enumitem、hyperref 这些已在 `X-deps` 里加载的包，`\from` 要排在 `X-deps` 之后。

3. `make cls` 生成。

4. 编译验证：至少跑一遍受影响 cls 的示例，确认没有 LaTeX 报错、PDF 渲染正常。

5. 跑排版比对，见 §6。

## 6. 改动的验证

排版类改动一律要过比对，光“能编译”不算数。

改动前先存基线：

```shell
make baseline      # 42 个变体
make doc-baseline  # 手册
```

改完之后：

```shell
make smoke      # 42 个变体与基线逐页比
make doc-check  # 手册与基线逐页比
```

纯重构（只挪代码、不改行为）的验收标准是零差异。有意的样式调整则要逐页确认差异是否符合预期，`tests/diff/` 下有标红的差异图。

手册有一点要注意：它会把源码连同行号一起排印，所以改代码必然让行号位移、索引重排。只有纯文档类改动才该期望 `make doc-check` 零差异。

CI 会在推送后跑这几项：

| 检查 | 内容 |
|---|---|
| TeX Live 矩阵 | 2022–2026 五个版本各编一遍文档与四个示例 |
| 跨平台 | macOS 与 Windows 上编译示例 |
| 变体矩阵 | 42 种 `\documentclass` 选项组合 |
| 排版回归 | 与参照版本逐页比对，差异出报告与截图 |

细节见 [tests/README.md](tests/README.md)。

## 7. 提交规范

### 7.1 commit 消息

用 [Conventional Commits](https://www.conventionalcommits.org/zh-hans/)，描述写中文：

```
<类型>(<范围>): <一句话摘要>

详细说明：改了什么、为什么、影响范围、验证结果。
```

摘要用祈使句，不加句号，控制在 50 字以内。范围可省，也可以像 `fix(thesis,report):`
这样并列多个。破坏性变更在类型后加 `!`，并在正文里用 `BREAKING CHANGE:` 起一段
说明用户要怎么改。

| 类型 | 用在什么上 |
|---|---|
| `feat` | 新功能、新选项 |
| `fix` | 修 bug |
| `docs` | 用户手册、README、CONTRIBUTING，用范围区分改的是哪一份 |
| `style` | 只动排版格式与注释，不改行为 |
| `refactor` | 重构，行为不变 |
| `test` | 变体定义、`testfiles/`、比对脚本 |
| `build` | `Makefile`、`build.lua`、`hithesis.ins`、打包脚本 |
| `ci` | `.github/workflows/` |
| `chore` | 版本号、依赖清单等杂项 |
| `revert` | 回滚 |

范围取改动落在哪里：

| 范围 | 对应 |
|---|---|
| `thesis` `report` `szmidterm` | 各个类，当前是 `src/hit-thesis.dtx`、`src/hit-report.dtx`、`src/hitsz-midterm-report.dtx` |
| `shared` | 各个类共用的底层模块 `src/shared/hit-*.dtx` |
| `bst` `eps` | 参考文献样式、图像数据 |
| `manual` | 用户手册 `src/hit-doc.dtx` |
| `readme` `contributing` | 对应的 md 文件 |
| `tests` `scripts` | `tests/`、`testfiles/`、`tools/`、`scripts/` |
| `deps` | 依赖清单 `.github/tl_packages` |

手册的范围叫 `manual` 不叫 `doc`，是为了跟类型 `docs` 区分开。`docs(doc):`
这种写法只会让人猜半天。范围能省则省，但**同一类型能落在多处时就该写**：
`docs:` 看不出改的是手册还是 README，`docs(manual):` 一眼就知道。

```
feat(thesis): 增加深圳校区博士封面的联合导师字段
fix(report,szmidterm): 修正中期报告页眉在偶数页丢失
refactor(thesis): 把封面绘制从 thesiscls 拆到 thesis-cover 模块
docs(manual): 补充 newgeometry 三个取值的版心差异
docs(contributing): 提交消息改用 Conventional Commits
test: 补充 report 与 szmidterm 的字段清单交叉验证
ci: l3build check 铺到所有 TeX Live 版本
```

`master` 上必须守这套。`dev` 上历史遗留的不规范消息不追溯，但新提交照此写。

### 7.2 不要提交

- 临时调试代码
- 未注明出处与许可的、从别的模板拷来的代码

### 7.3 commit 粒度

- 一个 commit 一件事，方便逐 commit 审
- 大重构按阶段分多个 commit
- 跨模块的批量改动可以放一个 commit，但要在消息里列出涉及范围

## 8. 分支与 PR

### 8.1 分支

- `master` 是稳定分支
- `dev` 是开发分支，维护者从这里合入新版本
- 协作者从 `dev` 派生 `feature/<topic>`

`dev` 合进 `master` 时压成一个 commit。开发期的提交是按调试节奏切的，逐条读
对使用者没有价值；`master` 的历史应该一个 commit 对应一件对用户有意义的事。
压出来的消息按 7.1 写，正文列清改了哪些方面、用户接口有没有变。

### 8.2 流程

```shell
# fork 后克隆自己的 fork
git clone https://github.com/<you>/hithesis.git
cd hithesis
git remote add upstream https://github.com/hithesis/hithesis.git

# 从最新 dev 派生分支
git fetch upstream
git checkout -b feature/my-topic upstream/dev

# 改完推到自己 fork，再开 PR
git push -u origin feature/my-topic
```

不要直推 `upstream/master`，不要对 `upstream` 任何分支 `git push --force`，不要把 feature 分支推成 master。有写权限也走 PR，不绕过 review。

### 8.3 PR 里要写

- 一句话说明解决了什么问题
- 关键改动列表
- 用户接口影响：零影响还是有可见变化
- 验证结果：跑过哪些示例、比对结果如何
- 影响渲染的话附截图或 PDF

## 9. 演进策略

### 9.1 加新选项或命令

允许，条件是：默认值保持旧行为、文档说明用途、加 `\changes` 条目。

### 9.2 移除老接口

走三段废弃期：

1. 可选期：新接口可用，旧接口保留，文档提示推荐新接口
2. 默认切换：默认改为新接口，旧接口保留为兼容选项
3. 彻底移除：删旧代码，属于 breaking change

具体计划依情况讨论。

### 9.2b 版本号

版本号散在三处：`src/hithesis.dtx` 的 `\ProvidesFile`（唯一的源，Makefile 取它命名发布包，手册封面的 `\date{v\fileversion (\filedate)}` 也读它）、同一文件里五条 `\ProvidesExplClass` / `\ProvidesExplFile`、以及四个示例开头 ASCII 横幅里的 `hithesis vX.Y`。手册里那四处展示是 `\lstinputlisting` 把示例源码贴进来的，改完示例跑一次 `make doc` 就跟上了。

一处改全部同步：

```
make version                       # 列出各处版本，不一致时退出码 1
make version-check                 # 同上，CI 用
make version-set VERSION=3.2b DATE=2026/08/07
```

横幅是等宽 ASCII 画，左边距是手工对齐过的（两行文字起点在同一列），脚本只补右边的空白，不重新居中，右边的图形不会错位。版本号等长时（3.2a → 3.2b）一个字符都不动。

`\changes` 条目里的版本号与正文里“v3.2a 起……”这类叙述**不在同步范围**：前者是历史记录，后者说的是某项改动发生在哪一版。

发版顺序：`make version-set` 定版本 → `scripts/changes.py --stamp` 填 changes 的日期 → 打 tag。

### 9.3 跨类改动

一个改动对多个类都适用时，每处都要同步。如果改的是各套规范一致的底层机制，考虑抽进 `src/shared/`，见 §4.2。

## 10. 常见陷阱

| 陷阱 | 现象 | 处理 |
|---|---|---|
| hyperref 加载顺序 | 引用、书签锚点错乱 | hyperref 已在 `X-deps` 内部的精确位置加载，别在其他模块重新加载 |
| enumitem 覆盖 cft* 长度 | 目录间距异常 | `X-toc` 的 `\from` 要排在 `X-deps` 之后 |
| `\from` 顺序写错 | 宏未定义、样式失效 | docstrip 按 `\from` 顺序输出，不按守卫块在 dtx 里的位置 |
| 新加的 dtx 排在共用文件之后 | `Incompatible order of input files` | docstrip 给同一个 `\file` 里重复出现的输入文件按出现次序各记一条，全局只有一张追加式的文件表。两个 cls 各自大量引用同一个 dtx、之后又共用另一个 dtx，就排不出一致的先后。`reportcfg` 因此留在 `hit-report.dtx` 里没有单独成文件 |
| 模块内残留 `\ProvidesPackage` | 日志里出现不存在的宏包 | 模块拼进 cls，不该有包身份声明 |
| 守卫缺失 | 代码漏进别的文件 | 每个 `%<*X>` 都要有配对的 `%</X>` |
| `\changes` 文本里写了 `=` | `make doc` 报 `Extra }`，修改记录那条目被拦腰截断 | `gglo.ist` 把 `=` 当 makeindex 的 actual 分隔符。改成 `\option{font} 取 \texttt{auto}` 这种写法，别写 `font=auto` |
| 给 expl3 内部名套 `\begin{macro}` | `make doc` 报 `Missing $ inserted` | 名字里的 `_` 在文档模式下是下标。`\__hit_...` 这类只写普通说明，不套 `macro` 环境 |
| `\changes` 漏写 | 看不到历史脉络 | 迁移、重命名、删除都要写 |
| 在 expl3 里走裸 `\input` 加载文件 | 被读进来的文件按 expl3 的 catcode 解析，带字面空格的键名散架。`\usetikzlibrary{calc}` 会报 `/tikz/cs/point/.storein` 未知 | `\RequirePackage` 没问题（LaTeX 加载宏包时会恢复 catcode），但 `\usetikzlibrary` 这类自己 `\input` 的要用 `\ExplSyntaxOff` 圈起来 |
| 在 expl3 里用 `\patchcmd`/`\pretocmd`/`\apptocmd` | 目标宏的排版悄悄错位。etoolbox 会把宏体 detokenize 后按当前 catcode 重扫，体内的字面空格被吃掉。踩过一次：`\pretocmd{\@makefntext}` 让脚注整块上移 4.2pt，正文一个字没动、页数没变，`pdftotext` 比对看不出来 | 用 `\ExplSyntaxOff` 圈起来。fduthesis、bithesis、sjtuthesis 一处 etoolbox 补丁都不用，长远看这些补丁值得换掉 |
| expl3 里换行也被忽略 | 多行文本值里，行末换行原本产生的空格没了，空行原本产生的 `\par` 也没了 | 行末补 `~`（行末是控制词的不用补，那个空格本来就被吸收），空行写成 `\par` |
| 用脚本批量给常量表加 `\ExplSyntaxOn` | 常量变 `\relax`、分支走错、`Incomplete \iffalse` | 三种切法都会出事：切进跨模块守卫的语句中间、切在 `\hit@if@both@options@TF{a}{b}` 与它的两个分支之间、切进多行文本值内部。只能逐条手工包，包完用常量 dump 对照（见下） |
| 改常量表后只跑 42 变体 | 没被封面用到的常量改坏了也看不出来 | 先 dump 全部 131 个常量在 master/doctor/bachelor/postdoc 四档下的 `\meaning` 做基线，改完再 dump 比对 |
| `\ExplSyntaxOn` 写在花括号参数里 | 代码看着在 expl3 里，空格却没被忽略；如 `\addcontentsline { toc }` 的 `#1` 变成 ` toc `，条目静悄悄丢失 | catcode 在读参数时就定了，`\ExplSyntaxOn` 放进 `\hit@if@option@TF{…}{…}` 这类参数中无效。把定义挪到参数外面各自取名，再用 `\hit@if@option@TF` 选一个 `\cs_new_eq:NN` 过去 |
| `\ifthenelse{\equal{}}` 换成 `\str_if_eq:eeTF` | 编译报 `Incomplete \iffalse`、整段被吞 | 两者不等价。`\equal` 走 `\protected@edef`，挡得住 `\hspace` 这类不可展开的命令；`\str_if_eq:ee` 是完全展开。被比较的内容可能含排版命令时不要换 |

## 11. 求助

- GitHub Issues：https://github.com/hithesis/hithesis/issues
- QQ 群：见 README.md

提问前先按上面的表找到对应文件，`grep` 一下看有没有类似实现。
