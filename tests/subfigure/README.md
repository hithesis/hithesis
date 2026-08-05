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

用 `pdftotext -bbox` 逐词比位置，两边页数、横排、编号、`\ref`、图目录条目一致，
只剩竖向偏移（五号子图题下测得）：

| 位置 | modern 比 classic |
| --- | --- |
| 子图题 | 高 4.10bp |
| 图之后的正文 | 高 1.86bp |

原因查清了，两个数都来自图题盒子的深度：

- `subfigure` 单行子图题排成裸 `\hbox`，深度是文字的自然深度，这份内容下是
  1.865pt。`caption` 排成段落，行里带 strut，深度固定 4.110pt，装进 `\vbox`
  之后又被折进高度，盒子深度成了 0。图之后的材料因此高 1.865bp。
- 子图题自身再多差一个 strut 的深度超出量 2.245pt，合起来 4.11bp。

已经排掉的原因：`\subfigtopskip`（tight 模式下 TeX Live 自带的 `subfigure.cfg`
把它设成 5pt，两边都加）、`\baselineskip`（图题先装 `\vbox` 再放进竖直列表，行间
胶已经和 `subfigure` 一致，图题基线离内容底两边都是 20.58083pt）、caption 的
`skip`（设成 0，改由行间胶承担）。

要抹平只能剥掉 `caption` 的 strut，那等于放弃它保证的子图题基线整齐。这里认为
`caption` 的做法更好，差值留着。

## 旧写法在 modern 下

兼容层接住了三个旧习惯用法，拿 `examples/hitbook/chinese` 那份真实文档
（一个字没改，只加 `subfigpkg=modern`）验过：0 错误、0 Overfull、50 页不变，
50 页里只有 4 页有位移。

- `\subfigure{\label{键}}`：内容为空、只为占标签，记下标签留给下一个子图，本身不排。
- 紧跟的 `\addtocounter{subfigure}{-2}`：直接吃掉。
- `\subfigure[英文]{\subfigure[中文]{图}}`：拆开转成 `\bisubcaption`。

## 已知问题

`\subtable` 在 modern 下会把表格内容吃掉，只剩子表题。同一个 `tabular` 改用
`\subfigure` 放在 `table` 里就正常，所以问题在 `\subtable` 的分发路径上，不在
`\__hit_subfloat:nn`。已排除：`\@currenvir` 在 `table` 浮动体里确实是 `table`
（分发应当走命令那支）、`tabular` 装箱正常（48.09pt × 24.28pt）、后面没有别的包
再改 `\subtable`。
