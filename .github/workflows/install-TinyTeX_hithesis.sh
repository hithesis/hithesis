##!/usr/bin/env sh

#' filename : install-TinyTeX_hithesis.sh
#' Date : 2022-03-01
#' contributor : Yanshuo Chu
#' function: minimum install of TeX package for hithesis

wget -qO- "https://yihui.org/gh/tinytex/tools/install-unx.sh" | sh

echo "Finish install TinyTeX, going to install extra dependencies..."

export PATH="$HOME/bin:$PATH";

tlmgr option repository http://www.ctan.org/tex-archive/systems/texlive/tlnet
tlmgr update --self --all
tlmgr path add
fmtutil-sys --all

echo "Finish update , install extra packages..."

tlmgr install \
      adobemapping algorithm2e amscls amsfonts amsmath arphic atbegshi atveryend \
      auxhook babel beamer bibtex bibtex.x86_64-linuxmusl bigfoot bigintcalc bitset \
      booktabs carlisle ccaption changepage cjk cjkpunct cm cns ctablestack ctex \
      datatool dehyph dvipdfmx dvipdfmx.x86_64-linuxmusl dvips dvips.x86_64-linuxmusl \
      ec enumitem environ epstopdf-pkg eso-pic etex etexcmds etoolbox euenc everyhook \
      everysel everyshi fancyhdr fancyvrb fandol filehook firstaid float fontaxes \
      fonts-tlwg fontspec footmisc fp framed garuda-c90 gbt7714 geometry \
      gettitlestring glossaries glossaries-extra glossaries.x86_64-linuxmusl glyphlist \
      graphics graphics-cfg graphics-def grfext grffile helvetic hycolor hypdoc \
      hyperref hyph-utf8 hyphen-base hyphen-german ifoddpage iftex inconsolata \
      infwarerr intcalc jknapltx kastrup knuth-lib kpathsea kpathsea.x86_64-linuxmusl \
      kvdefinekeys kvoptions kvsetkeys l3backend l3kernel l3packages latex \
      latex-amsmath-dev latex-base-dev latex-bin latex-bin.x86_64-linuxmusl \
      latex-firstaid-dev latex-fonts latex-tools-dev latexconfig latexmk \
      latexmk.x86_64-linuxmusl letltxmacro lipsum listings lm lm-math ltxcmds \
      lua-alt-getopt luahbtex luahbtex.x86_64-linuxmusl lualatex-math lualibs \
      luaotfload luaotfload.x86_64-linuxmusl luatex luatex.x86_64-linuxmusl luatexbase \
      luatexja makeindex makeindex.x86_64-linuxmusl mdwtools metafont \
      metafont.x86_64-linuxmusl metalogo mfirstuc mfware mfware.x86_64-linuxmusl modes \
      mptopdf mptopdf.x86_64-linuxmusl ms multirow natbib newpx newtx norasi-c90 \
      ntheorem oberdiek pdfescape pdflscape pdfpages pdftex pdftex.x86_64-linuxmusl \
      pdftexcmds pgf placeins plain platex platex-tools platex.x86_64-linuxmusl psnfss \
      ptex ptex-base ptex-fonts ptex.x86_64-linuxmusl realscripts refcount relsize \
      rerunfilecheck rsfs scheme-infraonly siunitx splitindex \
      splitindex.x86_64-linuxmusl stringenc subfigure substr svn-prov symbol tex \
      tex-gyre tex-ini-files tex.x86_64-linuxmusl texlive-scripts \
      texlive-scripts.x86_64-linuxmusl texlive.infra texlive.infra.x86_64-linuxmusl \
      textcase tikzpagenodes times tipa tools tracklang translator trimspaces ttfutils \
      ttfutils.x86_64-linuxmusl txfonts uhc ulem unicode-data unicode-math \
      uniquecounter uplatex uplatex.x86_64-linuxmusl uptex uptex-base uptex-fonts \
      uptex.x86_64-linuxmusl url varwidth wadalab xcjk2uni xcolor xecjk xetex \
      xetex.x86_64-linuxmusl xetexconfig xfor xkeyval xltxtra xpinyin xstring xunicode \
      zapfding zhmetrics zhmetrics-uptex zhnumber

echo "Finish install extra packages."

cd $HOME/bin && ls $HOME/.TinyTeX/bin/x86_64-*/* | xargs -n 1 ln -s -f
