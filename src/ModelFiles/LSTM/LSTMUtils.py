import pandas as pd
from ModelFiles.ModelConfigs import LSTMConfig
from NSWData.NSWDataLoader import NSWDataLoader
from ModelFiles.GroupAModels import LSTMModel
import numpy as np
import os, torch, math, json
from copy import deepcopy
from itertools import product

from ModelFiles.ModelEnums import LSTMModelType

def add_lag_features(
    df: pd.DataFrame,
    target_col: str,
    target_lags: list[int],
    target_mas: list[int],
    feature_lag_cols: list[tuple[str, int]]
) -> pd.DataFrame:
    df = df.copy()

    for lag in target_lags:
        df[f"{target_col}_lag_{lag}"] = df[target_col].shift(lag)

    for ma in target_mas:
        df[f"{target_col}_ma_{ma}"] = df[target_col].shift(1).rolling(ma).mean()

    for feature, lag in feature_lag_cols:
        df[f"{feature}_lag_{lag}"] = df[feature].shift(lag)
    return df.dropna()

def make_config_name(config: LSTMConfig):
    demand_lags_str = "-".join(map(str, config.target_lags if config.target_lags else [])) if config.target_lags else "none"
    temp_lags_str = "-".join(map(str, [f"{feature}_{lag}" for feature, lag in config.feature_lag_cols] if config.feature_lag_cols else [])) if config.feature_lag_cols else "none"

    name = (
        f"{config.model_type.value}"
        f"_lb{config.lookback_window}"
        f"_hs{config.hidden_size}"
        f"_nl{config.num_layers}"
        f"_do{config.dropout}"
        f"_lr{config.learning_rate}"
        f"_mlp{int(config.use_mlp_head if hasattr(config, 'use_mlp_head') else False)}"
        f"_dlags{demand_lags_str}"
        f"_tlags{temp_lags_str}"
    )

    if hasattr(config, 'num_attention_heads'):
        name += f"_heads{config.num_attention_heads}"

    return name

def run_experiment(config: LSTMConfig, experiment_name:str|None=None, specific_output_dir:str|None=None):
    """
    Atomic run function.
    Assumes the following already exist earlier in the notebook:
    - SEED
    - DEVICE
    - OUTPUT_DIR
    - set_seed
    - load_data
    - build_dataloaders
    - build_model
    - train_model
    - evaluate_model
    - plot_training_history
    - plot_predictions
    - nn (torch.nn)
    """
    lstm_model = LSTMModel(config, add_lag_features, specific_output_dir=specific_output_dir)
    experiment_name = experiment_name or make_config_name(config)

    print("\n" + "=" * 90)
    print(f"Running experiment: {experiment_name}")
    print("=" * 90)
    for k, v in config.__dict__.items():
        print(f"{k}: {v}")

    train_data, train_loader = lstm_model._get_data("train") 
    val_data, val_loader = lstm_model._get_data("val")
    test_data, test_loader = lstm_model._get_data("test")
    
    # DEBUG: Inspect input features
    print("\n" + "="*60)
    print("DEBUG: FEATURE INSPECTION")
    print("="*60)

    # 1. Feature names
    if config.all_feature_cols is not None:
        print("\nFeature names:")
        for i, f in enumerate([config.target_col] + config.all_feature_cols):
            print(f"{i}: {f}")
    else:
        print("\nNo feature list found in config.feature_cols.")

    # 2. Shape check
    print("\nSequence shape (lookback, num_features):", next(iter(train_loader))[0][0].shape)

    # 3. Convert to DataFrame for readability
    print("\nRaw sequence values (first 5 timesteps):")
    print(next(iter(train_loader))[0][0][:5])

    # 4. Target check
    print("\nTarget (scaled):", next(iter(train_loader))[1][0][0].item())

    # Optional: inverse transform
    if config.scale:
        pos = lstm_model.scaler.feature_names_in_.tolist().index(config.target_col)
        mean = lstm_model.scaler.mean_[pos]
        var = lstm_model.scaler.var_[pos]
        y_real = next(iter(train_loader))[1][0][0]* var**0.5 + mean
        print("Target (real scale):", y_real.item())

    print("="*60 + "\n")

    print("\nSequence shapes:")
    print("X_train:", train_data.shape()[0], "| y_train:", train_data.shape()[1])
    print("X_val:  ", val_data.shape()[0],   "| y_val:  ", val_data.shape()[1])
    print("X_test: ", test_data.shape()[0],  "| y_test: ", test_data.shape()[1])

    # Quick debug checks
    for name, param in lstm_model.model.named_parameters():
        print(f"[DEBUG] First parameter tensor: {name}")
        print("[DEBUG] First 5 values:", param.detach().view(-1)[:5].cpu().numpy())
        break

    print("[DEBUG] First 5 y values from first train batch:", next(iter(train_loader))[1][0][:5])

    train_output = lstm_model.train_model()

    train_losses = train_output["train_losses"]
    val_losses = train_output["val_losses"]
    best_state = train_output["best_state"]
    best_epoch = train_output["best_epoch"]
    best_val_loss = train_output["best_val_loss"]

    lstm_model.model.load_state_dict(best_state)

    eval_dict = lstm_model.evaluate_model(tolerance_pct=10.0, test_mode=1)

    result = {
        "experiment_name": experiment_name,
        "seed": config.seed,
        "best_epoch": best_epoch,
        "best_val_loss": float(best_val_loss) if best_val_loss is not None else np.nan,
        "test_rmse": eval_dict.get("rmse"),
        "test_mae": eval_dict.get("mae"),
        "test_mape": eval_dict.get("mape"),
        "test_r2": eval_dict.get("r2"),
        "test_acc_within_10pct": eval_dict.get("within_tol_acc"),
    }

    # Add selected config parameters into result row for easier sorting/filtering
    for k in [
        "model_type",
        "hidden_size",
        "num_layers",
        "dropout",
        "learning_rate",
        "use_mlp_head",
        "mlp_hidden_size",
        "lookback",
        "horizon",
        "demand_lags",
        "temp_lags",
        "num_attention_heads",
    ]:
        if hasattr(config, k):
            result[k] = getattr(config, k)

    artifact = {
        "config": deepcopy(config),
        "result": result,
        "model_class": lstm_model.model.__class__.__name__,
        "input_size": train_data.shape()[0][1],
        "train_losses": train_losses,
        "val_losses": val_losses,
        "best_state": deepcopy(best_state),
        "best_epoch": best_epoch,
        "best_val_loss": best_val_loss,
        "eval_dict": eval_dict,
    }
    return artifact

