# iota-hit 接口核对（2026-10-06）

核对对象：本地 iota-hit `fa93395`（工作区干净），hithesis `a4ec635` 加当前未提交修改。
双语输入现按用户后续决定采用 `{主语言}[副语言]` 与局部 `\bilingualswapon/off`；
`\keepvalue` 是解析器的保留标记，不注册全局命令。算法/代码第三方后端外观统一另行处理。
依据为两边源码，不以旧记忆或手册作为完成判据。日期字段按用户决定暂缓。

## 代码排版现状（2026-10-07 更新）

- hithesis 默认采用贪心断行、增强软断点、保留 100% 右页边空白；手册直接沿用类默认。
- 等宽字号校正与本机 iota/banshi 的 9 组结果一致，中文代码回落字形同步缩放，清单行盒按目标度量计算。
- 与真实 Word 的受控样例比较：模式 11、15 各 16/16 组断行一致；10 个等宽数字总宽差小于 0.03bp。
- 代码后的普通空格现按空格自身字体计算；113/107 个可比词首位置的最大相对横坐标差分别为
  0.187/0.197bp。原先约 3.613bp 的误差已修正，但还不能声称整页像素级一致。
- 对照使用无网格、无首行缩进、固定 18bp 行距；尚未覆盖完整论文的页眉、脚注、浮动体和分页组合。
- 半磅量化不能令任意替代字体字宽严格相等，Menlo 等字体的临界断行仍可能不同。
- Word 断行路径主要在 LuaLaTeX；XeLaTeX/pdfLaTeX 的断行机制不同。listings 等自管后端及严格字符网格仍有独立路径。
- 详见相邻 `latex-docxlike/test/mono-word/README.md` 与 `comparison.json`。以下接口清单保留原核对范围，不代表本次逐项重新验证。

## 字体预设更新

- `src/config/hit-font-presets.dtx` 统一保存 windows、macos、founder、noto、fandol 的角色表。
- `auto` 逐角色优先 Windows 字体，仅 macOS 上插入系统字体候选；所有预设缺项最终回退 fandol。
  数学默认统一为 TeX Gyre Termes Math，不随平台变化；显式角色允许覆盖。
- fandol 档的字体全部来自 TeX Live，按文件名加载；依赖为 fandol、tex-gyre、lm、tex-gyre-math。
  隶书、新魏没有对应回退字体，保留封面轮廓替代。
- macOS 的 LuaLaTeX 路径扫描 Apple 字体资源目录，按文件与 TTC 字面加载 Kaiti、STFangsong。
- noto 的楷体使用 arphic-ttf 提供的文鼎 PL 简中楷（gkai00mp.ttf），仿宋使用 lxgw-fonts 提供的朱雀仿宋；缺项与 founder 一样逐角色回退。
- LuaLaTeX 默认按 Windows 角色参考值校正中文字体墨迹中心；测常规字面的“国”（缺失时“國”），
  粗体、斜体继承该偏移，按实际字号换算，仅在输出时移动 glyph。
  `fontset={baseline-correction=auto/true/false}` 可在类选项与 hitsetup 使用；XeLaTeX/pdfLaTeX 暂不校正。
  字体角色预设与封面隶书、新魏已绑定；windows-local/mac-word 路径方案和无角色的自定义字体未绑定。
  `tests/font-baseline.tex` 检查混排、字重、代码字号、同字体不同角色、重复处理和行盒/断行不变。
- 支持 `fontset={preset=windows,mono=Menlo,fangsong=FangSong}`；中文、西文分项预设与旧名称保留兼容。
- Unicode 引擎使用 book，中文支持由 luatexja、xeCJK 提供；xeCJK 正常加载上游辅助包。
  pdfTeX 保留 ctexbook 的 CJK 初始化，具体版式仍由 docxlike 控制，见 `tests/chinese-backends.md`。
- Windows 预设的实际代码字体为 Consolas / FangSong，与真实 Word 输出中的字体家族一致。
- 代码中文当前按可用家族选择仿宋、楷体、宋体；罕见字的逐字回退仍受后端影响，不能据此声称完整复刻 Typst 的字体回退。
- 独立代码块仍有占列差异：当前 listings 固定列把中文按两个西文列占位；字体表对齐不等于该字距问题已解决。

## 深圳研究生报告更新

- 硕士开题、中期的中英文配置来自深圳教务部 2018 版 Word；博士暂时继承对应硕士版式。
- 四份封面各有段落序列、字段缩进和中英文行盒；开题保留深圳落款，中期不印落款。
- 正文页面、标题、目录、页眉页脚改由 docxlike 排版；Unicode 引擎全部使用 book。
- 删除旧深圳博士中期边框、表单及填写说明，删除旧 ctex 报告标题设置和固定页眉盒。
- 开题图表与公式连续编号，中期按节编号；目录及正文分别从阿拉伯数字 1 编号。
- 检查入口：`tests/run-shenzhen-report.py`，覆盖硕博 × 开题/中期 × 中英文八组。

## 已有对应入口

- `\sectionbreak` 为 Word 分节入口，continuous、next、odd、even 四选一，默认 next；设置可传入 columns、page-setup、page-number-format。
- 顶层标题要求分页时先清浮动体，再真实连续分节；报告与学位论文共用这一语义，保留原有右开页策略。
- 分节、页首段前、浮动体顺序和奇偶页测试见 `tests/sectionbreak.md`。JSON 转换暂未接入，后续方向为 iota4web JSON → hithesis。

