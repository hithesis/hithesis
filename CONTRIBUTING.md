# 贡献指南

本文写给要改代码的人：修 bug、加功能、调整文档结构。只是提 issue 或反馈样式问题的模板用户不必读。

---

## 1. 项目结构

```
hithesis/
├── src/
│   ├── hithesis.dtx            <- 入口：driver、共用文件头、派发类 hithesis.cls、旧类名空壳
│   ├── hit-thesis.dtx          <- 学位论文类 hit-thesis 的骨架：LoadClass 与前后钩子
│   ├── hit-report.dtx          <- 开题中期类 hit-report 的骨架，同上
│   ├── hit-bst.dtx             <- 参考文献样式 hithesis.bst（官方 gbt7714 底座）
│   ├── hit-ist.dtx             <- 索引排序样式 hithesis.ist
│   ├── hit-dtx-style.dtx       <- 排手册用的 dtx-style.sty，不随模板发布
│   ├── hit-sty.dtx             <- 示例宏包 hithesis.sty，示例文档自己 \usepackage
│   ├── manual/                 <- 用户手册 hit-manual.dtx，纯文档，不产出任何文件
│   ├── assets/                 <- EPS 图像数据 hit-eps.dtx，纯数据，不含代码
│   ├── setup/                  <- 设置子系统：选项、键、常量，见 §4.3
│   ├── utils/                  <- 各个类共用的小工具，守卫叫 shared-*，见 §4.3
│   ├── flow/                   <- 单类专属的排版配置：版心、页眉页脚、章节标题、
│   │                              段落、浮动体、字体、数学、脚注、超链接、第三方依赖
│   └── pages/                  <- 论文的一页一个文件
│                                  flow/ 与 pages/ 全是单类专属，文件名带类名
├── hithesis.ins          <- docstrip 驱动文件，src/hithesis.dtx 的 install 守卫的产物。
│                            提交进仓库随包发出去，开发时不改它、也不用它解压
├── build.lua             <- l3build 配置：unpack / distribute / doc / check / ctan
├── Makefile              <- 构建与测试入口
├── latexmkrc             <- latexmk 配置
├── scripts/              <- 打包、依赖清单、回归测试、changes 提取、标点检查
├── tools/                <- 排版测试脚本
├── tests/                <- 变体定义与测试说明
├── testfiles/            <- l3build 的宏级测试：*.lvt 用例与 *.tlg 基线
├── examples/demo/        <- 一棵示例树：开题、中期、学位论文放在同一个目录
│   ├── hitsetup.tex      <- 三份共用的元信息
│   ├── thesis.tex  thesis-en.tex  proposal.tex  interim.tex   <- 四个入口
│   └── front/ body/ back/ figures/
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
make manual       # 编译用户手册 hithesis.pdf
make distribute   # 只做分发（cls 已经生成过时用）
make clean        # 清理生成产物
make changes       # 从 \changes 生成 RELEASE_NOTES.md
make changes-check # 校验 \changes 的日期约定
make constlint     # 常量键有没有声明了却没人取用的（先 make cls）
make logcheck      # 扫编译日志里那几类「编得过但有毛病」（先把变体编出来）
make changes-fix   # 自动修正能修的部分
make depscheck     # 每个 \RequirePackage 都在 tools/deps-policy.txt 里交代了归属
make depslist      # 按当前代码打印一份策略表骨架，加包时拿它起草
```

测试相关：

```shell
make baseline        # 45 个变体全编一遍，渲染结果存成本地基线
make smoke           # 重编并与本地基线逐页比
make regression-test # 与参照版本逐页比，发版前跑
make manual-baseline # 改动前存一份手册 PDF
make manual-check    # 改完与之比对
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
cd examples/demo && make thesis     # 学位论文
cd examples/demo && make report     # 开题、中期报告
```

## 3. dtx 导航

`src/` 按职责分六个目录：

```
src/
  setup/    选项、键、常量：有哪些字段、字段取什么值、怎么声明
  utils/    小工具，两个类共用
  flow/     单类专属的排版配置：版心、页眉页脚、章节标题、段落、浮动体、
            字体、数学、脚注、超链接、第三方依赖
  pages/    论文的一页一个文件：封面、摘要、目录、声明、致谢、成果、决议、附录、参考文献
  manual/   用户手册的正文，纯文档，不产出任何文件
  assets/   EPS 图像数据，纯数据，不含代码
```