def build_config_list(base_config:LSTMConfig, param_grid=None):
    """
    Builds a list of config dictionaries from a base config and optional param grid.
    If param_grid is None or empty, returns [base_config].
    """
    if not param_grid:
        return [deepcopy(base_config)]

    keys = list(param_grid.keys())
    values = list(param_grid.values())

    configs = []
    for combo in product(*values):
        cfg = deepcopy(base_config)
        for k, v in zip(keys, combo):
            setattr(cfg, k, v)
        configs.append(cfg)
    return configs

def run_experiment_suite(
    base_config,
    param_grid=None,
    n_repeats=1,
    base_seed=42,
    save_results=None,
    save_best_model=False,
    show_live_plots=False,
):
    """
    Unified runner for:
    - single experiment (param_grid=None, n_repeats=1)
    - parameter sweep (param_grid=..., n_repeats=1)
    - repeated experiments (param_grid=..., n_repeats>1)
    """

    config_list = build_config_list(base_config, param_grid)
    total_runs = len(config_list) * n_repeats

    all_rows = []
    all_artifacts = []

    run_counter = 0
    print(f"Total configurations: {len(config_list)}")
    print(f"Repeats per configuration: {n_repeats}")
    print(f"Total runs: {total_runs}")

    for cfg_idx, cfg in enumerate(config_list, start=1):
        config_name = make_config_name(cfg)
        print(f"\n{'='*100}")
        print(f"[CONFIG {cfg_idx}/{len(config_list)}] {config_name}")
        print(f"{'='*100}")

        for repeat_idx in range(n_repeats):
            run_counter += 1
            run_seed = base_seed + repeat_idx

            cfg_run = deepcopy(cfg)
            setattr(cfg_run, "seed", run_seed)

            experiment_name = config_name if n_repeats == 1 else f"{config_name}__seed{run_seed}"

            print(f"\nRun {run_counter}/{total_runs} | repeat {repeat_idx + 1}/{n_repeats} | seed={run_seed}")

            artifact = run_experiment(
                config=cfg_run,
                experiment_name=experiment_name,
                save_best_model=save_best_model,
                show_live_plots=show_live_plots,
            )

            result = artifact.get("result", {})
            eval_dict = artifact.get("eval_dict", {})

            row = {
                "config_name": config_name,
                "experiment_name": experiment_name,
                "repeat_idx": repeat_idx + 1,
                "seed": run_seed,
                "model_type": getattr(cfg_run, "model_type", None),
                "hidden_size": getattr(cfg_run, "hidden_size", None),
                "num_layers": getattr(cfg_run, "num_layers", None),
                "dropout": getattr(cfg_run, "dropout", None),
                "learning_rate": getattr(cfg_run, "learning_rate", None),
                "use_mlp_head": getattr(cfg_run, "use_mlp_head", None),
                "mlp_hidden_size": getattr(cfg_run, "mlp_hidden_size", None),
                "lookback": getattr(cfg_run, "lookback", None),
                "horizon": getattr(cfg_run, "horizon", None),
                "num_attention_heads": getattr(cfg_run, "num_attention_heads", np.nan),
                "demand_lags": str(getattr(cfg_run, "demand_lags", [])),
                "temp_lags": str(getattr(cfg_run, "temp_lags", [])),
                "best_epoch": result.get("best_epoch"),
                "best_val_loss": result.get("best_val_loss"),
                "test_rmse": eval_dict.get("rmse"),
                "test_mae": eval_dict.get("mae"),
                "test_mape": eval_dict.get("mape"),
                "test_r2": eval_dict.get("r2"),
                "test_acc_within_10pct": eval_dict.get("within_tol_acc"),
            }

            all_rows.append(row)
            all_artifacts.append(artifact)

    runs_df = pd.DataFrame(all_rows)

    metric_cols = [
        "best_val_loss",
        "test_rmse",
        "test_mae",
        "test_mape",
        "test_r2",
        "test_acc_within_10pct",
    ]
    for col in metric_cols:
        if col in runs_df.columns:
            runs_df[col] = pd.to_numeric(runs_df[col], errors="coerce")

    if not runs_df.empty and "best_val_loss" in runs_df.columns:
        runs_df = runs_df.sort_values(
            by=["best_val_loss", "test_rmse"],
            ascending=[True, True]
        ).reset_index(drop=True)

    if save_results:
        results_path = os.path.join(NSWDataLoader.output_dir, "LSTM_results")
        if not os.path.exists(results_path):
            os.makedirs(results_path)
        runs_df.to_csv(os.path.join(results_path, f"{config_list[0].task_id}_all_runs_raw.csv"), index=False)
        print(f"Saved detailed rolling forecast results to {results_path}/{config_list[0].task_id}_all_runs_raw.csv")

        # Save a lightweight JSON copy of row-wise results
        with open(os.path.join(results_path, f"{config_list[0].task_id}_all_runs_raw.json"), "w") as f:
            json.dump(runs_df.to_dict(orient="records"), f, indent=2)

    return runs_df, all_artifacts