- 文档轴：stage、campus、degree-level、degree-type、category、form、lang。
- 元信息：title、author、institution、student-id、supervisor、associate-supervisor、industry-supervisor、degree-applied、speciality、practice-type、affiliation、secrecy、classified-index、udc、school-code、report-number、station。
  hithesis 双语字段使用 `{主语言}[副语言]`；不是 Typst 的 `en[]` 语法。日期字段仍使用原有名字。
- 全文开关：openright、caption-bilingual、caption-numbering-by-top-level-heading、equation-numbering-by-top-level-heading、equation-numbering-fullwidth、theorem-numbering-by-top-level-heading、theorem-body-indent、top-level-heading-pagebreak-before、abbreviation-indexed/fullwidth/links、outline-entry-number-align、em-dash。
- algorithm-style、raw-style 已有预设，但不能据族名相同认定所有子项完全一致。
- cover、titlepage、abstract、table-of-contents、symbols、abbreviations、conclusions、achievements、defense、declarations 等都有对应命令或环境。
- iota 已将副导师更名为 associate-supervisor，两边现在一致。

## 有意保留的语法差别

- iota `enum-hanging` / `list-hanging` 对应 `enumerate-hanging` / `itemize-hanging`，用户已确认。
- 参考文献使用 LaTeX 的 `\bibliography`，gb7714 子键依 gbt7714/biblatex 后端，不机械照搬 omni-gb7714。
- 缩略语词条在 `\hitsetup{abbreviations=...}` 声明，合页用 `\printnomenclature`，不照搬 iota 参数组织。
- `layout`、`styles` 的底层能力由 docxlike 提供，需按 Word 属性映射，不能直接复制 banshi 的键值结构。

## 尚未对应的全文接口

| iota 参数 | hithesis 当前情况 | 后续工作 |
|---|---|---|
| title-case | 无同名全局标题大小写入口；文献的 sentence-case 是另一回事 | 明确适用标题与语种后映射 |
| two-hanzi | 通过词条 heading-spread 等控制，两字标题没有统一入口 | 对齐取值及作用范围 |
| note-width | 已有图表注释命令，无同名统一宽度开关 | 核对 figurenote 与表注实现 |
| subcaption-numbering/separator/bilingual/gap | 已有 subcaption 及旧 subfigure 兼容层，无这四个顶层键 | 保留环境原生能力并加映射 |
| heading-body-indent | 无同名入口，现由样式和标题代码决定 | 核对标题后正文缩进 |
| appendix-numbering | 按学位默认选择数字或字母，无同名可配置入口 | 映射章号、目录与引用 |
| outline-entry-right-margin | 无同名入口 | 核对目录行可用宽与页码列 |
| page-numbering | 可用 LaTeX 命令及页面设置，没有同名入口 | 区分编号格式与分区起始值 |
| metrics、fake-bold、fake-italic | 字体度量及合成字形能力分布在 docxlike/fontset/styles | 先比能力、取值与引擎支持，再决定公开接口 |

副题目内容已独立为 `info/subtitle`，使用统一双语值；hithesis 另有 `show-subtitle` 显示开关，iota 当前由内容是否存在决定显示。

## 部件参数差异

依据：iota `src/pages/front.typ`；hithesis `hit-keylist.dtx`、`hit-final-abstract.dtx`、`hit-final-toc.dtx`。

- **cover**：本轮已接题目、作者、校名、practice-type 等局部值。未接 iota 的局部 degree-level/degree-type/form、layout、overrides、label、warning、annotated；日期暂缓。
- **titlepage**：已有中英题目、副题目、元信息和 shown。缺 lang（目前硕博同时排中英）、fields（可配置字段行）、degree-attribute、局部 form/degree-level、layout、overrides、openright、label、warning、annotated。
  hithesis 用页面的 `info={...}` 设置双语局部值；iota 的 `en` 是英文页参数字典，二者结构不同。
- **abstract**：已有 lang、keywords、keywords-hanging、shown；缺局部 title、overrides、openright、layout、keywords-above、styles。
- **table-of-contents**：已有 depth、lang、outline-entry-number-align。缺 title、two-hanzi、openright、outlined、levels、heading-body-indent、outline-entry-right-margin、fill、layout、overrides、warning。图表清单也需单独核对。

## 不能声称“语义已完全一致”的地方

- hithesis 列表 `auto` 保留现有变体；iota/banshi 的编号列表默认不悬挂，项目列表默认悬挂。
- hithesis 编号 `auto` 保留变体原逻辑；显式 true/false 已验证，仍需对照 iota 最新变体默认表。
- abbreviation-links 在 hithesis 链接到已排出的具体条目；iota 在 `printed` 为真时链接到表。跳转目标不同。
- 顶层标题换页：所有报告均接 docxlike；深圳硕博报告不再使用 ctex 标题路径。
- overrides 只有 references/achievements/defense 的公开分组名对齐，内部前缀仍为 bibliography/publications/resolution；iota 标题叶子用 title，hithesis 用 heading。不存在完整词条结构同构。

## 建议推进次序

1. titlepage 的 lang、fields：直接影响用户如何组织内封。
2. 分图四个开关：核对原生 subcaption 功能后映射。
3. 部件级 overrides/layout/openright，与 docxlike 明确分工。
4. 标题、附录、目录的剩余开关及默认语义差异。

本次仅核查，不自动实现上述缺项。验证按功能选小用例，不为接口盘点运行全量回归。
