"""Bel Zhou - reproducible Weeks 1-6 data engineering and modelling workflow.

Research question
-----------------
To what extent does adding recent rooftop PV information improve next-half-hour
forecasts of NSW operational-demand change compared with otherwise matched
non-PV models, and when is any improvement greatest?

Workflow evidence
-----------------
Week 1: project scope, research question and reproducibility setup.
Week 2: AEMO and weather data ingestion and cleaning.
Week 3: data-quality checks and exploratory data analysis.
Week 4: feature engineering and final modelling-table construction.
Week 5: matched OLS, spline and gradient-boosted-tree models with/without PV.
Week 6: AEMO POE50 benchmark, subgroup analysis, bootstrap uncertainty,
        residual checks and report-ready graph generation.

Required input files can be CSV or XLSX and are resolved from ``data/raw`` first,
then the repository root. See INPUT_CANDIDATES below for accepted names.

Run from the repository root:
    python bel_weeks1_to_6_reproducible_pipeline.py

All generated artefacts are written to:
    outputs/data, outputs/tables, outputs/figures, outputs/models, outputs/logs
"""

from __future__ import annotations

import json
import logging
import warnings
from pathlib import Path
from typing import Iterable, Sequence

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import SplineTransformer, StandardScaler

try:
    import statsmodels.api as sm
except ImportError:  # Pipeline remains usable without explanatory HAC output.
    sm = None

warnings.filterwarnings("ignore", category=FutureWarning)

# -----------------------------------------------------------------------------
# Week 1 - Scope and reproducibility configuration
# -----------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent
RAW_DIR = ROOT / "data" / "raw"
OUTPUT_ROOT = ROOT / "outputs"
DATA_DIR = OUTPUT_ROOT / "data"
TABLE_DIR = OUTPUT_ROOT / "tables"
FIGURE_DIR = OUTPUT_ROOT / "figures"
MODEL_DIR = OUTPUT_ROOT / "models"
LOG_DIR = OUTPUT_ROOT / "logs"

for directory in [OUTPUT_ROOT, DATA_DIR, TABLE_DIR, FIGURE_DIR, MODEL_DIR, LOG_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

RANDOM_SEED = 42
TRAIN_FRACTION = 0.80
BOOTSTRAP_REPETITIONS = 2_000
REGION = "NSW1"

INPUT_CANDIDATES = {
    "pv": [
        "Rooftop PV Actual 2017-2026.xlsx",
        "Rooftop_PV_202501_to_202608_Combined.csv",
    ],
    "demand": [
        "Operational Demand 202408 - 202608.xlsx",
        "Operational_Demand_202501_to_202608_Combined.csv",
    ],
    "forecast": [
        "Operational Demand Forecast 202408 - 202608.xlsx",
        "Operational_Demand_Forecast_202408_to_202608_Combined.csv",
    ],
    "combined_weather": ["Sydney_Airport_Weather_202508_to_202608_Combined.csv"],
    "max_temp": ["Daily Max Temperature.xlsx"],
    "min_temp": ["Daily Min Temperature.xlsx"],
    "rainfall": ["Daily Rainfall.xlsx"],
    "solar": [
        "Daily Solar Exposure.xlsx",
        "Sydney Airport North Daily Solar Exposure 2025.csv",
        "Sydney Airport North Daily Solar Exposure 2026.csv",
    ],
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "weeks1_to_6_pipeline.log", mode="w"),
        logging.StreamHandler(),
    ],
)
LOGGER = logging.getLogger(__name__)


def locate_file(candidates: Sequence[str], required: bool = True) -> Path | None:
    """Resolve an input from data/raw or the repository root."""
    for folder in [RAW_DIR, ROOT]:
        for name in candidates:
            path = folder / name
            if path.exists():
                return path
    if required:
        raise FileNotFoundError(
            "Could not locate any of: " + ", ".join(candidates)
            + ". Add the file to data/raw or the repository root."
        )
    return None


def read_table(path: Path) -> pd.DataFrame:
    """Read CSV/XLSX with explicit engines and low-memory protection."""
    if path.suffix.lower() in {".xlsx", ".xls"}:
        return pd.read_excel(path, sheet_name=0, engine="openpyxl")
    return pd.read_csv(path, low_memory=False)


def clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Trim headers and standardise whitespace without hiding source meaning."""
    out = df.copy()
    out.columns = [
        str(column).strip().replace("\\_", "_").replace("\n", " ")
        for column in out.columns
    ]
    return out


def find_column(df: pd.DataFrame, candidates: Iterable[str], required: bool = True):
    """Find a source column case-insensitively from known alternatives."""
    lookup = {str(column).strip().upper(): column for column in df.columns}
    for candidate in candidates:
        if candidate.upper() in lookup:
            return lookup[candidate.upper()]
    if required:
        raise KeyError(f"Missing one of {list(candidates)}. Found: {list(df.columns)}")
    return None


def numeric_series(series: pd.Series) -> pd.Series:
    """Convert cells to numbers after removing common thousands separators."""
    return pd.to_numeric(series.astype(str).str.replace(",", "", regex=False), errors="coerce")


def parse_datetime(series: pd.Series) -> pd.Series:
    """Parse mixed Australian date strings and Excel datetime values."""
    return pd.to_datetime(series, dayfirst=True, errors="coerce")


# -----------------------------------------------------------------------------
# Week 2 - Data acquisition and cleaning
# -----------------------------------------------------------------------------
def load_aemo_actuals() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load, filter and consolidate AEMO rooftop PV and demand actuals."""
    pv_path = locate_file(INPUT_CANDIDATES["pv"])
    demand_path = locate_file(INPUT_CANDIDATES["demand"])
    LOGGER.info("Loading PV actuals: %s", pv_path.name)
    LOGGER.info("Loading demand actuals: %s", demand_path.name)

    pv = clean_columns(read_table(pv_path))
    demand = clean_columns(read_table(demand_path))

    pv_region = find_column(pv, ["REGIONID", "REGION_ID"])
    pv_time = find_column(pv, ["INTERVAL_DATETIME", "DATETIME"])
    pv_value = find_column(pv, ["POWER_MW", "POWER", "ROOFTOP_PV_MW"])
    pv_type = find_column(pv, ["TYPE"], required=False)
    pv_quality = find_column(pv, ["QUALITY_INDICATOR", "QUALITY"], required=False)

    pv = pv[pv[pv_region].astype(str).str.upper().eq(REGION)].copy()
    if pv_type is not None:
        pv = pv[pv[pv_type].astype(str).str.upper().eq("MEASUREMENT")].copy()

    pv_clean = pd.DataFrame(
        {
            "DATETIME": parse_datetime(pv[pv_time]),
            "ROOFTOP_PV_MW": numeric_series(pv[pv_value]),
            "PV_QUALITY_INDICATOR": pv[pv_quality] if pv_quality else "",
        }
    ).dropna(subset=["DATETIME"])

    # Repeated timestamps can occur in historical extracts. Median consolidation
    # preserves one modelling value and SOURCE_RECORD_COUNT keeps the step auditable.
    pv_clean = (
        pv_clean.groupby("DATETIME", as_index=False)
        .agg(
            ROOFTOP_PV_MW=("ROOFTOP_PV_MW", "median"),
            PV_QUALITY_INDICATOR=("PV_QUALITY_INDICATOR", "first"),
            SOURCE_RECORD_COUNT=("ROOFTOP_PV_MW", "size"),
        )
        .sort_values("DATETIME")
    )

    dm_region = find_column(demand, ["REGIONID", "REGION_ID"])
    dm_time = find_column(demand, ["INTERVAL_DATETIME", "DATETIME"])
    dm_value = find_column(
        demand,
        ["OPERATIONAL_DEMAND", "OPERATIONALDEMAND", "OPERATIONAL_DEMAND_MW"],
    )
    dm_adjustment = find_column(demand, ["OPERATIONAL_DEMAND_ADJUSTMENT"], required=False)
    dm_wdr = find_column(demand, ["WDR_ESTIMATE"], required=False)

    demand = demand[demand[dm_region].astype(str).str.upper().eq(REGION)].copy()
    demand_clean = pd.DataFrame(
        {
            "DATETIME": parse_datetime(demand[dm_time]),
            "OPERATIONAL_DEMAND_MW": numeric_series(demand[dm_value]),
            "OPERATIONAL_DEMAND_ADJUSTMENT": (
                numeric_series(demand[dm_adjustment]) if dm_adjustment else np.nan
            ),
            "WDR_ESTIMATE": numeric_series(demand[dm_wdr]) if dm_wdr else np.nan,
        }
    ).dropna(subset=["DATETIME"])
    demand_clean = (
        demand_clean.groupby("DATETIME", as_index=False)
        .median(numeric_only=True)
        .sort_values("DATETIME")
    )

    pv_clean.to_csv(DATA_DIR / "rooftop_pv_actual_clean.csv", index=False)
    demand_clean.to_csv(DATA_DIR / "operational_demand_actual_clean.csv", index=False)
    return pv_clean, demand_clean


