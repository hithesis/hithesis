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
ENTRY=final.tex                       # 主文件，默认 final.tex
BIBSTYLE=gbt7714-2025-numeric           # 可选，替换掉整棵树里的 \bibliographystyle
```

`tools/compile-variant.sh` 把 `BASE` 整个复制到 `tests/work/<变体名>/`，改写主文件第一行的
`\documentclass`，再用 `latexmk -xelatex` 编译（变体矩阵与逐字节基线仍按 xelatex 跑，lualatex 另有冒烟）。输出一律叫 `main.pdf`：文件名会进 PDF
（同内容的 `a.tex` 与 `b.tex` 编出来第 2261 字节起就不同），入口一改名逐字节比对
就全是假差异。

`BIBSTYLE` 改写两处：源码里的 `\bibliographystyle{}` 那一行，以及 `gb7714` 族 `bibtex` 子组的
`style` 键。源码里没写前者时，`\bibliography` 那一刻由类按后者补一句。

变体 43 是深圳博士中期，由 `stage=interim,degree-level=doctor,campus=shenzhen`
三个选项选中。这一档 v3.2a 从独立文档类（`hithesisartplus`）并回报告类，当时
留了个转发空壳，42 号变体比的就是“空壳与三个选项输出逐字节相同”；空壳在
v3.2a 移除之后那一格没了意义，已删。

深圳研究生中英文报告现统一使用自有排版层，博士暂沿用硕士版式。
八组排版小样与 Word 坐标检查见 [`output/shenzhen/README.md`](output/shenzhen/README.md)。
分节命令和标题分页的跨引擎检查见 [`sectionbreak.md`](sectionbreak.md)。
独立引用包 wiseref 的标准文档测试与待实现接口的验收用例见
[`wiseref/README.md`](wiseref/README.md)。这些测试不加载 hithesis 或 docxlike。

变体 44 与 45 走 `fontset=mac`，其余全部钉死 `fontset=fandol`。行距与字体无关是
靠绝对值实现的：字号和行距都写成 bp，不用 `em` 也不用 `\linespread`。但每页第一行
走 `\topskip`（12pt），而 mac 仿宋的字面高是 10.13pt，余量只有 1.87pt——再高一点
每页第一行就会跟着字体往下掉。这两个变体钉的就是那点余量。

三个旧类名（`hithesisbook`、`hithesisart`、`hithesisartplus`）计划在 v4 移除，预计约 2027 年初。
稳定版 v3.2a 保留原有类名；以下行为属于当前 v4 开发版。
它们各留一份只报错的类文件，写了旧名会得到一条说清改法的错误，而不是 LaTeX
自己那句看不出该改成什么的“File not found”。`testfiles/23`、`24`、`72` 各钉
一个名字，钉的是“报了错”，不钉文案。

要加新组合，往 `tests/variants/` 里丢一个 `.conf` 就行，别处不用改。

## 用法

```sh
# 48 个变体全编一遍，渲染结果存为本地基线
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

## Lua 宏专项回归

```sh
make check-lua
# 不使用 make 的平台也可直接运行
python3 scripts/check-lua.py
# 运行入口的错误路径检查，不需要 TeX
python3 tests/lua-check.py
```

该入口用 `config-lua.lua` 实际运行 [`lua-cases.txt`](lua-cases.txt) 中的 118–126 九项测试，
覆盖封面候选测量、英文内封题目/字段/让步、有界量宽、决议分盒和名单测量；
118 同时核对公开正文安装后的几何缓存与页首状态。
`l3build` 自行从当前源码解包，不使用之前留下的类文件。
Lua 专用基线为 `testfiles/*.luatex.tlg`，本轮按 TeX Live 2026 核验；保留 LuaTeX-ja 的
JT3/JY3 字体信息及所有原断言，逐行比较完整日志，不过滤 Font Info 或警告。
默认 `l3build check` 继续运行现有 Xe 回归。

