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
