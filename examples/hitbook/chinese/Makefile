# Makefile for hithesis dissertation

# Compiling method: latexmk/xelatex
METHOD = xelatex
# Set opts for latexmk if you use it
LATEXMKOPTS = -xelatex
# Basename of thesis
THESISMAIN = thesis
PACKAGE = hithesis

THESISCONTENTS=$(THESISMAIN).tex front/*.tex body/*.tex back/*.tex $(FIGURES)
# NOTE: update this to reflect your local file types.
FIGURES=$(wildcard figures/*.eps figures/*.pdf)
BIBFILE=*.bib
CLSFILES=$(PACKAGE)book.cls $(PACKAGE)book.cfg $(PACKAGE).ist $(PACKAGE).sty *.bst

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
	-@$(RM) $(THESISMAIN).pdf
