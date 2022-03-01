REMOTE="http://mirror.ctan.org/systems/texlive/tlnet";

INSTALL="/tmp/install-texlive";

mkdir -p "$INSTALL";
curl -sSL "$REMOTE/install-tl-unx.tar.gz" | tar -xz -C "$INSTALL" \
    --strip-components=1;
"$INSTALL/install-tl" -profile .github/workflows/texlive.profile;

export PATH="/tmp/texlive/bin/x86_64-linux:$PATH";

tlmgr generate updmap

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
