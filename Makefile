# Makefile for hithesis

METHOD = xelatex
LATEXMKOPTS = -xelatex

PACKAGE = hithesis
VERSION = `grep -m 1 -o "v[0-9]\+\.[0-9]\+\.[0-9]\+" $(PACKAGE).dtx`

SOURCES = $(PACKAGE).ins $(PACKAGE).dtx
TARGETS = dtx-style.sty

CHANGE_RAW = .changes.raw
RELEASE_NOTES = RELEASE_NOTES.md

ifdef SystemRoot
	RM = del /Q
	OPEN = start
else
	RM = rm -f
	OPEN = open
endif

.PHONY: all cls doc viewdoc dist auxclean clean distclean changes version-changes

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
	-$(RM) *.bst *.ist *.cls *.cfg *.sty
	-$(RM) $(PACKAGE).pdf
	-$(RM) $(CHANGE_RAW) $(RELEASE_NOTES)

distclean: clean
	-$(RM) $(PACKAGE)-$(VERSION).zip

# -------------------------------
# Extract \changes{} from .dtx
# -------------------------------

$(CHANGE_RAW): $(PACKAGE).dtx
	@awk '/\\changes\{/ { \
	  match($$0, /\\changes\{([^}]*)\}\{([^}]*)\}\{([^}]*)\}/, a); \
	  if (a[1] != "") { \
	    gsub(/^v/, "", a[1]); \
	    print a[1] "|" a[2] "|" a[3]; \
	  } \
	}' $< > $@

$(RELEASE_NOTES): $(CHANGE_RAW)
	@latest=$$(cut -d'|' -f1 $< | sort -V | uniq | tail -n1); \
	echo "## v$$latest" > $@; \
	echo >> $@; \
	awk -F'|' -v v="$$latest" '$$1 == v { \
	  printf "- %s (%s)\n", $$3, $$2 \
	}' $< | sort -k2 >> $@

changes: $(RELEASE_NOTES)
	@echo "Release notes generated: $(RELEASE_NOTES)"

version-changes: $(CHANGE_RAW)
	@cut -d'|' -f1 $< | sort -V | uniq | tail -n1 | sed 's/^/v/'
