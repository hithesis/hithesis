# 子图专项测试

42 变体里的子图只覆盖示例正文里那几张，`subcapcenterlast` 分支、`\subtable`、
图目录里的子图条目都走不到。换宏包（[#284](https://github.com/hithesis/hithesis/issues/284)）
时要看的正是这些地方，所以单独一份。

```
bash tools/compile-subfigure.sh
OPT=subcapcenterlast bash tools/compile-subfigure.sh   # 走最后一行居中那条分支
```

输出在 `tests/work/subfigure/subfigure.pdf`。

覆盖：单语子图题、双语子图题（外层套内层的写法）、长子图题换行、`\subtable`、
三个子图排一行、`\ref` 与图目录条目。

## 与 subfigure 时代的差距

`subfigpkg` 选项已经去掉，`subcaption` 是唯一实现。拿 42 个变体对换包前的提交
逐页比：

- 竖向位移 **0**
- 断行变化 **0**
- 页数、编号、`\ref`、图目录条目全不变
- 只剩 2 个页面上 0.86bp（0.30mm）的横移，而且那两页**没有任何子图**——是加载
  `caption`/`subcaption` 对普通正文行的副作用（含 `\ref` 的那一行行内胶重新分配），
  与子图无关，还没查到根。

对齐是照 `subfigure` 的做法做的，不是补经验修正：

1. **行间胶**。`caption` 排图题前会放一条零高 `\hrule`（`\vspace` 在竖直模式的常规
   动作），`\hrule` 掐掉 TeX 的行间胶，图与图题之间少一整个 `\baselineskip`。图题
   先装 `\vbox` 再放进竖直列表，行间胶照常算；caption 的 `skip` 设成 0，由行间胶承担。
2. **strut**。`subfigure` 单行图题排成裸 `\hbox`，多行走 `\parbox`，两种情况行高都
   随文字走（`\parbox` 不自动加 strut）。`caption` 一律加，所以
   `\captionsetup[sub]{strut=false}`。
3. **参考点**。`subfigure` 的图题盒子高度是首行高度、其余算深度；`\vbox` 相反，把
   一切折进高度、深度为 0。先拿同样的字体量一遍图题（量的时候计数器还没走，
   `\thesubfigure` 拿到上一个号，宽高都一样），再用量出来的高度重设盒子高深。
4. **双语子图题**。两行之间隔着一段 `\subfigbottomskip`，那是旧写法内外两层子浮动体
   叠出来的结构，在图题文本里补不进去（`\vskip` 与 `\\` 在量宽度的 `\hbox` 里都
   非法）。所以 `\bisubcaption` 只当记号，由 `\subfigure` 认出来照旧结构递归摆一遍，
   外层排图题前把计数器退一格，两行共用同一个编号。
5. **空 `\subfigure`**。旧写法里 `\subfigure{\label{键}}` 会 `\leavevmode` 开段，
   兼容层吞掉它时也要 `\leavevmode`，否则后面那个换行空格的处理不一样。

子表题的位置在表上方：`subfigure` 那边是 `\ifsubtabletopcap`，这边按 `\@captype`
自己分，上方时上下留白对调并补 `\subfigcaptopadj`。

## 旧写法

兼容层接住三个旧习惯用法，用户文档不用改：

- `\subfigure{\label{键}}`：内容为空、只为占标签，记下标签留给下一个子图。
- 紧跟的 `\addtocounter{subfigure}{-2}`：吃掉。
- `\subfigure[英文]{\subfigure[中文]{图}}`：拆开按 `\bisubcaption` 的结构排。

新写法是 `\subfigure[\bisubcaption{中文}{英文}]{\label{键}图}`。

## 边界情形

42 变体查不出标签问题——示例里的 `golfer4x` 标签没人引用。下面这几种写法要单独试，
每种都应当 0 错误、0 `multiply defined`、`\ref` 全部解析：

1. 旧写法 `\subfigure{\label{键}}` + `\addtocounter{subfigure}{-2}`，并且真的 `\ref` 它
2. 嵌套但内层前面有别的记号（`\subfigure[EN]{\centering\subfigure[中文]{图}}`）——
   认不出来，会报一次提示并排成两个编号
3. `\subfigure{}` 内容真空
4. `subcaption` 原生环境语法 `\begin{subfigure}{宽度}...\end{subfigure}`
5. 新写法 `\subfigure[\bisubcaption{中文}{英文}]{\label{键}图}`

踩到过的两个：双语时内外两层都挂同一个标签会报一堆 `multiply defined`；只让内层挂
又写不进 `.aux`。现在是外层挂、内层跳过。
