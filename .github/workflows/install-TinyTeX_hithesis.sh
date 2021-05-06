##!/usr/bin/env sh

#' filename : install-TinyTeX_hithesis.sh
#' Date : 2020-05-11
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

tlmgr install tex-gyre ctex splitindex ntheorem newtx fontaxes psnfss pdfpages \
    enumitem environ trimspaces footmisc varwidth changepage placeins multirow \
    subfigure ccaption xltxtra realscripts siunitx jknapltx algorithm2e \
    ifoddpage relsize listings glossaries makeindex mfirstuc textcase xfor datatool tracklang \
    pdflscape rsfs txfonts xecjk newpx fancyhdr hyphen-german glossaries-extra \
    tikzpagenodes lipsum fandol gbt7714

echo "Finish install extra packages."

cd $HOME/bin && ls $HOME/.TinyTeX/bin/x86_64-*/* | xargs -n 1 ln -s -f