**不能用 `l3build check -e luatex` 的退出码代替 Lua 验证。** 默认配置只登记 Xe，
这个写法可能打印 `Skipping unknown engine luatex` 后返回 0。
正式入口固定使用 `l3build check -c config-lua -e luatex`，并额外检查九项实际执行记录、
原始日志的 LuaTeX/LuaHBTeX 引擎标识及每份完整标准化日志与专用基线是否一致。
先清理这九项已有的生成日志，防止本次跳过时借用旧结果；缺项、错误引擎、基线差异或跳过均失败。

当前运行记录在 `build/lua-check.log`、`build/lua-checks.json`，单项日志和差异在
`build/test-config-lua/`。这些是本轮可重建产物，排查前可另存；CI 在失败时上传它们。
最新 TeX Live 的 Lua 任务和开发分支任务均执行该入口，旧版本矩阵仍按原配置运行。

确需更新某项 Lua 基线时，先核对原 `.tlg` 中的断言及真实引擎差异，再单独保存：

```sh
l3build save -c config-lua -e luatex 118-special-page-measurement
make check-lua
```

## Word 逐页差异诊断

`scripts/check-pages.py` 是现有棘轮。另用 `scripts/diagnose-pages.py` 排查重复表头、续表和
正文换页：按全文顺序一对一配行，不按“哪个坐标最近”选重复行；重复文字仍标为歧义，
只配上行首的标为 `prefix-only`。一张参考页可以对应多张实际页。

```sh
python3 scripts/diagnose-pages.py --fixture tests/pages-bachelor.tsv \
  --pdf tests/sample/bachelor/main.pdf --json build/bachelor-page-diagnostic.json
python3 scripts/diagnose-pages.py --reference-pdf /path/to/word.pdf \
  --pdf /path/to/tex.pdf --json build/controlled-page-diagnostic.json --header-y 0
python3 tests/page-diagnostics.py
```

输出包含页对应关系、逐行 `dy`/`dx`、未匹配内容及唯一完整行的统计。它用于诊断，
不替换正式棘轮，也不把重复行的顺序候选算成已确认的几何匹配。`--header-y` 控制
第一页以外的页眉排除边界；无页眉受控稿可用 0。参考稿须与 TeX 内容一致，
否则 `prefix-only` 或未匹配可能来自输入不同，而非排版错误。

数学与正文的衔接标准见 [`reference/math-backend-contract.md`](reference/math-backend-contract.md)：
小公式装得进正常行盒时不异常撑行，大公式按实际 LaTeX 盒高深占位。对应功能回归为
`inline-math-linebox` 和 `inline-math-size`，不以 Word 数学内部坐标为基准。
整本 4.4 节前的 Word/LaTeX 累计差已另做公式、符号对象及字体角色控制，见
`build/reports/school-equation-spacing-feedback.md`；标题前距本身不是该累计差的来源。
普通正文直接接说明表的 Lua 首行重复补胶已修复，原复现另存于
[`sample/eqdenote-paragraph-boundary/`](sample/eqdenote-paragraph-boundary/)。
`eqdenote-boundary` 对比正文、大小公式、标题、页首和连续说明表的相对位置，
`eqdenote-pagination` 检查跨页首行、折行说明、嵌套试排及脚注执行次数。
修复与回归证据见 `build/reports/eqdenote-entry-fix-feedback.md`。

### 新同文 Word 参考

[`reference/word-content/`](reference/word-content/) 保存真实 Windows Word 导出的文字/基线，
`manifest.json` 记录 DOCX/PDF、字体、生成脚本和样稿来源摘要。它与旧
`tests/pages-{doctor,bachelor}.tsv` 并行；旧下限 234/153 不变。

```sh
# 同时重编样稿，检查旧棘轮和新的顺序一对一棘轮
make pages-word-content
# 已有新鲜 PDF 时只检查新参考
python3 scripts/check-word-reference.py check --degree doctor \
  --pdf tests/sample/doctor/main.pdf --min-ok 185 --json build/doctor-word-sequence.json
python3 scripts/check-word-reference.py check --degree bachelor \
  --pdf tests/sample/bachelor/main.pdf --min-ok 133 --json build/bachelor-word-sequence.json
python3 tests/word-reference.py
```

