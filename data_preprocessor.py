import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler, RobustScaler
from datetime import datetime, timedelta
import warnings
import logging

warnings.filterwarnings('ignore')


class NSWDataPreprocessor:
    def __init__(self, window_size=1440):
        """
        初始化预处理器

        参数:
        window_size: int - 时间窗口大小，默认为1440（24小时）
        """
        self.window_size = window_size
        self.scalers = {}

    def _is_nsw_holiday(self, dates):
        """
        判断是否为NSW的公共假期

        参数:
        dates: pandas Series 或 DatetimeIndex，日期数据
        """
        holidays = [
            # 2010
            '2010-01-01', '2010-01-26', '2010-04-02', '2010-04-05', '2010-04-26',
            '2010-06-14', '2010-10-04', '2010-12-27', '2010-12-28',
            # 2011
            '2011-01-03', '2011-01-26', '2011-04-22', '2011-04-25', '2011-04-26',
            '2011-06-13', '2011-10-03', '2011-12-26', '2011-12-27',
            # 2012
            '2012-01-02', '2012-01-26', '2012-04-06', '2012-04-09', '2012-04-25',
            '2012-06-11', '2012-10-01', '2012-12-25', '2012-12-26',
            # 2013
            '2013-01-01', '2013-01-28', '2013-03-29', '2013-04-01', '2013-04-25',
            '2013-06-10', '2013-10-07', '2013-12-25', '2013-12-26',
            # 2014
            '2014-01-01', '2014-01-27', '2014-04-18', '2014-04-21', '2014-04-25',
            '2014-06-09', '2014-10-06', '2014-12-25', '2014-12-26',
            # 2015
            '2015-01-01', '2015-01-26', '2015-04-03', '2015-04-06', '2015-04-25',
            '2015-06-08', '2015-10-05', '2015-12-25', '2015-12-28',
            # 2016
            '2016-01-01', '2016-01-26', '2016-03-25', '2016-03-28', '2016-04-25',
            '2016-06-13', '2016-10-03', '2016-12-26', '2016-12-27',
            # 2017
            '2017-01-02', '2017-01-26', '2017-04-14', '2017-04-17', '2017-04-25',
            '2017-06-12', '2017-10-02', '2017-12-25', '2017-12-26',
            # 2018
            '2018-01-01', '2018-01-26', '2018-03-30', '2018-04-02', '2018-04-25',
            '2018-06-11', '2018-10-01', '2018-12-25', '2018-12-26',
            # 2019
            '2019-01-01', '2019-01-28', '2019-04-19', '2019-04-22', '2019-04-25',
            '2019-06-10', '2019-10-07', '2019-12-25', '2019-12-26',
            # 2020
            '2020-01-01', '2020-01-27', '2020-04-10', '2020-04-13', '2020-04-25',
            '2020-06-08', '2020-10-05', '2020-12-25', '2020-12-28',
            # 2021
            '2021-01-01', '2021-01-26', '2021-04-02', '2021-04-05', '2021-04-25',
            '2021-06-14', '2021-10-04', '2021-12-27', '2021-12-28',
            # 2022
            '2022-01-03', '2022-01-26', '2022-04-15', '2022-04-18', '2022-04-25',
            '2022-06-13', '2022-10-03', '2022-12-26', '2022-12-27',
            # 2023
            '2023-01-01', '2023-01-26', '2023-04-07', '2023-04-10',
            '2023-04-25', '2023-06-12', '2023-10-02', '2023-12-25', '2023-12-26'
        ]
        holidays = pd.to_datetime(holidays).date
        if isinstance(dates, pd.Series):
            return dates.dt.date.isin(holidays).astype(int)
        else:
            return pd.Series(dates.date.isin(holidays), index=dates).astype(int)

    def load_and_merge_data(self, temp_file, demand_file):
        """
        读取并合并温度和需求数据
        """
        try:
            # 读取温度数据
            temp_df = pd.read_csv(temp_file)
            temp_df.columns = ['location', 'datetime', 'temperature']
            temp_df['datetime'] = pd.to_datetime(temp_df['datetime'], format='%d/%m/%Y %H:%M')

            # 如果有多个地点，取平均温度
            temp_df = temp_df.groupby('datetime')['temperature'].mean().reset_index()

            # 读取需求数据
            demand_df = pd.read_csv(demand_file)
            demand_df.columns = ['datetime', 'totaldemand', 'regionid']
            demand_df['datetime'] = pd.to_datetime(demand_df['datetime'], format='%d/%m/%Y %H:%M')

            # 合并数据
            df = pd.merge(demand_df, temp_df, on='datetime', how='inner')

            # 只保留需要的列并重命名
            df = df[['datetime', 'temperature', 'totaldemand']]
            df.columns = ['timestamp', 'temperature', 'load']

            # 确保数据按时间排序
            df = df.sort_values('timestamp').reset_index(drop=True)

            # 检查并处理缺失值
            if df.isnull().any().any():
                logging.warning("Find missing values and fill them in using interpolation.")
                df = self._handle_missing_values(df)

            return df

        except Exception as e:
            logging.error(f"Data loading error: {str(e)}")
            return None

    def _handle_missing_values(self, df):
        """
        处理缺失值
        """
        # 对温度和负载使用线性插值
        df['temperature'] = df['temperature'].interpolate(method='linear')
        df['load'] = df['load'].interpolate(method='linear')
        return df

    def _handle_outliers(self, df, threshold=3):
        """
        使用IQR方法处理异常值
        """
        for column in ['temperature', 'load']:
            # 按每个小时分组计算异常值
            df['hour'] = df['timestamp'].dt.hour
            grouped = df.groupby('hour')[column]

            Q1 = grouped.transform('quantile', 0.25)
            Q3 = grouped.transform('quantile', 0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - threshold * IQR
            upper_bound = Q3 + threshold * IQR

            # 记录并处理异常值
            outliers = df[(df[column] < lower_bound) | (df[column] > upper_bound)][column]
            if len(outliers) > 0:
                logging.warning(f"{column} column contains {len(outliers)} outliers.")

            df.loc[df[column] < lower_bound, column] = lower_bound
            df.loc[df[column] > upper_bound, column] = upper_bound

        df = df.drop('hour', axis=1)
        return df

    def create_features(self, df):
        """
        为NSW数据创建特征
        """
        # 基本时间特征
        df['hour'] = df['timestamp'].dt.hour
        df['minute'] = df['timestamp'].dt.minute
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        df['month'] = df['timestamp'].dt.month
        df['day'] = df['timestamp'].dt.day
        df['week_of_year'] = df['timestamp'].dt.isocalendar().week
        df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)

        # NSW的工作日/假期特征
        df['is_holiday'] = self._is_nsw_holiday(df['timestamp'])

        # 周期性特征
        df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
        df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
        df['minute_sin'] = np.sin(2 * np.pi * df['minute'] / 60)
        df['minute_cos'] = np.cos(2 * np.pi * df['minute'] / 60)
        df['day_of_week_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
        df['day_of_week_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)
        df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
        df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)

        # 负载相关特征
        df['load_rolling_mean_24h'] = df['load'].rolling(window=24).mean()
        df['load_rolling_std_24h'] = df['load'].rolling(window=24).std()
        df['load_rolling_mean_7d'] = df['load'].rolling(window=24 * 7).mean()

        # 温度相关特征
        df['temp_rolling_mean_24h'] = df['temperature'].rolling(window=24).mean()
        df['temp_diff'] = df['temperature'].diff()
        df['temp_rolling_std_24h'] = df['temperature'].rolling(window=24).std()

        # 温度和负载的交互特征
        df['temp_load_interaction'] = df['temperature'] * df['load_rolling_mean_24h']

        # 填充滚动特征的空值
        rolling_columns = [col for col in df.columns if 'rolling' in col or 'diff' in col]
        df[rolling_columns] = df[rolling_columns].fillna(method='bfill')

        return df

    def scale_data(self, data, feature_names):
        """
        分别对不同类型的特征进行标准化
        """
        scaled_data = np.zeros_like(data, dtype=np.float32)

        # 对周期性特征不进行标准化
        periodic_features = ['hour_sin', 'hour_cos', 'minute_sin', 'minute_cos',
                             'day_of_week_sin', 'day_of_week_cos', 'month_sin', 'month_cos']

        # 对布尔特征不进行标准化
        boolean_features = ['is_weekend', 'is_holiday']

        # 对不同类型的特征使用不同的标准化方法
        for i, feature in enumerate(feature_names):
            if feature in periodic_features or feature in boolean_features:
                scaled_data[:, i] = data[:, i]
            else:
                scaler = RobustScaler() if 'load' in feature or 'temperature' in feature else MinMaxScaler()
                scaled_data[:, i] = scaler.fit_transform(data[:, i].reshape(-1, 1)).ravel()
                self.scalers[feature] = scaler

        return scaled_data

    def create_sequences(self, data, seq_length):
        """
        创建时间窗口数据
        """
        sequences = []
        targets = []

        for i in range(len(data) - seq_length - 2880):
            sequence = data[i:(i + seq_length)]
            target = data[i + seq_length:i + seq_length + 2880, -1]

            if len(sequence) == seq_length and len(target) == 2880:
                sequences.append(sequence)
                targets.append(target)

        return np.array(sequences), np.array(targets)

    def prepare_data(self, temp_file, demand_file):
        """
        完整的NSW数据准备流程
        """
        # 加载并合并数据
        df = self.load_and_merge_data(temp_file, demand_file)
        if df is None:
            return None

        # 创建特征
        df = self.create_features(df)

        # 选择特征
        feature_names = [
            'hour_sin', 'hour_cos', 'minute_sin', 'minute_cos',
            'day_of_week_sin', 'day_of_week_cos', 'month_sin', 'month_cos',
            'is_weekend', 'is_holiday',
            'temperature', 'temp_rolling_mean_24h', 'temp_diff', 'temp_rolling_std_24h',
            'load', 'load_rolling_mean_24h', 'load_rolling_std_24h', 'load_rolling_mean_7d',
            'temp_load_interaction'
        ]

        logging.info("Start with feature engineering.")
        data = df[feature_names].values
        scaled_data = self.scale_data(data, feature_names)

        logging.info("Start creating sequences.")
        # 创建序列
        X, y = self.create_sequences(scaled_data, self.window_size)

        # 划分训练集和测试集
        train_size = int(len(X) * 0.8)
        X_train, X_test = X[:train_size], X[train_size:]
        y_train, y_test = y[:train_size], y[train_size:]

        return X_train, X_test, y_train, y_test, feature_names, df