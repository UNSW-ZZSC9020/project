---
title: "Exploring the Impacts of Residential And Commercial Solar Power Production on Grid Demand"
team: Group G – Watt’s Up Down Under
session: Hexamester 2, 2024
coursecode: ZZSC9020
author: 
- Bernard Lo (z3464235)
- Andrew Ryan (z2251397)
- Chadi Abi Fadel (z5442788)
- Joshua Evans (z5409600)

date: "23/04/2024"
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
Here is a test of an image
![Test cat in suit](img/cat_caviar.jpg)

_Template text is in italics_
# Abstract

There is a well-known relationship between electricity demand and temperature in the electricity industry, most commercial power suppliers use temperature to forecast energy demand. More and more Australian homes are considering adding solar panels as a source of renewable energy, the team is interested in whether adding solar power as another variable will improve the accuracy of the model that is currently being used. By using convolutional neural network (CNN) and long short-term memory (LSTM) models, we improved the accuracy of the energy forecasting by implementing the solar power output dataset along with the temperature dataset that were originally used. Using temperature and solar power datasets from 2017 to 2021, the team concluded that both CNN and LSTM modelling techniques provided more accurate energy forecasting and comparing both models, LSTM is the superior model over CNN. The findings from this experiment suggested that energy providers should consider implementing datasets from various renewable sources to improve its modelling accuracy in order to improve energy pricing and reduce wastage.  

## Josh is testing editing the MD File here

# Introduction

Electricity has become increasingly vital in our modern world, with per capita energy consumption more than doubling from 1978 to 2019, signaling a substantial shift in energy use patterns (World Bank, 2023). This surge is propelled not just by the global transition to electric vehicles, which promise to replace internal combustion engines, but also by other factors such as digitalisation, technological advancements, and the electrification of industries and home heating systems that once relied on fossil fuels. Additionally, the push towards sustainability has spurred the adoption of electrically powered technologies and the integration of renewable energy sources into the grid, further driving up electricity demand. 

There is a fundamental relationship between energy demand and external ambient temperature. Looking at the historic energy demand in the country, the energy demand is proportional to the external ambient temperature as the temperature dictates whether residential customers will require heating or air conditioning for comfortable living conditions. Forecasting energy demand is important for energy suppliers as it optimises profit by preventing under or over-production. In a competitive market, forecasting energy demand is essential for predicting electricity pricing and demand.  

Recalling from our project plan, our research question was to find out whether including commercial and residential solar energy production improves the energy demand forecasting accuracy. From this, we have come up with two hypotheses: 

 Null Hypothesis: Temperature data alone is sufficient to reliably forecast electricity demand 

Alternative Hypothesis: Including the additional features of 'solar generation capacity' and/or 'solar radiation' improves the estimate of electricity demand.

In order to test the hypotheses, the team would require more dataset, e.g. solar power generation data and public holidays, etc. These datasets are not provided and are significantly related to our hypotheses. From the project plan, the team has chosen LSTM as the main method for modelling. 2 models will then be built and compared in order to test if the hypotheses we listed above is valid. 

Since the data used only ranges from 2017 to 2021, hence there are limitation in terms of accuracy for the model. Moreover, we are only specifically including solar power generation but no other renewable energy sources, this may also affect the accuracy of the final result. 

# Literature Review

For the purpose of analysis our dataset, we have ultilised CNN and LSTM technique for analysis electricty demand. 
_Here are a few references that can be useful: [@Xie2018] and [@Lafaye2013]. See also https://bookdown.org/yihui/rmarkdown-cookbook/. In order to incorporate your own references in this report, we strongly advise you use BibTeX. Your references then needs to be recorded in the file `references.bib`._


# Material and Methods

A Jupyter notebook describing the steps taken in our analysis can be found in `~/report/Wattsup_energy_forecast.ipynb`. Following is a description.
## Loading the given dataset
**Chadi to complete**
Python was used to extract, transform and to load the data (ETL) into our notebook for further Exploratory Data Analysis (EDA) and modelling.
Unzipping programmatically ensures the repeatability of the data extraction process while ensuring that no human errors were introduced in the process as the number of files grows
- unzip
-

## Refactoring and simplifying the code
**Chadi to complete**

## Scraping PV data
**Chadi to complete**

_R and Python of course are great software for Data Science. Sometimes, you might want to use `bash` utilities such as `awk` or `sed`._

_Of course, to ensure reproducibility, you should use something like `Git` and RMarkdown (or a Jupyter Notebook). Do **not** use Word!_

## Description of the Data

General Overview 
The data that the team will be examining is stored as CSV files in Github. It includes independent variables such as the date of the year, the location and recorded temperature; and dependent variables such as the total demand and the forecasted demand.  In total, we are dealing with 13 million, which can be considered as a large dataset. The data is a time series which can introduce more complexity in the model. This complexity, together with the size of the data are uan indicator that the usage of GPUs to accelerate the training of our model. Tools such as Google Colab Pro provide this service. 

Dataset: totaldemand_nsw.csv, totaldemand_vic.csv, totaldemand_qld.csv, totaldemand_sa.csv, totaldemand_tas.csv1 
This dataset contains the total energy demand around Australia from 2010 to March 2021. The demand listed in the dataset will be used to predict the demand in the next 1 to 5 years and how solar panels affects the total demand.  There are shortcoming on this dataset as the data included in the 2021 is only up to March, hence for the purpose of our research, the year of 2021 will be omitted.  
Dataset: temperature_nsw.csv, temperature_vic.csv, temperature_qld.csv, temperature_tas.csv, temperature_sa.csv2 
This dataset records the temperature data from across Australia from 2010 to March 2021. Do note that this set of data only records the temperature from one location in the state. The temperature listed in the dataset will be used to predict the demand in the next 1 to 5 years and how solar panels affects the total demand. Again, this dataset has the same shortcomings with the previous dataset as the data included in the 2021 is only up to March, hence for the purpose of our research, the year of 2021 will be omitted as well. Another shortcoming is that the temperatures recorded in QLD and in SA are identical. This might be due to a an error with data storage and loading.   


How are the data stored? What are the sizes of the data files? How many files? etc.



## Pre-processing Steps
Andrew Ryan to complete
What did you have to do to transform the data so that they become useable?

Step 1:Unzip the files and import the data
Steo 2: Check for duplicate data records
Step 2:visualise

<!---
![alt text](duplicate_check_victoria-1.png)
--->


## Data Cleaning
Andrew Ryan to complete
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

<!--
![](unsw-ZZSC9020-report-template_files/figure-latex/unnamed-chunk-1-1.pdf) --> 

## Using Python {.fragile}

<!-- See https://cran.r-project.org/web/packages/reticulate/vignettes/r_markdown.html for more details.

\bigskip

You need to install the R package `reticulate`. -->


```python
# Key Libraries Used
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import xgboost as xgb
color_pal = sns.color_palette()
import time

from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, StackingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split

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



