import os
import random
import numpy as np
import torch
import matplotlib.pyplot as plt
from datetime import datetime
import logging
from typing import Dict, List, Tuple, Union


def setup_logging(save_path: str) -> None:
    """
    设置日志记录
    """
    os.makedirs(save_path, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(save_path, f'training_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')),
            logging.StreamHandler()
        ]
    )


def set_random_seed(seed: int) -> None:
    """
    设置随机种子以确保结果可复现
    """
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False


def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """
    计算各种评估指标
    """
    metrics = {}
    metrics['mae'] = np.mean(np.abs(y_true - y_pred))
    metrics['mse'] = np.mean((y_true - y_pred) ** 2)
    metrics['rmse'] = np.sqrt(metrics['mse'])
    # 避免除零错误
    mask = y_true != 0
    metrics['mape'] = np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100
    return metrics


def plot_predictions(
        y_true: np.ndarray,
        y_pred: np.ndarray,
        timestamps: List[datetime],
        save_path: str,
        title: str = "Load Forecasting Results"
) -> None:
    """
    绘制预测结果
    """
    plt.figure(figsize=(15, 6))
    plt.plot(timestamps, y_true, label='Actual', alpha=0.7)
    plt.plot(timestamps, y_pred, label='Predicted', alpha=0.7)
    plt.title(title)
    plt.xlabel('Time')
    plt.ylabel('Load (MW)')
    plt.legend()
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()

    # 保存图片
    os.makedirs(save_path, exist_ok=True)
    plt.savefig(os.path.join(save_path, f'prediction_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'))
    plt.close()


def save_model(
        model: torch.nn.Module,
        optimizer: torch.optim.Optimizer,
        epoch: int,
        loss: float,
        save_path: str,
        model_name: str
) -> None:
    """
    保存模型检查点
    """
    os.makedirs(save_path, exist_ok=True)
    checkpoint = {
        'epoch': epoch,
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
        'loss': loss
    }
    torch.save(checkpoint, os.path.join(save_path, f'{model_name}_epoch_{epoch}.pth'))


def load_model(
        model: torch.nn.Module,
        optimizer: torch.optim.Optimizer,
        model_path: str
) -> Tuple[torch.nn.Module, torch.optim.Optimizer, int, float]:
    """
    加载模型检查点
    """
    checkpoint = torch.load(model_path)
    model.load_state_dict(checkpoint['model_state_dict'])
    optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
    epoch = checkpoint['epoch']
    loss = checkpoint['loss']
    return model, optimizer, epoch, loss


class EarlyStopping:
    """
    早停机制
    """

    def __init__(self, patience: int = 7, min_delta: float = 0):
        self.patience = patience
        self.min_delta = min_delta
        self.counter = 0
        self.best_loss = None
        self.early_stop = False

    def __call__(self, val_loss: float) -> bool:
        if self.best_loss is None:
            self.best_loss = val_loss
        elif val_loss > self.best_loss - self.min_delta:
            self.counter += 1
            if self.counter >= self.patience:
                self.early_stop = True
        else:
            self.best_loss = val_loss
            self.counter = 0
        return self.early_stop