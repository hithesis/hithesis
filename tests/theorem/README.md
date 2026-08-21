# 定理环境专项测试

`tests/variants` 那 42 个变体只用到 `theorem`/`definition`/`axiom`/`lemma`/`remark`
五个环境，`proof` 一个都没有。换定理实现（[#183](https://github.com/hithesis/hithesis/issues/183)
把 `ntheorem` 换成 `thmtools`）时最容易出问题的恰好是 `proof` 的结束符与跨页，
所以单开这份文档。

覆盖：十三个编号环境、三种注记、`\ref`/`\autoref`、`proof` 的四种收尾
（文字/行内公式/显示公式/列表）、嵌套、跨页、以及手册和示例里教的三种自定义写法。

跑法：

    bash tools/compile-theorem.sh            # 中文
    LANG_OPT=lang=en bash tools/compile-theorem.sh

换实现前后各跑一遍，`cmp` 两个 PDF。