`setup/` 里三层分工：`hit-keylist.dtx` 说“有哪些字段”，`hit-defaults.dtx` 说
“字段取什么值”，`hit-key-engine.dtx` 与 `hit-option-engine.dtx` 是造这两者的机制。
详见 §4.2。

手册目录叫 `manual/` 不叫 `doc/`：`src/` 下每个 dtx 都产出文档，注释都由
`\DocInput` 织进 `hithesis.pdf`，`doc/` 这个名字占不住；而且 `doc` 在 LaTeX 里
已经指 `doc` 宏包那套排手册的机器，那套在本仓库是 `src/hit-dtx-style.dtx`。
`manual/` 说的是用户手册这一份具体产物。

`flow/` 与 `pages/` 里的文件按类分开，`hit-thesis-cover.dtx` 是毕业论文封面，`hit-report-cover.dtx`
是开题报告封面。不共用，是 docstrip 逼的：它给同一个输出里重复出现的输入文件改名
（原名后面添空格），并要求每个输出的输入文件表是全局表的子序列。一个输出一旦用上
自己独有的文件，扫描位置就落到全局表尾部，再回头引用排在前面的共享文件就找不到，
报 `Incompatible order of input files`。

推论：**共享文件必须全部排在类骨架第一次出现之前**。所以 `utils/hit-bibstyle.dtx`
排在选项区，而不是排在两个类的参考文献模块旁边。这也决定了哪些代码抽得动：
要在类骨架之后才能跑的（比如读类选项取值的），抽不动。

先按家族找文件，再在文件里按 docstrip 守卫找模块：

| 要改什么 | 打开哪个 |
|---|---|
| 不知道该改哪 | `src/hit-thesis.dtx`、`src/hit-report.dtx` 开头的装配表：这个类由哪些文件按什么顺序拼出来，一目了然。表是 `install` 守卫的产物，改完那边跑 `make mapfix` |
| 常量的默认值（改学校规范） | `src/setup/hit-defaults.dtx` |
| 有哪些信息字段与常量 | `src/setup/hit-keylist.dtx` |
| 这个类有哪些类选项 | `src/setup/hit-thesis-options.dtx`、`src/setup/hit-report-options.dtx` |
| 键与选项的声明机制 | `src/setup/hit-*-engine.dtx` |
| 改一句提示文案 | `src/utils/hit-messages.dtx` 一处，24 条全在里面 |
| 前置后置排哪些部件 | `src/utils/hit-structure.dtx` 声明键，`src/flow/hit-*-matter.dtx` 定顺序 |
| 第三方宏包加载与先后 | `src/flow/hit-thesis-deps.dtx`、`src/flow/hit-report-deps.dtx` |
| 哪个类装哪个基础类 | `src/hit-thesis.dtx`、`src/hit-report.dtx`，各只有一句 `\LoadClass` |
| 各个类共用的小工具 | `src/utils/hit-*.dtx` |
| 论文的某一页 | `src/pages/hit-thesis-*.dtx`、`src/pages/hit-report-*.dtx` |
| 版心、页眉、标题、浮动体、字体、数学、脚注 | `src/flow/hit-thesis-*.dtx`、`src/flow/hit-report-*.dtx` |
| 参考文献样式 | `src/hit-bst.dtx` |
| 索引排序样式 | `src/hit-ist.dtx` |
| 排手册用的样式 | `src/hit-dtx-style.dtx` |
| 示例文档自己要用的东西 | `src/hit-sty.dtx` |
| 用户手册文字 | `src/manual/hit-manual.dtx` |
| 类的公共文件头、派发类、旧类名空壳 | `src/hithesis.dtx` |

**文件名的规矩：`hit-<类>-<职责>.dtx` 是单类专属，`hit-<职责>.dtx` 是共用。**
`flow/` 与 `pages/` 里一个共用的都没有，全部带类名前缀；`utils/` 里全部共用，
一个前缀都不带，守卫也统一叫 `shared-*`。看文件名就知道改它会影响谁。

**52 个 dtx 的文件名必须全局唯一。** `src/` 下按职责分了目录，但解压规则
里按裸文件名引用，`l3build ctan` 打包和 TDS 的 `source/latex/hithesis/` 也都是平
的。两个目录下同名的文件，打包后会互相覆盖。这也是类名前缀只能写进文件名、不能
改成 `flow/thesis/` 与 `flow/report/` 两个子目录的原因——拍平之后就撞了。

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

