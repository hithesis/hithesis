##!/usr/bin/env bash

#' filename : install-MiKTeX_hithesis.sh
#' Date : 2020-05-12
#' contributor : Yanshuo Chu
#' function: install MiKTeX for hithesis

sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys D6BC243565B2087BC3F897C9277A7293F59E4889
echo "deb http://miktex.org/download/ubuntu bionic universe" | sudo tee /etc/apt/sources.list.d/miktex.list
sudo apt-get update
sudo apt-get install miktex
sudo miktexsetup --shared=yes finish
sudo initexmf --admin --set-config-value [MPM]AutoInstall=1
echo "Finish install MiKTeX."


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

