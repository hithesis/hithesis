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

用 `pdftotext -bbox` 逐词比位置。页数、编号、`\ref`、图目录条目一致。

| 情形 | 竖移 | 横移 |
| --- | --- | --- |
| 单语子图题 | 0 | 0 |
| 子表 | 0 | 1.5bp（列宽） |
| 双语子图题（`\bisubcaption`，两行） | 9.95～19.91bp | 0 |

单语的做法照抄 `subfigure`：它单行子图题排成裸 `\hbox`，高深随文字，排不下才退回
`\parbox`，那时才有 strut。所以这里也先拿同样的字体量一遍宽度（量的时候计数器还没
走，`\thesubfigure` 拿到上一个号，宽度一样），装得下就

1. `\captionsetup[sub]{strut=false}`，图题行的高深与 `subfigure` 逐值相同；
2. 把图题盒子的高度重设成量出来的首行高度、深度设成余下部分——`\vbox` 默认把一切
   折进高度、深度为 0，放进竖直列表时参考点是错的。

再加上图题先装 `\vbox` 再放进竖直列表（`caption` 排图题前会放一条零高 `\hrule`，
把行间胶掐掉，少一整个 `\baselineskip`）与 `skip=0pt`，单语情形逐值对齐。

双行还差着，原因是 `subfigure` 多行走 `\parbox[t]`：高度是首行的高度、其余算深度。
上面第 2 条对多行直接套会把整行的排布搞乱（试过，子图会重排），要按多行的首行高度
（带 strut）单独算。这是下一步。

子表题的位置两边都在表上方：`subfigure` 那边是 `\ifsubtabletopcap`，modern 这边按
`\@captype` 自己分，上方时上下留白对调并补 `\subfigcaptopadj`。

## 旧写法在 modern 下

兼容层接住了三个旧习惯用法，拿 `examples/hitbook/chinese` 那份真实文档
（一个字没改，只加 `subfigpkg=modern`）验过：0 错误、0 Overfull、50 页不变，
50 页里只有 4 页有位移，最大横移 1.62bp、最大竖移 11.53bp；这份示例的子图题全是
双语两行，正好是还没对齐的那一类。长子图题的断行点差一个字，那个差异来自写法本身
（一个图题盒排两行 vs 原来两个嵌套盒），换成 `\bisubcaption` 留在 classic 上也一样。

- `\subfigure{\label{键}}`：内容为空、只为占标签，记下标签留给下一个子图，本身不排。
- 紧跟的 `\addtocounter{subfigure}{-2}`：直接吃掉。
- `\subfigure[英文]{\subfigure[中文]{图}}`：拆开转成 `\bisubcaption`。

## 三种组合的差异

相对现状（旧写法 + classic），拿同一份 50 页示例量：

| 组合 | 有差异的页 | 最大横移 | 最大竖移 |
| --- | --- | --- | --- |
| 旧写法 + modern | 4/50 | 0.57mm | 4.07mm |
| 新写法 + modern | 4/50 | 0.98mm | 4.07mm |
| 新写法 + classic | 2/50 | 0.98mm | 1.44mm |

三组的文字流差异完全相同，都是第 27 页那条最长子图题的断行差一个字。