**判断一个名字能不能改，看它在最后一个 tag 里有没有，不看当前版本发没发布。**
这条我们栽过：v3.2a 把固定词汇改成了 `const` 族的键，那套机制 v3.1e 根本不存在，
所以那 55 个键去掉 `-zh` 后缀是零成本的。顺手把同一个结论套到宏上就错了——
`\theVector` 那九个数学速记在 `v3.1e:hithesis.dtx:8889` 就有，2017 年随
`hithesis.sty` 发出去过，改名或加前缀等于让老文档报 `Undefined control sequence`。

查法：

```shell
git show v3.1e:hithesis.dtx | grep -c '\\theVector'
```

**公开面有一份清单：`.github/public-api.txt`。** 类里定义的宏，名字不带 `@` 也不带
`_` `:` 的，用户在正文里就能直接调用。`scripts/check-api.py` 扫生成的 cls，跟清单
对一遍，没登记的报错。新写一个不带前缀的全局宏，这道门会拦：

```
myNewPublicThing 定义在类里但不在公开面清单上。它是能被用户打出来的名字，
要么登记进 .github/public-api.txt，要么改名带上 hit@ 前缀
```

清单分五节。“重定义”那节是上游内核或宏包的命令，名字必须保持原样，改了上游就
找不到；这一节由 `check-api.py --probe` 实测得出，装上同一套宏包但不装 hithesis，
逐个 `\ifdefined` 探一遍。“示例宏包”那节由 `hithesis.sty` 提供，不是类给的，用户
不写 `\usepackage{hithesis}` 就没有；名字同样不能改。名字在哪一节由脚本按它实际
定义在哪个生成物里判定，放错节也会报。

判断一样东西该进类还是进示例宏包 `hithesis.sty`（源文件 `src/hit-sty.dtx`），看类自己调不调。`siunitx`、`bm`、
`mathrsfs`、`rotating`、`listings`、`algorithm2e` 这六个宏包类里一句都没用到，
只是替文档预先装上并配好，就归示例宏包；封面要用的 `xcolor` 与 `tikz` 留在类里。

### 4.2 设置分三层：engine / keylist / defaults

`src/setup/` 是设置子系统，从造键到给值分三层，各层只做一件事：

| 层 | 文件 | 装什么 |
|---|---|---|
| engine 造键 | `hit-key-engine.dtx`、`hit-option-engine.dtx` | 怎么声明一个键、`\hitsetup` 入口、条件判断函数。只定义，一句执行都没有 |
| keylist 列键 | `hit-keylist.dtx` | 有哪些信息字段与常量。三个守卫：`shared-keylist` 两个类都取，`thesis-keylist` 与 `report-keylist` 各取各的。只声明，不给值 |
| defaults 给值 | `hit-defaults.dtx` | 常量的默认值。只给值，不声明；用户的 `\hitsetup` 晚于它执行，照样能盖掉 |

改学校规范只动 defaults，加一个字段动 keylist，改键的工作方式才动 engine。

**类选项不在这三层里，在各自的类文件。** `degree-level`、`campus`、`fontset` 这些写在
`\documentclass[…]` 里的东西，声明在 `src/hit-thesis.dtx` 与 `src/hit-report.dtx` 的
`*-options` 守卫，紧挨着 `\LoadClass`。它们不是清单：那一段除了声明，还跑
`\ProcessKeyOptions`、`\PassOptionsToPackage`，以及“没给 degree-level 就置 bachelor”这类
兜底逻辑，是类加载序列的一部分，必须在 `\LoadClass` 之前执行完。放进 keylist 试过，
那一层“只声明不执行”的规矩立刻就破了。

**加一个常量**（模板给的固定词汇，比如封面多一栏标签）：

1. `hit-keylist.dtx` 的 `\hit@declare@constant{…}` 列表里加键名 `foo-bar-zh`。
   两个类都要就加进 `shared-keylist` 那一份，只有一个类要就加进对应的那份
2. `hit-defaults.dtx` 里 `\hit@presetup{ const = { foo-bar-zh = {某某} } }`
3. 版式里写 `\hit@foo@bar@zh`。键名的 `-` 换成 `@`、前缀 `hit@`，换算是自动的

**加一个用户填的字段**（题目、作者那一类）：

