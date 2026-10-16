# docxlike 公开接口审查与学校调用迁移

日期：2026-10-16。范围为最新完整冻结的双层接口、配置合同及 hithesis 调用。
独立 docxlike 仓库只读；本轮没有修改、生成或发布上游交付。

## 结论

当前已导入并接受完整冻结 `author-api-9561e82bd7d3-5b3501b2`，source SHA256 为
`9561e82bd7d3dcefdce2d024f90cb1e812e15a10bb1057ca6164e3cb3e887050`。
511 项负载和 3,799 项上游证据逐项核验，五个 runtime 独立提取并与正式生成结果逐字节一致。
原页眉 variant 崩溃、页面 owner 恢复后增量设置丢失均已独立复验关闭。

学校标题分页使用公开 opaque 段距快照；`eqdenote` 使用公开物理盒查询及 owner 标签，
不再访问库的私有段距量、callback 名或节点属性。正文通过导言区的公开安装请求接入；
目录域和数学试排数量改用结构化记录，类扩展属性登记了显式 reset/inherit 路径。
现有样式 `auto` 语义保持不变。

正式源码通过 127 项 Xe 宏测试、9 项实际 Lua 专项、10 项 Lua 入口检查和 154 份双遍功能 PDF。
博士/本科整本各编两遍后稳定，文字、页归属、横纵坐标与导入前完全相同；
历史门槛为 236/234、156/153，新同文门槛为 185/185、133/133。
隔离验收另实际执行了 158 项作者接口检查、288 项实际 Word 参考重放、64 项学校脚注状态检查、
72 项数学上下文及 6 项原页面阻塞反例/控制。详细版本关联、首次失败及修复控制见
`build/reports/author-api-consumer-feedback.md` 和同名 summary.json / evidence.zip。

## 历史集成记录

以下保留 page-settings 与 header-variants 两次审查的原计数、反例和未导入原因。
当时接受基线是 `mixed-note-a76d465467ca-b5d3909d`；这些待办已由上面的 author-api 验收接续。

**page-settings 后续集成复验**：该冻结的学校标题包装、256+32 多段注、126 份功能 PDF、72 个数学上下文
及整本门槛已通过；但新增“嵌套恢复后再增量设置”反例在 Lua/Xe 丢失当前层扩展键，
故仍未导入。此问题已缩减为只加载 article/docxlike 的反例，见
[`../sample/page-settings-owner-state/`](../sample/page-settings-owner-state/)。
完整后续结果在 `build/reports/page-settings-consumer-feedback.md`；下文保留原接口审查范围和计数。

**页眉修复交付复验**：header-variants 的 486 负载及 937 项上游证据摘要核验通过，五 runtime
独立重建一致；原 6 失败、8 控制、新 32 组合共 46 项全部通过、完整字形坐标差 0，
原 8 项公开接口/错误恢复也通过。页眉可移出未关闭问题列表，框高度说明及 auto 注释已校正。
页面 owner 反例在该冻结仍复现，因此仍未导入学校。详见
`build/reports/header-variants-consumer-feedback.md`。

## 审查版本与独立验证

- 冻结：`/Users/wujunhao/latex-docxlike/build/handoffs/page-settings-4abb23ce5ab3-5a91afb5/`。
- source SHA256：`4abb23ce5ab31dfe67edd1818af1049aa5ba08c0b82a7ed415e7203b29065df5`。
- 482 个负载文件全部按 `MANIFEST.json` 核对；12 dtx 在新目录独立提取，五个 runtime 逐字节一致。
- 对前基线 consumer-fixes 的源码变化确为六份：docxlike、page、format、linebreak、headfoot、heading。
- 证据包：`build/page-margins/page-settings-verified-evidence.zip`，
  SHA256 `ef9bb8115307c97bcb77f1a2d9603dd927389de4aa5dbbae8801df6f9d18085e`；
  24,338 项负载全部按 `RECORDING.json` 重读核对，源码和 runtime 与冻结一致。
- 在冻结的隔离副本重跑原 `test/public-entrypoints.py`：Lua/Xe 六组双层调用可见字形、页尺寸、
  坐标及域副作用一致，最大坐标差 0；两项错误恢复通过。
- 页面 278 几何 / 54 Word 失败安全 / 20 引擎限制，以及 288 多段注等结果，
  本轮核验的是已有证据和版本关联，没有把它们计为本地重新执行的 Word 矩阵。
- 私用字体仅通过临时链接供隔离测试读取，Times、Times Bold、SimSun 文件摘要核对一致。

工作目录及脚本：
`/var/folders/g5/r0fc07p15cj0b269wxp0t5440000gn/T/opencode/hit-public-api-audit-20261016/`。
其中 `audit.py`、`freeze-verification.json`、`public-entrypoints.json` 保存核验命令和结果；
`frozen-copy/` 是临时副本，不是新交付或学校 vendor。

## 发现与优先级

