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

# Introduction

Electricity has become increasingly vital in our modern world, with per capita energy consumption more than doubling from 1978 to 2019, signaling a substantial shift in energy use patterns (World Bank, 2023). This surge is propelled not just by the global transition to electric vehicles, which promise to replace internal combustion engines, but also by other factors such as digitalisation, technological advancements, and the electrification of industries and home heating systems that once relied on fossil fuels. Additionally, the push towards sustainability has spurred the adoption of electrically powered technologies and the integration of renewable energy sources into the grid, further driving up electricity demand. 

There is a fundamental relationship between energy demand and external ambient temperature. Looking at the historic energy demand in the country, the energy demand is proportional to the external ambient temperature as the temperature dictates whether residential customers will require heating or air conditioning for comfortable living conditions. Forecasting energy demand is important for energy suppliers as it optimises profit by preventing under or over-production. In a competitive market, forecasting energy demand is essential for predicting electricity pricing and demand.  

Recalling from our project plan, our research question was to find out whether including commercial and residential solar energy production improves the energy demand forecasting accuracy. From this, we have come up with two hypotheses: 

**Null Hypothesis** ($H_0$): Temperature data alone is sufficient to reliably forecast electricity demand.

**Alternative Hypothesis** ($H_1$): Including the additional features of 'solar generation capacity' and/or 'solar radiation' improves the estimate of electricity demand.


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

**General Overview**

The data that the team will be examining is stored as CSV files in Github. It includes independent variables such as the date of the year, the location and recorded temperature; and dependent variables such as the total demand and the forecasted demand.  In total, we are dealing with 13 million, which can be considered as a large dataset. The data is a time series which can introduce more complexity in the model. This complexity, together with the size of the data are uan indicator that the usage of GPUs to accelerate the training of our model. Tools such as Google Colab Pro provide this service. 

**Dataset: totaldemand_nsw.csv, totaldemand_vic.csv, totaldemand_qld.csv, totaldemand_sa.csv, totaldemand_tas.csv1** 

This dataset contains the total energy demand around Australia from 2010 to March 2021. The demand listed in the dataset will be used to predict the demand in the next 1 to 5 years and how solar panels affects the total demand.  There are shortcoming on this dataset as the data included in the 2021 is only up to March, hence for the purpose of our research, the year of 2021 will be omitted.  

**Dataset: temperature_nsw.csv, temperature_vic.csv, temperature_qld.csv, temperature_tas.csv, temperature_sa.csv2**

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

## Modelling 

## Introduction to Modelling Methods

In this section, we present the modelling methods employed to forecast the total electricity demand in the NEM. Given the complexity of the factors influencing electricity consumption, multiple modelling approaches have been utilised to capture various patterns and dependencies in the data.

To address the challenge of forecasting electricity demand, we have deployed several statistical and machine learning models, each offering unique strengths and suited to capturing different aspects of the data. The models selected for this study include:

1. Linear Regression Model: This model leverages historical demand data to capture linear trends and seasonal variations, providing a baseline for performance comparison.
2. Neural Network Model (MLP): A Multi-Layer Perceptron (MLP), a type of neural network, is used to model non-linear relationships in the data. Its ability to learn complex patterns makes it suitable for the non-linear dynamics of electricity demand.
3. Stacked Model: Combining Generalised Boosted Models (GBM), Linear Regression, and MLP, this ensemble approach leverages the strengths of individual models to improve overall prediction accuracy. The stacking method helps in reducing the variance and bias of the forecast, capitalising on the diverse predictive capabilities of the constituent models.
4. Long Short-Term Memory (LSTM) Model: An LSTM model is specifically designed to address time-series data like electricity demand, which requires understanding long-term dependencies in data due to factors such as seasonal effects and economic cycles.

Each model has been chosen based on its potential to effectively handle the characteristics of the dataset and the specific forecasting requirements of the electricity market. The subsequent sections will detail the configuration, feature engineering, and performance evaluation of each model, providing insights into their comparative effectiveness and the rationale behind the final model selection.

## Description of Each Model

**1. Basic Linear Regression Model**

Model Overview:
Linear regression is a foundational statistical method used for modeling the relationship between a dependent variable and one or more independent variables by fitting a linear equation to observed data. The equation for a linear regression line is typically in the form:

The equation for a linear regression line is typically in the form:

$$ y = \beta_0 + \beta_1 x_1 + \dots + \beta_n x_n $$

where:
- $y$ is the predicted value,
- $\beta_0$ is the intercept,
- $\beta_i$ are the coefficients for each feature,
- $x_i$ are the feature values.

This model is well-suited for cases where the relationship between variables is expected to be linear.

