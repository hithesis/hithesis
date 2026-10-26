# dev 发布记录

日期按北京时间的 dev 发布日期归档；同日构建以提交号区分。

## v3.2b-dev.1026 · 2026-10-26

提交：`debc8e12e985763e65dcc7e00da432d005c57dc9` · [构建记录](https://github.com/hithesis/hithesis/actions/runs/40262588957)

- 默认中文日期和英文封面月份改用北京时间，保留手工日期和基础类日期回退。
- 从论文信息填写 PDF 标题、作者和关键词，手工设置的 PDF 属性优先。
- URL 字符间距默认不拉伸，参考文献沿用用户指定的伸缩量及宏包已有断点。
- 新增 eqdenote 公式符号说明，按列对齐，支持折行和跨页，不占表号。
- 新增 symbols 列表式符号表，默认自动列宽，也可直接指定宽度；原 denotation 用法不变。

[本次提交差异](https://github.com/hithesis/hithesis/compare/46e43590ae23e44ee32b1ee488f8bbe8fa50fa8b...99c5bf95998149e35a54ff3a4e37195871f2a61a)

## v3.2b-dev.1025 · 2026-10-25

提交：`46e43590ae23e44ee32b1ee488f8bbe8fa50fa8b` · [构建记录](https://github.com/hithesis/hithesis/actions/runs/40157121487)

- 构建、文档或维护更新，详见提交记录。

[本次提交差异](https://github.com/hithesis/hithesis/compare/0fa674dec6375fe6abba04877afe92c40e6c3fc5...46e43590ae23e44ee32b1ee488f8bbe8fa50fa8b)

## v3.2b-dev.1025 · 2026-10-25

提交：`4d8d49ec9be23bbcce321a5d5b5d72b418758ae8` · [构建记录](https://github.com/hithesis/hithesis/actions/runs/40115202879)

- 补回此前仅合入 dev 的三校区更新：本科毕业论文与毕业设计选择、深圳本科使用本部样式、威海本文章标题间距统一。#282
- 补回哈尔滨硕士中期报告结构与封面更新，并取消深圳参考文献样式中的作者名全大写硬编码。
- 现有日期字段支持数字年月日格式，手写日期和元信息原值继续保留。
- 封面期间关闭页锚点并恢复调用方设置，书签将换行与 enskip 转为空格。
- 英文内封长字段自动折行，利用标题区空白容纳增加的行高。
- caption 支持尾随副语言、短标题和星号形式，长表共用入口并保留旧 bicaption。
- 增加 keywords-hanging 开关，关键词续行默认不再悬挂。

[本次提交差异](https://github.com/hithesis/hithesis/commit/0fa674dec6375fe6abba04877afe92c40e6c3fc5)