### 历史 P1：公开段落 variant 放进页眉会崩溃（header-variants 已独立复验关闭）

目标冻结的 `docxlike-headfoot.dtx:1088–1107` 公开生成了
`docxlike_par:Vn`、`:nV`、`:VV`，但页眉段落分派仅识别 `docxpar` 和 `docxlike_par:nn`。
variant 会进入外层自动段落包装；页眉尺寸测量时发生嵌套段落错误。

实际结果：

- 页眉 `:Vn` / `:nV` / `:VV` × Lua/Xe：6/6 在 `begin{document}` 附近失败，
  错误为 `You can't use \prevdepth in horizontal mode`。
- 同样的常量声明配合页眉 `:nn`，以及三种 variant 仅用于正文：8/8 通过，
  完整可见字形和坐标与原接口探针完全一致，最大差 0。
- 另有不依赖 Word 字体的最小反例：Lua/Xe 各一失败输入、一通过控制，共四项均符合预期。

原六组双层接口测试仍然通过；它只覆盖页眉中的 `:nn`，未覆盖这些 variant。
这是新增组合反例，不能把原测试通过解释为所有公开 variant 均可安全组合。

持久复现：[`../sample/docxlike-header-variant/`](../sample/docxlike-header-variant/)。
原始输入、日志和控制在工作目录的 `frozen-copy/build/public-header-variants/`、
`public-header-controls/` 和 `minimal-header-repro/`；汇总为
`header-variants.json`、`header-controls.json`、`minimal-header-repro.json`。
当前学校基线没有这些新 variant，本轮学校改动没有引入此调用。
后续 header-variants 已将四种公开签名纳入显式段落识别；上述原输入、八项控制、
新增页眉/页脚与空/非空格式的延迟变量组合均经消费方重跑通过，原失败记录保留。

### 历史 P1：学校标题分页和 eqdenote 依赖内部状态（author-api 已迁移关闭）

- `src/engine/hit-docxlike.dtx:80–87`：标题分页直接保存/恢复
  `g__docxlike_format_prev_after_dim`、`g__docxlike_format_pending_after_dim`、
  `g__docxlike_format_after_placed_bool` 三个私有量。
- `src/engine/hit-math.dtx:507–539`：eqdenote 查询内部 callback 名
  `docxlike.native-boundary`，读取节点属性 `docxlike_line_leading`。
  这是已修复入口重复补胶的学校桥接，但这些名字并未成为受支持的公开边界合同。
- 新冻结的 `docxlike-format.dtx:7547–7609` 提供公开试排函数，保存状态的辅助函数仍为
  `__docxlike_format_state_save:N`。试排服务不能直接代替真实清页/分节的状态管理。

这些依赖是消费方与库侧共同需要关闭的接入缺口，不等于刚修好的 eqdenote 几何回归失败。
应由库侧提供稳定的分页状态和原生盒接排合同，再由学校移除上述私有读取/写回；
不能将复制内部变量改成调用另一个内部函数后就称已使用公开接口。

### 历史 P1：结构化参数与作者安装入口未完成（author-api 已交付并接入）

依据上游 `doc/author-api-review.md:14–18,29–33,67–73`：

- 数量、制表位和域仍需空格分词，公开 expl3 名称尚未消除类作者回拼文本的需要。
  冻结 `test/public-entrypoints.py:36–37,52–55` 仍用空格替换成 `~`、`SEQ~Q` 等写法。
  原始域代码继续保留有兼容价值，但应补不依赖空格分词的编程形式。
- 作者安装的调用时机、重复调用、覆盖范围及与 normalsize/回调/页样式的关系尚待统一。
  例如冻结 `docxlike-format.dtx:6890–6903` 的 `docxlike_format_apply_body:` 包含
  `AddToHook` 等安装动作，不能未经合同确认就当作任意时刻可反复调用的刷新函数；
  已有 `docxlike_format_body_refresh:` 是另一项操作。
- 明确的恢复默认/去掉覆盖（继承）操作仍待设计，必须处理限定词与复合属性槽。
  本轮学校不改变现有样式 `auto` 的含义。

上游文档已经如实承认这些缺口，尚未将“原则获确认”写成“所有接口已完成”。

### 历史 P2：配置文档与既有代码不一致（header-variants 已校正）

- 冻结 `doc/configuration-semantics.md:48` 及其后续待办称框高度只接受存储、尚未完整参与布局；
  同冻结 `docxlike-shape.dtx:261,490–498` 已明确并实现“指定高度为最小高度，较高内容不裁剪”。
  应修正文档，区分最小高度与固定/裁剪高度；不能将现状误报为高度值完全被忽略。
- 冻结 `docxlike-format.dtx:280` 的注释将样式 `auto` 描述为删除显式值恢复继承，
  与配置说明中“先恢复登记默认、无默认才删除”的实际合同不一致。
  应以实际恢复逻辑和复合槽测试为准更新旧注释。

## 已遵守的原则

