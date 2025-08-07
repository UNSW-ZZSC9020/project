import torch
from torch.utils.data import Dataset
import numpy as np
from typing import Tuple


class LoadForecastingDataset(Dataset):
    """
    电力负载预测数据集类
    """

    def __init__(self, features: np.ndarray, targets: np.ndarray):
        """
        初始化数据集

        参数:
        features: np.ndarray - 输入特征，形状为 (N, sequence_length, num_features)
        targets: np.ndarray - 目标值，形状为 (N, forecast_horizon)
        """
        self.features = torch.FloatTensor(features)
        self.targets = torch.FloatTensor(targets)

    def __len__(self) -> int:
        """返回数据集大小"""
        return len(self.features)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        """返回一个数据样本"""
        return self.features[idx], self.targets[idx]


class SequentialDataLoader:
    """
    序列数据加载器，用于生成批次数据
    """

    def __init__(self, dataset: LoadForecastingDataset, batch_size: int, shuffle: bool = True):
        """
        初始化数据加载器

        参数:
        dataset: LoadForecastingDataset - 数据集实例
        batch_size: int - 批次大小
        shuffle: bool - 是否打乱数据
        """
        self.dataset = dataset
        self.batch_size = batch_size
        self.shuffle = shuffle
        self.num_samples = len(dataset)
        self.indices = np.arange(self.num_samples)

    def __iter__(self):
        """返回数据迭代器"""
        if self.shuffle:
            np.random.shuffle(self.indices)

        for start_idx in range(0, self.num_samples, self.batch_size):
            end_idx = min(start_idx + self.batch_size, self.num_samples)
            batch_indices = self.indices[start_idx:end_idx]

            # 获取批次数据
            features = torch.stack([self.dataset[i][0] for i in batch_indices])
            targets = torch.stack([self.dataset[i][1] for i in batch_indices])

            yield features, targets

    def __len__(self) -> int:
        """返回批次数量"""
        return (self.num_samples + self.batch_size - 1) // self.batch_size