1. `hit-keylist.dtx` 里 `\hit@define@term{foo-zh}` 造写入器
2. 同文件的 `\hit@declare@info@field{…}` 列表里加 `foo-zh`，把 `hit/info` 族接上去
3. 版式里写 `\hit@foo@zh`，用户写 `\hitsetup{ info = { foo-zh = {某某} } }`

两条路都不碰 engine。常量的值里可以写 `<别的键名>` 交叉引用，例如
`author-field-label-zh = {<degree-level-zh>研究生}`，设值时就展开。

**engine 里的函数名：`define` 造出新名字，`declare` 只把已有的名字登记成键。**

| 造名字 → define | 只登记 → declare |
|---|---|
| `\hit@define@term` 造写入器 | `\hit@declare@class@key` 只 `\keys_define:nn` |
| `\hit@define@title`、`\hit@define@legacy@title` | `\hit@declare@info@field` |
| `\hit@define@legacy@term`、`\hit@define@legacy@terms` 造别名 | `\hit@declare@constant`、`@as`、`@ctex` |
| `\hit@define@condition` 造 `\hit@if@…` 一对 | |
| `\hit@define@boolean@option` 造标志位 | |
| `\hit@define@string@option`、`@as` 造 `\hit@<名>` | |
| `\hit@define@choice@option` 每个取值造一个标志位 | |

**一个例外要留意。** `\hit@define@string@option@as` 造出来的是文本宏（`\hit@fontset`），
不是标志位。option-engine 造的东西一般落在 `\g__hit_<名>_bool` 上给 `\hit@if@…` 选分支，
字符串选项落在文本宏上。它归 option-engine 是因为加载期就要用，不是因为存法。

**`\hit@presetup` 那套排队回放机制住在 `hit-defaults.dtx` 顶上，不在 engine 层。**
按分层它是机制，但 `hit-defaults.dtx` 在解压清单里排在第二位、自己就调用了
107 次 `\hit@presetup`，而 engine 排在一百多行之后。定义必须早于调用，挪不动。

**共用文件必须排在每个块的前面。** docstrip 的输入文件表全局只增，一个被两份输出
共用的文件，只有排在每份输出各自要求的位置之前，先后才彼此相容。排在中间会报：

