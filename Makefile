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

NPROC ?= 8

.PHONY: all cls doc viewdoc dist auxclean clean distclean changes version-changes \
        toc toc-update baseline smoke regression-test tl-packages testclean

all: doc

toc:
	python3 dtx-toc.py

toc-update:
	python3 dtx-toc.py write

cls: $(TARGETS)

# nonstopmode：docstrip 出错时直接失败，不要挂在交互提示上等输入
$(TARGETS): $(SOURCES)
	latex -interaction=nonstopmode $(PACKAGE).ins

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

# -------------------------------
# 排版测试，说明见 tests/README.md
# -------------------------------

# 全部变体编一遍，渲染结果存成本地 PNG 基线
baseline:
	NPROC=$(NPROC) bash tools/make-baseline.sh

# 全部变体重编一遍，跟本地基线逐页比
smoke:
	NPROC=$(NPROC) bash tools/smoke.sh

# 跟上一个正式 release 逐页比排版，发版前跑，逐个人工确认
regression-test:
	python3 scripts/regression_test.py --jobs $(NPROC)

# 重新生成 TeX Live 依赖清单的候选内容，要 diff 着合并进 .github/tl_packages
tl-packages:
	NPROC=$(NPROC) bash scripts/gen-tl-packages.sh

# 改动前存一份手册基线，改完用 doc-check 比
doc-baseline:
	bash tools/doc-snapshot.sh save

doc-check:
	bash tools/doc-snapshot.sh check

testclean:
	-rm -rf tests/work tests/current tests/diff tests/doc-current tests/doc-diff

auxclean:
	latexmk -c $(PACKAGE).dtx
	-$(RM) *.glo *.gls *.hd

clean: auxclean
	-$(RM) *.bst *.ist *.cls *.cfg *.sty
	-$(RM) *.eps
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
