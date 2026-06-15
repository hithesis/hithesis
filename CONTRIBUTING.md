# 贡献指南

感谢有意参与 HIThesis 的维护与改进。本文记录了贡献者在动手前需要了解的项目结构、开发约定与提交流程。文档面向 **代码贡献者**（修 bug、加功能、改文档结构）。仅作为模板用户提交 issue 或反馈样式问题不需要阅读本文。

---

## 1. 项目结构速览

```
hithesis/
├── hithesis.dtx          <- 主源文件（模块化代码、用户手册、bst/ist）
├── hithesis-eps.dtx      <- EPS 图像数据（校徽、封面、示例插图）
├── hithesis.ins          <- docstrip 驱动文件
├── Makefile              <- 构建入口
├── latexmkrc             <- latexmk 配置
├── dtx-toc.py            <- dtx 结构扫描工具
├── README.md
├── CONTRIBUTING.md       <- 本文
├── examples/
│   ├── hitbook/{chinese,english}/   <- 毕业论文示例
│   └── hitart/{reports,reportplus}/ <- 开题/中期/博士中期示例
└── .github/              <- Issue / PR 模板、CI 配置
```

构建产物（`*.cls`、`*.cfg`、`*.bst`、`*.ist`、`modules/*.sty`、`*.eps`、`*.pdf`）均由源文件生成，**禁止进版本库**。

## 2. 开发环境

| 工具 | 用途 | 必需性 |
|---|---|---|
| TeX Live ≥ 2024 | 编译模板与示例 | 必需 |
| Python 3.6+ | 跑 `dtx-toc.py` | 必需 |
| Make | 走 Makefile | 推荐 |

### 常用命令

```shell
make cls          # 从 dtx + ins 生成所有 cls/cfg/sty/bst/ist/eps
make doc          # 编译用户手册 hithesis.pdf
make toc          # 打印 dtx 模块结构到 stdout
make toc-update   # 把模块结构写回 dtx 顶部的 TOC 块（幂等）
make clean        # 清理所有生成产物
make distclean    # clean + 删发行 zip
```

在示例目录里：

```shell
cd examples/hitbook/chinese
make thesis       # 编译示例论文 thesis.pdf

cd examples/hitart/reports
make report       # 编译示例报告 report.pdf
```

## 3. dtx 与模块导航

主源 `hithesis.dtx` 按 docstrip 守卫块（Guard Block）划分。**先跑 `make toc` 看全貌**：

```shell
$ make toc
==== Major sections ====
  3196   artpluscls
  3843   artcls
  4886   bookcls
  9472   dtx-style

==== Modules (first .. last; block count) ====
   108   driver                   108-120 (1 block)
  3196   artpluscls               3196-3835 (3 blocks)
  3220   artplus-options          3220-3363 (1 block)
  3392   artplus-deps             3392-3767 (7 blocks)
  ...
```

输出每行的行号可直接跳转：编辑器里 `:数字` 即可。模块守卫块碎片化（如 art-deps 9 块）是模块化时为保持加载顺序的设计。

每个模块在 dtx 内部有 banner 注释：

```
% ^^A ======================================================================
% ^^A Module book-options: 文档类选项的声明与后处理（type/campus/fontset 等）（book）
% ^^A ======================================================================
%<*book-options>
```

dtx 顶部还有一段由 `make toc-update` 自动维护的静态 TOC，用 `% ^^A` 包裹，对 LaTeX 与 docstrip 均不可见。

### 3.1 命名约定

各处统一为 **cls 在前、职责在后**：

| 类型 | 例子 | 模式 |
|---|---|---|
| 模块 docstrip 守卫 | `%<*book-options>` | `<cls>-<职责>` |
| 模块文件名 | `hithesisbook-options.sty` | `hithesis<cls>-<职责>` |
| `\ProvidesPackage` 标识 | `hithesisbook-options` | 同文件名 |
| cls 守卫 | `%<*bookcls>` | `<cls>cls` |
| cfg 守卫 | `%<*bookcfg>` | `<cls>cfg` |

模块文件名前缀 `hithesis` 是 LaTeX 包惯例；其余字段顺序一律 cls 优先。共享资源（bst、ist、dtx-style 等）无 cls 后缀。

## 4. 模块化的硬性约定

下列原则贯穿整个 v3.2Z 架构。**不遵守的 PR 不会被合并。**

### 4.1 用户接口绝对不得改变

模板已有数千篇论文在用，任何 PR 不得改变：

