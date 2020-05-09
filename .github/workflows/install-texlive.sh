REMOTE="http://mirror.ctan.org/systems/texlive/tlnet";

INSTALL="/tmp/install-texlive";

mkdir -p "$INSTALL";
curl -sSL "$REMOTE/install-tl-unx.tar.gz" | tar -xz -C "$INSTALL" \
    --strip-components=1;
"$INSTALL/install-tl" -profile .github/workflows/texlive.profile;

export PATH="/tmp/texlive/bin/x86_64-linux:$PATH";

tlmgr install l3build \
    fontname fontspec xetex \
    cjk environ ms trimspaces ulem zhnumber \
    fandol tex-gyre xits \
    bibunits caption enumitem etoolbox footmisc notoccite pdfpages unicode-math \
    booktabs koma-script nomencl ntheorem siunitx xkeyval \
    pdflscape \
    hologo listings xcolor \
    diagbox float fp metalogo multirow pict2e \
    latexmk ctex ntheorem newtx fontaxes pdfpages enumitem environ trimspaces\
    footmisc varwidth changepage placeins multirow subfigure ccaption splitindex\
    xltxtra realscripts siunitx jknapltx algorithm2e ifoddpage relsize\
    listings glossaries mfirstuc textcase xfor datatool tracklang pdflscape rsfs\
    txfonts xecjk tex-gyre newpx

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
