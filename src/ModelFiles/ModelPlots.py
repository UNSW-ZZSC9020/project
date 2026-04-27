# This module contains functions for plotting training history and model predictions.

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pandas as pd

def plot_training_history(train_losses, val_losses, best_epoch=None, title="Training History"):
    """Plots the training and validation loss curves over epochs."""
    plt.figure(figsize=(8, 4))
    plt.plot(train_losses, label="Train Loss")
    plt.plot(val_losses, label="Val Loss")
    if best_epoch is not None:
        plt.axvline(x=best_epoch, color='r', linestyle='--', alpha=0.3, label='Best Epoch')
    plt.xlabel("Epoch")
    plt.ylabel("MSE Loss (scaled)")
    plt.title(title)
    plt.legend(fontsize=8)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()


def plot_predictions(results_dict: dict[str,dict[int,pd.DataFrame]], horizon:int, start_date: str, extra_time_steps: int = 48, pred_alpha: float = 0.7):
    """Plots the model predictions vs actuals for a given horizon and start date.
    Args:
        results_dict: A dictionary of the form {model_name: {horizon: DataFrame}} containing the predictions and timestamps for each model and horizon.
        horizon: The forecast horizon (number of time steps) to plot, should only accept 48, 336 and 720. They should also be present in the results_dict as keys.
        start_date: The start date for the plot.
        extra_time_steps: Additional time steps to include in the plot beyond the horizon for better visualization.
        pred_alpha: The alpha value for the prediction lines, controlling their transparency.
    """
    plt.figure(figsize=(12, 5))
    
    # Define specific colours for each model
    model_colours = {
        'SARIMAX': '#1f77b4',
        'LSTM': '#2ca02c',
        'Gradient Boosting': 'orange',
        'PatchTST': '#9467bd'
    }
    
    model_names = results_dict.keys()
    actuals = None
    for i, model_name in enumerate(model_names):
        min_date = pd.to_datetime(max(results_dict[model_name][horizon]['timestamp'].min(), results_dict[model_name][horizon]['timestamp'].min()))
        max_date = pd.to_datetime(min(results_dict[model_name][horizon]['timestamp'].max(), results_dict[model_name][horizon]['timestamp'].max()))
        _start_date = pd.to_datetime(start_date)
        assert _start_date >= min_date and _start_date <= max_date, f"start_date is out of range: {_start_date} not in [{min_date}, {max_date}]"
        _end_date = _start_date + pd.Timedelta(hours=horizon // 2)
        assert _end_date >= min_date and _end_date <= max_date, f"end_date is out of range: {_end_date} not in [{min_date}, {max_date}]"
        df = results_dict[model_name][horizon]
        start_index = df[(df['timestamp'] >= start_date) & (df['horizon'] == 0)].index[0]
        end_index = start_index + horizon - 1
        df = df.loc[start_index:end_index + extra_time_steps]
        df = df[['timestamp', 'y_pred']]
        if model_name.lower() == 'actuals':
            actuals = df['y_pred'].values
        else:
            # Get colour for the model, default to gray if not specified
            colour = model_colours.get(model_name, 'gray')
            plt.plot(df['timestamp'], df['y_pred'], label=model_name, alpha=pred_alpha, color=colour)
    if actuals is not None:
        plt.plot(df['timestamp'], actuals, label='Actual', linestyle='--', color='red')
    plt.legend(fontsize=8)
    plt.xticks(rotation=90, fontsize=8)
    plt.yticks(fontsize=8)
    # xticks every 6 hours (12 data points) for better readability
    plt.gca().xaxis.set_major_locator(ticker.MultipleLocator(12))
    # xticks to have format "YYYY-MM-DD HH:MM"
    #plt.gca().xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: pd.to_datetime(x).strftime('%Y-%m-%d %H:%M')))
    plt.xlabel('Timestamp')
    plt.ylabel('Electricity Demand (MW)')
    plt.title(f'Model Predictions vs Actuals (Horizon={horizon} steps)')
    plt.grid(True, alpha=0.3)
    plt.show()