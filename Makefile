# Makefile for hithesis

METHOD = xelatex
LATEXMKOPTS = -xelatex

PACKAGE = hithesis
VERSION = `grep -m 1 -o "v[0-9]\+\.[0-9]\+\.[0-9]\+" src/$(PACKAGE).dtx`

SOURCES = $(PACKAGE).ins src/$(PACKAGE).dtx
TARGETS = dtx-style.sty

RELEASE_NOTES = RELEASE_NOTES.md

ifdef SystemRoot
	RM = del /Q
	OPEN = start
else
	RM = rm -f
	OPEN = open
endif

NPROC ?= 8

.PHONY: all cls doc viewdoc dist auxclean clean distclean changes changes-check changes-fix punct punct-fix version-changes \
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
	$(METHOD) $(LATEXMKOPTS) src/$(PACKAGE).dtx

else ifeq ($(METHOD),xelatex)

$(PACKAGE).pdf: $(TARGETS)
	$(METHOD) src/$(PACKAGE).dtx
	makeindex -s gind.ist -o $(PACKAGE).ind $(PACKAGE).idx
	makeindex -s gglo.ist -o $(PACKAGE).gls $(PACKAGE).glo
	$(METHOD) src/$(PACKAGE).dtx
	$(METHOD) src/$(PACKAGE).dtx

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
	latexmk -c src/$(PACKAGE).dtx
	-$(RM) *.glo *.gls *.hd

clean: auxclean
	-$(RM) *.bst *.ist *.cls *.cfg *.sty
	-$(RM) *.eps
	-$(RM) $(PACKAGE).pdf
	-$(RM) $(RELEASE_NOTES)

distclean: clean
	-$(RM) $(PACKAGE)-$(VERSION).zip

# -------------------------------
# 从 .dtx 的 \changes 生成 release notes
#
# 以前这里用 awk，但依赖 gawk 的三参数 match()：macOS 自带 awk 不认，会静默产出
# 空文件；Windows 没有 awk。改用 python3（工具链本来就依赖它）。
# -------------------------------

changes:
	@python3 scripts/changes.py

changes-check:
	@python3 scripts/changes.py --check

changes-fix:
	@python3 scripts/changes.py --fix

# 中文标点检查，默认只报告；确认后 make punct-fix 写回
punct:
	@python3 scripts/fix-punct.py

punct-fix:
	@python3 scripts/fix-punct.py --fix

version-changes:
	@python3 scripts/changes.py --version
