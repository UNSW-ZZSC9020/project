%-----------------------------------------------------------------------
% UNSWThesis.cls : A thesis style of UNSW modified from ADFAThesis.cls
%-----------------------------------------------------------------------
\NeedsTeXFormat{LaTeX2e}[1995/12/01]
\ProvidesClass{unswthesis}[1999/11/10 \space v2.42 \space%
         UNSW thesis class]

%-----------------------------------------------------------------------
% 12-Apr-89  New flag for draft printing
% At this stage all I do is reset the page style
%-----------------------------------------------------------------------
\newif\ifATdr@ft         % Enable various commands during initial write-up
\ATdr@ftfalse            % Not draft, by default, must be set in BASE file
\newif\ifATh@nours       % Honours report not PhD or Masters?
\ATh@noursfalse          % Not Honours by default, must be set in BASE file
\newif\ifATugpr@ject     % Third Year Project report, not PhD or Masters?
\ATugpr@jectfalse        % Not Third Year Project by default, must be set in BASE file
\newif\ifATmbi@o         % Master of Biostatistics report, not PhD or Masters?
\ATmbi@ofalse            % Not Master of Biostatistics by default, must be set in BASE file
\newif\ifATmf@in         % Master of Financial Mathematics report, not PhD or Masters?
\ATmf@infalse            % Not Master of Fin. Maths. by default, must be set in BASE file
\newif\ifATmm@th         % Master of Mathematics report, not PhD or Masters?
\ATmm@thfalse            % Not Master of Mathematics by default, must be set in BASE file
\newif\ifATmst@t         % Master of Statistics report, not PhD or Masters?
\ATmst@tfalse            % Not Master of Statistics by default, must be set in BASE file

\newcommand{\ptsize}{}
\DeclareOption{draft}
   {\ATdr@fttrue
    \PassOptionsToClass{draft}{report}}
\DeclareOption{honours}
   {\ATh@nourstrue}
\DeclareOption{ugproject}
   {\ATugpr@jecttrue}
\DeclareOption{mbio}
   {\ATmbi@otrue}
\DeclareOption{mfin}
   {\ATmf@intrue}
\DeclareOption{mmath}
   {\ATmm@thtrue}
\DeclareOption{mstat}
   {\ATmst@ttrue}
% Make 12 point text the default
\DeclareOption{10pt}{\renewcommand{\ptsize}{10pt}}
\DeclareOption{11pt}{\renewcommand{\ptsize}{11pt}}
\DeclareOption{12pt}{\renewcommand{\ptsize}{12pt}}
\DeclareOption*{\PassOptionsToClass{\CurrentOption}{report}}
\ExecuteOptions{12pt}
\ProcessOptions\relax
\LoadClass[a4paper,\ptsize]{report}

%-----------------------------------------------------------------------
% The size of the paper shall approximate A4 (297mm x 210 mm).
% The margins on each sheet shall be not less than 40mm on the left
% hand side, 20mm on the right hand side, 30mm at the top and 20mm at
% the bottom.
% TeX has default margins of 1 inch (25.4mm) at the top and left.
%
% Use the code from size12.clo to set \textheight to an integer
% multiple of \baselineskips.  User \raggedbottom and add one
% \baselineskip to \topskip to allow pagelength to vary.
%-----------------------------------------------------------------------

\newcommand{\setpagesize}{%
    \setlength{\oddsidemargin}  {1.5cm}
    \setlength{\evensidemargin} {-0.5cm}    % was 0cm
    \setlength{\marginparwidth} {40\p@}
    \setlength{\marginparsep}   {10\p@}     % was 0pt
    \setlength{\topmargin}      {-0.6cm}    % was 0cm
    \setlength{\headheight}     {15\p@}     % was 12pt
    \setlength{\headsep}        {0.5cm}
    \setlength{\textwidth}      {14.9cm}    % was 15cm
    \setlength\@tempdima{\paperheight}
    \addtolength\@tempdima{-35mm}  % top margin
    \addtolength\@tempdima{-25mm}  % bottom margin
    \divide\@tempdima\baselineskip
    \@tempcnta=\@tempdima
    \setlength\textheight{\@tempcnta\baselineskip}
    \addtolength\textheight{\topskip}
    \setlength{\topskip}{1\topskip \@plus 1\baselineskip}
    \setlength{\parskip}{0pt}
    \raggedbottom
}
\setpagesize

%-----------------------------------------------------------------------
% Set spacing for space and a half, using values from setspace.sty.
% Use the new \linespread command rather than
% \renewcommand{\baselinestretch}{1.25} etc.
%-----------------------------------------------------------------------
\ifcase \@ptsize \relax % 10pt
  \linespread{1.25}%
