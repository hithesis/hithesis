%% This is file `hithesisart.cls',
%% generated with the docstrip utility.
%%
%% The original source files were:
%%
%% hithesis.dtx  (with options: `cls')
%% 
%% This is a generated file.
%% 
%% Copyright (C) 2017-2020 by Chu Yanshuo <yanshuoc@gmail.com>
%% 
%% This file may be distributed and/or modified under the
%% conditions of the LaTeX Project Public License, either version 1.3a
%% of this license or (at your option) any later version.
%% The latest version of this license is in:
%% 
%% http://www.latex-project.org/lppl.txt
%% 
%% and version 1.3a or later is part of all distributions of LaTeX
%% version 2004/10/01 or later.
%% 
%% To produce the documentation run the original source files ending with `.dtx'
%% through LaTeX.
%% 
\NeedsTeXFormat{LaTeX2e}[1999/12/01]
\ProvidesClass{hithesisart}
[2020/03/07 2.1.0 Harbin Institute of Technology Thesis Template]
\RequirePackage{ifthen}
\RequirePackage{kvoptions}
\SetupKeyvalOptions{
  family=hit,
  prefix=hit@,
  setkeys=\kvsetkeys}
\newif\ifhit@bachelor
\newif\ifhit@master
\newif\ifhit@doctor
\define@key{hit}{type}{%
  \hit@bachelorfalse
  \hit@masterfalse
  \hit@doctorfalse
  \expandafter\csname hit@#1true\endcsname}
\newif\ifhit@shenzhen
\newif\ifhit@weihai
\newif\ifhit@harbin
\define@key{hit}{campus}{%
  \hit@shenzhenfalse
  \hit@weihaifalse
  \hit@harbinfalse
  \expandafter\csname hit@#1true\endcsname}
\ifhit@weihai\relax\else
\ifhit@shenzhen\relax\else
\hit@harbintrue
\fi
\fi

\newif\ifhit@geometrynewone
\newif\ifhit@geometrynewtwo
\define@key{hit}{newgeometry}{%
  \hit@geometrynewonefalse
  \hit@geometrynewtwofalse
  \expandafter\csname hit@geometrynew#1true\endcsname}

\DeclareBoolOption[false]{arialtoc}
\DeclareBoolOption[false]{arialtitle}
\DeclareBoolOption[true]{raggedbottom}
\DeclareBoolOption[false]{pifootnote}
\DeclareBoolOption[false]{glue}
\DeclareBoolOption[false]{debug}
\DeclareBoolOption[true]{newtxmath}
\DeclareStringOption{fontset}


\DeclareDefaultOption{\PassOptionsToClass{\CurrentOption}{ctexart}}

\ProcessKeyvalOptions*
\PassOptionsToPackage{no-math}{fontspec}

\ifthenelse%
{\equal{\hit@fontset}{}}%
{%
  \PassOptionsToPackage{AutoFakeBold=2}{xeCJK}
}%
{%
  \ifthenelse%
  {\equal{\hit@fontset}{siyuan}}%
  {\relax}%
  {%
    \PassOptionsToPackage{AutoFakeBold=2}{xeCJK}
  }%
  \PassOptionsToClass{fontset=\hit@fontset}{ctexart}
}%
\LoadClass[a4paper,UTF8,zihao=-4,scheme=plain]{ctexart}

\ifhit@bachelor\relax\else
  \ifhit@master\relax\else
    \ifhit@doctor\relax\else
        \ClassError{hithesis}%
                   {Please specify thesis type in option: \MessageBreak
                    type=[bachelor | master | doctor]}{}
      \fi
  \fi
\fi

\RequirePackage{etoolbox}
\RequirePackage{ifxetex}
\ifxetex
\else
        \ClassError{hithesis}%
                   {Please use: \MessageBreak
                    xelatex}{}
\fi
\RequirePackage{xparse}
\RequirePackage{amsmath}
\RequirePackage[amsmath,thmmarks,hyperref]{ntheorem}
\RequirePackage{amssymb}
\RequirePackage[defaultsups]{newtxtext}
\ifhit@newtxmath
\RequirePackage{newtxmath}
\fi
\RequirePackage{courier}
\RequirePackage{graphicx}
\RequirePackage{pdfpages}
\includepdfset{fitpaper=true}
\RequirePackage{enumitem}       %使用enumitem宏包,改变列表项的格式
\RequirePackage{environ}
\ifhit@raggedbottom
  \RequirePackage[bottom,perpage,hang]{footmisc}
  \raggedbottom
\else
  \RequirePackage[perpage,hang]{footmisc}
\fi
\ifhit@pifootnote
  \RequirePackage{pifont}
\fi
\RequirePackage{CJKfntef}

\RequirePackage{longtable}
\RequirePackage{booktabs}
\RequirePackage[sort&compress]{natbib}
\RequirePackage{hyperref}
\hypersetup{%
  CJKbookmarks=true,
  linktoc=all,
  bookmarksnumbered=true,
  bookmarksopen=true,
  bookmarksopenlevel=1,
  breaklinks=true,
  colorlinks=false,
  plainpages=false,
  pdfborder=0 0 0}
\urlstyle{same}
\ifhit@debug\RequirePackage[showframe]{geometry}\else\RequirePackage{geometry}\fi
\geometry{%根据PlutoThesis 原版定义而来
  a4paper, % 210 * 297mm
  hcentering,
  ignoreall,
  nomarginpar,
}
\ifhit@geometrynewtwo%
\geometry{
  centering,
  text={150true mm,236true mm},
  left=30true mm,
  head=5true mm,
  headsep=2true mm,
  footskip=0true mm,
  foot=5.2true mm
}
\else%
\ifhit@geometrynewone%
\geometry{
  centering,
  text={150true mm,240true mm},
  left=30true mm,
  head=5true mm,
  headsep=0true mm,
  footskip=0true mm,
  foot=0true mm
}
\else%
\geometry{%根据PlutoThesis 原版定义而来
text={150true mm,224true mm},
top=35.5true mm,
left=30true mm,
head=5true mm,
headsep=2.5true mm,
foot=8.5true mm
}
\fi%
\fi%
\ifhit@debug%
\RequirePackage{layout}
\RequirePackage{layouts}
\RequirePackage{lineno}
\fi
\RequirePackage{fancyhdr}
\RequirePackage{tabularx}
\RequirePackage{varwidth}
\RequirePackage{changepage}
\RequirePackage{multicol}
\RequirePackage[below]{placeins}%允许上一个section的浮动图形出现在下一个section的开始部分,还提供\FloatBarrier命令,使所有未处理的浮动图形立即被处理
\RequirePackage{flafter}       % 使得所有浮动体不能被放置在其浮动环境之前，以免浮动体在引述它的文本之前出现.
\RequirePackage{multirow}       %使用Multirow宏包，使得表格可以合并多个row格
\RequirePackage{subfigure}%支持子图 %centerlast 设置最后一行是否居中
\RequirePackage[subfigure]{ccaption} %支持双语标题
\RequirePackage[makeindex]{splitidx}
\newindex[]{china}
\newindex[]{english}
\RequirePackage{xltxtra}


\renewcommand\normalsize{%
  \@setfontsize\normalsize{12bp}{\ifhit@glue 20.50398bp \@plus 2.83465bp \@minus 0bp\else 20.50398bp\fi}%
  \abovedisplayskip=8pt
  \abovedisplayshortskip=8pt
  \belowdisplayskip=\abovedisplayskip
  \belowdisplayshortskip=\abovedisplayshortskip}
\def\hit@def@fontsize#1#2{%
  \expandafter\newcommand\csname #1\endcsname[1][1.3]{%
    \fontsize{#2}{##1\dimexpr #2}\selectfont}}
\hit@def@fontsize{dachu}{58bp}
\hit@def@fontsize{chuhao}{42bp}
\hit@def@fontsize{xiaochu}{36bp}
\hit@def@fontsize{yihao}{26bp}
\hit@def@fontsize{xiaoyi}{24bp}
\hit@def@fontsize{erhao}{22bp}
\hit@def@fontsize{xiaoer}{18bp}
\hit@def@fontsize{sanhao}{16bp}
\hit@def@fontsize{xiaosan}{15bp}
\hit@def@fontsize{sihao}{14bp}
\hit@def@fontsize{banxiaosi}{13bp}
\hit@def@fontsize{xiaosi}{12bp}
\hit@def@fontsize{dawu}{11bp}
\hit@def@fontsize{wuhao}{10.5bp}
\hit@def@fontsize{xiaowu}{9bp}
\hit@def@fontsize{liuhao}{7.5bp}
\hit@def@fontsize{xiaoliu}{6.5bp}
\hit@def@fontsize{qihao}{5.5bp}
\hit@def@fontsize{bahao}{5bp}

\let\hit@section\section
\RenewDocumentCommand\section{s o m o}{
  \IfBooleanTF{#1}%
  {% if \section*
    \IfNoValueTF{#2}%
    {\hit@section*{#3}}%
    {\hit@section*[#2]{#3}}%
    \IfValueT{#4}{%
      \addcontentsline{toe}{section}{#4}
    }
  }%
  {% if \section
    \IfNoValueTF{#2}%
    {\hit@section{#3}}%
    {\hit@section[#2]{#3}}%
    \IfValueT{#4}{%
    \addcontentsline{toe}{section}{\protect\numberline{\csname thesection\endcsname}\ignorespaces #4}
    }
  }
}

\let\hit@subsection\subsection
\RenewDocumentCommand\subsection{s o m o}{
  \IfBooleanTF{#1}%
  {% if \subsection*
    \IfNoValueTF{#2}%
    {\hit@subsection*{#3}}%
    {\hit@subsection*[#2]{#3}}%
    \IfValueT{#4}{%
      \addcontentsline{toe}{subsection}{#4}
    }
  }%
  {% if \subsection
    \IfNoValueTF{#2}%
    {\hit@subsection{#3}}%
    {\hit@subsection[#2]{#3}}%
    \IfValueT{#4}{%
    \addcontentsline{toe}{subsection}{\protect\numberline{\csname thesubsection\endcsname}\ignorespaces #4}
    }
  }
}

\let\hit@subsubsection\subsubsection
\RenewDocumentCommand\subsubsection{s o m o}{
  \IfBooleanTF{#1}%
  {% if \subsubsection*
    \IfNoValueTF{#2}%
    {\hit@subsubsection*{#3}}%
    {\hit@subsubsection*[#2]{#3}}%
    \IfValueT{#4}{%
      \addcontentsline{toe}{subsubsection}{#4}
    }
  }%
  {% if \subsubsection
    \IfNoValueTF{#2}%
    {\hit@subsubsection{#3}}%
    {\hit@subsubsection[#2]{#3}}%
    \IfValueT{#4}{%
    \addcontentsline{toe}{subsubsection}{\protect\numberline{\csname thesubsubsection\endcsname}\ignorespaces #4}
    }
  }
}

\AtEndOfClass{\sloppy}
\endinput
%%
%% End of file `hithesis.cls'.