新下限博士 185、本科 133，只计不歧义且文字完整相同、`|Δy|≤0.5bp` 的行。
重复表头按全书顺序一对一给候选，不再复用首表行，也不计入已确认数；行首相同但断行不同
的 `prefix-only`、短数学片段同样不计。这个计数与旧棘轮口径不同，不表示全书已一致。

重新生成参考须有 [`reference/word-reference-sources.json`](reference/word-reference-sources.json)
列出的两份 `-LaTeX对齐.docx`，以及 Parallels 的 `Windows` VM/真实 Word。源 DOCX 校验 SHA256，
当前支持固定样稿中的纯文本角色，遇到不支持的 TeX 命令会停止。每次使用全新的输出目录：

```sh
make word-reference-prepare WORD_REFERENCE_INPUTS="/path/to/修正版docx" \
  WORD_REFERENCE_RUN=build/word-reference/new-run
make word-reference-export WORD_REFERENCE_RUN=build/word-reference/new-run
# 先检查导出的 DOCX/PDF，再冻结到新的候选目录；不要覆盖已接受的基准
make word-reference-freeze WORD_REFERENCE_RUN=build/word-reference/new-run \
  WORD_REFERENCE_FIXTURE=build/word-reference/new-fixture
```

导出采用独立 Word COM 实例、只读打开、临时目录和本机 host-only 接口，核对
`word-fonts.json` 的字体文件 SHA256；保存 Word/Windows 版本及导出字节摘要。
不更新目录域（`fields_updated=false`）。源稿、旧中间稿和既有 fixture 均保留。
相同输入生成的 DOCX 字节可重复；Word PDF 的时间等元数据可能随导出变化。

本次同文范围是中英摘要（含末尾省略号、关键词前空段）、结论、当前声明/授权正文。
同时修正这些节的字符网格、字体提示及本科结论链接。封面教学批注、文献/成果条目文字、
静态目录页码和 LaTeX 数学内部仍有不同；图页沿用按 LaTeX 布局修订的 Word 输入，
不能作为独立通用排版算法的证明。详细结果见 `build/reports/word-content-reference-feedback.md`。

当前两端的 Times New Roman、SimSun、SimHei 同名但文件 SHA256 不同，两端实际摘要另存
`build/reports/word-content-latex-fonts.json`。新基准用于稳定重放当前参考；剩余字距/断行差
不能在未控制字体版本时直接判为引擎错误。

#### 隔离的同字体整本控制

`scripts/compare-word-fonts.py` 将固定的样稿和当前运行时复制到独立目录，分别构建本机字体、
仅替换 Times、仅替换中易字体、两者都替换四组。用真实出页字形记录字体路径及 SHA256，
不会仅因声明了字体就认定实际使用成功。LuaTeX-ja 的命名字体默认特性需要与 fontspec 分别设置。

```sh
# 从实际 VM 复制八份字体到新的私用目录；先核对与已接受 Word 参考的字体摘要
python3 scripts/export-word-fonts.py --output build/private-word-fonts
python3 scripts/compare-word-fonts.py prepare --fonts build/private-word-fonts \
  --output build/font-controls/new-run
python3 scripts/compare-word-fonts.py build --output build/font-controls/new-run --jobs 2
python3 scripts/compare-word-fonts.py report --output build/font-controls/new-run
python3 tests/font-controls.py
```

字体不安装到系统、不放进源码或证据包。数学字体和后端仍按 LaTeX，Word 教学批注等内容差异
也未消除；“对应家族同文件”不表示整本完全一致。本轮控制及参照结构核查见
`build/reports/font-matched-whole-feedback.md`，原 gate 和 fixture 保持。

#### Word 自动跨页表与续表题实测

`scripts/word-auto-table.py` 从已核验的 content-v6 副本生成一张真实数据行表格，删除手工拆片间
的空段；第一行表题与第二行列标题都设为重复标题行。23 行原数据保留，另生成 69 行的明确标注
加长测试副本，验证自然跨页。数学表头/数据 run 和全部书签保留，输出另存：

```sh
python3 scripts/word-auto-table.py --output build/word-reference/auto-table-new
python3 scripts/export-word-reference.py --input build/word-reference/auto-table-new \
  --output build/word-reference/auto-table-new-export
python3 tests/word-auto-table.py
```

