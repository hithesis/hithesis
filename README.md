# What's hithesis?

hithesis is a LaTeX thesis template package for Harbin Institute of Technolog
supporting bachelor, master, doctor dissertations. Since the users of this
package are supposed to be Chinese or those understand Chinese, the following of
this file and all other documents are written in Chinese only.

# hithesis是什么？

hithesis, 既含我工hit，也是说用的“嗨！”，读作“嗨thesis”。hithesis 旨在建立一个
简单易用的哈尔滨工业大学学位论文LaTeX模板，包括本科论文、硕士论文、博士论文 。现
在支持本科、硕士、博士论文，对其它格式的支持会陆续加入。


# 文档

请[下载](https://github.com/dustincys/hithesis "下载")模板，生成具体使用说明以
及示例文档：

    模板使用说明 (hithesis.pdf)
    示例文档 (main.pdf)

# 下载

开发版有两个下载地址：

- [oschina 码云](https://git.oschina.net/dustincys/hithesis)
- [github](https://github.com/dustincys/hithesis)



# Make­file的用法

	make [{all|thesis|doc|clean|cleanall|distclean}]

## 目标

- make all 等于 make thesis && make doc；
- make cls 生成模板文件；
- make thesis 生成论文 main.pdf；
- make doc 生成使用说明书 thuthe­sis.pdf；
- make clean 删除示例文件的中间文件（不含 main.pdf）；
- make cleanall 删除示例文件的中间文件和 main.pdf；
- make distclean 删除示例文件和模板的所有中间文件和 PDF。