```
! DOCSTRIP error: Incompatible order of input files specified for file `hit-report.cls'
```

`hit-keylist.dtx` 一度按类分成两个文件，就是因为它当时排在类骨架之后。后来实测它
根本不需要类骨架给的任何东西，提到 `*-options` 之前照样逐字节一致，于是能合成一个
共用文件、共用那 96 个键名。加新文件时先想清楚它要排在哪，再决定能不能共用。

### 4.3 版式各写各的，底层机制共用

各个 cls 的版式代码物理隔离，由各自的 `<类>-*` 模块承载。当前是两个：`thesis-*` 在 `src/hit-thesis.dtx`，`report-*` 在 `src/hit-report.dtx`。每个类对应一套学校规范，各自演化，碰巧相似的版式不要合并，规范一独立变动就会变成维护负担。新增一个类就是新增一个 `hit-<名>.dtx` 加一组 `<名>-*` 模块。

反过来，同一套规范下的分支不要单开一个类。深圳博士中期原先是 `hithesisartplus`，与 `hithesisart`（今 `hit-report`）九成代码逐字相同，差的只有封面、页眉、节标题、正文行距四处；v3.2a 并回 `report-*`，由 `campus=shenzhen,degree-level=doctor,stage=interim` 三个选项选中，与其余十七格并列。判断标准是差异在哪一层：规范不同才分类，版式不同就加分支。

底层机制是另一回事。字号、数学、表格、脚注这些各套规范要求一致的东西，共用一份放在 `src/utils/hit-*.dtx`，守卫叫 `shared-*`：

| 文件 | 管什么 |
|---|---|
| `hit-fonts.dtx` | 中西文字体与字号阶梯 |
| `hit-math.dtx` | amsmath/thmtools、定理环境、`eqdenote` |
| `hit-table.dtx` | 长表格字号 |
| `hit-footnote.dtx` | 带圈脚注号与脚注版式 |
| `hit-list.dtx` | `enumitem` 加载、列表间距、`publist` |
| `hit-key-engine.dtx` | `\hitsetup` 的键机制与旧名兼容 |
| `hit-hyperlink.dtx` | hyperref 配置（书签、链接边框、url 字体） |
| `hit-title.dtx` | `title` 键的解析与三种取用 |
| `hit-caption.dtx` | 双语题注（`\caption{中}[英]`）与 `\bicaption` 兼容 |
| `hit-subfigure.dtx` | `\subfigure` 兼容层，整个文件到 v4 可删 |
| `hit-option-engine.dtx` | 选项声明助手与读标志位的判断函数 |

判断标准是“各套规范会不会分开改”。会分开改的（封面、页眉、章节标题、目录）留在各自的类文件里；不会的（`\hitsetup` 怎么解析键、字号阶梯怎么定义）才进 `utils/`。

`utils/` 的写法与类模块不同：文件里只放定义，需要在特定时机执行的部分包成 `\hit@setup@<名>`，由各个类在原来那段代码所在的位置调用。这样共享之后生成物的执行顺序不变，能用“生成的 cls 逐字节不变”来验收。

例外：`hithesis.bst`（或将废弃并切换到 biblatex-gb7714）和 `hit-eps.dtx` 也跨类共享，但它们不走 `utils/`，因为不是拼进 cls 的模块。

### 4.4 一个模块一个职责

模块名要能反映它唯一的职责：

模块名的形式是“类-职责”，类的前缀是 `thesis` / `report` / `shared`：

- √ `thesis-chapter` 只管毕业论文的章节标题格式
- √ `thesis-bib` 只管毕业论文的参考文献加载与样式
- × `thesis-floats` 兼管列表、定理、段落、引用

加代码前先问这段代码语义上属于哪个模块，找到答案再写。找不到就考虑拆一个新的出来，见 §5。

### 4.4b 第三方宏包放哪儿

`\RequirePackage` 按三条分家：

| 情况 | 放哪儿 |
|---|---|
| 类自己一处都不调，纯粹替用户预装 | `src/hit-sty.dtx`（出 `hithesis.sty`） |
| 类自己调，两个以上模块调 | `src/flow/hit-*-deps.dtx` |
| 类自己调，只有一个模块调 | 那个模块里自己 `\RequirePackage` |

每个包归哪儿、为什么，一行不落地写在 `tools/deps-policy.txt`。加了新包不写进去，`make depscheck` 会点名，CI 也会拦。起草新条目跑 `make depslist`。

一个包在多处加载得每处都是有意为之，把理由写进策略表那一条。纯粹的重复加载（后一次被 LaTeX 直接跳过）该删掉。

判断“谁在调”只能靠人读代码，脚本不猜。扒宏包提供了哪些宏这条路走不通：`\includegraphics` 定义在 `graphics.sty` 而不是 `graphicx.sty`，`subcaption` 的环境由 `caption` 的机制造出来，`hyperref` 重定义了 `\label` 与 `\ref`。据这种名单下结论会把能编的类改坏——`environ` 就差点被误删，它的消费者是摘要环境里的 `\Collect@Body`，不是常见的 `\NewEnviron`。

拿不准就删掉试编。45 变体逐字节比对是唯一靠得住的判据，见 §6。

### 4.5 模块内不写 `\ProvidesPackage`

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

### 4.6 `\changes` 历史条目

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

### 4.7 expl3 迁移

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

**`~` 排不排得出来还看它在行里的位置。** `~` 是空格字符，而 TeX 只在“行中”
（state M）这个词法状态下才把空格读成空格记号。行首（刚换行，state N）与控制字
之后（state S）都会把它丢掉。所以下面两种写法不等价：

```latex
 \hit@cover@row*{日期}{2023}~     % ~ 在行中，排出一个空格

 \hit@cover@row*{日期}{2023}
 ~                                % ~ 在行首，什么也不排
