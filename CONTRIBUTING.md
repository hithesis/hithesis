# 贡献指南

本文写给要改代码的人：修 bug、加功能、调整文档结构。只是提 issue 或反馈样式问题的模板用户不必读。

---

## 1. 项目结构

```
hithesis/
├── hithesis.dtx          <- 主源文件：类文件实现、bst、ist
├── hithesis-doc.dtx      <- 用户手册
├── hithesis-eps.dtx      <- EPS 图像数据（校徽、封面、示例插图）
├── hithesis.ins          <- docstrip 驱动文件
├── Makefile              <- 构建入口
├── latexmkrc             <- latexmk 配置
├── dtx-toc.py            <- dtx 结构扫描工具
├── scripts/              <- 打包、依赖清单、回归测试、changes 提取
├── tools/                <- 排版测试脚本
├── tests/                <- 变体定义与测试说明
├── examples/
│   ├── hitbook/{chinese,english}/   <- 毕业论文示例
│   └── hitart/{reports,reportplus}/ <- 开题/中期/博士中期示例
└── .github/              <- Issue / PR 模板、CI 配置
```

构建产物（`*.cls`、`*.cfg`、`*.bst`、`*.ist`、`*.eps`、`*.pdf`）都由源文件生成，不进版本库。

## 2. 开发环境

| 工具 | 用途 | 必需性 |
|---|---|---|
| TeX Live ≥ 2021 | 编译模板与示例 | 必需 |
| Python 3.8+ | dtx-toc、changes 提取、回归测试、变体编译 | 必需 |
| Make | 走 Makefile | 推荐 |
| Ghostscript | 排版比对时把 PDF 渲染成 PNG | 跑测试才需要 |
| ImageMagick | 生成逐页差异图 | 可选 |

测试脚本用 bash 写，只保证在 Linux 和 macOS 下可执行。Windows 下走 WSL 或 Git Bash。

### 常用命令

```shell
make cls          # 从 dtx + ins 生成 cls/cfg/bst/ist/eps
make doc          # 编译用户手册 hithesis.pdf
make toc          # 打印 dtx 结构到 stdout
make toc-update   # 把结构写回 dtx 顶部的 TOC 块（幂等）
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

在示例目录里：

```shell
cd examples/hitbook/chinese && make thesis
cd examples/hitart/reports  && make report
```

## 3. dtx 导航

`hithesis.dtx` 按 docstrip 守卫块划分。动手前先跑 `make toc` 看全貌：

```
==== Major sections ====
  2245  artpluscls
  2879  artcls
  3900  bookcls

==== Modules (first .. last; block count) ====
  2253  artplus-options           2253-2395  (1 block)
  2396  artpluscls-load           2396-2405  (1 block)
  ...
