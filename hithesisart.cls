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

\ifhit@debug
\RequirePackage[showframe]{geometry}
\else
\RequirePackage{geometry}
\fi

\geometry{%根据PlutoThesis 原版定义而来
  a4paper, % 210 * 297mm
  hcentering,
  ignoreall,
  nomarginpar,
  centering,
  text={150true mm,236true mm},
  left=30true mm,
  head=5true mm,
  headsep=2true mm,
  footskip=0true mm,
  foot=5.2true mm
}

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


%-- 添加字号设置 --%
\renewcommand\normalsize{%
  \@setfontsize\normalsize{12bp}{15bp}%
  \abovedisplayskip=6pt
  \abovedisplayshortskip=6pt
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

%-- 设置字号 --%
\ctexset{%
  section={
    afterindent=true,
    beforeskip={\ifhit@glue 13.5bp \@plus 1.677267bp \@minus 1.157391bp \else 13.5bp \fi},%上下空0.5行
    afterskip={\ifhit@glue 13.5bp \@plus 1.677267bp \@minus 1.157391bp  \else 13.5bp \fi},
    format={\heiti\ifhit@harbin\sihao[1.25]\else\xiaosan[1.25]\fi},
    aftername=\enspace,
    fixskip=true,
    break={},
  },
  subsection={
    afterindent=true,
    beforeskip={\ifhit@glue 11bp \@plus 1.842609bp \@minus 0.9920497bp \else 11bp \fi},
    afterskip={\ifhit@glue 11bp \@plus 2.33863bp \@minus 0.49602bp \else 11bp \fi},
    format={\heiti\sihao[1.25]},
    aftername=\enspace,
    fixskip=true,
    break={},
  },
  subsubsection={
    afterindent=true,
    beforeskip={\ifhit@glue 8.50398bp \@plus 2.83465bp \@minus 0bp \else 9bp \fi},
    afterskip={\ifhit@glue 8.50398bp \@plus 2.83465bp \@minus 0bp \else 9bp \fi},
    format={\heiti\normalsize},
    aftername=\enspace,
    fixskip=true,
    break={},
  },
  paragraph/afterindent=true,
  subparagraph/afterindent=true
}

\ctexset{
  contentsname={目录}
}

\newcommand{\hit@report@titlepage@graduate}{
   \thispagestyle{empty}
   \zihao{-2}\vspace*{10mm}
   \renewcommand{\CJKglue}{\hskip 3pt plus 0.08\baselineskip}
   \centerline{\kaishu\textbf{\hit@cschoolname}}
   \vspace*{15mm}
   \centering{\zihao{2}\songti\textbf{
    \renewcommand{\CJKglue}{\hskip 3pt plus 0.08\baselineskip}
    \hit@cdegree 论文题目\hit@stagestatus
    }}
   \zihao{-2}\vspace*{11mm}
   \renewcommand{\CJKglue}{\hskip 2pt plus 0.08\baselineskip}
   \begin{center}
   	\renewcommand{\arraystretch}{1.5}
   	\begin{tabular}{m{54pt}@{\hspace{15pt}}c}
       {\xiaoer\songti\textbf{题\hfill 目：}} & \songti\xiaoer\textbf{\hit@ctitleone} \\
                    & {\hspace{-2em} \songti\xiaoer\textbf{\hit@ctitletwo}} \\
    	\end{tabular}
   \end{center}
    \vspace*{-10pt}
   \zihao{3}\vspace{3\baselineskip}
   \begin{center}\songti
      \renewcommand{\arraystretch}{1.9}
      \begin{tabular}{l@{}l}
         \textbf{院\hfill （系）}   & \underline{\makebox[7cm]{\textbf\hit@caffil}}\\
         \textbf{学\hfill 科}     & \underline{\makebox[7cm]{\textbf\hit@csubject}}\\
         \textbf{导\hfill 师}     & \underline{\makebox[7cm]{\textbf\hit@csupervisor}}\\
         \textbf{研\hfill 究\hfill 生}      & \underline{\makebox[7cm]{\textbf\hit@cauthor}}\\
         \textbf{学\hfill 号}  & \underline{\makebox[7cm]{\textbf\hit@cstudentid}}\\
         \textbf{\hit@stagestatus 日期} & \underline{\makebox[7cm]{\textbf\hit@cdate}}\\
      \end{tabular}\renewcommand{\arraystretch}{1}
    \end{center}
   \vfill
   \centerline{\songti\textbf{研究生院制}}
   \vspace{0.9\baselineskip}
}
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% 目前和标准模板还有些许区别，“题目”两个字与题目的内容一同居中，而学校模板是题目两个字位置固定，而题目内容单独居中。 
%% 2.0.11.0a (2020/02/05) 更新研究生封面开题/中期code，使之与研究生院样例更加接近，但具体页面参数数值未精确校准；
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% 开题/中期报告封面—本科生 _modified by hithesis-alpha
%% 2.0.11.0a (2020/02/05) 更新本科开题/中期封面，代码参fu考zhi自：https://github.com/specialpointcentral/hithesis-beta
%% 为适应教务处(http://jwc.hit.edu.cn/2566/list.htm)要求，移除班号项，题目第二行改为居中
\newcommand{\hit@report@titlepage@bachelor}{
   \thispagestyle{empty}
   \zihao{-2}\vspace*{10mm}
   \centering\includegraphics[width=6.2cm]{hitlogo}
   \vfill
   \centering{\xiaoyi\songti\textbf{
    \renewcommand{\CJKglue}{\hskip 3pt plus 0.08\baselineskip}
    论文题目
    }}
   \vfill
   %\zihao{-2}\vspace*{10mm}
   \renewcommand{\CJKglue}{\hskip 2pt plus 0.08\baselineskip}
   \begin{center}
    \renewcommand{\arraystretch}{1.5}
    % 使用空格字符，保证能够空余半个汉字的位置
    \begin{tabular}{m{54pt}@{\hspace{9pt}}c}
      {\xiaoer\songti\textbf{题\hfill 目：}} & \songti\xiaoer\textbf{} \\
                    & {\hspace{-2em} \songti\xiaoer\textbf{}} \\
    \end{tabular}
    \renewcommand{\arraystretch}{1}
   \end{center}
   \zihao{3}\vspace{4\baselineskip}
   \hspace*{70pt}{
    \begin{center}\songti
      \renewcommand{\arraystretch}{2.1}
      \begin{tabular}{l@{\ \ }c}
         \textbf{专\hfill 业}                     & \underline{\makebox[6.1cm]{\textbf{}}}\\
         \textbf{学\hfill 生}                     & \underline{\makebox[6.1cm]{\textbf{}}}\\
         \textbf{学\hfill 号}                     & \underline{\makebox[6.1cm]{\textbf{}}}\\
        \ifhit@weihai % 威海校区特有
         \textbf{班\hfill 号}                     & \underline{\makebox[6.1cm]{\textbf{}}}\\
        \fi
         \textbf{指\hfill 导\hfill 教\hfill 师}   & \underline{\makebox[6.1cm]{\textbf{}}}\\
         \textbf{日\hfill 期}                     & \underline{\makebox[6.1cm]{\textbf{}}}\\
      \end{tabular}\renewcommand{\arraystretch}{1}
    \end{center}
    }
   \vfill
   \ifhit@weihai % 威海校区特有
   % 我也不懂为啥威海校区没有这个东西
   \else
   \centerline{\lishu\textbf{哈尔滨工业大学教务处制}}
   \fi
   \vspace{0.5\baselineskip}
}



\renewcommand\tableofcontents{%
  \clearpage
  \thispagestyle{empty}
  \phantomsection
  \centerline{\heiti\sanhao[1.25]\contentsname}
  \normalsize\@starttoc{toc}
  \clearpage
}


\def\makecover{
  \phantomsection
  \begin{titlepage}
    \clearpage
    \hit@report@titlepage@bachelor
    \clearpage
    \tableofcontents    % 中文目录
    \clearpage
  \end{titlepage}
}






\AtEndOfClass{\sloppy}
\endinput
%%
%% End of file `hithesis.cls'.