```

删条件分支时最容易撞上：`\hit@if@option@TF{...}{A}{B}~` 那个尾随 `~` 跟在右花括号
后面属于行中，是排出来的；把条件删掉、`~` 挪到单独一行，那个空格就没了。删掉
深圳本科分支时威海本科封面第二列因此窄了 1.875pt，`\unskip` 撤掉的东西变了。
把 `~` 贴在上一行末尾即可。

**反方向也踩过：从 expl3 里搬到 `\hit@presetup` 的取值里，原有的 `~` 要去掉。**
配置文件的 `\hit@presetup{...}` 取值是在 `\ExplSyntaxOff` 下记号化的，那里 `~` 又变回
不断行空格。把 cls 里的 `\hit@if@option@TF{interim}{中期~}{...}` 照抄成常量取值
`{<stage-interim>~报告}`，页眉就从“中期报告”变成了“中期 报告”，两个深圳硕士变体
的 PDF 有差异。cls 里那个 `~` 本来是可忽略空格，随后被 xeCJK 在两个汉字之间吃掉，
搬到配置里就吃不掉了。

判断方法：看这段代码最终在哪个语法下被记号化，不是看它从哪抄来的。

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

这批定义在 `src/setup/hit-option-engine.dtx`，各个类共用。

另有若干针对具体组合的具名函数，由 `\hit@define@condition{名}{布尔表达式}` 生成，
名字读下来就是条件本身：`\hit@if@harbin@master@or@doctor@or@shenzhen@master`、
`\hit@if@harbin@master@proposal@or@interim`。末尾带 `@TF` 的要给两个分支。

已迁移：`thesis-geometry`、`report-geometry`、`thesis-mainmatter`、`report-chapter`、
`report-pagestyle`、`report-toc`、`thesis-toc`、`thesis-pagestyle`、`report-floats`、`thesis-deps-c`、
`thesis-glossary`、`report-deps-a`、`thesis-deps-a`、`report-options` 与
`thesis-options`、`report-options`、
`thesis-keylist`、`report-keylist`、`thesis-floats`、`thesis-hyperlink`、
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
以 `}` 或普通字符结尾的分支，那个空格是真的。`\ifhit@proposal {\ } \else \enspace \fi`
的真分支是 `{\ }` 加一个空格，写成 `\hit@if@option@TF{proposal}{{\ } }{\enspace}` 才对。

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

1. `make manual` 要过。手册会把 dtx 的注释排印出来，注释里写错宏名不会影响 `.cls`
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

加一个**产物**（不是模块）时，权威清单只有 `src/hithesis.dtx` 的 `install` 守卫，
另外三份从它派生：`tools/distfiles.txt`（拷进示例目录的）、`build.lua` 的
`installfiles`（装进 TEXMF 的）、install 守卫末尾的 `\Msg` 安装横幅。
改完跑 `make productcheck`，四份对不上会逐条说是哪一份漏了。

图片分两类。**模板资源**（封面上的校徽、题名、落款）要装进 `tex/latex/hithesis/`，
四份清单都要有。**示例与手册的内容**（`zfb.pdf` 打赏二维码、`golfer.pdf` 插图样例）
只随示例目录发，在 `tools/distfiles.txt` 里行首写 `@`，不进 `installfiles` 也不进
安装横幅——用户装完模板，`tex/latex/hithesis/` 里躺着一张二维码说不过去。
thuthesis 与 fduthesis 都是这么分的：`tex/` 下只有校徽校名，示例在 `doc/` 下，
一张图都不带。

2. 在 `src/hithesis.dtx` 的 `install` 守卫里，对应的 `\file{...cls}` 中插一条 `\from`：

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
make baseline      # 45 个变体
make manual-baseline  # 手册
```

改完之后：

```shell
make smoke      # 45 个变体与基线逐页比
make manual-check  # 手册与基线逐页比
```

纯重构（只挪代码、不改行为）的验收标准是零差异。有意的样式调整则要逐页确认差异是否符合预期，`tests/diff/` 下有标红的差异图。

手册有一点要注意：它会把源码连同行号一起排印，所以改代码必然让行号位移、索引重排。只有纯文档类改动才该期望 `make manual-check` 零差异。

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
| `build` | `Makefile`、`build.lua`、`src/hithesis.dtx` 的 install 守卫、`tools/distfiles.txt`、打包脚本 |
| `ci` | `.github/workflows/` |
| `chore` | 版本号、依赖清单等杂项 |
| `revert` | 回滚 |

范围取改动落在哪里：

| 范围 | 对应 |
|---|---|
| `thesis` `report` | 各个类，当前是 `src/hit-thesis.dtx`、`src/hit-report.dtx` |
| `utils` | 各个类共用的小工具 `src/utils/hit-*.dtx` |
| `pages` | 论文的某一页 `src/pages/hit-*.dtx` |
| `setup` | 设置子系统 `src/setup/hit-*.dtx` |
| `flow` | 页面流的版式 `src/flow/hit-*.dtx` |
| `bst` `eps` | 参考文献样式、图像数据 |
| `manual` | 用户手册 `src/manual/hit-manual.dtx` |
| `readme` `contributing` | 对应的 md 文件 |
| `tests` `scripts` | `tests/`、`testfiles/`、`tools/`、`scripts/` |
| `deps` | 依赖清单 `.github/tl_packages` |