```

行号会随改动漂移，改完记得 `make toc-update` 刷新。

`(N blocks)` 里 `N > 1` 表示这个区块在 dtx 里被切成 N 段、与别的区块交替排布。例如 `art-deps` 有 9 段，因为 `hyperlink` 和 `geometry` 要插在它中间才能保持原有的加载顺序。这是有意为之，不要合并整理。

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

三个 cls（毕业论文 / 开题中期 / 深圳博士中期）的代码物理隔离，由各自的 `book-*` / `art-*` / `artplus-*` 区块承载。内容相似也不跨类共享。

理由是三个类对应三套学校规范，各自演化。当下的碰巧相似会在规范独立变动时变成维护负担。

例外：`hithesis.bst`（或将废弃并切换到 biblatex-gb7714）和 `hithesis-eps.dtx` 跨类共享。

### 4.3 一个区块一个职责

区块名要能反映它唯一的职责：

- √ `chapter-book` 只管 book 类的章节标题格式
- √ `bib-book` 只管 book 类的参考文献加载与样式
- × `floats-book` 兼管列表、定理、段落、引用

加代码前先问这段代码语义上属于哪个区块，找到答案再写。找不到就考虑拆一个新的出来，见 §5。

### 4.4 区块内不写 `\ProvidesPackage`

v3.2a 起区块内容直接拼进 `.cls`，不再生成独立的 `.sty`。在类文件里写 `\ProvidesPackage` 会声明一个并不存在的宏包，日志里出现的身份信息也是假的。

区块开头只写注释标识：

```
% ^^A ======================================================================
% ^^A Module book-footnote: 脚注样式与编号（book）
% ^^A ======================================================================
%<*book-footnote>
...实际代码...
%</book-footnote>
```

### 4.5 `\changes` 历史条目

新增区块、迁移代码、语义有明显变化，都要写 `\changes`：

```latex
% \changes{v3.2a}{0000/00/00}{某段代码从某处迁到某处，理由}
```

- 版本号 `v3.2a` 是当前开发版，合入 master 后由维护者改成正式版本号
- 日期填占位符 `0000/00/00`，发版时由 `scripts/changes.py --stamp` 统一替换成发布日期
- 描述要写为什么这么做，不只写做了什么

CI 会校验这三条，不合规直接失败：开发版条目必须是 `0000/00/00`，已发布版本不得留占位符，
日期格式必须 `YYYY/MM/DD`。本地跑 `make changes-check` 看结果，`make changes-fix` 自动修
补零和写错的开发版日期。

## 5. 新增区块的步骤

以给 `bookcls` 加 `book-footnote` 为例（这个区块已经存在，仅作示范）：

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

   加载顺序敏感：如果新区块依赖 enumitem、hyperref 这些已在 `X-deps` 里加载的包，`\from` 要排在 `X-deps` 之后。

3. `make cls` 生成，`make toc-update` 刷新 TOC。

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
| TeX Live 矩阵 | 2021–2026 六个版本各编一遍文档与四个示例 |
| 跨平台 | macOS 与 Windows 上编译示例 |
| 变体矩阵 | 42 种 `\documentclass` 选项组合 |
| 排版回归 | 与参照版本逐页比对，差异出报告与截图 |

细节见 [tests/README.md](tests/README.md)。

## 7. 提交规范

### 7.1 commit 消息

```
<前缀>: <一句话摘要>

详细说明：改了什么、为什么、影响范围、验证结果。
```

前缀用区块名（`floats-book:`、`glossary-art:`）或类别（`docs:`、`build:`、`fix:`、`feat:`）。

### 7.2 不要提交

- 临时调试代码
- 未注明出处与许可的、从别的模板拷来的代码

### 7.3 commit 粒度

- 一个 commit 一件事，方便逐 commit 审
- 大重构按阶段分多个 commit
- 跨区块的批量改动可以放一个 commit，但要在消息里列出涉及范围

## 8. 分支与 PR

### 8.1 分支

- `master` 是稳定分支
- `dev` 是开发分支，维护者从这里合入新版本
- `modularity` 是重构分支，参照物是 `dev`，要求排版零差异
- 协作者从 `dev` 派生 `feature/<topic>`

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
| hyperref 加载顺序 | 引用、书签锚点错乱 | hyperref 已在 `X-deps` 内部的精确位置加载，别在其他区块重新加载 |
| enumitem 覆盖 cft* 长度 | 目录间距异常 | `X-toc` 的 `\from` 要排在 `X-deps` 之后 |
| `\from` 顺序写错 | 宏未定义、样式失效 | docstrip 按 `\from` 顺序输出，不按守卫块在 dtx 里的位置 |
| 区块内残留 `\ProvidesPackage` | 日志里出现不存在的宏包 | 区块拼进 cls，不该有包身份声明 |
| 守卫缺失 | 代码漏进别的文件 | 每个 `%<*X>` 都要有配对的 `%</X>` |
| `\changes` 漏写 | 看不到历史脉络 | 迁移、重命名、删除都要写 |

## 11. 求助

- GitHub Issues：https://github.com/hithesis/hithesis/issues
- QQ 群：见 README.md

提问前先 `make toc` 看结构，`grep` 一下 dtx 看有没有类似实现。
