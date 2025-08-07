import tensorflow as tf
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Dense, Dropout, BatchNormalization, Input, Conv1D
from tensorflow.keras.layers import MaxPooling1D, Flatten, Concatenate, LSTM, Activation
from tensorflow.keras.layers import Add, Lambda
from tensorflow.keras.optimizers import Adam
from sklearn.preprocessing import MinMaxScaler
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from typing import Optional, Tuple
import logging
import os


class HybridPredictor:
    """基于CNN、LSTM和XGBoost的动态权重混合预测器"""

    def __init__(self, lookback_hours: int = 48, forecast_hours: int = 48,
                 sample_interval: str = '30T'):
        self.lookback_hours = lookback_hours
        self.forecast_hours = forecast_hours
        self.sample_interval = sample_interval
        self.lookback_points = int(lookback_hours * 60 / int(sample_interval[:-1]))
        self.forecast_points = int(forecast_hours * 60 / int(sample_interval[:-1]))
        self.scaler = MinMaxScaler(feature_range=(0, 1))

        # 检测GPU
        if tf.config.list_physical_devices('GPU'):
            logging.info("Hybrid model using GPU")
            tf.keras.mixed_precision.set_global_policy('mixed_float16')

        self.model = None
        self.val_losses = {'cnn': 0, 'lstm': 0, 'xgb': 0}

    def _build_weight_network(self, features):
        """构建动态权重生成网络"""
        x = Dense(64)(features)
        x = BatchNormalization()(x)
        x = Activation('relu')(x)
        x = Dropout(0.2)(x)

        x = Dense(32)(x)
        x = BatchNormalization()(x)
        x = Activation('relu')(x)
        x = Dropout(0.2)(x)

        x = Dense(3)(x)
        weights = Activation('softmax')(x)  # 确保权重和为1

        return weights

    def _build_cnn_branch(self, input_layer):
        """构建CNN分支"""
        x = Conv1D(filters=64, kernel_size=3, activation='relu')(input_layer)
        x = MaxPooling1D(pool_size=2)(x)
        x = Conv1D(filters=128, kernel_size=3, activation='relu')(x)
        x = MaxPooling1D(pool_size=2)(x)
        x = Conv1D(filters=256, kernel_size=3, activation='relu')(x)
        x = Flatten()(x)
        x = Dense(256)(x)
        x = Dropout(0.2)(x)
        return x

    def _build_lstm_branch(self, input_layer):
        """构建LSTM分支"""
        x = LSTM(units=64, return_sequences=True)(input_layer)
        x = Dropout(0.2)(x)
        x = LSTM(units=32)(x)
        x = Dropout(0.2)(x)
        x = Dense(256)(x)
        return x

    def _build_xgboost_branch(self, input_layer):
        """构建XGBoost分支"""
        x = Dense(1000)(input_layer)
        x = BatchNormalization()(x)
        x = Activation('relu')(x)
        x = Dropout(0.2)(x)

        x = Dense(512)(x)
        x = BatchNormalization()(x)
        x = Activation('relu')(x)
        x = Dropout(0.2)(x)

        x = Dense(256)(x)
        x = BatchNormalization()(x)
        x = Activation('relu')(x)
        x = Dropout(0.2)(x)
        return x

    def _build_model(self):
        """构建完整的混合模型"""
        # 特征输入
        cnn_input = Input(shape=(self.lookback_points, 4))
        lstm_input = Input(shape=(self.lookback_points, 4))
        xgb_input = Input(shape=(self.lookback_points * 4,))

        # 各分支预测
        cnn_out = self._build_cnn_branch(cnn_input)
        lstm_out = self._build_lstm_branch(lstm_input)
        xgb_out = self._build_xgboost_branch(xgb_input)

        # 生成动态权重
        concat_features = Concatenate()([cnn_out, lstm_out, xgb_out])
        weights = Dense(3, activation='softmax', name='weights')(concat_features)

        # 加权组合
        weighted = Lambda(lambda x: x[0][:, 0:1] * x[1] +
                                    x[0][:, 1:2] * x[2] +
                                    x[0][:, 2:3] * x[3],
                          name='weighted_sum')([weights, cnn_out, lstm_out, xgb_out])

        # 最终输出层
        outputs = Dense(self.forecast_points)(weighted)

        # 构建模型 - 注意这里只输出预测值
        model = Model(inputs=[cnn_input, lstm_input, xgb_input], outputs=outputs)

        # 编译模型
        model.compile(optimizer=Adam(learning_rate=0.001), loss='mse')

        return model

    def _preprocess_data(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, np.ndarray]:
        """数据预处理"""
        try:
            logging.info("Starting data preprocessing...")

            # 基础数据准备
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

    def _create_sequences(self, scaled_data: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """创建序列数据"""
        try:
            X_cnn, X_lstm, X_xgb, y = [], [], [], []
            for i in range(len(scaled_data) - self.lookback_points - self.forecast_points):
                sequence = scaled_data[i:(i + self.lookback_points)]
                target = scaled_data[(i + self.lookback_points):(i + self.lookback_points + self.forecast_points), -1]

                X_cnn.append(sequence)
                X_lstm.append(sequence)
                X_xgb.append(sequence.flatten())
                y.append(target)

            return np.array(X_cnn), np.array(X_lstm), np.array(X_xgb), np.array(y)

        except Exception as e:
            logging.error(f"Error in sequence creation: {str(e)}")
            raise

    def predict(self, df: pd.DataFrame, save_dir: Optional[str] = None) -> Optional[pd.DataFrame]:
        """执行预测"""
        try:
            # 数据预处理
            processed_df, scaled_data = self._preprocess_data(df)
            X_cnn, X_lstm, X_xgb, y = self._create_sequences(scaled_data)

            logging.info(f"Training Hybrid model with shapes: "
                         f"CNN={X_cnn.shape}, LSTM={X_lstm.shape}, "
                         f"XGB={X_xgb.shape}, output={y.shape}")

            # 构建和训练模型
            if self.model is None:
                self.model = self._build_model()

            # 训练回调函数
            callbacks = [
                tf.keras.callbacks.EarlyStopping(
                    monitor='val_loss',
                    patience=10,
                    restore_best_weights=True
                ),
                tf.keras.callbacks.ReduceLROnPlateau(
                    monitor='val_loss',
                    factor=0.5,
                    patience=5,
                    min_lr=1e-6
                )
            ]

            history = self.model.fit(
                [X_cnn, X_lstm, X_xgb],
                y,
                epochs=100,
                batch_size=128,
                validation_split=0.2,
                callbacks=callbacks,
                verbose=0
            )

            # 预测
            last_sequence = scaled_data[-self.lookback_points:]
            last_sequence_cnn = last_sequence.reshape(1, self.lookback_points, 4)
            last_sequence_lstm = last_sequence.reshape(1, self.lookback_points, 4)
            last_sequence_xgb = last_sequence.flatten().reshape(1, -1)

            # 获取预测值
            future_prediction = self.model.predict(
                [last_sequence_cnn, last_sequence_lstm, last_sequence_xgb]
            )

            # 尝试获取权重(如果可能的话)
            try:
                weight_model = Model(
                    inputs=self.model.input,
                    outputs=self.model.get_layer('weights').output
                )
                weights = weight_model.predict(
                    [last_sequence_cnn, last_sequence_lstm, last_sequence_xgb]
                )
            except:
                weights = None
                logging.info("Unable to extract model weights")

            # 反标准化
            dummy_features = np.zeros((self.forecast_points, scaled_data.shape[1]))
            dummy_features[:, -1] = future_prediction[0]
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
            self._plot_predictions(
                processed_df, predictions_df, history,
                weights[0] if weights is not None else None,
                save_dir
            )

            # 输出预测统计信息
            self._print_prediction_summary(final_predictions)

            return predictions_df

        except Exception as e:
            logging.error(f"Error in prediction process: {str(e)}")
            return None

    def _plot_predictions(self, historical_df: pd.DataFrame,
                          predictions_df: pd.DataFrame,
                          history: any,
                          weights: Optional[np.ndarray] = None,
                          save_dir: Optional[str] = None) -> None:
        """绘制预测结果和训练历史"""
        plt.style.use('classic')
        plt.rcParams.update({
            'font.family': 'DejaVu Sans',
            'font.size': 10,
            'axes.labelsize': 12,
            'axes.titlesize': 12,
            'figure.dpi': 300
        })

        # 确定图表布局
        if weights is not None:
            fig = plt.figure(figsize=(15, 12))
            gs = plt.GridSpec(2, 2)
        else:
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 12))

        # 绘制预测结果
        if weights is not None:
            ax1 = fig.add_subplot(gs[0, :])
        historical_data = historical_df['load'].iloc[-self.lookback_points:]
        historical_timestamps = historical_df['timestamp'].iloc[-self.lookback_points:]
        ax1.plot(historical_timestamps, historical_data,
                 label='Historical Data', color='blue', alpha=0.6)
        ax1.plot(predictions_df['timestamp'], predictions_df['predicted_load'],
                 label='Hybrid Predicted Load', color='red', alpha=0.6)
        ax1.set_title(f'{self.forecast_hours}-hour Hybrid Load Forecast')
        ax1.set_xlabel('Time')
        ax1.set_ylabel('Load (MW)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        ax1.tick_params(axis='x', rotation=45)

        # 绘制训练损失
        if weights is not None:
            ax2 = fig.add_subplot(gs[1, 0])
        ax2.plot(history.history['loss'], label='Training Loss')
        ax2.plot(history.history['val_loss'], label='Validation Loss')
        ax2.set_title('Model Training History')
        ax2.set_xlabel('Epoch')
        ax2.set_ylabel('Loss')
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        # 绘制权重分布(如果有)
        if weights is not None:
            ax3 = fig.add_subplot(gs[1, 1])
            model_names = ['CNN', 'LSTM', 'XGBoost']
            x = np.arange(len(model_names))
            ax3.bar(x, weights, alpha=0.8)
            ax3.set_title('Model Weights Distribution')
            ax3.set_ylabel('Weight')
            ax3.set_xticks(x)
            ax3.set_xticklabels(model_names)
            ax3.grid(True, alpha=0.3)

        plt.tight_layout()

        if save_dir:
            os.makedirs(save_dir, exist_ok=True)
            plt.savefig(os.path.join(save_dir, f'hybrid_prediction.png'),
                        dpi=300, bbox_inches='tight')
            logging.info(f"Hybrid model prediction plot saved in {save_dir}")
        else:
            plt.show()

        plt.close()

    def _print_prediction_summary(self, predictions: np.ndarray) -> None:
        """打印预测结果统计信息"""
        logging.info("Hybrid Model Prediction Summary:")
        logging.info(f"Mean Load: {predictions.mean():.2f} MW")
        logging.info(f"Standard Deviation: {predictions.std():.2f} MW")
        logging.info(f"Maximum Load: {predictions.max():.2f} MW")
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
            # 构建模型（如果尚未构建）
            if self.model is None:
                self.model = self._build_model()

            # 准备模型输入数据
            # 为CNN, LSTM和XGBoost分支准备不同格式的输入
            X_cnn_train = []
            X_lstm_train = []
            X_xgb_train = []

            # 重新处理训练数据
            for i in range(len(X_train)):
                # 将数据重塑为三个分支需要的形状
                sequence = X_train[i].reshape(-1, 4)  # 假设重塑为(lookback_points, 4)
                X_cnn_train.append(sequence)
                X_lstm_train.append(sequence)
                X_xgb_train.append(X_train[i])  # XGBoost分支使用展平的特征

            X_cnn_train = np.array(X_cnn_train)
            X_lstm_train = np.array(X_lstm_train)
            X_xgb_train = np.array(X_xgb_train)

            # 处理测试数据
            X_cnn_test = []
            X_lstm_test = []
            X_xgb_test = []
            for i in range(len(X_test)):
                sequence = X_test[i].reshape(-1, 4)
                X_cnn_test.append(sequence)
                X_lstm_test.append(sequence)
                X_xgb_test.append(X_test[i])

            X_cnn_test = np.array(X_cnn_test)
            X_lstm_test = np.array(X_lstm_test)
            X_xgb_test = np.array(X_xgb_test)

            # 训练回调函数
            callbacks = [
                tf.keras.callbacks.EarlyStopping(
                    monitor='val_loss',
                    patience=10,
                    restore_best_weights=True
                ),
                tf.keras.callbacks.ReduceLROnPlateau(
                    monitor='val_loss',
                    factor=0.5,
                    patience=5,
                    min_lr=1e-6
                )
            ]

            # 训练模型
            logging.info("Training Hybrid (CNN+LSTM+XGBoost) model with split data...")
            history = self.model.fit(
                [X_cnn_train, X_lstm_train, X_xgb_train], y_train,
                epochs=100,
                batch_size=128,
                validation_split=0.2,
                callbacks=callbacks,
                verbose=0
            )
            logging.info("Model training completed")

            # 生成预测
            logging.info("Generating predictions on test data...")
            predictions = self.model.predict([X_cnn_test, X_lstm_test, X_xgb_test])

            # 创建预测结果DataFrame
            predictions_df = pd.DataFrame({
                'timestamp': test_df['timestamp'],
                'predicted_load': predictions.flatten()[:len(test_df)]
            })

            # 尝试获取权重(如果可能的话)
            try:
                weight_model = Model(
                    inputs=self.model.input,
                    outputs=self.model.get_layer('weights').output
                )
                weights = weight_model.predict(
                    [X_cnn_test[:1], X_lstm_test[:1], X_xgb_test[:1]]
                )
            except:
                weights = None
                logging.info("Unable to extract model weights")

            # 可视化结果
            self._plot_predictions_with_split(test_df, predictions_df, weights, save_dir)

            # 输出预测统计信息
            self._print_prediction_summary(predictions.flatten())

            return predictions_df

        except Exception as e:
            logging.error(f"Error in prediction process with split: {str(e)}")
            return None

    def _plot_predictions_with_split(self, test_df: pd.DataFrame,
                                     predictions_df: pd.DataFrame,
                                     weights: Optional[np.ndarray] = None,
                                     save_dir: Optional[str] = None) -> None:
        """
        绘制基于训练测试集划分的预测结果图表

        参数:
        test_df: pd.DataFrame - 测试数据
        predictions_df: pd.DataFrame - 预测结果
        weights: Optional[np.ndarray] - 模型权重（可选）
        save_dir: Optional[str] - 保存目录
        """
        # # 设置图表样式
        # plt.style.use('classic')
        # plt.rcParams.update({
        #     'font.family': 'DejaVu Sans',
        #     'font.size': 10,
        #     'axes.labelsize': 12,
        #     'axes.titlesize': 12,
        #     'figure.dpi': 300
        # })

        # 确定图表布局
        if weights is not None:
            # 创建包含权重可视化的图表
            fig = plt.figure(figsize=(15, 10))
            gs = plt.GridSpec(2, 1, height_ratios=[2, 1])
            ax1 = fig.add_subplot(gs[0])
            ax2 = fig.add_subplot(gs[1])
        else:
            # 创建单一图表
            plt.figure(figsize=(15, 6))
            ax1 = plt.gca()

        # 绘制预测结果与实际值的对比
        ax1.plot(test_df['timestamp'], test_df['load'],
                 label='Actual Load', color='blue', alpha=0.6)
        ax1.plot(predictions_df['timestamp'], predictions_df['predicted_load'],
                 label='Hybrid Predicted Load', color='red', alpha=0.6)
        ax1.set_title('Hybrid (CNN+LSTM+XGBoost) Load Forecast with Train-Test Split')
        ax1.set_xlabel('Time')
        ax1.set_ylabel('Load (MW)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        ax1.tick_params(axis='x', rotation=45)

        # 如果有权重信息，绘制权重分布
        if weights is not None:
            model_names = ['CNN', 'LSTM', 'XGBoost']
            x = np.arange(len(model_names))
            ax2.bar(x, weights[0], alpha=0.8)
            ax2.set_title('Model Weights Distribution')
            ax2.set_ylabel('Weight')
            ax2.set_xticks(x)
            ax2.set_xticklabels(model_names)
            ax2.grid(True, alpha=0.3)

        plt.tight_layout()

        if save_dir:
            os.makedirs(save_dir, exist_ok=True)
            plt.savefig(os.path.join(save_dir, f'hybrid_prediction_split.png'),
                        dpi=300, bbox_inches='tight')
            logging.info(f"Hybrid (CNN+LSTM+XGBoost) prediction plot saved in {save_dir}")
        else:
            plt.show()

        plt.close()

"""无权重绘图代码
def predict_with_split(self, X_train, y_train, X_test, test_df: pd.DataFrame, save_dir: Optional[str] = None) -> \
        Optional[pd.DataFrame]:
    '''
    使用预先划分的训练集和测试集进行预测和评估

    参数:
    X_train: np.ndarray - 训练特征
    y_train: np.ndarray - 训练目标
    X_test: np.ndarray - 测试特征
    test_df: pd.DataFrame - 包含测试数据的原始DataFrame
    save_dir: Optional[str] - 保存目录

    返回:
    Optional[pd.DataFrame] - 包含预测结果的DataFrame
    '''
    try:
        # 构建模型（如果尚未构建）
        if self.model is None:
            self.model = self._build_model()

        # 准备模型输入数据
        # 为CNN, LSTM和XGBoost分支准备不同格式的输入
        X_cnn_train = []
        X_lstm_train = []
        X_xgb_train = []
        
        # 重新处理训练数据
        for i in range(len(X_train)):
            # 将数据重塑为三个分支需要的形状
            sequence = X_train[i].reshape(-1, 4)  # 假设重塑为(lookback_points, 4)
            X_cnn_train.append(sequence)
            X_lstm_train.append(sequence)
            X_xgb_train.append(X_train[i])  # XGBoost分支使用展平的特征
        
        X_cnn_train = np.array(X_cnn_train)
        X_lstm_train = np.array(X_lstm_train)
        X_xgb_train = np.array(X_xgb_train)
        
        # 处理测试数据
        X_cnn_test = []
        X_lstm_test = []
        X_xgb_test = []
        for i in range(len(X_test)):
            sequence = X_test[i].reshape(-1, 4)
            X_cnn_test.append(sequence)
            X_lstm_test.append(sequence)
            X_xgb_test.append(X_test[i])
        
        X_cnn_test = np.array(X_cnn_test)
        X_lstm_test = np.array(X_lstm_test)
        X_xgb_test = np.array(X_xgb_test)

        # 训练回调函数
        callbacks = [
            tf.keras.callbacks.EarlyStopping(
                monitor='val_loss',
                patience=10,
                restore_best_weights=True
            ),
            tf.keras.callbacks.ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.5,
                patience=5,
                min_lr=1e-6
            )
        ]

        # 训练模型
        logging.info("Training Hybrid (CNN+LSTM+XGBoost) model with split data...")
        history = self.model.fit(
            [X_cnn_train, X_lstm_train, X_xgb_train], y_train,
            epochs=100,
            batch_size=128,
            validation_split=0.2,
            callbacks=callbacks,
            verbose=0
        )
        logging.info("Model training completed")

        # 生成预测
        logging.info("Generating predictions on test data...")
        predictions = self.model.predict([X_cnn_test, X_lstm_test, X_xgb_test])

        # 创建预测结果DataFrame
        predictions_df = pd.DataFrame({
            'timestamp': test_df['timestamp'],
            'predicted_load': predictions.flatten()[:len(test_df)]
        })

        # 可视化结果
        self._plot_predictions_with_split(test_df, predictions_df, None, save_dir)

        # 输出预测统计信息
        self._print_prediction_summary(predictions.flatten())

        return predictions_df

    except Exception as e:
        logging.error(f"Error in prediction process with split: {str(e)}")
        return None

def _plot_predictions_with_split(self, test_df: pd.DataFrame,
                                 predictions_df: pd.DataFrame,
                                 weights: Optional[np.ndarray] = None,
                                 save_dir: Optional[str] = None) -> None:
    '''
    绘制基于训练测试集划分的预测结果图表

    参数:
    test_df: pd.DataFrame - 测试数据
    predictions_df: pd.DataFrame - 预测结果
    weights: Optional[np.ndarray] - 模型权重（未使用）
    save_dir: Optional[str] - 保存目录
    '''
    # 设置图表样式
    plt.style.use('classic')
    plt.rcParams.update({
        'font.family': 'DejaVu Sans',
        'font.size': 10,
        'axes.labelsize': 12,
        'axes.titlesize': 12,
        'figure.dpi': 300
    })

    # 创建单一图表
    plt.figure(figsize=(15, 6))

    # 绘制预测结果与实际值的对比
    plt.plot(test_df['timestamp'], test_df['load'],
            label='Actual Load', color='blue', alpha=0.6)
    plt.plot(predictions_df['timestamp'], predictions_df['predicted_load'],
            label='Hybrid Predicted Load', color='red', alpha=0.6)
    plt.title('Hybrid (CNN+LSTM+XGBoost) Load Forecast with Train-Test Split')
    plt.xlabel('Time')
    plt.ylabel('Load (MW)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()

    # 注释掉权重信息绘图部分
    '''
    # 如果有权重信息，绘制权重分布
    if weights is not None:
        model_names = ['CNN', 'LSTM', 'XGBoost']
        x = np.arange(len(model_names))
        ax2.bar(x, weights[0], alpha=0.8)
        ax2.set_title('Model Weights Distribution')
        ax2.set_ylabel('Weight')
        ax2.set_xticks(x)
        ax2.set_xticklabels(model_names)
        ax2.grid(True, alpha=0.3)
    '''

    if save_dir:
        os.makedirs(save_dir, exist_ok=True)
        plt.savefig(os.path.join(save_dir, f'hybrid_prediction_split.png'),
                    dpi=300, bbox_inches='tight')
        logging.info(f"Hybrid (CNN+LSTM+XGBoost) prediction plot saved in {save_dir}")
    else:
        plt.show()

    plt.close()
"""
