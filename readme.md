# hithesis
# 哈尔滨工业大学LaTeX论文模板

## 模板介绍

- 这是[PlutoThesis](https://github.com/dustincys/PlutoThesis "PlutoThesis")的又蠢又简单的进化
- 极大程度实现了[《哈尔滨工业大学研究生学位论文撰写规范》](http://hitgs.hit.edu.cn/aa/fd/c3425a109309/page.htm)、[《哈尔滨工业大学本科生毕业论文撰写规范》](http://jwc.hit.edu.cn/2566/list.htm)

## 特点

- 呆萌的操作，傲娇的效果
 - 论文主文件只有三个选项，本硕博选项，字体选项（设置弹性间距或者刚性间距），文科生选项（目录可以设成四级目录）
 - 图题，标题字号在字数超过两行时自动由五号变小五号，实现自适应（硕博规范规定，字数多时用五号）
 - 自动化中英文索引（博士规范要求，有需要时候添加）
 - 极大程度自动化

- 矫正PlutoThesis的不足
 - 纠正PlutoThesis页面向下溢出
 - 纠正PlutoThesis不符合规范要求的各层次题序及标题不得置于页面的最后一行（孤行）
 - 纠正PlutoThesis行间距与标题段前段后距离
 - 补充了PlutoThesis没有的符号表、索引两项
 - 字体设置符合CTeX的自动识别系统功能
 - 纠正PlutoThesis中图片中一些距离设置
 - 纠正了附录中标题错误
 - ……

- 为了我工的规格严格、功夫到家
 - 行间距、段前后距离设置精确到小数后四位， 例如 1bp = 1.00374pt，1mm = 2.84526pt， 按照我工之要求, 行距在3mm～4mm之间，换算之后为20.50398～23.33863bp，严格符合规范要求，哪怕是显微镜级别
 - 重写了一个重要函数，例如章节标题由原来的`BiChapter{}{}`方式进化为`chapter{}[]`，少写一个字也节省能量，后面方括号中为可选括号，硕本可以不用，用了自动忽略
 - 严格符合（满足）两个规范要求，由于规范中有矛盾之处，例如本科生的标题段前距离有两处不一样的规定，刚性行距尽量满足行数（要求约33行）要求。
 - 规范中给出了行距区间，为了规格严格，设置了弹性行距
 - ……


## 关于模板的命名和其他说明

本模板对PlutoThesis中的核心代码进行了彻底深入的修改。
PlutoThesis中没有采用cls，这种文档类的模式，代码与正文内容耦合程度大难以维护，导致出现本科模板和硕博模板分家等苦境。
所以不使用PlutoThesis名称命名了（现在冥王星已经不是太阳系星星之一了）。

hithesis, 既含我工hit，也是说用的“嗨！”，读作“嗨thesis”。
为了使hithesis成为标准化CTAN package，需要编写详细的dtx文档，以及使用说明等。

临时的编译说明：

	xelatex main.tex
	bibtex main
	xelatex main.tex
	xelatex main.tex
	splitindex main -- -s hithesis.ist  # 自动生成索引
	xelatex main.tex

由于维护者（就是本书呆）已经高龄不毕业博士，课题繁忙，实在无空余时间再写详细文档以及 无偿解决一些用户要求（例如前面文档中[已经解决的算法格式各实验室要求不一致](https://github.com/dustincys/PlutoThesis#%E6%B2%A1%E6%9C%89%E6%98%8E%E7%A1%AE%E8%A6%81%E6%B1%82%E7%9A%84%E6%A0%BC%E5%BC%8F)问题）。

各位刀客和大侠如用的嗨，要解囊相助，请微信扫码～～

![5](http://wx4.sinaimg.cn/large/61dccbaaly1fge32sbb32j20my0uz3zt.jpg "谢谢")

如果用的非常嗨，

![10](http://wx4.sinaimg.cn/large/61dccbaaly1fge32tuvvsj20my0uzabc.jpg "谢谢")

那个，看在苦X高领博士，还熬夜写代码的份上…… 唉……

![1](http://wx4.sinaimg.cn/large/61dccbaaly1fge32qrvgij20my0uzjso.jpg "谢谢")

其实没关系，为了我工的“规格严格，功夫到家”

- 本模板参考了CTAN中清华大学薛瑞尼所开发的thuthesis以及其分支重庆大学等毕业论文模板的代码