Rationale for Inclusion:
The basic Linear Regression model is included in this study due to its effectiveness in providing a clear and straightforward understanding of the influences of different predictors on electricity demand. It serves as a fundamental benchmark for evaluating more complex models. The model's simplicity and interpretability are particularly valuable for initial exploratory analyses, where understanding the direct linear impact of individual factors—such as temperature, time of day, and economic indicators—on electricity demand is crucial. 

**2. Neural Network Model (MLP)**

Model Overview:
The Multi-Layer Perceptron (MLP) is a type of neural network known for its capability to model complex, non-linear relationships through its multiple layers and neurons. MLPs are widely used in pattern recognition, forecasting, and classification tasks where the relationships between variables are not easily discernible or are highly non-linear [@Nielsen2015].

The MLP model consists of multiple layers: an input layer, one or more hidden layers, and an output layer. Each layer \(l\) performs a linear transformation followed by a non-linear activation:

$$ z^{(l)} = W^{(l)}a^{(l-1)} + b^{(l)} $$
$$ a^{(l)} = \sigma(z^{(l)}) $$

Where:
- $a^{(0)}$ is the input vector,
- $W^{(l)}$ and $b^{(l)}$ are the weight matrix and bias vector for layer $l$ respectively,
- $z^{(l)}$ is the linear combination at layer $l$,
- $a^{(l)}$ is the activation after applying the non-linear function $\sigma$ at layer $l$,
- $\sigma$ is the activation function, such as Sigmoid, ReLU, or Tanh.

The output of the final layer $a^{(L)}$ is used for prediction:
$$ \hat{y} = a^{(L)} $$

This is the forward propagation mechanism. Learning in MLPs involves adjusting $W^{(l)}$ and $b^{(l)}$ through backpropagation to minimize the loss function comparing $\hat{y}$ and the actual target outputs.

Rationale for Inclusion:
The MLP model is included in this project to leverage its ability to capture intricate patterns in the data that simpler models might miss. The non-linear dynamics of electricity demand, influenced by numerous factors such as economic activity, unpredictable weather conditions, and changes in consumer behaviour, make MLP a suitable choice. 

**3. Stacked Model**

Model Overview:
A stacked model is an ensemble technique that combines the predictions from multiple individual models to produce a final output. The stacking method involves training a meta-model to synthesise the outputs of the base models into a single prediction, aiming to reduce bias and variance. In this specific application, the stacked model includes Generalised Boosted Models (GBM), Linear Regression, and a Multi-Layer Perceptron (MLP). Each base model independently processes the input data and makes predictions which are then used as inputs for the meta-model [@Wolpert1992].

For example, suppose we have $n$ base models, where each model $m_i$ provides a prediction $p_i$ for the same input data $x$. The predictions of these base models are then used as input features for the meta-model.

The process can be summarized by the following equations:

1. Each base model $m_i$ predicts the output:
$$ p_i = m_i(x) \quad \text{for} \ i = 1, 2, \ldots, n $$

2. The meta-model $M$ takes these predictions as inputs and combines them to produce the final prediction $\hat{y}$:
$$ \hat{y} = M(p_1, p_2, \ldots, p_n) $$

where:
- $x$ is the input data,
- $p_i$ is the prediction from the $i$-th base model,
- $\hat{y}$ is the final output from the meta-model.

The meta-model is trained to optimize the combination of base models' outputs, effectively learning the best way to integrate different predictive signals to minimise the overall prediction error.


Rationale for Inclusion:
The rationale for including a stacked model in this study is rooted in its ability to leverage the diverse strengths of various models to improve overall forecasting accuracy. Each of the selected base models — GBM, Linear Regression, and MLP — captures different aspects and complexities of the electricity demand forecasting problem:

GBM is adept at handling nonlinear relationships and interactions between variables, making it valuable for complex, hierarchical data structures.
Linear Regression provides clear insights into the linear relationships and is highly interpretable, which is useful for understanding direct impacts and trends.
MLP, with its deep learning capabilities, is good at at identifying patterns and dependencies in large datasets that might be non-linear or hidden.
By stacking these models, we aim to mitigate the individual weaknesses of each model and enhance prediction stability. The meta-model, a simpler model like linear regression, is trained on the predictions of the base models, ensuring that the final predictions are not just a simple average but a  weighted combination that considers how each model performs in various scenarios. 

**4. Long Short-Term Memory (LSTM) Model**

Model Overview:
Long Short-Term Memory (LSTM) models are a kind of Recurrent Neural Network (RNN) particularly well-suited to classifying, processing, and predicting time series data given time lags of unknown duration between important events. Unlike standard feedforward neural networks, LSTMs have feedback connections that allow them to process not just individual data points, but entire sequences of data [@Hochreiter1997]. This feature makes them ideal for tasks where context from the input data is crucial, such as speech recognition, language modeling, and, importantly, time-series forecasting like electricity demand.

