# Makefile for hithesis

METHOD = xelatex
LATEXMKOPTS = -xelatex

PACKAGE = hithesis
VERSION = `grep -m 1 -o "v[0-9]\+\.[0-9]\+\.[0-9]\+" src/$(PACKAGE).dtx`

# 所有 dtx 都要列进来。只列 src/hithesis.dtx 的话，改 book/art/bst 等文件
# make 会认为目标是最新的，直接跳过生成，拿旧产物继续跑测试。
SOURCES = $(PACKAGE).ins $(wildcard src/*.dtx)
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

.PHONY: all cls doc viewdoc dist auxclean clean distclean distribute changes changes-check changes-fix punct punct-fix doclint version-changes \
        baseline smoke regression-test tl-packages testclean

all: doc



cls: $(TARGETS)

# nonstopmode：docstrip 出错时直接失败，不要挂在交互提示上等输入
# TEXINPUTS 指到 src/：这样 .ins 与 driver 里写不带目录的文件名即可，
# make（在根目录跑）和 l3build（把源码拍平到 build/unpacked）都能找到。
$(TARGETS): $(SOURCES)
	TEXINPUTS=src: latex -interaction=nonstopmode $(PACKAGE).ins
	$(MAKE) --no-print-directory distribute

# .ins 只生成到根目录，示例目录里的那份由这里分发。
# 这样 docstrip 的输出不依赖调用时的当前目录，l3build 的 unpack 才能直接用。
#
# build.lua 里的 distribute 目标有一份等价实现，给不装 make 的平台用（CI 的
# macOS/Windows 任务走那条）。改动下面的清单时两边都要改。
BOOKFILES = $(PACKAGE)book.cls $(PACKAGE).bst hitszthesis.bst \
            hitlogo.eps bthesistitle.eps shenzhenbthesistitle.eps zfb.eps \
            hrb-bachelor-bottommark.eps
ARTFILES  = $(PACKAGE)art.cls $(PACKAGE).bst hitszthesis.bst \
            hitlogo.eps bthesistitle.eps zfb.eps

distribute:
	@for d in examples/hitbook/chinese examples/hitbook/english; do \
	  cp $(BOOKFILES) $$d/; mkdir -p $$d/figures; cp golfer.eps $$d/figures/; \
	done
	@cp $(PACKAGE).ist examples/hitbook/chinese/
	@cp $(ARTFILES) hrb-bachelor-bottommark.eps examples/hitart/reports/
	@mkdir -p examples/hitart/reports/figures && cp golfer.eps examples/hitart/reports/figures/
	@cp $(PACKAGE)artplus.cls $(PACKAGE).bst hitszthesis.bst \
	    hitlogo.eps bthesistitle.eps zfb.eps examples/hitart/reportplus/
	@mkdir -p examples/hitart/reportplus/figures && cp golfer.eps examples/hitart/reportplus/figures/

doc: $(PACKAGE).pdf

viewdoc: doc
	$(OPEN) $(PACKAGE).pdf

ifeq ($(METHOD),latexmk)

$(PACKAGE).pdf: $(TARGETS)
	TEXINPUTS=src: $(METHOD) $(LATEXMKOPTS) src/$(PACKAGE).dtx

else ifeq ($(METHOD),xelatex)

# nonstopmode：手册里写错宏名之类的错误会让 xelatex 停在交互提示上等输入，
# 无人看管时会一直挂着。cls 目标早就加了，doc 漏了。
$(PACKAGE).pdf: $(TARGETS)
	TEXINPUTS=src: $(METHOD) -interaction=nonstopmode src/$(PACKAGE).dtx
	makeindex -s gind.ist -o $(PACKAGE).ind $(PACKAGE).idx
	makeindex -s gglo.ist -o $(PACKAGE).gls $(PACKAGE).glo
	TEXINPUTS=src: $(METHOD) -interaction=nonstopmode src/$(PACKAGE).dtx
	TEXINPUTS=src: $(METHOD) -interaction=nonstopmode src/$(PACKAGE).dtx

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

# dtx 注释里的文档宏检查。写错宏名不影响 cls 生成，只有 make doc 会报，
# 而那要跑一分多钟；这个几秒钟出结果，提交前先挡一道。
doclint:
	@python3 scripts/check-dtx-doc.py

# 中文标点检查，默认只报告；确认后 make punct-fix 写回
punct:
	@python3 scripts/fix-punct.py

punct-fix:
	@python3 scripts/fix-punct.py --fix

version-changes:
	@python3 scripts/changes.py --version
