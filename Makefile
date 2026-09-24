# Makefile for hithesis

# 手册用哪个引擎编。模板本身认 xelatex 与 lualatex，见手册的“用哪个引擎”；
# 2026-09-15 起默认 lualatex（主线引擎，断行层只在它上面有）。换引擎两行一起改。
METHOD = lualatex
LATEXMKOPTS = -lualatex

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

.PHONY: all cls docxlike-sync docxlike-check lineends lineends-self lineends-verb lineends-typst pages-doctor pages-bachelor pages lineends-self-baseline compat-regression manual viewmanual doc viewdoc dist auxclean clean distclean distribute changes changes-check changes-fix punct punct-fix doclint constlint constcheck apilint inscheck productcheck mapcheck mapfix refscheck depscheck depslist eps2pdf logcheck logcheck-update version-changes \
        manual-baseline manual-check doc-baseline doc-check \
        baseline smoke regression-test tl-packages testclean version version-check version-set

all: manual



cls: $(TARGETS)

# 行末回归：demo 与书写范例逐行比对（先重编 examples/demo/thesis.pdf）
# 旧版面兼容回归：钉死 v3.1e，测 v2-layout 还原不还原得了老版面。
# 名单与做法见 tests/compat/README.txt。
compat-regression:
	bash scripts/compat-regression.sh

# 行末距离：断行交给 TeX，与 Word 不会归零；--max-diff 是棘轮上限，
# 只保证不变坏，改进之后把这个数调低。
#
# 必须先重编 demo。这个目标从前直接读 examples/demo 的 PDF，那个文件是
# 上一次谁编过就是谁的，改了 cls 不重编就量的是陈货——2026/08/25 实测：
# 报了好几轮的“行差 84”量的是两天前的 PDF，当天新鲜构建其实是 88。
#
# 字体集钉死 windows。基线来自范例的 Word 导出，那份 PDF 里嵌的是
# TimesNewRomanPSMT 加 SimSun；我们这边 fontset=windows 嵌的是同样两个，
# 同字体对同字体量才有意义（fandol 那档是 TeXGyreTermes 加 FandolSong，
# 实测行差 80，windows 是 79）。
#
# 代价是这个目标要机器上装了 Office 字体才能跑。lineends 不进 CI（CI 只跑
# compat-regression），是本机开发用的量具，可以这么钉。
#
# 2026/09/15 起主线是 lualatex：断行由 src/docxlike/docxlike-linebreak.dtx 的 Lua 照 Word
# 的贪心算法做，行差从 78 降到 61。基线是本科范例的 docx 转出来的 PDF，那份 docx
# 转换时升成了 Word 现行版式 15，而类默认按学校 doc 原件的版式 11 排，所以这里把
# 模式钉到 15 再比。剩下的 61 是七处平局与语料伪差各自往后串出来的行。
lineends:
	cd examples/demo && TEXINPUTS="$(CURDIR):" latexmk -lualatex -g \
	  -interaction=nonstopmode \
	  -usepretex='\PassOptionsToClass{fontset=windows}{hithesis}\AddToHook{class/hithesis/after}{\hitsetup{layout={compatibility-mode=word-2013}}}' final.tex \
	  > /dev/null
	python3 scripts/check-line-ends.py --pdf examples/demo/final.pdf --max-diff 21

# 三个目标都带 -g 强制重编：latexmk 不知道 -usepretex 变了，lineends（钉 15）与
# lineends-self（默认 11）接连跑时，第二个会拿第一个的 PDF 去比，满屏假差异。
#
# 自比对：拿 demo 全文（256 段 671 行）与 tests/lineends-demo.tsv 逐行比，钉住 Lua
# 断行层的现状，改动之后看见的差异都得是有意的。上面的 lineends 只比规范那一章
# 与 Word 的差距，这一条比全文与自己的差距。默认兼容模式（11）、fontset=windows。
lineends-self:
	cd examples/demo && TEXINPUTS="$(CURDIR):" latexmk -lualatex -g \
	  -interaction=nonstopmode \
	  -usepretex='\PassOptionsToClass{fontset=windows}{hithesis}' final.tex \
	  > /dev/null
	python3 scripts/check-line-ends.py --pdf examples/demo/final.pdf --fixture tests/lineends-demo.tsv

