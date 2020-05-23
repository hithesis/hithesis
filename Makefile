# Makefile for hithesis document

METHOD = xelatex
# Set opts for latexmk if you use it
LATEXMKOPTS = -xelatex
# Basename of thesis

PACKAGE=hithesis
SOURCES=$(PACKAGE).ins $(PACKAGE).dtx

CLSFILES=dtx-style.sty

# make deletion work on Windows
ifdef SystemRoot
	RM = del /Q
	OPEN = start
else
	RM = rm -f
	OPEN = open
endif

.PHONY: all clean distclean dist doc viewdoc cls check

all: doc

cls: $(CLSFILES)

$(CLSFILES): $(SOURCES)
	latex $(PACKAGE).ins

viewdoc: doc
	$(OPEN) $(PACKAGE).pdf

doc: $(PACKAGE).pdf

ifeq ($(METHOD),latexmk)

$(PACKAGE).pdf: $(CLSFILES)
	$(METHOD) $(LATEXMKOPTS) $(PACKAGE).dtx

else ifeq ($(METHOD),xelatex)

$(PACKAGE).pdf: $(CLSFILES)
	$(METHOD) $(PACKAGE).dtx
	makeindex -s gind.ist -o $(PACKAGE).ind $(PACKAGE).idx
	makeindex -s gglo.ist -o $(PACKAGE).gls $(PACKAGE).glo
	$(METHOD) $(PACKAGE).dtx
	$(METHOD) $(PACKAGE).dtx

else
$(error Unknown METHOD: $(METHOD))

endif

clean:
	latexmk -c $(PACKAGE).dtx
	-@$(RM) *~ *.idx *.ind *.ilg *.thm *.toe *.bbl

cleanall: clean
	-@$(RM) $(PACKAGE).pdf

distclean: cleanall
	-@$(RM) $(CLSFILES)
	-@$(RM) *.cls *.cfg *.ist *.bst *.sty *.eps
