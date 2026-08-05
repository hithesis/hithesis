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
只剩一个恒定的竖向偏移（五号子图题下测得）：

| 位置 | modern 比 classic |
| --- | --- |
| 子图题 | 高 4.97bp |
| 主图题 | 高 2.74bp |

也就是图与子图题之间少 4.97bp，子图题与主图题之间多 2.23bp。已排除的原因：
`\subfigtopskip`（设成 0 两边同步变，差值不动）、`\baselineskip`（在图题前恢复
成外层的值，差值不动）。还没查的方向是 `subfigure` 单行子图题走的是裸
`\hbox to\@tempdima{\hss...\hss}`，而 `\subcaption` 一律排成段落，两者的
高度与 `\lineskip` 处理不同。
