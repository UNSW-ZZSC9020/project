import os
import logging
import time
from datetime import datetime, timedelta
from functools import wraps
import sys
import torch
import numpy as np
import pandas as pd
import sklearn
import tensorflow as tf
import random

from matplotlib import pyplot as plt
from sklearn.metrics import mean_squared_error

os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'  # 关闭 oneDNN 优化
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # 控制日志级别
os.environ['PYTHONHASHSEED'] = '0'  # 确保 Python hash 种子固定

from style import setup_plot_style
from data_preprocessor import NSWDataPreprocessor
from visualizer import Visualizer
from time_series_predictor import TimeSeriesPredictor
from prophet_predictor import ProphetPredictor
from MLP_predictor import MLPPredictor
from BNN_predictor import BNNPredictor
from CNN_predictor import CNNPredictor
from LSTM_predictor import LSTMPredictor
from XGBoost_ensemble import XGBoostEnsemblePredictor
from RandomForests_ensemble import RandomForestsPredictor
from ModelEvaluator import ModelEvaluator
from Stack_CNN_LSTM import StackCNNLSTMPredictor
from Stack_CNN_XGBoost import StackCNNXGBoostPredictor
from Stack_LSTM_XGBoost import StackLSTMXGBoostPredictor
from Stack_CNN_LSTM_XGBoost import StackCNNLSTMXGBoostPredictor
from Hybrid_CNN_LSTM_XGBoost import HybridPredictor

###########################################################创建logs文件夹
# 确保logs文件夹存在
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

###########################################################日志记录
# 创建logger对象
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# 创建文件处理器
file_handler = logging.FileHandler(
    os.path.join(log_dir, f'{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.log'),
    mode='a'
)
file_handler.setLevel(logging.INFO)

# 创建控制台处理器
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# 创建格式器
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# 将处理器添加到logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)


###########################################################函数名称输出装饰器
def fun_name(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        logging.info(f"{'=' * 10}Function \"{func.__name__}\" Is Running.{'=' * 20}")
        try:
            result = func(*args, **kwargs)
            logging.info(f"{'=' * 10}Function \"{func.__name__}\" Is Done.{'=' * 23}\n")
            return result
        except Exception as e:
            logging.error(f"Error in function {func.__name__}: {str(e)}")
            raise

    return wrapper


###########################################################版本检查
@fun_name
def version_check():
    versions = {
        "Python": sys.version,
        "PyTorch": torch.__version__,
        "NumPy": np.__version__,
        "Pandas": pd.__version__,
        "Scikit-learn": sklearn.__version__,
        "Tensorflow": tf.__version__
    }

    # 记录基本版本信息
    for name, version in versions.items():
        logging.info(f"{name} version: {version}")

    # CUDA 信息检查
    if torch.cuda.is_available():
        logging.info("CUDA is available")
        device_count = torch.cuda.device_count()
        logging.info(f'GPU count: {device_count}')

        device = torch.device("cuda:0")
        gpu_properties = torch.cuda.get_device_properties(device)
        logging.info(f"GPU Name: {gpu_properties.name}")
        logging.info(f"GPU Memory: {gpu_properties.total_memory / 1024 / 1024:.2f} MB")

        versions.update({
            "CUDA_available": True,
            "GPU_count": device_count,
            "GPU_name": gpu_properties.name,
            "GPU_memory": f"{gpu_properties.total_memory / 1024 / 1024:.2f} MB"
        })
    else:
        logging.info("CUDA is not available")
        versions["CUDA_available"] = False


###########################################################设置随机种子
@fun_name
def set_random_seed(seed):
    """设置所有相关的随机种子以确保结果可重复"""
    logging.info(f"Random Seed: {seed}")
    random.seed(seed)  # Python 随机数生成器
    np.random.seed(seed)  # NumPy 随机数生成器
    tf.random.set_seed(seed)  # TensorFlow 随机数生成器
    torch.manual_seed(seed)  # PyTorch CPU 随机数生成器
    if torch.cuda.is_available():  # PyTorch GPU 随机数生成器
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)  # 如果使用多个 GPU
        torch.backends.cudnn.deterministic = True  # 确保 CUDNN 后端的确定性
        torch.backends.cudnn.benchmark = False  # 关闭 CUDNN 的自动优化


###########################################################数据处理
@fun_name
def process_data():
    preprocessor = NSWDataPreprocessor(window_size=1440)  # 24小时

    # 准备数据
    X_train, X_test, y_train, y_test, feature_names, df = preprocessor.prepare_data(
        'data/NSW/temperature_nsw.csv',
        'data/NSW/totaldemand_nsw.csv'
    )

    if X_train is not None:
        logging.info("Data preprocessing completed:")
        logging.info(f"Training set shape: {X_train.shape}")
        logging.info(f"Test set shape: {X_test.shape}")
        logging.info(f"Number of features: {len(feature_names)}")
        logging.info("Feature list:")
        for i, feature in enumerate(feature_names):
            logging.info(f"{i + 1}. {feature}")

    return X_train, X_test, y_train, y_test, feature_names, df


