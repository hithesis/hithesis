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

用 `pdftotext -bbox` 逐词比位置。两边页数、横排、编号、`\ref`、图目录条目一致，
横向最大差 1.5bp（子表列宽），竖向：

| 位置 | modern 比 classic |
| --- | --- |
| 单语子图题 | 高 4.09bp |
| 双语子图题（两行） | 高 9.95～19.91bp |
| 图之后的正文 | 高 1.86bp |

原因是图题盒子的深度：`subfigure` 单行子图题排成裸 `\hbox`，深度随文字走（这份
内容下 1.865pt）；`caption` 排成段落，行里带 strut，深度固定 4.110pt，装进 `\vbox`
之后又折进高度，盒子深度成了 0。图之后的材料因此高 1.865bp，子图题自身再多差一个
strut 深度超出量 2.245pt，两行就翻倍。

已经排掉的原因：`\subfigtopskip`（TeX Live 自带的 `subfigure.cfg` 把 subfigure 设成
tight，两边都是 5pt）、`\baselineskip`（图题先装 `\vbox` 再放进竖直列表，行间胶已
与 `subfigure` 一致，图题基线离内容底两边都是 20.58083pt）、caption 的 `skip`（设成
0，改由行间胶承担）。

要抹平只能剥掉 `caption` 的 strut，那等于放弃它保证的子图题基线整齐。这里认为
`caption` 的做法更好，差值留着。

子表题的位置两边都在表上方：`subfigure` 那边是 `\ifsubtabletopcap`，modern 这边按
`\@captype` 自己分，上方时上下留白对调并补 `\subfigcaptopadj`。
