# Welcome to ZZSC9020 GitHub repository for group A

This GitHub repository is the main point of access for students and lecturers of the ZZSC9020 capstone course. 

In this repository, you will find the data to start developing your project. Also, we will use the repository to share code, documentation, data, models and other resources between the group members and course lecturers.

Complete the information below regarding your group.

## Group and project information

### Group members and zIDs
- Brendan	(z5632728): Research consultant and Model analysis of SARIMAX + LSTM + Comparison
- Daniel	(z5623647): Presentation/Communication Lead and Model analysis of Gradient Boosting + LSTM
- Kam	(z5618444):     Project Manager, Presentation/Communication Lead and Model lead of PatchTST
- Kelvin (z5502200):	Logistics coordinator, Code Refactorer, Model lead of PatchTST + SARIMAX + Comparison


### Brief project description

Describe your project in one paragraph.

## Repository structure

The repository has the following folder structure:

- agendas: agendas for each weekly meeting with lecturers (left 24h before the next meeting)
- checklists: teamwork checklist or a link to an account in a project task management tool
- data: datasets for analysis
- gantt_chart: Gantt chart or a link to an account in a project task management tool
- minutes: minutes for each meeting (left not more than 24h after the corresponding meeting)
- report: RMarkdown or Jupyter notebook report in progress
- src: source code
    - ModelEvaluation: test loops on test data to retrieve RMSE and other metrics on best models
    - ModelTuning: training/validation loops on best models to retrieve validation RMSE and other metrics on candidate models
    - ModelFiles: code files that house different models we used to compare. 
        - PatchTST_supervised: houses PatchTST code. Taken from PatchTST authors (yuqinie98, 2025) and adapted for our use case
        - GradientBoosting / LSTM: additional utility functions for these models
        - BasicModels.py / GroupAModels.py: holds the model classes. Gradient Booster and SARIMAX codes implemented by Scikit-learn.org., 2009 and ‌www.statsmodels.org respectively
        - ModelConfigs.py: config classes used to standaradize inputs into the model classes
        - ModelPlots.py: graphing functions to generate plots for the report
    - NSWData: code files for datasets and dataloaders used commonly by the model classes
        - NSWDataloader.py: extracts, pre-processes and train/val/test splitting of raw data files from data/NSW and saves it back into the folder
        - NSWDataSet.py: torch data sets used in the training/testing loops of LSTM and PatchTST
    - best_models.ipynb: notebook for analysis on validation data on candidate models to get best models for each family
    - model_plots.ipynb: notebook for plotting predictions vs actuals used in the reporting
    - model_test_results.ipynb: consolidates test metric results of best models and outputs tables for reporting
    - others: draft notebooks used to refactor code and Exploratory Data Analysis notebook

### Code References
Scikit-learn.org. (2009). 3.2.4.3.6. sklearn.ensemble.GradientBoostingRegressor — scikit-learn 0.21.2 documentation. [online] Available at: https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.GradientBoostingRegressor.html.

‌www.statsmodels.org. (n.d.). statsmodels.tsa.statespace.sarimax.SARIMAX — statsmodels. [online] Available at: https://www.statsmodels.org/dev/generated/statsmodels.tsa.statespace.sarimax.SARIMAX.html.

‌yuqinie98 (2025). GitHub - yuqinie98/PatchTST: An offical implementation of PatchTST: ‘A Time Series is Worth 64 Words: Long-term Forecasting with Transformers.’ (ICLR 2023) https://arxiv.org/abs/2211.14730. [online] GitHub. Available at: https://github.com/yuqinie98/PatchTST?tab=readme-ov-file [Accessed 14 Apr. 2026].