- `\documentclass` 接受的选项名与默认值
- `\hitsetup{}` 接受的 key 名
- 已对外暴露的命令名（`\inlinecite`、`\bicaption`、`\rcell` 等）
- 已对外暴露的环境名（`cabstract`、`publist`、`appendix` 等）

新增是允许的，**重命名/删除/默认值改动是禁止的**，除非走完废弃期（见 §9）。

### 4.2 book / art / artplus 三模板类完全独立

三个 cls（毕业论文 / 开题中期 / 深圳博士中期）的代码物理隔离，由独立的 `*-book` / `*-art` / `*-artplus` 模块承载。即使内容相似也不跨 cls 共享。

理由：三模板类理应对应三套学校规范，规范常各自演化，强行耦合会让某时期的碰巧相似在规范独立改变时维护难度增大。

例外：`hithesis.bst`（或将废弃并切换到 biblatex-gb7714）、`hithesis-eps.dtx` 是跨类共享的。

### 4.3 一个模块一个职责

模块名应反映其唯一职责：

- ✅ `chapter-book` 只管 book 类的章节标题格式
- ✅ `bib-book` 只管 book 类的参考文献加载与样式
- ❌ `floats-book` 兼管列表+定理+段落+引用

新加代码前问：**这段代码语义上属于哪个模块？**找到答案再写。若找不到，先考虑拆出新模块（参考 §5）。

### 4.4 `\ProvidesPackage` 必须是模块第一条非注释语句

每个 `%<*modname>` 块开头：

```
%<*modname>
\ProvidesPackage{hithesisX-modname}[0000/00/00 v3.2a hithesis-X modname]
... 实际代码 ...
%</modname>
```

错位会让 `.log` 横幅 "先做事后报名"，且影响错误归属。

### 4.5 `\changes` 历史条目

新增任何模块、迁移、显著语义变化，都要写 `\changes` 条目：

```latex
% \changes{v3.2a}{0000/00/00}{某模块从某处拆出至某处，理由}
```

- 版本号 `v3.2a` 是当前开发版（合入 master 后由维护者改为正式版本）
- 日期 `0000/00/00` 是占位符，正式发版时统一替换
- 描述要写**为什么**做这件事，不只是写做了什么

## 5. 新增模块的标准步骤

假设要新增 `bookcls` 的 `book-footnote` 模块（已存在，仅作示范）：

1. **在 dtx 中加守卫块** —— 选合适位置（按现有 cls 内部顺序），加：

   ```
   % ^^A ======================================================================
   % ^^A Module book-footnote: 脚注样式与编号（book）
   % ^^A ======================================================================
   %<*book-footnote>
   \ProvidesPackage{hithesisbook-footnote}[0000/00/00 v3.2a hithesis-book footnote]
   ...实际代码...
   %</book-footnote>
   ```

2. **在 cls 加载点插入 `\RequirePackage{...}`** —— 在 dtx 对应 cls 块里（找到 `%<*bookcls>` 区域）：

   ```latex
   \RequirePackage{hithesisbook-footnote}
   ```

   **加载顺序敏感**：如果新模块依赖 enumitem/hyperref 等已在 `X-deps` 加载的包，要放在 X-deps **之后**。

3. **在 `hithesis.ins` 加生成项**：

   ```
   \hitbookmod{footnote}     % 或 \hitartmod{} / \hitartplusmod{}
   ```

4. **跑 `make cls` + `make toc-update`** —— 验证生成正常，自动刷新 dtx 顶部 TOC。

5. **本地编译验证** —— 至少跑过受影响 cls 的示例（`make thesis` / `make report`），确认无 LaTeX 报错、PDF 渲染正常。

6. **如果是用户可见的功能改动**，更新手册 `\subsection{模块说明}` 表格（dtx 内）。

## 6. 修改现有模块

不涉及新模块的改动（修 bug、调样式、迁移代码）：

1. 用 `make toc` 定位目标模块
2. 改代码，加 `\changes{v3.2a}{0000/00/00}{...}` 条目
3. 跑 `make cls` 重新生成
4. 编译受影响 cls 的示例验证
5. `make toc-update`（如果改动影响行号，自动刷新静态 TOC）

## 7. 提交规范

### 7.1 commit 消息

格式：

```
<前缀>: <一句话摘要>

详细说明：改了什么、为什么、影响范围、verification 结果。
```

前缀建议：

- 模块名前缀：`floats-book:` / `glossary-art:`
- 类别前缀：`docs:` / `build:` / `fix:` / `feat:`

