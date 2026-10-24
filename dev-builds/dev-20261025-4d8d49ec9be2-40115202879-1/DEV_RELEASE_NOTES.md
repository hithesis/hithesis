# v3.2b-dev.1025

发布日期：2026-10-25（北京时间）

源版本：v3.2b，提交：`4d8d49ec9be23bbcce321a5d5b5d72b418758ae8`

- 补回此前仅合入 dev 的三校区更新：本科毕业论文与毕业设计选择、深圳本科使用本部样式、威海本文章标题间距统一。#282
- 补回哈尔滨硕士中期报告结构与封面更新，并取消深圳参考文献样式中的作者名全大写硬编码。
- 现有日期字段支持数字年月日格式，手写日期和元信息原值继续保留。
- 封面期间关闭页锚点并恢复调用方设置，书签将换行与 enskip 转为空格。
- 英文内封长字段自动折行，利用标题区空白容纳增加的行高。
- caption 支持尾随副语言、短标题和星号形式，长表共用入口并保留旧 bicaption。
- 增加 keywords-hanging 开关，关键词续行默认不再悬挂。

[详细更新说明（PDF）](https://hithesis.site/dev-builds/dev-20261025-4d8d49ec9be2-40115202879-1/DEV_UPDATE.pdf)

[下载模板](https://hithesis.site/?version=dev) · [构建记录](https://github.com/hithesis/hithesis/actions/runs/40115202879)