- 新增 setup/par/tab/parmark/bookmark/scoped-page/range 2e 包装转发公开 expl3 入口，
  共享设置器和执行路径；没有新增全量 PascalCase 别名。
- 样式 commit 自动完成；headfoot 的公开编程函数确实存在，不能因名字是 expl3 就认作私有。
- 冻结、源码集合、runtime 和证据版本明确关联；无网格 live 修改未混进页面冻结。
- Word 导出失败、Xe 限制、H 整盒合同、1px 图量纲差异与几何匹配分开计数，保留失败。
- 无网格最新记录明确 `word_geometry_complete=false`，不同阶段回归未拼作同版本全通过。

## 首轮学校量宽与分盒迁移的历史记录

- `src/pages/hit-final-titlepage.dtx:301–303`：英文题目量宽改用
  `docxlike_format_measure_width:nnNN`，输出 dim/bool 直接按 `N` 参数传递。
- `src/pages/hit-final-resolution.dtx:762–763`：决议分片改用
  `docxlike_textbox_split:NnNNN`，保留源盒可与余量盒别名以及四种状态处理。
- 两项公开函数已存在于当前 mixed-note，和原 PascalCase 包装共用同一实现。
  本次完成类文件提取，没有导入新的 vendor。
- 原 `l3build check -e xetex,luatex` 实际仅执行九项 Xe 检查：构建配置会跳过未登记的 Lua
  并退出 0，初版“18 个组合通过”的计数有误。后续集成已通过隔离配置补跑原基线和候选各九项
  真实 Lua 检查，完整同引擎日志和原语义断言一致；原跳过日志及 Xe/Lua Font Info 差异保留，
  详见 `build/reports/page-settings-consumer-feedback.md`。
- `titlepage-en-fit`、`resolution-layout` 在硕士中文、博士中文、博士英文、Lua/Xe 的
  12 份 PDF 各直接编译两遍，通过原功能检查；`.fls` 确认加载本次生成的学校类和当前 runtime。
- `make constcheck apilint inscheck productcheck mapcheck` 通过。
- 完整结果和日志：工作目录 `school-verification.json`、`targeted-macros.log`、`feature-check.log`。

## 作者接口接入要点与后续边界

- 正文首次安装在加载包后、导言区直接请求，不能首次放进文档开始钩子。
  学校选择 `cjk=external,normalsize=preserve,word-interline=false,rigid-ragged=false`，
  保留学校 CJK、字号及段间策略；安装在 `begindocument/end` 激活后才同步网格、缓存正文几何。
- 几何缓存保留 LaTeX 内核的 `topskip >= 1sp` 下限。初次迁移曾因过早缓存得到零值，
  造成四个 Lua 页首上下文多补约 5.5bp；旧安装控制与新安装后缓存控制已隔离验证。
  `118` 和 `128-author-body-boundary` 覆盖该时序，不用固定负间距补偿。
- 段距快照在外层竖直模式使用，只恢复真实段距。原生盒查询不消费余量；
  `hithesis/eqdenote` 标签属于当前物理盒，嵌套试排不能借外层页面。
- TOC 直接传 `file/levels/links/formatting` 记录，图表清单传 `caption`；不再回拼域代码。
  `129-author-style-operations` 检查类扩展槽的完整 reset 与重新继承；旧 `auto` 没有批量改义。
- 库侧未完成的无网格 Word 几何、NEU 半行段距与额外 clearpage 页眉页仍独立跟踪。
  本轮冻结不含 live nogrid；既有图盒和复杂脚注边界记录继续有效。

## 原审查时的库侧提示词（历史记录；页眉修复已关闭）

> 请只修改 `/Users/wujunhao/latex-docxlike`，学校仓库继续只读。先关闭公开段落 variant
> 与页眉故事组合的反例：page-settings-4abb23ce5ab3-5a91afb5 的 `docxlike_par:Vn/nV/VV`
> 放进 `docxlike_headfoot_set:nnn{header}` 后，Lua/Xe 六项均报
> `You can't use \prevdepth in horizontal mode`；同参数 `:nn` 及正文 variant 八项控制均通过、
> 坐标零差。最小原稿和普通字体通过控制在学校 `tests/sample/docxlike-header-variant/`，
> 完整证据在本报告所列临时工作目录。审查 `docxlike-headfoot.dtx:1088–1107` 的段落识别与
> 自动包装，补公开 variant、变量参数、空/非空格式及页脚的组合测试，保留原失败，
> 不只验证单独调用或原来的六组测试。随后明确公开分页状态/原生盒接排及作者安装合同，
> 让学校移除三项私有段距量、callback 名与节点属性依赖。数量/制表位/域的结构化调用及
> reset/inherit 仍是未完成项；框高度现为最小高度，先修过时文档，不要误删已有实现。
> 新修复应从完整基线做隔离回归和不可变交付，明确是否包含未完成 nogrid，不写入学校仓库。
