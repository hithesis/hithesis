# 普通正文接 eqdenote 的独立边界探针

本例比较表形式的三行说明与相同数学符号、说明内容的三个普通段落，按各自 `Before` 基线归一化。
`After`、后接标题和其后正文也记录，避免只检查表内横向对齐。

在仓库根目录设置 `TEXINPUTS` 后，于新的工作目录复制 `main.tex`，分别用 XeLaTeX / LuaLaTeX 编译两遍。
首次修复核验使用 `mixed-note-a76d465467ca-b5d3909d` 运行时；博士、本科均测试。

修复前观察（历史记录）：

- XeLaTeX / Fandol：对应标记的相对基线差为 0。
- LuaLaTeX / Fandol：表首行相对普通段落低约 5.5bp，后接正文/标题相对早约 7.6bp。
- 使用实际 VM 的对应 Windows 字体再控制，Lua 首行仍有约 7.4bp 的差异，后续累计约 6.2bp。
- 因而不能只归因于 Fandol，不能通过固定负间距处理。

当前修复位于学校模块 `src/engine/hit-math.dtx`：已有 Lua 原生接排回调处理正文出段行距时，
说明表不再重复补胶；表撑杆通过公开试排接口取得当前正文字体的实际行盒。
本例 Fandol 的博士/本科、Xe/Lua 对照全部重合；Windows 纯文本对照的首末标记也重合，
原数学符号版本的首行差已归零。后续数学行盒约 1.1bp 的差异另记在修复报告中，不当作首行补胶误差抵消。

持久功能用例 `eqdenote-boundary` 覆盖正文、大小公式、标题、页首和连续说明表；
`eqdenote-pagination` 覆盖跨页、说明折行、嵌套试排和前一段脚注只执行一次。

这不是原整本 4.4 场景：原场景是两条显示公式直接接说明表。后者的约 18bp 已由独立 Word 对象
与字体角色控制解释，不能把本例与它合并为同一个问题。

原失败记录见 `build/reports/school-equation-spacing-feedback.md`；修复、回归及证据见
`build/reports/eqdenote-entry-fix-feedback.md` 及同名 summary.json / evidence.zip。

当前 `author-api-9561e82bd7d3-5b3501b2` 已完成学校公开接口迁移。
`eqdenote` 通过 `docxlike_native_boundary_get:NNN` 查询当前物理盒，
通过 `docxlike_native_boundary_mark:n` 标记 `hithesis/eqdenote`；原 callback/节点属性读取已移除。
72 项数学上下文、正式功能检查及整本门槛均通过。正文安装后的几何缓存须晚于安装激活，
并保留 LaTeX 的正 topskip 下限；首次时序失败与修复控制另存
`build/reports/author-api-consumer-feedback.md`。