**重复原表题不等于自动加“（续表）”。** 实际 Word 16.0.20430.20182 的模式 11/15 中，
重复表行里的 `PAGE` 保持首页值，`IF PAGE = PAGEREF` 不能逐页切换题名；三轮字段更新/重新分页
后仍如此。实测文档及边界见 `build/reports/word-auto-table-feedback.md`，不将其冒充自动续表题已实现。

#### 分页后自动生成“（续表）”与“（续图）”

`scripts/word-continuations.py` 使用实际 Word 的数据行/图块页归属生成续题，不依赖重复行中的
`PAGE` 域。流程是**编辑源稿 → 保存 → 运行更新命令 → 得到生成稿/PDF**，不是 Word 键入时的
实时功能。源稿保留单张真实行表和带开始/结束标记的分块图组；生成稿按页生成表片和图题。

```sh
python3 scripts/word-continuations.py prepare \
  --input build/word-reference/auto-table-v1/doctor-auto-table-long.docx \
  --output build/word-continuations/doctor-source.docx
python3 scripts/word-continuations.py update \
  --input build/word-continuations/doctor-source.docx \
  --output build/word-continuations/doctor-run
python3 tests/word-continuations.py
```

图组内已有图片分块与子图说明，同页只放一次正常图题，跨页后生成“图…（续图）”；不会把
一张位图自动裁成多块。表号/图号沿用源稿文字，不代替全文自动编号。生成稿是派生输出，
继续修改应改 `*-源稿.docx` 并生成新目录；直接把生成稿作输入会被拒绝。
实际 Word 增删、改页、重复更新及保存往返结果见 `build/reports/word-continuations-feedback.md`。

Windows Word 单文件入口已另制为 `HIT论文工具.dotm`，内嵌博士/本科/演示源稿和纯 VBA 更新程序，
使用者不需要外部 Python。源码及说明见 [`tools/word/`](../tools/word/使用说明.md)；功能区和
“加载项”按钮共用更新逻辑。11 个生成用例和错误恢复的真实 Word 验收见
`build/reports/word-click-update-feedback.md`。首次运行仍遵循本机宏策略，运行时不需要 VBA 工程访问权限。

封面连排测量用 `126-cover-continuation-measurement` 核对六档让步下的零空行、默认
`2/2/6` 和最大空行组合：缓存预测须与完整候选的校名基线、总自然高相符。
`longtblr-firstline` 检查题注实际折行后，首行相对表前正文的位置不随题注盒总高改变；
同时保留硕士/博士的单语与双语题注分支。

`title-subtitle-case` 检查外封和英文内封：空英文副题、仅中文副题、有英文副题、隐藏副题，
均须在全部大写处理后保留正确的文字和分隔符。副题显示条件应先于大小写转换求值，
避免内部语言标识 `en` 被转成 `EN` 后误判空副题。
有界题目回归同时检查接近限宽但仍能放下的格式化题目，以及明确超出限宽的题目。

`defense-unframed` / `defense-unframed-long` 覆盖可选的 `\defense[unframed]`：
长单位折行、匿名评阅省略、六十名委员跨页并重复表头、名单后普通决议接排、正文只执行一次及表号保持。
`127-defense-unframed` 核对 `true`/裸键、`false`、`auto` 及下一次默认调用的切换。
`auto` 和默认调用目前保留有框版；原 `resolution-layout`、`resolution-roster` 继续检查有框兼容行为。
依据和最小例子见 [`sample/defense-unframed/`](sample/defense-unframed/)；
学校指南给出无框要求但没有对应样表，列宽与分页属于模板实现选择。

`declarations-after-index` 检查索引后声明页的导师签名与声明标题同页。
声明页的独立试排盒不会继承外层物理行，容量判定须计入公开边界查询返回的待接排余量；
只比较盒子自然高会在 Lua 下少让掉一个空段，导致导师签名独占下一页。