def summarise_runs(runs_df):
    metric_cols = [
        "best_val_loss",
        "test_rmse",
        "test_mae",
        "test_mape",
        "test_r2",
        "test_acc_within_10pct",
    ]

    group_cols = [
        "config_name",
        "model_type",
        "hidden_size",
        "num_layers",
        "dropout",
        "learning_rate",
        "use_mlp_head",
        "mlp_hidden_size",
        "lookback",
        "horizon",
        "demand_lags",
        "temp_lags",
        "num_attention_heads",
    ]

    # only keep columns that actually exist
    group_cols = [c for c in group_cols if c in runs_df.columns]

    summary_rows = []

    grouped = runs_df.groupby(group_cols, dropna=False)
    for group_key, group_df in grouped:
        row = dict(zip(group_cols, group_key))
        n = len(group_df)
        row["n_runs"] = n

        for metric in metric_cols:
            if metric not in group_df.columns:
                row[f"{metric}_mean"] = np.nan
                row[f"{metric}_std"] = np.nan
                row[f"{metric}_sem"] = np.nan
                row[f"{metric}_ci95_low"] = np.nan
                row[f"{metric}_ci95_high"] = np.nan
                continue

            vals = group_df[metric].dropna().astype(float).values

            if len(vals) == 0:
                row[f"{metric}_mean"] = np.nan
                row[f"{metric}_std"] = np.nan
                row[f"{metric}_sem"] = np.nan
                row[f"{metric}_ci95_low"] = np.nan
                row[f"{metric}_ci95_high"] = np.nan
                continue

            mean_val = float(np.mean(vals))
            std_val = float(np.std(vals, ddof=1)) if len(vals) > 1 else 0.0
            sem_val = std_val / math.sqrt(len(vals)) if len(vals) > 1 else 0.0
            ci95 = 1.96 * sem_val

            row[f"{metric}_mean"] = mean_val
            row[f"{metric}_std"] = std_val
            row[f"{metric}_sem"] = sem_val
            row[f"{metric}_ci95_low"] = mean_val - ci95
            row[f"{metric}_ci95_high"] = mean_val + ci95

        summary_rows.append(row)

    summary_df = pd.DataFrame(summary_rows)

    if not summary_df.empty and "test_rmse_mean" in summary_df.columns:
        summary_df = summary_df.sort_values(
            by=["test_rmse_mean", "test_mae_mean"],
            ascending=[True, True]
        ).reset_index(drop=True)

    return summary_df

