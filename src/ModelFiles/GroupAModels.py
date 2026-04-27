# This module contains the implementation of the Gradient Boosting and LSTM models for time series forecasting, 
# as well as a unified wrapper for transformer-based models like PatchTST. 
# Each model class inherits from a base model class (BasicModels.py) and implements methods 
# for training, loading, and evaluating the model. 

# The evaluation method computes metrics such as RMSE and MAE, and can save detailed results to CSV files. 
# The training method includes support for early stopping and learning rate scheduling (where applicable).

# Note that the PatchTST codes are adapted from the original implementation by the authors.
# See README.md for references to the original code and papers.
# The adapted model files for PatchTST are located in src/ModelFiles/PatchTST_supervised/.

import pandas as pd, numpy as np,torch, torch.nn as nn
from ModelFiles.PatchTST_supervised.models import PatchTST, TimeXer
from ModelFiles.PatchTST_supervised.models import iTransformer
from ModelFiles.PatchTST_supervised.utils.tools import EarlyStopping, adjust_learning_rate
from ModelFiles.PatchTST_supervised.utils.metrics import metric
from ModelFiles.LSTM.models import AttentionBiLSTMForecaster, MultiHeadAttentionBiLSTMForecaster, SequenceForecaster
from ModelFiles.ModelConfigs import GradientBoostingConfig, TransformersConfig, SARIMAXConfig, LSTMConfig
from ModelFiles.ModelEnums import *
from ModelFiles.BasicModels import BaseModel, DeepLearningModel
from statsmodels.tsa.statespace.sarimax import SARIMAX, SARIMAXResultsWrapper
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from time import time
from copy import deepcopy
from torch import optim
from torch.optim import lr_scheduler
from typing import Callable


