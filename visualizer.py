import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from typing import List
import os
from datetime import datetime
import logging


class Visualizer:
    def __init__(self, save_dir: str):
        self.save_dir = save_dir
        os.makedirs(save_dir, exist_ok=True)
        self._setup_plot_style()

    def _setup_plot_style(self):
        """设置SCI风格的图表样式"""
        plt.style.use('classic')  # 使用经典样式作为基础
        plt.rcParams.update({
            'figure.figsize': (8, 6),  # 更适合的默认图表大小
            'font.family': 'DejaVu Sans',  # 使用Arial字体
            'font.size': 10,  # 基础字号
            'axes.labelsize': 12,  # 轴标签字号
            'axes.titlesize': 12,  # 标题字号
            'xtick.labelsize': 10,  # x轴刻度标签字号
            'ytick.labelsize': 10,  # y轴刻度标签字号
            'lines.linewidth': 1.5,  # 线条宽度
            'lines.markersize': 6,  # 标记大小
            'legend.fontsize': 10,  # 图例字号
            'axes.grid': True,  # 显示网格
            'grid.alpha': 0.3,  # 网格透明度
            'axes.axisbelow': True,  # 网格线置于数据之下
            'axes.spines.top': False,  # 隐藏上边框
            'axes.spines.right': False,  # 隐藏右边框
            'figure.dpi': 300,  # 高分辨率
            'savefig.dpi': 300,  # 保存时的分辨率
            'savefig.bbox': 'tight',  # 紧凑的边界
            'savefig.pad_inches': 0.1  # 边距
        })

    def _save_plot(self, name: str):
        """
        保存图表

        参数:
        name: str - 图表名称
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{name}.png"
        plt.savefig(os.path.join(self.save_dir, filename), dpi=300, bbox_inches='tight')
        plt.close()
        logging.info(f"Plot saved: {filename}")

    def plot_time_series(self, df: pd.DataFrame, columns: List[str], title: str):
        """
        重写时间序列绘制函数，分别绘制负载和温度
        """
        # 绘制负载时间序列
        if 'load' in df.columns:
            plt.figure(figsize=(16, 6))
            plt.plot(df['timestamp'], df['load'], color='blue', label='Load', alpha=0.8)
            plt.title('Load Time Series', pad=20)
            plt.xlabel('Date')
            plt.ylabel('Load (MW)')
            plt.legend(loc='upper left')
            plt.grid(True, alpha=0.3)
            plt.xticks(rotation=45)
            plt.tight_layout()
            self._save_plot('time_series_load')

        # 绘制温度时间序列
        if 'temperature' in df.columns:
            plt.figure(figsize=(16, 6))
            plt.plot(df['timestamp'], df['temperature'], color='red', label='Temperature', alpha=0.8)
            plt.title('Temperature Time Series', pad=20)
            plt.xlabel('Date')
            plt.ylabel('Temperature (°C)')
            plt.legend(loc='upper left')
            plt.grid(True, alpha=0.3)
            plt.xticks(rotation=45)
            plt.tight_layout()
            self._save_plot('time_series_temperature')

    def plot_correlation_heatmap(self, df: pd.DataFrame, features: List[str]):
        """
        重写相关性热力图函数，不显示具体数值
        """
        plt.figure(figsize=(12, 10))
        correlation = df[features].corr()
        sns.heatmap(correlation, annot=True,fmt=".2f", cmap='coolwarm', center=0)
        plt.title('Feature Correlation Heatmap', pad=20)
        self._save_plot('correlation_heatmap')

    def plot_feature_distributions(self, df: pd.DataFrame, features: List[str]):
        """
        绘制特征分布图

        参数:
        df: pd.DataFrame - 包含特征的DataFrame
        features: List[str] - 需要分析分布的特征列表
        """
        n_features = len(features)
        n_cols = 2
        n_rows = (n_features + 1) // 2

        plt.figure(figsize=(15, 5 * n_rows))
        for i, feature in enumerate(features, 1):
            plt.subplot(n_rows, n_cols, i)
            sns.histplot(data=df, x=feature, kde=True)
            plt.title(f'{feature} Distribution')
            plt.xlabel(feature)
            plt.ylabel('Count')

        plt.tight_layout()
        self._save_plot('feature_distributions')

    def plot_daily_pattern(self, df: pd.DataFrame):
        """
        绘制每日负载模式图

        参数:
        df: pd.DataFrame - 包含负载数据的DataFrame
        """
        daily_df = df.copy()
        daily_df['hour'] = daily_df['timestamp'].dt.hour
        daily_pattern = daily_df.groupby('hour')['load'].agg(['mean', 'std']).reset_index()

        plt.figure(figsize=(12, 6))
        plt.plot(daily_pattern['hour'], daily_pattern['mean'], 'b-', label='Mean Load')
        plt.fill_between(
            daily_pattern['hour'],
            daily_pattern['mean'] - daily_pattern['std'],
            daily_pattern['mean'] + daily_pattern['std'],
            alpha=0.2,
            label='±1 std'
        )

        plt.title('Average Daily Load Pattern')
        plt.xlabel('Hour of Day')
        plt.ylabel('Load (MW)')
        plt.legend()
        plt.grid(True)
        plt.xticks(range(0, 24, 2))
        self._save_plot('daily_pattern')

    def plot_yearly_volatility(self, df: pd.DataFrame):
        """Plot yearly volatility analysis without categorical warnings"""
        df['year'] = pd.to_datetime(df['timestamp']).dt.year

        def calculate_volatility(group):
            return group.std() / group.mean() * 100

        yearly_load = df.groupby('year')['load'].apply(calculate_volatility)
        yearly_temp = df.groupby('year')['temperature'].apply(calculate_volatility)

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 8))

        # Plot using numeric indices
        years = np.array(yearly_load.index)
        x = np.arange(len(years))

        # Load volatility
        ax1.bar(x, yearly_load.values, color='lightblue', alpha=0.8)
        ax1.set_title('Yearly Load Volatility', pad=10)
        ax1.set_ylabel('Volatility (%)')
        ax1.grid(True, alpha=0.3)
        ax1.set_xticks(x)
        ax1.set_xticklabels(years, rotation=45)

        # Temperature volatility
        ax2.bar(x, yearly_temp.values, color='lightcoral', alpha=0.8)
        ax2.set_title('Yearly Temperature Volatility', pad=10)
        ax2.set_ylabel('Volatility (%)')
        ax2.grid(True, alpha=0.3)
        ax2.set_xticks(x)
        ax2.set_xticklabels(years, rotation=45)

        plt.tight_layout()
        self._save_plot('yearly_volatility')

    def plot_quarterly_volatility(self, df: pd.DataFrame):
        """Plot quarterly volatility analysis without categorical warnings"""
        df['quarter'] = pd.to_datetime(df['timestamp']).dt.to_period('Q')

        def calculate_volatility(group):
            return group.std() / group.mean() * 100

        quarterly_load = df.groupby('quarter')['load'].apply(calculate_volatility)
        quarterly_temp = df.groupby('quarter')['temperature'].apply(calculate_volatility)

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 8))

        # Plot using numeric indices
        x = np.arange(len(quarterly_load))
        quarters = [str(q) for q in quarterly_load.index]

        # Load volatility
        ax1.bar(x, quarterly_load.values, color='lightblue', alpha=0.8)
        ax1.set_title('Quarterly Load Volatility', pad=10)
        ax1.set_ylabel('Volatility (%)')
        ax1.set_xticks(x)
        ax1.set_xticklabels(quarters, rotation=45)
        ax1.grid(True, alpha=0.3)

        # Temperature volatility
        ax2.bar(x, quarterly_temp.values, color='lightcoral', alpha=0.8)
        ax2.set_title('Quarterly Temperature Volatility', pad=10)
        ax2.set_ylabel('Volatility (%)')
        ax2.set_xticks(x)
        ax2.set_xticklabels(quarters, rotation=45)
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()
        self._save_plot('quarterly_volatility')

    def plot_monthly_volatility(self, df: pd.DataFrame):
        """Plot monthly volatility analysis without categorical warnings"""
        df['month'] = pd.to_datetime(df['timestamp']).dt.to_period('M')

        def calculate_volatility(group):
            return group.std() / group.mean() * 100

        monthly_load = df.groupby('month')['load'].apply(calculate_volatility)
        monthly_temp = df.groupby('month')['temperature'].apply(calculate_volatility)

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 8))

        # Plot using numeric indices
        x = np.arange(len(monthly_load))
        months = [str(m) for m in monthly_load.index]

        # Load volatility
        ax1.bar(x, monthly_load.values, color='lightblue', alpha=0.8)
        ax1.set_title('Monthly Load Volatility', pad=10)
        ax1.set_ylabel('Volatility (%)')
        # Only show every 6th label to avoid crowding
        ax1.set_xticks(x[::6])
        ax1.set_xticklabels(months[::6], rotation=45)
        ax1.grid(True, alpha=0.3)

        # Temperature volatility
        ax2.bar(x, monthly_temp.values, color='lightcoral', alpha=0.8)
        ax2.set_title('Monthly Temperature Volatility', pad=10)
        ax2.set_ylabel('Volatility (%)')
        ax2.set_xticks(x[::6])
        ax2.set_xticklabels(months[::6], rotation=45)
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()
        self._save_plot('monthly_volatility')

    def plot_temp_load_relationship(self, df: pd.DataFrame):
        """
        重写温度负载关系图，加宽图表
        """
        plt.figure(figsize=(16, 6))
        sns.scatterplot(data=df, x='temperature', y='load', alpha=0.5)

        # 添加趋势线
        z = np.polyfit(df['temperature'], df['load'], 2)
        p = np.poly1d(z)
        temp_range = np.linspace(df['temperature'].min(), df['temperature'].max(), 100)
        plt.plot(temp_range, p(temp_range), 'r--', linewidth=1.5, label='Trend Line')

        plt.title('Temperature vs Load Relationship', pad=20)
        plt.xlabel('Temperature (°C)')
        plt.ylabel('Load (MW)')
        plt.legend()
        plt.grid(True, alpha=0.3)
        self._save_plot('temp_load_relationship')

    def plot_weekly_pattern(self, df: pd.DataFrame):
        """
        重写每周负载模式图，使用新样式
        """
        weekly_df = df.copy()
        weekly_df['day_of_week'] = weekly_df['timestamp'].dt.day_name()
        days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

        # Create categorical type and ensure proper ordering
        weekly_df['day_of_week'] = pd.Categorical(weekly_df['day_of_week'],
                                                  categories=days_order,
                                                  ordered=True)

        # Calculate statistics with the categorical column
        weekly_pattern = weekly_df.groupby('day_of_week')['load'].agg(['mean', 'std']).reset_index()

        plt.figure(figsize=(16, 6))

        # Use numerical indices for plotting
        x = np.arange(len(days_order))
        plt.plot(x, weekly_pattern['mean'], 'b-', linewidth=1.5)
        plt.fill_between(
            x,
            weekly_pattern['mean'] - weekly_pattern['std'],
            weekly_pattern['mean'] + weekly_pattern['std'],
            alpha=0.2,
            color='blue'
        )

        plt.title('Average Weekly Load Pattern', pad=20)
        plt.xlabel('Day of Week')
        plt.ylabel('Load (MW)')
        plt.grid(True, alpha=0.3)
        plt.xticks(x, days_order, rotation=45)
        self._save_plot('weekly_pattern')
