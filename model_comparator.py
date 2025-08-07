"""
model_comparator.py
用于比较不同负载预测模型性能的模块
"""

import pandas as pd
import numpy as np
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import matplotlib.pyplot as plt
from typing import Dict, List, Optional
import os
import logging
from datetime import datetime

# Import model predictors
from time_series_predictor import TimeSeriesPredictor
from prophet_predictor import ProphetPredictor
from MLP_predictor import MLPPredictor
from BNN_predictor import BNNPredictor
from CNN_predictor import CNNPredictor
from LSTM_predictor import LSTMPredictor
from XGBoost_ensemble import XGBoostEnsemblePredictor
from RandomForests_ensemble import RandomForestsPredictor
from Stack_ensemble import StackingEnsemblePredictor


class ModelComparator:
    """
    用于比较不同模型性能的框架类
    """

    def __init__(self, save_dir: str = 'model_comparison'):
        """
        初始化比较器

        参数:
        save_dir: str - 结果保存目录
        """
        self.save_dir = save_dir
        os.makedirs(save_dir, exist_ok=True)
        self.models = {}
        self.results = {}
        self._initialize_models()

    def _initialize_models(self):
        """
        初始化所有要比较的模型
        """
        self.models = {
            'Time Series': TimeSeriesPredictor(
                lookback_hours=48,
                forecast_hours=48,
                sample_interval='30T',
                n_neighbors=5
            ),
            'Prophet': ProphetPredictor(
                forecast_hours=48,
                sample_interval='30T'
            ),
            'MLP': MLPPredictor(
                lookback_hours=48,
                forecast_hours=48,
                sample_interval='30T'
            ),
            'BNN': BNNPredictor(
                lookback_hours=48,
                forecast_hours=48,
                sample_interval='30T'
            ),
            'CNN': CNNPredictor(
                lookback_hours=48,
                forecast_hours=48,
                sample_interval='30T'
            ),
            'LSTM': LSTMPredictor(
                lookback_hours=48,
                forecast_hours=48,
                sample_interval='30T'
            ),
            'XGBoost': XGBoostEnsemblePredictor(
                lookback_hours=48,
                forecast_hours=48,
                sample_interval='30T'
            ),
            'Random Forest': RandomForestsPredictor(
                lookback_hours=48,
                forecast_hours=48,
                sample_interval='30T'
            ),
            'Stacking Ensemble': StackingEnsemblePredictor(
                lookback_hours=48,
                forecast_hours=48,
                sample_interval='30T'
            )
        }

    def _calculate_metrics(self, y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
        """
        计算各种评估指标
        """
        return {
            'MSE': mean_squared_error(y_true, y_pred),
            'RMSE': np.sqrt(mean_squared_error(y_true, y_pred)),
            'MAE': mean_absolute_error(y_true, y_pred),
            'R2': r2_score(y_true, y_pred),
            'MAPE': np.mean(np.abs((y_true - y_pred) / y_true)) * 100
        }

    def compare_models(self, df: pd.DataFrame):
        """
        比较所有模型的性能

        参数:
        df: pd.DataFrame - 输入数据
        """
        print("Starting model comparison...")
        print("=" * 80)  # 开始分隔线

        for model_name, model in self.models.items():
            print("=" * 80)  # 方法之间的分隔线
            print(f"\nEvaluating {model_name} model...")
            print(f"\n{'='*40} {model_name} Model {'='*40}")  # 添加醒目的标题
            try:
                # 创建模型专属保存目录
                model_dir = os.path.join(self.save_dir, f'model-{model_name.lower().replace(" ", "_")}')
                os.makedirs(model_dir, exist_ok=True)

                # 预测
                start_time = datetime.now()
                predictions = model.predict(df, save_dir=model_dir)
                end_time = datetime.now()

                if predictions is not None:
                    # 计算执行时间
                    execution_time = (end_time - start_time).total_seconds()

                    # 获取最后48小时的实际值进行比较
                    actual_values = df['load'].iloc[-96:]  # 48小时，每30分钟一个数据点
                    predicted_values = predictions['predicted_load'].values

                    # 计算评估指标
                    metrics = self._calculate_metrics(actual_values, predicted_values)
                    metrics['execution_time'] = execution_time

                    self.results[model_name] = metrics
                    print(f"\n{model_name} Evaluation Results:")
                    print("-" * 60)  # 添加结果分隔线
                    print(f"Status: Successfully completed")
                    print(f"Execution time: {execution_time:.2f} seconds")
                    print("\nMetrics:")
                    print("-" * 40)  # 添加指标分隔线
                    for metric, value in metrics.items():
                        print(f"{metric:15} : {value:.4f}")
                    print("\n" + "=" * 80)  # 添加方法结束分隔线

            except Exception as e:
                print(f"Error evaluating {model_name}: {str(e)}")
                continue

        # 生成比较报告
        self._generate_comparison_report()

    def _generate_comparison_report(self):
        """
        生成模型比较报告
        """
        if not self.results:
            print("No results to compare")
            return

        # 创建比较表格
        comparison_df = pd.DataFrame(self.results).round(4)

        # 保存比较结果
        comparison_df.to_csv(os.path.join(self.save_dir, 'model_comparison.csv'))

        # 绘制性能对比图
        self._plot_comparison()

        print("\nModel Comparison Summary:")
        print(comparison_df)

    def _plot_comparison(self):
        """
        绘制模型性能对比图
        """
        metrics_to_plot = ['MSE', 'MAE', 'MAPE']
        num_metrics = len(metrics_to_plot)

        plt.figure(figsize=(15, 5 * num_metrics))

        for i, metric in enumerate(metrics_to_plot, 1):
            plt.subplot(num_metrics, 1, i)

            values = [self.results[model][metric] for model in self.results]
            models = list(self.results.keys())

            bars = plt.bar(models, values)
            plt.title(f'Model Comparison - {metric}')
            plt.xlabel('Models')
            plt.ylabel(metric)
            plt.xticks(rotation=45)

            # 添加数值标签
            for bar in bars:
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height:.2f}',
                        ha='center', va='bottom')

        plt.tight_layout()
        plt.savefig(os.path.join(self.save_dir, 'model_comparison.png'),
                    dpi=300, bbox_inches='tight')
        plt.close()


def run_comparison(temp_file: str, demand_file: str):
    """
    运行模型比较的主函数

    参数:
    temp_file: str - 温度数据文件路径
    demand_file: str - 负载数据文件路径
    """
    from data_preprocessor import NSWDataPreprocessor

    print("Starting model comparison process...")
    print("Initializing data preprocessor...")

    preprocessor = NSWDataPreprocessor(window_size=1440)  # 24小时
    results = preprocessor.prepare_data(temp_file, demand_file)

    if results is not None:
        _, _, _, _, _, df = results

        print("Data preprocessing completed")
        print("Starting model comparator...")

        # 创建比较器并运行比较
        comparator = ModelComparator()
        comparator.compare_models(df)

        print("Model comparison completed. Results saved in the model_comparison directory.")
    else:
        print("Error in data preprocessing. Cannot proceed with model comparison.")