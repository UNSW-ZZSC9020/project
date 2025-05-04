import pandas as pd
import numpy as np
from sklearn.model_selection import RandomizedSearchCV, TimeSeriesSplit
from sklearn.metrics import mean_squared_error, mean_absolute_percentage_error
import xgboost as xgb
import shap
import matplotlib.pyplot as plt

# Load and preprocess
df = pd.read_csv("C:/Users/nmutt/OneDrive/Documents/Masters/combined_data_new.csv")
df = df.loc[df.Temperature.notna()]
df = df[(df['period_id'] == 24)]
df['date_time_future'] = pd.to_datetime(df['date_time_future'], errors='coerce')
df = df.drop_duplicates(subset='date_time_future')
period_id = 24

df.date_time_current = pd.to_datetime(df.date_time_current, format = "%Y-%m-%d %H:%M:%S")
df.date_time_future = pd.to_datetime(df.date_time_future, format = "%Y-%m-%d %H:%M:%S")
df.date_time_current_rounded = pd.to_datetime(df.date_time_current_rounded, format = "%Y-%m-%d %H:%M:%S")

df["forecast_interval"] = df.date_time_future - df.date_time_current_rounded
df["forecast_error"] = df.total_demand - df.forecast_demand
df["forecast_error_relative"] = df.forecast_error/df.total_demand

df["date_time_future_hour"] = df.date_time_future.dt.hour

# Calculate forecast error and lag features
df['forecast_error'] = df['forecast_demand'] - df['total_demand']
df['24hrpreverrors'] = df['forecast_error'].shift(24)
df['48hrpreverrors'] = df['forecast_error'].shift(48)
df['7daypreverrors'] = df['forecast_error'].shift(24 * 7)
df['14daypreverrors'] = df['forecast_error'].shift(24 * 14)
# Time-based features
df["Hour"] = df.date_time_future.dt.hour
df["MonthNumb"] = df.date_time_future.dt.month
df["Day of week"] = df.date_time_future.dt.dayofweek  # Monday = 0, Sunday = 6

df = df.dropna()



# Encode Hour as cyclic features
df["hour_sin"] = np.sin(2 * np.pi * df["Hour"] / 24)
df["hour_cos"] = np.cos(2 * np.pi * df["Hour"] / 24)

# Interaction features
df["hour_x_temp"] = df["Hour"] * df["Temperature"]
df["month_x_temp"] = df["MonthNumb"] * df["Temperature"]
df["hour_x_forecast"] = df["Hour"] * df["forecast_demand"]
df["temp_x_forecast"] = df["Temperature"] * df["forecast_demand"]
df["temp_x_hour_sin"] = df["Temperature"] * df["hour_sin"]
df["temp_x_hour_cos"] = df["Temperature"] * df["hour_cos"]
df["forecast_x_hour_sin"] = df["forecast_demand"] * df["hour_sin"]
df["forecast_x_hour_cos"] = df["forecast_demand"] * df["hour_cos"]

features = [
    'Temperature', 'Humidity',
    'Wind_speed', 'Rain',
    'hour_sin', 'hour_cos',
    'MonthNumb', 'Day of week',
    'forecast_demand',
    '24hrpreverrors',
    '48hrpreverrors', '7daypreverrors', '14daypreverrors',
    #'hour_x_temp', 'month_x_temp', 'hour_x_forecast', 'temp_x_forecast',
    'temp_x_hour_sin', 'temp_x_hour_cos',
    #'forecast_x_hour_sin', 'forecast_x_hour_cos'
]

train_df = df[(df['date_time_future'] >= "2017-10-07 23:00:00") & (df['date_time_future'] <= "2020-03-05 23:00:00")]
test_df = df[(df['date_time_future'] > "2020-03-06 23:00:00") & (df['date_time_future'] <= "2021-03-17 23:00:00")]

# Prepare train/test split sets
X_train = train_df[features]
y_train = train_df['total_demand']
X_test = test_df[features]
y_test = test_df['total_demand']

# Baseline metrics from forecast and total demand
original_mse = mean_squared_error(y_test, test_df['forecast_demand'])
original_mape = mean_absolute_percentage_error(y_test, test_df['forecast_demand']) * 100

# Model creation, taken from fine tuning
xgb_model = xgb.XGBRegressor(objective='reg:squarederror', tree_method='hist', random_state=42)

model = xgb.XGBRegressor(
    objective='reg:squarederror',
    learning_rate=0.1,
    n_estimators=150,
    max_depth=3,
    subsample=0.8,
    random_state=42
)

model.fit(X_train, y_train)


# Predict and evaluate
y_pred = model.predict(X_test)
model_mse = mean_squared_error(y_test, y_pred)
model_mape = mean_absolute_percentage_error(y_test, y_pred) * 100

# Results
print(f"Original Forecast MSE: {original_mse:.2f}")
print(f"Original Forecast MAPE: {original_mape:.3f}%")
print(f"XGBoost Tuned Model MSE: {model_mse:.2f}")
print(f"XGBoost Tuned Model MAPE: {model_mape:.3f}%")


# Explain model predictions using SHAP
explainer = shap.Explainer(model, X_test)
shap_values = explainer(X_test)
shap_df = pd.DataFrame(shap_values.values, columns=X_test.columns)

# Forecast demand skews the plot so hide it
filtered_shap_values = shap_df.drop(columns=["forecast_demand"])
filtered_X_test = X_test.drop(columns=["forecast_demand"])

shap.summary_plot(
    filtered_shap_values.values,
    features=filtered_X_test,
    feature_names=filtered_X_test.columns
)

