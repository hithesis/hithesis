##!/usr/bin/env bash

#' filename : install-MiKTeX_hithesis.sh
#' Date : 2020-05-12
#' contributor : Yanshuo Chu
#' function: install MiKTeX for hithesis

sudo apt-get update
sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys D6BC243565B2087BC3F897C9277A7293F59E4889
sudo apt-get update
echo "deb http://miktex.org/download/ubuntu bionic universe" | sudo tee /etc/apt/sources.list.d/miktex.list
sudo apt-get update
sudo apt-get install miktex --fix-missing
sudo miktexsetup --shared=yes finish
sudo initexmf --admin --set-config-value [MPM]AutoInstall=1
echo "Finish install MiKTeX."