if __name__ == "__main__":
    RUN_SINGLE = True
    RUN_SWEEP = False
    RUN_REPEATED = False
    SEED = 31415

    BASE_CONFIG = LSTMConfig(
        task_id= "sweep_run_test",
        model_type= LSTMModelType.MULTIHEAD_ATTENTION_BILSTM,
        hidden_size= 64,
        num_layers= 2,
        dropout= 0.4,
        learning_rate= 5e-5,
        batch_size= 64,
        training_epochs= 1,
        patience= 8,
        use_mlp_head= True,
        mlp_hidden_size= 64,
        target_col= "TOTALDEMAND",
        feature_cols= ["TEMPERATURE"],
        feature_lag_cols= ["TEMPERATURE"],
        target_lags= [],
        feature_lags= [0,2,50],
        lookback_window= 168,
        forecast_horizon= 48,
        weight_decay= 1e-4,
        num_attention_heads= 4,
    )

    summary_path = os.path.join(NSWDataLoader.output_dir,"results","LSTM_summary")
    if not os.path.exists(summary_path):
        os.makedirs(summary_path)

    # SINGLE EXPERIMENT
    if RUN_SINGLE:
        runs_df, all_artifacts = run_experiment_suite(
            base_config=BASE_CONFIG,
            param_grid=None,
            n_repeats=1,
            base_seed=SEED,
            save_results=1,
            save_best_model=True,
            show_live_plots=False,
        )

        summary_df = summarise_runs(runs_df)
        summary_df.to_csv(os.path.join(summary_path, "single_run_summary.csv"), index=False)
        

        #best_artifact = plot_best_run(runs_df, all_artifacts, n_points=500)

        # if best_artifact["config"]["model_type"] in ["attention_bilstm", "multihead_attention_bilstm"]:
        #     plot_attention_for_sample(best_artifact, sample_index=0)

    if RUN_SWEEP:

        # PARAMETER SWEEP

        PARAM_GRID = {
            "target_col": ["LOG_TOTALDEMAND"], # ["TOTALDEMAND"]
            "used_log_target": [True], # [False]
            "lookback": [168], #[168, 336, 672],
            "horizon": [336],
            "model_type": ["lstm", "bilstm", "multihead_attention_bilstm"],
            "hidden_size": [64],
            "num_layers": [2],
            "dropout": [0.1],
            "learning_rate": [5e-5],
        }

        runs_df, all_artifacts = run_experiment_suite(
            base_config=BASE_CONFIG,
            param_grid=PARAM_GRID,
            n_repeats=1,
            base_seed=SEED,
            save_results=1,
            save_best_model=True,
            show_live_plots=False
        )

        summary_df = summarise_runs(runs_df)
        summary_df.to_csv(os.path.join(summary_path, "sweep_run_summary.csv"), index=False)

        # print("\nRaw run results:")
        # display(runs_df.head())

        # print("\nSummary:")
        # display(summary_df)

        # best_artifact = plot_best_run(runs_df, all_artifacts, n_points=500)

        # if best_artifact["config"]["model_type"] in ["attention_bilstm", "multihead_attention_bilstm"]:
        #     plot_attention_for_sample(best_artifact, sample_index=0)

    if RUN_REPEATED:
        # REPEATED EXPERIMENTS

        REPEAT_N = 5
        SAVE_DIR = "repeated_experiment_outputs"

        PARAM_GRID = {
            "lookback": [168, 336, 672],
            "horizon": [336],
            "model_type": ["lstm", "bilstm", "multihead_attention_bilstm"],
            "hidden_size": [64],
            "num_layers": [2],
            "dropout": [0.1],
            "learning_rate": [5e-5],
        }

        runs_df, all_artifacts = run_experiment_suite(
                base_config=BASE_CONFIG,
                param_grid=PARAM_GRID,
                n_repeats=REPEAT_N,
                base_seed=1000,
                save_results=1,
                save_best_model=False,
                show_live_plots=False,
        )

        summary_df = summarise_runs(runs_df)

        runs_df.to_csv(os.path.join(SAVE_DIR, "all_runs_raw.csv"), index=False)
        summary_df.to_csv(os.path.join(SAVE_DIR, "summary_stats.csv"), index=False)

        # print("\nRaw run results:")
        # display(runs_df.head())

        # print("\nSummary results:")
        # display(summary_df)

        # plot_metric_distribution_with_summary(
        #     runs_df,
        #     metric="test_rmse",
        #     title=f"Test RMSE Distribution ({len(runs_df)} Runs)"
        # )