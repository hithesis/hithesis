# Makefile for the hithesis demo

# Compiling method: latexmk/xelatex/lualatex
#
# 模板认 xelatex 与 lualatex 两个引擎。默认 lualatex：2026 年 9 月起断行照 Word 的
# 贪心算法在 Lua 里做，只有 lualatex 有这条路，xelatex 编出来的断行是 TeX 自己的。
# 换回 xelatex 两行一起改：METHOD = xelatex，LATEXMKOPTS = -xelatex。
METHOD = lualatex
# Set opts for latexmk if you use it
LATEXMKOPTS = -lualatex
# Basename of the final (degree) document
FINALMAIN = final
# Basename of report（开题与中期）
REPORTMAIN = report
PACKAGE = hithesis

FINALCONTENTS=$(FINALMAIN).tex $(REPORTMAIN).tex info.tex final/frontmatter/*.tex final/mainmatter/*.tex proposal/mainmatter/*.tex interim/mainmatter/*.tex final/backmatter/*.tex $(FIGURES)
# NOTE: update this to reflect your local file types.
FIGURES=$(wildcard figures/*.eps figures/*.pdf)
BIBFILE=$(wildcard final/backmatter/*.bib)
CLSFILES=$(PACKAGE).cls $(PACKAGE).cfg $(PACKAGE).ist *.bst

# make deletion work on Windows
ifdef SystemRoot
	RM = del /Q
	OPEN = start
else
	RM = rm -f
	OPEN = open
endif

.PHONY: clean cleanall clean-generated final viewfinal report viewreport

viewfinal: final
	$(OPEN) $(FINALMAIN).pdf

final: $(FINALMAIN).pdf

viewreport: report
	$(OPEN) $(REPORTMAIN).pdf

report: $(REPORTMAIN).pdf

$(REPORTMAIN).pdf: $(CLSFILES)
	latexmk $(LATEXMKOPTS) $(REPORTMAIN)

# 两份主文件：final.tex 排学位论文（中英文两版由 lang 决定），report.tex 排
# 开题与中期（由 kind 决定）。各自顶上都写了怎么切换。
ifeq ($(METHOD),latexmk)

$(FINALMAIN).pdf: $(CLSFILES)
	$(METHOD) $(LATEXMKOPTS) $(FINALMAIN)

else ifneq ($(filter $(METHOD),xelatex lualatex),)

$(FINALMAIN).idx: $(FINALMAIN).bbl
	$(METHOD) $(FINALMAIN)
	$(METHOD) $(FINALMAIN)

$(FINALMAIN)_china.idx : $(CLSFILES) $(FINALMAIN).bbl $(FINALMAIN).idx
	splitindex $(FINALMAIN) -- -s $(PACKAGE).ist  # 自动生成索引

$(FINALMAIN)_english.ind $(FINALMAIN)_china.ind $(FINALMAIN)_english.idx : $(FINALMAIN)_china.idx

$(FINALMAIN).pdf: $(CLSFILES) $(FINALCONTENTS) $(FINALMAIN)_china.ind $(FINALMAIN)_china.idx $(FINALMAIN)_english.ind $(FINALMAIN)_english.idx $(FINALMAIN).bbl
	$(METHOD) $(FINALMAIN)
	splitindex $(FINALMAIN) -- -s $(PACKAGE).ist  # 自动生成索引
	$(METHOD) $(FINALMAIN)

$(FINALMAIN).bbl: $(BIBFILE)
	$(METHOD) $(FINALMAIN)
	-bibtex $(FINALMAIN)
	-if [ -f $(FINALMAIN)-pub.aux ]; then bibtex $(FINALMAIN)-pub; fi  # 成果页那一份
	$(RM) $(FINALMAIN).pdf

else
$(error Unknown METHOD: $(METHOD))

endif

# 换 kind 编别的交付物时可以自己指定 jobname，这里把常见的几个一并清掉。
JOBS = $(FINALMAIN) thesis-en opening midterm

# 按扩展名通配删，不按 jobname 逐个删。原先 JOBS 只列了四个 jobname
# （thesis、thesis-en、opening、midterm），而手工编别的档（-jobname=h3、ork2
# 这类）留下的产物一个都扫不到，日子久了目录里堆出上百个文件。
#
# ist 不在这张表里：hithesis.ist 是 make cls 生成再拷过来的，名字与
# jobname 无关，通配一扫就把它删了，下次编索引直接报找不到样式文件。
# 它跟 cls/cfg/sty/bst 一起由 clean-generated 那条按名删。
#
# latexmkrc 的 $clean_ext 里带着 pdf，所以 latexmk -c 已经把 thesis.pdf 与 report.pdf 删了，
# cleanall 那条是给不走 latexmk 的情形兜底。
JUNKEXT = aux bbl bcf blg glo gls idx ilg ind log out run.xml synctex.gz \
          thm toc toe fls fdb_latexmk xdv

clean:
	-latexmk -c $(FINALMAIN)
	-latexmk -c thesis-en
	-latexmk -c opening
	-latexmk -c midterm
	-@$(RM) $(foreach e,$(JUNKEXT),*.$(e))
	-@$(RM) *-BSTcontrol.bib *-pub.aux *-pub.bbl *-pub.blg
	-@$(RM) *~
	# 分章的产物落在源码旁边（\include 按给的路径写），latexmk -c 只管当前目录。
	# 按扩展名通配，与上面那条同一套：在子目录里手工编一次（-jobname=v01 这类）
	# 会留下 .log 与 .aux，只删 .aux 的话 .log 会一直堆着。
	-@$(RM) $(foreach d,final proposal interim,\
	          $(foreach sub,frontmatter mainmatter backmatter,\
	            $(foreach e,$(JUNKEXT),$(d)/$(sub)/*.$(e))))
	-@$(RM) $(foreach d,final proposal interim,$(foreach e,$(JUNKEXT),$(d)/*.$(e)))

# make cls 生成、由编译脚本拷进来的那几份，以及 assets/ 里拷过来的图。
# 它们不是这个目录的内容，是别处的产物，按名删不通配。
GENERATED = hithesis.cls hithesis.cfg hithesis.sty hithesis.ist hithesis.bst \
            hithesisbook.cls hithesisart.cls hithesisartplus.cls \
            docxlike.sty docxlike.lua \
            hit-logo.pdf zfb.pdf hit-bachelor-report-bottommark.pdf \
            figures/golfer.pdf

# 已经不再生成、但旧版本拷进来过的那几份。留在这张表里，从旧版升上来的目录
# 才扫得干净；生成物那边删掉一个名字就往这里补一个。
LEGACY = hit-thesis.cfg hit-report.cfg hit-thesis.cls hit-report.cls banshi.sty banshi.lua zhwordlike.sty zhwordlike.lua hit-linebreak.lua

clean-generated:
	-@$(RM) $(GENERATED) $(LEGACY)

cleanall: clean clean-generated
	-@$(RM) *.pdf