\or % 11pt
  \linespread{1.213}%
\or % 12pt
  \linespread{1.6}%
\fi

%-----------------------------------------------------------------------
% Next two sections taken from setspace.
%-----------------------------------------------------------------------
\newcommand{\displayskipstretch}{\baselinestretch}
\newcommand{\setdisplayskipstretch}[1]{\renewcommand{\displayskipstretch}{#1}}

%
% Fix up spacing before and after displayed math
% (arraystretch seems to do a fine job for inside LaTeX displayed math,
% since array and eqnarray seem to be affected as expected).
% Changing \baselinestretch and doing a font change also works if done here,
% but then you have to change @setsize to remove the call to @nomath)
%
\everydisplay\expandafter{%
  \the\everydisplay
  \abovedisplayskip \displayskipstretch\abovedisplayskip
  \belowdisplayskip \displayskipstretch\belowdisplayskip
  \abovedisplayshortskip \displayskipstretch\abovedisplayshortskip
  \belowdisplayshortskip \displayskipstretch\belowdisplayshortskip
}
%-----------------------------------------------------------------------
%  Following changed by Stephen Harker, October 1993 to:
%  (i)   Make Chapter title centred, and modify size to \Large not
%        \Huge, use small caps for `chapter' and rules above and
%        below.  Rule thickness defined by new length \chaprule.
%        To change this use \setlength.
%  (ii)  Make corresponding reductions to size of section,
%        subsection and subsubsection headers.
%  (iii) Rename Bibliography section to References.
%-----------------------------------------------------------------------
\newlength{\chaprule}    % Forced to be less than 6 points below!
\newlength{\ATchapskip}
\setlength{\chaprule}{0.4\p@}
\setlength{\ATchapskip}{10\p@}
\advance \ATchapskip by -1\chaprule
\renewcommand{\@makechapterhead}[1]{%
  \ifdim\chaprule>6\p@ \setlength{\chaprule}{6\p@}\fi
  \vspace*{\ATchapskip}%
  \noindent\rule{\textwidth}{\chaprule}\par%
  \vskip 10\p@
  {\parindent \z@ \centering \normalfont
    \ifnum \c@secnumdepth >\m@ne
        {\Large\scshape \@chapapp\space \thechapter}
        \par\nobreak
        \vskip 8\p@
    \fi
    \interlinepenalty\@M
    \Large #1\par\nobreak
    \vskip 10\p@
    \noindent\rule{\textwidth}{\chaprule}\par%
    \vskip\ATchapskip
  }}
\renewcommand{\@makeschapterhead}[1]{%
  \ifdim\chaprule>6\p@ \setlength{\chaprule}{6\p@}\fi
  \vspace*{\ATchapskip}%
  \noindent\rule{\textwidth}{\chaprule}\par%
  \vskip 10\p@
  {\parindent \z@ \centering
    \normalfont
    \interlinepenalty\@M
    \Large #1\par\nobreak
    \vskip 10\p@
    \noindent\rule{\textwidth}{\chaprule}\par%
    \vskip\ATchapskip
  }}

\renewcommand{\section}{\@startsection{section}{1}{\z@}%
    {-1.5ex \@plus-1ex \@minus -.2ex}{0.8ex \@plus.2ex}%
    {\normalfont\large\raggedright}}
\renewcommand{\subsection}{\@startsection{subsection}{2}{\z@}%
    {-1.2ex \@plus -.5ex \@minus-.2ex}{0.5ex \@plus.1ex}%
    {\normalfont\normalsize\itshape\raggedright}}
\renewcommand{\subsubsection}{\@startsection{subsubsection}{3}{\z@}%
    {-1.0ex\@plus -.5ex \@minus -.2ex}{0.3ex \@plus .1ex}%
    {\normalfont\normalsize\itshape\raggedright}}
\renewcommand{\paragraph}{\@startsection{paragraph}{4}{\z@}%
    {1.0ex \@plus.5ex \@minus.2ex}{-1em}%
    {\normalfont\normalsize\itshape\raggedright}}
\renewcommand{\subparagraph}{\@startsection{subparagraph}{5}{\parindent}%
    {1.0ex \@plus.5ex \@minus .2ex}{-1em}%
    {\normalfont\normalsize\itshape\raggedright}}

\renewcommand{\bibname}{References}

%-----------------------------------------------------------------------
% Taken from sober.sty, Nico Poppelier and rapport1.cls (NTG classes).
% Makes list (enumerate and itemize) more reasonable in vertical space,
% by adjusting the spacing between items.
% Unfortunately in the size*.clo files \small etc also redefine these
% values.  We could redefine \small etc, but they are size dependent!
% Leave alone, since \small is not usually used as an environment, at
% least not for large sections of a document.
%-----------------------------------------------------------------------
\def\@listi{\leftmargin\leftmargini
    \labelsep .5em%
    \labelwidth\leftmargini
    \advance\labelwidth-\labelsep
    \parsep \z@
    \topsep 0.4ex \@plus\p@
    \itemsep 0\p@ \@plus1\p@}
\let\@listI\@listi
\@listi
\def\@listii{\leftmargin\leftmarginii
    \labelsep .5em%
    \labelwidth\leftmarginii
    \advance\labelwidth-\labelsep
    \topsep 0\p@ \@plus\p@
    \parsep \z@ \@plus\p@
    \itemsep \parsep}
\def\@listiii{\leftmargin\leftmarginiii
    \labelsep .5em%
    \labelwidth\leftmarginiii
    \advance\labelwidth-\labelsep
    \topsep 0\p@ \@plus\p@
    \parsep \z@
    \partopsep \z@ \@plus\p@
    \itemsep \topsep}
\def\@listiv{\leftmargin\leftmarginiv
    \labelsep .5em%
    \labelwidth\leftmarginiv
    \advance\labelwidth-\labelsep
    \topsep 0\p@ \@plus\p@
    \parsep \z@
    \partopsep \z@ \@plus\p@
    \itemsep \topsep}
\def\@listv{\leftmargin\leftmarginv
     \labelsep  .5em%
     \labelwidth\leftmarginv
     \advance\labelwidth-\labelsep%
     \topsep    0\p@ \@plus\p@
     \parsep    \z@
     \itemsep   \z@ \@plus\p@}
\def\@listvi{\leftmargin\leftmarginvi
     \labelsep  .5em
     \labelwidth\leftmarginvi
     \advance\labelwidth{-\labelsep}%
     \topsep    0\p@ \@plus\p@
     \parsep    \z@
     \itemsep   \z@ \@plus\p@}

%-----------------------------------------------------------------------
% Re-define \cleardoublepage as recommended by Piet van Oostrum in the
% documentation for fancyhdr.sty page 15.  This is to avoid blank pages
% having headers or footers.
%-----------------------------------------------------------------------
\renewcommand{\cleardoublepage}{\clearpage\if@twoside \ifodd\c@page\else
   \thispagestyle{empty}
   \hbox{}\newpage\if@twocolumn\hbox{}\newpage\fi\fi\fi}
%-----------------------------------------------------------------------
%  Reduce widow/orphan problems, mainly from a posting from Donald
%  Arsenau on comp.text.tex, 24 Sep 1995.
%  Updated to follow comments from Michael Downes on comp.text.tex,
%  31 Aug 1998.
%-----------------------------------------------------------------------
\doublehyphendemerits=10000     % No consecutive line hyphens.
\brokenpenalty=4991             % Reduce broken words across columns/pages.
\widowpenalty=9999              % Almost no widows at bottom of page.
\clubpenalty=9996               % Almost no orphans at top of page.
\interfootnotelinepenalty=9999  % Almost never break footnotes.
\predisplaypenalty=10000        % Default value
\postdisplaypenalty=1549        % Few breaks between display and widows
\displaywidowpenalty=1602       % At least as high as \postdisplaypenalty
%-----------------------------------------------------------------------
% Change float placement parameters to reduce problems.  Based on
% values posted by Donald Arsenau on comp.text.tex at various times.
% See in particular 17th Nov 1997.
%-----------------------------------------------------------------------
\renewcommand{\topfraction}{.85}
\renewcommand{\bottomfraction}{.7}
\renewcommand{\textfraction}{.15}
\renewcommand{\floatpagefraction}{.66}
\renewcommand{\dbltopfraction}{.66}
\renewcommand{\dblfloatpagefraction}{.66}
\setcounter{topnumber}{9}
\setcounter{bottomnumber}{9}
\setcounter{totalnumber}{20}
\setcounter{dbltopnumber}{9}

%-----------------------------------------------------------------------
%  Make tables and figures default to small text and be single spaced,
%  and modify caption macro to allow this to take effect in the caption.
%  Use this version rather than previous redefinition of \@xfloat, see
%  setspace.sty for an improved example of the latter.
%  From comp.text.tex, Donald Arsenau 25 July 1996.
%  Also reverse \abovecaptionskip and \belowcaptionskip for tables.
%-----------------------------------------------------------------------
\renewenvironment{table}
               {\setlength{\abovecaptionskip}{0\p@}
                \setlength{\belowcaptionskip}{10\p@}
                \linespread{1}\normalfont\small\@float{table}}
               {\end@float}
\renewenvironment{table*}
               {\setlength{\abovecaptionskip}{0\p@}
                \setlength{\belowcaptionskip}{10\p@}
                \linespread{1}\normalfont\small\@dblfloat{table}}
               {\end@dblfloat}
\renewenvironment{figure}
               {\linespread{1}\normalfont\small\@float{figure}}
               {\end@float}
\renewenvironment{figure*}
               {\linespread{1}\normalfont\small\@dblfloat{figure}}
               {\end@dblfloat}
\long\def\@caption#1[#2]#3{\par\addcontentsline{\csname
  ext@#1\endcsname}{#1}{\protect\numberline{\csname
  the#1\endcsname}{\ignorespaces #2}}\begingroup
    \@parboxrestore
    \if@minipage
      \@setminipage
    \fi
%%  \normalsize   % Remove this so we can get \small captions.
    \@makecaption{\csname fnum@#1\endcsname}{\ignorespaces #3}\par
  \endgroup}

% Also Donald Arsenau's modified \@makecaption which fixes problems
% with spacing of captions before tables.  Taken from comp.text.tex
% 21 May 1997.  Regular version (acts like regular caption, but with
% Donald Arsenau's improvements).

\def\onecaptflag{268 }
\renewcommand{\@makecaption}[2]{\let\@tempa\relax
   \ifdim\prevdepth>-99\p@ \vskip\abovecaptionskip \relax
   \else \def\@tempa{\vbox to\topskip{}}\fi
   {#1: }\@tempa \vadjust{\penalty \onecaptflag}#2\par
   \ifnum\lastpenalty=\onecaptflag
      \unpenalty \setbox\@tempboxa\lastbox
      \nointerlineskip
      \hbox to\hsize{\hskip\parfillskip\unhbox\@tempboxa}%
   \fi \vskip\belowcaptionskip}
%-----------------------------------------------------------------------
% Number figures, tables and equations by chapter.  Re-define footnotes
% and minipage footnotes to be single spaced.  Make new macros needed
% for thesis definitions.
%-----------------------------------------------------------------------

\renewcommand{\thefigure}{\thechapter.\@arabic\c@figure}
\renewcommand{\thetable}{\thechapter.\@arabic\c@table}
\renewcommand{\theequation}{\thechapter.\@arabic\c@equation}

% Re-define \@footnotetext and \@mpfootnotetext to use single spacing
% rather than the space-and-a-half that is the default elsewhere.

\renewcommand{\@footnotetext}[1]{\insert\footins{%
    \linespread{1}\normalfont\footnotesize%
    \interlinepenalty\interfootnotelinepenalty
    \splittopskip\footnotesep
    \splitmaxdepth \dp\strutbox \floatingpenalty \@MM
    \hsize\columnwidth \@parboxrestore
    \protected@edef\@currentlabel{%
      \csname p@footnote\endcsname\@thefnmark}%
    \color@begingroup
      \@makefntext{%
        \rule\z@\footnotesep\ignorespaces#1\@finalstrut\strutbox}%
    \color@endgroup}}

\renewcommand{\@mpfootnotetext}[1]{%
  \global\setbox\@mpfootins\vbox{%
    \unvbox \@mpfootins
    \linespread{1}\normalfont\footnotesize%
    \hsize\columnwidth
    \@parboxrestore
    \protected@edef\@currentlabel{%
      \csname p@mpfootnote\endcsname\@thefnmark}%
    \color@begingroup
      \@makefntext{%
       \rule\z@\footnotesep\ignorespaces#1\@finalstrut\strutbox}%
   \color@endgroup}}

%-----------------------------------------------------------------------
% Define thesis related commands.
% Another change is to add \thesistype which can be defined
% as appropriate for Masters or Doctoral thesis (default Doctoral).
%-----------------------------------------------------------------------
\newcommand{\dept}[1]{\gdef\@dept{#1}}
\newcommand{\thesistype}[1]{\gdef\@thesistype{#1}}
\newcommand{\degreetype}[1]{\gdef\@degreetype{#1}}
\newcommand{\principaladviser}[1]{\gdef\@principaladviser{#1}}
\newcommand{\advis@r}{Adviser}
\newcommand{\principaladvisor}[1]{\gdef\@principaladviser{#1}%
        \gdef\advis@r{Advisor}}
\newcommand{\firstreader}[1]{\gdef\@firstreader{#1}}
\newcommand{\secondreader}[1]{\gdef\@secondreader{#1}}
\newcommand{\submitdate}[1]{\gdef\@submitdate{#1}}
\newcommand{\copyrightyear}[1]{\gdef\@copyrightyear{#1}} % \author, \title
                                                         % in report

\renewcommand{\@title}{}
\renewcommand{\@author}{}
\newcommand{\@dept}{Mathematics and Statistics}
\newcommand{\@thesistype}{Doctor of Philosophy}
\newcommand{\@degreetype}{Science}
\newcommand{\@principaladviser}{}
\newcommand{\@firstreader}{}
\newcommand{\@secondreader}{}
\newcommand{\@submitdate}{\ifcase\the\month\or
  January\or February\or March\or April\or May\or June\or
  July\or August\or September\or October\or November\or December\fi
  \space \number\the\year}
\ifnum\month=12
    \@tempcnta=\year \advance\@tempcnta by 1
    \edef\@copyrightyear{\number\the\@tempcnta}
\else
    \newcommand{\@copyrightyear}{\number\the\year}
\fi

\newif\ifcopyright
\newif\iffigurespage
\newif\iftablespage
\copyrighttrue
\figurespagetrue
\tablespagetrue
%-----------------------------------------------------------------------
% A new definition, mainly for the DECLARATION.
%-----------------------------------------------------------------------
\newcommand{\authornameonly}[1]{\gdef\Authornameonly{#1}}
%-----------------------------------------------------------------------
% Title page, copyrightpage and declaration page definitions.
% Add re-definition for Honours reports rather than Higher Degree
% theses.
%-----------------------------------------------------------------------
\newcommand{\titlep}{%
        \pagestyle{empty}%
        \null\vskip2.5cm%
        \begin{center}
                {\rmfamily\Large\uppercase\expandafter{\@title}}
        \end{center}
        \vfill
        \begin{center}
                \textsc{A thesis submitted for the degree of \\
                \expandafter{\@thesistype}}
        \end{center}
        \vfill
        \begin{center}
                {\rmfamily\normalsize By\\
                \@author}\\
        \end{center}
        \vfill
        \begin{center}  % Department changed to School July 1995
                {\rmfamily\normalsize School of \expandafter{\@dept},\\
                UNSW Sydney.}
                \vskip1cm
                {\rmfamily\normalsize \@submitdate}\\
        \end{center}
        \vskip1cm
        \newpage}
\ifATh@nours\renewcommand{\titlep}{%
        \pagestyle{empty}%
        \null\vskip2.5cm%
        \begin{center}
                {\rmfamily\Large\uppercase\expandafter{\@title}}
        \end{center}
        \vfill
        \begin{center}
                {\rmfamily\normalsize \@author}\\
        \end{center}
\begin{figure} \begin{center}
\includegraphics[width=5cm]{unsw-logo}
\end{center} \end{figure}
        \vskip1cm
        \begin{center}  % Department changed to School July 1995
                {\rmfamily\normalsize School of \expandafter{\@dept}\\
                UNSW Sydney} \\
                \vskip1cm
                {\rmfamily\normalsize \@submitdate}\\
        \end{center}
        \vfill
        \begin{center}
                \small\textsc{Submitted in partial fulfillment of the
                requirements of the degree of \\
                Bachelor of \expandafter{\@degreetype} with Honours}
        \end{center}
        \newpage}\fi
\ifATugpr@ject\renewcommand{\titlep}{%
        \pagestyle{empty}%
        \null\vskip2.5cm%
        \begin{center}
                {\rmfamily\Large\uppercase\expandafter{\@title}}
        \end{center}
        \vfill
        \begin{center}
                {\rmfamily\normalsize \@author}\\
        \end{center}
\begin{figure} \begin{center}
\includegraphics[width=5cm]{unsw-logo}
\end{center} \end{figure}
        \vskip1cm
        \begin{center}  % Department changed to School July 1995
                {\rmfamily\normalsize School of \expandafter{\@dept}\\
                UNSW Sydney} \\
                \vskip1cm
                {\rmfamily\normalsize \@submitdate}\\
        \end{center}
        \vfill
        \begin{center}
                \small\textsc{Third Year Project Report}
        \end{center}
\newpage}\fi
\ifATmbi@o\renewcommand{\titlep}{%
        \pagestyle{empty}%
        \null\vskip2.5cm%
        \begin{center}
                {\rmfamily\Large\uppercase\expandafter{\@title}}
        \end{center}
        \vfill
        \begin{center}
                {\rmfamily\normalsize \@author}\\
        \end{center}
\begin{figure} \begin{center}
\includegraphics[width=5cm]{unsw-logo}
\end{center} \end{figure}
        \vskip1cm
        \begin{center}  % Department changed to School July 1995
                {\rmfamily\normalsize School of \expandafter{\@dept}\\
                UNSW Sydney} \\
                \vskip1cm
                {\rmfamily\normalsize \@submitdate}\\
        \end{center}
        \vfill
        \begin{center}
                \small\textsc{Submitted in partial fulfilment of the requirements of
                      the degree of\\Master of Biostatistics}
        \end{center}
\newpage}\fi
\ifATmf@in\renewcommand{\titlep}{%
        \pagestyle{empty}%
        \null\vskip2.5cm%
        \begin{center}
                {\rmfamily\Large\uppercase\expandafter{\@title}}
        \end{center}
        \vfill
        \begin{center}
                {\rmfamily\normalsize \@author}\\
        \end{center}
\begin{figure} \begin{center}
\includegraphics[width=5cm]{unsw-logo}
\end{center} \end{figure}
        \vskip1cm
        \begin{center}  % Department changed to School July 1995
                {\rmfamily\normalsize School of \expandafter{\@dept}\\
                UNSW Sydney} \\
                \vskip1cm
                {\rmfamily\normalsize \@submitdate}\\
        \end{center}
        \vfill
        \begin{center}
                \small\textsc{Submitted in partial fulfilment of the requirements of
                      the degree of\\Master of Financial Mathematics}
        \end{center}
\newpage}\fi
\ifATmm@th\renewcommand{\titlep}{%
        \pagestyle{empty}%
        \null\vskip2.5cm%
        \begin{center}
                {\rmfamily\Large\uppercase\expandafter{\@title}}
        \end{center}
        \vfill
        \begin{center}
                {\rmfamily\normalsize \@author}\\
        \end{center}
\begin{figure} \begin{center}
\includegraphics[width=5cm]{unsw-logo}
\end{center} \end{figure}
        \vskip1cm
        \begin{center}  % Department changed to School July 1995
                {\rmfamily\normalsize School of \expandafter{\@dept}\\
                UNSW Sydney} \\
                \vskip1cm
                {\rmfamily\normalsize \@submitdate}\\
        \end{center}
        \vfill
        \begin{center}
                \small\textsc{Submitted in partial fulfilment of the requirements of
                      the degree of\\Master of Mathematics}
        \end{center}
\newpage}\fi
\ifATmst@t\renewcommand{\titlep}{%
        \pagestyle{empty}%
        \null\vskip2.5cm%
        \begin{center}
                {\rmfamily\Large\uppercase\expandafter{\@title}}
        \end{center}
        \vfill
        \begin{center}
                {\rmfamily\normalsize \@author}\\
        \end{center}
\begin{figure} \begin{center}
\includegraphics[width=5cm]{unsw-logo}
\end{center} \end{figure}
        \vskip1cm
        \begin{center}  % Department changed to School July 1995
                {\rmfamily\normalsize School of \expandafter{\@dept}\\
                UNSW Sydney} \\
                \vskip1cm
                {\rmfamily\normalsize \@submitdate}\\
        \end{center}
        \vfill
        \begin{center}
                \small\textsc{Submitted in partial fulfilment of the requirements of\\
                      the capstone course ZZSC9020}
        \end{center}
\newpage}\fi

\newcommand{\copyrightpage}{%
        \null\vfill
        \begin{center}
                {\Large\copyright\ Copyright \@copyrightyear\\
                by\\
                \@author}\\
        \end{center}
        \vfill\newpage}

\newcommand{\declaration}{%
\newpage
\null\vfill
\begin{center}
\begin{minipage}{11cm}
\setlength{\parindent}{0\p@}
\setlength{\parskip}{2ex \@plus0.5ex}
{\rmfamily\normalsize
I hereby declare that this submission is my own work and to the best of my
knowledge it contains no materials previously published or written by another
person, nor material which to a substantial extent has been accepted for the
award of any other degree or diploma at UNSW or any other educational
institution, except where due acknowledgement is made in the thesis. Any
contribution made to the research by others, with whom I have worked at UNSW or
elsewhere, is explicitly acknowledged in the thesis.

I also declare that the intellectual content of this thesis is the product of
my own work, except to the extent that assistance from others in the project's
design and conception or in style, presentation and linguistic expression is
acknowledged.
}
\par
\vspace{2.5cm}
\mbox{}\hfill\Authornameonly
\end{minipage}
\end{center}
\vfill\null
%\addcontentsline{toc}{chapter}{Declaration}
}

%-----------------------------------------------------------------------
% Add definitions for \beforepreface, \prefacesection and \afterpreface
% to allow page numbering and headerstyle to be changed.
%-----------------------------------------------------------------------
\newcommand{\beforepreface}{%
        \pagestyle{empty}
        \titlep
        \if@twoside\cleardoublepage\fi
        \pagenumbering{roman}
        \ifATdr@ft\pagestyle{draft}\else\pagestyle{plain}\fi
        \setcounter{page}\@ne% Reset the page number to 1, i.e. titlepage is page 0
        \ifcopyright\copyrightpage\fi
        }

\newcommand{\prefacesection}[1]{
        \chapter*{#1}
        %\addcontentsline{toc}{chapter}{#1}
    }

\newcommand{\afterpreface}{%
        \if@twoside
          \cleardoublepage
          \else\newpage
        \fi
        \tableofcontents
        \if@twoside
           \cleardoublepage
           \else\newpage
        \fi
        \iftablespage
                {\addvspace{10\p@}
                \let\saveaddvspace=\addvspace
                \def\addvspace##1{}
                \listoftables
                \let\addvspace=\saveaddvspace}
                \if@twoside
                  \cleardoublepage
                  \else\newpage
                \fi
        \fi
        \iffigurespage
                {\addvspace{10\p@}
                \let\saveaddvspace=\addvspace
                \def\addvspace##1{}
                \listoffigures
                \let\addvspace=\saveaddvspace}
                \if@twoside
                  \cleardoublepage
                  \else\newpage
                \fi
        \fi
        \pagenumbering{arabic}
        \ifATdr@ft\pagestyle{draft}\else\pagestyle{plain}\fi}
%-----------------------------------------------------------------------
% Create a brand new page style to include the date in the page header.
%-----------------------------------------------------------------------
\newcommand{\ps@draft}{%\let\@mkboth\@gobbletwo
     \renewcommand{\@oddfoot}{\@empty}%
     \renewcommand{\@oddhead}{\rmfamily\slshape\today\hfil\thepage}%
     \renewcommand{\@evenhead}{\rmfamily\slshape\thepage\hfil\today}%
     \renewcommand{\@evenfoot}{\@oddfoot}}
%-----------------------------------------------------------------------
% Start with pagestyle{plain} in case front matter isn't processed
%-----------------------------------------------------------------------
\pagestyle{plain}

%***********************************************************************
% Modify Table of contents entry for chapter to normal font not bold.
% Second use word Chapter/Appendix before number.  Use \appendixname
% rather than \@chapapp to set width for this element as it is longer!
%***********************************************************************
\newlength{\@chapwidth}%
\renewcommand*\l@chapter[2]{%
  \ifnum \c@tocdepth >\m@ne
    \addpenalty{-\@highpenalty}%
    \vskip 1.0em \@plus\p@
    \settowidth{\@chapwidth}{\appendixname}% not \@chapapp
    \addtolength{\@chapwidth}{\@pnumwidth}
    \setlength\@tempdima{\@chapwidth}%
    \begingroup
      \parindent \z@ \rightskip \@pnumwidth
      \parfillskip -\@pnumwidth
      \leavevmode \normalfont
      \advance\leftskip\@tempdima
      \hskip -\leftskip
      #1\nobreak\hfil \nobreak\hb@xt@\@pnumwidth{\hss #2}\par
      \penalty\@highpenalty
    \endgroup
  \fi}
\def\@chapter[#1]#2{%
    \ifnum \c@secnumdepth >\m@ne
       \refstepcounter{chapter}%
       \typeout{\@chapapp\space\thechapter.}%
       \addcontentsline{toc}{chapter}%
       {\protect\numberline{\expandafter\@chapapp\space\thechapter}#1}%
    \else
       \addcontentsline{toc}{chapter}{#1}%
    \fi
    \chaptermark{#1}%
    \addtocontents{lof}{\protect\addvspace{10\p@}}%
    \addtocontents{lot}{\protect\addvspace{10\p@}}%
    \if@twocolumn
    \@topnewpage[\@makechapterhead{#2}]%
    \else
    \@makechapterhead{#2}%
    \@afterheading
    \fi}

\endinput
%----------------------------------------------------------------------------
% Documentation
%----------------------------------------------------------------------------
\documentclass{article}
\newcommand{\bs}{\char '134 }  % A backslash character for \tt font
\title{The \texttt{UNSWthesis} class}
\author{Stephen Harker}
\date{25 May 1997}

\begin{document}
\maketitle

Some basic information on
the use of \texttt{UNSWthesis} (a modification of the \texttt{adfathesis} style
which was a modification of the \texttt{SUthesis} style) follows.  This class
file can only be used under \LaTeXe.  Firstly an example of use:

\begin{quote}
\small
\begin{verbatim}
\documentclass[a4paper,12pt,openright,twoside]{UNSWthesis}

% Control which chapters are LaTeX'd in this run with

\includeonly{chapter1,chapter2,chapter3}

\title{How to Write Theses\\
       With Two Line Titles}
\authornameonly{John Henry Candidate}
\author{\Authornameonly \\ B.Sc.(Hons)}
\copyrightfalse     % No copyright page
\figurespagefalse   % No List of Figures
\tablespagefalse    % No List of Tables

\begin{document}
\beforepreface
\prefacesection{Abstract}
    This thesis tells you all you need to know about...
\declaration   % Declaration page
\prefacesection{Acknowledgements}
    I would like to thank...
\afterpreface

\include{chapter1}  % Introduction
         ...
\include{chapter6}  % Conclusions
         ...
\appendix
\include{appendix1} % A Long Proof
         ...
\clearpage                                        % Needed to get page
\addcontentsline{toc}{chapter}{References}        % in TOC correct.
\bibliographystyle{UNSWthesis}
\bibliography{mybib}
\end{document}
\end{verbatim}
\end{quote}

\textbf{Documentation}: This class modifies the standard report class
to meet the \textsc{UNSW} requirements given in the `\emph{University
  College Handbook}'.  It sets the margins, interline spacing, the
figure and table numbering style, and disallows page breaks at
hyphens.

The `\texttt{\bs{}beforepreface}' command creates the title page, a
copyright page (optionally), and the table of contents.  Then the user
should put preface section(s), using the command
`\texttt{\bs{}prefacesection\{}\emph{Section Title}\texttt{\}}', this
should include the declaration page.  The tables of tables and figures
are then produced by the `\texttt{\bs{}afterpreface}' command, which
also sets things up to start the main body (on arabic page~1).

The following commands can control what goes in the front matter
material:
\begin{description}
\small
\item{\ttfamily\bs{}title\{\emph{thesis title}\}} Title of the thesis.
\item{\ttfamily\bs{}authornameonly\{\emph{name}\}} The author's name
  without degrees earned, needed for the declaration.
\item{\ttfamily\bs{}author\{\emph{name}\}} The author's name with
  degrees earned, for the titlepage.
\item{\ttfamily\bs{}dept\{\emph{department}\}} The default value is
  School of `\emph{Mathematics}'.
\item{\ttfamily\bs{}thesistype\{\emph{Type of thesis}\}} The default
  value is `\emph{Doctor of Philosophy}', for an Honours report this should
  be the faculty (e.g.\ `\emph{Science}').
\item{\ttfamily\bs{}degreetype\{\emph{Faculty for degree}\}} The default
  value is `\emph{Science}', used for Honours only.
\item{\ttfamily\bs{}submitdate\{\emph{date}\}} Month and year in which
  submitted; date \LaTeX{}'d if omitted.
\item{\ttfamily\bs{}copyrightyear\{\emph{year}\}} Year degree
  conferred, or year \LaTeX{}'d if omitted (next year if in December).
\item{\ttfamily\bs{}declaration} Produce the required declaration that
  the thesis is all the author's own work.
\item{\ttfamily\bs{}copyrighttrue} Produce or
  \texttt{\bs{}copyrightfalse} don't produce a `\emph{copyright}' page
  (true by default).
\item{\ttfamily\bs{}figurespagetrue} Produce or
  \texttt{\bs{}figurespagefalse} don't produce a `\emph{List of
    Figures}' page (true by default).
