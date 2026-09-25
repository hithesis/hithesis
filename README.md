# hithesis：哈尔滨工业大学 LaTeX 论文模板

[![Test](https://github.com/hithesis/hithesis/actions/workflows/test.yml/badge.svg?branch=master)](https://github.com/hithesis/hithesis/actions/workflows/test.yml)
[![GitHub release](https://img.shields.io/github/v/release/hithesis/hithesis)](https://github.com/hithesis/hithesis/releases)
[![CTAN](https://img.shields.io/ctan/v/hithesis)](https://ctan.org/pkg/hithesis)

hithesis 用于排版哈尔滨工业大学一校三区的本科、硕士和博士毕业论文（设计），
也支持开题报告、中期报告、英文论文和博士后出站报告。现行接口只有一个文档类
`hithesis`，交付物由 `stage=final|proposal|interim` 选择。

模板已收录于 [CTAN](https://ctan.org/pkg/hithesis)。发行版适合直接使用；`dev`
分支包含尚未发布的改动，升级前应先用自己的论文完整编译一次。完整说明见项目生成的
`hithesis.pdf`。

English summary: hithesis is a LaTeX class for HIT theses, dissertations,
proposals, interim reports and postdoctoral reports on all three campuses.
Chinese and English final documents are supported.

## 快速开始

从仓库源码使用时，先生成并分发类文件：

```shell
make cls
cd examples/demo
make final       # 学位论文
make report      # 开题或中期报告
```

默认引擎是 LuaLaTeX。XeLaTeX 仍能编译，但模板的 Word 式断行和逐行行高计算只在
LuaLaTeX 下启用。一份即将提交的稿件不要中途换引擎。

最小的类选项写法如下：

```latex
\documentclass[
  stage=final,
  degree-level=doctor,
  campus=harbin
]{hithesis}
```

建议复制 [`examples/demo/`](examples/demo/) 再改。`final.tex` 排学位论文，
`report.tex` 排开题或中期报告，`info.tex` 放两者共用的作者、题目和院系信息。

## 支持范围

| 校区 | 学位 | 终稿 | 开题 | 中期 |
| --- | --- | :---: | :---: | :---: |
| 哈尔滨 | 本科、硕士、博士 | 支持 | 支持 | 支持 |
| 深圳 | 本科、硕士、博士 | 支持 | 支持 | 支持 |
| 威海 | 本科、硕士、博士 | 支持 | 支持 | 支持 |

另支持博士后出站报告和英文学位论文。不同校区、学位和材料的封面与正文规则由类选项
分流，不需要换文档类。

## 版式能力

- 封面、内封、中英文摘要、目录、声明页、答辩决议和博士后封面按校区与学位选择。
- 支持双语题注、图表清单、符号表、缩略语表、中英文索引和成果页。
- 参考文献可选 BibTeX 或 biber；表格与长表使用 `tabularray`，子图使用 `subcaption`。
- 打印版可按学位启用右开页；图书馆电子版可关闭空白页。
- 排版数值来自学校规范和 Word 范例的测量。两者冲突时，手册或源码注释会写明取舍。

## 安装

模板支持 TeX Live 2022 及以上版本，排版基准是 TeX Live 2026。LuaLaTeX 和
XeLaTeX 都需要 OpenType 中文字体；没有学校常用字体时可用 TeX Live 自带的 Fandol。

最省事的做法是安装完整 TeX Live。精简安装可按
[`.github/tl_packages`](.github/tl_packages) 补齐项目实际用到的宏包：

```shell
tlmgr install $(grep -v '^#' .github/tl_packages)
```

示例中的 EPS 插图还需要 Ghostscript。只想使用 CTAN 发行版时，不必生成类文件；
直接复制示例并按本机 TeX 发行版的方式编译即可。

## 从源码生成

有 `make` 时运行：

```shell
make cls
```

这会从 `.dtx` 源码生成 `hithesis.cls`、`hithesis.cfg`、参考文献与索引样式，
并复制到示例目录。没有 `make` 时可直接运行：

```shell
xetex src/hithesis.dtx
```

CTAN 源码包也可以按惯例运行 `latex hithesis.ins`。仓库里的
`src/hithesis.dtx` 含中文，直接解包时使用 `xetex`，不要用 plain `tex`。

用户手册由下面的命令生成：

```shell
make manual
```

## 编译论文

示例目录已经带有 `latexmkrc`，通常只需：

```shell
cd examples/demo
latexmk final.tex
```

也可以运行 `make final` 或 `make report`。手工编译需要按参考文献后端运行
BibTeX 或 biber，并重复运行 LuaLaTeX 直到交叉引用稳定；要生成主题索引时还需运行
`splitindex`。具体命令和两条参考文献路线见用户手册。

## 打印版与电子版

博士论文通常双面打印，本科和硕士通常单面打印。需要每章从右页开始时设置
`openright=true`；只想在个别位置换到右页，可关闭该选项并在目标位置写
`\cleardoublepage`。

图书馆电子版一般不留右开页产生的空白页，设置 `library=true` 即可。这个选项会
同时关闭 `openright`。

## 规范来源

| 校区   | 学位                                   | 撰写规范                                                                                                                                                                                   | Word排版范例                                                                                                                                                                               | 更新日期   |
| ------ | -------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------- |
| 深圳   | 本科毕业                               | -                                                                                                                                                                                          | [关于做好2022届本科生毕业设计（论文） 答辩工作的通知](https://www.hitsz.edu.cn/article/view/id-132766.html)                                                                                |
| 深圳   | 硕士/英文版硕士暂行规定                | [哈工大（深圳）学术规范及硕士学位论文撰写文件包（2020年版）](http://due.hitsz.edu.cn/info/1211/1859.htm)                                                                                   | 同左                                                                                                                                                                                       | 2020-10-23 |
| 深圳   | 硕士中期                               | -                                                                                                                                                                                          | [硕士学位论文中期报告模板](http://due.hitsz.edu.cn/info/1210/4794.htm)<!-- http://due.hitsz.edu.cn/info/1210/1828.htm -->                                                                  | 2023-01-31 |
| 深圳   | 博士开题                               | -                                                                                                                                                                                          | [博士学位开题报告模板](http://due.hitsz.edu.cn/info/1252/1865.htm)                                                                                                                         | 2018-07-31 |
| 深圳   | 博士中期                               | -                                                                                                                                                                                          | [博士学位论文中期检查报告](http://due.hitsz.edu.cn/info/1253/1860.htm)                                                                                                                     | 2018-07-31 |
| 深圳   | 博士毕业                               | [哈尔滨工业大学研究生学位论文撰写规范（2011版）](http://due.hitsz.edu.cn/info/1243/1776.htm)                                                                                               | [哈尔滨工业大学研究生学位论文书写范例（2011版）](http://due.hitsz.edu.cn/info/1243/1777.htm)                                                                                               | 2018-07-31 |
| 深圳   | 英文版博士毕业                         | [Thesis-Tmplt(英文论文撰写规范)](http://due.hitsz.edu.cn/info/1243/1775.htm)                                                                                                               | 同左                                                                                                                                                                                       | 2018-07-31 |
| 威海   | 本科所有                               | [本科毕业论文撰写规范和相关资料](http://jwc.hitwh.edu.cn/bysj/list.htm)                                                                                                                    | 同左                                                                                                                                                                                       | 2021-11-29 |
| 威海   | 硕士                                   | [研究生学位论文撰写规范](http://yjsc.hitwh.edu.cn/2012/1217/c981a37691/page.htm)                                                                                                           | [研究生学位论文书写范例](http://yjsc.hitwh.edu.cn/2012/1217/c981a37689/page.htm)                                                                                                           | 2012-12-17 |
| 威海   | 硕士                                   | [硕士学位论文撰写规范自查表2011版](http://yjsc.hitwh.edu.cn/2015/1230/c981a37718/page.htm)                                                                                                 | 同左                                                                                                                                                                                       | 2015-12-30 |
| 哈尔滨 | 本科所有                               | [毕业论文撰写规范](http://jwc.hit.edu.cn/2014/0504/c4305a116176/page.htm)                                                                                                                  | [所有word范例](http://jwc.hit.edu.cn/2566/list.htm)                                                                                                                                        | 2022-06    |
| 哈尔滨 | 硕士开题中期                           | -                                                                                                                                                                                          | [所有word范例](http://hitgs.hit.edu.cn/2015/1210/c3359a123058/page.htm)                                                                                                                    | 2015-12-10 |
| 哈尔滨 | 博士开题中期                           | -                                                                                                                                                                                          | [所有word范例](http://hitgs.hit.edu.cn/2015/1210/c3416a123048/page.htm)                                                                                                                    | 2015-12-10 |
| 哈尔滨 | 硕博毕业论文所有（含有部分英文版说明） | [研究生学位论文或者实践成果写作指南](https://hitgs.hit.edu.cn/2025/0331/c17373a365618/page.htm) | [研究生学位论文书写范例（理工类）](https://hitgs.hit.edu.cn/2021/0513/c17373a317228/page.htm)<br>[研究生学位论文书写范例（人文社科类）](https://hitgs.hit.edu.cn/2021/0508/c17373a317224/page.htm)<br>[博士研究生学位论文书写范例（理工类）](https://hitgs.hit.edu.cn/2021/0513/c17461a318415/page.htm)<br>[博士研究生学位论文书写范例（人文社科类）](https://hitgs.hit.edu.cn/2021/0508/c17461a318413/page.htm) | 2026-03-20 |
| 哈尔滨 | 博后                                   | -                                                                                                                                                                                          | [出站报告以及封皮](http://rsc.hit.edu.cn/2015/1209/c10906a212031/page.htm)                                                                                                                 | 2015-12-09 |

项目没有替学校解决规范本身的矛盾。已知问题包括版心、行距、章节标题是否加粗、
中英文摘要标题大小写、页眉横线，以及规范和 Word 范例对每行字数的不同要求：
[版心说明](http://yanshuo.site/cn/2017/06/hithesisregulation/)、
[本科生行距说明](http://yanshuo.site/cn/2017/06/hithesissiyuan/)。

## 下载、提问与维护

- 稳定版：[GitHub Releases](https://github.com/hithesis/hithesis/releases)
- TeX 发行版：[CTAN](https://ctan.org/pkg/hithesis)
- 问题与缺陷：[GitHub Issues](https://github.com/hithesis/hithesis/issues)
- QQ 群：259959600、851792460、704864357

提问时请附最小示例、完整日志、TeX Live 版本和使用的引擎。项目只实现公开的学校规范；
院系或评审老师提出的临时口径，需要提供原始文件或可复核的截图。

开发约定、模块边界和检查命令见 [`CONTRIBUTING.md`](CONTRIBUTING.md)。hithesis
源自 [PlutoThesis](https://github.com/dustincys/PlutoThesis)，并参考了 thuthesis
等高校论文模板的实现。

## 版本号

v3 使用 `vX.Yz`，最后一版是 v3.2x。v4 起改用 `vX.YYYYz`：

| 段 | 含义 |
| --- | --- |
| X | 架构版本，整体重写时进位 |
| YYYY | 服务的毕业年份 |
| z | 该年份内的版本，从 `a` 开始 |

开发版在字母后加月日，例如 `v4.2026a0813`；发布时去掉月日。年份写进版本号后，
可以直接看出手上的模板服务哪个毕业季，字符串顺序也与新旧版本的时间顺序一致。

## 许可

源码按 LaTeX Project Public License 1.3c 或后续版本发布。仓库中的文档内容同时采用
[CC BY-NC 4.0](http://creativecommons.org/licenses/by-nc/4.0/) 许可。

## 赞助

hithesis 由维护者在业余时间开发。如果模板帮你省下了排版时间，可以赞助下面的维护者。

|                   维护者                   |                                          微信                                           |                                          支付宝                                          |
| :----------------------------------------: | :--------------------------------------------------------------------------------------: | :--------------------------------------------------------------------------------------: |
|    [@syvshc](https://github.com/syvshc)    | ![szh_wechat](https://raw.githubusercontent.com/hithesis/hithesis/images/szh_wechat.jpg) | ![szh_alipay](https://raw.githubusercontent.com/hithesis/hithesis/images/szh_alipay.jpg) |
| [@dustincys](https://github.com/dustincys) | ![cys_wechat](https://raw.githubusercontent.com/dustincys/hifvwm/screenshots/wechat.jpg) |     ![sys_alipay](http://wx3.sinaimg.cn/large/61dccbaaly1fizali9tafj20k00ucgos.jpg)      |
| [@xiF616](https://github.com/xiF616) | ![616_wechat](https://raw.githubusercontent.com/hithesis/hithesis/images/616_wechat.jpg) | ![616_alipay](https://raw.githubusercontent.com/hithesis/hithesis/images/616_alipay.jpg) |
| [@SchrodingerBlume](https://github.com/SchrodingerBlume) | ![SchrodingerBlume_wechat](https://raw.githubusercontent.com/SchrodingerBlume/hithesis/images/SchrodingerBlume_wechat.png) | ![SchrodingerBlume_alipay](https://raw.githubusercontent.com/SchrodingerBlume/hithesis/images/SchrodingerBlume_alipay.jpg) |

Zelle：yanshuoc@gmail.com

### 赞助记录

名单如有遗漏，请联系维护者补充。

| Time       | Name      | Comments        |
| ---------- | --------- | --------------- |
| 2020-05-06 | Li Liming |                 |
| 2020-06-16 | 航明      |                 |
| 2020-06-28 | *鑫       |                 |
| 2020-07-20 | CR        | Wechat          |
| 2020-08-13 | d*g       |                 |
| 2020-09-11 | **扬      |                 |
| 2020-11-03 | **宝      |                 |
| 2020-11-05 | **庭      |                 |
| 2021-01-04 | **杰      |                 |
| 2021-02-27 | *晰       |                 |
| 2021-04-29 | *振兴     | Alipay          |
| 2021-04-21 | *作       |                 |
| 2021-05-06 | *文陶     | Zelle quick pay |
| 2021-05-13 | *涵       |                 |
| 2021-05-13 | 慕*       |                 |
| 2021-05-28 | Y*a       |                 |
| 2021-06-19 | *淞       |                 |
| 2021-10-18 | q*q       |                 |
| 2021-11-21 | **刚      | Alipay          |
| 2022-07-06 | 初八      | Wechat          |
| 2022-07-19 | 夏日的风  | WeChat          |
| 2022-08-26 | Yang      | WeChat          |
| 2022-10-18 | cyf       | WeChat          |
| 2023-02-28 | hidadeng  | QQ              |
| 2023-04-16 | Yang      | Alipay          |
| 2023-04-28 | Lin       | Alipay          |
| 2023-05-11 | hzy       | WeChat          |
| 2023-09-05 | 曹世达    | Wechat          |
| 2023-11-30 | JerryLiu  | WeChat          |
| 2024-03-12 | Chuck     | Alipay          |
| 2024-04-09 | 老学水    | Alipay          |
| 2024-04-10 | csat      | WeChat          |
| 2024-04-14 | Cen       | WeChat          |
| 2025-01-14 | 沉梦昂志  | WeChat          |
| 2025-03-10 |  xw       | Alipay          |
| 2025-04-09 | Lrz       | WeChat          |
| 2026-01-03 | 无题      | Alipay          |
| 2026-01-26 | *新       | WeChat          |
| 2026-03-20 | 青云      | WeChat          |
| 2026-08-01 | w*r       | WeChat.         |