学校的英文题目量宽和决议拆盒直接使用公开编程入口
`docxlike_format_measure_width:nnNN`、`docxlike_textbox_split:NnNNN`；输出寄存器按 `N` 参数传递。
两者在先前 mixed-note 冻结中已有。当前已导入 `author-api-9561e82bd7d3-5b3501b2`，
标题段距、`eqdenote` 物理盒状态、正文安装和结构化 TOC 也已改用公开入口。
`128-author-body-boundary` 检查安装后的几何缓存与幂等请求，
`129-author-style-operations` 检查类扩展属性的完整 reset/inherit；默认 Xe 宏回归现有 127 项。
双层入口、配置语义及历史内部依赖的迁移记录见
[`reference/docxlike-author-api-audit.md`](reference/docxlike-author-api-audit.md)。

`footnote-keep` 实际加载终稿、开题、中期的类文件，在页底检查单段多行脚注与引用一起移页，
并检查脚注文字只执行一次。该用例使用单段内的 `\break`；左对齐排版中的 `\\` 可能结束
段落，不能用多段脚注代替“段中不分页”的测试。库默认允许续注与学校显式段中不分页分别验收。
`footnote-two` 进一步检查两条独立脚注可随各自引用分别换页：同条注的两行不拆，第一条能放下时
保留当前页，两条注的顺序与执行次数均保持。

`footnote-long` 检查学校终稿的**显式 `\docxpar` 路径**：10 行注保持整段，80 行单段注在文末
完成续排、文字不重复执行、待放队列和注区上限恢复。该新用例仅验收 LuaLaTeX / Word2013 模式；
四种兼容模式的同源控制和完整 Word 重放见 `build/reports/long-note-consumer-feedback.md`。
`footnote-long-plain` 覆盖普通正文入口；`sample/footnote-long-implicit/main.tex` 保留原反例内容，
在 compatibility 冻结的四模式旧新控制中，纸面外字形从各 158 个降为 0，全部 80 个标记完整。
验收检查实际文字和纸面边界，不仅检查引擎退出码。
开题/中期的原生脚注路径继续由短注/双注回归覆盖，不计入新超页回退认证。

`footnote-paragraphs` 检查显式 `\docxpar` 引用中的三个普通注段：首末短段完整，中间连续文字
自动折行，超页时仅中间段续排，首段不随整条注延期。当前限定学校终稿 / Lua / Word2013；
消费方还核对了这份样稿的完整 7283 个非空白注字符及实际纸面边界。完整四模式自动折行
Word 重放的历史结果见 `build/reports/paragraph-note-consumer-feedback.md`。
`footnote-paragraphs-plain` 进一步覆盖普通正文中的多段注。普通入口修复的验收见
`build/reports/compatibility-consumer-feedback.md`。当前接受冻结为
`mixed-note-a76d465467ca-b5d3909d`；48 项普通/显式入口状态控制、学校 38 份功能 PDF、
已有脚注和原生数学/盒子合同及整本新旧棘轮均通过，见
`build/reports/mixed-note-consumer-feedback.md`。本轮消费方完整重跑了 20 组兼容矩阵的 914 次重放，
支持范围内的 Word 几何为 886/886；4 项整盒差异和 24 项无设置的独立分隔线字号诊断不计为匹配。

`footnote-mixed` 和 `footnote-mixed-reverse` 检查学校终稿同段不同引用行的短长/长短双注：
前面的短注能与其引用同页，后来的短注不能越过延期长注；长注可续页，注文字只执行一次。
四模式、普通/docxpar 两入口的学校控制 16/16 通过，旧 compatibility 在现代长短两入口下失败。
独立 Word 正常分辨率组 256/256、9984 条注行完整匹配，新状态检查 64/64；原 1×1 PNG 组仍为
240/256，裸 graphicx 可复现的图片量纲临界差异保留，没有扩页面、放宽门槛或加固定补偿。
该冻结的完整认证限于两条注、单段长注加两行短注及相同字号/引用行距预留。
新增混排 Word/状态与学校功能使用 Lua，不据此扩为 Xe 联合 Word 几何认证。