def load_aemo_forecast() -> pd.DataFrame:
    """Load POE50 forecasts and retain the latest valid pre-interval vintage."""
    forecast_path = locate_file(INPUT_CANDIDATES["forecast"])
    LOGGER.info("Loading AEMO demand forecast: %s", forecast_path.name)
    forecast = clean_columns(read_table(forecast_path))

    region_col = find_column(forecast, ["REGIONID", "REGION_ID"])
    interval_col = find_column(forecast, ["INTERVAL_DATETIME", "DATETIME"])
    version_col = find_column(forecast, ["VERSION_DATETIME", "LOAD_DATE"])
    poe50_col = find_column(
        forecast,
        ["DEMAND_FORECAST_POE50", "POE50", "AEMO_POE50_MW"],
    )

    forecast = forecast[forecast[region_col].astype(str).str.upper().eq(REGION)].copy()
    clean = pd.DataFrame(
        {
            "DATETIME": parse_datetime(forecast[interval_col]),
            "VERSION_DATETIME": parse_datetime(forecast[version_col]),
            "AEMO_POE50_MW": numeric_series(forecast[poe50_col]),
        }
    ).dropna(subset=["DATETIME", "VERSION_DATETIME", "AEMO_POE50_MW"])

    clean["FORECAST_HORIZON_MINUTES"] = (
        clean["DATETIME"] - clean["VERSION_DATETIME"]
    ).dt.total_seconds() / 60
    clean = clean[clean["FORECAST_HORIZON_MINUTES"] > 0].copy()
    clean = (
        clean.sort_values(["DATETIME", "VERSION_DATETIME"])
        .groupby("DATETIME", as_index=False)
        .tail(1)
        .sort_values("DATETIME")
    )
    clean.to_csv(DATA_DIR / "operational_demand_forecast_clean.csv", index=False)
    return clean


def _load_single_daily_weather(path: Path, output_name: str) -> pd.DataFrame:
    """Read one BoM daily workbook and infer its date and measurement fields."""
    raw = clean_columns(read_table(path))
    date_col = find_column(raw, ["DATE"], required=False)
    if date_col is not None:
        dates = parse_datetime(raw[date_col]).dt.normalize()
    else:
        year = find_column(raw, ["YEAR"])
        month = find_column(raw, ["MONTH"])
        day = find_column(raw, ["DAY"])
        dates = pd.to_datetime(
            dict(year=numeric_series(raw[year]), month=numeric_series(raw[month]), day=numeric_series(raw[day])),
            errors="coerce",
        )

    keywords = {
        "MAX_TEMP_C": ["MAXIMUM TEMPERATURE", "MAX TEMP"],
        "MIN_TEMP_C": ["MINIMUM TEMPERATURE", "MIN TEMP"],
        "RAINFALL_MM": ["RAINFALL"],
        "SOLAR_EXPOSURE_MJ_M2": ["SOLAR EXPOSURE"],
    }[output_name]
    value_col = next(
        (column for column in raw.columns if any(word in str(column).upper() for word in keywords)),
        None,
    )
    if value_col is None:
        excluded = {date_col, "Year", "Month", "Day", "YEAR", "MONTH", "DAY"}
        numeric_candidates = [
            column for column in raw.columns
            if column not in excluded and numeric_series(raw[column]).notna().sum() > 0
        ]
        if not numeric_candidates:
            raise KeyError(f"No measurement column found in {path.name}")
        value_col = numeric_candidates[-1]

    out = pd.DataFrame({"DATE": dates, output_name: numeric_series(raw[value_col])})
    return out.dropna(subset=["DATE"]).groupby("DATE", as_index=False)[output_name].median()


def load_weather() -> pd.DataFrame:
    """Load combined legacy weather or the four final daily BoM files."""
    combined_path = locate_file(INPUT_CANDIDATES["combined_weather"], required=False)
    if combined_path is not None:
        LOGGER.info("Loading combined weather: %s", combined_path.name)
        weather = clean_columns(read_table(combined_path))
        date_col = find_column(weather, ["DATE", "Date"])
        weather["DATE"] = parse_datetime(weather[date_col]).dt.normalize()
        rename = {
            "Minimum temperature (°C)": "MIN_TEMP_C",
            "Maximum temperature (°C)": "MAX_TEMP_C",
            "Rainfall (mm)": "RAINFALL_MM",
            "Sunshine (hours)": "SUNSHINE_HOURS",
            "9am relative humidity (%)": "RH_9AM_PCT",
            "9am cloud amount (oktas)": "CLOUD_9AM_OKTAS",
            "3pm relative humidity (%)": "RH_3PM_PCT",
            "3pm cloud amount (oktas)": "CLOUD_3PM_OKTAS",
        }
        keep = ["DATE"] + [column for column in rename if column in weather.columns]
        weather = weather[keep].rename(columns=rename).drop_duplicates("DATE")
    else:
        LOGGER.info("Loading final separate daily weather workbooks")
        weather = _load_single_daily_weather(
            locate_file(INPUT_CANDIDATES["max_temp"]), "MAX_TEMP_C"
        )
        for key, output_name in [
            ("min_temp", "MIN_TEMP_C"),
            ("rainfall", "RAINFALL_MM"),
            ("solar", "SOLAR_EXPOSURE_MJ_M2"),
        ]:
            part = _load_single_daily_weather(locate_file(INPUT_CANDIDATES[key]), output_name)
            weather = weather.merge(part, on="DATE", how="outer")
        weather = weather.sort_values("DATE")

    # Legacy combined file keeps solar exposure in separate annual files.
    if "SOLAR_EXPOSURE_MJ_M2" not in weather.columns:
        solar_paths = []
        for name in INPUT_CANDIDATES["solar"]:
            path = locate_file([name], required=False)
            if path is not None:
                solar_paths.append(path)
        if solar_paths:
            solar = pd.concat(
                [_load_single_daily_weather(path, "SOLAR_EXPOSURE_MJ_M2") for path in solar_paths],
                ignore_index=True,
            ).groupby("DATE", as_index=False).SOLAR_EXPOSURE_MJ_M2.median()
            weather = weather.merge(solar, on="DATE", how="left")

    weather.to_csv(DATA_DIR / "weather_daily_clean.csv", index=False)
    return weather