An LSTM model is composed of various gates that control the flow of information. These gates include the forget gate, input gate, and output gate, which work together to update and maintain the cell state across time steps. The equations that govern the behavior of an LSTM unit are as follows [@Chung2014]:

1. **Forget Gate:**
   $$ f_t = \sigma(W_f \cdot [h_{t-1}, x_t] + b_f) $$
   This gate decides what information to discard from the cell state. It looks at $h_{t-1}$ (the previous hidden state) and $x_t$ (the current input), and applies a sigmoid function.

2. **Input Gate:**
   $$ i_t = \sigma(W_i \cdot [h_{t-1}, x_t] + b_i) $$
   $$ \tilde{C}_t = \tanh(W_C \cdot [h_{t-1}, x_t] + b_C) $$
   The input gate updates the cell state by first deciding which values to update (using $i_t$), and then creating a vector of new candidate values ($\tilde{C}_t$) that could be added to the state.

3. **Update Cell State:**
   $$ C_t = f_t * C_{t-1} + i_t * \tilde{C}_t $$
   The cell state $C_t$ is updated by forgetting the old state as decided by $f_t$ and adding new candidate values scaled by $i_t$.

4. **Output Gate:**
   $$ o_t = \sigma(W_o \cdot [h_{t-1}, x_t] + b_o) $$
   $$ h_t = o_t * \tanh(C_t) $$
   The output gate decides what the next hidden state should be. The state $C_t$ is passed through $\tanh$, which is then scaled by $o_t$ to decide the output $h_t$.

where:
- $x_t$ is the input vector at time step $t$,
- $h_t$ is the hidden state at time step $t$,
- $C_t$ is the cell state at time step $t$,
- $W$ and $b$ are the weights and biases for different gates,
- $\sigma$ is the sigmoid activation function,
- $\tanh$ is the hyperbolic tangent activation function.

These components work together to allow the LSTM to maintain a long-term memory, making it particularly effective for time-series data where the context from previous events is crucial for understanding the current state.


Rationale for Inclusion:
The decision to include an LSTM model in this study stems from its proven capability in handling sequential data with dependencies over time, which is a common characteristic of electricity usage data [@Huang2016]. Electricity demand forecasting involves understanding patterns that unfold over time, influenced by factors such as weather, time of day, and economic conditions. Traditional models often struggle with capturing these temporal dynamics effectively, especially when the sequences have long time dependencies.

LSTMs are designed to overcome the vanishing gradient problem that can occur with standard RNNs in the training process, allowing them to learn from data where important events are separated by long time lags. This capability is critical for accurately predicting electricity demand where previous consumption patterns and external factors like weather conditions can significantly influence future demand.

# Feature Engineering

Feature engineering was a fundamental step in the data preprocessing pipeline that significantly enhanced model performance. By transforming raw data into new features, our models signficantly improved performance over the baseline. 

**Engineered Features:**

1. Cooling Degree Days (CDD) Feature:

Description: The 'Cooling' feature represents the Cooling Degree Days, calculated as the number of degrees where the temperature is above a certain threshold (24°C here), indicating the energy demand for cooling.

Justification: This feature is essential in Australia where air conditioning is widely used. A temperature above 24°C would typically result in increased electricity usage for cooling, making this a relevant predictor for demand forecasting.

2. Heating Degree Days (HDD) Feature:

Description: The 'Heating' feature represents the Heating Degree Days, calculated as the number of degrees where the temperature is below a certain threshold (20°C here), indicating the energy demand for heating.

Justification: Similar to CDD, HDD accounts for additional energy demand for heating when the temperature drops below a comfortable threshold, a key consideration for accurate demand prediction in cooler seasons.

3. Weekend Indicator Feature:
   
Description: The 'is_weekend' binary feature indicates whether a given date falls on a weekend.

Justification: Electricity patterns often differ on weekends due to changes in commercial activity and personal routines. Recognising weekends can help the model adjust its forecasts accordingly.

4. Seasonal Feature:
   
Description: The 'season' feature categorizes dates into seasons ('Summer', 'Autumn', 'Winter', 'Spring') based on the month.

Justification: Seasonal variations significantly affect energy consumption due to weather-related changes in heating and cooling needs. This categorization aligns with Australia's distinct seasons, which correspond to varying energy usage profiles throughout the year.

5. Public Holiday Feature:
   
Description: A binary feature derived from the 'public_holidays' dataset, indicating whether a date is a public holiday.

Justification: Public holidays usually mean a reduction in commercial activity and can affect residential electricity consumption patterns. Including this feature helps in predicting atypical demand associated with holidays.


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