后续 `footnote-multipar-mixed` / `footnote-multipar-mixed-reverse` 覆盖短注与“短段—超页段—短段”长注：
学校四模式、两入口、两策略、live/trial 的 64 项通过，32 对试排与正式分页一致。
新 64 份实际 Word DOCX 的 256 重放中，注文字和顺序均完整，但只有模式 15 的 64 项逐行匹配；
模式 11/12/14 各 64 项存在后续注段的中文混排断行差异。模式 11 删除另一条短注仍失败，
改回单段则通过；原输入、DIFF 和 8 份独立 Word 控制保留，不据学校功能通过扩大 Word 几何认证。
复现入口见 [`sample/footnote-multipar-mixed/`](sample/footnote-multipar-mixed/)，详细证据见
`build/reports/multipar-mixed-note-feedback.md`。三注以上和不同预留量仍待验证。

后续 page-settings 冻结的隔离集成中，上述四模式 Word 矩阵已全部 256/256，另 32 个边界控制通过；
学校 64 项状态、126 份功能 PDF、72 个数学上下文及整本新旧门槛也通过。
但仍位于中间页面范围时，修改上边距会使已恢复的学校扩展设置回退为外层值，
纯库反例在 Lua/Xe 同样复现，因此尚未导入，默认基线仍为 mixed-note。
输入见 [`sample/page-settings-owner-state/`](sample/page-settings-owner-state/)，
本轮结果见 `build/reports/page-settings-consumer-feedback.md`。

随后 `header-variants-9aa1869a9e1f-d44b89ec` 的页眉公开 variant 修复已独立复验：
原 6 失败、8 控制、新 32 组合全部通过，坐标零差；页面 owner 状态反例仍失败，故未更新 vendor。
详见 `build/reports/header-variants-consumer-feedback.md`。

## 按功能的回归（`tests/feature`）

上面几条都是整本比：示例一改基线就全换，单个功能在冷门分支上坏了，要靠示例恰好碰到
才发现（例如 pdfLaTeX 下成果页没有年份的条目让 natbib 连报三条错、
XeLaTeX 下报告里的西文字母叠成一团）。这一条照 iota-hit 的 `tests/` 拆开：一个功能
一份小文档，跑遍各分支（阶段 × 学位 × 校区 × 语种）与三个引擎，逐份查。平时不跑，改了哪个
功能、或者发版前跑一次。

```sh
make feature                                   # 全部用例
make feature CASES='algorithm-caption'         # 只跑这几个
make feature ENGINES=lualatex BRANCHES='stage=final,campus=harbin'
texlua tests/feature/run.lua --list            # 列出用例
texlua tests/feature/run.lua --keep 用例        # 过了的工作目录也留着
```

一个用例是 `tests/feature/cases/` 下同名的两个文件：

- `<名>.tex`：文档本身，`\documentclass` 由 `run.lua` 按分支补在最前面，接着读
  `tests/feature/feature-prelude.tex`（关掉文末自动补排的前置、正文、后置，用例要哪段自己写）。
  文件头的 `%!` 行是指令：`branches`（条件，写法与 `\hitsetup[…]` 相同，另认 `engine` 与
  分支名 `id`）、`engines`、`options`（给 `\documentclass` 多加的选项）、`files`（一起拷进工作
  目录的文件）、`allow`（容许的告警，Lua 模式，可写多行）。
- `<名>.lua`：检查，返回一个函数，拿到的对象有 `branch`、`engine`、`log`，查 PDF 用
  `has`/`hasnt`/`count`（找一段字，空白不算、不跨行）、`bold`（每个字粗或细）、`font`、`pos`、
  `page_of`、`lines`（逐行的字，每个字带页、坐标、字体、字号、粗细），类按分支定的开关用
  `fact`（`chapter`、`en`、`shenzhen`、`bilingual-caption`，由 prelude 写进日志），
  不对就 `fail`/`expect`。可以没有，那样只查编没编出 PDF、有没有报错与告警。

每份默认都查：编出了 PDF、日志里没有 `!` 开头的错、没有 hithesis 与 docxlike 的告警、没有
“Font shape … undefined”。引擎自己写明了的局限（pdfLaTeX 下全角标点不贴格那一条）
不算。PDF 靠 `mutool trace` 读，合成粗体认描边。工作目录在 `tests/feature/work/`，过了的删掉，
不过的留着看。

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
