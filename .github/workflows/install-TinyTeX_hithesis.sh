##!/usr/bin/env sh

#' filename : install-TinyTeX_hithesis.sh
#' Date : 2026-04-13
#' contributor : Yanshuo Chu
#' function: minimum install of TeX package for hithesis

# make sure perl is properly installed (e.g., apt install -y perl)
perl -mFile::Find /dev/null
# then install TinyTeX
wget -qO- "https://tinytex.yihui.org/install-bin-unix.sh" | sh

echo "Finish install TinyTeX, going to install extra dependencies..."

tlmgr option repository https://mirrors.tuna.tsinghua.edu.cn/CTAN/systems/texlive/tlnet
tlmgr update --self --all
tlmgr path add
fmtutil-sys --all

echo "Finish update , install extra packages..."

tlmgr install adobemapping algorithm2e amscls amsfonts amsmath arphic atbegshi atveryend
tlmgr install auxhook babel beamer bibtex bibtex.x86_64-linuxmusl bigfoot bigintcalc bitset
tlmgr install booktabs carlisle ccaption changepage cjk cjkpunct cm cns ctablestack ctex
tlmgr install datatool dehyph dvipdfmx dvipdfmx.x86_64-linuxmusl dvips dvips.x86_64-linuxmusl
tlmgr install ec enumitem environ epstopdf-pkg eso-pic etex etexcmds etoolbox euenc everyhook
tlmgr install everysel everyshi fancyhdr fancyvrb fandol filehook firstaid float fontaxes
tlmgr install fonts-tlwg fontspec footmisc fp framed garuda-c90 gbt7714 geometry
tlmgr install gettitlestring glossaries glossaries-extra glossaries.x86_64-linuxmusl glyphlist
tlmgr install graphics graphics-cfg graphics-def grfext grffile helvetic hycolor hypdoc
tlmgr install hyperref hyph-utf8 hyphen-base hyphen-german ifoddpage iftex inconsolata
tlmgr install infwarerr intcalc jknapltx kastrup knuth-lib kpathsea kpathsea.x86_64-linuxmusl
tlmgr install kvdefinekeys kvoptions kvsetkeys l3backend l3kernel l3packages latex
tlmgr install latex-amsmath-dev latex-base-dev latex-bin latex-bin.x86_64-linuxmusl
tlmgr install latex-firstaid-dev latex-fonts latex-tools-dev latexconfig latexmk
tlmgr install latexmk.x86_64-linuxmusl letltxmacro lipsum listings lm lm-math ltxcmds
tlmgr install lua-alt-getopt luahbtex luahbtex.x86_64-linuxmusl lualatex-math lualibs
tlmgr install luaotfload luaotfload.x86_64-linuxmusl luatex luatex.x86_64-linuxmusl luatexbase
tlmgr install luatexja makeindex makeindex.x86_64-linuxmusl mdwtools metafont
tlmgr install metafont.x86_64-linuxmusl metalogo mfirstuc mfware mfware.x86_64-linuxmusl modes
tlmgr install mptopdf mptopdf.x86_64-linuxmusl multirow natbib newpx newtx norasi-c90
tlmgr install ntheorem oberdiek pdfescape pdflscape pdfpages pdftex pdftex.x86_64-linuxmusl
tlmgr install pdftexcmds pgf placeins plain platex platex-tools platex.x86_64-linuxmusl psnfss
tlmgr install ptex ptex-base ptex-fonts ptex.x86_64-linuxmusl realscripts refcount relsize
tlmgr install rerunfilecheck rsfs scheme-infraonly siunitx splitindex
tlmgr install splitindex.x86_64-linuxmusl stringenc subfigure substr svn-prov symbol tex
tlmgr install tex-gyre tex-ini-files tex.x86_64-linuxmusl texlive-scripts
tlmgr install texlive-scripts.x86_64-linuxmusl texlive.infra texlive.infra.x86_64-linuxmusl
tlmgr install tabularray textcase tikzpagenodes times tipa tools tracklang translator trimspaces ttfutils
tlmgr install ttfutils.x86_64-linuxmusl txfonts uhc ulem unicode-data unicode-math
tlmgr install uniquecounter uplatex uplatex.x86_64-linuxmusl uptex uptex-base uptex-fonts
tlmgr install uptex.x86_64-linuxmusl url varwidth wadalab xcjk2uni xcolor xecjk xetex
tlmgr install xetex.x86_64-linuxmusl xetexconfig xfor xkeyval xltxtra xpinyin xstring xunicode
tlmgr install zapfding zhmetrics zhmetrics-uptex zhnumber
tlmgr install adjustbox colortbl tcolorbox fontawesome5 textpos yfonts wasysym bbm
tlmgr install biblatex mathtools minted pgfplots bbm-macros flowchart makeshape
tlmgr install collection-fontsrecommended cite overpic eepic caption silence ifsym

echo "Finish install extra packages."