# -----------------------------------------------------------------------------
# Week 3-4 - Data quality, EDA and feature engineering
# -----------------------------------------------------------------------------
def add_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create only lagged/calendar features available before the target interval."""
    out = df.sort_values("DATETIME").reset_index(drop=True).copy()
    dt = out["DATETIME"]
    out["DATE"] = dt.dt.normalize()
    out["YEAR"] = dt.dt.year
    out["MONTH"] = dt.dt.month
    out["MONTH_NAME"] = dt.dt.month_name()
    out["QUARTER"] = "Q" + dt.dt.quarter.astype(str)
    out["DAY_OF_WEEK"] = dt.dt.day_name()
    out["WEEKEND_FLAG"] = (dt.dt.dayofweek >= 5).astype(int)
    out["HOUR"] = dt.dt.hour
    out["MINUTE"] = dt.dt.minute
    out["HALF_HOUR_SLOT"] = dt.dt.strftime("%H:%M")
    out["SEASON"] = out["MONTH"].map(
        {
            12: "Summer", 1: "Summer", 2: "Summer",
            3: "Autumn", 4: "Autumn", 5: "Autumn",
            6: "Winter", 7: "Winter", 8: "Winter",
            9: "Spring", 10: "Spring", 11: "Spring",
        }
    )

    for lag in [1, 2, 4, 48, 336]:
        out[f"PV_LAG_{lag}"] = out["ROOFTOP_PV_MW"].shift(lag)
        out[f"DEMAND_LAG_{lag}"] = out["OPERATIONAL_DEMAND_MW"].shift(lag)

    out["DELTA_PV_MW"] = out["ROOFTOP_PV_MW"].diff()
    out["DELTA_DEMAND_MW"] = out["OPERATIONAL_DEMAND_MW"].diff()
    out["TARGET_DELTA_DEMAND_MW"] = (
        out["OPERATIONAL_DEMAND_MW"].shift(-1) - out["OPERATIONAL_DEMAND_MW"]
    )
    out["AEMO_DELTA_FORECAST_MW"] = (
        out["AEMO_POE50_MW"] - out["OPERATIONAL_DEMAND_MW"]
    )
    out["PV_RAMP_DIRECTION"] = np.select(
        [out["DELTA_PV_MW"] > 0, out["DELTA_PV_MW"] < 0],
        ["Increase", "Decrease"],
        default="No change",
    )
    out.loc[out["DELTA_PV_MW"].isna(), "PV_RAMP_DIRECTION"] = np.nan

    holidays = {
        "2025-10-06": "Labour Day",
        "2025-12-25": "Christmas Day",
        "2025-12-26": "Boxing Day",
        "2026-01-01": "New Year's Day",
        "2026-01-26": "Australia Day",
        "2026-04-03": "Good Friday",
        "2026-04-04": "Easter Saturday",
        "2026-04-05": "Easter Sunday",
        "2026-04-06": "Easter Monday",
        "2026-04-25": "Anzac Day",
        "2026-04-27": "Additional public holiday for Anzac Day",
        "2026-06-08": "King's Birthday",
    }
    key = dt.dt.strftime("%Y-%m-%d")
    out["NSW_PUBLIC_HOLIDAY_FLAG"] = key.isin(holidays).astype(int)
    out["NSW_PUBLIC_HOLIDAY_NAME"] = key.map(holidays).fillna("")
    return out


def validate_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """Create the coordinator-facing data-quality summary."""
    expected = pd.date_range(df.DATETIME.min(), df.DATETIME.max(), freq="30min")
    metrics = {
        "Rows": len(df),
        "Start": df.DATETIME.min(),
        "End": df.DATETIME.max(),
        "Duplicate timestamps": int(df.DATETIME.duplicated().sum()),
        "Missing half-hours": len(expected.difference(pd.DatetimeIndex(df.DATETIME))),
        "Repeated source PV timestamps consolidated": int((df.SOURCE_RECORD_COUNT > 1).sum()),
        "Missing PV": int(df.ROOFTOP_PV_MW.isna().sum()),
        "Missing demand": int(df.OPERATIONAL_DEMAND_MW.isna().sum()),
        "Missing AEMO forecast": int(df.AEMO_POE50_MW.isna().sum()),
    }
    for column in ["MAX_TEMP_C", "MIN_TEMP_C", "RAINFALL_MM", "SOLAR_EXPOSURE_MJ_M2"]:
        if column in df.columns:
            metrics[f"Missing {column}"] = int(df[column].isna().sum())
    return pd.DataFrame({"Metric": metrics.keys(), "Value": metrics.values()})


def save_figure(filename: str) -> None:
    plt.tight_layout()
    plt.savefig(FIGURE_DIR / filename, dpi=200, bbox_inches="tight")
    plt.close()


def create_eda(df: pd.DataFrame) -> None:
    """Write Week 3 descriptive tables and report-ready EDA graphs."""
    numeric_columns = [
        column for column in [
            "ROOFTOP_PV_MW", "OPERATIONAL_DEMAND_MW", "DELTA_PV_MW",
            "DELTA_DEMAND_MW", "MAX_TEMP_C", "MIN_TEMP_C", "RAINFALL_MM",
            "SOLAR_EXPOSURE_MJ_M2", "SUNSHINE_HOURS", "CLOUD_9AM_OKTAS",
            "CLOUD_3PM_OKTAS",
        ] if column in df.columns
    ]
    df[numeric_columns].describe().T.to_csv(TABLE_DIR / "descriptive_statistics.csv")
    correlations = df[numeric_columns].corr()
    correlations.to_csv(TABLE_DIR / "correlation_matrix.csv")

    monthly = (
        df.set_index("DATETIME")
        .resample("MS")
        .agg(
            Avg_PV_MW=("ROOFTOP_PV_MW", "mean"),
            Avg_Demand_MW=("OPERATIONAL_DEMAND_MW", "mean"),
        )
        .reset_index()
    )
    monthly.to_csv(TABLE_DIR / "monthly_summary.csv", index=False)

    plt.figure(figsize=(9, 5))
    plt.hist(np.log1p(df["ROOFTOP_PV_MW"].clip(lower=0).dropna()), bins=60)
    plt.title("Distribution of log(1 + NSW1 rooftop PV)")
    plt.xlabel("log(1 + MW)")
    plt.ylabel("Half-hour intervals")
    save_figure("figure_01_log1p_pv_distribution.png")

    annual = df.groupby("YEAR", as_index=False).agg(Avg_PV_MW=("ROOFTOP_PV_MW", "mean"))
    annual.to_csv(TABLE_DIR / "annual_pv_growth.csv", index=False)
    plt.figure(figsize=(9, 5))
    plt.plot(annual.YEAR, annual.Avg_PV_MW, marker="o")
    plt.title("Average NSW1 rooftop PV by year")
    plt.xlabel("Year")
    plt.ylabel("Average rooftop PV (MW)")
    save_figure("figure_02_pv_growth_by_year.png")

    intraday = df.groupby(["SEASON", "HOUR"], as_index=False)[
        ["ROOFTOP_PV_MW", "OPERATIONAL_DEMAND_MW"]
    ].mean()
    intraday.to_csv(TABLE_DIR / "seasonal_intraday_profiles.csv", index=False)
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    for season, subset in intraday.groupby("SEASON"):
        axes[0].plot(subset.HOUR, subset.ROOFTOP_PV_MW, label=season)
        axes[1].plot(subset.HOUR, subset.OPERATIONAL_DEMAND_MW, label=season)
    axes[0].set(title="Rooftop PV profile", xlabel="Hour", ylabel="MW")
    axes[1].set(title="Operational demand profile", xlabel="Hour", ylabel="MW")
    axes[1].legend()
    save_figure("figure_03_seasonal_intraday_profiles.png")

    plt.figure(figsize=(9, 7))
    plt.imshow(correlations, cmap="coolwarm", vmin=-1, vmax=1)
    plt.xticks(range(len(correlations)), correlations.columns, rotation=80)
    plt.yticks(range(len(correlations)), correlations.columns)
    plt.colorbar(label="Pearson correlation")
    plt.title("Correlation matrix")
    save_figure("figure_04_correlation_matrix.png")

    valid = df.dropna(subset=["ROOFTOP_PV_MW", "DELTA_DEMAND_MW"]).copy()
    valid["PV_BIN"] = pd.qcut(valid.ROOFTOP_PV_MW, 20, duplicates="drop")
    binned = valid.groupby("PV_BIN", observed=True).agg(
        Mean_PV_MW=("ROOFTOP_PV_MW", "mean"),
        Mean_Demand_Change_MW=("DELTA_DEMAND_MW", "mean"),
    ).reset_index(drop=True)
    binned.to_csv(TABLE_DIR / "binned_pv_demand_relationship.csv", index=False)
    plt.figure(figsize=(9, 5))
    plt.plot(binned.Mean_PV_MW, binned.Mean_Demand_Change_MW, marker="o")
    plt.title("Binned non-linear rooftop PV-demand relationship")
    plt.xlabel("Mean rooftop PV (MW)")
    plt.ylabel("Mean half-hour demand change (MW)")
    save_figure("figure_05_binned_nonlinearity.png")

    plt.figure(figsize=(10, 5))
    df[["ROOFTOP_PV_MW", "OPERATIONAL_DEMAND_MW", "DELTA_PV_MW", "DELTA_DEMAND_MW"]].plot.box(ax=plt.gca(), rot=20)
    plt.title("Outlier screening boxplots")
    save_figure("figure_06_outlier_boxplots.png")


# -----------------------------------------------------------------------------
# Week 5 - Matched models with and without PV
# -----------------------------------------------------------------------------
def metric_row(model: str, specification: str, actual, prediction) -> dict:
    return {
        "Model": model,
        "Specification": specification,
        "MAE_MW": mean_absolute_error(actual, prediction),
        "RMSE_MW": mean_squared_error(actual, prediction) ** 0.5,
    }


def run_models(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Fit OLS, spline and tree specifications on one chronological split."""
    model_df = df.dropna(subset=["TARGET_DELTA_DEMAND_MW"]).sort_values("DATETIME").copy()
    split_index = int(len(model_df) * TRAIN_FRACTION)
    train = model_df.iloc[:split_index].copy()
    holdout = model_df.iloc[split_index:].copy()

    weather_features = [
        column for column in [
            "MAX_TEMP_C", "MIN_TEMP_C", "RAINFALL_MM", "SOLAR_EXPOSURE_MJ_M2",
            "SUNSHINE_HOURS", "RH_9AM_PCT", "RH_3PM_PCT",
            "CLOUD_9AM_OKTAS", "CLOUD_3PM_OKTAS",
        ] if column in model_df.columns
    ]
    base_features = [
        "DEMAND_LAG_1", "DEMAND_LAG_2", "DEMAND_LAG_4", "DELTA_DEMAND_MW",
        "HOUR", "MONTH", "WEEKEND_FLAG", "NSW_PUBLIC_HOLIDAY_FLAG",
    ] + weather_features
    pv_features = ["ROOFTOP_PV_MW", "PV_LAG_1", "PV_LAG_2", "PV_LAG_4", "DELTA_PV_MW"]

    model_builders = {
        "OLS": lambda: make_pipeline(
            SimpleImputer(strategy="median"), StandardScaler(), LinearRegression()
        ),
        "Spline": lambda: make_pipeline(
            SimpleImputer(strategy="median"),
            SplineTransformer(n_knots=5, degree=3),
            LinearRegression(),
        ),
        "Tree": lambda: make_pipeline(
            SimpleImputer(strategy="median"),
            HistGradientBoostingRegressor(
                max_iter=100,
                max_leaf_nodes=15,
                learning_rate=0.08,
                min_samples_leaf=30,
                l2_regularization=1.0,
                random_state=RANDOM_SEED,
            ),
        ),
    }

    results = []
    for model_name, builder in model_builders.items():
        for specification, features in [
            ("Without PV", base_features),
            ("With PV", base_features + pv_features),
        ]:
            model = builder()
            model.fit(train[features], train["TARGET_DELTA_DEMAND_MW"])
            prediction = model.predict(holdout[features])
            prediction_column = f"PRED_{model_name.upper()}_{specification.upper().replace(' ', '_')}"
            holdout[prediction_column] = prediction
            results.append(
                metric_row(model_name, specification, holdout.TARGET_DELTA_DEMAND_MW, prediction)
            )

    # Simple zero-change forecast is a transparent persistence benchmark.
    holdout["PRED_ZERO_CHANGE"] = 0.0
    results.append(
        metric_row("Persistence", "Zero demand change", holdout.TARGET_DELTA_DEMAND_MW, holdout.PRED_ZERO_CHANGE)
    )

    settings = {
        "random_seed": RANDOM_SEED,
        "train_fraction": TRAIN_FRACTION,
        "target": "TARGET_DELTA_DEMAND_MW",
        "base_features": base_features,
        "pv_features": pv_features,
        "holdout_start": str(holdout.DATETIME.min()),
        "holdout_end": str(holdout.DATETIME.max()),
    }
    (MODEL_DIR / "model_settings.json").write_text(json.dumps(settings, indent=2))

    # HAC OLS is explanatory only and is not labelled as the forecasting baseline.
    if sm is not None:
        hac_data = train[["TARGET_DELTA_DEMAND_MW"] + base_features + pv_features].copy()
        for column in base_features + pv_features:
            hac_data[column] = hac_data[column].fillna(hac_data[column].median())
        hac = sm.OLS(
            hac_data.TARGET_DELTA_DEMAND_MW,
            sm.add_constant(hac_data[base_features + pv_features]),
        ).fit(cov_type="HAC", cov_kwds={"maxlags": 48})
        pd.DataFrame(
            {
                "Coefficient": hac.params,
                "HAC_Standard_Error": hac.bse,
                "P_Value": hac.pvalues,
            }
        ).to_csv(MODEL_DIR / "ols_hac_coefficients.csv")

    metrics = pd.DataFrame(results)
    metrics.to_csv(TABLE_DIR / "model_metrics.csv", index=False)
    holdout.to_csv(DATA_DIR / "chronological_holdout_predictions.csv", index=False)
    return metrics, holdout


