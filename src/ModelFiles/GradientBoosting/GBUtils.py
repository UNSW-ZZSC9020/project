import pandas as pd
from ModelFiles.ModelConfigs import GradientBoostingConfig

def add_features(df: pd.DataFrame, target_col: str, target_lags: list[int], target_mas: list[int], feature_lag_cols: list[tuple[str, int]]) -> pd.DataFrame:
    df = df.copy()

    for lag in target_lags:
        df[f"{target_col}_lag_{lag}"] = df[target_col].shift(lag)

    for ma in target_mas:
        df[f"{target_col}_ma_{ma}"] = df[target_col].shift(1).rolling(ma).mean()

    for feature, lag in feature_lag_cols:
        df[f"{feature}_lag_{lag}"] = df[feature].shift(lag)

    df = df.dropna().reset_index()
    return df