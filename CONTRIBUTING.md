# 贡献指南

本文写给要改代码的人：修 bug、加功能、调整文档结构。只是提 issue 或反馈样式问题的模板用户不必读。

---

## 1. 项目结构

```
hithesis/
├── src/
│   ├── hithesis.dtx      <- 入口：driver、三类共用的文件头、索引样式、dtx-style
│   ├── hithesis-book.dtx <- 毕业论文类 hithesisbook 与它的 cfg
│   ├── hithesis-art.dtx  <- 开题中期类 hithesisart、深圳博士中期类 hithesisartplus 与 cfg
│   ├── hithesis-bst.dtx  <- 参考文献样式 hithesis.bst / hitszthesis.bst
│   ├── hithesis-doc.dtx  <- 用户手册
│   └── hithesis-eps.dtx  <- EPS 图像数据（校徽、封面、示例插图）
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

构建产物（`*.cls`、`*.cfg`、`*.bst`、`*.ist`、`*.eps`、`*.pdf`）都由源文件生成，不进版本库。

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
make cls          # 生成 cls/cfg/bst/ist/eps，并分发到四个示例目录
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
| 毕业论文的任何行为 | `src/hithesis-book.dtx` |
| 开题、中期、深圳博士中期 | `src/hithesis-art.dtx` |
| 参考文献样式 | `src/hithesis-bst.dtx` |
| 用户手册文字 | `src/hithesis-doc.dtx` |
| 类的公共文件头、索引样式 | `src/hithesis.dtx` |

文件内用 `grep -n '%<\*book-' src/hithesis-book.dtx` 之类列出模块起点。模块用注释标出：

```
% ^^A ======================================================================
% ^^A Module book-footnote: 脚注样式与编号（book）
% ^^A ======================================================================
```

这些 `^^A` 行必须待在 macrocode 之外，否则会被当成代码原样印进手册。

同一个模块在 dtx 里可能被切成多段、与别的模块交替排布。例如 `art-deps` 有 9 段，因为
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

### 4.2 book / art / artplus 三类完全独立

三个 cls（毕业论文 / 开题中期 / 深圳博士中期）的代码物理隔离，由各自的 `book-*` / `art-*` / `artplus-*` 模块承载。内容相似也不跨类共享。

理由是三个类对应三套学校规范，各自演化。当下的碰巧相似会在规范独立变动时变成维护负担。

例外：`hithesis.bst`（或将废弃并切换到 biblatex-gb7714）和 `hithesis-eps.dtx` 跨类共享。

### 4.3 一个模块一个职责

模块名要能反映它唯一的职责：

- √ `chapter-book` 只管 book 类的章节标题格式
- √ `bib-book` 只管 book 类的参考文献加载与样式
- × `floats-book` 兼管列表、定理、段落、引用

加代码前先问这段代码语义上属于哪个模块，找到答案再写。找不到就考虑拆一个新的出来，见 §5。

### 4.4 模块内不写 `\ProvidesPackage`

v3.2a 起模块内容直接拼进 `.cls`，不再生成独立的 `.sty`。在类文件里写 `\ProvidesPackage` 会声明一个并不存在的宏包，日志里出现的身份信息也是假的。

模块开头只写注释标识：

```
% ^^A ======================================================================
% ^^A Module book-footnote: 脚注样式与编号（book）
% ^^A ======================================================================
%<*book-footnote>
...实际代码...
%</book-footnote>
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

**选项与标志位暂时不动。** 它们由 `kvoptions` 声明，属于用户接口，本轮不碰。
模块内部要读旧标志位，用 expl3 的桥接函数：

```latex
\legacy_if:nTF { hit@debug } { 真 } { 假 }
\bool_lazy_and:nnT { \legacy_if_p:n { hit@harbin } } { \legacy_if_p:n { hit@bachelor } } { ... }
```

**`\ExplSyntaxOn` 会改变空格与 `~` 的含义。** 三种情形都实测踩过：

- 字面文本里的空格被吞。`text={150true mm}` 直接照抄会变成 `150truemm`，要写 `~`。
- **`~` 在两种语法下含义不同。** LaTeX 里它是活动字符，表示不断行空格；expl3 里
  它是普通空格（catcode 10）。原有代码里的 `~` 照抄进 `\ExplSyntaxOn`，不断行空格
  就退化成了普通空格。`book-pagestyle` 的 `\fancyfoot[C]{\xiaowu-~\thepage~-}` 这样
  照抄之后，42 个变体里有 21 个的 PDF 变了。要保持原意就写 `\nobreakspace`。
- 控制空格 `\ ` 的记号化与平时不同。`art-chapter` 里 `aftername=\ifhit@opening {\ }`
  照抄进 expl3 之后，变体 32 的 PDF 就变了。

前两条方向相反，容易搞混：**要空格时写 `~`，而原文里已有的 `~` 要改写成
`\nobreakspace`。**

第二种情形没有简单的等价写法。可靠做法是把这类取值留在 expl3 之外定义成一个宏，
再由 expl3 的条件调用它，记号与改动前逐个相同：

```latex
\ExplSyntaxOff
\def\hit@art@shenzhenmaster@sectionset{\ctexset{ ...原样照抄... }}
\ExplSyntaxOn
\bool_lazy_and:nnT { ... } { ... } { \hit@art@shenzhenmaster@sectionset }
```

