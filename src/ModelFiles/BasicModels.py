import pickle
import os

import torch
import random
import numpy as np
from NSWData.NSWDataLoader import NSWDataLoader
from ModelFiles.ModelConfigs import Config, DeepLearningConfig
from typing import Callable
import pandas as pd

class BaseModel:
    def __init__(self, config: Config, func: Callable[[pd.DataFrame, str, list[int], list[int],list[tuple[str,int]]], pd.DataFrame] | None = None, specific_output_dir: str | None = None):
        self.config: Config = config
        self.specific_output_dir = specific_output_dir
        self.nsw_data_loader = NSWDataLoader()
        self.train, self.validation, self.test, self.train_scaled, self.val_scaled, self.test_scaled, self.scaler = self.nsw_data_loader.load_data()
        training_data = self.train_scaled if self.config.scale else self.train
        if self.config.training_data_size is not None:
            training_data = training_data.iloc[-1*self.config.training_data_size:]
        validation_data = self.val_scaled if self.config.scale else self.validation
        test_data = self.test_scaled if self.config.scale else self.test
        full_data = pd.concat([training_data, validation_data, test_data], axis=0)
        full_data = func(full_data, config.target_col, config.target_lags, config.target_mas, config.feature_lag_cols) if func else full_data
        n_dropped = len(pd.concat([training_data, validation_data, test_data])) - len(full_data)
        self.training_data = full_data.iloc[:len(training_data) - n_dropped]
        self.validation_data = full_data.iloc[len(training_data) - n_dropped : len(training_data) - n_dropped + len(validation_data)]
        self.test_data = full_data.iloc[len(training_data) - n_dropped + len(validation_data):]
        self.val_step_size = min(config.eval_step_size, config.forecast_horizon)
        if self.config.seed is not None:
            self.set_seed(self.config.seed)
            print(f"Set random seed to {self.config.seed}")

    def set_seed(self, seed: int = 42, deterministic: bool = True):
        random.seed(seed)
        np.random.seed(seed)
        torch.manual_seed(seed)

        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)

        if deterministic:
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False

    def _get_data(self, flag):
            data_set, data_loader = self.nsw_data_loader.data_provider(self.training_data, self.validation_data, self.test_data, self.config, flag)
            return data_set, data_loader
            
    def train_model(self):
        raise NotImplementedError
    
    def evaluate_model(self):
        raise NotImplementedError
    
    def _generate_output_path(self, folder_name):
        if self.specific_output_dir:
            output_directory = os.path.join(self.specific_output_dir, folder_name)
        else:
            output_directory = os.path.join(NSWDataLoader.output_dir, folder_name)
        os.makedirs(output_directory, exist_ok=True)
        return output_directory
    
    def torch_save_checkpoints(self, model, folder_name, checkpoint_file_name):
        model_dir = self._generate_output_path(folder_name)
        model_path = os.path.join(model_dir, checkpoint_file_name)
        state_dict = model.state_dict() if hasattr(model, 'state_dict') else model
        torch.save(state_dict, model_path)
        print(f"Saved {checkpoint_file_name} to {model_path}")

    def torch_load_checkpoints(self, folder_name, checkpoint_file_name):
        model_dir = self._generate_output_path(folder_name)
        model_path = os.path.join(model_dir, checkpoint_file_name)
        self.model.load_state_dict(torch.load(model_path))
        print(f"Loaded {checkpoint_file_name} from {model_path}")
        return self.model

    def pickle_save_checkpoints(self, model, folder_name, checkpoint_file_name):
        model_dir = self._generate_output_path(folder_name)
        model_path = os.path.join(model_dir, checkpoint_file_name)
        with open(model_path, 'wb') as f:
            pickle.dump(model, f)
        print(f"Saved {checkpoint_file_name} to {model_path}")

    def pickle_load_checkpoints(self, folder_name, checkpoint_file_name):
        model_dir = self._generate_output_path(folder_name)
        model_path = os.path.join(model_dir, checkpoint_file_name)
        with open(model_path, 'rb') as f:
            model = pickle.load(f)
        print(f"Loaded {checkpoint_file_name} from {model_path}")
        return model

    def save_df(self, df: pd.DataFrame, folder_name: str, file_name: str):
        results_path = self._generate_output_path(folder_name)
        file_path = os.path.join(results_path, f"{file_name}.csv")
        file_exists = os.path.isfile(file_path)
        df.to_csv(file_path,mode='a' if file_exists else 'w', header=not file_exists, index=False)
        print(f"Saved {file_name}.csv to {file_path}")

    def _debug_batch_timing(self, loop_name, exog_series: pd.DataFrame | None, actuals_series: pd.Series):
        print("="*50)
        print(f"{loop_name} Loop Debug Info:")
        print("="*50)
        y_times = np.array(actuals_series.index, dtype='datetime64[us]')
        step = np.timedelta64(30, 'm')
        val_step_size = min(self.val_step_size, actuals_series.shape[0]) # in case eval_step_size is greater than number of time steps in batch
        y_within_batch_diff = int((y_times[-1]-y_times[0])/step) + 1
        print("="*20 + f"ACTUALS_SERIES SHAPE: {actuals_series.shape}" + "="*20 )
        print(f"\tactuals_series name: {actuals_series.name}")
        print(f"\tFirst datetime in target vector: {np.array(actuals_series.index[0], '<M8[us]')}\n\tLast datetime in target vector: {np.array(actuals_series.index[-1], '<M8[us]')}\n"
            f"\t\tTotal steps within target vector: {y_within_batch_diff}\tConfig Horizon: {self.config.forecast_horizon}\n"
            f"\t\tVal Step Size: {val_step_size}\t\t\tConfig Eval Step Size: {self.config.eval_step_size}\n"
            f"\t\tEvaluation Step Size: {val_step_size} (should be steps from last debug log to this one.\n"
            f"\tNOTE: Dates should be consecutive and match the val_step_size where val_step_size <= horizon.")
        if exog_series is not None:
            x_times = np.array(exog_series.index, dtype='datetime64[us]')
            x_within_batch_diff = int((x_times[-1]-x_times[0])/step) + 1
            print("="*20 + f"EXOG_SERIES SHAPE: {exog_series.shape}" + "="*20)
            print(f"\tExogenous features: {exog_series.columns.tolist()}")
            print(f"\tFirst datetime in exogenous features: {np.array(exog_series.index[0], '<M8[us]')}\n\tLast datetime in exogenous features: {np.array(exog_series.index[-1], '<M8[us]')}\n"
                f"\t\tTotal steps within exogenous features: {x_within_batch_diff}\tConfig Horizon: {self.config.forecast_horizon}\n"
                f"\t\tEvaluation Step Size: {val_step_size} (should be steps from last debug log to this one)\n"
                f"\tNOTE: Dates should be consecutive and match the horizon.")
        user_input = input("Press Enter to continue to next iteration or enter 'q' to skip this: ")
        if user_input.lower() == 'q':
            return False
        return True