手册的范围叫 `manual` 不叫 `doc`，是为了跟类型 `docs` 区分开。`docs(doc):`
这种写法只会让人猜半天。范围能省则省，但**同一类型能落在多处时就该写**：
`docs:` 看不出改的是手册还是 README，`docs(manual):` 一眼就知道。

```
feat(thesis): 增加深圳校区博士封面的联合导师字段
fix(report): 修正中期报告页眉在偶数页丢失
refactor(thesis): 把封面绘制从 thesiscls 拆到 thesis-cover 模块
docs(manual): 补充 newgeometry 三个取值的版心差异
docs(contributing): 提交消息改用 Conventional Commits
test: 补充 thesis 与 report 的字段清单交叉验证
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

`vX.YYYYz`：`X` 是架构大版本（整体重写才进位），`YYYY` 是这一版**服务的年份**，`z` 是该年份内的第几版，从 `a` 起。开发版在字母后接月日，例如 `v3.2a0813`，发版时去掉。

排序（左边新）：

```
v4.2027a > v4.2026b > v4.2026a > v4.2026a0813 > v4.2026a0812 > v3.2a > v3.1f
```

改的理由：`vX.YZ` 里 `Y` 与 `Z` 实际执行中重叠了——每次 `Z` 进位都带着新功能，`Y` 反而一直不动，v3.1a 到 v3.1f 六个版本 `Y` 一次没进。改成年份之后，用户拿到版本号就知道自己那份是不是当年的，也不耽误 `\changes` 按字符串排序。

版本号散在三处：`src/hithesis.dtx` 的 `\ProvidesFile`（唯一的源，Makefile 取它命名发布包，手册封面的 `\date{v\fileversion (\filedate)}` 也读它）、同一文件里五条 `\ProvidesExplClass` / `\ProvidesExplFile`、以及四个示例开头 ASCII 横幅里的 `hithesis vX.Y`。手册里那四处展示是 `\lstinputlisting` 把示例源码贴进来的，改完示例跑一次 `make manual` 就跟上了。

一处改全部同步：

```
make version                       # 列出各处版本，不一致时退出码 1
make version-check                 # 同上，CI 用
make version-set VERSION=3.2b DATE=2026/08/07
```

横幅是等宽 ASCII 画，左边距是手工对齐过的（两行文字起点在同一列），脚本只补右边的空白，不重新居中，右边的图形不会错位。版本号等长时（3.2a → 3.2b）一个字符都不动。

`\changes` 条目里的版本号与正文里“v3.2a 起……”这类叙述**不在同步范围**：前者是历史记录，后者说的是某项改动发生在哪一版。

### 9.2c `\changes` 的日期

**写这条改动做出来的那天，不是发版日。**

```latex
% \changes{v3.2a}{2026/08/13}{决议区改用 tcolorbox，能跨页}
```

原先的约定是同一版本共用发布日期（v3.1d 的 59 条全是 2025/03/03），开发期间一律写 `0000/00/00`，发版时 `--stamp` 统一填上。那样一整版几百条挤在同一天，看不出哪个功能是什么时候做的。

现在 `--stamp` 只兜底填还留着的占位符，已经写了日期的条目不动。`make changes-check` 查三样：格式是不是 `YYYY/MM/DD`、有没有写到将来、还剩几条占位符（只提醒，不算错）。`make changes-fix` 只补零，不再把日期打回占位符。

发版顺序：`make version-set` 定版本 → `scripts/changes.py --stamp` 兜底填剩下的占位符 → 打 tag。

### 9.3 跨类改动

一个改动对多个类都适用时，每处都要同步。如果改的是各套规范一致的底层机制，考虑抽进 `src/utils/`，见 §4.2。

## 10. 常见陷阱

| 陷阱 | 现象 | 处理 |
|---|---|---|
| hyperref 加载顺序 | 引用、书签锚点错乱 | hyperref 已在 `X-deps` 内部的精确位置加载，别在其他模块重新加载 |
| enumitem 覆盖 cft* 长度 | 目录间距异常 | `X-toc` 的 `\from` 要排在 `X-deps` 之后 |
| `\from` 顺序写错 | 宏未定义、样式失效 | docstrip 按 `\from` 顺序输出，不按守卫块在 dtx 里的位置 |
| 新加的 dtx 排在共用文件之后 | `Incompatible order of input files` | docstrip 给同一个 `\file` 里重复出现的输入文件按出现次序各记一条，全局只有一张追加式的文件表。两个 cls 各自大量引用同一个 dtx、之后又共用另一个 dtx，就排不出一致的先后。`reportcfg` 因此留在 `hit-report.dtx` 里没有单独成文件 |
| 模块内残留 `\ProvidesPackage` | 日志里出现不存在的宏包 | 模块拼进 cls，不该有包身份声明 |
| 守卫缺失 | 代码漏进别的文件 | 每个 `%<*X>` 都要有配对的 `%</X>` |
| `\changes` 文本里写了 `=` | `make manual` 报 `Extra }`，修改记录那条目被拦腰截断 | `gglo.ist` 把 `=` 当 makeindex 的 actual 分隔符。改成 `\option{font} 取 \texttt{auto}` 这种写法，别写 `font=auto` |
| 给 expl3 内部名套 `\begin{macro}` | `make manual` 报 `Missing $ inserted` | 名字里的 `_` 在文档模式下是下标。`\__hit_...` 这类只写普通说明，不套 `macro` 环境 |
| `\changes` 漏写 | 看不到历史脉络 | 迁移、重命名、删除都要写 |
| 在 expl3 里走裸 `\input` 加载文件 | 被读进来的文件按 expl3 的 catcode 解析，带字面空格的键名散架。`\usetikzlibrary{calc}` 会报 `/tikz/cs/point/.storein` 未知 | `\RequirePackage` 没问题（LaTeX 加载宏包时会恢复 catcode），但 `\usetikzlibrary` 这类自己 `\input` 的要用 `\ExplSyntaxOff` 圈起来 |
| 在 expl3 里用 `\patchcmd`/`\pretocmd`/`\apptocmd` | 目标宏的排版悄悄错位。etoolbox 会把宏体 detokenize 后按当前 catcode 重扫，体内的字面空格被吃掉。踩过一次：`\pretocmd{\@makefntext}` 让脚注整块上移 4.2pt，正文一个字没动、页数没变，`pdftotext` 比对看不出来 | 用 `\ExplSyntaxOff` 圈起来。fduthesis、bithesis、sjtuthesis 一处 etoolbox 补丁都不用，长远看这些补丁值得换掉 |
| expl3 里换行也被忽略 | 多行文本值里，行末换行原本产生的空格没了，空行原本产生的 `\par` 也没了 | 行末补 `~`（行末是控制词的不用补，那个空格本来就被吸收），空行写成 `\par` |
| 用脚本批量给常量表加 `\ExplSyntaxOn` | 常量变 `\relax`、分支走错、`Incomplete \iffalse` | 三种切法都会出事：切进跨模块守卫的语句中间、切在 `\hit@if@both@options@TF{a}{b}` 与它的两个分支之间、切进多行文本值内部。只能逐条手工包，包完用常量 dump 对照（见下） |
| 改常量表后只跑变体 | 没被封面用到的常量改坏了也看不出来 | 先 dump 全部 131 个常量在 master/doctor/bachelor/postdoc 四档下的 `\meaning` 做基线，改完再 dump 比对 |
| `\ExplSyntaxOn` 写在花括号参数里 | 代码看着在 expl3 里，空格却没被忽略；如 `\addcontentsline { toc }` 的 `#1` 变成 ` toc `，条目静悄悄丢失 | catcode 在读参数时就定了，`\ExplSyntaxOn` 放进 `\hit@if@option@TF{…}{…}` 这类参数中无效。把定义挪到参数外面各自取名，再用 `\hit@if@option@TF` 选一个 `\cs_new_eq:NN` 过去 |
| `\ifthenelse{\equal{}}` 换成 `\str_if_eq:eeTF` | 编译报 `Incomplete \iffalse`、整段被吞 | 两者不等价。`\equal` 走 `\protected@edef`，挡得住 `\hspace` 这类不可展开的命令；`\str_if_eq:ee` 是完全展开。被比较的内容可能含排版命令时不要换 |

## 11. 求助

- GitHub Issues：https://github.com/hithesis/hithesis/issues
- QQ 群：见 README.md

提问前先按上面的表找到对应文件，`grep` 一下看有没有类似实现。
