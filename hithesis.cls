\NeedsTeXFormat{LaTeX2e}[1999/12/01]
\ProvidesClass{hithesis}[2017/05/23 0.0.0 Harbin Institute of Technology Thesis Template]

%%%{{{ Package
\RequirePackage{ifthen}
\RequirePackage{kvoptions}
\SetupKeyvalOptions{
  family=hit,
  prefix=hit@,
  setkeys=\kvsetkeys}
\newif\ifhit@bachelor % 定义一个布尔变量
\newif\ifhit@master
\newif\ifhit@doctor
\newif\ifhit@postdoctor
\define@key{hit}{type}{%
  \hit@bachelorfalse %默认都是false
  \hit@masterfalse
  \hit@doctorfalse
  \hit@postdoctorfalse
  \expandafter\csname hit@#1true\endcsname} %含有选项的设为true

%%手动载入字体选项，为了兼容更多的系统
\newif\ifhit@winxp
\define@key{hit}{os}{%
  \hit@winxpfalse
  \expandafter\csname hit@#1true\endcsname}

\def\hit@deprecated@type@option{%
  \kvsetkeys{hit}{type=\CurrentOption} % for compatability.
  \ClassError{hithesis}{Option '\CurrentOption' is deprecated, \MessageBreak
                         please use 'type=\CurrentOption' instead}{}}
%\DeclareVoidOption{bachelor}{\hit@deprecated@type@option}
%\DeclareVoidOption{master}{\hit@deprecated@type@option}
%\DeclareVoidOption{doctor}{\hit@deprecated@type@option}
%\DeclareVoidOption{postdoctor}{\hit@deprecated@type@option}
\DeclareBoolOption{secret}
\DeclareBoolOption{arialtoc}
\DeclareBoolOption{arialtitle}
\DeclareBoolOption{raggedbottom}
\DeclareBoolOption{pifootnote}
\DeclareBoolOption{glue}
\DeclareBoolOption{tocfour}
\DeclareStringOption{fontset}

\DeclareDefaultOption{\PassOptionsToClass{\CurrentOption}{ctexbook}}
\kvsetkeys{hit}{raggedbottom}
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

\LoadClass[zihao=-4,openany,UTF8,scheme=plain]{ctexbook}

\ifhit@bachelor\relax\else
  \ifhit@master\relax\else
    \ifhit@doctor\relax\else
      \ifhit@postdoctor\relax\else
        \ClassError{hithesis}%
                   {Please specify thesis type in option: \MessageBreak
                    type=[bachelor | master | doctor | postdoctor]}{}
      \fi
    \fi
  \fi
\fi

\RequirePackage{etoolbox}% 提供常用命令的包
\RequirePackage{ifxetex}% 检验引擎是不是xetex

\ifxetex
\else
        \ClassError{hithesis}%
                   {Please use: \MessageBreak
                    xelatex}{}
\fi


\RequirePackage{xparse}


\RequirePackage{amsmath}        % AMSLaTeX宏包 用来排出更加漂亮的公式

\RequirePackage[defaultsups]{newtxtext}
\RequirePackage{newtxmath}
\RequirePackage{courier}

\RequirePackage{graphicx}
%\RequirePackage[labelformat=simple]{subcaption} 比subfigure 更好？
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

\RequirePackage{CJKfntef} % 汉字加点，分散对齐功能
\RequirePackage[amsmath,thmmarks,hyperref]{ntheorem}% 定理类环境宏包，其中 amsmath 选项用来兼容 AMS LaTeX 的宏包
%\RequirePackage{array}
\RequirePackage{longtable}      %支持跨页的表格。
\RequirePackage{booktabs}       % 表格，横的粗线；\specialrule{1pt}{0pt}{0pt}
\RequirePackage[sort&compress,numbers]{natbib}% 支持引用缩写的宏包

\RequirePackage{hyperref}
\ifxetex
  \hypersetup{%
    CJKbookmarks=true}
\else
  \hypersetup{%
    unicode=true,
    CJKbookmarks=false}
\fi
\hypersetup{%
  linktoc=all,
  bookmarksnumbered=true,
  bookmarksopen=true,
  bookmarksopenlevel=1,
  breaklinks=true,
  colorlinks=false,
  plainpages=false,
  pdfborder=0 0 0}
\urlstyle{same}  %论文中引用的网址的字体默认与正文中字体不一致，这里修正为一致的。
\RequirePackage{geometry}
\geometry{%根据PlutoThesis 原版定义而来
  a4paper, % 210 * 297mm
  hcentering,
  ignoreall,
  nomarginpar,
  text={150true mm,224true mm},
  top=35.5true mm,
  left=30true mm,
  head=5true mm,
  headsep=2.5true mm,
  foot=8.5true mm
}
\RequirePackage{layout}

\RequirePackage{fancyhdr}                   % fancyhdr宏包 页眉和页脚的相关定义
\let\hit@cleardoublepage\cleardoublepage
\newcommand{\hit@clearemptydoublepage}{%
  \clearpage{\pagestyle{hit@empty}\hit@cleardoublepage}
}
\let\cleardoublepage\hit@clearemptydoublepage

\renewcommand\frontmatter{%
  \if@openright\cleardoublepage\else\clearpage\fi
  \@mainmatterfalse
  \pagenumbering{Roman}
  \pagestyle{hit@empty}
}

\renewcommand\mainmatter{%
  \addtocontents{toc}{\vspace{\baselineskip}} %规范中并没有这一要求，此处不应该加
  \addtocontents{toe}{\vspace{\baselineskip}}
  \if@openright\cleardoublepage\else\clearpage\fi
  \@mainmattertrue
  \pagenumbering{arabic}
  \pagestyle{hit@headings}
}

\renewcommand\backmatter{%
  \if@openright\cleardoublepage\else\clearpage\fi
  \@mainmattertrue}

\RequirePackage{tabularx}
\RequirePackage{color}          % 支持彩色
\RequirePackage{amssymb}
\RequirePackage[below]{placeins}%允许上一个section的浮动图形出现在下一个section的开始部分,还提供\FloatBarrier命令,使所有未处理的浮动图形立即被处理
\RequirePackage{flafter}       % 使得所有浮动体不能被放置在其浮动环境之前，以免浮动体在引述它的文本之前出现.
\RequirePackage{multirow}       %使用Multirow宏包，使得表格可以合并多个row格
\RequirePackage[hang]{subfigure}%支持子图 %centerlast 设置最后一行是否居中
\RequirePackage[subfigure]{ccaption} %支持双语标题

\RequirePackage{varwidth}
\RequirePackage{multicol}
\RequirePackage[makeindex]{splitidx}
\newindex[]{china}
\newindex[]{english}


\RequirePackage[boxed,linesnumbered,algochapter]{algorithm2e}  % 算法的宏包，注意宏包兼容性，先后顺序为float、hyperref、algorithm(2e)，否则无法生成算法列表
\RequirePackage{xltxtra}
\RequirePackage{listings}
\lstset{
%basicstyle=\small\ttfamily,
columns=flexible,
breaklines=true
}


%%%}}}

%%%{{{ Font
% 1bp = 1.00374pt
% 1mm = 2.84526pt
%按照窝工之要求, 行距在3mm～4mm之间，换算之后为20.50398～23.33863bp
% 换算公式为：
%((3 * 2.84526) / (12 * 1.00374) + 1) * 12 bp
%((4 * 2.84526) / (12 * 1.00374) + 1) * 12 bp
%所以改为默认21bp
%注意，原PlutoThesis 的1.67倍行距，是20.04bp, 小于规定最小值0.46398bp
%这里设置为glue， 可能会不美观
%或者直接设置为21bp更好。
%此处应该给出一个设置选项

\renewcommand\normalsize{%
  \@setfontsize\normalsize{12bp}{\ifhit@glue 20.50398bp \@plus 2.83465bp \@minus 0bp\else 21bp\fi}%
  \abovedisplayskip=4pt
  \abovedisplayshortskip=4pt
  \belowdisplayskip=\abovedisplayskip
  \belowdisplayshortskip=\abovedisplayshortskip}

\predisplaypenalty=0  %公式之前可以换页，公式出现在页面顶部

\def\hit@def@fontsize#1#2{%
  \expandafter\newcommand\csname #1\endcsname[1][1.3]{%
    \fontsize{#2}{##1\dimexpr #2}\selectfont}}

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
%%%}}}

%%{{{ header footer
\fancypagestyle{hit@empty}{%
  \fancyhf{}
  \renewcommand{\headrulewidth}{0pt}
  \renewcommand{\footrulewidth}{0pt}
}

\fancypagestyle{hit@plain}{%
  \fancyhead{}
  \fancyfoot[C]{\xiaowu\thepage}
  \renewcommand{\headrulewidth}{0pt}
  \renewcommand{\footrulewidth}{0pt}
}

\fancypagestyle{hit@headings}{%
  \fancyhf{}
  \ifhit@doctor
  \fancyhead[CO]{\songti\xiaowu[0]\leftmark}
  \fancyhead[CE]{\songti\xiaowu[0]\hit@cschoolname\hit@cdegree\hit@cthesisname}%
  \else
  \ifhit@master
  \fancyhead[C]{\songti\xiaowu[0]\hit@cschoolname\hit@cdegree\hit@cthesisname}
  \fi
  \ifhit@bachelor
  \fancyhead[C]{\songti\xiaowu[0]\hit@cschoolname\hit@bachelor@cxuewei\hit@bachelor@cthesisname}%
  \fi
  \fi
  \fancyfoot[C,C]{\xiaowu -~\thepage~-}
  % 此处可能和word模板不一致
  % 页眉中小五汉字，0行距时，占用9bt，页眉高度为14pt, 所以以下数字之和要保持等于14pt-9bt=4.96634pt
  % 根据PlutoThesis模板中rule宽度定义为2.25， 0.75， 保持粗线和细线之间的间距为细线宽度。
  % 如果页眉是多行的情况，rule向下溢出
  \renewcommand{\headrule}{
    \vskip 1.190132pt
    \hrule\@height2.276208pt\@width\headwidth
    \vskip 0.75pt
    \hrule\@height.75pt\@width\headwidth
  }
  \renewcommand{\footrulewidth}{0pt}
}

\AtBeginDocument{%
  \pagestyle{hit@empty}
  \renewcommand{\chaptermark}[1]{\@mkboth{\CTEXthechapter\enspace#1}{}}}
%%%}}}

%%%{{{段落
\ctexset{%
  punct=quanjiao,
  space=auto,
  autoindent=true}
\setlist{nosep}
%%%}}}

%%%{{{脚注
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


%%%{{{ 数学公式
\allowdisplaybreaks[4]
\renewcommand\theequation{\ifnum \c@chapter>\z@ \thechapter-\fi\@arabic\c@equation}
%%%}}}

%%%{{{ Structure
\setlength{\floatsep}{\ifhit@glue 20.50398bp \@plus 2.83465bp \@minus 0bp\else 21bp\fi}
\setlength{\intextsep}{\ifhit@glue 20.50398bp \@plus 2.83465bp \@minus 0bp\else 21bp\fi}
\setlength{\textfloatsep}{\ifhit@glue 20.50398bp \@plus 2.83465bp \@minus 0bp\else 21bp\fi}
\setlength{\@fptop}{0bp}
\setlength{\@fpsep}{12bp}
\setlength{\@fpbot}{0bp}
\renewcommand{\textfraction}{0.15}
\renewcommand{\topfraction}{0.85}
\renewcommand{\bottomfraction}{0.65}
\renewcommand{\floatpagefraction}{0.60}


%这里减少一个字符高度
\let\hit@oldfigure\figure
\let\hit@oldendfigure\endfigure
\def\figure{\begingroup\hit@oldfigure}
\def\endfigure{\vskip-1em\hit@oldendfigure\endgroup}
\let\hit@oldtable\table
\let\hit@oldendtable\endtable
\def\table{\begingroup\hit@oldtable}
\def\endtable{\vskip-1em\hit@oldendtable\endgroup}


%\long\def\@caption#1[#2]#3{%
%  \par
%  \addcontentsline{\csname ext@#1\endcsname}{#1}%
%  {\protect\numberline{\csname the#1\endcsname}{\ignorespaces #2}}%
%  \begingroup
%  \@parboxrestore
%  \if@minipage
%  \@setminipage
%  \fi
%  \normalsize
% \newlength{\hit@captionlength}
%  \settowidth{\hit@captionlength}{#3}
%  \ifdim\hit@captionlength>300mm\xiaowu[1.667]\else\wuhao[1.667]\fi
%  \@makecaption{\csname fnum@#1\endcsname}{\ignorespaces #3\the\hit@captionlength}\par % <----
%\endgroup}


\newlength{\hit@captionlength}
\long\def\@makecaption#1#2{%
  \settowidth{\hit@captionlength}{#2}
  \ifhit@bachelor\wuhao[1.667]\else\ifdim\hit@captionlength>300mm\xiaowu[1.667]\else\wuhao[1.667]\fi\fi
  \vskip\abovecaptionskip
  \sbox\@tempboxa{#1\ifhit@bachelor\hskip\ccwd\else\enskip\fi#2}%
  \ifdim \wd\@tempboxa >\hsize
  #1\ifhit@bachelor\hskip\ccwd\else\enskip\fi#2\par
  \else
  \global \@minipagefalse
  \hb@xt@\hsize{\hfil\box\@tempboxa\hfil}%
  \fi
\vskip\belowcaptionskip}


%\ifhit@bachelor
%\g@addto@macro\appendix{\renewcommand*{\thefigure}{\thechapter-\arabic{figure}}}
%\g@addto@macro\appendix{\renewcommand*{\thetable}{\thechapter-\arabic{table}}}
%\fi
%\let\old@tabular\@tabular
%\def\hit@tabular{\dawu[1.5]\old@tabular}
%\DeclareCaptionLabelFormat{hit}{{\dawu[1.5]\normalfont
% #1~#2}}
%\DeclareCaptionLabelSeparator{hit}{\hspace{1em}}
%\DeclareCaptionFont{hit}{\dawu[1.5]}
%\captionsetup{labelformat=hit,labelsep=hit,font=hit}
%\captionsetup[table]{position=top,belowskip={12bp-\intextsep},aboveskip=6bp}
%\captionsetup[figure]{position=bottom,belowskip={12bp-\intextsep},aboveskip=6bp}
%\captionsetup[sub]{font=hit,skip=6bp}

\let\hit@LT@array\LT@array
\def\LT@array{\dawu[1.5]\hit@LT@array}
% set default font size

\renewcommand{\thesubtable}{(\alph{subtable})}
\renewcommand{\thefigure}{\arabic{chapter}-\arabic{figure}}%使图编号为 7-1 的格式 %\protect{~}
\renewcommand{\thesubfigure}{\alph{subfigure})}%使子图编号为 a)的格式
\renewcommand{\p@subfigure}{\thefigure~} %使子图引用为 7-1 a) 的格式，母图编号和子图编号之间用~加一个空格
\renewcommand{\thetable}{\arabic{chapter}-\arabic{table}}%使表编号为 7-1 的格式
\renewcommand{\theequation}{\arabic{chapter}-\arabic{equation}}%使公式编号为 7-1 的格式

\newcommand{\algoenname}{Algo.} %算法英文标题
\newfloatlist[chapter]{algoen}{aen}{\listalgoenname}{\algoenname}
\newfixedcaption{\algoencaption}{algoen}
\renewcommand{\thealgoen}{\thechapter-\arabic{algocf}}
\renewcommand{\@cftmakeaentitle}{\chapter*{\listalgoenname\@mkboth{\bfseries\listalgoenname}{\bfseries\listalgoenname}}
}

\renewcommand{\algorithmcfname}{算法}
\setlength\AlCapSkip{1.2ex}
\SetAlgoSkip{1pt}
\renewcommand{\algocf@captiontext}[2]{\wuhao#1\algocf@typo ~ \AlCapFnt{}#2} % text of caption
\expandafter\ifx\csname algocf@within\endcsname\relax% if \algocf@within doesn't exist
\renewcommand\thealgocf{\@arabic\c@algocf} % and the way it is printed
\else%                                    else
\renewcommand\thealgocf{\csname the\algocf@within\endcsname-\@arabic\c@algocf}
\fi
\renewcommand{\algocf@makecaption}[2]{%中英文双标题一定多于一行，因此去掉单行时的判断，并将\parbox中标题设置为居中
  \addtolength{\hsize}{\algomargin}%
  \sbox\@tempboxa{\algocf@captiontext{#1}{#2}}%
    \hskip .5\algomargin%
    \parbox[t]{\hsize}{\centering\algocf@captiontext{#1}{#2}}%
  \addtolength{\hsize}{-\algomargin}%
}
\newcommand{\AlgoBiCaption}[2]{%直接取出自定义的中英文标题条目加入到真正的\caption 中
   \caption[#1]{\protect\setlength{\baselineskip}{1.5em}#1 \protect \\ Algo. \thealgocf~~ #2} % \algoencaption{#2}
   \addcontentsline{aen}{algoen}{\protect\numberline{\thealgoen}{#2}}
}

  %%%}}}

   %%%{{{ Key for options
% 使用key-value 设置封面选项
\def\hit@def@term#1{%
  \define@key{hit}{#1}{\csname #1\endcsname{##1}}
  \expandafter\gdef\csname #1\endcsname##1{%
    \expandafter\gdef\csname hit@#1\endcsname{##1}}
  \csname #1\endcsname{}}

\hit@def@term{statesecrets} %密级
\hit@def@term{natclassifiedindex}  %国内图书分类号
\hit@def@term{internatclassifiedindex}  %国际图书分类号

\hit@def@term{ctitle} %中文标题
\hit@def@term{cxueke} %中文学科
\hit@def@term{cauthor} %中文作者
\hit@def@term{csupervisor} %中文导师
\hit@def@term{cassosupervisor} %中文副导师
\hit@def@term{ccosupervisor}%中文联合导师
\hit@def@term{caffil}%中文院系
\hit@def@term{csubject}%中文专业
\hit@def@term{cdate}

\hit@def@term{cstudentid}%
\hit@def@term{ctitleone}%
\hit@def@term{ctitletwo}%


\hit@def@term{etitle} %英文标题
\hit@def@term{exueke} %英文学科
\hit@def@term{eauthor} %英文作者
\hit@def@term{esupervisor} %英文导师
\hit@def@term{eassosupervisor} %英文副导师
\hit@def@term{ecosupervisor} %英文联合导师
\hit@def@term{eaffil}
\hit@def@term{esubject}
\hit@def@term{edate}

% for the other degree
%\hit@def@term{id}
%\hit@def@term{udc}
%\hit@def@term{catalognumber}
%\hit@def@term{cfirstdiscipline}
%\hit@def@term{cseconddiscipline}
%\hit@def@term{postdoctordate}


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
%%%}}}

\theoremstyle{plain}
\theorembodyfont{\songti\rmfamily}
\theoremheaderfont{\heiti\rmfamily}
\theoremsymbol{$\square$}
\setlength{\theorempreskipamount}{0pt}
\setlength{\theorempostskipamount}{-2pt}

\allowdisplaybreaks[4]
\setlength{\parindent}{2em}
\arraycolsep=1.6pt
\setcounter{secnumdepth}{4} \setcounter{tocdepth}{2}




\def\hit@title@font{%
  \ifhit@arialtitle\sffamily\else\heiti\fi}

\newcommand\hit@chapter@titleformat[1]{%开启悬挂缩进选项
    \ifthenelse%
      {\equal{#1}{\eabstractcname}}%
      {\bfseries #1}%
      %实现章标题的居中加悬挂缩进，注意，此处一定是\CTEX@chaptername\CTEX@chapter@aftername, 否则是英文标题长度
      {\settowidth{\hangindent}{\CTEX@chaptername\CTEX@chapter@aftername}\hangafter=1#1}%
      %{\begin{varwidth}[t]{\hit@chapter@indentboxwidth}#1\end{varwidth}}
}



%\def\@chapter[#1]#2{%
% \ifnum \c@secnumdepth >\m@ne
% \if@mainmatter
% \ifodd \CTEX@chapter@numbering
% \CTEX@ifnametrue
% \refstepcounter{chapter}%
% \typeout{\CTEXthechapter}%
% \else
% \CTEX@ifnamefalse
% \CTEX@makeanchor{\Hy@chapapp*}%
% \fi
% \else
% \CTEX@ifnamefalse
% \CTEX@makeanchor@chapter{\Hy@chapapp*}%
% \fi
% \else
% \CTEX@ifnamefalse
% \CTEX@makeanchor@chapter{\Hy@chapapp*}%
% \fi
% \CTEX@addtocline{chapter}{#1}%
% \chaptermark{#1}%
% \CTEX@addloflotskip{chapter}%
% \if@twocolumn
% \@topnewpage[\@makechapterhead{#2}]%
% \else
% \@makechapterhead{#2}%
% \@afterheading
% \fi}



% 窝工规定章标题行间距要10mm
% 1bp = 1.00374pt
% 1mm = 2.84526pt
% 小二号字体 18bp
% 所以行间距倍数为 (10 × 2.84526) / (18 × 1.00374) = 1.57481，
% 以上没问题
% 按照窝工硕博论文规范的规定： 章标题要段前空一行，段后空0.8行 （最好是给距离mm, bp, 给出一行……）
% 这就有了歧义： 空这一行，是什么格式？是标题的格式么？那么
% 为18 * (1 + 0.57481) = 23.17329bp
% 按照word的操作习惯规定应该是空行格式为章标题格式
% 本科规范中的格式是1.25倍行距
% word中的1.25倍行距是单倍行距的1.25倍。单倍行距是的固定值是某一个大于字体磅数的正数，这个正数对于不同的字体不一样，有一定的随机性，且此处规定与后文中的10mm间距矛盾，
% 由于这个行距是某一个不固定值，且本科生规范中含有了与硕博规范中一样的弹性区间规定（章节标题间距是固定值），所以这里不用单独设置这个1.25倍行距了。

% 这个值默认是两行，即章节标题之后至少两行，才可以分页
% 确保每一个章节提款标题之后保留一行就可以分页。
% 这样确保剩余空白不过大，且不会出现标题出现在页底的情况
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


\NewDocumentCommand{\hit@appendix@chapter}{s m o}{%
  \IfBooleanT{#1}%
  {
    \phantomsection
    \markboth{#2}{#2}
    \addcontentsline{toc}{chapter}{\ifhit@arialtitle\sffamily\heiti\else\heiti\fi #2}
    \IfValueT{#3}{\addcontentsline{toe}{chapter}{\bfseries #3}}
    \hit@chapter*{#2}
  }
}
 % 该附录命令适用于发表文章，简历等

\newcommand{\BiAppChapter}[2]    % 该附录命令适用于有章节的完整附录
{\phantomsection
 \chapter{#1}
 \addcontentsline{toe}{chapter}{\bfseries \xiaosi Appendix \thechapter~~#2}
}


% s: 星号，表示在目录中出不出现序号
% m: 必须要有的选项，中文章节名称也即目录中名称，页眉中名称，书签中的名称
% o: 可选内容，没有就默认是正文章节，如果有，则是英文目录中显示的内容。
\let\hit@chapter\chapter
\RenewDocumentCommand{\chapter}{s o m o}{%
  \if@openright\cleardoublepage\else\clearpage\fi\phantomsection%
  \IfBooleanTF{#1}%
  {%	if \chapter*
    \hit@chapter*{#3}%
    \IfValueT{#4}{%
      \addcontentsline{toe}{chapter}{\bfseries #4}
    }
  }%
  {%	if \chapter
    \IfNoValueTF{#2}%
    {\hit@chapter{#3}}%
    {\hit@chapter[#2]{#3}}%
    \IfValueT{#4}{%
    \addcontentsline{toe}{chapter}{\bfseries\relax Chapter \thechapter\hspace{0.5em} #4}
    }
  }
}

\let\hit@section\section
\RenewDocumentCommand\section{s o m o}{
  \IfBooleanTF{#1}%
  {%	if \section*
    \hit@section*{#3}%
    \IfValueT{#4}{%
      \addcontentsline{toe}{section}{#4}
    }
  }%
  {%	if \section
    \IfNoValueTF{#2}%
    {\hit@section{#3}}%
    {\hit@section[#2]{#3}}%
    \IfValueT{#4}{%
    \addcontentsline{toe}{section}{\protect\numberline{\csname thesection\endcsname} #4}
    }
  }
}

\let\hit@subsection\subsection
\RenewDocumentCommand\subsection{s o m o}{
  \IfBooleanTF{#1}%
  {%	if \subsection*
    \hit@subsection*{#3}%
    \IfValueT{#4}{%
      \addcontentsline{toe}{subsection}{#4}
    }
  }%
  {%	if \subsection
    \IfNoValueTF{#2}%
    {\hit@subsection{#3}}%
    {\hit@subsection[#2]{#3}}%
    \IfValueT{#4}{%
    \addcontentsline{toe}{subsection}{\protect\numberline{\csname thesubsection\endcsname} #4}
    }
  }
}

\let\hit@subsubsection\subsubsection
\RenewDocumentCommand\subsubsection{s o m o}{
  \IfBooleanTF{#1}%
  {%	if \subsubsection*
    \hit@subsubsection*{#3}%
    \IfValueT{#4}{%
      \addcontentsline{toe}{subsubsection}{#4}
    }
  }%
  {%	if \subsubsection
    \IfNoValueTF{#2}%
    {\hit@subsubsection{#3}}%
    {\hit@subsubsection[#2]{#3}}%
    \IfValueT{#4}{%
    \addcontentsline{toe}{subsubsection}{\protect\numberline{\csname thesubsubsection\endcsname} #4}
    }
  }
}

% 调整罗列环境的布局
\setitemize{leftmargin=0em,itemsep=0em,partopsep=0em,parsep=0em,topsep=0em,itemindent=3em}
\setenumerate{leftmargin=0em,itemsep=0em,partopsep=0em,parsep=0em,topsep=0em,itemindent=3.5em}
\newcommand{\citeup}[1]{\textsuperscript{\cite{#1}}}
% 定制浮动图形和表格标题样式

\captionnamefont{\wuhao[1.667]}
\captiontitlefont{\wuhao[1.667]}
\captiondelim{~~}
\hangcaption
\renewcommand{\subcapsize}{\wuhao[1.667]}
\setlength{\abovecaptionskip}{0pt}%为了双标题之间的间距，不能设置
\setlength{\belowcaptionskip}{0pt}

% 自定义项目列表标签及格式 \begin{publist} 列表项 \end{publist}

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
{\end{list}}%%%%%

% 定义封面
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
  \begin{center}\erhao[0]\heiti\hit@ctitle\end{center} }
    \parbox[t][9cm][t]{\textwidth}{
    \begin{center}\xiaoer[0]\songti\textbf{\hit@cauthor}\end{center}
  }
  \begin{center}
    \setlength{\hit@title@width}{4em}
    \heiti\xiaosi
      \begin{tabular}{rc}
	{\hit@put@title{\hit@bachelor@caffiltitle}\hit@title@csep} & \hit@caffil\\[14pt]
	{\hit@put@title{\hit@bachelor@cstudentidtitle}\hit@title@csep} & \hit@cstudentid
    \end{tabular}
      \begin{tabular}{rc}
	{\hit@put@title{\hit@bachelor@cmajortitle}\hit@title@csep} & \hit@csubject\\[14pt]
	{\hit@put@title{\hit@bachelor@csupervisortitle}\hit@title@csep} &  \hit@csupervisor
      \end{tabular}
    \end{center}
    \vspace{2.6cm}
    {\xiaosi[0]\songti\textbf{\hit@cdate}}
  \end{center}
}
\newcommand{\hit@second@titlepage@bachelor}{
  \vspace*{0.6cm}
  \centering\includegraphics[scale=0.38]{logo.pdf}
  \vspace{1.5cm}
  \begin{center}
    \centering\includegraphics[scale=0.25]{bthesistitle.pdf}
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
\newcommand{\hit@first@titlepage@other}{
  % 封面一
\ifthenelse%
{\equal{\hit@fontset}{siyuan}}%
{\xiaosi[1]\vspace*{0.65em}}%
{\xiaosi[1]\textcolor[rgb]{1,1,1}{\songti{\hit@hi}}}%
 \vspace*{1.2cm}
  \begin{center}
  \begin{center}\xiaoyi[1]\songti\textbf{\hit@cxuewei\hit@cthesisname}\end{center}
    \vspace{1.4cm}
    \parbox[t][2.8cm][t]{\textwidth}{
  \begin{center}\erhao\heiti\hit@ctitle\end{center} }
    \parbox[t][5.1cm][t]{\textwidth}{ %英文标题太长时可以采用\xiaoer
  \begin{center}\erhao\textbf{\MakeUppercase{\hit@etitle}}\end{center} }
    \parbox[t][7.4cm][t]{\textwidth}{
  \begin{center}\xiaoer\songti\textbf{\hit@cauthor}\end{center}}
    \parbox[t][1.4cm][t]{\textwidth}{
  \begin{center}\kaishu\xiaoer\textbf{\hit@cschoolname}\end{center} }
    {\songti\xiaoer\textbf{\hit@cdate}}
  \end{center}
}

%内封
\newcommand{\hit@second@titlepage@other}{
  \begin{center}
    {\songti \xiaosi
      \begin{tabular}{@{}r@{：}l@{}}
	\hit@natclassifiedindextitle & \hit@natclassifiedindex\\
	\hit@internatclassifiedindextitle & \hit@internatclassifiedindex
    \end{tabular}}\hfill
    {\songti \xiaosi
      \begin{tabular}{@{}r@{：}l@{}}
	\hit@schoolidtitle & \hit@schoolid\\
	\hit@secretlevel & \hit@statesecrets
    \end{tabular}}
  \parbox[t][3.2cm][t]{\textwidth}{\begin{center} \end{center} }
    \parbox[t][2.4cm][t]{\textwidth}{\xiaoer
  \begin{center} {\songti \bfseries \hit@cdegree \hit@cthesisname }\end{center} }
    \parbox[t][5cm][t]{\textwidth}{\erhao
  \begin{center} {\heiti  \hit@ctitle}\end{center} }
    \parbox[t][9.8cm][b]{\textwidth}
    {\sihao
      \setlength{\hit@title@width}{6em}
      \begin{center} \renewcommand{\arraystretch}{1.62} \songti
	\begin{tabular}{l@{\hit@title@csep}l}
	  {\heiti \hit@put@title{\hit@cauthortitle}}	&	\hit@cauthor\\
	  {\heiti \hit@put@title{\hit@csupervisortitle}}	&	\hit@csupervisor\\
        \ifx\hit@cassosupervisor\@empty\else%
	  {\heiti \hit@put@title{\hit@cassosupervisortitle}}&	\hit@cassosupervisor\\
        \fi
        \ifx\hit@ccosupervisor\@empty\else%
	  {\heiti \hit@put@title{\hit@ccosupervisortitle}}	&	\hit@ccosupervisor\\
        \fi
	  {\heiti \hit@put@title{\hit@cdegreetitle}}	&	\hit@cdegree\\
	  {\heiti \hit@put@title{\hit@csubjecttitle}}	&	\hit@csubject\\
	  {\heiti \hit@put@title{\hit@caffiltitle}}		&	\hit@caffil\\
	  {\heiti \hit@put@title{\hit@cdatetitle}}		&	\hit@cdate\\
	  {\heiti \hit@put@title{\hit@cschoolnametitle}}	&	\hit@cschoolname
	\end{tabular} \renewcommand{\arraystretch}{1}
    \end{center} }
  \end{center}
}

% 英文封面

\newcommand{\emultiline}[2][c]{\renewcommand{\arraystretch}{1}\begin{tabular}[#1]{@{}l@{}}#2\end{tabular} \renewcommand{\arraystretch}{1.3}}
\newcommand{\hit@engcover}{
  {
    \xiaosi[1.667]\noindent Classified Index: \hit@natclassifiedindex \\[8pt]
  U.D.C:  \hit@internatclassifiedindex }
  \vspace*{1em}
  \begin{center}
  \parbox[t][1.6cm][t]{\textwidth}{\begin{center} \end{center} }
    \parbox[t][3.5cm][t]{\textwidth}{\xiaoer
  \begin{center} {  Dissertation for the {\hit@exueweier} Degree in \hit@exueke}\end{center} } %与中文保持一致，删除in {\hit@exueke}
    \parbox[t][7cm][t]{\textwidth}{\erhao
  \begin{center}\textbf{\MakeUppercase{\hit@etitle}}\end{center} }
    %★★★★若信息内容不太长，不会引起信息内容分行时，使用tabular环境，否则使用下面的tabularx环境。
    {\sihao\renewcommand{\arraystretch}{1.3}
      \begin{tabular}{@{}l@{~}l@{}}
	\textbf{\hit@eauthortitle\hit@title@esep}		&	\hit@eauthor\\
	\textbf{\hit@esupervisortitle\hit@title@esep}	&	\hit@esupervisor\\
      \ifx\hit@eassosupervisor\@empty\else%
	\textbf{\hit@eassosupervisortitle\hit@title@esep}	&	\hit@eassosupervisor\\
      \fi
      \ifx\hit@ecosupervisor\@empty\else%
	\textbf{\hit@ecosupervisortitle\hit@title@esep}	&	\hit@ecosupervisor\\
      \fi
	\textbf{\hit@edegreetitle\hit@title@esep}		&	\hit@edegree\\
      \textbf{\hit@esubjecttitle\hit@title@esep}		&\hit@esubject\\
	\textbf{\hit@eaffiltitle\hit@title@esep}		&\hit@eaffil\\
	\textbf{\hit@edatetitle\hit@title@esep}		&	\hit@edate\\
	\textbf{\hit@eschoolnametitle\hit@title@esep}	&	\hit@eschoolname
    \end{tabular}\renewcommand{\arraystretch}{1}}
  \end{center}
}

\def\makecover{
  \phantomsection
  \pdfbookmark[-1]{\hit@ctitle}{ctitle}
  \xiaosi[1]%
  \begin{titlepage}
    \hit@first@titlepage
    \cleardoublepage
    \hit@second@titlepage
    \cleardoublepage
    \ifhit@bachelor
    \relax
    \else
    \hit@engcover
    \cleardoublepage
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
  \if@openright\cleardoublepage\else\clearpage\fi
  \hit@appendix@chapter*{\cabstractcname}[\cabstractename]
  \pagestyle{hit@headings}
  \pagenumbering{Roman}
  \hit@cabstract
  \vskip12bp
  \hit@put@keywords{\heiti\hit@ckeywords@title}{\hit@ckeywords}
  \clearpage
  \hit@appendix@chapter*{\eabstractcname}[\eabstractename]
  \hit@eabstract
  \vskip12bp
  \hit@put@keywords{\textbf{Keywords:\enskip}}{\hit@ekeywords}}

\newenvironment{denotation}[1][2.5cm]{%
  \clearpage
  \hit@appendix@chapter*{\hit@denotation@ctitle}[\hit@denotation@etitle]
\setcounter{table}{0}
\renewcommand{\thetable}{\arabic{table}}%使表编号为 1 的格式
  }{\renewcommand{\thetable}{\arabic{chapter}-\arabic{table}}%使表编号为 7-1 的格式
\setcounter{table}{0}}%

% 虽然格式漂亮但不符合规范
%\newlist{hitdenotation}{description}{1}
%\setlist[hitdenotation]{%
%  nosep,
%  font=\normalfont,
%  align=left,
%  leftmargin=!, % sum of the following 3 lengths
%  labelindent=0pt,
%  labelwidth=2.5cm,
%  labelsep*=0.5cm,
%  itemindent=0pt,
%}

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
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%中文目录格式

\setcounter{secnumdepth}{3}
\ifhit@bachelor\ifhit@tocfour\setcounter{tocdepth}{3}\fi\fi
\setcounter{tocdepth}{2}
\renewcommand\tableofcontents{%
\hit@chapter*{\contentsname}
\pdfbookmark[0]{\contentsname}{ccontent}
\normalsize\@starttoc{toc}}
\ifhit@arialtoc
  \def\hit@toc@font{\sffamily}
\fi
\def\@pnumwidth{4em}%规定中的提前悬挂
\def\@tocrmarg{\@pnumwidth}
\def\@dotsep{1}
\patchcmd{\@dottedtocline}{#4}{\csname hit@toc@font\endcsname #4}{}{}
\patchcmd{\@dottedtocline}{\hb@xt@\@pnumwidth}{\hbox}{}{}

\renewcommand*\l@chapter[2]{%
  \ifnum \c@tocdepth >\m@ne
    \addpenalty{-\@highpenalty}%
    %\vskip 4bp \@plus\p@
    \setlength\@tempdima{4em}%
    \begingroup
      \parindent \z@ \rightskip \@pnumwidth
      \parfillskip -\@pnumwidth
      \leavevmode
      \advance\leftskip\@tempdima
      \hskip -\leftskip
      % numberline is called here, and it uses \@tempdima
      {\ifhit@bachelor\sffamily\else\csname hit@toc@font\endcsname\fi\heiti #1}
      \leaders\hbox{$\m@th\mkern \@dotsep mu\hbox{.}\mkern \@dotsep mu$}\hfill
      \nobreak{\normalfont\normalcolor #2}\par
      \penalty\@highpenalty
    \endgroup
  \fi}

% 按工大标准, 缩小目录中各级标题之间的缩进，使它们相隔一个字符距离，也就是12pt
\renewcommand*\l@section{\@dottedtocline{1}{1em}{1.8em}}
\renewcommand*\l@subsection{\@dottedtocline{2}{2em}{2.5em}}
\renewcommand*\l@subsubsection{\@dottedtocline{3}{3\ccwd}{3.1em}}

% 英文目录格式
\def\@dotsep{0.75}           % 定义英文目录的点间距
\setlength\leftmargini {0pt}
\setlength\leftmarginii {0pt}
\setlength\leftmarginiii {0pt}
\setlength\leftmarginiv {0pt}
\setlength\leftmarginv {0pt}
\setlength\leftmarginvi {0pt}

\def\engcontentsname{\bfseries Contents}
\newcommand\tableofengcontents{
  \@restonecolfalse
  \chapter*{\engcontentsname  %chapter*上移一行，避免在toc中出现。
  \pdfbookmark[0]{Contents}{econtent}
    \@mkboth{%
  \engcontentsname}{\engcontentsname}}
  \@starttoc{toe}%
  \if@restonecol\twocolumn\fi
}

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
  \if@openright\cleardoublepage\else\clearpage\fi
  \hit@appendix@chapter*{\hit@conclusion@ctitle}[\hit@conclusion@etitle]}{}
\newenvironment{acknowledgements}{%
  \if@openright\cleardoublepage\else\clearpage\fi
  \hit@appendix@chapter*{\hit@acknowledgement@ctitle}[\hit@acknowledgement@etitle]}{}
\newenvironment{resume}{%
  \if@openright\cleardoublepage\else\clearpage\fi
  \hit@appendix@chapter*{\hit@resume@ctitle}[\hit@resume@etitle]}{}
\newenvironment{publication}{%
  \if@openright\cleardoublepage\else\clearpage\fi
  \hit@appendix@chapter*{\hit@publication@ctitle}[\hit@publication@etitle]}{}

\newenvironment{ceindex}{%
  \if@openright\cleardoublepage\else\clearpage\fi
  \hit@appendix@chapter*{\indexname}[\hit@index@etitle]\begin{multicols*}{2}}{\end{multicols*}}

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

\def\authorization{%
  \if@openright\cleardoublepage\else\clearpage\fi
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

\newcommand\bibstyle@numerical{\bibpunct{[}{]}{,}{s}{,}{\textsuperscript{,}}}
\newcommand\bibstyle@authoryear{\bibpunct{(}{)}{;}{a}{,}{,}}
\newcommand\bibstyle@inline{\bibpunct{[}{]}{,}{n}{,}{,}}
\citestyle{numerical}
\DeclareRobustCommand\inlinecite{\@inlinecite}
\def\@inlinecite#1{\begingroup\let\@cite\NAT@citenum\citep{#1}\endgroup}
\let\onlinecite\inlinecite
\renewenvironment{thebibliography}[1]{%
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
  \clubpenalty4000
  \@clubpenalty \clubpenalty
  \widowpenalty4000%
  \interlinepenalty4000%
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
