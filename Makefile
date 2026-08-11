# Makefile for hithesis

METHOD = xelatex
LATEXMKOPTS = -xelatex

PACKAGE = hithesis
VERSION = `grep -m 1 -o "v[0-9]\+\.[0-9]\+\.[0-9]\+" src/$(PACKAGE).dtx`

# 所有 dtx 都要列进来。只列 src/hithesis.dtx 的话，改 book/art/bst 等文件
# make 会认为目标是最新的，直接跳过生成，拿旧产物继续跑测试。
SOURCES = $(wildcard src/*.dtx) $(wildcard src/*/*.dtx)
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

.PHONY: all cls doc viewdoc dist auxclean clean distclean distribute changes changes-check changes-fix punct punct-fix doclint constlint apilint inscheck productcheck logcheck logcheck-update version-changes \
        baseline smoke regression-test tl-packages testclean version version-check version-set

all: doc



cls: $(TARGETS)

# 解压走自解压的 dtx，不走 .ins：解压规则写在 src/hithesis.dtx 的 install 守卫里，
# hithesis.ins 是它的产物之一（提交进仓库，随 CTAN 包发出去，供拿到源码包的人用）。
#
# 必须用 xetex：docstrip 逐字节搬运，plain tex 会把 dtx 里的中文写成 ^^e5 这种
# 转义，生成的 cls 排出来是乱码。原先跑 latex hithesis.ins 没事，是因为 LaTeX
# 格式已经把高位字节设成可打印。
#
# nonstopmode：docstrip 出错时直接失败，不要挂在交互提示上等输入
# TEXINPUTS 指到 src/：这样 install 守卫里写不带目录的文件名即可，
# make（在根目录跑）和 l3build（把源码拍平到 build/unpacked）都能找到。
$(TARGETS): $(SOURCES)
	TEXINPUTS=src:src/setup:src/utils:src/flow:src/pages: xetex -interaction=nonstopmode src/$(PACKAGE).dtx
	$(MAKE) --no-print-directory distribute

# .ins 只生成到根目录，示例目录里的那份由这里分发。
# 这样 docstrip 的输出不依赖调用时的当前目录，l3build 的 unpack 才能直接用。
#
# 文件清单读 tools/distfiles.txt，build.lua 的 distribute 目标读的是同一份。
# 没让 Makefile 直接转调那边，是因为 l3build 不在 scheme-minimal 里，那样会把
# 它变成 make 的硬依赖。清单与 install 守卫对不对得上由 make productcheck 把关。
DISTFILES = $(shell python3 scripts/products.py --dist)
FIGFILES  = $(shell python3 scripts/products.py --figures)

distribute:
	@cp $(DISTFILES) examples/demo/
	@mkdir -p examples/demo/figures && cp $(FIGFILES) examples/demo/figures/

doc: $(PACKAGE).pdf

viewdoc: doc
	$(OPEN) $(PACKAGE).pdf

ifeq ($(METHOD),latexmk)

$(PACKAGE).pdf: $(TARGETS)
	TEXINPUTS=src:src/setup:src/utils:src/flow:src/pages: $(METHOD) $(LATEXMKOPTS) src/$(PACKAGE).dtx

else ifeq ($(METHOD),xelatex)

# nonstopmode：手册里写错宏名之类的错误会让 xelatex 停在交互提示上等输入，
# 无人看管时会一直挂着。cls 目标早就加了，doc 漏了。
$(PACKAGE).pdf: $(TARGETS)
	TEXINPUTS=src:src/setup:src/utils:src/flow:src/pages: $(METHOD) -interaction=nonstopmode src/$(PACKAGE).dtx
	makeindex -s gind.ist -o $(PACKAGE).ind $(PACKAGE).idx
	makeindex -s gglo.ist -o $(PACKAGE).gls $(PACKAGE).glo
	TEXINPUTS=src:src/setup:src/utils:src/flow:src/pages: $(METHOD) -interaction=nonstopmode src/$(PACKAGE).dtx
	TEXINPUTS=src:src/setup:src/utils:src/flow:src/pages: $(METHOD) -interaction=nonstopmode src/$(PACKAGE).dtx

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

# hithesis.ins 是 src/hithesis.dtx 的 install 守卫的产物，提交进仓库随包发出去。
# CTAN 劝阻生成物的理由是“容易忘记跟着源更新”，这道检查就是防这个：
# 先 make cls 重新生成，再看有没有未提交的改动。
inscheck:
	@$(MAKE) --no-print-directory cls >/dev/null
	@git diff --exit-code -- $(PACKAGE).ins \
	  || { echo "hithesis.ins 与 src/hithesis.dtx 的 install 守卫不同步，把上面的改动提交进去"; exit 1; }
	@echo "hithesis.ins 与源同步"

# 产物清单交叉校验：install 守卫、tools/distfiles.txt、build.lua 的 installfiles、
# 安装横幅，四份两两对上。加一个产物只改 install 守卫，剩下三份漏了这里会说。
productcheck:
	@python3 scripts/products.py --check

# 常量键有没有声明了却没人取用的。要先 make cls
apilint:
	@python3 scripts/check-api.py

constlint:
	@python3 scripts/check-unused-const.py

# 扫编译日志里那几类“编得过但有毛病”。要先把变体编出来（make baseline）
logcheck:
	@python3 scripts/check-logs.py

logcheck-update:
	@python3 scripts/check-logs.py --update

# 中文标点检查，默认只报告；确认后 make punct-fix 写回
punct:
	@python3 scripts/fix-punct.py

# CI 门禁：有可改之处就退出码 1
punct-check:
	@python3 scripts/fix-punct.py --check

punct-fix:
	@python3 scripts/fix-punct.py --fix

version-changes:
	@python3 scripts/changes.py --version

# 版本号散在 ProvidesFile、五条 ProvidesExpl* 与四个示例横幅里，这里一处改全部同步。
# 手册封面读 \fileversion，示例横幅由 \lstinputlisting 贴进手册，改完跑 make doc 跟上。
version:
	@python3 scripts/version.py

version-check:
	@python3 scripts/version.py --check

# 用法：make version-set VERSION=3.2b DATE=2026/08/07（DATE 可省）
version-set:
	@test -n "$(VERSION)" || { echo "用法：make version-set VERSION=3.2b [DATE=YYYY/MM/DD]"; exit 2; }
	@python3 scripts/version.py --set $(VERSION) $(if $(DATE),--date $(DATE))
