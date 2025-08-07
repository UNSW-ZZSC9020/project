import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, Lambda
from tensorflow.keras.optimizers import Adam
from tensorflow.keras import backend as K
from sklearn.preprocessing import MinMaxScaler
import matplotlib.pyplot as plt
from typing import Optional, Tuple
from datetime import datetime
import os
import numpy as np
import pandas as pd
import logging


class BNNPredictor:
    """
    基于MC Dropout的贝叶斯神经网络时间序列预测器
    主要用于预测电力负载，考虑预测的不确定性
    """

    def __init__(self, lookback_hours: int = 48, forecast_hours: int = 48,
                 sample_interval: str = '30T'):
        """
        初始化预测器

        参数:
        lookback_hours: int - 用于预测的历史数据时长（小时）
        forecast_hours: int - 预测时长（小时）
        sample_interval: str - 数据采样间隔，默认30分钟
        """
        # 检查是否有可用的GPU
        if tf.config.list_physical_devices('GPU'):
            logging.info("BNN using GPU")
            tf.keras.mixed_precision.set_global_policy('mixed_float16')

        self.lookback_hours = lookback_hours
        self.forecast_hours = forecast_hours
        self.sample_interval = sample_interval
        self.lookback_points = int(lookback_hours * 60 / int(sample_interval[:-1]))
        self.forecast_points = int(forecast_hours * 60 / int(sample_interval[:-1]))
        self.scaler = MinMaxScaler(feature_range=(0, 1))

        # 初始化模型
        self.model = None
        self.dropout_rate = 0.2
        self.num_monte_carlo = 100

    def _preprocess_data(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, np.ndarray]:
        """
        预处理时间序列数据
        """
        try:
            logging.info("Starting data preprocessing for BNN...")

            # 准备基础数据
            df = df[['timestamp', 'temperature', 'load']].copy()
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp').reset_index(drop=True)

            # 添加时间特征
            df['hour'] = df['timestamp'].dt.hour
            df['dayofweek'] = df['timestamp'].dt.dayofweek
            df['month'] = df['timestamp'].dt.month
            df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
            df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)

            # 重采样数据
            df.set_index('timestamp', inplace=True)
            df = df.resample(self.sample_interval).mean().interpolate(method='time')
            df.reset_index(inplace=True)

            # 标准化数据
            features = ['hour_sin', 'hour_cos', 'temperature', 'load']
            scaled_data = self.scaler.fit_transform(df[features])

            return df, scaled_data

        except Exception as e:
            logging.error(f"Error in data preprocessing: {str(e)}")
            raise

    def _create_sequences(self, scaled_data: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        创建时间序列的输入序列和目标序列
        """
        try:
            X, y = [], []
            for i in range(len(scaled_data) - self.lookback_points - self.forecast_points):
                sequence = scaled_data[i:(i + self.lookback_points)].flatten()
                target = scaled_data[(i + self.lookback_points):(i + self.lookback_points + self.forecast_points), -1]

                X.append(sequence)
                y.append(target)

            return np.array(X), np.array(y)

        except Exception as e:
            logging.error(f"Error in sequence creation: {str(e)}")
            raise

    def _build_mc_dropout_model(self, input_shape: int):
        """
        构建带有MC Dropout的神经网络模型
        """
        with tf.device('/device:GPU:0'):
            model = Sequential([
                Dense(128, input_shape=(input_shape,), activation='relu'),
                Dropout(self.dropout_rate),
                Dense(64, activation='relu'),
                Dropout(self.dropout_rate),
                Dense(32, activation='relu'),
                Dropout(self.dropout_rate),
                Dense(self.forecast_points, activation='linear')
            ])

            model.compile(
                optimizer=Adam(learning_rate=0.001),
                loss='mse',
                metrics=['mae']
            )

            return model

    def predict(self, df: pd.DataFrame, save_dir: Optional[str] = None) -> Optional[pd.DataFrame]:
        """
        执行完整的预测流程
        """
        try:
            # 数据预处理
            processed_df, scaled_data = self._preprocess_data(df)

            # 创建序列
            X, y = self._create_sequences(scaled_data)
            logging.info(f"Training MC Dropout Network with input shape: {X.shape}, output shape: {y.shape}")

            # 构建并训练模型
            if self.model is None:
                self.model = self._build_mc_dropout_model(X.shape[1])
                logging.info("Training MC Dropout model...")
                history = self.model.fit(X, y, epochs=50, batch_size=128, validation_split=0.2,
                                         verbose=0)

                # 只打印最终的损失值
                final_loss = history.history['loss'][-1]
                final_val_loss = history.history['val_loss'][-1]
                logging.info(f"Training completed - Final loss: {final_loss:.4f}, Validation loss: {final_val_loss:.4f}")

            # 准备最后一个时间窗口用于预测
            last_window = scaled_data[-self.lookback_points:].flatten().reshape(1, -1)

            # 使用MC Dropout进行多次预测
            logging.info("Generating predictions with MC Dropout sampling...")
            predictions_list = []
            for _ in range(self.num_monte_carlo):
                predictions_list.append(self.model(last_window, training=True))
            predictions_array = np.array(predictions_list)

            # 计算均值和标准差
            predictions_mean = np.mean(predictions_array, axis=0)[0]
            predictions_std = np.std(predictions_array, axis=0)[0]

            # 反标准化预测结果
            dummy_features = np.zeros((self.forecast_points, scaled_data.shape[1]))

            # 处理均值
            dummy_features[:, -1] = predictions_mean
            final_predictions_mean = self.scaler.inverse_transform(dummy_features)[:, -1]

            # 处理置信区间
            dummy_features[:, -1] = predictions_mean + 2 * predictions_std
            final_predictions_upper = self.scaler.inverse_transform(dummy_features)[:, -1]

            dummy_features[:, -1] = predictions_mean - 2 * predictions_std
            final_predictions_lower = self.scaler.inverse_transform(dummy_features)[:, -1]

            # 创建时间索引
            last_timestamp = processed_df['timestamp'].iloc[-1]
            future_timestamps = pd.date_range(
                start=last_timestamp,
                periods=self.forecast_points + 1,
                freq=self.sample_interval
            )[1:]

            # 创建预测结果DataFrame
            predictions_df = pd.DataFrame({
                'timestamp': future_timestamps,
                'predicted_load': final_predictions_mean,
                'prediction_lower': final_predictions_lower,
                'prediction_upper': final_predictions_upper
            })

            # 可视化结果
            self._plot_predictions(processed_df, predictions_df, save_dir)

            # 输出预测统计信息
            self._print_prediction_summary(predictions_df)

            return predictions_df

        except Exception as e:
            logging.error(f"Error in prediction process: {str(e)}")
            return None

    def _plot_predictions(self, historical_df: pd.DataFrame,
                          predictions_df: pd.DataFrame,
                          save_dir: Optional[str] = None) -> None:
        """
        绘制预测结果图表，包括置信区间
        """
        plt.figure(figsize=(15, 6))

        # 绘制历史数据
        historical_data = historical_df['load'].iloc[-self.lookback_points:]
        historical_timestamps = historical_df['timestamp'].iloc[-self.lookback_points:]
        plt.plot(historical_timestamps, historical_data,
                 label='Historical Data', color='blue', alpha=0.6)

        # 绘制预测数据及置信区间
        plt.plot(predictions_df['timestamp'], predictions_df['predicted_load'],
                 label='BNN Predicted Load', color='red', alpha=0.6)
        plt.fill_between(predictions_df['timestamp'],
                         predictions_df['prediction_lower'],
                         predictions_df['prediction_upper'],
                         color='red', alpha=0.2,
                         label='95% Confidence Interval')

        plt.title(f'{self.forecast_hours}-hour BNN Load Forecast with Uncertainty')
        plt.xlabel('Time')
        plt.ylabel('Load (MW)')
        plt.legend()
        plt.grid(True)
        plt.xticks(rotation=45)
        plt.tight_layout()

        if save_dir:
            os.makedirs(save_dir, exist_ok=True)
            plt.savefig(os.path.join(save_dir, f'bnn_prediction.png'),
                        dpi=300, bbox_inches='tight')
            logging.info(f"BNN prediction plot saved in {save_dir}")
        else:
            plt.show()

        plt.close()

    def _print_prediction_summary(self, predictions_df: pd.DataFrame) -> None:
        """
        打印预测结果的统计信息，包括不确定性估计
        """
        predictions = predictions_df['predicted_load'].values
        uncertainty = (predictions_df['prediction_upper'].values -
                       predictions_df['prediction_lower'].values) / 2

        logging.info("BNN Prediction Summary:")
        logging.info(f"Mean Load: {predictions.mean():.2f} MW")
        logging.info(f"Standard Deviation: {predictions.std():.2f} MW")
        logging.info(f"Maximum Load: {predictions.max():.2f} MW")
        logging.info(f"Minimum Load: {predictions.min():.2f} MW")
        logging.info(f"Average Uncertainty: ±{uncertainty.mean():.2f} MW")

    def predict_with_split(self, X_train, y_train, X_test, test_df: pd.DataFrame, save_dir: Optional[str] = None) -> \
    Optional[pd.DataFrame]:
        """
        使用预先划分的训练集和测试集进行预测和评估

        参数:
        X_train: np.ndarray - 训练特征
        y_train: np.ndarray - 训练目标
        X_test: np.ndarray - 测试特征
        test_df: pd.DataFrame - 包含测试数据的原始DataFrame
        save_dir: Optional[str] - 保存目录

        返回:
        Optional[pd.DataFrame] - 包含预测结果的DataFrame
        """
        try:
            # 构建并训练模型
            if self.model is None:
                input_shape = X_train.shape[1]
                self.model = self._build_mc_dropout_model(input_shape)
                logging.info("Training MC Dropout model...")
                history = self.model.fit(X_train, y_train, epochs=50, batch_size=128, validation_split=0.2,
                                         verbose=0)

                # 打印最终的损失值
                final_loss = history.history['loss'][-1]
                final_val_loss = history.history['val_loss'][-1]
                logging.info(
                    f"Training completed - Final loss: {final_loss:.4f}, Validation loss: {final_val_loss:.4f}")

            # 使用MC Dropout进行多次预测
            logging.info("Generating predictions with MC Dropout sampling...")
            predictions_list = []
            for _ in range(self.num_monte_carlo):
                predictions_list.append(self.model(X_test, training=True))
            predictions_array = np.array(predictions_list)

            # 计算均值和标准差
            predictions_mean = np.mean(predictions_array, axis=0)
            predictions_std = np.std(predictions_array, axis=0)

            # 反标准化预测结果 - 这部分需要根据模型的特定预处理调整
            # 假设test_df中包含我们需要预测的所有时间点
            predictions_df = pd.DataFrame({
                'timestamp': test_df['timestamp'],
                'predicted_load': predictions_mean.flatten()[:len(test_df)],
                'prediction_lower': (predictions_mean - 2 * predictions_std).flatten()[:len(test_df)],
                'prediction_upper': (predictions_mean + 2 * predictions_std).flatten()[:len(test_df)]
            })

            # 可视化结果
            self._plot_predictions_with_split(test_df, predictions_df, save_dir)

            # 输出预测统计信息
            self._print_prediction_summary(predictions_df)

            return predictions_df

        except Exception as e:
            logging.error(f"Error in prediction process: {str(e)}")
            return None

    def _plot_predictions_with_split(self, test_df, predictions_df, save_dir=None):
        """绘制基于训练测试集划分的预测结果图表"""
        plt.figure(figsize=(15, 6))

        # 绘制测试数据的实际值
        plt.plot(test_df['timestamp'], test_df['load'],
                 label='Actual Load', color='blue', alpha=0.6)

        # 绘制预测值
        plt.plot(predictions_df['timestamp'], predictions_df['predicted_load'],
                 label='BNN Predicted Load', color='red', alpha=0.6)

        plt.title(f'BNN Load Forecast with Train-Test Split')
        plt.xlabel('Time')
        plt.ylabel('Load (MW)')
        plt.legend()
        plt.grid(True)
        plt.xticks(rotation=45)
        plt.tight_layout()

        if save_dir:
            os.makedirs(save_dir, exist_ok=True)
            plt.savefig(os.path.join(save_dir, f'bnn_prediction_split.png'),
                        dpi=300, bbox_inches='tight')
            logging.info(f"BNN prediction plot saved in {save_dir}")
        else:
            plt.show()

        plt.close()