class GradientBoostingModel(BaseModel):
    def __init__(self, config: GradientBoostingConfig, func: Callable[[pd.DataFrame, str, list[int], list[int], list[tuple[str, int]]], pd.DataFrame] | None = None, specific_output_dir: str | None = None):
        super().__init__(config, func, specific_output_dir)
        self.config: GradientBoostingConfig = config
        if config.eval_step_size > config.forecast_horizon:
            print(f"Warning: eval_step_size {config.eval_step_size} is greater than forecast_horizon {config.forecast_horizon}. Setting eval_step_size to forecast_horizon.")
        self.val_step_size = min(config.eval_step_size, config.forecast_horizon)
        self.model = GradientBoostingRegressor(
            n_estimators=self.config.n_estimators,
            learning_rate=self.config.learning_rate,
            max_depth=self.config.max_depth,
            random_state=self.config.seed,
            verbose=self.config.verbose
        )

    def train_model(self):
        start = time()
        x_train = self.training_data[self.config.all_feature_cols].copy()
        y_train = self.training_data[self.config.target_col].copy()
        self.model.fit(x_train, y_train)
        _, _, rmse, mae = self.evaluate_model(None, test_mode=0)
        end = time()
        print(f"Training completed in {end - start:.2f} seconds.")

        progress_log_df = pd.DataFrame({
            "task_id": [self.config.task_id],
            "model_type": ["GradientBoosting"],
            "rmse": [rmse],
            "mae": [mae],
            "time_taken_seconds": [end - start],
            **{k: [v] for k, v in self.config.config_params_to_results.items()}
        })
        if self.config.save_model:
            self.pickle_save_checkpoints(self.model, "gradient_boosting_models", f"{self.config.task_id}_model.pkl")
        if self.config.save_training_log:
            self.save_df(progress_log_df, "gradient_boosting_results", f"{self.config.task_id}_fitting_log")
        return self.model

    def load_model(self, file_name: str):
        self.model = self.pickle_load_checkpoints("gradient_boosting_models", file_name)
        return self.model

    def evaluate_model(self, model_fit: GradientBoostingRegressor | str | None, test_mode=0):
        if model_fit is None:
            if self.model is None:
                raise ValueError("No model provided for testing. Please provide a fitted GradientBoostingRegressor object or a model file name, or ensure that train_model() has been called to train and set the best_model.")
            else:
                _model_fit = self.model
        elif isinstance(model_fit, str):
            _model_fit = self.load_model(model_fit)
            if _model_fit is None:
                raise ValueError("Model not found in gradient_boosting_models directory. Please check the file name and try again or use train_model() to train a new model.")
        elif isinstance(model_fit, GradientBoostingRegressor):
            _model_fit = model_fit
        else:
            raise ValueError("model_fit must be either None, a file name string, or a GradientBoostingRegressor object.")
        
        if test_mode:
            test_df = self.test_data.copy()
        else:
            test_df = self.validation_data.copy()

        val_step_size = min(self.val_step_size, len(test_df) - self.config.forecast_horizon)
        origins = range(0, len(test_df) - self.config.forecast_horizon, val_step_size)
        all_preds = []
        all_actuals = []
        all_timestamps = []   
        all_origins = []  
        full_data = pd.concat([self.training_data, self.validation_data, self.test_data], axis=0)
        debug = self.config.debug
        for i in origins:
            freq = pd.Timedelta(minutes=30)
            forecast_index = test_df.index[i:i + self.config.forecast_horizon]
            if debug:
                print("\n="*50 + f"{'Test' if test_mode else 'Validation'} Loop Debug Info:" + "="*50)
                print(f"Evaluating origin {i} / {len(test_df) - self.config.forecast_horizon} or ({i // val_step_size} / {(len(test_df) - self.config.forecast_horizon) // val_step_size})")
                print(f"\tForecast index from {forecast_index[0]} to {forecast_index[-1]} with freq {freq}")
                print(f"\tThis is {forecast_index.shape[0]} steps, which should be equal to the config forecast horizon of {self.config.forecast_horizon}.")
                print(f"\tVal Step Size: {val_step_size} (should be steps from last debug log to this one, and val_step_size should be <= forecast_horizon)")
                user_input = input("Press Enter to continue to next iteration or enter 'q' to skip this: ")
                if user_input.lower() == 'q':
                    debug = False
            history_end = forecast_index[0] - freq
            history = list(full_data.loc[:history_end, self.config.target_col].values)
            preds = []
            for ts in forecast_index:
                row = pd.DataFrame([
                    list(test_df.loc[ts, self.config.feature_cols])
                    + [history[-i] for i in self.config.target_lags]
                    + [full_data.loc[ts - i * freq, feature] for feature, i in self.config.feature_lag_cols]
                    + [np.mean(history[-i:]) for i in self.config.target_mas]
                ], columns=self.config.all_feature_cols)
                forecast = _model_fit.predict(row)[0]
                history.append(forecast)
                preds.append(forecast)

            y_actual = test_df.iloc[i:i + self.config.forecast_horizon][self.config.target_col].copy()
            y_pred = pd.Series(preds, index=y_actual.index)
            pred = y_pred.copy().values
            actual = y_actual.copy().values
            if self.config.scale:
                pos = self.nsw_data_loader.scaler.feature_names_in_.tolist().index(self.config.target_col)
                mean = self.nsw_data_loader.scaler.mean_[pos]
                var = self.nsw_data_loader.scaler.var_[pos]
                pred = pred*var**0.5 + mean
                actual = actual*var**0.5 + mean
            if self.config.used_log_target:
                pred = np.exp(pred)
                actual = np.exp(actual)
            all_preds.extend(pred)
            all_actuals.extend(actual)
            all_timestamps.extend(y_pred.index.to_list())
            all_origins.extend([i // val_step_size] * self.config.forecast_horizon)
            if (i // val_step_size) % 10 == 0:
                print(f"Evaluating origin {i} / {len(test_df) - self.config.forecast_horizon} or ({i // val_step_size} / {(len(test_df) - self.config.forecast_horizon) // val_step_size})")
                print(f"\tRMSE so far: {np.sqrt(mean_squared_error(all_actuals, all_preds)):.4f}")

        rmse = np.sqrt(mean_squared_error(all_actuals, all_preds))
        mae = mean_absolute_error(all_actuals, all_preds)    # use MAE
        print(f"{'Test' if test_mode else 'Validation'} Results - RMSE: {rmse:.2f} MW | MAE: {mae:.2f} MW")
        results_df = pd.DataFrame({
            'origins': all_origins,
            'horizon': [i % self.config.forecast_horizon for i in range(len(all_actuals))],
            'timestamp': all_timestamps,
            'y_actual': all_actuals,
            'y_pred': all_preds
        })
        metrics_df = pd.DataFrame({
            'rmse': [rmse],
            'mae': [mae],
            'total_epochs_run': [None],
            'best_epoch': [None],
            'early_stop_epoch': [None],
            **{k: [v] for k, v in self.config.config_params_to_results.items()}
        })
        if test_mode:
            folder_name = "gradient_boosting_results"
            if self.config.save_test_results:
                self.save_df(results_df, folder_name, f"{self.config.task_id}_test_results")
            self.save_df(metrics_df, folder_name, f"{self.config.task_id}_test_metrics")
        return all_actuals, all_preds, rmse, mae


class LSTMModel(DeepLearningModel):
    def __init__(self, config: LSTMConfig, func: Callable[[pd.DataFrame, str, list[int], list[int], list[tuple[str, int]]], pd.DataFrame] | None = None, specific_output_dir: str | None = None):
        super().__init__(config, func, specific_output_dir)
        self.config: LSTMConfig = config
        self.model = self._build_model(config, input_size=len(self.config.all_feature_cols)+1)
        self.total_epochs_run: int | None = None
        self.best_epoch: int | None = None
        self.early_stop_epoch: int | None = None

    def _build_model(self, config: LSTMConfig, input_size):
        model_type = config.model_type.value

        if model_type == LSTMModelType.LSTM.value:
            model = SequenceForecaster(
                input_size=input_size,
                hidden_size=config.hidden_size,
                num_layers=config.num_layers,
                horizon=config.forecast_horizon,
                forecast_last_step_only=config.forecast_last_step_only,
                dropout=config.dropout,
                bidirectional=False,
                use_mlp_head=config.use_mlp_head,
                mlp_hidden_size=config.mlp_hidden_size,
            )

        elif model_type == LSTMModelType.BILSTM.value:
            model = SequenceForecaster(
                input_size=input_size,
                hidden_size=config.hidden_size,
                num_layers=config.num_layers,
                horizon=config.forecast_horizon,
                forecast_last_step_only=config.forecast_last_step_only,
                dropout=config.dropout,
                bidirectional=True,
                use_mlp_head=config.use_mlp_head,
                mlp_hidden_size=config.mlp_hidden_size,
            )

        elif model_type == LSTMModelType.MULTIHEAD_ATTENTION_LSTM.value:
            model = AttentionBiLSTMForecaster(
                input_size=input_size,
                hidden_size=config.hidden_size,
                num_layers=config.num_layers,
                horizon=config.forecast_horizon,
                forecast_last_step_only=config.forecast_last_step_only,
                dropout=config.dropout,
                bidirectional=True,
                use_mlp_head=config.use_mlp_head,
                mlp_hidden_size=config.mlp_hidden_size,
            )

        elif model_type == LSTMModelType.MULTIHEAD_ATTENTION_BILSTM.value:
            model = MultiHeadAttentionBiLSTMForecaster(
                input_size=input_size,
                hidden_size=config.hidden_size,
                num_layers=config.num_layers,
                horizon=config.forecast_horizon,
                forecast_last_step_only=config.forecast_last_step_only,
                dropout=config.dropout,
                bidirectional=True,
                use_mlp_head=config.use_mlp_head,
                mlp_hidden_size=config.mlp_hidden_size,
                num_attention_heads=config.num_attention_heads,
            )

        else:
            raise ValueError(f"Unknown model_type: {model_type}")

        return model.to(torch.device("cuda" if torch.cuda.is_available() else "cpu"))

    def _select_criterion(self):
        criterion = nn.MSELoss()
        return criterion

    def _select_optimizer(self):
        # Optimizer
        optimizer_name = self.config.optimizer.lower()
        lr = self.config.learning_rate
        weight_decay = self.config.weight_decay

        if optimizer_name == "adam":
            optimizer = torch.optim.Adam(self.model.parameters(), lr=lr, weight_decay=weight_decay)
        elif optimizer_name == "adamw":
            optimizer = torch.optim.AdamW(self.model.parameters(), lr=lr, weight_decay=weight_decay)
        elif optimizer_name == "sgd":
            optimizer = torch.optim.SGD(self.model.parameters(), lr=lr, momentum=0.9, weight_decay=weight_decay)
        else:
            raise ValueError(f"Unsupported optimizer: {optimizer_name}")
        return optimizer

    def _get_scheduler(self, optimizer):
        scheduler = None
        scheduler_name = self.config.scheduler
        if scheduler_name:
            scheduler_name = scheduler_name.lower()
            if scheduler_name == "reduce_on_plateau":
                scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
                    optimizer,
                    mode="min",
                    factor=self.config.scheduler_factor,
                    patience=self.config.scheduler_patience,
                )
            elif scheduler_name == "step":
                scheduler = torch.optim.lr_scheduler.StepLR(
                    optimizer,
                    step_size=self.config.scheduler_step_size,
                    gamma=self.config.scheduler_gamma,
                )
            else:
                raise ValueError(f"Unsupported scheduler: {scheduler_name}")
        return scheduler
    
    def train_model(self):
        dataset, data_loader = self._get_data(flag='train')
        train_losses = []
        val_losses = []
        val_rmse = []
        best_val_loss = float("inf")
        best_epoch = -1
        best_state = None
        epochs_no_improve = 0
        criterion = self._select_criterion()
        optimizer = self._select_optimizer()
        scheduler = self._get_scheduler(optimizer)

        for epoch in range(self.config.training_epochs):
            self.model.train()
            running_train_loss = 0.0
            debug = self.config.debug
            for X_batch, y_batch, _, _, x_batch_time, y_batch_time in data_loader:
                if debug:
                    print(f"Target Shape: {dataset.reference_data_y_df.shape}")
                    print(f"Target Col Name: {dataset.reference_data_y_df.columns.tolist()}")
                    print(f"Feature Shape: {dataset.reference_data_x_df.shape}")
                    print(f"Feature Cols: {dataset.reference_data_x_df.columns.tolist()}")
                    debug = self._debug_batch_timing('Training', x_batch_time, y_batch_time)
                X_batch = X_batch.to(self.device)
                if self.config.forecast_last_step_only:
                    last_step = -1
                    y_batch = y_batch[:, last_step, -1].to(self.device) # need last -1 to reshape from (batch_size, horizon, 1) to (batch_size, horizon)
                else:
                    y_batch = y_batch[:, :, -1].to(self.device) # need last -1 to reshape from (batch_size, horizon, 1) to (batch_size, horizon)
                optimizer.zero_grad()
                y_pred = self.model(X_batch)
                loss = criterion(y_pred, y_batch)
                loss.backward()
                optimizer.step()

                running_train_loss += loss.item() * X_batch.size(0)

            epoch_train_loss = running_train_loss / len(data_loader.dataset)
            train_losses.append(epoch_train_loss)

            self.model.eval()

            epoch_val = self.evaluate_model(test_mode=0)
            val_losses.append(epoch_val["loss"])
            val_rmse.append(epoch_val["rmse"])
            if scheduler is not None:
                if isinstance(scheduler, torch.optim.lr_scheduler.ReduceLROnPlateau):
                    scheduler.step(epoch_val["loss"])
                else:
                    scheduler.step()

            # Stops the training when the val loss meets a certain condition
            if epoch_val["loss"] < best_val_loss:
                best_val_loss = epoch_val["loss"]
                best_epoch = epoch
                best_state = deepcopy(self.model.state_dict())
                epochs_no_improve = 0
            else:
                epochs_no_improve += 1

            print(
                f"Epoch [{epoch+1}/{self.config.training_epochs}] | "
                f"Train Loss: {epoch_train_loss:.6f} | "
                f"Val Loss: {epoch_val['loss']:.6f} | "
                f"RMSE: {epoch_val['rmse']:.6f} | "
                f"MAE: {epoch_val['mae']:.6f}"
            )

            if epochs_no_improve >= self.config.patience:
                print(f"Early stopping triggered at epoch {epoch+1}")
                break

        self.total_epochs_run = len(train_losses)
        self.best_epoch = best_epoch + 1  # 1-indexed
        self.early_stop_epoch = epoch + 1 if epochs_no_improve >= self.config.patience else None

        if best_state is None:
            best_state = deepcopy(self.model.state_dict())

        if self.config.save_training_log:
            progress_log = {
                "epoch": list(range(1, self.total_epochs_run + 1)),
                "train_loss": train_losses,
                "val_loss": val_losses,
                "val_rmse": val_rmse,
                "best_epoch": [self.best_epoch] * self.total_epochs_run,
                "early_stop_epoch": [self.early_stop_epoch] * self.total_epochs_run,
                "num_parameters": [sum(p.numel() for p in self.model.parameters())] * self.total_epochs_run,
                **{k: [v] * self.total_epochs_run for k, v in self.config.config_params_to_results.items()}
            }
            progress_log_df = pd.DataFrame(progress_log)
            self.save_df(progress_log_df, "LSTM_results", f"{self.config.task_id}_fitting_log")
        if self.config.save_model:
            self.torch_save_checkpoints(best_state, "lstm_models", f"{self.config.task_id}_best_model.pth")

        return {
            "model": self.model,
            "best_state": best_state,
            "best_epoch": best_epoch,
            "best_val_loss": best_val_loss,
            "train_losses": train_losses,
            "val_losses": val_losses,
        }

    def load_model(self, file_name: str):
        self.torch_load_checkpoints("lstm_models", file_name)
        return self.model

    
    def _compute_inverse_scaling(self, shape, pred, true):
            pos = self.nsw_data_loader.scaler.feature_names_in_.tolist().index(self.config.target_col)
            mean = self.nsw_data_loader.scaler.mean_[pos]
            var = self.nsw_data_loader.scaler.var_[pos]
            pred_tile = np.tile(pred, [1, 1, 1])
            pred_inverse = pred_tile.reshape(shape[0] * shape[1], 1)
            pred_inverse = pred_inverse* var**0.5 + mean
            pred_inverse = pred_inverse[:, -1:].reshape(shape)
            true_tiled = np.tile(true, [1, 1, 1])
            true_inverse = true_tiled.reshape(shape[0] * shape[1], 1)
            true_inverse = true_inverse*var**0.5 + mean
            true_inverse = true_inverse[:, -1:].reshape(shape)
            return pred_inverse, true_inverse
    
    def evaluate_model(self, tolerance_pct=10.0, test_mode: int = 0):

        dataset, data_loader = self._get_data(flag='test' if test_mode else 'val')
        self.model.eval()
        y_pred_raw = []
        y_actual_raw = []
        timestamps = []
        batch_nums = []
        horizon_windows = []

        with torch.no_grad():
            debug = self.config.debug
            for i, (X_batch, y_batch, _, _, x_batch_time, y_batch_time) in enumerate(data_loader):
                if debug:
                    print(f"Target Shape: {dataset.reference_data_y_df.drop(columns=dataset.config.date_col).shape}")
                    print(f"Target Col Name: {dataset.reference_data_y_df.drop(columns=dataset.config.date_col).columns.tolist()}")
                    print(f"Feature Shape: {dataset.reference_data_x_df.drop(columns=dataset.config.date_col).shape}")
                    print(f"Feature Cols: {dataset.reference_data_x_df.drop(columns=dataset.config.date_col).columns.tolist()}")
                    debug = self._debug_batch_timing('Test' if test_mode else 'Validation', x_batch_time, y_batch_time)
                X_batch = X_batch.to(self.device)
                if self.config.forecast_last_step_only:
                    last_step = -1
                    # predicting only the last timestep in the forecast horizon
                    y_batch = y_batch[:, last_step, -1] # need last -1 to reshape from (batch_size, horizon, 1) to (batch_size, horizon)
                    y_batch_time = y_batch_time[:, last_step]
                else:
                    y_batch = y_batch[:, :, -1] # need last -1 to reshape from (batch_size, horizon, 1) to (batch_size, horizon)

                y_pred = self.model(X_batch).cpu().numpy()
                y_pred_raw.extend(y_pred)
                y_actual_raw.extend(y_batch.numpy())
                if y_batch.ndim == 2:
                    horizon_window = np.zeros_like(y_batch) + np.arange(y_batch.shape[1])
                else:  # forecast_last_step_only=True → y_batch is (batch_size,)
                    horizon_window = np.zeros(y_batch.shape[0]) + (self.config.forecast_horizon - 1)  # all predictions are for the last step in the horizon

                ts = y_batch_time.detach().numpy()
                current_batch_number = np.zeros(ts.shape)+i
                horizon_windows.extend(horizon_window)
                timestamps.extend(ts)
                batch_nums.extend(current_batch_number)

        y_pred_raw = np.array(y_pred_raw).reshape(-1, 1)
        y_actual_raw = np.array(y_actual_raw).reshape(-1, 1)
        test_loss = mean_squared_error(y_pred_raw, y_actual_raw)
        horizon_windows = np.array(horizon_windows).reshape(-1, 1)
        timestamps = np.array(timestamps, dtype='<M8[us]').reshape(-1, 1)
        batch_nums = np.array(batch_nums).reshape(-1, 1)

        if self.config.scale:
            y_pred_real, y_true_real = self._compute_inverse_scaling(y_pred_raw.shape, y_pred_raw, y_actual_raw)
        else:
            y_pred_real, y_true_real = y_pred_raw, y_actual_raw

        if self.config.used_log_target:
            y_pred_real = np.exp(y_pred_real)
            y_true_real = np.exp(y_true_real)

        y_pred_real = y_pred_real.ravel()
        y_true_real = y_true_real.ravel()
        horizon_windows = horizon_windows.ravel()
        timestamps = timestamps.ravel()
        batch_nums = batch_nums.ravel()

        rmse = np.sqrt(mean_squared_error(y_true_real, y_pred_real))
        mae = mean_absolute_error(y_true_real, y_pred_real)
        r2 = r2_score(y_true_real, y_pred_real)

        mask = np.abs(y_true_real) > 1e-8
        mape = (
            np.mean(np.abs((y_true_real[mask] - y_pred_real[mask]) / y_true_real[mask])) * 100
            if np.any(mask) else np.nan
        )
        if test_mode == 0:
            return {"loss": test_loss, "rmse": rmse, "mae": mae}
        tolerance = tolerance_pct / 100.0
        within_tol_acc = np.mean(
            np.abs(y_pred_real - y_true_real) <= tolerance * np.abs(y_true_real)
        ) * 100

        eval_dict = {
            "batch_number": batch_nums.astype(int),
            "horizon": horizon_windows.astype(int),
            "timestamp": timestamps,
            "y_pred": y_pred_real,
            "y_actual": y_true_real,
            "rmse": rmse,
            "mae": mae,
        }
        results_df = pd.DataFrame(eval_dict)
        metrics_df = pd.DataFrame({
            "rmse": [rmse],
            "mse": [rmse**2],
            "mae": [mae],
            "mape": [mape],
            "r2": [r2],
            "within_tol_acc": [within_tol_acc],
            "total_epochs_run": [self.total_epochs_run],
            "best_epoch": [self.best_epoch],
            "early_stop_epoch": [self.early_stop_epoch],
            **{k: [v] for k, v in self.config.config_params_to_results.items()}
        })
        if self.config.save_test_results:
            self.save_df(results_df, "LSTM_results", f"{self.config.task_id}_test_results")
        self.save_df(metrics_df, "LSTM_results", f"{self.config.task_id}_test_metrics")
        return eval_dict
    

class TransformersModel(DeepLearningModel):
    """Unified wrapper for PatchTST, iTransformer, TimeXer and other transformer-based models."""
    def __init__(self, config: TransformersConfig, func: Callable[[pd.DataFrame, str, list[int], list[int], list[tuple[str, int]]], pd.DataFrame] | None = None, specific_output_dir: str | None = None):
        self.variate = config.variate
        self.patch_len = config.patch_len
        self.stride = config.stride
        self.d_model = config.d_model
        self.num_attention_heads = config.num_attention_heads
        self.num_encoder_layers = config.num_encoder_layers
        self.dim_ff = config.dim_ff
        self.dropout_ff = config.dropout_ff
        self.dropout_head_fc = config.dropout_head_fc
        super().__init__(config, func, specific_output_dir)
        self.config: TransformersConfig = config
        self.model = self._build_model().to(self.device)
        self.total_epochs_run: int | None = None
        self.best_epoch: int | None = None
        self.early_stop_epoch: int | None = None
   
    def _build_model(self):
        model_dict = {
            TransformerModelType.PATCHTST: PatchTST,
            TransformerModelType.ITRANSFORMER: iTransformer,
            TransformerModelType.TIMEXER: TimeXer
        }
        model = model_dict[self.config.model].Model(self.config).float()
        return model
    
    def _select_optimizer(self):
        model_optim = optim.Adam(self.model.parameters(), lr=self.config.learning_rate)
        return model_optim

    def _select_criterion(self):
        criterion = nn.MSELoss()
        return criterion

    def _forward_model(self, batch_x, batch_x_mark):
        """Dispatch forward call based on model type."""
        model_name = self.config.model.value.lower()
        if 'timexer' in model_name:
            outputs = self.model(batch_x, batch_x_mark, None, None)
        elif 'linear' in model_name or 'tst' in model_name:
            outputs = self.model(batch_x)
        else:
            if self.config.output_attention:
                outputs = self.model(batch_x, batch_x_mark)[0]
            else:
                outputs = self.model(batch_x, batch_x_mark)
        return outputs
    
    def train_model(self):
        dataset, data_loader = self._get_data(flag='train')

        time_now = time()

        train_steps = len(data_loader)
        early_stopping = EarlyStopping(patience=self.config.patience, verbose=True, save_model=self.config.save_model)

        model_optim = self._select_optimizer()
        criterion = self._select_criterion()

        best_val_rmse_train = float("inf")
        best_epoch_train = -1

        # OneCycleLR scheduler only used for 'TST' learning rate adjustment
        scheduler = None
        if self.config.lradj == 'TST':
            scheduler = lr_scheduler.OneCycleLR(optimizer = model_optim,
                                                steps_per_epoch = train_steps,
                                                pct_start = self.config.pct_start,
                                                epochs = self.config.training_epochs,
                                                max_lr = self.config.learning_rate)

        progress_log = {
            'model_name': [],
            'num_parameters': [],
            'lookback_window': [],
            'epoch': [],
            'training_loss': [],
            'validation_loss': [],
            'validation_horizon': [],
            'validation_rmse': [],
            'validation_mse': [],
            'time_taken_seconds': []
        }
        checkpoint_path = self._generate_output_path(f"{self.config.model.value}_checkpoints")
        for epoch in range(self.config.training_epochs):
            iter_count = 0
            train_loss = []

            self.model.train()
            epoch_time = time()
            debug = self.config.debug
            for i, (batch_x, batch_y, batch_x_mark, batch_y_mark, x_batch_time, y_batch_time) in enumerate(data_loader):
                if debug:
                    print(f"Target Shape: {dataset.reference_data_y_df.shape}")
                    print(f"Target Col Name: {dataset.reference_data_y_df.columns.tolist()}")
                    print(f"Feature Shape: {dataset.reference_data_x_df.shape}")
                    print(f"Feature Cols: {dataset.reference_data_x_df.columns.tolist()}")
                    debug = self._debug_batch_timing('Training', x_batch_time, y_batch_time)
                iter_count += 1
                model_optim.zero_grad()
                batch_x = batch_x.float().to(self.device)

                batch_y = batch_y.float().to(self.device)
                batch_x_mark = batch_x_mark.float().to(self.device)
                batch_y_mark = batch_y_mark.float().to(self.device)

                outputs = self._forward_model(batch_x, batch_x_mark)

                f_dim = -1 if self.config.variate == 'MS' else 0
                outputs = outputs[:, -self.config.forecast_horizon:, f_dim:]
                batch_y = batch_y[:, -self.config.forecast_horizon:, f_dim:].to(self.device)

                loss = criterion(outputs, batch_y)
                train_loss.append(loss.item())

                if (i + 1) % 100 == 0:
                    print("\titers: {0}, epoch: {1} | loss: {2:.7f}".format(i + 1, epoch + 1, loss.item()))
                    speed = (time() - time_now) / iter_count
                    left_time = speed * ((self.config.training_epochs - epoch) * train_steps - i)
                    print('\tspeed: {:.4f}s/iter; left time: {:.4f}s'.format(speed, left_time))
                    iter_count = 0
                    time_now = time()

                loss.backward()
                model_optim.step()
                    
                if self.config.lradj == 'TST' and scheduler is not None:
                    adjust_learning_rate(model_optim, scheduler, epoch + 1, self.config, printout=False)
                    scheduler.step()
            cost_time = time() - epoch_time
            print("Epoch: {} cost time: {}".format(epoch + 1, cost_time))
            train_loss = np.average(train_loss)
            _, _, _, _, _, mae_val, rmse_val, mse_val, vali_loss = self.evaluate_model()
            if rmse_val < best_val_rmse_train:
                best_val_rmse_train = rmse_val
                best_epoch_train = epoch + 1
            progress_log['model_name'].append(self.config.task_id)
            progress_log['num_parameters'].append(sum(p.numel() for p in self.model.parameters()))
            progress_log['lookback_window'].append(self.config.lookback_window)
            progress_log['epoch'].append(epoch + 1)
            progress_log['training_loss'].append(train_loss)
            progress_log['validation_loss'].append(vali_loss)
            progress_log['validation_horizon'].append(self.config.forecast_horizon)
            progress_log['validation_rmse'].append(rmse_val)
            progress_log['validation_mse'].append(mse_val)
            progress_log['time_taken_seconds'].append(cost_time)
            print("Epoch: {0}, Steps: {1} | Train Loss: {2:.7f} Vali Loss: {3:.7f}".format(
                epoch + 1, train_steps, train_loss, vali_loss))
            print(f"\tValidation RMSE: {rmse_val:.4f} | Validation MAE: {mae_val:.4f}")
            early_stopping(vali_loss, self.model, checkpoint_path, self.config.task_id)
            if early_stopping.early_stop:
                print("Early stopping")
                break

            if self.config.lradj != 'TST':
                adjust_learning_rate(model_optim, scheduler, epoch + 1, self.config)
            else:
                print('Updating learning rate to {}'.format(scheduler.get_last_lr()[0]))

        self.total_epochs_run = epoch + 1
        self.best_epoch = best_epoch_train
        self.early_stop_epoch = epoch + 1 if early_stopping.early_stop else None
        progress_log.update({k: [v] * len(progress_log['epoch']) for k, v in self.config.config_params_to_results.items()})
        fitting_progress_log_df = pd.DataFrame(progress_log)
        if self.config.save_training_log:
            self.save_df(fitting_progress_log_df, f"{self.config.model.value}_results", f"{self.config.task_id}_fitting_log")
        return self.model

    def load_model(self, file_name: str):
        self.torch_load_checkpoints(f"{self.config.model.value}_checkpoints", file_name)
        return self.model

    def evaluate_model(self, model=None, test_mode=0):
        if model is None:
            if self.model is None:
                raise ValueError("No model provided for testing. Please provide a torch.nn.Module object or a model file name, or ensure that train_model() has been called to train and set self.model.")
            else:
                print('loading model from training')
        elif isinstance(model, str):
            self.load_model(model)
            if self.model is None:
                raise ValueError("Model not found in patchtst_models directory. Please check the file name and try again or use train_model() to train a new model.")
        elif isinstance(model, torch.nn.Module):
            self.model = model.to(self.device)
        else:
            raise ValueError("model must be either None, a file name string, or a torch.nn.Module object.")
        
        dataset, data_loader = self._get_data(flag='test' if test_mode else 'val')

        criterion = self._select_criterion()
        preds = []
        trues = []
        timestamps = []
        batch_nums = []
        batch_windows = []
        total_loss = []
        self.model.eval()
        debug = self.config.debug
        with torch.no_grad():
            for i, (batch_x, batch_y, batch_x_mark, _, x_batch_time, y_batch_time) in enumerate(data_loader):
                if debug:
                    print(f"Target Shape: {dataset.reference_data_y_df.shape}")
                    print(f"Target Col Name: {dataset.reference_data_y_df.columns.tolist()}")
                    print(f"Feature Shape: {dataset.reference_data_x_df.shape}")
                    print(f"Feature Cols: {dataset.reference_data_x_df.columns.tolist()}")
                    debug = self._debug_batch_timing('Test' if test_mode else 'Validation', x_batch_time, y_batch_time)
                batch_x = batch_x.float().to(self.device)
                batch_y = batch_y.float()
                batch_x_mark = batch_x_mark.float().to(self.device)
                batch_window = (np.zeros((y_batch_time.shape[0],y_batch_time.shape[1])) + np.arange(y_batch_time.shape[1]))

                outputs = self._forward_model(batch_x, batch_x_mark)
                
                f_dim = -1 if self.config.variate == 'MS' else 0
                outputs = outputs[:, -self.config.forecast_horizon:, f_dim:]
                batch_y = batch_y[:, -self.config.forecast_horizon:, f_dim:]
                y_batch_time = y_batch_time[:, -self.config.forecast_horizon:]
                batch_window = batch_window[:, -self.config.forecast_horizon:]
                outputs = outputs.detach().cpu()
                batch_y = batch_y.detach().cpu()

                loss = criterion(outputs, batch_y)
                total_loss.append(loss)

                ts = y_batch_time.detach().cpu().numpy()
                current_batch_number = np.zeros(ts.shape)+i
                batch_nums.extend(current_batch_number)
                
                if self.config.scale:
                    pred, true = self._compute_inverse_scaling(batch_y.shape, outputs, batch_y)
                else:
                    pred = outputs.numpy()
                    true = batch_y.numpy()
                if self.config.used_log_target:
                    pred = np.concatenate([pred[:,:,:-1], np.exp(pred[:,:,-1:])], axis=2)
                    true = np.concatenate([true[:,:,:-1], np.exp(true[:,:,-1:])], axis=2)
                preds.extend(pred)
                trues.extend(true)
                timestamps.extend(ts)
                batch_windows.extend(batch_window)
        
        total_loss = np.average(total_loss)
        preds = np.array(preds)
        trues = np.array(trues)
        timestamps = np.array(timestamps, dtype='<M8[us]')
        batch_nums = np.array(batch_nums)
        batch_windows = np.array(batch_windows)

        preds = preds.reshape(-1, preds.shape[-2], preds.shape[-1])
        trues = trues.reshape(-1, trues.shape[-2], trues.shape[-1])
        timestamps = timestamps.reshape(-1, timestamps.shape[-1])
        batch_nums = batch_nums.reshape(-1, batch_nums.shape[-1])
        batch_windows = batch_windows.reshape(-1, batch_windows.shape[-1])
        mae, mse, rmse, mape, mspe, rse, corr = metric(preds[:, :, -1], trues[:, :, -1]) # only get metrics for target variable.
        
        # result save
        results_df = pd.DataFrame({
            'batch_number': batch_nums.flatten().astype(int),
            'horizon': batch_windows.flatten().astype(int),
            'timestamp': timestamps.flatten(),
            'y_actual': trues[:, :, -1].flatten(),
            'y_pred': preds[:, :, -1].flatten()
        })
        metrics_df = pd.DataFrame({
            'mae': [mae],
            'mse': [mse],
            'rmse': [rmse],
            'total_epochs_run': [self.total_epochs_run],
            'best_epoch': [self.best_epoch],
            'early_stop_epoch': [self.early_stop_epoch],
            **{k: [v] for k, v in self.config.config_params_to_results.items()}
        })
        if test_mode:
            print(f"Test Results - MAE: {mae:.2f} MW | RMSE: {rmse:.2f} MW | MSE: {mse:.2f} MW^2")
            folder_name = f"{self.config.model.value}_results"
            if self.config.save_test_results:
                self.save_df(results_df, folder_name, f"{self.config.task_id}_test_results")
            self.save_df(metrics_df, folder_name, f"{self.config.task_id}_test_metrics")
        else:
            self.model.train()
        return batch_nums.flatten().astype(int), timestamps.flatten(), trues[:, :, -1].flatten(), preds[:, :, -1].flatten(), batch_windows.flatten(), mae, rmse, mse, total_loss


class SarimaxModel(BaseModel):
    def __init__(self, config: SARIMAXConfig, func: Callable[[pd.DataFrame, str, list[int], list[int], list[tuple[str, int]]], pd.DataFrame] | None = None, specific_output_dir: str | None = None):
        super().__init__(config, func, specific_output_dir)
        self.p = config.p
        self.d = config.d
        self.q = config.q
        self.P = config.P
        self.D = config.D
        self.Q = config.Q
        self.seasonality_period = config.seasonality_period
        self.enforce_stationarity = config.enforce_stationarity
        self.enforce_invertibility = config.enforce_invertibility
        if config.eval_step_size > config.forecast_horizon:
            print(f"Warning: eval_step_size {config.eval_step_size} is greater than forecast_horizon {config.forecast_horizon}. Setting eval_step_size to forecast_horizon.")
        
        self.best_model: SARIMAXResultsWrapper | None = None
        self.best_order = None
        self.best_seasonal_order = None
        self.config: SARIMAXConfig = config
        self.results_folder_name = "sarimax_results"
        self.models_folder_name = "sarimax_models"
   
    def train_model(self):
        # only use the most recent 'lookback_window' data points for training, if lookback_window is specified in the config
        self.training_data = self.training_data.iloc[-self.config.lookback_window:] if self.config.lookback_window else self.training_data
        best_training_aic = np.inf
        best_val_mse = np.inf
        best_order = None
        best_seasonal_order = None
        progress_log = {
            'model_name': [],
            'order': [],
            'seasonal_order': [],
            'training_aic': [],
            'validation_horizon': [],
            'validation_iters': [],
            'validation_mae': [],
            'validation_mse': [],
            'validation_rmse': [],
            'time_taken_seconds': []
        }
        for p in self.p:
            for d in self.d:
                for q in self.q:
                    for p_s in self.P:
                        for d_s in self.D:
                            for q_s in self.Q:
                                    print(f"Fitting SARIMAX({p},{d},{q})({p_s},{d_s},{q_s},{self.seasonality_period})...")
                                    start = time()
                                    model = SARIMAX(
                                        endog=self.training_data[self.config.target_col], 
                                        exog=self.training_data[self.config.all_feature_cols] if self.config.all_feature_cols else None,
                                        order=(p,d,q), 
                                        seasonal_order=(p_s,d_s,q_s,self.seasonality_period),
                                        enforce_stationarity=self.enforce_stationarity,
                                        enforce_invertibility=self.enforce_invertibility
                                    )
                                    model_fit = model.fit(disp=False, warn_convergence=False)
                                    end = time()
                                    print(f"\tFitted SARIMAX({p},{d},{q})({p_s},{d_s},{q_s},{self.seasonality_period}) - Training AIC: {model_fit.aic:.2f} | Time taken: {end - start:.2f} seconds\n")
                                    try:
                                        print(f"\tValidating SARIMAX({p},{d},{q})({p_s},{d_s},{q_s},{self.seasonality_period}) on horizon {self.config.forecast_horizon} with step size {self.val_step_size}...")
                                        _, _, _, _, mae, rmse, mse = self.evaluate_model(model_fit)
                                        if mse < best_val_mse:
                                            print(f"New best model found: order ({p},{d},{q}) | seasonal_order ({p_s},{d_s},{q_s},{self.seasonality_period}) - RMSE: {rmse:.2f}")
                                            best_val_mse = mse
                                            best_order = (p,d,q)
                                            best_seasonal_order = (p_s,d_s,q_s,self.seasonality_period)
                                            best_model = model_fit
                                            best_training_aic = model_fit.aic
                                            progress_log['model_name'].append(self.config.task_id)
                                            progress_log['order'].append(best_order)
                                            progress_log['seasonal_order'].append(best_seasonal_order)
                                            progress_log['validation_horizon'].append(self.config.forecast_horizon)
                                            progress_log['validation_iters'].append(self.val_step_size)
                                            progress_log['training_aic'].append(model_fit.aic)
                                            progress_log['validation_mae'].append(mae)
                                            progress_log['validation_rmse'].append(rmse)
                                            progress_log['validation_mse'].append(mse)
                                            progress_log['time_taken_seconds'].append(end - start)
                                    except Exception as e:
                                        print(e)
                                        print(f"\tError validating SARIMAX({p},{d},{q})({p_s},{d_s},{q_s},{self.seasonality_period}) on horizon {self.config.forecast_horizon} with step size {self.val_step_size}: {e}")
        print(f"Best SARIMAX{best_order}{best_seasonal_order} - AIC: {best_training_aic:.2f} | Validation MSE: {best_val_mse:.2f} | Validation RMSE: {np.sqrt(best_val_mse):.2f} | Time taken: {progress_log['time_taken_seconds'][-1]:.2f} seconds")
        self.best_model = best_model
        self.best_order = best_order
        self.best_seasonal_order = best_seasonal_order
        if self.config.save_training_log:
            progress_log.update({k: [v] * len(progress_log['model_name']) for k, v in self.config.config_params_to_results.items()})
            fitting_progress_log_df = pd.DataFrame(progress_log)
            self.save_df(fitting_progress_log_df, self.results_folder_name, f"{self.config.task_id}_fitting_log")
        if self.config.save_model:
            self.pickle_save_checkpoints(self.best_model, self.models_folder_name, f"{self.config.task_id}_model.pkl")
        print("Training complete. Saved best model and fitting progress log.")

    def load_model(self, file_name: str):
        self.best_model = self.pickle_load_checkpoints(self.models_folder_name, file_name)
        return self.best_model

    def evaluate_model(self, model_fit:SARIMAXResultsWrapper | str | None, test_mode: bool = False):
        if model_fit is None:
            if self.best_model is None:
                raise ValueError("No model provided for testing. Please provide a fitted SARIMAXResultsWrapper object or a model file name, or ensure that train_model() has been called to train and set the best_model.")
            else:
                _model_fit = self.best_model
        elif isinstance(model_fit, str):
            _model_fit = self.load_model(model_fit)
            if _model_fit is None:
                raise ValueError("Model not found in sarimax_models directory. Please check the file name and try again or use train_model() to train a new model.")
        elif isinstance(model_fit, SARIMAXResultsWrapper):
            _model_fit = model_fit
        else:
            raise ValueError("model_fit must be either None, a file name string, or a SARIMAXResultsWrapper object.")

        rolling_state = deepcopy(_model_fit)

        if test_mode:
            test_df = self.test_data.copy()
            print("\nNow updating the internal state of the best model with validation data WITHOUT updating parameters...")
            rolling_state = rolling_state.append(
                self.validation_data[self.config.target_col], 
                exog=self.validation_data[self.config.all_feature_cols] if self.config.all_feature_cols else None, 
                refit=False)
        else:
            test_df = self.validation_data.copy()

        exog_vars_df = test_df[self.config.all_feature_cols] if self.config.all_feature_cols else None
        test_df = test_df[self.config.target_col]

        assert len(test_df) >= self.config.forecast_horizon, "Test target data points must be at least as many as the forecast horizon"
        assert exog_vars_df is None or len(exog_vars_df) >= self.config.forecast_horizon, "Exogenous variables data points must be at least as many as the forecast horizon"
        val_step_size = min(self.val_step_size, len(test_df) - self.config.forecast_horizon)
        origins = range(0, len(test_df) - self.config.forecast_horizon, val_step_size)
        print(f"\tNumber of rolling forecast origins: {len(list(origins))}")

        all_actuals = []
        all_predictions = []
        all_timestamps = []   
        all_origins = []  
        debug = self.config.debug
        for i in origins:
            # 1. First, make the forecast from the current state
            future_exog = exog_vars_df.iloc[i : i + self.config.forecast_horizon] if exog_vars_df is not None else None
            forecast = rolling_state.forecast(steps=self.config.forecast_horizon, exog=future_exog)
            actuals = test_df.iloc[i : i + self.config.forecast_horizon]
            if debug:
                debug = self._debug_batch_timing('Test' if test_mode else 'Validation', future_exog, actuals)
            if self.config.scale:
                pos = self.nsw_data_loader.scaler.feature_names_in_.tolist().index(self.config.target_col)
                mean = self.nsw_data_loader.scaler.mean_[pos]
                var = self.nsw_data_loader.scaler.var_[pos]
                forecast = forecast*var**0.5 + mean
                actuals = actuals*var**0.5 + mean
            if self.config.used_log_target:
                forecast = np.exp(forecast)
                actuals = np.exp(actuals)
            # Store predictions and actuals
            all_predictions.extend(forecast.values)
            all_actuals.extend(actuals)
            all_timestamps.extend(test_df.index[i : i + self.config.forecast_horizon].tolist())
            all_origins.extend([i // val_step_size] * self.config.forecast_horizon)
            
            if (i // val_step_size) % 100 == 0 and i > 0:
                mae_so_far  = mean_absolute_error(all_actuals, all_predictions)
                mse_so_far  = mean_squared_error(all_actuals, all_predictions)
                rmse_so_far = np.sqrt(mse_so_far)
                print(f"\t\tOrigin {i//val_step_size} out of {len(origins)}: Validation MAE: {mae_so_far:.2f} MW | Validation RMSE so far: {rmse_so_far:.2f} MW")

            # 2. Then, advance the Origin forward by 'val_step_size'
            # We do this by APPENDING the model state with the actuals that occurred during that step
            new_endog = test_df.iloc[i : i + val_step_size]
            new_exog = exog_vars_df.iloc[i : i + val_step_size] if exog_vars_df is not None else None
            
            # .extend() updates the auto-regressive state of the model with the new observed data, so that the next forecast will be based on this updated state.
            # This simulates the real-world scenario where after making a forecast, we observe the actual outcome and then use that information to make the next forecast.
            rolling_state = rolling_state.extend(new_endog, exog=new_exog)

        mae  = mean_absolute_error(all_actuals, all_predictions)
        mse  = mean_squared_error(all_actuals, all_predictions)
        rmse = np.sqrt(mse)
        print(f"Rolling Forecast (h={self.config.forecast_horizon} steps) — Validation MAE: {mae:.2f} MW | Validation RMSE: {rmse:.2f} MW")
        results_df = pd.DataFrame({
            'origins': all_origins,
            'horizon': [i % self.config.forecast_horizon for i in range(len(all_actuals))],
            'timestamp': all_timestamps,
            'y_actual': all_actuals,
            'y_pred': all_predictions
        })
        metrics_df = pd.DataFrame({
            'rmse': [rmse],
            'mse': [mse],
            'mae': [mae],
            'total_epochs_run': [None],
            'best_epoch': [None],
            'early_stop_epoch': [None],
            **{k: [v] for k, v in self.config.config_params_to_results.items()}
        })
        if test_mode:
            if self.config.save_test_results:
                self.save_df(results_df, self.results_folder_name, f"{self.config.task_id}_test_results")
            self.save_df(metrics_df, self.results_folder_name, f"{self.config.task_id}_test_metrics")
        return all_origins, all_timestamps, all_actuals, all_predictions, mae, rmse, mse
     