# 行内代码与 Word 对拍：三段带 \verb 的文字照 Word 探针 docx 逐字抄（tests/sample/verb/），
# 靶子是 Mac Word 导出的 PDF 抽成的 tests/lineends-verb.tsv。行文本与行末坐标都要对上，棘轮 0
lineends-verb:
	cd tests/sample/verb && TEXINPUTS="$(CURDIR):" lualatex -interaction=nonstopmode main.tex > /dev/null
	python3 scripts/check-line-ends.py --pdf tests/sample/verb/main.pdf --fixture tests/lineends-verb.tsv

# 排版引擎 docxlike 的正本在独立仓库 latex-docxlike（默认与本仓库并列），src/docxlike/ 是
# 那边 dtx 的副本。改动在那边做、提交，再跑 make docxlike-sync 拷过来验收；
# make docxlike-check 看两边是否一致。那个仓库不在 CI 里，这两条只在本机用。
DOCXLIKE_DIR ?= ../latex-docxlike
DOCXLIKE_DTX = docxlike.dtx docxlike-page.dtx docxlike-metrics.dtx docxlike-format.dtx docxlike-linebreak.dtx docxlike-headfoot.dtx docxlike-numbering.dtx docxlike-heading.dtx docxlike-preset.dtx

docxlike-sync:
	@test -d $(DOCXLIKE_DIR) || { echo "找不到 $(DOCXLIKE_DIR)，用 DOCXLIKE_DIR=路径 指定"; exit 2; }
	@for f in $(DOCXLIKE_DTX); do cp $(DOCXLIKE_DIR)/$$f src/docxlike/$$f || exit 1; done
	@echo "已从 $(DOCXLIKE_DIR) 拷入 $(words $(DOCXLIKE_DTX)) 个 dtx，那边的提交是 $$(git -C $(DOCXLIKE_DIR) rev-parse --short HEAD)"

docxlike-check:
	@test -d $(DOCXLIKE_DIR) || { echo "找不到 $(DOCXLIKE_DIR)，用 DOCXLIKE_DIR=路径 指定"; exit 2; }
	@bad=; for f in $(DOCXLIKE_DTX); do cmp -s $(DOCXLIKE_DIR)/$$f src/docxlike/$$f || { echo "src/docxlike/$$f 与 $(DOCXLIKE_DIR)/$$f 不一致"; bad=1; }; done; \
	  test -z "$$bad" && echo "src/docxlike/ 与 $(DOCXLIKE_DIR) 一致" || exit 1

# 与 typst-with-msword-linebreaks 对拍：同一批段落（tests/typst-corpus.txt）两边各排一遍，
# 逐行比行末。docxlike.lua 是照那个 fork 抄的，Word 只能量翻转点，两个实现之间
# 能逐行比。棘轮只数文本差异：两档各 6 处，全是 URL 段（那边有紧急断点）。要本机有
# 那个 fork 的二进制（TYPST 环境变量或默认路径），不进 CI
lineends-typst:
	python3 scripts/typst-compare.py --compat 15 --max-diff 6
	python3 scripts/typst-compare.py --compat 11 --max-diff 6

# 逐页对拍：博士范例的整本复刻件（tests/sample/doctor）与范例修正版的 Word 导出逐行比基线，
# 棘轮是配上且 |Δy| ≤ 0.5bp 的行数。靶子来路见 tests/pages-doctor.tsv 头注释
pages-doctor:
	cd tests/sample/doctor && TEXINPUTS="$(CURDIR):" BSTINPUTS="$(CURDIR):" latexmk main.tex > /dev/null
	python3 scripts/check-pages.py --pdf tests/sample/doctor/main.pdf --fixture tests/pages-doctor.tsv --min-ok 233

# 本科那份同理：对拍件 tests/sample/bachelor 引博士那份的正文，靶子是模式 15 的本科范例修正版。
# 2026-09-21 靶子重制（空段按正文格式、表后头一段段前一行空段也算、章前分节符、页码起点删）
# 后两个数从 194/127 变成 174/106，2026-09-22 换页判据改成 Word 的“盒底不越版心底”
# （Lua 断行档 \maxdepth 归零、一栏照满版心）后回到 192/120
pages-bachelor:
	cd tests/sample/bachelor && TEXINPUTS="$(CURDIR):" BSTINPUTS="$(CURDIR):" latexmk main.tex > /dev/null
	python3 scripts/check-pages.py --pdf tests/sample/bachelor/main.pdf --fixture tests/pages-bachelor.tsv --min-ok 146