### 7.2 严禁出现的内容

- **`Co-Authored-By: Claude ...` 一类 AI 工具署名** —— 项目偏好显式人类作者，AI 辅助不写进 trailer
- 包含临时调试代码（被注释的 `\typeout{...}` 等）
- 直接拷贝其他模板代码而未注明出处与许可

### 7.3 commit 粒度

- 一个 commit 一件事，方便 reviewer 逐 commit 审
- 大重构按阶段分多个 commit
- 跨模块 / 跨 cls 的批量改动允许放在一个 commit，但要在 commit 消息中明确列出涉及的模块

## 8. 分支与 PR 流程

### 8.1 分支

- 维护者主仓库（upstream/hithesis/hithesis）的 `master` 是稳定分支
- `dev` 是开发分支，维护者从此处合入新版本
- 协作者从 `dev` 派生 feature 分支：`feature/<topic>` 或简短描述

### 8.2 PR 流程（fork 工作流）

```shell
# 1. fork 后克隆你的 fork
git clone https://github.com/<you>/hithesis.git
cd hithesis
git remote add upstream https://github.com/hithesis/hithesis.git

# 2. 从最新 dev 派生分支
git fetch upstream
git checkout -b feature/my-topic upstream/dev

# 3. 改 → commit → push 到自己 fork
git push -u origin feature/my-topic

# 4. 在 GitHub 上开 PR，base=upstream/dev，head=origin/feature/my-topic
```

**禁止**：

- 直推 `upstream/master`
- `git push --force` 到 `upstream` 任意分支
- 把 `feature/X` 推成 `master`

如果有 write 权限，也走 PR 流程，不要绕过 review。

### 8.3 PR 需要包含

- 一句话说明：解决了什么问题
- 关键改动列表（按模块或 commit）
- 用户接口影响声明：是 zero-impact 还是有 user-visible 变化
- 本地验证结果：跑过哪些示例、是否 PDF 渲染正常
- 截图或 PDF 链接（如果改动影响渲染）

## 9. 演进策略

### 9.1 加新选项 / 命令

允许，但要符合：

- 默认值保持旧行为
- 文档（手册或 thesis.tex 注释）说明用途
- 加 `\changes` 条目

### 9.2 移除老接口

需要走废弃期：

1. **opt-in 期**（≥ 6 个月）—— 新接口可用，旧接口保留，文档提示推荐新接口
2. **默认切换**（v4.0 这类大版本）—— 默认改为新接口，旧接口保留为兼容选项
3. **观察期**（≥ 24 个月）—— 等用户论文完成完整培养周期
4. **彻底移除**（v5.0 大版本）—— 删旧代码

参考：本仓库 issue 区"subfigure → subcaption 迁移计划"。

### 9.3 跨 cls 改动

如果一个改动对 book/art/artplus 都适用，**必须三处同步**。否则会让模块矩阵不对称。例外：仅一个 cls 适用的规范变化。

## 10. 常见陷阱

| 陷阱 | 现象 | 解决 |
|---|---|---|
| hyperref 加载顺序 | 引用/书签锚点错乱 | `hyperref` 已在 `X-deps` 内部精确位置加载，不要在其他模块重新加载 |
| enumitem 覆盖 cft* 长度 | 目录间距异常 | X-toc 模块必须在 X-deps 之后加载（深圳硕士目录的历史教训） |
| subfigure 不可改 | 用户论文用 `\subfigure[]{}` 语法 | 不要切换到 subcaption，会破坏所有现存论文 |
| `\ProvidesPackage` 错位 | 模块 .log 输出乱 | 必须放在 `%<*modname>` 紧后第一行非注释语句 |
| docstrip 守卫缺失 | 模块代码漏进其他文件 | 每个 `%<*X>` 必须有匹配的 `%</X>` |
| `\changes` 漏写 | 看不到历史脉络 | 任何语义变化都加，包括迁移、重命名、删除 |

## 11. 找谁帮助

- **GitHub Issues** —— https://github.com/hithesis/hithesis/issues
- **QQ 群** —— 见 README.md
- **维护者邮件** —— 见 dtx 顶部许可声明

提问前请先 `make toc` 看模块结构、`grep` 一下 dtx 看是否已有类似实现。

---

**最后一句话**：HIThesis 已经被千余学生用着，每一次 PR 都可能影响他们的论文。**保守、可回滚、可验证** 是这个项目的核心原则。
