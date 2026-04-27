# This module contains dataclass definitions for model parameters, training/eval loop configurations, and other settings used in the project, 
# as well as some global constants for horizons and seeds. 
# Each model type (SARIMAX, LSTM, Transformers) has its own configuration dataclass that inherits from a base Config dataclass. 
# The configuration dataclasses also have a method to convert their parameters into a dictionary format suitable for saving results.

from dataclasses import dataclass, field
from ModelFiles.ModelEnums import *

__all__ = ["TransformersConfig", "SARIMAXConfig", "LSTMConfig", "HORIZONS", "SEEDS"]

HORIZONS = [48, 336, 720]
SEEDS = [31415, 27182, 14142, 17320, 22360, 57721]

@dataclass
class Config:
    task_id: str
    forecast_horizon: int
    lookback_window: int | None = None
    date_col: str = 'DATETIME'
    target_col: str = 'TOTALDEMAND'
    used_log_target: bool = False
    target_lags: list[int] = field(default_factory=list)
    target_mas: list[int] = field(default_factory=list)
    feature_cols: list[str] = field(default_factory=list)
    feature_lag_cols: list[tuple[str, int]] = field(default_factory=list)
    scale: bool = True # if scale, then make sure to set inverse to True as well
    seed: int | None = None
    eval_step_size: int = 1
    save_training_log: bool = False
    save_test_results: bool = False
    save_model: bool = False
    debug: bool = False
    training_data_size: int | None = None # if not None, will limit the size of the training data to this number of rows (after train/val/test split). Used for debugging with smaller dataset.
    @property
    def all_feature_cols(self) -> list[str]:
        lag_feature_cols = []
        for lag in self.target_lags:
            lag_feature_cols.append(f"{self.target_col}_lag_{lag}")
        for feature, lag in self.feature_lag_cols:
            lag_feature_cols.append(f"{feature}_lag_{lag}")
        for ma in self.target_mas:
            lag_feature_cols.append(f"{self.target_col}_ma_{ma}")
        return self.feature_cols + lag_feature_cols

@dataclass(kw_only=True)
class GradientBoostingConfig(Config):
    n_estimators: int = 100
    learning_rate: float = 0.1
    max_depth: int = 3
    verbose: int = 0
    @property
    def config_params_to_results(self) -> dict:
        return {
            "model_type": "GradientBoosting",
            "target_col": self.target_col,
            "used_log_target": self.used_log_target,
            "all_feature_cols": self.all_feature_cols,
            "scale": self.scale,
            "n_estimators": self.n_estimators,
            "learning_rate": self.learning_rate,
            "max_depth": self.max_depth,
            "horizon": self.forecast_horizon,
            "target_lags": self.target_lags,
            "target_mas": self.target_mas,
            "feature_lags": self.feature_lag_cols,
            "step_size": min(self.eval_step_size, self.forecast_horizon),
            "seed": self.seed,
        }

@dataclass(kw_only=True)
class SARIMAXConfig(Config):
    # If any of the number of elements in these lists is greater than 1, then grid search will be performed
    p: list[int] = field(default_factory=list)
    d: list[int] = field(default_factory=list)
    q: list[int] = field(default_factory=list)
    P: list[int] = field(default_factory=list)
    D: list[int] = field(default_factory=list)
    Q: list[int] = field(default_factory=list)
    seasonality_period: int
    enforce_stationarity: bool
    enforce_invertibility: bool
    @property
    def config_params_to_results(self) -> dict:
        return {
            "model_type": "SARIMAX",
            "target_col": self.target_col,
            "used_log_target": self.used_log_target,
            "all_feature_cols": self.all_feature_cols,
            "scale": self.scale,
            "horizon": self.forecast_horizon,
            "training_size": self.lookback_window,
            "target_lags": self.target_lags,
            "target_mas": self.target_mas,
            "feature_lags": self.feature_lag_cols,
            "step_size": min(self.eval_step_size, self.forecast_horizon),
            "p": self.p,
            "d": self.d,
            "q": self.q,
            "P": self.P,
            "D": self.D,
            "Q": self.Q,
            "seasonality_period": self.seasonality_period,
            "enforce_stationarity": self.enforce_stationarity,
            "enforce_invertibility": self.enforce_invertibility,
        }
    
@dataclass(kw_only=True)
class DeepLearningConfig(Config):
    training_epochs: int = 10
    batch_size: int = 64
    learning_rate: float = 0.0001
    patience: int = 5 # for early stopping
    num_attention_heads: int = 4
    dropout: float = 0.1 # dropout for residual connections. Used before the encoder layer but after the input embedding + positional encoding, used inside the encoder layer after the multihead attention and after the fully connected layer of each encoder block.
    # also used for LSTM's. default is 0.4 for LSTMs.

    use_gpu: bool = True
    gpu: int = 0
    num_workers: int = 0 # for data loading. Set to 0 for debugging, can increase for faster data loading in production.
    time_encoding: str = 'timeF' # not used for PatchTST, LSTMs and SARIMAX. Only used for TimeXer.

