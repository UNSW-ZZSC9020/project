import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error
from typing import Dict, List, Optional, Tuple
import logging
import matplotlib.pyplot as plt


class ModelEvaluator:
    """
    模型评估器 - 计算不同预测深度的RMSE
    """

    def __init__(self, sample_interval: str = '30T'):
        """
        初始化评估器

        参数:
        sample_interval: str - 数据采样间隔,默认30分钟
        """
        # 定义评估小时数
        self.evaluation_hours = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24]
        self.sample_interval = sample_interval
        # 计算每个评估点对应的数据点数
        interval_minutes = int(sample_interval[:-1])
        self.evaluation_points = [int(hour * 60 / interval_minutes)
                                  for hour in self.evaluation_hours]

    def calculate_rmse(self, df: pd.DataFrame, predictions_df: pd.DataFrame) -> Dict[int, Tuple[float, float]]:
        """
        计算不同预测深度的RMSE及其标准误差

        返回:
        Dict[int, Tuple[float, float]] - 键为小时数，值为(RMSE, SE)元组
        """
        results = {}

        try:
            logging.info("Calculating RMSE with Standard Error...")

            for hours, points in zip(self.evaluation_hours, self.evaluation_points):
                true_values = df['load'].iloc[-points:].values
                pred_values = predictions_df['predicted_load'].iloc[:points].values

                # 计算每个时间点的平方误差
                squared_errors = (true_values - pred_values) ** 2

                # 计算RMSE
                rmse = np.sqrt(np.mean(squared_errors))

                # 计算标准误差 (使用bootstrap方法)
                n_bootstrap = 1000
                bootstrap_rmses = []
                for _ in range(n_bootstrap):
                    indices = np.random.randint(0, len(squared_errors), len(squared_errors))
                    bootstrap_mse = np.mean(squared_errors[indices])
                    bootstrap_rmses.append(np.sqrt(bootstrap_mse))

                se = np.std(bootstrap_rmses)

                results[hours] = (rmse, se)
                logging.info(f"{hours}h RMSE: {rmse:.4f} ± {se:.4f}")

        except Exception as e:
            logging.error(f"RMSE计算错误: {str(e)}")
            raise

        return results

    def plot_rmse_comparison(self, rmse_dict: Dict[int, float],
                             model_name: str,
                             save_path: Optional[str] = None) -> None:
        """
        绘制RMSE对比图
        """
        # 设置科研论文风格
        plt.style.use('classic')
        plt.rcParams.update({
            'font.family': 'DejaVu Sans',
            'font.size': 10,
            'axes.labelsize': 12,
            'axes.titlesize': 12,
            'figure.dpi': 300
        })

        plt.figure(figsize=(8, 6))
        hours = list(rmse_dict.keys())
        rmse_values = list(rmse_dict.values())

        plt.plot(hours, rmse_values, 'o-', linewidth=1.5)
        plt.grid(True, alpha=0.3)
        plt.xlabel('Prediction Horizon (hours)')
        plt.ylabel('RMSE (MW)')
        plt.title(f'RMSE at Different Prediction Horizons - {model_name}')

        if save_path:
            plt.savefig(save_path, bbox_inches='tight')
            logging.info(f"RMSE plot has been saved to : {save_path}")
        else:
            plt.show()

        plt.close()
