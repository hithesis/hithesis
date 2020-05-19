%%
%% This is file `hithesis.cls',
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
\ProvidesClass{hithesis}
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


\newif\ifhit@english
\newif\ifhit@chinese
\define@key{hit}{language}{%
  \hit@englishfalse
  \hit@chinesefalse
  \expandafter\csname hit@#1true\endcsname}
\ifhit@english\relax\else
\hit@chinesetrue
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
\DeclareBoolOption[false]{tocfour}
\DeclareBoolOption[true]{tocblank}
\DeclareBoolOption[true]{chapterhang}
\DeclareBoolOption[true]{fulltime}
\DeclareBoolOption[false]{subtitle}
\DeclareBoolOption[false]{debug}
\DeclareBoolOption[false]{openright}
\DeclareBoolOption[false]{library}
\DeclareBoolOption[false]{capcenterlast}
\DeclareBoolOption[false]{subcapcenterlast}
\DeclareBoolOption[false]{absupper}
\DeclareBoolOption[false]{bsmainpagenumberline}
\DeclareBoolOption[false]{bsfrontpagenumberline}
\DeclareBoolOption[true]{bsheadrule}
\DeclareBoolOption[true]{newtxmath}
\DeclareBoolOption[false]{splitbibitem}
\DeclareStringOption{fontset}
\DeclareDefaultOption{\PassOptionsToClass{\CurrentOption}{ctexbook}}
\ProcessKeyvalOptions*
\PassOptionsToPackage{no-math}{fontspec}
\ifhit@bachelor
\PassOptionsToClass{oneside}{book}
\fi
\ifhit@master
\PassOptionsToClass{oneside}{book}
\fi
\ifhit@doctor
\PassOptionsToClass{twoside}{book}
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
  \PassOptionsToClass{fontset=\hit@fontset}{ctexbook}
}%
\LoadClass[a4paper,openany,UTF8,zihao=-4,scheme=plain]{ctexbook}
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
\ifhit@subcapcenterlast
\PassOptionsToPackage{centerlast}{subfigure}
\fi
\RequirePackage{subfigure}%支持子图 %centerlast 设置最后一行是否居中
\RequirePackage[subfigure]{ccaption} %支持双语标题
\RequirePackage[makeindex]{splitidx}
\newindex[]{china}
\newindex[]{english}
\RequirePackage{xltxtra}


\ifhit@english
\RequirePackage[xindy,order=letter]{glossaries-extra}
\newglossarystyle{engstyle}{%
  \glossarystyle{long}%
  \renewenvironment{theglossary}%
  {\vspace{-\baselineskip}\centering\begin{longtable}{@{\hskip 1cm}p{3.5cm}p{\glsdescwidth}}}%
     {\end{longtable}}}
\setabbreviationstyle[acronym]{long-short}
\else
\RequirePackage{glossaries}
\setacronymstyle{short-long}
\fi

\renewcommand*{\genacrfullformat}[2]{%
  \glsentrylong{#1}%
}
\ifhit@english
\makenoidxglossaries
\else
\makeglossaries
\fi



\ifhit@library\hit@openrightfalse\else\relax\fi
\let\hit@cleardoublepage\cleardoublepage
\newcommand{\hit@clearemptydoublepage}{%
  \clearpage{\pagestyle{hit@empty}\hit@cleardoublepage}
}
\let\cleardoublepage\hit@clearemptydoublepage
\renewcommand\frontmatter{%
  \ifhit@openright\cleardoublepage\else\clearpage\fi
  \@mainmatterfalse
  \pagenumbering{Roman}
  \pagestyle{hit@empty}
}
\renewcommand\mainmatter{%
  \ifhit@tocblank%
  \addtocontents{toc}{\vspace{\baselineskip}} %规范中并没有这一要求，此处不应该加
  \addtocontents{toe}{\vspace{\baselineskip}}
  \fi%
  \ifhit@doctor%
    \ifhit@library\clearpage\else\cleardoublepage\fi
    \else%
    \clearpage
  \fi%
  \@mainmattertrue
  \pagenumbering{arabic}
  \pagestyle{hit@headings}
}
\renewcommand\backmatter{%
  \ifhit@openright\cleardoublepage\else\clearpage\fi
  \@mainmattertrue}
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
\let\hit@headrule\headrule
\fancypagestyle{hit@empty}{%
  \fancyhf{}
  \let\headrule\hit@headrule%
  \renewcommand{\headrulewidth}{0pt}
  \renewcommand{\footrulewidth}{0pt}
}
\fancypagestyle{hit@headings}{%
  \fancyhf{}
  \ifhit@english
    \fancyhead[C]{\xiaowu[0]\leftmark}
    \fancyfoot[C]{\xiaowu-~\thepage~-}
    \renewcommand{\headrule}{
      \vskip 1.190132pt
      \hrule\@height2.276208pt\@width\headwidth
      \vskip 0.75pt
      \hrule\@height.75pt\@width\headwidth
    }
  \else
    \ifhit@doctor
      \fancyhead[CO]{\songti\xiaowu[0]\leftmark}
      \ifhit@harbin
        \fancyhead[CE]{\songti\xiaowu[0]\hit@cschoolname\hit@cdegree\hit@cthesisname}
      \fi
      \ifhit@shenzhen
        \fancyhead[CE]{\songti\xiaowu[0]\hit@cschoolname\hit@shenzhencampus\hit@cdegree\hit@cthesisname}
      \fi
      \ifhit@weihai
        \fancyhead[CE]{\songti\xiaowu[0]\hit@cschoolname\hit@weihaicampus\hit@cdegree\hit@cthesisname}
      \fi
    \else
      \ifhit@master
        \ifhit@harbin
          \fancyhead[C]{\songti\xiaowu[0]\hit@cschoolname\hit@cdegree\hit@cthesisname}
        \fi
        \ifhit@shenzhen
          \fancyhead[C]{\songti\xiaowu[0]\hit@cschoolname\hit@shenzhencampus\hit@cdegree\hit@cthesisname}
        \fi
        \ifhit@weihai
          \fancyhead[C]{\songti\xiaowu[0]\hit@cschoolname\hit@weihaicampus\hit@cdegree\hit@cthesisname}
        \fi
      \fi
    \fi
    \ifhit@bachelor
      \ifhit@harbin
        \fancyhead[C]{\songti\xiaowu[0]\hit@cschoolname\hit@bachelor@cxuewei\hit@bachelor@cthesisname}%
      \fi
      \ifhit@shenzhen
        \fancyhead[C]{\songti\xiaowu[0]\hit@cschoolname\hit@shenzhencampus\hit@bachelor@cxuewei\hit@bachelor@cthesisname}%
      \fi
      \ifhit@weihai
        \fancyhead[C]{\songti\xiaowu[0]\hit@cschoolname\hit@weihaicampus\hit@bachelor@cxuewei\hit@bachelor@cthesisname}%
      \fi
      \fancyfoot[C]{\xiaowu\if@mainmatter\ifhit@bsmainpagenumberline-~\thepage~-\else\thepage\fi\else\ifhit@bsfrontpagenumberline-~\thepage~-\else\thepage\fi\fi}
      \ifhit@bsheadrule
        \renewcommand{\headrule}{
        \vskip 1.190132pt
        \hrule\@height2.276208pt\@width\headwidth
        \vskip 0.75pt
        \hrule\@height.75pt\@width\headwidth
        }
      \else
        \renewcommand{\headrulewidth}{0pt}
      \fi
    \else
      \fancyfoot[C]{\xiaowu-~\thepage~-}
      \renewcommand{\headrule}{
      \vskip 1.190132pt
      \hrule\@height2.276208pt\@width\headwidth
      \vskip 0.75pt
      \hrule\@height.75pt\@width\headwidth
      }
    \fi
  \fi

  % 此处可能和word模板不一致
  % 页眉中小五汉字，0行距时，占用9bt，页眉高度为14pt, 所以以下数字之和要保持等于14pt-9bt=4.96634pt
  % 根据PlutoThesis模板中rule宽度定义为2.25， 0.75， 保持粗线和细线之间的间距为细线宽度。
  % 如果页眉是多行的情况，rule向下溢出
  \renewcommand{\footrulewidth}{0pt}
}
\AtBeginDocument{%此处解决页眉经典bug
  \pagestyle{hit@empty}
  \renewcommand{\chaptermark}[1]{\@mkboth{\CTEXthechapter\enspace#1}{}}}
\ctexset{%
  punct=quanjiao,
  space=auto,
  autoindent=true}
\setlist{nosep}
\def\hit@textcircled#1{%
  \ifnum\value{#1} >9
    \ClassError{hithesis}%
      {Too many footnotes in this page.}{Keep footnote less than 10.}
  \fi
  \ifhit@pifootnote%
    \ding{\the\numexpr\value{#1}+171\relax}%
  \else%
    \textcircled{\xiaoliu\arabic{#1}}%
  \fi}
\renewcommand{\thefootnote}{\hit@textcircled{footnote}}
\renewcommand{\thempfootnote}{\hit@textcircled{mpfootnote}}
\def\footnoterule{\vskip-3\p@\hrule\@width0.3\textwidth\@height0.4\p@\vskip2.6\p@}
\let\hit@footnotesize\footnotesize
\renewcommand\footnotesize{\hit@footnotesize\xiaowu[1.5]}
\footnotemargin1.5em\relax
\let\hit@makefnmark\@makefnmark
\def\hit@@makefnmark{\hbox{{\normalfont\@thefnmark}}}
\pretocmd{\@makefntext}{\let\@makefnmark\hit@@makefnmark}{}{}
\apptocmd{\@makefntext}{\let\@makefnmark\hit@makefnmark}{}{}
\allowdisplaybreaks[4]
\predisplaypenalty=0  %公式之前可以换页，公式出现在页面顶部
\postdisplaypenalty=0
\renewcommand\theequation{\ifnum \c@chapter>\z@ \thechapter-\fi\@arabic\c@equation}
\def\make@df@tag{\@ifstar\hit@make@df@tag@@\make@df@tag@@@}
\def\hit@make@df@tag@@#1{\gdef\df@tag{\hit@maketag{#1}\def\@currentlabel{#1}}}
\iffalse
\ifhit@bachelor
  \def\hit@maketag#1{\maketag@@@{%
    (\ignorespaces\text{\equationname\hskip0.5em}#1\unskip\@@italiccorr)}}
  \def\tagform@#1{\maketag@@@{%
    (\ignorespaces\text{\equationname\hskip0.5em}#1\unskip\@@italiccorr)\equcaption{#1}}}
\fi
\fi
\def\hit@maketag#1{\maketag@@@{(\ignorespaces #1\unskip\@@italiccorr)}}
\def\tagform@#1{\maketag@@@{(\ignorespaces #1\unskip\@@italiccorr)\equcaption{#1}}}
\renewcommand{\eqref}[1]{\textup{(\ref{#1})}}
\setlength{\intextsep}{\ifhit@glue 8.50398bp \@plus 2.83465bp \@minus 0bp\else 8.50398bp\fi}
\setlength{\textfloatsep}{\ifhit@glue 8.50398bp \@plus 2.83465bp \@minus 0bp\else 8.50398bp\fi}
\setlength{\floatsep}{\ifhit@glue 12bp \@plus 2.83465bp \@minus 0bp\else 12bp\fi}
\g@addto@macro\appendix{\renewcommand*{\thefigure}{\thechapter-\arabic{figure}}}
\g@addto@macro\appendix{\renewcommand*{\thetable}{\thechapter-\arabic{table}}}
\g@addto@macro\appendix{\renewcommand*{\theequation}{\thechapter-\arabic{equation}}}
\renewcommand{\textfraction}{0.15}
\renewcommand{\topfraction}{0.85}
\renewcommand{\bottomfraction}{0.65}
\renewcommand{\floatpagefraction}{0.60}
\long\def\@makecaption#1#2{%
  \vskip\abovecaptionskip
  \wuhao\sbox\@tempboxa{#1\ifhit@bachelor\hskip\ccwd\else\enskip\fi#2}%
  \ifdim \wd\@tempboxa >\hsize
  \ifhit@capcenterlast%
  \vskip 6.3bp%
  {\setbox0=\vbox{#1\ifhit@bachelor\hskip\ccwd\else\enskip\fi#2}
  \setbox1=\vbox{%
  \unvbox0
  \setbox2=\lastbox
  \hbox to \textwidth{\hfill\unhcopy2 \unskip\unskip\hfill}
  }
  \unvbox1}
  \else%
  #1\ifhit@bachelor\hskip\ccwd\else\enskip\fi#2%
  \fi%
    \par
  \else
  \global \@minipagefalse
  \hb@xt@\hsize{\hfil\box\@tempboxa\hfil}%
  \fi
\vskip\belowcaptionskip}
\long\def\LT@makecaption#1#2#3{%
  \LT@mcol\LT@cols c{\hbox to\z@{\hss\parbox[t]\LTcapwidth{%
    \wuhao\sbox\@tempboxa{#1{#2\ifhit@bachelor\hskip\ccwd\else\enskip\fi }#3}%
    \ifdim\wd\@tempboxa>\hsize
      \ifhit@capcenterlast%
        \vskip 6.3bp%
        {\setbox0=\vbox{#1{#2\ifhit@bachelor\hskip\ccwd\else\enskip\fi }#3}
          \setbox1=\vbox{%
             \unvbox0
             \setbox2=\lastbox
             \hbox to \textwidth{\hfill\unhcopy2 \unskip\unskip\hfill}
          }
        \unvbox1}
      \else%
        #1{#2\ifhit@bachelor\hskip\ccwd\else\enskip\fi }#3%
      \fi%
      \par
    \else
      \global \@minipagefalse
      \hbox to\hsize{\hfil\box\@tempboxa\hfil}
    \fi
    \endgraf\vskip\belowcaptionskip}%
  \hss}}}
\renewcommand*{\longbionenumcaption}[7]{%
\@if@contemptyarg{#1}{\caption{#2}}{\caption[#1]{#2}}%
\global\let\@cont@oldtablename\tablename
\gdef\tablename{#3}
\global\let\LT@c@ption\@cont@LT@nonumintoc
\\[#6]
\@if@contemptyarg{#4}{\caption{#5}}{\caption[#4]{#5}}%
\global\let\tablename\@cont@oldtablename
\global\let\LT@c@ption\@cont@oldLT@c@ption
\vspace{#7}}
\let\hit@LT@array\LT@array
\def\LT@array{\wuhao\hit@LT@array} % set default font size
\newcommand{\ltfontsize}[1]{\def\LT@array{#1\hit@LT@array}}
\renewcommand{\thesubtable}{(\alph{subtable})}
\renewcommand{\thefigure}{\arabic{chapter}-\arabic{figure}}%使图编号为 7-1 的格式 %\protect{~}
\renewcommand{\thesubfigure}{\alph{subfigure})}%使子图编号为 a)的格式
\renewcommand{\p@subfigure}{\thefigure~} %使子图引用为 7-1 a) 的格式，母图编号和子图编号之间用~加一个空格
\renewcommand{\thetable}{\arabic{chapter}-\arabic{table}}%使表编号为 7-1 的格式
\setitemize{leftmargin=0em,itemsep=0em,partopsep=0em,parsep=0em,topsep=0em,itemindent=3em}
\setenumerate{leftmargin=0em,itemsep=0em,partopsep=0em,parsep=0em,topsep=0em,itemindent=3.5em}
\newcommand{\citeup}[1]{\textsuperscript{\cite{#1}}}
\captionnamefont{\wuhao}
\captiontitlefont{\wuhao}
\renewcommand{\subcapsize}{\wuhao}
\setlength{\abovecaptionskip}{0pt}%为了双标题之间的间距，不能设置
\setlength{\belowcaptionskip}{0pt}
\newcounter{pubctr} %自定义新计数器
\newenvironment{publist}{%%%%%定义新环境
\begin{list}{[\arabic{pubctr}]} %%标签格式
    {
     \usecounter{pubctr}
     \setlength{\leftmargin}{1.7em}     % 左边界 \leftmargin =\itemindent + \labelwidth + \labelsep
     \setlength{\itemindent}{0em}     % 标号缩进量
     \setlength{\labelsep}{0.5em}       % 标号和列表项之间的距离,默认0.5em
     \setlength{\rightmargin}{0em}    % 右边界
     \setlength{\topsep}{0ex}         % 列表到上下文的垂直距离
     \setlength{\parsep}{0ex}         % 段落间距
     \setlength{\itemsep}{0ex}        % 标签间距
     \setlength{\listparindent}{0pt} % 段落缩进量
    }}
{\end{list}}
\renewtheoremstyle{plain}
{\item[\hskip\labelsep \theorem@headerfont ##1\ ##2\theorem@separator]}
{\item[\hskip\labelsep \theorem@headerfont ##1\ ##2\ ##3\theorem@separator]}
\theorembodyfont{\songti\rmfamily}
\theoremheaderfont{\heiti\rmfamily}
\theoremsymbol{$\square$}
\setlength{\theorempreskipamount}{0pt}
\setlength{\theorempostskipamount}{-2pt}
\setlength{\parindent}{2em}
\arraycolsep=1.6pt
\def\hit@title@font{%
  \ifhit@arialtitle\sffamily\else\heiti\fi}

\newcommand\hit@chapter@titleformat[1]{%开启悬挂缩进选项
  \ifhit@english
  \MakeUppercase{#1}
  \else
    \ifthenelse%
    {\equal{#1}{\eabstractcname}}%
    {\bfseries #1}%
    % 实现章标题的居中加悬挂缩进，注意，此处一定是\CTEX@chaptername\CTEX@chapter@aftername, 否则是英文标题长度
    {\ifhit@chapterhang\settowidth{\hangindent}{\CTEX@chaptername\CTEX@chapter@aftername}\hangafter=1\fi#1}
    \fi}

\newcommand\hit@chapter@engformat[1]{%开启悬挂缩进选项
  \begin{center}
    \hit@title@font
    \if@mainmatter
    \xiaoer[1.57481]
    \else
    \sanhao[1.57481]
    \fi\bfseries
    #1
  \end{center}}

\newcommand\hit@chapter@engnameformat[1]{%开启悬挂缩进选项
  \begin{center}
    \MakeUppercase{#1}
  \end{center}}


\renewcommand\@afterheading{%
  \@nobreaktrue
  \everypar{%
    \if@nobreak
      \@nobreakfalse
      \clubpenalty 1
      \if@afterindent \else
        {\setbox\z@\lastbox}%
      \fi
    \else
      \clubpenalty 1
      \everypar{}%
    \fi}}

\ifhit@english
  \ctexset{%
    chapter={
      afterindent=true,
      pagestyle={hit@headings},
      beforeskip={28.34658bp},%一个空行 1.57481 × 18
      afterskip={24.74658bp},%0.8应该不计算间距 0.8 × 18 + 0.57481×18
      aftername={\par},
      format={\hit@chapter@engformat},
      nameformat={\hit@chapter@engnameformat},%\center 会影响之后全局
      numberformat=\relax,
      titleformat={\hit@chapter@titleformat},
      fixskip=true, % 添加这一行去除默认间距
      %hang=true,
    },
    section={
      afterindent=true,
      beforeskip={\ifhit@glue 13.5bp \@plus 1.677267bp \@minus 1.157391bp \else 13.5bp \fi},%上下空0.5行
      afterskip={\ifhit@glue 13.5bp \@plus 1.677267bp \@minus 1.157391bp  \else 13.5bp \fi},
      format={\hit@title@font\ifhit@glue\fontsize{15bp}{21bp \@plus 1.677267bp \@minus 1.157391bp}\else\fontsize{15bp}{21bp}\fi\selectfont\bfseries},
      aftername=\enspace,
      fixskip=true,
      break={},
    },
    subsection={
      afterindent=true,
      beforeskip={\ifhit@glue 11bp \@plus 1.842609bp \@minus 0.9920497bp \else 11bp \fi},
      afterskip={\ifhit@glue 11bp \@plus 2.33863bp \@minus 0.49602bp \else 11bp \fi},
      format={\hit@title@font\ifhit@glue\fontsize{14bp}{18bp \@plus 1.842609bp \@minus 0.9920497bp}\else\fontsize{14bp}{18bp}\fi\selectfont\bfseries},
      aftername=\enspace,
      fixskip=true,
      break={},
    },
    subsubsection={
      afterindent=true,
      beforeskip={\ifhit@glue 8.50398bp \@plus 2.83465bp \@minus 0bp \else 9bp \fi},
      afterskip={\ifhit@glue 8.50398bp \@plus 2.83465bp \@minus 0bp \else 9bp \fi},
      format={\hit@title@font\normalsize},
      aftername=\enspace,
      fixskip=true,
      break={},
    },
    paragraph/afterindent=true,
    subparagraph/afterindent=true
  }
\else
  \ctexset{%
    chapter={
      afterindent=true,
      pagestyle={hit@headings},
      beforeskip={28.34658bp},%一个空行 1.57481 × 18
      afterskip={24.74658bp},%0.8应该不计算间距 0.8 × 18 + 0.57481×18
      aftername=\enspace,
      format={\centering\hit@title@font\xiaoer[1.57481]},%\center 会影响之后全局
      nameformat=\relax,
      numberformat=\relax,
      titleformat=\hit@chapter@titleformat,
      fixskip=true, % 添加这一行去除默认间距
      %hang=true,
    },
    section={
      afterindent=true,
      beforeskip={\ifhit@glue 13.5bp \@plus 1.677267bp \@minus 1.157391bp \else 13.5bp \fi},%上下空0.5行
      afterskip={\ifhit@glue 13.5bp \@plus 1.677267bp \@minus 1.157391bp  \else 13.5bp \fi},
      format={\hit@title@font\ifhit@glue\fontsize{15bp}{21bp \@plus 1.677267bp \@minus 1.157391bp}\else\fontsize{15bp}{21bp}\fi\selectfont},
      aftername=\enspace,
      fixskip=true,
      break={},
    },
    subsection={
      afterindent=true,
      beforeskip={\ifhit@glue 11bp \@plus 1.842609bp \@minus 0.9920497bp \else 11bp \fi},
      afterskip={\ifhit@glue 11bp \@plus 2.33863bp \@minus 0.49602bp \else 11bp \fi},
      format={\hit@title@font\ifhit@glue\fontsize{14bp}{18bp \@plus 1.842609bp \@minus 0.9920497bp}\else\fontsize{14bp}{18bp}\fi\selectfont},
      aftername=\enspace,
      fixskip=true,
      break={},
    },
    subsubsection={
      afterindent=true,
      beforeskip={\ifhit@glue 8.50398bp \@plus 2.83465bp \@minus 0bp \else 9bp \fi},
      afterskip={\ifhit@glue 8.50398bp \@plus 2.83465bp \@minus 0bp \else 9bp \fi},
      format={\hit@title@font\normalsize},
      aftername=\enspace,
      fixskip=true,
      break={},
    },
    paragraph/afterindent=true,
    subparagraph/afterindent=true
  }
\fi


\ifhit@english
\NewDocumentCommand{\hit@appendix@chapter}{s o m o}{%
  \IfBooleanT{#1}%
  {
    \phantomsection
    \IfValueTF{#2}{
      \markboth{#2}{#2}
    }{
      \markboth{#3}{#3}
    }

    \ifthenelse%
    {\equal{#3}{\cabstractcname}}%
    {\relax}
    {\addcontentsline{toc}{chapter}{\texorpdfstring{\ifhit@arialtitle\sffamily\heiti\else\heiti\fi #3}{#3}}}

    \IfValueT{#4}{\addcontentsline{toe}{chapter}{\texorpdfstring{\bfseries #4}{#4}}}
    \hit@chapter*{#3}
  }
}
\else
\NewDocumentCommand{\hit@appendix@chapter}{s o m o}{%
  \IfBooleanT{#1}%
  {
    \phantomsection
    \IfValueTF{#2}{
      \markboth{#2}{#2}
    }{
      \markboth{#3}{#3}
    }

    \ifthenelse%
      {\equal{#3}{\eabstractcname}}%
      {\addcontentsline{toc}{chapter}{\texorpdfstring{\ifhit@arialtitle\sffamily\heiti\else\heiti\fi \ifhit@absupper\MakeUppercase{#3}\else#3\fi}{#3}}}
      {\addcontentsline{toc}{chapter}{\texorpdfstring{\ifhit@arialtitle\sffamily\heiti\else\heiti\fi #3}{#3}}}

    \IfValueT{#4}{\addcontentsline{toe}{chapter}{\texorpdfstring{\bfseries #4}{#4}}}
    \hit@chapter*{#3}
  }
}
\fi


\newcommand{\BiAppChapter}[2]    % 该附录命令适用于有章节的完整附录
{\phantomsection
 \chapter{#1}
 \addcontentsline{toe}{chapter}{\texorpdfstring{\bfseries \xiaosi Appendix \thechapter~~#2}{Appendix \thechapter~~#2}}
}
\let\hit@chapter\chapter
\RenewDocumentCommand{\chapter}{s o m o}{%
  \ifhit@openright\cleardoublepage\else\clearpage\fi\phantomsection%
  \IfBooleanTF{#1}%
  {% if \chapter*
    \IfNoValueTF{#2}%
    {\hit@chapter*{#3}}%
    {\hit@chapter*[#2]{#3}}%
    \IfValueT{#4}{%
    \addcontentsline{toe}{chapter}{\texorpdfstring{\bfseries #4}{#4}}
    }
  }%
  {% if \chapter
    \IfNoValueTF{#2}%
    {\hit@chapter{#3}}%
    {\hit@chapter[#2]{#3}}%
    \IfValueT{#4}{%
    \addcontentsline{toe}{chapter}{\texorpdfstring{\bfseries\relax Chapter \thechapter\hspace{0.5em}\ignorespaces #4}{Chapter \thechapter\hspace{0.5em}\ignorespaces #4}}
    }
  }
}

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
\def\hit@def@term#1{%
  \define@key{hit}{#1}{\csname #1\endcsname{##1}}
  \expandafter\gdef\csname #1\endcsname##1{%
    \expandafter\gdef\csname hit@#1\endcsname{##1}}
  \csname #1\endcsname{}}

\hit@def@term{statesecrets} %密级
\hit@def@term{natclassifiedindex}  %国内图书分类号
\hit@def@term{intclassifiedindex}  %国际图书分类号

\hit@def@term{ctitlecover} %中文标题封面
\hit@def@term{ctitle} %中文标题
\hit@def@term{csubtitle} %中文副标题
\hit@def@term{cxueke} %中文学科
\hit@def@term{cauthor} %中文作者
\hit@def@term{csupervisor} %中文导师
\hit@def@term{cassosupervisor} %中文副导师
\hit@def@term{ccosupervisor}%中文联合导师
\hit@def@term{caffil}%中文院系
\hit@def@term{csubject}%中文专业
\hit@def@term{cdate}

\hit@def@term{cstudentid}%
\hit@def@term{cstudenttype}%
\hit@def@term{ctitleone}%
\hit@def@term{ctitletwo}%

\hit@def@term{etitle} %英文标题
\hit@def@term{esubtitle} %英文标题
\hit@def@term{exueke} %英文学科
\hit@def@term{eauthor} %英文作者
\hit@def@term{esupervisor} %英文导师
\hit@def@term{eassosupervisor} %英文副导师
\hit@def@term{ecosupervisor} %英文联合导师
\hit@def@term{eaffil}
\hit@def@term{esubject}
\hit@def@term{edate}
\hit@def@term{estudenttype}
\newcommand{\hit@@cabstract}[1]{\long\gdef\hit@cabstract{#1}}
\newenvironment{cabstract}{\Collect@Body\hit@@cabstract}{}
\newcommand{\hit@@eabstract}[1]{\long\gdef\hit@eabstract{#1}}
\newenvironment{eabstract}{\Collect@Body\hit@@eabstract}{}
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
\hit@parse@keywords{ckeywords}
\hit@parse@keywords{ekeywords}
\def\hitsetup{\kvsetkeys{hit}}
\newlength{\hit@title@width}
\newcommand{\hit@put@title}[2][\hit@title@width]{%
  \begin{CJKfilltwosides}[b]{#1}#2\end{CJKfilltwosides}}

\def\hit@first@titlepage{%
  \ifhit@bachelor\hit@first@titlepage@bachelor\else\hit@first@titlepage@other\fi}
\def\hit@second@titlepage{%
  \ifhit@bachelor\hit@second@titlepage@bachelor\else\hit@second@titlepage@other\fi}

\newcommand{\hit@first@titlepage@bachelor}{
\ifthenelse%
{\equal{\hit@fontset}{siyuan}}%
{\xiaosi[1]\vspace*{0.65em}}%
{\xiaosi[1]\textcolor[rgb]{1,1,1}{\songti{\hit@hi}}}%
  \vspace*{1.2cm}
  \begin{center}
    \parbox[t][3.4cm][t]{\textwidth}{
  \begin{center}\erhao[0]\heiti\hit@ctitlecover\end{center} }
    \parbox[t][9cm][t]{\textwidth}{
    \begin{center}\xiaoer[0]\songti\textbf{\hit@cauthor}\end{center}
  }
  \begin{center}
    \setlength{\hit@title@width}{4em}
    \heiti\xiaosi
    \ifhit@shenzhen%
      \begin{tabular}{rl}%
    \else%
      \begin{tabular}{rc}%
    \fi%
        {\hit@put@title{%
          \ifhit@harbin%
            \hit@bachelor@caffiltitle%
          \else%
            \ifhit@shenzhen%
              \hit@bachelor@caffiltitlesz%
            \else%
              \ifhit@weihai%
                \hit@bachelor@caffiltitlewh%
              \fi%
            \fi%
          \fi%
        }\hit@title@csep} & \hit@caffil\\[14pt]
{\hit@put@title{\hit@bachelor@cstudentidtitle}\hit@title@csep} & \hit@cstudentid
    \end{tabular}
    \ifhit@shenzhen%
      \begin{tabular}{rl}%
    \else%
      \begin{tabular}{rc}%
    \fi%
{\hit@put@title{\hit@bachelor@cmajortitle}\hit@title@csep} & \hit@csubject\\[14pt]
{\hit@put@title{\hit@bachelor@csupervisortitle}\hit@title@csep} &  \hit@csupervisor
      \end{tabular}
    \end{center}
    \vspace{2.6cm}
    {\xiaosi[0]\songti\textbf{\hit@cdate}}
  \end{center}
}
\newcommand{\hit@second@titlepage@bachelor}{
  \vspace*{0.8cm}
  \ifhit@harbin%
  \centering{\includegraphics[width=6.2cm]{hitlogo}}
  \else%
  \ifhit@shenzhen%
  \centering{\includegraphics[width=6.2cm]{hitlogo}~~\raisebox{0.2em}{\kaishu\yihao\hit@shenzhencampus}}
  \else%
  \ifhit@weihai%
  \centering{\includegraphics[width=6.2cm]{hitlogo}~~\raisebox{0.2em}{\kaishu\yihao\hit@weihaicampus}}
  \fi%
  \fi%
  \fi%
  \vspace{1.3cm}
  \begin{center}
    \centering\includegraphics[width=10.5cm]{bthesistitle}
    \vfill
    \parbox[t][14.2cm][b]{\textwidth}
    {\heiti\xiaosan
      \begin{center} \renewcommand{\arraystretch}{2.5} \heiti
\setlength{\hit@title@width}{5.5em}
\begin{tabular}{l@{\ \  }c}

  {\xiaoer  \hit@put@title{\hit@bachelor@cthesistitle}} & \underline{\makebox[6.1cm]{\xiaoer \hit@ctitleone}}\\
     &  \underline{\makebox[6.1cm]{\xiaoer \hit@ctitletwo}}\\
    & \\
  {\hit@put@title{\hit@bachelor@cmajortitle}}                  & \underline{\makebox[6.1cm]{\hit@csubject}}\\
  {\hit@put@title{\hit@bachelor@cstudentidtitle}}                  & \underline{\makebox[6.1cm]{\hit@cstudentid}}\\
  {\hit@put@title{\hit@bachelor@cstudenttitle}}                  & \underline{\makebox[6.1cm]{\hit@cauthor}}\\
  {\hit@put@title{\hit@bachelor@csupervisortitle}} & \underline{\makebox[6.1cm]{\hit@csupervisor}}\\
  {\hit@put@title{\hit@cdatetitle}} & \underline{\makebox[6.1cm]{\hit@cdate}}
\end{tabular} \renewcommand{\arraystretch}{1}
      \end{center}
    }
  \end{center}
}

\newlength{\hit@etitlelength}%
\newcommand{\hit@first@titlepage@other}{
  % 封面一
\ifthenelse%
{\equal{\hit@fontset}{siyuan}}%
{\xiaosi[1]\vspace*{0.65em}}%
{\xiaosi[1]\textcolor[rgb]{1,1,1}{\songti{\hit@hi}}}%
 \vspace*{1.2cm}
\begin{center}
  \begin{center}\xiaoyi[1]\songti\textbf{\hit@cxuewei\hit@cthesisname}\end{center}
    \ifhit@fulltime\vspace{1.4cm}\else%
      \begin{center}\xiaoyi[1]\songti\textbf{\hit@cbraceleft\hit@cstudenttype\hit@cbraceright}\end{center}
    \fi%
    \parbox[t][7.8cm][t]{\textwidth}{%
  \begin{center}\erhao\heiti\hit@ctitlecover\end{center}
\ifhit@subtitle\begin{center}\hspace{-4em}\xiaoer\heiti\pozhehao\hit@csubtitle\end{center}\fi
  \begin{center}%
    \settowidth{\hit@etitlelength}{\erhao\hit@etitle\ifhit@subtitle\hit@title@esep\hit@esubtitle\fi}%
    \ifdim\hit@etitlelength>450mm\xiaoer\else\erhao\fi%
    \textbf{\MakeUppercase{\hit@etitle}%
\ifhit@subtitle\hit@title@esep\MakeUppercase{\hit@esubtitle}\fi}\end{center}}

    \parbox[t][7.4cm][t]{\textwidth}{
  \begin{center}\xiaoer\songti\textbf{\hit@cauthor}\end{center}}
    \parbox[t][1.4cm][t]{\textwidth}{
  \begin{center}\kaishu\xiaoer\textbf{\hit@cschoolname}\end{center}}
    {\songti\xiaoer\textbf{\hit@cdate}}
\end{center}
}

\newcommand{\hit@second@titlepage@other}{
  \begin{center}
    {\songti \xiaosi
      \begin{tabular}{@{}r@{：}l@{}}
\hit@natclassifiedindextitle & \hit@natclassifiedindex\\
\hit@internatclassifiedindextitle & \hit@intclassifiedindex
    \end{tabular}}\hfill
    {\songti \xiaosi
      \begin{tabular}{@{}r@{：}l@{}}
\hit@schoolidtitle & \hit@schoolid\\
\hit@secretlevel & \hit@statesecrets
    \end{tabular}}
  \parbox[t][3.2cm][t]{\textwidth}{\begin{center} \end{center} }
    \parbox[t][2.4cm][t]{\textwidth}{\xiaoer[1]
  \begin{center}\songti\bfseries\hit@cdegree\hit@cthesisname\end{center}
      \ifhit@fulltime\relax\else\begin{center}\songti\textbf{\hit@cbraceleft\hit@cstudenttype\hit@cbraceright}\end{center}\fi}
\parbox[t][5cm][t]{\textwidth}{\erhao
  \begin{center}\heiti\hit@ctitlecover\end{center}
\ifhit@subtitle\begin{center}\hspace{-4em}\xiaoer\heiti\pozhehao\hit@csubtitle\end{center}\fi}
    \parbox[t][9.8cm][b]{\textwidth}
    {\sihao
      \setlength{\hit@title@width}{6em}
      \begin{center} \renewcommand{\arraystretch}{1.62} \songti
\begin{tabular}{l@{\hit@title@csep}l}
  {\heiti \hit@put@title{\hit@cauthortitle}} & \hit@cauthor\\
  {\heiti \hit@put@title{\hit@csupervisortitle}} & \hit@csupervisor\\
        \ifx\hit@cassosupervisor\@empty\else%
  {\heiti \hit@put@title{\hit@cassosupervisortitle}}& \hit@cassosupervisor\\
        \fi
        \ifx\hit@ccosupervisor\@empty\else%
  {\heiti \hit@put@title{\hit@ccosupervisortitle}} & \hit@ccosupervisor\\
        \fi
  {\heiti \hit@put@title{\hit@cdegreetitle}} & \hit@cdegree\\
  {\heiti \hit@put@title{\hit@csubjecttitle}} & \hit@csubject\\
  {\heiti \hit@put@title{\hit@caffiltitle}} & \hit@caffil\\
  {\heiti \hit@put@title{\hit@cdatetitle}} & \hit@cdate\\
  {\heiti \hit@put@title{\hit@cschoolnametitle}} & \hit@cschoolname
\end{tabular} \renewcommand{\arraystretch}{1}
    \end{center} }
  \end{center}
}
\newcommand{\emultiline}[2][c]{\renewcommand{\arraystretch}{1}\begin{tabular}[#1]{@{}l@{}}#2\end{tabular} \renewcommand{\arraystretch}{1.3}}
\newcommand{\hit@engcover}{
  {
    \xiaosi[1.667]\noindent Classified Index: \hit@natclassifiedindex \\[8pt]
  U.D.C:  \hit@intclassifiedindex }
  \vspace*{1em}
  \begin{center}
  \parbox[t][1.6cm][t]{\textwidth}{\begin{center} \end{center} }
    \parbox[t][3.5cm][t]{\textwidth}{\xiaoer[1]
  \begin{center}Dissertation for the {\hit@exueweier} Degree in \hit@exueke\end{center}
      \ifhit@fulltime\relax\else\begin{center}\hit@ebraceleft\hit@estudenttype\hit@ebraceright\end{center}\fi} %与中文保持一致，删除in {\hit@exueke}
    \parbox[t][7cm][t]{\textwidth}{%
   \begin{center}%
    \settowidth{\hit@etitlelength}{\erhao\hit@etitle\ifhit@subtitle\hit@title@esep\hit@esubtitle\fi}%
    \ifdim\hit@etitlelength>450mm\xiaoer\else\erhao\fi%
    \textbf{\MakeUppercase{\hit@etitle}%
\ifhit@subtitle\hit@title@esep\MakeUppercase{\hit@esubtitle}\fi}\end{center}}
    %★★★★若信息内容不太长，不会引起信息内容分行时，使用tabular环境，否则使用下面的tabularx环境。
    {\sihao\renewcommand{\arraystretch}{1.3}
      \begin{tabular}{@{}l@{~}l@{}}
\textbf{\hit@eauthortitle\hit@title@esep} & \hit@eauthor\\
\textbf{\hit@esupervisortitle\hit@title@esep} & \hit@esupervisor\\
      \ifx\hit@eassosupervisor\@empty\else%
\textbf{\hit@eassosupervisortitle\hit@title@esep} & \hit@eassosupervisor\\
      \fi
      \ifx\hit@ecosupervisor\@empty\else%
\textbf{\hit@ecosupervisortitle\hit@title@esep} & \hit@ecosupervisor\\
      \fi
\textbf{\hit@edegreetitle\hit@title@esep} & \hit@edegree\\
      \textbf{\hit@esubjecttitle\hit@title@esep} &\hit@esubject\\
\textbf{\hit@eaffiltitle\hit@title@esep} &\hit@eaffil\\
\textbf{\hit@edatetitle\hit@title@esep} & \hit@edate\\
\textbf{\hit@eschoolnametitle\hit@title@esep} & \hit@eschoolname
    \end{tabular}\renewcommand{\arraystretch}{1}}
  \end{center}
}

\def\makecover{
  \phantomsection
  \pdfbookmark[0]{\hit@ctitle}{ctitle}
  \xiaosi[1]%
  \begin{titlepage}
    \hit@first@titlepage
    \ifhit@library\clearpage\else\cleardoublepage\fi
    \hit@second@titlepage
    \ifhit@library\clearpage\else\cleardoublepage\fi
    \ifhit@bachelor
    \relax
    \else
    \phantomsection
    \pdfbookmark[0]{\hit@etitle}{etitle}
    \hit@engcover
    \ifhit@library\clearpage\else\cleardoublepage\fi
    \fi
  \end{titlepage}
  \normalsize
  \hit@makeabstract}
\newbox\hit@kw
\newcommand\hit@put@keywords[2]{%
  \begingroup
    \setbox\hit@kw=\hbox{#1}
    \noindent\hangindent\wd\hit@kw\hangafter1%
    \box\hit@kw#2\par
  \endgroup}




\newcommand{\hit@makeabstract}{%
  \ifhit@openright\cleardoublepage\else\clearpage\fi
  \hit@appendix@chapter*{\cabstractcname}[\cabstractename]
  \pagestyle{hit@headings}
  \pagenumbering{Roman}
  \hit@cabstract
  \vskip12bp
  \hit@put@keywords{\heiti\hit@ckeywords@title}{\hit@ckeywords}
  \ifhit@openright\cleardoublepage\else\clearpage\fi
  \hit@appendix@chapter*{\eabstractcname}[\eabstractename]
  \hit@eabstract
  \vskip12bp
  \hit@put@keywords{\textbf{Keywords:\enskip}}{\hit@ekeywords}}


\newenvironment{hitnomenclature}[1][2.5cm]{%
  \ifhit@openright\cleardoublepage\else\clearpage\fi
  \hit@appendix@chapter*{\hit@nomenclature@etitle}}{}%



\newenvironment{denotation}[1][2.5cm]{%
  \ifhit@openright\cleardoublepage\else\clearpage\fi
  \hit@appendix@chapter*{\hit@denotation@ctitle}[\hit@denotation@etitle]
\setcounter{table}{0}
\renewcommand{\thetable}{\arabic{table}}%使表编号为 1 的格式
  }{\renewcommand{\thetable}{\arabic{chapter}-\arabic{table}}%使表编号为 7-1 的格式
\setcounter{table}{0}}%

\def\hit@starttoc#1{% #1: float type, prepend type name in \listof*** entry.
  \let\oldnumberline\numberline
  \def\numberline##1{\oldnumberline{\csname #1name\endcsname\hskip.4em ##1}}
  \@starttoc{\csname ext@#1\endcsname}
  \let\numberline\oldnumberline}
\def\hit@listof#1#2{% #1: float type
\chapter*{\csname list#1name\endcsname}[#2]\hit@starttoc{#1}}

\renewcommand\listoffigures{\hit@listof{figure}{\listfigureename}}
\renewcommand*\l@figure{\addvspace{6bp}\@dottedtocline{1}{0em}{4em}}
\renewcommand\listoftables{\hit@listof{table}{\listtableename}}
\let\l@table\l@figure
\def\ext@equation{loe}
\def\equcaption#1{%
  \addcontentsline{\ext@equation}{equation}%
                  {\protect\numberline{#1}}}
\newcommand\listofequations{\hit@listof{equation}{\listequationename}}
\let\l@equation\l@figure
\setcounter{secnumdepth}{3}
\setcounter{tocdepth}{2}
\ifhit@bachelor\ifhit@tocfour\setcounter{tocdepth}{3}\fi\fi
\renewcommand\tableofcontents{%
\ifhit@openright\cleardoublepage\else\clearpage\fi
\phantomsection
\markboth{\contentsname}{ccontent}
\hit@chapter*{\contentsname}
\pdfbookmark[0]{\contentsname}{ccontent}
\normalsize\@starttoc{toc}}
\ifhit@arialtoc
  \def\hit@toc@font{\sffamily}
\fi
\def\@pnumwidth{4em}%规定中的提前悬挂
\def\@tocrmarg{\@pnumwidth}
\def\@dotsep{1}
\setlength\@tempdima{4em}%
\patchcmd{\@dottedtocline}{#4}{\csname hit@toc@font\endcsname #4}{}{}
\patchcmd{\@dottedtocline}{\hb@xt@\@pnumwidth}{\hbox}{}{}
\renewcommand*\l@chapter[2]{%
  \ifnum \c@tocdepth >\m@ne
    \addpenalty{-\@highpenalty}%
    %\vskip 4bp \@plus\p@
    \begingroup
      \parindent \z@ \rightskip \@pnumwidth
      \parfillskip -\@pnumwidth
      \leavevmode
      \advance\leftskip\@tempdima
      \hskip -\leftskip
      % numberline is called here, and it uses \@tempdima
      {\ifhit@bachelor\rmfamily\else\csname
        hit@toc@font\endcsname\fi\heiti\ifhit@english\bfseries\fi #1}
      \leaders\hbox{$\m@th\mkern \@dotsep mu\hbox{.}\mkern \@dotsep mu$}\hfill
      \nobreak{\normalfont\normalcolor #2}\par
      \penalty\@highpenalty
    \endgroup
  \fi}
\renewcommand*\l@section{\@dottedtocline{1}{1em}{1.8em}}
\renewcommand*\l@subsection{\@dottedtocline{2}{2em}{2.5em}}
\renewcommand*\l@subsubsection{\@dottedtocline{3}{3\ccwd}{3.1em}}
\def\@dotsep{0.75}           % 定义英文目录的点间距
\setlength\leftmargini {0pt}
\setlength\leftmarginii {0pt}
\setlength\leftmarginiii {0pt}
\setlength\leftmarginiv {0pt}
\setlength\leftmarginv {0pt}
\setlength\leftmarginvi {0pt}

\def\engcontentsname{\bfseries Contents}
\newcommand\tableofengcontents{
  \def\l@chapter{\@dottedtocline{0}{0em}{5em}}%控制英文目录： 细点\@dottedtocline  粗点\@dottedtoclinebold
  \@restonecolfalse
  \chapter*{\engcontentsname  %chapter*上移一行，避免在toc中出现。
  \pdfbookmark[0]{Contents}{econtent}
    \@mkboth{%
  \engcontentsname}{\engcontentsname}}
  \@starttoc{toe}%
  \if@restonecol\twocolumn\fi}
\def\@dotsep{0.75}           % 定义英文目录的点间距
\ctexset{%
  appendix/number=\ifhit@bachelor\arabic{chapter}\else\Alph{chapter}\fi,
}
\let\hit@appendix\appendix
\renewenvironment{appendix}{%
  \let\title\hit@appendix@title
  \hit@appendix
  \ifhit@bachelor\renewcommand{\thechapter}{\arabic{chapter}}\fi
  }{%
  \let\title\@gobble}
\let\title\@gobble
\newcommand{\hit@appendix@title}[1]{%
  \begin{center}
    \bfseries\xiaosi #1
  \end{center}}
\newlist{translationbib}{enumerate}{1}
\setlist[translationbib]{label=[\arabic*],align=left,nosep,itemsep=6bp,
  leftmargin=10mm,labelsep=!,before=\vspace{0.5\baselineskip}\wuhao[1.3]}

\newenvironment{conclusions}{%
\ifhit@openright\cleardoublepage\else\clearpage\fi
  \hit@appendix@chapter*{\hit@conclusion@ctitle}[\hit@conclusion@etitle]}{}
\newenvironment{acknowledgements}{%
  \ifhit@openright\cleardoublepage\else\clearpage\fi
  \hit@appendix@chapter*{\hit@acknowledgement@ctitle}[\hit@acknowledgement@etitle]
}{}
\newenvironment{resume}{%
  \ifhit@openright\cleardoublepage\else\clearpage\fi
  \hit@appendix@chapter*{\hit@resume@ctitle}[\hit@resume@etitle]}{}
\newenvironment{publication}{%
  \ifhit@openright\cleardoublepage\else\clearpage\fi
  \hit@appendix@chapter*{\hit@publication@ctitle}[\hit@publication@etitle]}{}
\newenvironment{ceindex}{%
  \ifhit@openright\cleardoublepage\else\clearpage\fi
  \hit@appendix@chapter*{\indexname}[\hit@index@etitle]
  \setlength{\columnsep}{4em}
  \begin{adjustwidth}{2em}{2em}
  \begin{multicols*}{2}}{\end{multicols*}
  \end{adjustwidth}
  }

\newlist{idxwordlist}{description}{3}
\setlist[idxwordlist, 1]{%
  itemsep=\baselineskip,
  labelindent=8em,
  font=\normalsize\bfseries,
}
\setlist[idxwordlist, 2]{%
  nosep,
  labelindent=2em,
  font=\wuhao\rm,
}
\setlist[idxwordlist, 3]{%
  nosep,
  labelindent=4em,
  font=\wuhao\rm,
}

\def\hit@authorization@other{%
  \ifhit@openright\cleardoublepage\else\clearpage\fi
  \hit@appendix@chapter*{\hit@authorization@ctitle}[\hit@authorization@etitle]
  \xiaosi[1.6]\vspace{\baselineskip}
\begin{center}\xiaosan\heiti\hit@declarename\end{center}
\par\hit@declaretext
\vspace{\baselineskip}
\par\hspace{6em}\hit@authorsig\hfill\hit@frontdate\hit@datefill
\vspace{2\baselineskip}
\begin{center}\xiaosan\heiti\hit@authorizationtitle\end{center}
\par\hit@authorizationtext
\vspace{2\baselineskip}
\par\hspace{6em}\hit@authorsig\hfill\hit@frontdate\hit@datefill
\vspace{2\baselineskip}
\par\hspace{6em}\hit@teachersig\hfill\hit@frontdate\hit@datefill}
\def\hit@authorization@bachelor{%
  \ifhit@openright\cleardoublepage\else\clearpage\fi
  \hit@appendix@chapter*{\hit@declarename@bachelor}
  \hit@authorizationtext@bachelor
\vspace{2\baselineskip}
\par\hspace{6em}\hit@authorsig\hfill\hit@frontdate\hit@datefill
}

\NewDocumentCommand{\authorization}{o}{%
  \IfNoValueTF{#1}{%
    \ifhit@bachelor\hit@authorization@bachelor\else\hit@authorization@other\fi
    }{%
    \includepdf[fitpaper=true,pagecommand={%
\thispagestyle{hit@empty}%
\phantomsection\addcontentsline{toc}{chapter}{\ifhit@bachelor\hit@declarename@bachelor\else\hit@authorization@ctitle\fi}%
\ifhit@doctor%
\addcontentsline{toe}{chapter}{\texorpdfstring{\bfseries \hit@authorization@etitle}{\hit@authorization@etitle}}%
\fi%
    }]{#1}%
  }%
}

\newcommand\bibstyle@numerical{\bibpunct{[}{]}{,}{s}{,}{\textsuperscript{,}}}
\newcommand\bibstyle@authoryear{\bibpunct{(}{)}{;}{a}{,}{,}}
\newcommand\bibstyle@inline{\bibpunct{[}{]}{,}{n}{,}{\hit@inline@sep}}
\citestyle{numerical}
\DeclareRobustCommand\inlinecite{\@inlinecite}
\def\@inlinecite#1{\begingroup\citestyle{inline}\let\@cite\NAT@citenum\citep{#1}\endgroup}
\let\onlinecite\inlinecite
\renewenvironment{thebibliography}[1]{%
  \ifhit@openright\cleardoublepage\else\clearpage\fi\phantomsection%
  \hit@appendix@chapter*{\bibname}[\hit@bibname@etitle]
  \normalsize
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
{\def\@noitemerr
  {\@latex@warning{Empty `thebibliography' environment}}%
