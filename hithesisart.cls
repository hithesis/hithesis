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


\newif\ifhit@opening
\newif\ifhit@midterm
\define@key{hit}{stage}{%
  \hit@openingfalse
  \hit@midtermfalse
  \expandafter\csname hit@#1true\endcsname}

\DeclareBoolOption[true]{raggedbottom}
\DeclareBoolOption[false]{pifootnote}
\DeclareBoolOption[false]{glue}
\DeclareBoolOption[false]{debug}
\DeclareBoolOption[true]{toc}
\DeclareBoolOption[true]{newtxmath}

\DeclareStringOption{fontset}


\DeclareDefaultOption{\PassOptionsToClass{\CurrentOption}{ctexart}}

\ProcessKeyvalOptions*
\PassOptionsToPackage{no-math}{fontspec}

\ifhit@bachelor\relax\else
\ifhit@master\relax\else
\ifhit@doctor\relax\else
\ClassError{hithesisart}%
{
  \MessageBreak Please specify thesis type in option:
  \MessageBreak type=[bachelor | master | doctor]
}
\fi
\fi
\fi

\ifhit@opening\relax\else
\ifhit@midterm\relax\else
\ClassError{hithesisart}%
{
  \MessageBreak Please specify stage in option:
  \MessageBreak stage=<opening|midterm>
}
\fi
\fi


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
\RequirePackage[sort&compress,numbers]{natbib}
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





\def\hit@def@term#1{%
  \define@key{hit}{#1}{\csname #1\endcsname{##1}}
  \expandafter\gdef\csname #1\endcsname##1{%
    \expandafter\gdef\csname hit@#1\endcsname{##1}}
  \csname #1\endcsname{}}


\hit@def@term{ctitlecover} %中文标题封面
\hit@def@term{csubject}
\hit@def@term{cauthor}
\hit@def@term{cstudentid}
\hit@def@term{cclassid}
\hit@def@term{csupervisor}
\hit@def@term{cdate}


\def\hit@parse@keywords#1{
  \define@key{hit}{#1}{\csname #1\endcsname{##1}}
  \expandafter\gdef\csname hit@#1\endcsname{}
  \expandafter\gdef\csname #1\endcsname##1{
    \@for\reserved@a:=##1\do{
      \expandafter\ifx\csname hit@#1\endcsname\@empty\else
      \expandafter\g@addto@macro\csname hit@#1\endcsname{%
        \ignorespaces\csname hit@#1@separator\endcsname}
      \fi
      \expandafter\expandafter\expandafter\g@addto@macro%
      \expandafter\csname hit@#1\expandafter\endcsname\expandafter{\reserved@a}}}}

\def\hitsetup{\kvsetkeys{hit}}

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

\newcommand{\hit@report@titlepage@bachelor}{
   \ifthenelse%
   {\equal{\hit@fontset}{siyuan}}%
   {\xiaosi[1]\vspace*{0.65em}}%
   {\xiaosi[1]\textcolor[rgb]{1,1,1}{\songti{\hit@hi}}}%
   \vspace*{10mm}
   \begin{center}
     \includegraphics[width=6.2cm]{hitlogo}
   \end{center}
   \begin{center}
     \songti\xiaoyi\textbf{\hit@bachelor@cthesisname\ifhit@opening\hit@bachelor@cthesisproposal\else\hit@bachelor@cthesismidterm\fi}
   \end{center}
   \vspace{15mm}
   \parbox[t][6.5cm][t]{\textwidth}{
     \begin{center}
       \songti\xiaoer\textbf{\hit@bachelor@cthesistitleprefix\hit@title@csep\hit@ctitlecover}
     \end{center}
   }
     \parbox[b][6cm][t]{\textwidth}{
       \begin{center}\songti\sanhao
       \renewcommand{\arraystretch}{2.1}
       \begin{tabular}{l@{\ \ }c}
         \textbf{\hit@bachelor@cmajortitle} & \underline{\makebox[6.1cm]{\textbf{\hit@csubject}}}\\
         \textbf{\hit@bachelor@cstudenttitle} & \underline{\makebox[6.1cm]{\textbf{\hit@cauthor}}}\\
         \textbf{\hit@bachelor@cstudentidtitle} & \underline{\makebox[6.1cm]{\textbf{\hit@cstudentid}}}\\
         \ifhit@weihai % 威海校区特有
         \textbf{\hit@bachelor@cclass} & \underline{\makebox[6.1cm]{\textbf{\hit@cclassid}}}\\
         \fi
         \textbf{\hit@bachelor@csupervisortitle} & \underline{\makebox[6.1cm]{\textbf{\hit@csupervisor}}}\\
         \textbf{\hit@bachelor@cdatetitle} & \underline{\makebox[6.1cm]{\textbf{\hit@cdate}}}\\
       \end{tabular}\renewcommand{\arraystretch}{1}
     \end{center}
     }
   \vfill
   \ifhit@weihai
   \relax
   \else
   \begin{center}
     \lishu\xiaoer\textbf{哈尔滨工业大学教务处制}
   \end{center}
   \fi
}




\newcommand{\hit@report@backpage@bachelor}{
  \thispagestyle{empty}
  \noindent\parbox[t][6.5cm][t]{\textwidth}{\hit@bachelor@teachercomment}
  \noindent\parbox[b][6cm][t]{\textwidth}{\hit@bachelor@teachersign\underline{\makebox[3cm]{}}\hfill\hit@bachelor@checkdate\underline{\makebox[3cm]{}}}
}



\renewcommand\tableofcontents{%
  \thispagestyle{empty}
  \normalsize\@starttoc{toc}
}


\def\makecover{
  \begin{titlepage}
    \hit@report@titlepage@bachelor
    \clearpage
    \ifhit@toc
    \tableofcontents
    \clearpage
    \fi
  \end{titlepage}
}
\def\makebackcover{
    \clearpage
    \hit@report@backpage@bachelor
}


\newcommand\bibstyle@numerical{\bibpunct{[}{]}{,}{s}{,}{\textsuperscript{,}}}
\newcommand\bibstyle@inline{\bibpunct{[}{]}{,}{n}{,}{\hit@inline@sep}}

\citestyle{numerical}
\DeclareRobustCommand\inlinecite{\@inlinecite}
\def\@inlinecite#1{\begingroup\citestyle{inline}\let\@cite\NAT@citenum\citep{#1}\endgroup}
\let\onlinecite\inlinecite

\renewenvironment{thebibliography}[1]{%
  \list{\@biblabel{\@arabic\c@enumiv}}%
  {\renewcommand{\makelabel}[1]{##1\hfill}
    \settowidth{\labelwidth}{\@biblabel{#1}}
    \setlength{\labelsep}{0.5em}
    \setlength{\itemindent}{0pt}
    \setlength{\leftmargin}{\labelsep+\labelwidth}
    \addtolength{\itemsep}{-0.8em}
    \usecounter{enumiv}%
    \let\p@enumiv\@empty
  \renewcommand\theenumiv{\@arabic\c@enumiv}}%
  \sloppy\frenchspacing
  \flushbottom
  \clubpenalty0
  \@clubpenalty \clubpenalty
  \widowpenalty0%
  \interlinepenalty-50%
\sfcode`\.\@m}


\AtEndOfClass{\input{hithesisart.cfg}}
\AtEndOfClass{\sloppy}
\endinput
%%
%% End of file `hithesis.cls'.