pages: pages-doctor pages-bachelor

# 重制自比对基线：先确认当前构建的差异都是有意的
lineends-self-baseline:
	cd examples/demo && TEXINPUTS="$(CURDIR):" latexmk -lualatex -g \
	  -interaction=nonstopmode \
	  -usepretex='\PassOptionsToClass{fontset=windows}{hithesis}' final.tex \
	  > /dev/null
	{ echo '# 行末基线，由 scripts/check-line-ends.py --gen 生成'; \
	  echo '# 来源：examples/demo/final.pdf，lualatex，fontset=windows，兼容模式默认（Word 2003）'; \
	  echo '# 用途：新版面轨的自比对，钉住 Lua 断行层的现状；改断行规则后确认差异都是有意的，再用 make lineends-self-baseline 重制'; \
	  python3 scripts/check-line-ends.py --gen examples/demo/final.pdf | tail -n +3; } > tests/lineends-demo.tsv

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
	TEXINPUTS=src:src/engine:src/docxlike:src/config:src/flow:src/pages:src/assets:src/manual: xetex -interaction=nonstopmode src/$(PACKAGE).dtx
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

manual: $(PACKAGE).pdf

viewmanual: manual
	$(OPEN) $(PACKAGE).pdf

# 手册的源文件在 v3.2a 从 src/doc/hit-doc.dtx 改名 src/manual/hit-manual.dtx，
# 目标名跟着改成 manual。旧名留着当别名，先提示再转发，兼容期到 v4.1。
# README 里给用户的 docker 用法示例写的是旧名，直接删会让那条命令不通。
DEPRECATED_TARGET = @printf '\033[33m[hithesis]\033[0m make %s 已改名 make %s，旧名将在 v4 中移除。\n'

doc:
	$(DEPRECATED_TARGET) doc manual
	@$(MAKE) --no-print-directory manual

viewdoc:
	$(DEPRECATED_TARGET) viewdoc viewmanual
	@$(MAKE) --no-print-directory viewmanual

ifeq ($(METHOD),latexmk)

$(PACKAGE).pdf: $(TARGETS)
	TEXINPUTS=src:src/engine:src/docxlike:src/config:src/flow:src/pages:src/assets:src/manual: $(METHOD) $(LATEXMKOPTS) src/$(PACKAGE).dtx

else ifneq ($(filter $(METHOD),xelatex lualatex),)

# nonstopmode：手册里写错宏名之类的错误会让 xelatex 停在交互提示上等输入，
# 无人看管时会一直挂着。cls 目标早就加了，manual 漏了。
#
# 索引用 upmendex 不用 makeindex：索引里有中文条目（示例文件名），makeindex 拿
# 首字节当分组标题，写出来的 .ind 不是合法 UTF-8，lualatex 读到直接报
# “String contains an invalid utf-8 sequence”（xelatex 只是吞掉）。upmendex 认
# Unicode，gind.ist 照用。修改记录那份没有中文键，仍用 makeindex。
#
# 头一句之前先删 .gls 与 .ind：第一次 xelatex 会把它们读进来，而重建它们的
# makeindex 排在后面，于是上一轮的陈旧内容会进这一轮的第一遍。改了 \changes
# 条目之后这一点会直接炸——旧 .gls 里那条记录还带着改之前的花括号，报
# “Extra }”，而源码本身是好的。踩过两次。
$(PACKAGE).pdf: $(TARGETS)
	-$(RM) $(PACKAGE).gls $(PACKAGE).glo $(PACKAGE).ind $(PACKAGE).idx
	TEXINPUTS=src:src/engine:src/docxlike:src/config:src/flow:src/pages:src/assets:src/manual: $(METHOD) -interaction=nonstopmode src/$(PACKAGE).dtx
	upmendex -s gind.ist -o $(PACKAGE).ind $(PACKAGE).idx
	makeindex -s gglo.ist -o $(PACKAGE).gls $(PACKAGE).glo
	TEXINPUTS=src:src/engine:src/docxlike:src/config:src/flow:src/pages:src/assets:src/manual: $(METHOD) -interaction=nonstopmode src/$(PACKAGE).dtx
	TEXINPUTS=src:src/engine:src/docxlike:src/config:src/flow:src/pages:src/assets:src/manual: $(METHOD) -interaction=nonstopmode src/$(PACKAGE).dtx

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

