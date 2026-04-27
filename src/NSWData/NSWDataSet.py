from torch.utils.data import Dataset
import pandas as pd
import numpy as np
from ModelFiles.ModelConfigs import Config, DeepLearningConfig, LSTMConfig, TransformersConfig
from ModelFiles.PatchTST_supervised.utils.timefeatures import time_features
from torch.utils.data import Dataset
import pandas as pd

class BaseDeepLearningNSWDataSet(Dataset):
    """
    Base dataset class for deep learning models on NSW data. 
    This class handles loading and preprocessing the data, as well as providing a consistent interface for getting items and lengths. 
    It is designed to be subclassed by specific dataset classes for different model types (e.g. LSTMDataSet, TransformersDataSet) that 
    may have different logic for how to slice the data and what features to include.
    
    Note that the data's index will be reset and date column will be brought out as a separate column.
    """
    def __init__(self, config:DeepLearningConfig, train_df, val_df, test_df, flag='train'):
        self.config = config
        self.train_df = train_df
        self.val_df = val_df
        self.test_df = test_df       

        assert flag in ['train', 'test', 'val']
        type_map = {'train': 0, 'val': 1, 'test': 2}
        self.set_type = type_map[flag]

    def __read_data__(self):
        """Shared border/slicing logic for all subclasses."""
        df_raw = pd.concat([self.train_df, self.val_df, self.test_df], axis=0).reset_index() # reset index to bring out date column for time encoding for TimeXer
        self.df_raw = df_raw[[self.config.date_col] + self.config.all_feature_cols + [self.config.target_col]]
        num_train = len(self.train_df)
        num_test = len(self.test_df)
        num_vali = len(self.val_df)
        
        border1s = [0, num_train - self.config.lookback_window, len(self.df_raw) - num_test - self.config.lookback_window]
        border2s = [num_train, num_train + num_vali, len(self.df_raw)]
        self.border1 = border1s[self.set_type]
        self.border2 = border2s[self.set_type]
        self.get_item_data_x, self.get_item_data_y, self.get_item_time_stamp, self.get_item_data_stamp = self._set_data()

    def _set_data(self) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        raise NotImplementedError("This method should be implemented by subclasses if they want to use time encoding features.")

    def __getitem__(self, index):
        s_begin = index
        s_end = s_begin + self.config.lookback_window
        r_begin = s_end
        r_end = r_begin + self.config.forecast_horizon

        seq_x = self.get_item_data_x[s_begin:s_end]
        seq_y = self.get_item_data_y[r_begin:r_end]
        if self.get_item_data_stamp is not None:
            seq_x_mark = self.get_item_data_stamp[s_begin:s_end]
            seq_y_mark = self.get_item_data_stamp[r_begin:r_end]
        else:
            seq_x_mark = np.zeros((len(seq_x), 1)) # dummy time encoding features if not using time encoding, to maintain consistent return type
            seq_y_mark = np.zeros((len(seq_y), 1)) # dummy time encoding features if not using time encoding, to maintain consistent return type
        seq_x_time = self.get_item_time_stamp[s_begin:s_end]
        seq_y_time = self.get_item_time_stamp[r_begin:r_end]

        return seq_x.copy(), seq_y.copy(), seq_x_mark.copy() if seq_x_mark is not None else None, seq_y_mark.copy() if seq_y_mark is not None else None, seq_x_time.copy(), seq_y_time.copy()

    def __len__(self):
        return len(self.get_item_data_x) - self.config.lookback_window - self.config.forecast_horizon + 1

    def shape(self):
        return self.get_item_data_x.shape, self.get_item_data_y.shape

