# Makefile for hithesis

METHOD = xelatex
# Set opts for latexmk if you use it
LATEXMKOPTS = -xelatex

# Basename of thesis
PACKAGE=hithesis
VERSION=`grep -m 1 -o "v[0-9]\+\.[0-9]\+\.[0-9]\+" $(PACKAGE).dtx`

SOURCES=$(PACKAGE).ins $(PACKAGE).dtx
TARGETS=dtx-style.sty

# make deletion work on Windows
ifdef SystemRoot
	RM = del /Q
	OPEN = start
else
	RM = rm -f
	OPEN = open
endif

.PHONY: all cls doc viewdoc dist auxclean clean distclean

all: doc

cls: $(TARGETS)

$(TARGETS): $(SOURCES)
	latex $(PACKAGE).ins

doc: $(PACKAGE).pdf

viewdoc: doc
	$(OPEN) $(PACKAGE).pdf

ifeq ($(METHOD),latexmk)

$(PACKAGE).pdf: $(TARGETS)
	$(METHOD) $(LATEXMKOPTS) $(PACKAGE).dtx

else ifeq ($(METHOD),xelatex)

$(PACKAGE).pdf: $(TARGETS)
	$(METHOD) $(PACKAGE).dtx
	makeindex -s gind.ist -o $(PACKAGE).ind $(PACKAGE).idx
	makeindex -s gglo.ist -o $(PACKAGE).gls $(PACKAGE).glo
	$(METHOD) $(PACKAGE).dtx
	$(METHOD) $(PACKAGE).dtx

else
$(error Unknown METHOD: $(METHOD))

endif

dist: all
	-$(RM) $(PACKAGE)-$(VERSION).zip
	zip -r $(PACKAGE)-$(VERSION).zip examples/ $(PACKAGE).pdf

auxclean:
	latexmk -c $(PACKAGE).dtx
	-$(RM) *.glo *.gls *.hd

clean: auxclean
	-$(RM) *.bst *.ist *.cls *.cfg *.sty *.eps
	-$(RM) $(PACKAGE).pdf

distclean: clean
	-$(RM) $(PACKAGE)-$(VERSION).zip