# 改动前存一份手册基线，改完用 manual-check 比
manual-baseline:
	bash tools/doc-snapshot.sh save

manual-check:
	bash tools/doc-snapshot.sh check

doc-baseline:
	$(DEPRECATED_TARGET) doc-baseline manual-baseline
	@$(MAKE) --no-print-directory manual-baseline

doc-check:
	$(DEPRECATED_TARGET) doc-check manual-check
	@$(MAKE) --no-print-directory manual-check

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
	-$(MAKE) -C examples/demo cleanall

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

# dtx 注释里的文档宏检查。写错宏名不影响 cls 生成，只有 make manual 会报，
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

# 六份图像转成 PDF 提交进仓库。XeLaTeX 不认 EPS，是把文件丢给 xdvipdfmx 调
# ghostscript 转，也就是每个用户都得装 gs 才编得出封面。事先转好随包发，
# gs 就只有维护者跑这条时要。
#
# EPS 留在 hit-eps.dtx 里当可读、可 diff 的源；改图动那边，再跑一次这个。
# 哈希记进 tools/eps.sha256，make productcheck 靠它发现“改了 EPS 忘了重转”。
EPSSOURCES = $(shell python3 scripts/products.py --eps)

# 三个 gs 选项是为了可复现：不加的话 ghostscript 会把当前时间写进 PDF 的
# XMP 元数据、再塞一个随机 /ID，每跑一次都产出新字节，assets/ 平白多一堆 diff。
# SOURCE_DATE_EPOCH 在这条路上不管用，epstopdf 只是转调 gs，那个环境变量到不了。
eps2pdf: cls
	@mkdir -p assets
	@for f in $(EPSSOURCES); do \
	  epstopdf --gsopt=-dOmitInfoDate=true --gsopt=-dOmitID=true \
	           --gsopt=-dOmitXMP=true \
	           --outfile=assets/$${f%.eps}.pdf $$f || exit 1; \
	done
	@shasum -a 256 $(EPSSOURCES) > tools/eps.sha256
	@echo "assets/ 里 $(words $(EPSSOURCES)) 份 PDF 已更新，哈希记进 tools/eps.sha256"

# 两个类骨架开头的装配表与 install 守卫比对。装配表是给开发者用的路标：
# 想知道“章节标题在哪处理”，看 src/hithesis.dtx 开头那张装配表就够。
# 它是副本，会陈旧，所以机器盯着。
mapcheck:
	@python3 scripts/check-map.py

# install 守卫改完跑这个，两张装配表按它重新生成
mapfix:
	@python3 scripts/check-map.py --fix

# dtx 注释里的 \file{src/...} 路标指向真实文件。文件改名合并之后这些引用不会
# 自动跟着走，也不会报错——它只是注释，所以机器盯着。
refscheck:
	@python3 scripts/check-dtx-refs.py

# 产物清单交叉校验：install 守卫、tools/distfiles.txt、build.lua 的 installfiles、
# 安装横幅，四份两两对上。加一个产物只改 install 守卫，剩下三份漏了这里会说。
productcheck:
	@python3 scripts/products.py --check

# 宏包归属：每个 \RequirePackage 都得在 tools/deps-policy.txt 里交代放哪儿、为什么。
# 三条规矩是“类不调的进 sty，多模块调的进 deps，单模块调的自己装”。
depscheck:
	@python3 scripts/check-deps.py

# 按当前代码打印一份策略表骨架，加包时拿它起草
depslist:
	@python3 scripts/check-deps.py --list

# 常量键有没有声明了却没人取用的。要先 make cls
apilint:
	@python3 scripts/check-api.py

constlint:
	@python3 scripts/check-unused-const.py

# 常量取值的构建期检查：声明表、两份 cfg、查表三处对不上时，排版代码取到的是
# 未定义的宏，nonstopmode 下只在页面上留一格空白，编译照样以 0 退出。
constcheck:
	@python3 scripts/check-const.py

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