class TransformersDataSet(BaseDeepLearningNSWDataSet):
    """For PatchTSTConfig and LSTMConfig that require lookback windows"""
    
    def __init__(self, config:TransformersConfig, train_df, val_df, test_df, flag='train'):
        super().__init__(config, train_df, val_df, test_df, flag)
        self.config: TransformersConfig = config
        self.timeenc = 0 if config.time_encoding != 'timeF' else 1
        
        assert flag in ['train', 'test', 'val']
        type_map = {'train': 0, 'val': 1, 'test': 2}
        self.set_type = type_map[flag]
        self.__read_data__()

    def __read_data__(self):
        super().__read_data__()

    def _set_data(self):
        df_stamp = self.df_raw[[self.config.date_col]][self.border1:self.border2]
        df_stamp[self.config.date_col] = pd.to_datetime(df_stamp[self.config.date_col])
        if self.timeenc == 0:
            df_stamp['month'] = df_stamp[self.config.date_col].apply(lambda row: row.month)
            df_stamp['day'] = df_stamp[self.config.date_col].apply(lambda row: row.day)
            df_stamp['weekday'] = df_stamp[self.config.date_col].apply(lambda row: row.weekday())
            df_stamp['hour'] = df_stamp[self.config.date_col].apply(lambda row: row.hour)
            data_stamp = df_stamp.drop([self.config.date_col], axis=1).values
        elif self.timeenc == 1:
            data_stamp = time_features(pd.to_datetime(df_stamp[self.config.date_col].values), freq='30min')
            data_stamp = data_stamp.transpose(1, 0)
 
        if self.config.variate == 'M' or self.config.variate == 'MS':
            df_data = self.df_raw
        else: # for self.config.variate == 'S'
            df_data = self.df_raw[[self.config.date_col,self.config.target_col]]

        # since transformers can output multivariate forecasts, x and y dfs have same columns.
        # we create separate reference dfs for consistency.
        self.reference_data_x_df = df_data.iloc[self.border1:self.border2]
        self.reference_data_y_df = df_data.iloc[self.border1:self.border2]
            
        get_item_data_x = self.reference_data_x_df.iloc[:, 1:].values.astype(np.float32) # exclude date_col in get_item
        get_item_data_y = self.reference_data_y_df.iloc[:, 1:].values.astype(np.float32) # exclude date_col in get_item
        get_item_time_stamp = df_stamp[self.config.date_col].values.astype(np.int64)
        get_item_data_stamp = data_stamp
        return get_item_data_x, get_item_data_y, get_item_time_stamp, get_item_data_stamp

class LSTMDataSet(BaseDeepLearningNSWDataSet):
    """For PatchTSTConfig and LSTMConfig that require lookback windows"""
    
    def __init__(self, config:LSTMConfig, train_df, val_df, test_df, flag='train'):
        super().__init__(config, train_df, val_df, test_df, flag)
        self.config: LSTMConfig = config
        
        assert flag in ['train', 'test', 'val']
        type_map = {'train': 0, 'val': 1, 'test': 2}
        self.set_type = type_map[flag]
        self.__read_data__()

    def __read_data__(self):
        super().__read_data__()

    def _set_data(self):
        df_stamp = self.df_raw[[self.config.date_col]][self.border1:self.border2]
        df_stamp[self.config.date_col] = pd.to_datetime(df_stamp[self.config.date_col])

        self.reference_data_x_df = self.df_raw.iloc[self.border1:self.border2]
        self.reference_data_y_df = self.df_raw.iloc[self.border1:self.border2][[self.config.date_col,self.config.target_col]] # only predict target column for LSTM, which is the first column after date_col in df_raw. This is because LSTMs are univariate in our implementation, while PatchTST can be multivariate.
        
        get_item_data_x = self.reference_data_x_df.drop(columns=self.config.date_col).values.astype(np.float32) # exclude date_col in get_item
        get_item_data_y = self.reference_data_y_df.drop(columns=self.config.date_col).values.astype(np.float32) # exclude date_col in get_item
        get_item_time_stamp = df_stamp[self.config.date_col].values.astype(np.int64)
        get_item_data_stamp = None # LSTMs do not use time encoding features, but we return None for consistency of the return type across datasets.
        return get_item_data_x, get_item_data_y, get_item_time_stamp, get_item_data_stamp