\endlist\frenchspacing}
\patchcmd\NAT@citexnum{%
  \@ifnum{\NAT@ctype=\z@}{%
    \if*#2*\else\NAT@cmt#2\fi
  }{}%
  \NAT@mbox{\NAT@@close}%
}{%
  \NAT@mbox{\NAT@@close}%
  \@ifnum{\NAT@ctype=\z@}{%
    \if*#2*\else\textsuperscript{#2}\fi
  }{}%
}{}{}
\renewcommand\NAT@citesuper[3]{\ifNAT@swa
  \if*#2*\else#2\NAT@spacechar\fi
\unskip\kern\p@\textsuperscript{\NAT@@open#1\NAT@@close\if*#3*\else#3\fi}%
   \else #1\fi\endgroup}
\patchcmd{\NAT@citex}{%
  \if*#2*\else\NAT@cmt#2\fi
  \if\relax\NAT@date\relax\else\NAT@@close\fi
}{%
  \if\relax\NAT@date\relax\else\NAT@@close\fi
  \if*#2*\else\textsuperscript{#2}\fi
}{}{}
\renewcommand\NAT@cite%
    [3]{\ifNAT@swa\NAT@@open\if*#2*\else#2\NAT@spacechar\fi
        #1\NAT@@close\if*#3*\else\textsuperscript{#3}\fi\else#1\fi\endgroup}
\AtEndOfClass{\input{hithesis.cfg}}
\AtEndOfClass{\sloppy}
\endinput
%%
%% End of file `hithesis.cls'.
