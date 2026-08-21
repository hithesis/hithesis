# Makefile for hithesis dissertation

# Compiling method: latexmk/xelatex
METHOD = xelatex
# Set opts for latexmk if you use it
LATEXMKOPTS = -xelatex
# Basename of thesis
THESISMAIN = main
PACKAGE = hithesis

THESISCONTENTS=$(THESISMAIN).tex thesis/frontmatter/*.tex thesis/mainmatter/*.tex report/*/mainmatter/*.tex thesis/backmatter/*.tex $(FIGURES)
# NOTE: update this to reflect your local file types.
FIGURES=$(wildcard figures/*.eps figures/*.pdf)
BIBFILE=$(wildcard thesis/backmatter/*.bib)
CLSFILES=hit-thesis.cls hit-report.cls $(PACKAGE).cls $(PACKAGE).ist *.bst

# make deletion work on Windows
ifdef SystemRoot
	RM = del /Q
	OPEN = start
else
	RM = rm -f
	OPEN = open
endif

.PHONY: clean cleanall thesis viewthesis

viewthesis: thesis
	$(OPEN) $(THESISMAIN).pdf

thesis: $(THESISMAIN).pdf

# 四种交付物共用这一份 main.tex，写哪一种由第一行 \documentclass 上的 kind
# 决定（见 main.tex 顶上的说明）。所以这里只有一个编译目标；从前那三个
# thesis-en / opening / midterm 找的是同名 .tex，四棵示例树合成一棵之后
# 就没有那些文件了，一直编不出来，删掉。
ifeq ($(METHOD),latexmk)

$(THESISMAIN).pdf: $(CLSFILES)
	$(METHOD) $(LATEXMKOPTS) $(THESISMAIN)

else ifeq ($(METHOD),xelatex)

$(THESISMAIN).idx: $(THESISMAIN).bbl
	$(METHOD) $(THESISMAIN)
	$(METHOD) $(THESISMAIN)

$(THESISMAIN)_china.idx : $(CLSFILES) $(THESISMAIN).bbl $(THESISMAIN).idx
	splitindex $(THESISMAIN) -- -s $(PACKAGE).ist  # 自动生成索引

$(THESISMAIN)_english.ind $(THESISMAIN)_china.ind $(THESISMAIN)_english.idx : $(THESISMAIN)_china.idx

$(THESISMAIN).pdf: $(CLSFILES) $(THESISCONTENTS) $(THESISMAIN)_china.ind $(THESISMAIN)_china.idx $(THESISMAIN)_english.ind $(THESISMAIN)_english.idx $(THESISMAIN).bbl
	$(METHOD) $(THESISMAIN)
	splitindex $(THESISMAIN) -- -s $(PACKAGE).ist  # 自动生成索引
	$(METHOD) $(THESISMAIN)

$(THESISMAIN).bbl: $(BIBFILE)
	$(METHOD) $(THESISMAIN)
	-bibtex $(THESISMAIN)
	$(RM) $(THESISMAIN).pdf

else
$(error Unknown METHOD: $(METHOD))

endif

# 换 kind 编别的交付物时可以自己指定 jobname，这里把常见的几个一并清掉。
JOBS = $(THESISMAIN) thesis-en opening midterm

# 按 jobname 逐个删，不用 *.idx 这种通配：hithesis.ist 是随包发的，
# 通配一扫就把它删了，下次编索引直接报找不到样式文件。
#
# latexmkrc 的 $clean_ext 里带着 pdf，所以 latexmk -c 已经把 main.pdf 删了，
# cleanall 那条是给不走 latexmk 的情形兜底。
JUNKEXT = aux bbl blg glo gls idx ilg ind ist log out thm toc toe fls fdb_latexmk

clean:
	-latexmk -c $(THESISMAIN)
	-latexmk -c thesis-en
	-latexmk -c opening
	-latexmk -c midterm
	-@$(RM) $(foreach j,$(JOBS),$(foreach e,$(JUNKEXT),$(j).$(e)))
	-@$(RM) $(foreach j,$(JOBS),$(j)-china.idx $(j)-china.ilg $(j)-china.ind)
	-@$(RM) $(foreach j,$(JOBS),$(j)-english.idx $(j)-english.ilg $(j)-english.ind)
	-@$(RM) *~
	# 分章的 .aux 落在源码旁边（\include 按给的路径写），latexmk -c 只管当前目录
	-@$(RM) thesis/frontmatter/*.aux thesis/mainmatter/*.aux thesis/backmatter/*.aux
	-@$(RM) report/proposal/frontmatter/*.aux report/proposal/mainmatter/*.aux
	-@$(RM) report/interim/frontmatter/*.aux report/interim/mainmatter/*.aux

cleanall: clean
	-@$(RM) $(foreach j,$(JOBS),$(j).pdf)