###########################################################可视化
@fun_name
def create_visualizations(df, feature_names, save_dir='plots'):
    """
    创建全面的数据可视化

    参数:
    df: pd.DataFrame - 包含特征和目标变量的数据框
    feature_names: List[str] - 特征名称列表
    save_dir: str - 图表保存目录
    """
    # 使用自定义的可视化器
    visualizer = Visualizer(save_dir)
    logging.info("Starting comprehensive data visualization...")

    try:
        # 1. 时间序列分析
        numeric_columns = df.select_dtypes(include=['float64', 'int64']).columns.tolist()
        if 'timestamp' in df.columns and len(numeric_columns) > 0:
            time_series_cols = [col for col in numeric_columns if col != 'timestamp'][:2]
            logging.info(f"1. Analyzing time series for columns: {time_series_cols}")
            visualizer.plot_time_series(
                df,
                columns=time_series_cols,
                title='Time Series Analysis'
            )

        # 2. 温度-负载相关性分析
        temp_load_features = ['temperature', 'load', 'temp_rolling_mean_24h', 'load_rolling_mean_24h',
                              'temp_rolling_std_24h', 'load_rolling_std_24h', 'temp_load_interaction'
                              ]
        logging.info(f"2. Analyzing correlations between {len(temp_load_features)} features")
        visualizer.plot_correlation_heatmap(df, temp_load_features)

        # 3. 每日负载模式
        if 'load' in df.columns and 'timestamp' in df.columns:
            logging.info("3. Analyzing daily load patterns")
            visualizer.plot_daily_pattern(df)

        # 4. 每周负载模式
        if 'load' in df.columns and 'timestamp' in df.columns:
            logging.info("4. Analyzing weekly load patterns")
            visualizer.plot_weekly_pattern(df)

        # 5. 温度与负载关系
        if all(col in df.columns for col in ['temperature', 'load']):
            logging.info("5. Analyzing temperature-load relationship")
            visualizer.plot_temp_load_relationship(df)

        # 6. 波动率分析（分别绘制年度、季度、月度）
        if all(col in df.columns for col in ['temperature', 'load', 'timestamp']):
            logging.info("6. Analyzing volatility patterns")
            visualizer.plot_yearly_volatility(df)
            visualizer.plot_quarterly_volatility(df)
            visualizer.plot_monthly_volatility(df)

        # 7. 特征分布图
        if 'load' in df.columns and 'temperature' in df.columns:
            logging.info("7. Analysis feature distributions")
            visualizer.plot_feature_distributions(df, ['load', 'temperature'])

        logging.info("Data visualization completed successfully")

    except Exception as e:
        logging.error(f"Error during visualization: {str(e)}")
        raise


###########################################################单个模型操作
@fun_name
def run_single_model(model, model_name: str, X_train, X_test, y_train, y_test, df: pd.DataFrame,
                     eval_dir: str, model_dir: str):
    """
    执行单个模型的预测和评估
    """
    logging.info(f"{'>' * 10} {model_name} {'>' * 10}")

    try:
        # 执行训练和预测
        train_df = df.iloc[:len(X_train) + len(y_train)]  # 对应训练数据的原始dataframe
        test_df = df.iloc[len(X_train):]  # 对应测试数据的原始dataframe

        predictions_df = model.predict_with_split(X_train, y_train, X_test, test_df, save_dir=model_dir)

        if predictions_df is None:
            logging.error(f"{model_name} Fail")
            return

        # 创建评估器并评估
        evaluator = ModelEvaluator()
        rmse_results = evaluator.calculate_rmse(
            test_df,
            predictions_df
        )

        # 保存评估结果
        plot_path = os.path.join(eval_dir, f'{model_name.lower()}_rmse.png')
        evaluator.plot_rmse_comparison(rmse_results, model_name, plot_path)

        logging.info(f"{model_name} Successful.")
        return rmse_results

    except Exception as e:
        logging.error(f"{model_name} Fail: {str(e)}")
        return None

###########################################################模型预测
@fun_name
def run_models(X_train, X_test, y_train, y_test, df):
    """按顺序执行所有模型"""
    # 创建评估结果目录
    eval_dir = "RMSE_results"
    os.makedirs(eval_dir, exist_ok=True)

    # 创建模型输出目录
    model_dir = "model_outputs"
    os.makedirs(model_dir, exist_ok=True)

    # 定义模型执行顺序
    models = [
        (TimeSeriesPredictor(), "TimeSeries"),
        (ProphetPredictor(), "Prophet"),
        (MLPPredictor(), "MLP"),
        (CNNPredictor(), "CNN"),
        (BNNPredictor(), "BNN"),
        (LSTMPredictor(), "LSTM"),
        (XGBoostEnsemblePredictor(), "XGBoost"),
        (RandomForestsPredictor(), "RandomForest"),
        (StackCNNLSTMPredictor(), "Stack(CNN+LSTM+meta)"),
        (StackCNNXGBoostPredictor(), "Stack(CNN+XGBoost+meta)"),
        (StackLSTMXGBoostPredictor(), "Stack(LSTM+XGBoost+meta)"),
        (HybridPredictor(), "Hybrid(CNN+LSTM+XGBoost)"),
        (StackCNNLSTMXGBoostPredictor(), "Stack(CNN+LSTM+XGBoost+meta)")
    ]

    all_results = {}

    # 逐个执行模型
    for model, name in models:
        results = run_single_model(model, name, X_train, X_test, y_train, y_test, df, eval_dir, model_dir)
        if results:
            all_results[name] = results
        time.sleep(2)

    return all_results
###########################################################

if __name__ == '__main__':
    # 设置绘图样式
    setup_plot_style()
    # 软件版本检查
    version_check()
    # 设置随机种子
    set_random_seed(73)
    # 数据处理
    X_train, X_test, y_train, y_test, feature_names, df = process_data()
    # 可视化
    create_visualizations(df, feature_names)
    # 执行回测和预测
    all_results = run_models(X_train, X_test, y_train, y_test, df)

