# 子图专项测试

42 变体里的子图只覆盖示例正文里那几张，`subcapcenterlast` 分支、`\subtable`、
图目录里的子图条目都走不到。换宏包（[#284](https://github.com/hithesis/hithesis/issues/284)）
时要看的正是这些地方，所以单独一份。

```
bash tools/compile-subfigure.sh                    # classic，当前默认
OPT=subfigpkg=modern bash tools/compile-subfigure.sh
```

输出在 `tests/work/subfigure/subfigure.pdf`。

覆盖：单语子图题、双语子图题（外层套内层的写法）、长子图题换行、`\subtable`、
三个子图排一行、`\ref` 与图目录条目。

## classic 与 modern 的差距

用 `pdftotext -bbox` 逐词比位置。同一份源码换引擎，**竖向零位移**；页数、编号、
`\ref`、图目录条目一致。唯一剩下的是子表的列宽差 1.5bp，属于 `tabular` 在两种
子浮动体盒子里的自然宽度差，不影响版面。

对齐是照 `subfigure` 的做法做的，不是补经验修正：

1. **行间胶**。`caption` 排图题前会放一条零高 `\hrule`（`\vspace` 在竖直模式的常规
   动作），`\hrule` 掐掉 TeX 的行间胶，图与图题之间少一整个 `\baselineskip`。图题
   先装 `\vbox` 再放进竖直列表，行间胶照常算。caption 的 `skip` 一并设成 0，由行间
   胶承担。
2. **strut**。`subfigure` 单行图题排成裸 `\hbox`，多行走 `\parbox`，两种情况的行高
   都随文字走，`\parbox` 不自动加 strut。`caption` 一律加，深度固定。所以
   `\captionsetup[sub]{strut=false}`。
3. **参考点**。`subfigure` 的图题盒子高度是首行高度、其余算深度（裸 `\hbox` 与
   `\parbox[t]` 都是如此）；`\vbox` 相反，把一切折进高度、深度为 0。所以先拿同样的
   字体量一遍图题（量的时候计数器还没走，`\thesubfigure` 拿到上一个号，宽度高度都
   一样），再用量出来的高度把图题盒子的高深重设一遍。

子表题的位置两边都在表上方：`subfigure` 那边是 `\ifsubtabletopcap`，modern 这边按
`\@captype` 自己分，上方时上下留白对调并补 `\subfigcaptopadj`。

## 旧写法在 modern 下

兼容层接住了三个旧习惯用法：

- `\subfigure{\label{键}}`：内容为空、只为占标签，记下标签留给下一个子图，本身不排。
- 紧跟的 `\addtocounter{subfigure}{-2}`：直接吃掉。
- `\subfigure[英文]{\subfigure[中文]{图}}`：拆开转成 `\bisubcaption`。

拿 `examples/hitbook/chinese` 那份 50 页真实文档量的三组数（相对现状「旧写法 +
classic」）：

| 组合 | 有差异的页 | 最大横移 | 最大竖移 | 断行 |
| --- | --- | --- | --- | --- |
| 只换写法（留在 classic） | 2/50 | 0.98mm | 1.44mm | 第 27 页 |
| 只换引擎（旧写法不动） | 4/50 | 0.57mm | 1.44mm | 第 27 页 |
| 已换写法后再换引擎 | 2/50 | 0.30mm | **0** | 无 |

三组都是 0 错误、0 Overfull、50 页不变。剩下的 1.44mm 和那处断行**来自写法本身**
（一个图题盒排两行 vs 原来两个嵌套盒），不是引擎差异——「只换写法留在 classic」
这一行的数字与「只换引擎」相同就是证据。
