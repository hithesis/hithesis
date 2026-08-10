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
BIBFILE=*.bib
CLSFILES=hit-thesis.cls hit-report.cls $(PACKAGE).cls $(PACKAGE).ist *.bst

# make deletion work on Windows
ifdef SystemRoot
	RM = del /Q
	OPEN = start
else
	RM = rm -f
	OPEN = open
endif

.PHONY: clean cleanall thesis viewthesis thesis-en opening midterm

viewthesis: thesis
	$(OPEN) $(THESISMAIN).pdf

thesis: $(THESISMAIN).pdf

# 这个目录里放着三份交付物：开题、中期、学位论文。元信息在 hitsetup.tex，
# 三份共用；主文件只有第一行的 kind 不同。学位论文要跑 splitindex 做索引，
# 走下面那套规则；其余三份交给 latexmk 就够了。
thesis-en opening midterm:
	latexmk $(LATEXMKOPTS) $@

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

clean:
	latexmk -c $(THESISMAIN)
	-@$(RM) *~ *.idx *.ind *.ilg *.thm *.toe *.bbl

cleanall: clean
	-@$(RM) $(THESISMAIN).pdf thesis-en.pdf opening.pdf midterm.pdf