@dataclass(kw_only=True)
class TransformersConfig(DeepLearningConfig):
    model: TransformerModelType = TransformerModelType.PATCHTST
    variate: str = 'MS' # 'S' for single variate, 'MS' for multiple predictors but single output, 'M' for multiple predictors and multiple outputs
    patch_len: int = 16
    stride: int = 1
    d_model: int = 128
    num_encoder_layers: int = 3
    dim_ff: int = 256
    dropout_head_fc: float = 0.1 # dropout for the fully connected layers in the head (after the transformer backbone)
    output_attention: bool = False
    lradj: str = 'TST' # options are 'type1', 'type2', 'type3', 'TST', 'constant', '1', '2', '3', '4', '5', '6'. See tools.py for details on each type of learning rate adjustment strategy.
    pct_start: float = 0.3 # for OneCycleLR scheduler, the percentage of the cycle spent increasing the learning rate.
    padding_patch: str = 'end'
    revin: int = 1
    affine: int = 0
    subtract_last: int = 0
    decomposition: int = 0
    kernel_size: int = 25
    dropout_ff: float = 0.1 # dropout for a fully connected layer head only if pretrain_head is True, but pretrain_head is never used in official repo.
    individual: int = 0 # whether to use individual head for each channel input.
    use_norm: bool = True # TimeXer: whether to apply instance normalization on encoder input
    activation: str = 'gelu' # TimeXer: activation function in encoder feed-forward layers ('relu' or 'gelu')

    # --- Alias properties for TimeXer.Model compatibility ---
    # TimeXer.Model.__init__ reads config attributes using original paper naming.
    # These read-only properties map our naming convention to the names expected by TimeXer.
    @property
    def task_name(self) -> str:
        return 'long_term_forecast'
    @property
    def features(self) -> str:
        return self.variate
    @property
    def seq_len(self) -> int | None:
        return self.lookback_window
    @property
    def pred_len(self) -> int:
        return self.forecast_horizon
    @property
    def embed(self) -> str:
        return self.time_encoding
    @property
    def n_heads(self) -> int:
        return self.num_attention_heads
    @property
    def d_ff(self) -> int:
        return self.dim_ff
    @property
    def e_layers(self) -> int:
        return self.num_encoder_layers
    @property
    def factor(self) -> int:
        """Hardcoded; FullAttention accepts but ignores this parameter."""
        return 1
    @property
    def freq(self) -> str:
        """Hardcoded; DataEmbedding_inverted accepts but ignores this parameter."""
        return '30min'

    @property
    def enc_in(self) -> int:
        n = len(self.all_feature_cols) if self.all_feature_cols else 0
        return n + 1  # +1 for target column included in MS/M input
    @property
    def c_out(self) -> int:
        return 1 if self.variate in ['S', 'MS'] else len(self.all_feature_cols)
    @property
    def config_params_to_results(self) -> dict:
        return {
            "model_type": self.model.value,
            "target_col": self.target_col,
            "used_log_target": self.used_log_target,
            "all_feature_cols": self.all_feature_cols,
            "scale": self.scale,
            "horizon": self.forecast_horizon,
            "lookback": self.lookback_window,
            "target_lags": self.target_lags,
            "target_mas": self.target_mas,
            "feature_lags": self.feature_lag_cols,
            "step_size": min(self.eval_step_size, self.forecast_horizon),
            "variate": self.variate,
            "patch_len": self.patch_len,
            "stride": self.stride,
            "d_model": self.d_model,
            "num_encoder_layers": self.num_encoder_layers,
            "num_attention_heads": self.num_attention_heads,
            "dim_ff": self.dim_ff,
            "dropout": self.dropout,
            "dropout_head_fc": self.dropout_head_fc,
            "use_norm": self.use_norm,
            "activation": self.activation,
            "learning_rate": self.learning_rate,
            "seed": self.seed,
        }


@dataclass(kw_only=True)
class LSTMConfig(DeepLearningConfig):
    model_type: LSTMModelType = LSTMModelType.MULTIHEAD_ATTENTION_BILSTM
    hidden_size: int = 64
    num_layers: int = 2
    use_mlp_head: bool = True
    mlp_hidden_size: int = 64
    weight_decay: float = 1e-4
    scheduler: str | None = None
    optimizer: str = "adam"
    scheduler_factor: float = 0.5
    scheduler_patience: int = 5
    scheduler_step_size: int = 10
    scheduler_gamma: float = 0.5
    forecast_last_step_only: bool = True # if True, only predict the last step in the forecast horizon. If False, predict all steps in the forecast horizon.

    @property
    def config_params_to_results(self) -> dict:
        return {
            "model_type": self.model_type.value,
            "target_col": self.target_col,
            "used_log_target": self.used_log_target,
            "all_feature_cols": self.all_feature_cols,
            "scale": self.scale,
            "horizon": self.forecast_horizon,
            "lookback": self.lookback_window,
            "target_lags": self.target_lags,
            "target_mas": self.target_mas,
            "feature_lags": self.feature_lag_cols,
            "step_size": min(self.eval_step_size, self.forecast_horizon),
            "forecast_last_step_only": self.forecast_last_step_only,
            "hidden_size": self.hidden_size,
            "num_layers": self.num_layers,
            "dropout": self.dropout,
            "learning_rate": self.learning_rate,
            "use_mlp_head": self.use_mlp_head,
            "mlp_hidden_size": self.mlp_hidden_size,
            "num_attention_heads": self.num_attention_heads,
            "learning_rate": self.learning_rate,
            "seed": self.seed,
        }

