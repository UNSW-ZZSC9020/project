# Electric Load Forecasting System

A deep learning and ensemble learning-based electric load forecasting research project that implements multiple machine learning models for 48-hour electric load prediction in New South Wales (NSW), Australia.

## Project Overview

This project implements 13 different prediction models, including traditional time series models, deep learning models, and advanced ensemble learning models for high-precision electric load forecasting. The project adopts rigorous experimental design and evaluates model performance through RMSE.

## Core Features

- **Multi-model Architecture**: Integrates 13 prediction models covering time series, deep learning, and ensemble learning methods
- **48-hour Prediction**: Supports 48-hour future electric load forecasting
- **Real-time Data Processing**: High-frequency data processing and prediction at 30-minute intervals
- **Uncertainty Quantification**: Bayesian neural networks provide prediction uncertainty estimation
- **Automated Evaluation**: Complete model evaluation and comparison framework
- **Visualization Analysis**: Comprehensive data and result visualization

## Project Structure

```
Load_2025/
├── main.py                      # Main program entry
├── data_preprocessor.py         # NSW data preprocessor
├── visualizer.py               # Data visualization tools
├── style.py                    # Chart style configuration
├── ModelEvaluator.py           # Model evaluator
│
├── Basic Prediction Models/
│   ├── time_series_predictor.py    # Time series predictor
│   ├── prophet_predictor.py        # Prophet predictor
│   ├── MLP_predictor.py           # Multi-layer perceptron
│   ├── CNN_predictor.py           # Convolutional neural network
│   ├── BNN_predictor.py           # Bayesian neural network
│   └── LSTM_predictor.py          # Long short-term memory network
│
├── Ensemble Learning Models/
│   ├── XGBoost_ensemble.py         # XGBoost ensemble
│   └── RandomForests_ensemble.py  # Random forest ensemble
│
├── Stacking Ensemble Models/
│   ├── Stack_CNN_LSTM.py          # CNN+LSTM two-layer stacking
│   ├── Stack_CNN_XGBoost.py       # CNN+XGBoost two-layer stacking
│   ├── Stack_LSTM_XGBoost.py      # LSTM+XGBoost two-layer stacking
│   └── Stack_CNN_LSTM_XGBoost.py  # CNN+LSTM+XGBoost three-layer stacking
│
├── Hybrid Models/
│   └── Hybrid_CNN_LSTM_XGBoost.py # Hybrid CNN+LSTM+XGBoost
│
├── data/                       # Data directory
│   ├── NSW/                    # New South Wales data
│   │   ├── temperature_nsw.csv # Temperature data
│   │   └── totaldemand_nsw.csv # Load demand data
│   └── Australia/              # Other state data
│
├── outputs/                    # Output directory
│   ├── plots/                  # Visualization results
│   ├── logs/                   # Runtime logs
│   ├── RMSE_results/          # RMSE evaluation results
│   └── model_outputs/         # Model prediction outputs
│
├── requirements.txt            # Package dependencies
└── README.md                  # Project documentation
```

## Model Architecture

### Basic Models
1. **Time Series Predictor** (`time_series_predictor.py`) - Traditional method based on similar pattern matching
2. **Prophet Predictor** (`prophet_predictor.py`) - Facebook's open-source time series forecasting tool
3. **Multi-layer Perceptron** (`MLP_predictor.py`) - Deep neural network basic model
4. **Convolutional Neural Network** (`CNN_predictor.py`) - For capturing local temporal patterns
5. **Bayesian Neural Network** (`BNN_predictor.py`) - Probabilistic model providing uncertainty quantification
6. **Long Short-term Memory Network** (`LSTM_predictor.py`) - Specialized for handling long-term temporal dependencies

### Ensemble Learning Models
7. **XGBoost Ensemble** (`XGBoost_ensemble.py`) - Gradient boosting decision trees
8. **Random Forest Ensemble** (`RandomForests_ensemble.py`) - Multi-decision tree ensemble

### Stacking Ensemble Models
9. **CNN+LSTM Stacking** (`Stack_CNN_LSTM.py`) - Two-layer stacking architecture
10. **CNN+XGBoost Stacking** (`Stack_CNN_XGBoost.py`) - Combination of deep learning and gradient boosting
11. **LSTM+XGBoost Stacking** (`Stack_LSTM_XGBoost.py`) - Combination of sequence modeling and gradient boosting
12. **CNN+LSTM+XGBoost Stacking** (`Stack_CNN_LSTM_XGBoost.py`) - Three-layer stacking architecture

### Hybrid Models
13. **Hybrid CNN+LSTM+XGBoost** (`Hybrid_CNN_LSTM_XGBoost.py`) - Multi-branch parallel fusion architecture

## Installation Requirements

### System Requirements
- Python 3.8+
- CUDA support (optional, for GPU acceleration)

### Dependency Installation
```bash
pip3 install -r requirements.txt
```

### Main Dependencies
- **Deep Learning Frameworks**: TensorFlow 2.18.0, PyTorch 2.5.1
- **Data Processing**: pandas 2.2.3, numpy 1.26.3
- **Machine Learning**: scikit-learn 1.6.0, xgboost 2.1.3
- **Time Series**: prophet 1.1.6
- **Visualization**: matplotlib 3.10.0, seaborn 0.13.2

## Data Format

### Input Data Format
The project uses two main data files:

**Temperature Data** (`temperature_nsw.csv`):
```csv
LOCATION,DATETIME,TEMPERATURE
Bankstown,1/1/2010 0:00,23.1
Bankstown,1/1/2010 0:30,22.9
```

**Load Demand Data** (`totaldemand_nsw.csv`):
```csv
DATETIME,TOTALDEMAND,REGIONID
1/1/2010 0:00,8038,NSW1
1/1/2010 0:30,7809.31,NSW1
```

## Usage

### Basic Execution
```bash
python main.py
```

### Execution Flow
The program executes the following steps:
1. **Environment Check** - Verify software versions and GPU availability
2. **Data Preprocessing** - Data cleaning, feature engineering, and standardization
3. **Data Visualization** - Generate data analysis charts
4. **Model Training** - Train all 13 models sequentially
5. **Result Evaluation** - Calculate RMSE and generate comparison charts

## Output Files

### Runtime Logs (`logs/`)
Records detailed model training and evaluation processes, including:
- Version check information
- Data preprocessing details
- Model training progress
- Performance evaluation results

### Visualization Results (`plots/`)
- Time series analysis charts
- Correlation analysis charts
- Daily/weekly pattern analysis charts
- Feature distribution charts

### Evaluation Results (`RMSE_results/`)
- RMSE comparison charts for each model
- Detailed performance evaluation reports

### Model Outputs (`model_outputs/`)
- Prediction results from each model
- Model prediction visualization charts

## Notes

1. Ensure GPU drivers and CUDA environment are properly installed for optimal performance
2. Required output directories will be automatically created on first run
3. Large model training may take considerable time; recommend running in high-performance computing environment
4. Log files are named with timestamps for tracking different run results

## Citation

If using this project for research, please cite the related paper:
```
Development and Evaluation of Ensemble Learning and Deep Learning Models for Electric Load Forecasting
```

## Technical Support

For issues or technical support, please refer to:
- Runtime log files (logs directory)
- Model evaluation results (RMSE_results directory)
- Detailed error output information

---