class DeepLearningModel(BaseModel):
    def __init__(self, config: DeepLearningConfig, func: Callable[[pd.DataFrame, str, list[int], list[int], list[tuple[str, int]]], pd.DataFrame] | None = None, specific_output_dir: str | None = None):
        super().__init__(config, func, specific_output_dir)
        self.config: DeepLearningConfig = config
        self.device = self._acquire_device()
        self.training_data = self.training_data.dropna().reset_index()
        self.validation_data = self.validation_data.dropna().reset_index()
        self.test_data = self.test_data.dropna().reset_index()
        
    def _acquire_device(self):
        # taken from official repository:
        if self.config.use_gpu:
            device = torch.device('cuda:{}'.format(self.config.gpu))
            print('Use GPU: cuda:{}'.format(self.config.gpu))
        else:
            device = torch.device('cpu')
            print('Use CPU')
        return device
    
    def _debug_batch_timing(self, loop_name, x_batch_time, y_batch_time):
        print("="*50)
        print(f"{loop_name} Loop Debug Info:")
        print("="*50)
        x_times = np.array(x_batch_time, dtype='datetime64[us]')
        y_times = np.array(y_batch_time, dtype='datetime64[us]')
        step = np.timedelta64(30, 'm')
        val_step_size = min(self.val_step_size, y_batch_time.shape[1]) # in case eval_step_size is greater than number of time steps in batch
        y_within_batch_diff = int((y_times[0, -1] - y_times[0, 0]) / step) + 1
        y_across_batch_diff = ((int((y_times[-1, 0] - y_times[0, 0]) / step)) / val_step_size) + 1
        x_within_batch_diff = int((x_times[0, -1] - x_times[0, 0]) / step) + 1
        x_across_batch_diff = ((int((x_times[-1, 0] - x_times[0, 0]) / step)) / val_step_size) + 1
        print("="*20 + f"Y_BATCH_TIME SHAPE: {y_batch_time.shape}" + "="*20)
        print(f"\tFirst datetime in first batch: {np.array(y_batch_time[0][0], '<M8[us]')}\n\tLast datetime in first batch: {np.array(y_batch_time[0][-1], '<M8[us]')}\n"
              f"\tFirst datetime in last batch: {np.array(y_batch_time[-1][0], '<M8[us]')}\n\tLast datetime in last batch: {np.array(y_batch_time[-1][-1], '<M8[us]')}\n"
            f"\t\tTotal steps within a batch: {y_within_batch_diff}\t\t\tConfig Horizon: {self.config.forecast_horizon}\n"
            f"\t\tTotal steps across batches: {y_across_batch_diff:.0f}\t\tConfig Batch Size: {self.config.batch_size}\n"
            f"\t\tEvaluation Step Size: {val_step_size} x {self.config.batch_size} = {val_step_size * self.config.batch_size:.0f} (should be steps from last debug log to this one)\n"
            f"\tNOTE: If 'TOTAL STEPS ACROSS BATCHES' do not match the expected numbers, this is ok for training loop as the dataloader is set to 'shuffle=True'.")
        print("="*20 + f"X_BATCH_TIME SHAPE: {x_batch_time.shape}" + "="*20)
        print(f"\tFirst datetime in first batch: {np.array(x_batch_time[0][0], '<M8[us]')}\n\tLast datetime in first batch: {np.array(x_batch_time[0][-1], '<M8[us]')}\n"
              f"\tFirst datetime in last batch: {np.array(x_batch_time[-1][0], '<M8[us]')}\n\tLast datetime in last batch: {np.array(x_batch_time[-1][-1], '<M8[us]')}\n"
            f"\t\tTotal steps within a batch: {x_within_batch_diff}\t\t\tConfig Lookback: {self.config.lookback_window}\n"
            f"\t\tTotal steps across batches: {x_across_batch_diff:.0f}\t\tConfig Batch Size: {self.config.batch_size}\n"
            f"\t\tEvaluation Step Size: {val_step_size} x {self.config.batch_size} = {val_step_size * self.config.batch_size:.0f} or {val_step_size * self.config.batch_size/48:.0f} days (should be steps from last debug log to this one)\n"
            f"\tNOTE: If 'TOTAL STEPS ACROSS BATCHES' do not match the expected numbers, this is ok for training loop as the dataloader is set to 'shuffle=True'.")
        user_input = input("Press Enter to continue to next iteration or enter 'q' to skip this: ")
        if user_input.lower() == 'q':
            return False
        return True

    def _compute_inverse_scaling(self, shape, pred, true):
        feature_names = self.nsw_data_loader.scaler.feature_names_in_.tolist()
        n_features = shape[-1]
        total = shape[0] * shape[1]

        pred_arr = pred if isinstance(pred, np.ndarray) else np.array(pred)
        true_arr = true if isinstance(true, np.ndarray) else np.array(true)

        if n_features == 1:
            # Univariate / MS: only the target column
            pos = feature_names.index(self.config.target_col)
            means = self.nsw_data_loader.scaler.mean_[pos]   # scalar
            stds  = self.nsw_data_loader.scaler.var_[pos] ** 0.5
        else:
            # Multivariate M: one mean/std per output channel, in feature_cols order
            positions = [feature_names.index(col) for col in self.config.all_feature_cols+[self.config.target_col]]
            means = self.nsw_data_loader.scaler.mean_[positions]   # shape: (n_features,)
            stds  = self.nsw_data_loader.scaler.var_[positions] ** 0.5

        pred_inverse = (pred_arr.reshape(total, n_features) * stds + means).reshape(shape)
        true_inverse = (true_arr.reshape(total, n_features) * stds + means).reshape(shape)
        return pred_inverse, true_inverse