---
title: "A Data Science Approach to Forecast Electricity Consumption in Australia"
team: 22
session: Term 1, 2021
coursecode: MATH0000
author: 
  - "John Student (z123456), "
  - "Jim Student2 (zID), "
  - "Jack Student3 (zID)." 
date: "25/07/2020"
Acknowledgements: 
  - "By far the greatest thanks must go to my supervisor for the guidance, care and support they provided."
  - "Thanks must also go to Emily, Michelle, John and Alex who helped by proof-reading the document in the final stages of preparation."
  - "Although I have not lived with them for a number of years, my family also deserve many thanks for their encouragement. Thanks go to Robert Taggart for allowing his thesis style to be shamelessly copied."
Abstract: "The image below gives you some hint about how to write a good abstract.\\par  \\bigskip ![](good-abstract.png){width=10cm height=10cm}"
output:
  pdf_document:
    template: template.tex
    md_extensions: +raw_attribute
    keep_md: true 
    keep_tex: true 
    pandoc_args:
    - --top-level-division="chapter"
    - --bibliography="references.bib"
    toc: true
    toc_depth: 1
    number_sections: true
    fig_caption: yes
  word_document:
    toc: true
    toc_depth: 1
    number_sections: true
    fig_caption: true
bibliography: references.bib
csl: university-of-south-wales-harvard.csl
---




# Introduction {.label:s-intro}

This R Markdown template can be used for the ZZSC9020 course report. You can incorporate R [@R] chunks and Python chunks that will be run on the fly. You can incorporate \LaTeX\ commands.

\bigskip

Before submitting the last version of your report, you might want to use https://overleaf.com to collaborate with other members of your team directly on the \LaTeX\ version of this document (which is a byproduct you get when you Knit it from studio).

\bigskip

We suggest you organise your report using the following chapters but, depending on your own project, nothing prevents you to have a different organisation.

# Literature Review

Here are a few references that can be useful: [@Xie2018] and [@Lafaye2013]. See also https://bookdown.org/yihui/rmarkdown-cookbook/

\bigskip

In order to incorporate your own references in this report, we strongly advise you use BibTeX. Your references then needs to be recorded in the file `references.bib`.


# Material and Methods

## Software

R and Python of course are great software for Data Science. Sometimes, you might want to use `bash` utilities such as `awk` or `sed`.

Of course, to ensure reproducibility, you should use something like `Git` and RMarkdown (or a Jupyter Notebook). Do **not** use Word!

## Description of the Data

How are the data stored? What are the sizes of the data files? How many files? etc.

## Pre-processing Steps

What did you have to do to transform the data so that they become useable?

## Data Cleaning

How did you deal with missing data? etc. 

## Assumptions

What assumptions are you making on the data?

## Modelling Methods

# Exploratory Data Analysis

This is where you explore your data using histograms, scatterplots, boxplots, numerical summaries, etc.

## Using R {.fragile}


```r
boxplot(cars, col = c("#5975a4", "#cc8963"))
```

![](unsw-ZZSC9020-report-template_files/figure-latex/unnamed-chunk-1-1.pdf)<!-- --> 

## Using Python {.fragile}

See https://cran.r-project.org/web/packages/reticulate/vignettes/r_markdown.html for more details.

\bigskip

You need to install the R package `reticulate`.


```python
print("Python can be used with MATHxxxx!")
```

```
## Python can be used with MATHxxxx!
```

```python
import sys
print(sys.version)
```

```
## 3.6.13 (default, Feb 19 2021, 05:17:09) [MSC v.1916 64 bit (AMD64)]
```



```python
import numpy as np
np.random.seed(1)
np.random.normal(0.0, 1.0, size=10)
```

```
## array([ 1.62434536, -0.61175641, -0.52817175, -1.07296862,  0.86540763,
##        -2.3015387 ,  1.74481176, -0.7612069 ,  0.3190391 , -0.24937038])
```


```python
import pandas as pd
import matplotlib.pyplot as plt
df=pd.DataFrame([[1, 2], [3, 4], [4, 3], [2, 3]])
fig = plt.figure(figsize=(4, 4))
for i in df.columns:
    ax=plt.subplot(2,1,i+1) 
    df[[i]].plot(ax=ax)
    print(i)

plt.show()
```

![](unsw-ZZSC9020-report-template_files/figure-latex/unnamed-chunk-4-1.pdf)<!-- --> 


# Analysis and Results

## A First Model

Having a very simple model is always good so that you can benchmark any result you would obtain with a more elaborate model.

\bigskip

For example, one can use the linear regression model

$$
Y_i = \beta_0 + \beta_1 x_{1i} + \cdots \beta_p x_{pi} + \epsilon_i, \qquad i=1,\ldots,n.
$$
where it is assumed that the $\epsilon_i$'s are i.i.d.\ $N(0,1)$.

# Discussion

Put the results you got in the previous chapter in perspective with respect to the problem studied.

# Conclusion and Further Issues {.label:ccl}

What are the main conclusions? What are your recommendations for the "client"? What further analysis could be done in the future?

A figure:

![A caption \label{myfigure}](unsw-logo.png){width="6cm" height="2cm"}

In the text, see Figure \ref{myfigure}.


# References {-}

<div id="refs"></div>

\bibliographystyle{elsarticle-harv}
\bibliography{references}

# Appendix {-}

## **Codes** {-}

Add you codes here.

## **Tables** {-}

If you have tables, you can add them here.

Use https://www.tablesgenerator.com/markdown_tables to crete very simple markdown tables, otherwise use \LaTeX.

| Tables   |      Are      |  Cool |
|----------|:-------------:|------:|
| col 1 is |  left-aligned | $1600 |
| col 2 is |    centered   |   $12 |
| col 3 is | right-aligned |    $1 |



