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
    tikzpagenodes lipsum

echo "Finish install extra packages."

cd $HOME/bin && ls $HOME/.TinyTeX/bin/x86_64-*/* | xargs -n 1 ln -s -f

echo "Begin install font..."
if [ ! -d $HOME/.fonts ]; then
    mkdir $HOME/.fonts;
fi

wget https://github.com/StellarCN/scp_zh/raw/master/fonts/SimSun.ttf -O $HOME/.fonts/SimSun.ttf
wget https://github.com/StellarCN/scp_zh/raw/master/fonts/SimHei.ttf -O $HOME/.fonts/SimHei.ttf
wget https://github.com/Halfish/lstm-ctc-ocr/raw/master/fonts/simkai.ttf -O $HOME/.fonts/simkai.ttf
wget https://github.com/Halfish/lstm-ctc-ocr/raw/master/fonts/simfang.ttf -O $HOME/.fonts/simfang.ttf
wget https://github.com/dangxinchudian/interfacedbcms/raw/master/tcpdf/msyh.ttf -O $HOME/.fonts/msyh.ttf
wget https://github.com/owent-utils/font/raw/master/%E5%BE%AE%E8%BD%AF%E9%9B%85%E9%BB%91/MSYH.TTC -O $HOME/.fonts/msyh.ttc
wget https://github.com/owent-utils/font/raw/master/%E5%BE%AE%E8%BD%AF%E9%9B%85%E9%BB%91/MSYHBD.TTC -O $HOME/.fonts/msyhbd.ttc
wget https://github.com/junmer/source-han-serif-ttf/raw/master/SubsetTTF/CN/SourceHanSerifCN-Regular.ttf -O $HOME/.fonts/SourceHanSerifCN-Regular.ttf

fc-cache -f $HOME/.fonts/
echo "Finish install font..."