# -----------------------------------------------------------------------------
# Week 6 - AEMO benchmark, subgroup analysis and uncertainty
# -----------------------------------------------------------------------------
def run_week6_validation(metrics: pd.DataFrame, holdout: pd.DataFrame) -> None:
    """Produce final benchmark, time-block, seasonal, bootstrap and residual evidence."""
    actual = holdout["TARGET_DELTA_DEMAND_MW"]
    valid_aemo = holdout["AEMO_DELTA_FORECAST_MW"].notna()
    if valid_aemo.any():
        aemo = metric_row(
            "AEMO POE50",
            "Aligned pre-interval benchmark",
            actual[valid_aemo],
            holdout.loc[valid_aemo, "AEMO_DELTA_FORECAST_MW"],
        )
        metrics = pd.concat([metrics, pd.DataFrame([aemo])], ignore_index=True)
    metrics.to_csv(TABLE_DIR / "model_metrics_with_aemo.csv", index=False)

    labels = metrics["Model"] + " - " + metrics["Specification"]
    plt.figure(figsize=(12, 6))
    plt.bar(labels, metrics.MAE_MW)
    plt.ylabel("MAE (MW)")
    plt.title("Chronological holdout forecast comparison")
    plt.xticks(rotation=65, ha="right")
    save_figure("figure_07_model_and_aemo_benchmark.png")

    horizon = holdout["FORECAST_HORIZON_MINUTES"].dropna()
    if not horizon.empty:
        horizon.describe().to_csv(TABLE_DIR / "aemo_forecast_horizon_summary.csv")
        plt.figure(figsize=(9, 5))
        plt.hist(horizon, bins=50)
        plt.xlabel("Forecast horizon (minutes)")
        plt.ylabel("Intervals")
        plt.title("AEMO POE50 forecast horizon after vintage filtering")
        save_figure("figure_08_aemo_forecast_horizon.png")

    holdout["TIME_BLOCK"] = pd.cut(
        holdout.HOUR,
        bins=[-1, 5, 11, 17, 23],
        labels=["00:00-06:00", "06:00-12:00", "12:00-18:00", "18:00-24:00"],
    )

    def matched_tree_summary(group: pd.DataFrame) -> pd.Series:
        without_error = np.abs(
            group.TARGET_DELTA_DEMAND_MW - group.PRED_TREE_WITHOUT_PV
        )
        with_error = np.abs(group.TARGET_DELTA_DEMAND_MW - group.PRED_TREE_WITH_PV)
        return pd.Series(
            {
                "Rows": len(group),
                "MAE_Without_PV_MW": without_error.mean(),
                "MAE_With_PV_MW": with_error.mean(),
                "PV_Gain_MW": without_error.mean() - with_error.mean(),
            }
        )

    time_block = holdout.groupby("TIME_BLOCK", observed=True).apply(matched_tree_summary)
    time_block.to_csv(TABLE_DIR / "pv_gain_by_time_block.csv")
    plt.figure(figsize=(9, 5))
    time_block.PV_Gain_MW.plot.bar()
    plt.ylabel("Tree MAE reduction from PV (MW)")
    plt.title("Incremental PV value by time of day")
    save_figure("figure_09_pv_gain_by_time_block.png")

    seasonal = holdout.groupby("SEASON").apply(matched_tree_summary)
    seasonal.to_csv(TABLE_DIR / "pv_gain_by_season.csv")
    plt.figure(figsize=(9, 5))
    seasonal.PV_Gain_MW.plot.bar()
    plt.ylabel("Tree MAE reduction from PV (MW)")
    plt.title("Incremental PV value by season")
    save_figure("figure_10_pv_gain_by_season.png")

    holdout["DATE_ONLY"] = holdout.DATETIME.dt.date
    daily_gain = holdout.groupby("DATE_ONLY").apply(
        lambda group: np.abs(group.TARGET_DELTA_DEMAND_MW - group.PRED_TREE_WITHOUT_PV).mean()
        - np.abs(group.TARGET_DELTA_DEMAND_MW - group.PRED_TREE_WITH_PV).mean()
    )
    rng = np.random.default_rng(RANDOM_SEED)
    bootstrap = np.array(
        [rng.choice(daily_gain.to_numpy(), size=len(daily_gain), replace=True).mean()
         for _ in range(BOOTSTRAP_REPETITIONS)]
    )
    pd.DataFrame({"Bootstrap_PV_Gain_MW": bootstrap}).to_csv(
        TABLE_DIR / "paired_daily_bootstrap_pv_gain.csv", index=False
    )
    pd.DataFrame(
        {
            "Metric": ["Mean gain", "2.5 percentile", "97.5 percentile"],
            "Value_MW": [bootstrap.mean(), *np.quantile(bootstrap, [0.025, 0.975])],
        }
    ).to_csv(TABLE_DIR / "paired_daily_bootstrap_summary.csv", index=False)
    plt.figure(figsize=(9, 5))
    plt.hist(bootstrap, bins=45)
    plt.axvline(0, color="black", linewidth=1)
    plt.xlabel("Paired daily tree MAE reduction from PV (MW)")
    plt.ylabel("Bootstrap samples")
    plt.title("Paired daily bootstrap uncertainty")
    save_figure("figure_11_bootstrap_uncertainty.png")

    example = holdout.iloc[: 48 * 4].copy()
    plt.figure(figsize=(13, 5))
    plt.plot(example.DATETIME, example.TARGET_DELTA_DEMAND_MW, label="Observed")
    plt.plot(example.DATETIME, example.PRED_TREE_WITHOUT_PV, label="Tree without PV")
    plt.plot(example.DATETIME, example.PRED_TREE_WITH_PV, label="Tree with PV")
    plt.ylabel("Next-half-hour demand change (MW)")
    plt.title("Representative chronological holdout forecast")
    plt.legend()
    save_figure("figure_12_holdout_forecast_example.png")

    residual = holdout.TARGET_DELTA_DEMAND_MW - holdout.PRED_TREE_WITH_PV
    residual_summary = pd.DataFrame(
        {
            "Metric": ["Mean", "Standard deviation", "Median absolute residual"],
            "Value_MW": [residual.mean(), residual.std(), residual.abs().median()],
        }
    )
    residual_summary.to_csv(TABLE_DIR / "tree_residual_summary.csv", index=False)
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    axes[0].hist(residual, bins=60)
    axes[0].set(title="PV-enhanced tree residual distribution", xlabel="Residual (MW)")
    axes[1].plot(holdout.DATETIME.iloc[:500], residual.iloc[:500])
    axes[1].set(title="Residual sequence", ylabel="Residual (MW)")
    save_figure("figure_13_residual_diagnostics.png")