判断标准：模块里如果有大段字面排版内容（页眉文字、`\ctexset` 取值、控制空格），
就用这个办法把内容与控制流分开，别把内容裹进 `\ExplSyntaxOn`。

已迁移：`book-geometry`、`art-geometry`、`book-mainmatter`、`art-chapter`、
`art-pagestyle`、`art-toc`、`book-toc`、`book-pagestyle`、`art-floats`、`book-deps-c`、
`book-glossary`、`art-deps-a`、`book-deps-a`、`art-options` 与
`artplus-options`、`book-options`（均仅校验与后处理逻辑，选项声明仍归 kvoptions）。

评估后跳过：`art-hyperlink`（零条件）、`book-bib`（含 natbib 补丁需逐字保留）、
`book-appendix`（条件几乎全嵌在含字面空格的排版内容里，按本节规则该留在 expl3 之外，
而模块本身几乎全是这类内容）。

迁移一个模块的验收三步，缺一不可：

1. `make doc` 要过。手册会把 dtx 的注释排印出来，注释里写错宏名不会影响 `.cls`
   的生成，只在这一步暴露。已经踩过：`\opt{}` 本项目没有（应为 `\option{}`），
   `\cs{}` 的参数里 `_` 会被当成数学下标（要写 `\_`）。
2. `l3build check` 全过。
3. 与改动前的 PDF 逐字节比对。挑变体容易漏，`book-pagestyle` 那次 42 个里有 21 个
   变了，只挑几个未必抽中，所以跑全量。建参照树用
   `git worktree add --detach <目录> <上一个提交>`，比在原地 `git stash` 安全。

命名向 fduthesis 与 BIThesis 看齐：内部函数 `\__hit_模块_动作:参数签名`，变量
`\g__hit_描述_类型` / `\l__hit_描述_类型`。等有成规模的 expl3 代码之后再引入
`l3docstrip` 的 `%<@@=hit>` 前缀替换，那之前先写全名。

## 5. 新增模块的步骤

以给 `bookcls` 加 `book-footnote` 为例（这个模块已经存在，仅作示范）：

1. 在 dtx 里加守卫块。位置按现有 cls 的内部顺序选：

   ```
   % ^^A ======================================================================
   % ^^A Module book-footnote: 脚注样式与编号（book）
   % ^^A ======================================================================
   %<*book-footnote>
   ...实际代码...
   %</book-footnote>
   ```

2. 在 `hithesis.ins` 的对应 `\file{...book.cls}` 里插一条 `\from`：

   ```
   \from{\jobname.dtx}{book-footnote}
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

摘要用祈使句，不加句号，控制在 50 字以内。范围可省，也可以像 `fix(book,art):`
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
| `book` `art` `artplus` | 三个类家族，即 `src/hithesis-{book,art}.dtx` |
| `bst` `eps` | 参考文献样式、图像数据 |
| `manual` | 用户手册 `src/hithesis-doc.dtx` |
| `readme` `contributing` | 对应的 md 文件 |
| `tests` `scripts` | `tests/`、`testfiles/`、`tools/`、`scripts/` |
| `deps` | 依赖清单 `.github/tl_packages` |

手册的范围叫 `manual` 不叫 `doc`，是为了跟类型 `docs` 区分开。`docs(doc):`
这种写法只会让人猜半天。范围能省则省，但**同一类型能落在多处时就该写**：
`docs:` 看不出改的是手册还是 README，`docs(manual):` 一眼就知道。

```
feat(book): 增加深圳校区博士封面的联合导师字段
fix(art,artplus): 修正中期报告页眉在偶数页丢失
refactor(book): 把封面绘制从 bookcls 拆到 book-cover 模块
docs(manual): 补充 newgeometry 三个取值的版心差异
docs(contributing): 提交消息改用 Conventional Commits
test: 补充 art 与 artplus 的字段清单交叉验证
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

### 9.3 跨类改动

一个改动对 book/art/artplus 都适用时，三处必须同步。

## 10. 常见陷阱

| 陷阱 | 现象 | 处理 |
|---|---|---|
| hyperref 加载顺序 | 引用、书签锚点错乱 | hyperref 已在 `X-deps` 内部的精确位置加载，别在其他模块重新加载 |
| enumitem 覆盖 cft* 长度 | 目录间距异常 | `X-toc` 的 `\from` 要排在 `X-deps` 之后 |
| `\from` 顺序写错 | 宏未定义、样式失效 | docstrip 按 `\from` 顺序输出，不按守卫块在 dtx 里的位置 |
| 模块内残留 `\ProvidesPackage` | 日志里出现不存在的宏包 | 模块拼进 cls，不该有包身份声明 |
| 守卫缺失 | 代码漏进别的文件 | 每个 `%<*X>` 都要有配对的 `%</X>` |
| `\changes` 漏写 | 看不到历史脉络 | 迁移、重命名、删除都要写 |

## 11. 求助

- GitHub Issues：https://github.com/hithesis/hithesis/issues
- QQ 群：见 README.md

提问前先按上面的表找到对应文件，`grep` 一下看有没有类似实现。
