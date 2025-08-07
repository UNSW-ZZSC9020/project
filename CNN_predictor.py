import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv1D, MaxPooling1D, Dense, Flatten, Dropout
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping
from sklearn.preprocessing import MinMaxScaler
import matplotlib.pyplot as plt
from typing import Optional, Tuple
from datetime import datetime
import os
import numpy as np
import pandas as pd
import logging


class CNNPredictor:
    """
    基于Keras CNN的时间序列预测器
    主要用于预测电力负载
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
            logging.info("CNN using GPU")
            tf.keras.mixed_precision.set_global_policy('mixed_float16')

        self.lookback_hours = lookback_hours
        self.forecast_hours = forecast_hours
        self.sample_interval = sample_interval
        self.lookback_points = int(lookback_hours * 60 / int(sample_interval[:-1]))
        self.forecast_points = int(forecast_hours * 60 / int(sample_interval[:-1]))
        self.scaler = MinMaxScaler(feature_range=(0, 1))

        # CNN模型参数
        self.filters = 64
        self.kernel_size = 3
        self.model = self._build_model()

    def _build_model(self) -> Sequential:
        """
        构建CNN模型
        """
        with tf.device('/device:GPU:0'):
            model = Sequential([
                # 第一个卷积层
                Conv1D(filters=self.filters, kernel_size=self.kernel_size,
                       activation='relu', input_shape=(self.lookback_points, 4)),
                MaxPooling1D(pool_size=2),

                # 第二个卷积层
                Conv1D(filters=self.filters * 2, kernel_size=self.kernel_size, activation='relu'),
                MaxPooling1D(pool_size=2),

                # 第三个卷积层
                Conv1D(filters=self.filters * 4, kernel_size=self.kernel_size, activation='relu'),

                # 展平层
                Flatten(),

                # 全连接层
                Dense(512, activation='relu'),
                Dropout(0.3),
                Dense(256, activation='relu'),
                Dense(self.forecast_points, activation='linear')
            ])

            model.compile(optimizer=Adam(learning_rate=0.001),
                          loss='mse',
                          metrics=['mae'])

            return model

    def _preprocess_data(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, np.ndarray]:
        """
        预处理时间序列数据
        """
        try:
            logging.info("Starting data preprocessing...")

            # 准备基础数据
            df = df[['timestamp', 'temperature', 'load']].copy()
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp').reset_index(drop=True)

            # 添加时间特征
            df['hour_sin'] = np.sin(2 * np.pi * df['timestamp'].dt.hour / 24)
            df['hour_cos'] = np.cos(2 * np.pi * df['timestamp'].dt.hour / 24)

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
                # 使用所有特征作为输入
                sequence = scaled_data[i:(i + self.lookback_points)]
                target = scaled_data[(i + self.lookback_points):(i + self.lookback_points + self.forecast_points), -1]

                X.append(sequence)
                y.append(target)

            return np.array(X), np.array(y)

        except Exception as e:
            logging.error(f"Error in sequence creation: {str(e)}")
            raise

    def predict(self, df: pd.DataFrame, save_dir: Optional[str] = None) -> Optional[pd.DataFrame]:
        """
        执行完整的预测流程
        """
        try:
            # 数据预处理
            processed_df, scaled_data = self._preprocess_data(df)

            # 创建序列
            X, y = self._create_sequences(scaled_data)
            logging.info(f"Training CNN with input shape: {X.shape}, output shape: {y.shape}")

            # 设置早停
            early_stopping = EarlyStopping(
                monitor='val_loss',
                patience=10,
                restore_best_weights=True
            )

            # 训练模型
            logging.info("Training CNN model...")
            history = self.model.fit(
                X, y,
                epochs=100,
                batch_size=128,
                validation_split=0.2,
                callbacks=[early_stopping],
                verbose=0
            )
            logging.info("Model training completed")

            # 准备最后一个时间窗口用于预测
            last_window = scaled_data[-self.lookback_points:].reshape(1, self.lookback_points, 4)

            # 生成预测
            logging.info("Generating predictions...")
            future_prediction = self.model.predict(last_window)[0]

            # 反标准化预测结果
            dummy_features = np.zeros((self.forecast_points, scaled_data.shape[1]))
            dummy_features[:, -1] = future_prediction
            final_predictions = self.scaler.inverse_transform(dummy_features)[:, -1]

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
                'predicted_load': final_predictions
            })

            # 可视化结果
            self._plot_predictions(processed_df, predictions_df, history, save_dir)

            # 输出预测统计信息
            self._print_prediction_summary(final_predictions)

            return predictions_df

        except Exception as e:
            logging.error(f"Error in prediction process: {str(e)}")
            return None

    def _plot_predictions(self, historical_df: pd.DataFrame,
                          predictions_df: pd.DataFrame,
                          history: object,
                          save_dir: Optional[str] = None) -> None:
        """
        绘制预测结果图表和训练历史
        """
        # 创建一个包含两个子图的图表
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 12))

        # 绘制预测结果
        historical_data = historical_df['load'].iloc[-self.lookback_points:]
        historical_timestamps = historical_df['timestamp'].iloc[-self.lookback_points:]

        ax1.plot(historical_timestamps, historical_data,
                 label='Historical Data', color='blue', alpha=0.6)
        ax1.plot(predictions_df['timestamp'], predictions_df['predicted_load'],
                 label='CNN Predicted Load', color='red', alpha=0.6)

        ax1.set_title(f'{self.forecast_hours}-hour CNN Load Forecast')
        ax1.set_xlabel('Time')
        ax1.set_ylabel('Load (MW)')
        ax1.legend()
        ax1.grid(True)
        ax1.tick_params(axis='x', rotation=45)

        # 绘制训练历史
        ax2.plot(history.history['loss'], label='Training Loss')
        ax2.plot(history.history['val_loss'], label='Validation Loss')
        ax2.set_title('Model Loss During Training')
        ax2.set_xlabel('Epoch')
        ax2.set_ylabel('Loss')
        ax2.legend()
        ax2.grid(True)

        plt.tight_layout()

        if save_dir:
            os.makedirs(save_dir, exist_ok=True)
            plt.savefig(os.path.join(save_dir, f'cnn_prediction.png'),
                        dpi=300, bbox_inches='tight')
            logging.info(f"CNN prediction plot saved in {save_dir}")
        else:
            plt.show()

        plt.close()

    def _print_prediction_summary(self, predictions: np.ndarray) -> None:
        """
        打印预测结果的统计信息
        """
        logging.info("CNN Prediction Summary:")
        logging.info(f"Mean Load: {predictions.mean():.2f} MW")
        logging.info(f"Standard Deviation: {predictions.std():.2f} MW")
        logging.info(f"Maximum Load: {predictions.max():.2f} MW")
        logging.info(f"Minimum Load: {predictions.min():.2f} MW")
        logging.info(f"Minimum Load: {predictions.min():.2f} MW")

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
            # 设置早停
            early_stopping = EarlyStopping(
                monitor='val_loss',
                patience=10,
                restore_best_weights=True
            )

            # 训练模型
            logging.info("Training CNN model...")
            history = self.model.fit(
                X_train, y_train,
                epochs=100,
                batch_size=128,
                validation_split=0.2,
                callbacks=[early_stopping],
                verbose=0
            )
            logging.info("Model training completed")

            # 生成预测
            logging.info("Generating predictions...")
            future_prediction = self.model.predict(X_test)[0]

            # 创建预测结果DataFrame
            predictions_df = pd.DataFrame({
                'timestamp': test_df['timestamp'],
                'predicted_load': future_prediction.flatten()[:len(test_df)]
            })

            # 可视化结果
            self._plot_predictions_with_split(test_df, predictions_df, history, save_dir)

            # 输出预测统计信息
            self._print_prediction_summary(future_prediction)

            return predictions_df

        except Exception as e:
            logging.error(f"Error in prediction process: {str(e)}")
            return None

    def _plot_predictions_with_split(self, test_df: pd.DataFrame,
                                     predictions_df: pd.DataFrame,
                                     history: object,
                                     save_dir: Optional[str] = None) -> None:
        """
        绘制预测结果图表和训练历史，基于训练测试集划分

        参数:
        test_df: pd.DataFrame - 测试数据
        predictions_df: pd.DataFrame - 预测结果
        history: object - 训练历史
        save_dir: Optional[str] - 保存目录
        """
        # 创建图表
        plt.figure(figsize=(15, 12))

        # 绘制预测结果
        plt.plot(test_df['timestamp'], test_df['load'],
                 label='Actual Load', color='blue', alpha=0.6)
        plt.plot(predictions_df['timestamp'], predictions_df['predicted_load'],
                 label='CNN Predicted Load', color='red', alpha=0.6)

        plt.title(f'CNN Load Forecast with Train-Test Split')
        plt.xlabel('Time')
        plt.ylabel('Load (MW)')
        plt.legend()
        plt.grid(True)
        plt.xticks(rotation=45)
        plt.tight_layout()

        if save_dir:
            os.makedirs(save_dir, exist_ok=True)
            plt.savefig(os.path.join(save_dir, f'cnn_prediction_split.png'),
                        dpi=300, bbox_inches='tight')
            logging.info(f"CNN prediction plot saved in {save_dir}")
        else:
            plt.show()

        plt.close()


