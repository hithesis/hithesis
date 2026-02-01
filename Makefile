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
	  line = $$0; \
	  match(line, /\\changes\{([^}]*)\}\{([^}]*)\}\{/, a); \
	  if (a[1] != "") { \
	    ver = a[1]; \
	    date = a[2]; \
	    gsub(/^v/, "", ver); \
	    sub(/.*\\changes\{[^}]*\}\{[^}]*\}\{/, "", line); \
	    depth = 1; txt = ""; \
	    for (i = 1; i <= length(line); i++) { \
	      c = substr(line, i, 1); \
	      if (c == "{") depth++; \
	      if (c == "}") depth--; \
	      if (depth == 0) break; \
	      txt = txt c; \
	    } \
	    print ver "|" date "|" txt; \
	  } \
	}' $< > $@

$(RELEASE_NOTES): $(CHANGE_RAW)
	@latest=$$(cut -d'|' -f1 $< | sort -V | uniq | tail -n1); \
	echo "## v$$latest" > $@; \
	echo >> $@; \
	awk -F'|' -v v="$$latest" '$$1 == v { \
	  printf "- %s (%s)\n", $$3, $$2 \
	}' $< | sort -k2 | uniq >> $@

changes: $(RELEASE_NOTES)
	@echo "Release notes generated: $(RELEASE_NOTES)"

version-changes: $(CHANGE_RAW)
	@cut -d'|' -f1 $< | sort -V | uniq | tail -n1 | sed 's/^/v/'
