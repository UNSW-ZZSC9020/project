import pandas as pd
import numpy as np
from prophet import Prophet
from sklearn.metrics import mean_squared_error, mean_absolute_error
import itertools
import matplotlib.pyplot as plt
import os
from typing import Optional, Dict, List, Tuple
from datetime import datetime
import logging


class ProphetPredictor:
    """
    基于Facebook Prophet的时间序列预测器
    主要用于预测电力负载，支持温度作为额外的回归变量
    """

    def __init__(self, forecast_hours: int = 48, sample_interval: str = '30T'):
        """
        初始化预测器

        参数:
        forecast_hours: int - 预测时长（小时）
        sample_interval: str - 数据采样间隔，默认30分钟
        """
        self.forecast_hours = forecast_hours
        self.sample_interval = sample_interval
        self.forecast_points = int(forecast_hours * 60 / int(sample_interval[:-1]))
        self.best_params = None

        # 定义参数网格
        self.param_grid = {
            'changepoint_prior_scale': [0.01],
            'seasonality_prior_scale': [0.1],
            'seasonality_mode': ['multiplicative'],
            'changepoint_range': [0.9],
            'holidays_prior_scale': [0.1]
        }

    def _preprocess_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        预处理时间序列数据

        参数:
        df: DataFrame - 包含 'timestamp', 'temperature', 'load' 列的数据框

        返回:
        DataFrame - 处理后的Prophet格式数据框
        """
        try:
            logging.info("Starting data preprocessing for Prophet...")

            # 准备Prophet格式数据
            prophet_df = df[['timestamp', 'load', 'temperature']].copy()
            prophet_df.columns = ['ds', 'y', 'temperature']

            # 确保数据按时间排序
            prophet_df = prophet_df.sort_values('ds').reset_index(drop=True)

            # 重采样数据
            prophet_df.set_index('ds', inplace=True)
            prophet_df = prophet_df.resample(self.sample_interval).mean().interpolate(method='time')
            prophet_df.reset_index(inplace=True)

            return prophet_df

        except Exception as e:
            logging.error(f"Error in data preprocessing: {str(e)}")
            raise

    def _grid_search(self, train_df: pd.DataFrame, val_df: pd.DataFrame) -> Dict:
        """
        网格搜索最佳参数

        参数:
        train_df: DataFrame - 训练数据
        val_df: DataFrame - 验证数据

        返回:
        Dict - 最佳参数
        """
        all_params = [dict(zip(self.param_grid.keys(), v))
                      for v in itertools.product(*self.param_grid.values())]
        logging.info(f"Evaluating {len(all_params)} parameter combinations")

        best_params = None
        best_score = float('inf')

        for params in all_params:
            try:
                logging.info(f"Trying parameters: {params}")

                model = Prophet(
                    changepoint_prior_scale=params['changepoint_prior_scale'],
                    seasonality_prior_scale=params['seasonality_prior_scale'],
                    seasonality_mode=params['seasonality_mode'],
                    changepoint_range=params['changepoint_range'],
                    holidays_prior_scale=params['holidays_prior_scale'],
                    yearly_seasonality=True,
                    weekly_seasonality=True,
                    daily_seasonality=True
                )

                # 添加温度作为回归变量
                model.add_regressor('temperature')

                # 训练模型
                model.fit(train_df)

                # 验证
                forecast = model.predict(val_df)
                mse = mean_squared_error(val_df['y'], forecast['yhat'])
                mae = mean_absolute_error(val_df['y'], forecast['yhat'])

                if mse < best_score:
                    best_score = mse
                    best_params = params
                    logging.info(f'New best parameters found: MSE={mse:.2f}, MAE={mae:.2f}')

            except Exception as e:
                logging.error(f"Error with parameters {params}: {str(e)}")
                continue

        return best_params

    def predict(self, df: pd.DataFrame, save_dir: Optional[str] = None) -> Optional[pd.DataFrame]:
        """
        执行完整的预测流程

        参数:
        df: DataFrame - 输入数据
        save_dir: Optional[str] - 保存预测结果的目录

        返回:
        Optional[pd.DataFrame] - 预测结果数据框
        """
        try:
            # 数据预处理
            prophet_df = self._preprocess_data(df)

            # 划分训练集和验证集
            train_size = int(len(prophet_df) * 0.8)
            train_df = prophet_df[:train_size]
            val_df = prophet_df[train_size:]

            # 网格搜索最佳参数
            if not self.best_params:
                self.best_params = self._grid_search(train_df, val_df)

            if self.best_params:
                logging.info("Training final model with best parameters...")
                final_model = Prophet(
                    changepoint_prior_scale=self.best_params['changepoint_prior_scale'],
                    seasonality_prior_scale=self.best_params['seasonality_prior_scale'],
                    seasonality_mode=self.best_params['seasonality_mode'],
                    changepoint_range=self.best_params['changepoint_range'],
                    holidays_prior_scale=self.best_params['holidays_prior_scale'],
                    yearly_seasonality=True,
                    weekly_seasonality=True,
                    daily_seasonality=True
                )
                final_model.add_regressor('temperature')
                final_model.fit(prophet_df)

                # 创建未来时间序列
                future = final_model.make_future_dataframe(periods=self.forecast_points,
                                                           freq=self.sample_interval)

                # 使用最后一个已知温度值
                future['temperature'] = df['temperature'].iloc[-1]

                # 生成预测
                logging.info("Generating predictions...")
                forecast = final_model.predict(future)
                predictions = forecast['yhat'].tail(self.forecast_points).values

                # 创建时间戳
                last_timestamp = pd.to_datetime(df['timestamp'].iloc[-1])
                future_timestamps = pd.date_range(
                    start=last_timestamp,
                    periods=self.forecast_points + 1,
                    freq=self.sample_interval
                )[1:]

                # 创建预测结果DataFrame
                predictions_df = pd.DataFrame({
                    'timestamp': future_timestamps,
                    'predicted_load': predictions
                })

                # 可视化结果
                self._plot_predictions(df, predictions_df, save_dir)

                # 输出预测统计信息
                self._print_prediction_summary(predictions)

                return predictions_df

            return None

        except Exception as e:
            logging.error(f"Error in prediction process: {str(e)}")
            return None

    def _plot_predictions(self, historical_df: pd.DataFrame,
                          predictions_df: pd.DataFrame,
                          save_dir: Optional[str] = None) -> None:
        """
        绘制预测结果图表

        参数:
        historical_df: pd.DataFrame - 历史数据
        predictions_df: pd.DataFrame - 预测数据
        save_dir: Optional[str] - 保存图表的目录
        """
        plt.figure(figsize=(15, 6))

        # 绘制历史数据（最后48小时）
        historical_data = historical_df['load'].iloc[-48:]
        historical_timestamps = historical_df['timestamp'].iloc[-48:]
        plt.plot(historical_timestamps, historical_data,
                 label='Historical Data', color='blue', alpha=0.6)

        # 绘制预测数据
        plt.plot(predictions_df['timestamp'], predictions_df['predicted_load'],
                 label='Prophet Predicted Load', color='red', alpha=0.6)

        plt.title(f'{self.forecast_hours}-hour Prophet Load Forecast')
        plt.xlabel('Time')
        plt.ylabel('Load (MW)')
        plt.legend()
        plt.grid(True)
        plt.xticks(rotation=45)
        plt.tight_layout()

        if save_dir:
            os.makedirs(save_dir, exist_ok=True)
            plt.savefig(os.path.join(save_dir, f'prophet_prediction.png'),
                        dpi=300, bbox_inches='tight')
            logging.info(f"Prophet prediction plot saved in {save_dir}")
        else:
            plt.show()

        plt.close()

    def _print_prediction_summary(self, predictions: np.ndarray) -> None:
        """
        打印预测结果的统计信息

        参数:
        predictions: np.ndarray - 预测结果数组
        """
        logging.info("Prophet Prediction Summary:")
        logging.info(f"Mean Load: {predictions.mean():.2f} MW")
        logging.info(f"Standard Deviation: {predictions.std():.2f} MW")
        logging.info(f"Maximum Load: {predictions.max():.2f} MW")
        logging.info(f"Minimum Load: {predictions.min():.2f} MW")

    def predict_with_split(self, X_train, y_train, X_test, test_df: pd.DataFrame, save_dir: Optional[str] = None) -> \
            Optional[pd.DataFrame]:
        """
        使用预先划分的训练集和测试集进行预测和评估

        参数:
        X_train: np.ndarray - 训练特征（Prophet不直接使用）
        y_train: np.ndarray - 训练目标（Prophet不直接使用）
        X_test: np.ndarray - 测试特征（Prophet不直接使用）
        test_df: pd.DataFrame - 包含测试数据的原始DataFrame
        save_dir: Optional[str] - 保存目录

        返回:
        Optional[pd.DataFrame] - 包含预测结果的DataFrame
        """
        try:
            # Prophet需要特定格式的数据，我们从test_df中提取
            prophet_test_df = test_df[['timestamp', 'load', 'temperature']].copy()
            prophet_test_df.columns = ['ds', 'y', 'temperature']

            # 确保数据按时间排序
            prophet_test_df = prophet_test_df.sort_values('ds').reset_index(drop=True)

            # 如果之前已经找到了最佳参数，使用它们
            if not self.best_params:
                # 使用默认参数
                self.best_params = {
                    'changepoint_prior_scale': 0.01,
                    'seasonality_prior_scale': 0.1,
                    'seasonality_mode': 'multiplicative',
                    'changepoint_range': 0.9,
                    'holidays_prior_scale': 0.1
                }
                logging.info("Using default parameters for Prophet")

            # 训练模型
            logging.info("Training Prophet model with split data...")
            model = Prophet(
                changepoint_prior_scale=self.best_params['changepoint_prior_scale'],
                seasonality_prior_scale=self.best_params['seasonality_prior_scale'],
                seasonality_mode=self.best_params['seasonality_mode'],
                changepoint_range=self.best_params['changepoint_range'],
                holidays_prior_scale=self.best_params['holidays_prior_scale'],
                yearly_seasonality=True,
                weekly_seasonality=True,
                daily_seasonality=True
            )
            model.add_regressor('temperature')

            # 获取预测开始之前的数据用于训练
            train_cutoff = prophet_test_df['ds'].iloc[0]
            train_data = prophet_test_df[prophet_test_df['ds'] < train_cutoff]

            if len(train_data) > 0:
                model.fit(train_data)
            else:
                # 如果没有训练数据，使用测试数据的一部分进行训练
                train_size = int(len(prophet_test_df) * 0.5)
                model.fit(prophet_test_df.iloc[:train_size])

            # 生成预测
            logging.info("Generating predictions on test data...")
            future = model.make_future_dataframe(periods=0, freq=self.sample_interval)
            future = pd.concat([future, prophet_test_df[['ds', 'temperature']]])
            future = future.drop_duplicates(subset=['ds'])

            forecast = model.predict(future)

            # 合并预测结果与实际结果
            results = pd.merge(prophet_test_df[['ds', 'y']],
                               forecast[['ds', 'yhat']],
                               on='ds',
                               how='inner')

            # 创建预测结果DataFrame
            predictions_df = pd.DataFrame({
                'timestamp': results['ds'],
                'predicted_load': results['yhat']
            })

            # 可视化结果
            self._plot_predictions_with_split(prophet_test_df, predictions_df, model, save_dir)

            # 输出预测统计信息
            self._print_prediction_summary(predictions_df['predicted_load'].values)

            return predictions_df

        except Exception as e:
            logging.error(f"Error in prediction process with split: {str(e)}")
            return None

    def _plot_predictions_with_split(self, test_df: pd.DataFrame,
                                     predictions_df: pd.DataFrame,
                                     model: Prophet,
                                     save_dir: Optional[str] = None) -> None:
        """
        绘制基于训练测试集划分的预测结果图表

        参数:
        test_df: pd.DataFrame - 测试数据，Prophet格式(ds, y)
        predictions_df: pd.DataFrame - 预测结果
        model: Prophet - 训练好的Prophet模型
        save_dir: Optional[str] - 保存目录
        """
        plt.figure(figsize=(15, 10))

        # 绘制预测结果
        plt.subplot(2, 1, 1)
        plt.plot(test_df['ds'], test_df['y'],
                 label='Actual Load', color='blue', alpha=0.6)
        plt.plot(predictions_df['timestamp'], predictions_df['predicted_load'],
                 label='Prophet Predicted Load', color='red', alpha=0.6)

        plt.title(f'Prophet Load Forecast with Train-Test Split')
        plt.xlabel('Time')
        plt.ylabel('Load (MW)')
        plt.legend()
        plt.grid(True)
        plt.xticks(rotation=45)

        # Prophet模型的组件图
        plt.subplot(2, 1, 2)
        try:
            model_components = model.plot_components(model.predict(test_df[['ds', 'temperature']]))
            plt.tight_layout()
        except:
            plt.text(0.5, 0.5, 'Component plot not available',
                     horizontalalignment='center', verticalalignment='center')

        plt.tight_layout()

        if save_dir:
            os.makedirs(save_dir, exist_ok=True)
            plt.savefig(os.path.join(save_dir, f'prophet_prediction_split.png'),
                        dpi=300, bbox_inches='tight')
            logging.info(f"Prophet prediction plot saved in {save_dir}")
        else:
            plt.show()

        plt.close()