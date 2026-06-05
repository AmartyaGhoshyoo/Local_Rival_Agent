LATEX_TEMPLATE = r"""
\documentclass[10pt, letterpaper]{article}

% Packages:
\usepackage[
    ignoreheadfoot,
    top=0.8 cm,
    bottom=0.8 cm,
    left=1.2 cm,
    right=1.2 cm,
    footskip=0.3 cm,
]{geometry}
\usepackage{titlesec}
\usepackage{tabularx}
\usepackage{array}
\usepackage[dvipsnames]{xcolor}
\definecolor{primaryColor}{RGB}{0, 0, 0}
\usepackage{enumitem}

\usepackage{amsmath}
\usepackage[
    colorlinks=true,
    urlcolor=primaryColor
]{hyperref}
\usepackage{calc}
\usepackage{changepage}
\usepackage{paracol}
\usepackage{ifthen}
\usepackage{needspace}
\usepackage{iftex}

\ifPDFTeX
    \input{glyphtounicode}
    \pdfgentounicode=1
    \usepackage[T1]{fontenc}
    \usepackage[utf8]{inputenc}
    \usepackage{lmodern}
\fi

\usepackage{charter}

% Compact settings:
\raggedright
\AtBeginEnvironment{adjustwidth}{\partopsep0pt}
\pagestyle{empty}
\setcounter{secnumdepth}{0}
\setlength{\parindent}{0pt}
\setlength{\topskip}{0pt}
\setlength{\columnsep}{0.12cm}
\pagenumbering{gobble}

\titleformat{\section}{\needspace{1.5\baselineskip}\bfseries\large}{}{0pt}{}[\vspace{-2pt}\titlerule]
\titlespacing{\section}{-1pt}{0.08 cm}{0.05 cm}
\renewcommand\labelitemi{$\vcenter{\hbox{\small$\bullet$}}$}

\newenvironment{highlights}{
    \begin{itemize}[
        topsep=0.02 cm,
        parsep=0.02 cm,
        partopsep=0pt,
        itemsep=0pt,
        leftmargin=0 cm + 10pt
    ]
}{
    \end{itemize}
}

\newenvironment{onecolentry}{
    \begin{adjustwidth}{0 cm + 0.00001 cm}{0 cm + 0.00001 cm}
}{
    \end{adjustwidth}
}

\newenvironment{twocolentry}[2][]{
    \onecolentry
    \def\secondColumn{#2}
    \setcolumnwidth{\fill, 4.5 cm}
    \begin{paracol}{2}
}{
    \switchcolumn \raggedleft \secondColumn
    \end{paracol}
    \endonecolentry
}

\newenvironment{header}{
    \setlength{\topsep}{0pt}\par\kern\topsep\centering\linespread{1.1}
}{
    \par\kern\topsep
}

\let\hrefWithoutArrow\href

\begin{document}
    \newcommand{\AND}{\unskip
        \cleaders\copy\ANDbox\hskip\wd\ANDbox
        \ignorespaces
    }
    \newsavebox\ANDbox
    \sbox\ANDbox{$|$}

    \begin{header}
        \fontsize{22 pt}{22 pt}\selectfont <<NAME>>

        \vspace{3 pt}

        \normalsize
        \mbox{<<ADDRESS>>}%
        \kern 4.0 pt%
        \AND%
        \kern 4.0 pt%
        \mbox{\hrefWithoutArrow{mailto:<<EMAIL>>}{<<EMAIL>>}}%
        \kern 4.0 pt%
        \AND%
        \kern 4.0 pt%
        \mbox{\hrefWithoutArrow{tel:<<PHONE>>}{<<PHONE>>}}%
        \kern 4.0 pt%
        \AND%
        \kern 4.0 pt%  
        \mbox{\hrefWithoutArrow{<<LINKEDIN>>}{\textcolor{blue}{Linkedin}}}%
        \kern 4.0 pt%
        \AND%
        \kern 4.0 pt%
        \mbox{\href{<<GITHUB>>}{\textcolor{blue}{Github}}}
    \end{header}

    \vspace{2 pt}

    \section{Professional Summary}
    \begin{onecolentry}
        \small <<SUMMARY>>
    \end{onecolentry}

    \vspace{0.05 cm}

    \section{Education}
    <<EDUCATION_TEX>>

    \vspace{0.05 cm}
    
    \section{Experience}
    <<EXPERIENCE_TEX>>

    \vspace{0.05 cm}

    \section{Projects}
    <<PROJECTS_TEX>>

    \vspace{0.05 cm}

    \section{Technical Skills}
    \begin{onecolentry}
        \small <<SKILLS_TEX>>
    \end{onecolentry}

\end{document}
"""