\item{\ttfamily\bs{}tablespagetrue} Produce or
  \texttt{\bs{}tablespagefalse} don't produce a `\emph{List of
    Tables}' page (true by default).
\end{description}

This class uses space and a half interline spacing, except in
footnote, figure and table environments where normal spacing is used.
The command: `\texttt{\bs{}linespread\}\-\{1.655\}}' can be used to
change this (use whatever you want instead of 1.655).  For 12 point
Computer Modern fonts 1.241 corresponds to space and a half, and 1.655
to double spacing.  This command should be given in the preamble
(i.e.\ before the `\texttt{\bs{}begin\{document\}}').

The example given shows the \textsf{12pt} option being used.  This is
required by the 1997 handbook, but may be omitted (at your own risk)
to get smaller print.  There are three options which may be declared
in \texttt{\bs{}documentclass[a4paper,12pt]\{UNSWthesis\}}:
\begin{itemize}
\item \texttt{draft} which changes the pagestyle to include the date
  on the page header.
\item \textsf{honours} which changes the titlepage to one more
  appropriate to an Honours report.
\end{itemize}

To get the correct page number for the bibliography in the table of
contents you need to put a `\texttt{\bs{}clearpage}' command before
the `\texttt{\bs{}addcontentsline}' command.  The thickness of the
rules used for the chapter headings is controlled by
`\texttt{\bs{}chaprule}' and can be set to another value, say 0~pt, by
the command `\texttt{\bs{}setlength\{\bs{}chaprule\}\{0pt\}}' in the
preamble. There is a maximum value of 6~pt for
`\texttt{\bs{}chaprule}'.

\end{document}
