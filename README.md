# hithesis 哈尔滨工业大学LaTeX论文模板

<!-- [![docker-build-TinyTeX-hithesis](https://github.com/hithesis/hithesis/workflows/docker-build-TinyTeX-hithesis/badge.svg?branch=master)](https://github.com/hithesis/hithesis/actions?query=workflow%3Adocker-build-TinyTeX-hithesis) -->
<!-- [![TinyTeX](https://github.com/hithesis/hithesis/workflows/TinyTeX/badge.svg?branch=master)](https://github.com/dustincys/hithesis/actions?query=workflow%3ATinyTeX) -->
<!-- [![MiKTeX](https://github.com/hithesis/hithesis/workflows/MiKTeX/badge.svg?branch=master)](https://github.com/dustincys/hithesis/actions?query=workflow%3AMiKTeX) -->
<!-- [![MacTeX](https://github.com/hithesis/hithesis/workflows/MacTeX/badge.svg?branch=mac)](https://github.com/dustincys/hithesis/actions?query=branch%3Amac)  -->
<!-- [![TeXLive](https://github.com/hithesis/hithesis/workflows/TeXLive/badge.svg)](https://github.com/dustincys/hithesis/actions?query=workflow%3ATeXLive) -->

[![ubuntu-dockerhub-hithesis](https://github.com/hithesis/hithesis/actions/workflows/test_ubuntu_dockerhub_hithesis.yml/badge.svg)](https://github.com/hithesis/hithesis/actions/workflows/test_ubuntu_dockerhub_hithesis.yml)

[![macos-dockerhub-hithesis](https://github.com/hithesis/hithesis/actions/workflows/test_macos_dockerhub_hithesis.yml/badge.svg)](https://github.com/hithesis/hithesis/actions/workflows/test_macos_dockerhub_hithesis.yml)

[![GitHub tag (latest by date)](https://img.shields.io/github/v/tag/hithesis/hithesis)](https://github.com/hithesis/hithesis/releases)
[![GitHub release (latest by date)](https://img.shields.io/github/v/release/hithesis/hithesis)](https://github.com/hithesis/hithesis/releases)
[![CTAN](https://img.shields.io/ctan/v/hithesis)](https://ctan.org/pkg/hithesis)
![GitHub repo size](https://img.shields.io/github/repo-size/hithesis/hithesis)
<!-- [![GitHub All Releases](https://img.shields.io/github/downloads/dustincys/hithesis/total)](https://github.com/dustincys/hithesis/tags)  -->

<a rel="license" href="http://creativecommons.org/licenses/by-nc/4.0/"><img alt="知识共享许可协议" style="border-width:0" src="https://i.creativecommons.org/l/by-nc/4.0/88x31.png" /></a><br />本作品采用<a rel="license" href="http://creativecommons.org/licenses/by-nc/4.0/">知识共享署名-非商业性使用 4.0 国际许可协议</a>进行许可。

## What's hithesis?

hithesis is a LaTeX thesis template package for Harbin Institute of Technology (all 3 campuses) supporting bachelor, master, doctor dissertations, postdoc report, thesis proposal and midterm report, *both Chinese and English version*.

Files/Codes in hithesis may be distributed and/or modified under the conditions of the LaTeX Project Public License, either version 1.3a of this license or (at your option) any later version. The latest version of this license is in:

[http://www.latex-project.org/lppl.txt](http://www.latex-project.org/lppl.txt)

and version 1.3a or later is part of all distributions of LaTeX version 2004/10/01 or later.

Files/Codes in hithesis also under the protection of license of [Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)](http://creativecommons.org/licenses/by-nc/4.0/).

## hithesis是什么？

一个简单易用的哈尔滨工业大学学位论文LaTeX模板，现包括一校三区本科、硕士、博士开题、中期和毕业论文，包括博后出站报告和英文毕业论文格式。
hithesis 已收录在[CTAN](https://ctan.org/pkg/hithesis)中，用户安装TeXLive将自带窝工模板。

## hithesis版本更新说明

~~版本号：vX.Y.Z 中，X表示重大不兼容改进，Y表示功能改进，Z表示非功能的bug补丁。~~
由于 `\changes` 命令的排序方便，现将版本号的表示法更新，vX.Y.Z 形式的最后一版为 v3.0.22，接下来改为 v3.1a。

版本号：vX.YZ 中，X 表示重大的不兼容改进，Y 表示功能改进，Z 表示非功能的 bug 补丁。其中 X, Y 为数字，Z 为小写字母。

## 窝工规范以及模板支持

### 窝工规范

校区|学位|撰写规范|Word排版范例|更新日期
-|-|-|-|-
深圳|本科毕业|-|[关于做好2022届本科生毕业设计（论文） 答辩工作的通知](https://www.hitsz.edu.cn/article/view/id-132766.html)
深圳|硕士/英文版硕士暂行规定|[哈工大（深圳）学术规范及硕士学位论文撰写文件包（2020年版）](http://due.hitsz.edu.cn/info/1211/1859.htm)|同左|2020-10-23
深圳|硕士中期|-|[硕士学位论文中期报告模板](http://due.hitsz.edu.cn/info/1210/1828.htm)
深圳|博士开题|-|[博士学位开题报告模板](http://due.hitsz.edu.cn/info/1252/1865.htm)|2018-07-31
深圳|博士中期|-|[博士学位论文中期检查报告](http://due.hitsz.edu.cn/info/1253/1860.htm)|2018-07-31
深圳|博士毕业|[哈尔滨工业大学研究生学位论文撰写规范（2011版）](http://due.hitsz.edu.cn/info/1243/1776.htm)|[哈尔滨工业大学研究生学位论文书写范例（2011版）](http://due.hitsz.edu.cn/info/1243/1777.htm)|2018-07-31
深圳|英文版博士毕业|[Thesis-Tmplt(英文论文撰写规范)](http://due.hitsz.edu.cn/info/1243/1775.htm)|同左|2018-07-31
威海|本科所有|[本科毕业论文撰写规范和相关资料](http://jwc.hitwh.edu.cn/bysj/list.htm)|同左|2021-11-29
威海|硕士|[研究生学位论文撰写规范](http://yjsc.hitwh.edu.cn/2012/1217/c981a37691/page.htm)|[研究生学位论文书写范例](http://yjsc.hitwh.edu.cn/2012/1217/c981a37689/page.htm)|2012-12-17
威海|硕士|[硕士学位论文撰写规范自查表2011版](http://yjsc.hitwh.edu.cn/2015/1230/c981a37718/page.htm)|同左|2015-12-30
哈尔滨|本科所有|[毕业论文撰写规范](http://jwc.hit.edu.cn/2014/0504/c4305a116176/page.htm)|[所有word范例](http://jwc.hit.edu.cn/2566/list.htm)|2014-05-04
哈尔滨|硕士开题中期|-|[所有word范例](http://hitgs.hit.edu.cn/2015/1210/c3359a123058/page.htm)|2015-12-10
哈尔滨|博士开题中期|-|[所有word范例](http://hitgs.hit.edu.cn/2015/1210/c3416a123048/page.htm)|2015-12-10
哈尔滨|硕博毕业论文所有（含有部分英文版说明）|[研究生学位论文书写范例（理工类）](http://hitgs.hit.edu.cn/2021/0429/c3425a253485/page.htm)[研究生学位论文书写范例（人文社科类）](http://hitgs.hit.edu.cn/2021/0429/c3425a253486/page.htm)|[研究生学位论文写作指南（理工类）](http://hitgs.hit.edu.cn/2021/0429/c3425a253487/page.htm)[研究生学位论文写作指南（人文社科类）](http://hitgs.hit.edu.cn/2021/0429/c3425a253488/page.htm)|2021-04-29
哈尔滨|博后|-|[出站报告以及封皮](http://rsc.hit.edu.cn/2015/1209/c10906a212031/page.htm)|2015-12-09

### 歧义说明

- 规范自身歧义之处：[版芯歧义](http://yanshuo.name/cn/2017/06/hithesisregulation/)和[本科生行距歧义](http://yanshuo.name/cn/2017/06/hithesissiyuan/)。

- 规范与Word模板的歧义：
  - 在[规范](http://hitgs.hit.edu.cn/aa/fd/c3425a109309/page.htm)中规定和[研究生word排版范例](http://hitgs.hit.edu.cn/ab/1f/c3425a109343/page.htm)的中文目录中出现的“ABSTRACT”和“Abstract”的写法歧义（规格严格功夫到家！！！）。
  - [《哈尔滨工业大学本科生毕业论文撰写规范》](http://jwc.hit.edu.cn/2014/0504/c4305a116176/page.htm)与[本科生论文word排版范例](http://jwc.hit.edu.cn/2566/list.htm)中章节标题是否加粗有歧义
  - 本科生论文官方模板的页眉页码格式混乱，有的有页码横线有的没有，有的有页眉有的没有。
  - 规范规定一行33个字，Word模板34个字。

- Word模板自身歧义：
  - Contradictory font size of section title in English version of Word template

### hithesis 支持

- [x] 哈尔滨校区本科毕业设计
- [x] 哈尔滨校区硕士毕业论文
- [x] 哈尔滨校区博士毕业论文
- [x] 哈尔滨校区本科毕业设计开题
- [x] 哈尔滨校区本科毕业设计中期
- [x] 哈尔滨校区硕士毕业设计开题
- [x] 哈尔滨校区硕士毕业设计中期
- [x] 哈尔滨校区博士毕业设计开题
- [x] 哈尔滨校区博士毕业设计中期
- [x] 哈尔滨校区博后出站报告
- [x] 威海校区本科毕业设计
- [x] 威海校区硕士毕业论文
- [x] 威海校区博士毕业论文
- [x] 威海校区本科毕业设计开题
- [x] 威海校区本科毕业设计中期
- [x] 威海校区硕士毕业设计开题
- [x] 威海校区硕士毕业设计中期
- [x] 威海校区博士毕业设计开题
- [x] 威海校区博士毕业设计中期
- [x] 威海校区博后出站报告
- [x] 深圳校区硕士毕业论文
- [x] 深圳校区本科毕业设计
- [x] 深圳校区博士毕业论文
- [x] 深圳校区本科毕业设计开题
- [x] 深圳校区本科毕业设计中期
- [x] 深圳校区硕士毕业设计开题
- [x] 深圳校区硕士毕业设计中期
- [x] 深圳校区博士毕业设计开题
- [x] 深圳校区博士毕业设计中期
- [x] 深圳校区博后出站报告
- [x] English version of thesis

## 模板特点

### 呆萌的操作，傲娇的效果

- 极限程度实现了[《哈尔滨工业大学研究生学位论文撰写规范》](http://hitgs.hit.edu.cn/aa/fd/c3425a109309/page.htm)、[《哈尔滨工业大学本科生毕业论文撰写规范》](http://jwc.hit.edu.cn/2014/0504/c4305a116176/page.htm)
- 这是[PlutoThesis](https://github.com/dustincys/PlutoThesis)的终极进化，PlutoThesis废弃不再维护。
- 更傻更简单的选项，例如论文主文件，只需要在文档类的括号中填写本硕博选项，字体选项（设置弹性间距或者刚性间距），文科生选项（目录可以设成四级目录），非全日制类型等，轻松设定目标格式。
- 更聪明更简单的自适应格式，例如图题和标题，标题字号在字数超过两行时自动由五号变小五号，实现自适应（硕博规范规定，字数多时用五号）
- 自动化中英文索引（博士规范要求，有需要时候添加）
- 自动化表格和图片目录（英文版）
- 自动化生成术语词汇表（英文版）
- 图书馆提交论文级的电子版
- ……

### 矫正PlutoThesis的不足

- 纠正PlutoThesis页面向下溢出
- 纠正PlutoThesis不符合规范要求的各层次题序及标题不得置于页面的最后两行，改为不得置于最后一行（孤行），从此解决了饱受诟病的空白大的问题。
- 纠正PlutoThesis行间距与标题段前段后距离统统设置为1.6倍行距的问题
- 更强大的版芯设置，满足所有需求
- 补充了PlutoThesis没有的符号表、索引两项
- 字体设置符合CTeX的自动识别系统功能
- 纠正PlutoThesis中图片中一些距离设置
- 添加了符合规范要求的“图注在图题之上的设置”
- 纠正PlutoThesis的双语图、表题中英语的非两端对齐问题
- 添加了PlutoThesis中没有的图题最后一行居中且两端对齐格式
- 添加了所有的图形排版格式
- 纠正了附录中标题错误
- 纠正了博士论文右翻页问题
- 添加扫描替换功能，替换之后、页码目录书签自动设置
- 添加思源宋体设置，再也不用害怕奇怪字打不出来了
- 添加文科生、非全日制同等学力封面格式
- 添加PlutoThesis没有的说明文档
- ……

### 为了窝工的规格严格、功夫到家

- 行间距、段前后距离设置精确到小数后四位， 例如 1bp = 1.00374pt，1mm = 2.84526pt， 按照窝工之要求, 行距在3mm～4mm之间，换算之后为20.50398～23.33863bp，严格符合规范要求，哪怕是显微镜级别
- 规范明确规定，数字间空格要求为汉字宽度的四分之一（形式类似与 12 2345 和 0.123 456 这样多于3位以上的整数或小数）。默认情况下在LaTeX中任何人工输入的空格均不正确（“\:”为4/18汉字宽度，“\;”为5/18汉字宽度，所以PlutoThesis中的数字间宽度错误）。hithesis模板中定义了精准的数字间宽度。
- 重写了一堆重要函数，例如章节标题由原来的`BiChapter{}{}`方式进化为`chapter{}[]`，极大简化，后面方括号中为可选括号，硕本可以不用，用了自动忽略
- 严格符合（满足）两个规范要求，由于规范中有矛盾之处，例如本科生的标题段前距离有两处不一样的规定，刚性行距尽量满足行数（要求约33行）要求。
- 规范中给出了行距区间，为了规格严格，设置了弹性行距
- ……

## 关于模板的命名和其他说明

### 模板的命名

本模板对PlutoThesis中的核心代码进行了彻底深入的修改。
PlutoThesis中没有采用cls，这种文档类的模式，代码与正文内容耦合程度大难以维护，本科模板和硕博模板难以融合。
由于冥王星已经不是太阳系C9之一，所以不继续使用PlutoThesis命名。

hithesis, 既含窝工hit，也是说用的“嗨！”，读作“嗨thesis”。

### 关于模板的下载地址

模板有三个下载地址：

1. github: [https://github.com/hithesis/hithesis](https://github.com/hithesis/hithesis)
2. ~~gitee: [https://gitee.com/dustincys/hithesis](https://gitee.com/dustincys/hithesis)~~
3. CTAN: [https://ctan.org/pkg/hithesis](https://ctan.org/pkg/hithesis)

github和gitee的版本是同步且是最新的模板。
CTAN的版本一般会比较落后，但在每年年底会同步为最新版本。

### 关于hithesis的线上讨论区

- QQ群
  - hithesis讨论区：259959600 （人满）
  - 窝工山hithesis派：851792460。
- 微信公众号

   ![石见石页](https://raw.githubusercontent.com/dustincys/cn/assets/qrcode_for_gh_af6e07ba273e_258.jpg)

### 关于查重

注意：窝工的论文查重可以使用pdf查重！！！！！！！

另外一点注意：查重的pdf一定要确保能够正常复制汉字。有些系统自动识别的汉字字体，
会出现无法正常复制的情况（可能是系统的字体映射出现了误差）。一般需要在主文件的
选项中明确声明使用哪一种fontset。

### 关于LaTeX软件的安装

#### 平台

- 推荐使用开源系统 Linux
- 推荐使用开源编辑器 [Spacemacs](https://www.spacemacs.org/)

#### 中文字体

- 推荐使用LaTeX安装包自带的开源中文字体集[fandol](https://www.ctan.org/pkg/fandol)

#### LaTeX安装包介绍

不推荐安装完整版TeXLive/MiKTeX/MacTeX，因为太费时间。
如果不介意在自己房子里放进一堆小破烂，那么浪费硬盘空间完全不是问题，即使99%的模板八百年都用不到。

所以推荐安装非完整版TeXLive/MiKTeX/MacTex。不完整的安装包有的支持自动安装缺失package，有的不支持，需要手动安装。

LaTeX安装包|是否支持非完整安装|平台|是否支持自动安装Package|最小满足hithesis安装脚本
-|-|-|-|-
TeXLive|是，称为BasicTeX|WIN/Mac/Linux|否|[install-TeXLive_hithesis.sh](https://github.com/dustincys/hithesis/blob/master/.github/workflows/install-TeXLive_hithesis.sh)
MiKTeX|是|WIN/Mac/Linux|是|[install-MiKTeX_hithesis.sh](https://github.com/dustincys/hithesis/blob/master/.github/workflows/install-MiKTeX_hithesis.sh)
MacTeX|否，MacTeX官方推荐BasicTeX|Mac|否|[install BasicTeX on Mac](https://github.com/dustincys/hithesis/blob/mac/.github/workflows/test2.yml)
TinyTeX|自身就是最Mini的安装包|Linux/Mac|否|[install-TinyTeX_hithesis.sh](https://github.com/dustincys/hithesis/blob/master/.github/workflows/install-TinyTeX_hithesis.sh)

强烈推荐安装TinyTeX，只占不到300M左右，如果用开源字体集合fandol不用额外安装字体。

#### docker 镜像 [tinytex-hithesis](https://hub.docker.com/r/dustincys/tinytex-hithesis)

[![Docker Image Version (latest by date)](https://img.shields.io/docker/v/dustincys/tinytex-hithesis?style=plastic)](https://hub.docker.com/r/dustincys/tinytex-hithesis)
[![Docker Image Size (latest by date)](https://img.shields.io/docker/image-size/dustincys/tinytex-hithesis?style=plastic)](https://hub.docker.com/r/dustincys/tinytex-hithesis)

[tinytex-hithesis](https://hub.docker.com/r/dustincys/tinytex-hithesis)构建策略是基于最轻量Alpine Linux（5MB）系统安装最轻量的TinyTeX和最小的hithesis依赖包集合。[还能有比这还要**更快更节省空间更方便部署更良心**的安装和使用hithesis的方法么？](https://5b0988e595225.cdn.sohucs.com/images/20171216/1f6862975513431cbb744c3f6e25c971.gif)

- 第一步，下载[tinytex-hithesis](https://hub.docker.com/r/dustincys/tinytex-hithesis)镜像，

      docker pull dustincys/tinytex-hithesis:latest

- 第二步，在hithesis根目录下执行抽取格式

      docker run --rm -i  -v $(pwd):/home/runner dustincys/tinytex-hithesis:latest latex hithesis.ins

- 第三步，在hithesis毕业论文文件夹hitbook或报告文件夹report下执行以下命令进行编译

      docker run --rm -i  -v $(pwd):/home/runner dustincys/tinytex-hithesis:latest make thesis

      docker run --rm -i  -v $(pwd):/home/runner dustincys/tinytex-hithesis:latest make report

  或者在根目录编译文档

      docker run --rm -i  -v $(pwd):/home/runner dustincys/tinytex-hithesis:latest make doc

  或者直接在hitbook或报告文件夹report下执行

      docker run --rm -i  -v $(pwd):/home/runner dustincys/tinytex-hithesis:latest latexmk

编译过程可以参照下一节模板的编译方法。

使用Docker可以使本地安装不再受平台限制、随时部署，不再受bug、字体、环境变量困扰。诸位上仙、大侠、刀客、头领可以任性地、随意地、抽象地、写实地设置别名，最终完成羽化、飞升。

    alias xelatex='docker run --rm -i  -v $(pwd):/home/runner dustincys/tinytex-hithesis:latest xelatex'
    alias splitindex='docker run --rm -i  -v $(pwd):/home/runner dustincys/tinytex-hithesis:latest splitindex'
    alias bibtex='docker run --rm -i  -v $(pwd):/home/runner dustincys/tinytex-hithesis:latest bibtex'
    alias latexmk='docker run --rm -i  -v $(pwd):/home/runner dustincys/tinytex-hithesis:latest latexmk'
    ...

### 模板的编译方法

1. 生成论文格式文件(第一步要生成 *.cls，*.cfg，*.ist，然后再生成论文)

   - 如果是Linux/Mac执行

         latex hithesis.ins

   - 如果是Windows执行（作者没测试过，如遇问题同上）

         lualatex hithesis.ins

   - 如果喜欢玩 make

         make cls

2. 生成好格式后，下一步进入到示例文件夹中

       examples
       ├── hitart
       │   ├── reportplus  %深圳校区博士中期报告
       │   └── reports     %除去深圳校区博士中期报告的一校三区本硕博开题、中期报告
       └── hitbook
           ├── chinese     %一校三区本硕博毕业论文以及博后出站报告
           └── english     %一校三区本硕博英文版毕业论文

3. 生成论文方式

   - 手动狙击（源文件更改后每次编译逐行命令输入一轮）

     - hitbook/chinese 文件夹中

           xelatex -shell-escape thesis.tex
           bibtex thesis
           xelatex -shell-escape thesis.tex
           xelatex -shell-escape thesis.tex
           splitindex thesis -- -s hithesis.ist  # 自动生成索引
           xelatex -shell-escape thesis.tex

     - hitbook/english 文件夹中

           xelatex -shell-escape thesis.tex
           bibtex thesis
           xelatex -shell-escape thesis.tex
           xelatex -shell-escape thesis.tex

     - hitart/{reports,reportplus}文件夹中

           xelatex -shell-escape report.tex
           bibtex report
           xelatex -shell-escape report.tex
           xelatex -shell-escape report.tex

   - 半自动精确射击（源文件更改后每次编译敲一次）

         make thesis

   - 全自动火力覆盖（只需要输入一次命令，源文件更改后自动识别更改自动编译）

         latexmk

4. 生成文档（没什么用，因为有文档也基本没人看）

   - 手动狙击（逐行命令输入一轮）

         xelatex hithesis.dtx
         makeindex -s gind.ist -o hithesis.ind hithesis.idx
         makeindex -s gglo.ist -o hithesis.gls hithesis.glo
         xelatex hithesis.dtx
         xelatex hithesis.dtx

   - 半自动精确射击（编译敲一次）

         make doc

### 打印版、电子版

注意，一般情况下，博士论文的打印版要求双面打印，本硕单面。
博士论文在双面打印成册时，规范中没有明确规定是否要右翻页（右翻页是每一章的起始位
置位于书的右侧页面），所以会出现DIY（或身不由己DIY）哪一处右翻页。
`openright`选项设置为真时，会将所有章（即所有部分，包括前文和后文）起始设置成右翻页。
如果想DIY（或身不由己DIY）在什么地方右翻页，将这个选项设置为false，然后在目标位
置添加`\cleardoublepage`命令即可。

最后向图书管提交的电子版不是右翻页且要求没有任何空白页，这时只需要设置选项`library=true`
即可，这时候会强制`openright=false`。然后什么都不用做，就会出现如同`Sirius`同学
的这种“书签还没整明白，论文居然已经通过了”的情况。

### 幻灯片

有些强迫症刀客喜欢用Beamer，推荐[progressbar主题](https://github.com/dustincys/progressbar)，
能够使用[pympress](https://github.com/Cimbali/pympress)播放双屏提示。
[progressbar主题](https://github.com/dustincys/progressbar)在幻灯片上边排列毕业论文章节链接，在下边有进度指示条，十分适合展示结构复杂的毕业论文内容。

### 关于hithesis的博客

- [2022-06-19 hithesis的二代目掌门](https://yanshuo.name/cn/2022/06/hithesis/)
- [2022-03-04 hithesis 如何使用 docker](https://yanshuo.name/cn/2022/03/hithesis/)
- [2021-11-16 如何维护hithesis（三）](https://yanshuo.name/cn/2021/11/hithesis3/)
- [2021-11-16 如何维护hithesis（二）](https://yanshuo.name/cn/2021/11/hithesis2/)
- [2021-11-15 如何维护hithesis（一）](https://yanshuo.name/cn/2021/11/hithesis/)
- [2020-05-24 hithesis v3 进化](https://yanshuo.name/cn/2020/05/hithesisv3/)
- [2020-02-09 hithesis的“昨天今天和明天”](https://yanshuo.name/cn/2020/01/hithesis/)
- [2017-08-29 发布到了CTAN](https://yanshuo.name/cn/2017/08/ctan/)
- [2017-06-22 规范的正确打开方式](https://yanshuo.name/cn/2017/06/hithesisregulation/)
- [2017-06-16 为了大唐中兴！](https://yanshuo.name/cn/2017/06/hithesissiyuan/)

### 其他说明

- hithesis的维护和创造基于开源式爱心发电精神，所以千万不要向作者提出无礼请求。
- 作者由于工作繁忙，不再无偿解决一些用户要求（例如前面文档中[已经解决的算法格式各实验室要求不一致](https://github.com/dustincys/PlutoThesis#%E6%B2%A1%E6%9C%89%E6%98%8E%E7%A1%AE%E8%A6%81%E6%B1%82%E7%9A%84%E6%A0%BC%E5%BC%8F)问题）。
- 本模板以PlutoThesis为核心基础，参考了CTAN中清华大学薛瑞尼所开发的thuthesis以及其分支重庆大学等毕业论文模板的代码开发而来
- 学校教务处和研究生院提供了规范和[研究生word模板](http://hitgs.hit.edu.cn/ab/1f/c3425a109343/page.htm)以及[本科生word模板](http://jwc.hit.edu.cn/2566/list.htm)，此模板仅为规范的参考实现，不保证格式审查老师不提意见。任何由于使用本模板而引起的论文格式审查问题均与本模板作者无关

### Apply to sponsor

We have spent a lot time and long been involved in developing/maintaining
this open source project.
I'd be humbled and grateful if you could financially support hithesis.

Contributer | WeChat | Alipay
:-:|:-:|:-:
[@syvshc](https://github.com/syvshc)|![szh_wechat](https://raw.githubusercontent.com/hithesis/hithesis/images/szh_wechat.jpg)|![szh_alipay](https://raw.githubusercontent.com/hithesis/hithesis/images/szh_alipay.jpg)
[@dustincys](https://github.com/dustincys)|![cys_wechat](https://raw.githubusercontent.com/dustincys/hifvwm/screenshots/wechat.jpg)|![sys_alipay](http://wx3.sinaimg.cn/large/61dccbaaly1fizali9tafj20k00ucgos.jpg)

Or Zelle quick pay: yanshuoc@gmail.com

### Sponsor List

Please contact me if I missed to add any sponsor. Thank you so much.

|       Time | Name      | Comments |
|------------|-----------|----------|
| 2020-05-06 | Li Liming |  |
| 2020-06-16 | 航明 |  |
| 2020-06-28 | *鑫 |  |
| 2020-07-20 | CR | Wechat |
| 2020-08-13 | d*g |  |
| 2020-09-11 | **扬 |  |
| 2020-11-03 | **宝 |  |
| 2020-11-05 | **庭 |  |
| 2021-01-04 | **杰 |  |
| 2021-02-27 | *晰 |  |
| 2021-04-29 | *振兴 | Alipay |
| 2021-04-21 | *作 |  |
| 2021-05-06 | *文陶 | Zelle quick pay |
| 2021-05-13 | *涵 |  |
| 2021-05-13 | 慕* |  |
| 2021-05-28 | Y*a |  |
| 2021-06-19 | *淞 |  |
| 2021-10-18 | q*q |  |
| 2021-11-21 | **刚 | Alipay |
