# hithesis 排版测试

`tests/` 和 [`tools/`](../tools) 放排版测试用的东西，测两件事：42 种 `\documentclass`
选项组合（校区 × 学位 × 中英文 × book/art）还能不能编出 PDF，以及改完 `hithesis.dtx`
之后版面有没有跟着变。

## 目录结构

| 路径 | 是否入库 | 说明 |
| --- | --- | --- |
| `tests/variants/*.conf` | ✅ | 变体定义，测试矩阵按这个目录扫 |
| `tests/quick-set.txt` | ✅ | PR 上跑的代表性子集 |
| `tools/*.sh` | ✅ | 编译、比对、生成基线 |
| `tests/work/` | ❌ | 各变体的编译工作目录 |
| `tests/current/` | ❌ | 本次编译渲染出的 PNG |
| `tests/baseline/` | ❌ | 本地 PNG 基线，约 53 MB，太大不入库 |
| `tests/diff/` | ❌ | ImageMagick 生成的差异图 |
| `tests/doc-baseline/` | ❌ | 手册 PDF 的对照基线 |
| `tests/doc-current/` | ❌ | 本次编出的手册 PDF |
| `target/regression-cache/` | ❌ | 回归测试下载的参照版本源码 |

## 变体定义

每个 `.conf` 是一份 shell 变量文件：

```sh
BASE=examples/hitbook/chinese          # 取哪个 example 目录作模板
OPTIONS=fontset=fandol,type=bachelor,campus=harbin   # 替换进 \documentclass[...] 的选项
CLS=hit-thesis                         # 文档类名
ENTRY=thesis.tex                       # 主文件，默认 thesis.tex
BIBSTYLE=gbt7714-2025-numeric           # 可选，替换掉整棵树里的 \bibliographystyle
```

`tools/compile-variant.sh` 把 `BASE` 整个复制到 `tests/work/<变体名>/`，改写主文件第一行的
`\documentclass`，再用 `latexmk -xelatex` 编译。输出一律叫 `main.pdf`：文件名会进 PDF
（同内容的 `a.tex` 与 `b.tex` 编出来第 2261 字节起就不同），入口一改名逐字节比对
就全是假差异。

`BIBSTYLE` 改写两处：源码里的 `\bibliographystyle{}` 那一行，以及 `structure` 族的
`bib-style` 键。用 `\hitbackmatter` 排后置部分时前者由类生成，源码里根本没有。

变体 42 与 43 是同一份文档的两种写法：42 走 `hithesisartplus` 空壳，43 走
`hit-report` 加三个选项。深圳博士中期 v3.2a 从独立文档类并回报告类，
两者的 PDF 必须逐字节相同，空壳一断就会在这里露出来。空壳在 v4.1a 移除，
届时删掉 42。

变体 44 与 45 走 `fontset=mac`，其余全部钉死 `fontset=fandol`。行距与字体无关是
靠绝对值实现的：字号和行距都写成 bp，不用 `em` 也不用 `\linespread`。但每页第一行
走 `\topskip`（12pt），而 mac 仿宋的字面高是 10.13pt，余量只有 1.87pt——再高一点
每页第一行就会跟着字体往下掉。这两个变体钉的就是那点余量。

另外两个空壳 `hithesisbook` 与 `hithesisart` 走 `testfiles/23`、`testfiles/24`，
那边比变体便宜，只钉转发结果。

要加新组合，往 `tests/variants/` 里丢一个 `.conf` 就行，别处不用改。

## 用法

```sh
# 45 个变体全编一遍，渲染结果存为本地基线
make baseline            # 即 bash tools/make-baseline.sh

# 改完 dtx，重编并与本地基线逐页比对
make smoke               # 即 bash tools/smoke.sh

# 单编一个变体，排查用
bash tools/compile-variant.sh 07-master-harbin

# 与上一个正式 release 逐页比对，发版前跑，逐个人工确认
make regression-test
python3 scripts/regression_test.py --quick          # 只跑 tests/quick-set.txt 里的
python3 scripts/regression_test.py --against v3.1e  # 指定 tag
python3 scripts/regression_test.py --against dev    # 指定分支
```

手册（`hithesis.pdf`）不在上面这套里，它有单独一条：

```sh
make manual-baseline   # 动手改之前存一份
make manual-check      # 改完重编，与基线逐页比
```

参照的是改动前的自己，所以只能在本地跑，CI 取不到“改动前”的状态。要注意手册会把源码
连同行号一起排印，改代码必然让行号位移、索引重排，所以只有纯文档类改动才该期望零差异。

`NPROC` 控制并发，默认 8：

```sh
NPROC=4 make smoke
```

## 两种参照物

本地 PNG 基线（`make baseline` + `make smoke`）拿自己改动前的工作树作参照，改 dtx 时
自检用，跑得快。基线是本地生成的，换台机器得重做，也没法共享。

另一个版本（`scripts/regression_test.py`）拿别的 tag 或分支作参照。它下载那个 ref 的
源码存档，在里面跑一遍 `make cls` 生成那一版的 `.cls`，用同一套 TeX Live 环境重编，
再和当前工作树的输出逐页比。两侧环境相同，比出来的差异就只可能来自模板改动，TeX Live
自身升级造成的变化掺不进来。CI 用的是这一种。

参照物取源码存档而不是 release 挂的 zip 资产：资产是人手动传的，传错了工具照样一片绿。
zipball 由 GitHub 按 ref 生成，搞不错。

默认参照最近一个正式 release，看的是相对发布版改了什么。要跟别的 ref 比就用
`--against <ref>`，纯重构类的改动拿它对着基准分支比，正确结果是零差异。

## 日期得钉死

封面日期取的是 `\today`，不管的话每天编出来的 PDF 都不一样，比对没法看。回归测试统一设：

```sh
export SOURCE_DATE_EPOCH=1700000000
export FORCE_SOURCE_DATE=1   # 让 \today 也认 SOURCE_DATE_EPOCH，不只改 PDF 元数据
```

手工比对时照着设。