# -----------------------------------------------------------------------------
# Pipeline entry point
# -----------------------------------------------------------------------------
def main() -> None:
    LOGGER.info("Starting reproducible Weeks 1-6 workflow")
    pv, demand = load_aemo_actuals()
    forecast = load_aemo_forecast()
    weather = load_weather()

    core = pv.merge(demand, on="DATETIME", how="inner", validate="one_to_one")
    core = core.merge(forecast, on="DATETIME", how="left", validate="one_to_one")
    core["DATE"] = core.DATETIME.dt.normalize()
    combined = core.merge(weather, on="DATE", how="left", validate="many_to_one")
    modelling = add_features(combined)

    quality = validate_dataset(modelling)
    quality.to_csv(TABLE_DIR / "data_quality_summary.csv", index=False)
    modelling.to_csv(
        DATA_DIR / "NSW1_Historical_Modelling_Dataset_Weeks1_to_6.csv",
        index=False,
        date_format="%Y-%m-%d %H:%M:%S",
    )

    create_eda(modelling)
    metrics, holdout = run_models(modelling)
    run_week6_validation(metrics, holdout)

    manifest = []
    for path in sorted(OUTPUT_ROOT.rglob("*")):
        if path.is_file():
            manifest.append(
                {
                    "file": str(path.relative_to(ROOT)),
                    "bytes": path.stat().st_size,
                }
            )
    (OUTPUT_ROOT / "output_manifest.json").write_text(json.dumps(manifest, indent=2))
    LOGGER.info("Workflow complete. Generated %d output files.", len(manifest))


if __name__ == "__main__":
    main()
