import os


class Config:
    # 项目根目录
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

    # 数据相关配置
    DATA_PATH = {
        'TEMPERATURE': os.path.join(ROOT_DIR, 'data', 'NSW', 'temperature_nsw.csv'),
        'DEMAND': os.path.join(ROOT_DIR, 'data', 'NSW', 'totaldemand_nsw.csv')
    }

    # 时间窗口配置
    WINDOW_SIZE = 1440  # 24小时 * 60分钟
    FORECAST_HORIZON = 2880  # 48小时 * 60分钟
    TRAIN_TEST_SPLIT = 0.8

    # 模型相关配置
    MODEL = {
        'type': 'transformer',  # 可选: 'lstm', 'transformer', 'tcn'
        'hidden_size': 128,
        'num_layers': 4,
        'dropout': 0.1,
        'num_heads': 8,  # 用于transformer
        'forward_expansion': 4  # 用于transformer的FFN
    }

    # 训练相关配置
    TRAINING = {
        'batch_size': 32,
        'epochs': 100,
        'learning_rate': 0.001,
        'early_stopping_patience': 10,
        'scheduler_patience': 5,
        'scheduler_factor': 0.5
    }

    # 评估指标配置
    METRICS = ['mae', 'mse', 'rmse', 'mape']

    # 系统配置
    RANDOM_SEED = 42
    DEVICE = 'cuda'  # 或 'cpu'
    NUM_WORKERS = 4

    # 文件保存路径
    SAVE_PATH = {
        'models': os.path.join(ROOT_DIR, 'saved_models'),
        'logs': os.path.join(ROOT_DIR, 'logs'),
        'predictions': os.path.join(ROOT_DIR, 'predictions'),
        'figures': os.path.join(ROOT_DIR, 'figures')
    }

    def __init__(self):
        """初始化时创建必要的目录"""
        for path in self.SAVE_PATH.values():
            os.makedirs(path, exist_ok=True)

        # 确保数据目录存在
        os.makedirs(os.path.dirname(self.DATA_PATH['TEMPERATURE']), exist_ok=True)
        os.makedirs(os.path.dirname(self.DATA_PATH['DEMAND']), exist_ok=True)