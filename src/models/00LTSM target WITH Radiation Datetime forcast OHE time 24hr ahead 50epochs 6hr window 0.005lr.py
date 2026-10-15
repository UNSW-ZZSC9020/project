#LSTM

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import tensorflow as tf
from tensorflow import keras
from matplotlib.dates import MonthLocator, DateFormatter, YearLocator
from keras.models import Sequential, load_model
from keras.losses import MeanSquaredError
from keras.metrics import RootMeanSquaredError
from keras.layers import Dense, InputLayer, LSTM, Conv1D, MaxPooling1D
from keras.callbacks import ModelCheckpoint
from keras.optimizers import Adam
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error, mean_squared_error, r2_score


MODEL_NAME = "LSTM_OHE_Time_WITH_RADIATION_TEST"


##"C:\Group Project\ZZSC9020-group-A-main-1709\data\NSW\nsw_train.csv"

# load dataset
train = pd.read_csv('C:/Group Project/ZZSC9020-group-A-main-1709/data/NSW/nsw_train.csv')
validate = pd.read_csv('C:/Group Project/ZZSC9020-group-A-main-1709/data/NSW/nsw_validation.csv')
test = pd.read_csv('C:/Group Project/ZZSC9020-group-A-main-1709/data/NSW/nsw_test.csv')


print(f"train_shape: {train.shape}")
print(f"test_shape: {validate.shape}")
print(f"test_shape: {test.shape}")

#SinCos Datetime - Cyclical time

train['DATETIME'] = pd.to_datetime(train['DATETIME'])
validate['DATETIME'] = pd.to_datetime(validate['DATETIME'])
test['DATETIME'] = pd.to_datetime(test['DATETIME'])


#Scale minmax

scaler = MinMaxScaler()

train_scaled = train.copy()
validate_scaled = validate.copy()
test_scaled = test.copy()

train_scaled["TOTALDEMAND"] = scaler.fit_transform(train[["TOTALDEMAND"]])

validate_scaled["TOTALDEMAND"] = scaler.transform(validate[["TOTALDEMAND"]])

test_scaled["TOTALDEMAND"] = scaler.transform(test[["TOTALDEMAND"]])

#Define Features (#yay pre one hot encoding!)

feature_cols = ['TOTALDEMAND', 'TEMPERATURE', 'radiation', "radiation_day_before", "forecast_closest", "forecast_12hr_prior", "forecast_dayprior",
                'hour_0', 'hour_1', 'hour_2', 'hour_3', 'hour_4', 'hour_5',
                'hour_6', 'hour_7', 'hour_8', 'hour_9', 'hour_10', 'hour_11',
                'hour_12', 'hour_13', 'hour_14', 'hour_15', 'hour_16', 'hour_17',
                'hour_18', 'hour_19', 'hour_20', 'hour_21', 'hour_22', 'hour_23',
                 'day_Monday', 'day_Tuesday', 'day_Wednesday', 'day_Thursday',
                 'day_Friday', 'day_Saturday', 'day_Sunday',
                 'month_1', 'month_2', 'month_3', 'month_4', 'month_5', 'month_6',
                 'month_7', 'month_8', 'month_9', 'month_10', 'month_11', 'month_12'
                 ]



horizon = 48 #(1 day horizon)

#Define window - window size 12 (previous 6 hours)

def df_windowed(df, feature_cols, target_col, window_size=8):
    data=df[feature_cols].values.astype('float32')
    target = df[target_col].values.astype('float32')
    X, y = [], []
    for i in range(len(data) - window_size - horizon + 1):
        X.append(data[i:i+window_size])
        y.append(target[i+window_size + horizon - 1])
    X = np.array(X) # (samples, timesteps, features)
    y = np.array(y)
    return X, y

window = 12 #30min timesteps use previous 6hrs of data

X_train, y_train = df_windowed(train_scaled, feature_cols, 'TOTALDEMAND', window)

X_val, y_val = df_windowed(validate_scaled, feature_cols, 'TOTALDEMAND', window)

x_test, y_test = df_windowed(test_scaled, feature_cols, 'TOTALDEMAND', window)


validate['DATETIME'] = pd.to_datetime(validate['DATETIME'])
val_dates = validate['DATETIME'].values[window+horizon-1:]

test['DATETIME'] = pd.to_datetime(test['DATETIME'])
test_dates = test['DATETIME'].values[window+horizon-1:]

model = Sequential([
    InputLayer(input_shape=(window, len(feature_cols))),
    LSTM(64),       #64 hidden units (h_t/c_t size --> memory capacity)
    Dense(32, activation='relu'), #summary and decision maker
    Dense(1)    #regression output
])

model.summary()

#Compile

model.compile(
    loss=MeanSquaredError(),
    optimizer=Adam(learning_rate=0.005),
    metrics=[RootMeanSquaredError()]
)

cp = ModelCheckpoint('best_model.keras', save_best_only=True)

history = model.fit(
    X_train, y_train,
    validation_data=(X_val, y_val),
    epochs=50,
    batch_size=32,
    callbacks=[cp]
)

best_model = load_model('best_model.keras')

val_predictions = best_model.predict(X_val).flatten()
test_predictions = best_model.predict(x_test).flatten()

#descale

y_val_unscale = scaler.inverse_transform(y_val.reshape(-1, 1)).flatten()
val_predictions_unscale = scaler.inverse_transform(val_predictions.reshape(-1, 1)).flatten()

y_test_unscale = scaler.inverse_transform(y_test.reshape(-1, 1)).flatten()
test_predictions_unscale = scaler.inverse_transform(test_predictions.reshape(-1, 1)).flatten()


#Save evaluation results

def evaluate(y_true, y_pred, model_name):
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mae = mean_absolute_error(y_true, y_pred)
    mape = mean_absolute_percentage_error(y_true, y_pred) * 100
    r2 = r2_score(y_true, y_pred)
    metrics = {"model": model_name, "rmse": rmse, "mae": mae, "mape_pct": mape, "r2": r2}
    print(metrics)
    return metrics

val_metrics = evaluate(y_val_unscale, val_predictions_unscale, f"{MODEL_NAME}_val")
test_metrics = evaluate(y_test_unscale, test_predictions_unscale, f"{MODEL_NAME}_test")

#save trained model as the trainted model so i know where the hell to find it. 

model.save("C:/Group Project/LTSM MODELS/trained_{MODEL_NAME}.keras")


# save prediction performance

results = Path('C:/Group Project/LTSM MODELS/results')
results.mkdir(parents=True, exist_ok=True)

pd.Series(val_predictions_unscale, index=val_dates, name=MODEL_NAME).to_csv(results / f"{MODEL_NAME}_VAL_predictions.csv")
pd.Series(test_predictions_unscale, index=test_dates, name=MODEL_NAME).to_csv(results / f"{MODEL_NAME}_TEST_predictions.csv")



#Pretty graphs

    # Validate Demand

plt.figure(figsize=(14, 5))
plt.plot(val_dates, y_val_unscale, label='Actual', color='#00FFFF')
plt.plot(val_dates, val_predictions_unscale, label='Predicted', color='#FF00FF', alpha=0.5)
plt.title(label='Actual vs Predicted Energy Demand')
plt.xlabel(xlabel='time')
plt.ylabel(ylabel='energy demand')
plt.legend()
plt.show()

    #Residual Plot

residuals = y_val_unscale - val_predictions_unscale

plt.figure(figsize=(14, 5))
plt.plot(val_dates, residuals, color='#00FFFF', alpha=0.7)
plt.axhline(0, color='red', linewidth=1, linestyle='--')
plt.title(label='Residuals (Actual - Predicted) Over Time')
plt.xlabel(xlabel='time')
plt.ylabel(ylabel='error (MW)')
plt.show()

    #pred actual scatter

plt.figure(figsize=(7, 7))
plt.scatter(y_val_unscale, val_predictions_unscale, color='#FF00FF', alpha=0.4, s=10)
lims = [min(y_val_unscale.min(), val_predictions_unscale.min()),
        max(y_val_unscale.max(), val_predictions_unscale.max())]
plt.plot(lims, lims, linewidth=1, linestyle='--')
plt.title(label='Predicted vs Actual')
plt.xlabel(xlabel='actual energy demand')
plt.ylabel(ylabel='predicted energy demand')
plt.show()

    #Error dist hist

plt.figure(figsize=(8, 5))
plt.hist(residuals, bins=50, color='#00FFFF', alpha=0.7)
plt.axvline(0, color='black', linewidth=1, linestyle='--')
plt.title(label='Distribution of Prediction Errors')
plt.xlabel(xlabel='error (MW)')
plt.ylabel(ylabel='count')
plt.show()


#whats going on in the seasons bro?

val_seasons = validate['season'].values[window+horizon- 1:]

season_results = pd.DataFrame({
    'DATETIME': val_dates,
    'season': val_seasons,
    'actual': y_val_unscale,
    'predicted': val_predictions_unscale
})

season_results['error'] = (season_results['actual'] -season_results['predicted'])
season_results['absolute_error'] = np.abs(season_results['error'])
season_results['percentage_error'] = (season_results['absolute_error']/ season_results['actual'])*100

season_summary = []

for season_name, group in season_results.groupby('season'):
    rmse = np.sqrt(mean_squared_error(group['actual'], group['predicted']))
    mae = mean_absolute_error(group['actual'], group['predicted'])
    mape = mean_absolute_percentage_error(group['actual'], group['predicted'])
    r2 = r2_score(group['actual'], group['predicted'])
    bias = np.mean(group['actual'] - group['predicted']) 

    season_summary.append({
        'season': season_name,
        'actual_mean': group['actual'].mean(),
        'predicted_mean': group['predicted'].mean(),
        'RMSE': rmse,
        'MAE': mae,
        'MAPE': mape,
        'R^2': r2,
        'bias': bias
})

season_summary = pd.DataFrame(season_summary)

season_order = ['summer', 'autumn', 'winter', 'spring']

season_summary['season'] = pd.Categorical(season_summary['season'], categories=season_order, ordered=True)

season_summary = season_summary.sort_values('season')

season_summary.to_csv(results / f"Whats_up_with_seasons.csv")
    
    
#how much power do kids need?

val_school_term = validate['is_school_term'].values[window+horizon-1:]

holiday_results = pd.DataFrame({
    'DATETIME': val_dates,
        'is_school_term': val_school_term,
        'actual': y_val_unscale,
        'predicted': val_predictions_unscale
})

holiday_summary = []

for freedom_name, group in holiday_results.groupby('is_school_term'):
    rmse = np.sqrt(mean_squared_error(group['actual'], group['predicted']))
    mae = mean_absolute_error(group['actual'], group['predicted'])
    mape = mean_absolute_percentage_error(group['actual'], group['predicted'])
    r2 = r2_score(group['actual'], group['predicted'])
    bias = np.mean(group['actual'] - group['predicted'])

    holiday_summary.append({
        'is_school_term': freedom_name,
        'actual_mean': group['actual'].mean(),
        'predicted_mean': group['predicted'].mean(),
        'RMSE': rmse,
        'MAE': mae,
        'MAPE_pct': mape,
        'R2': r2,
        'bias_MW': bias
    })

holiday_summary = pd.DataFrame(holiday_summary)

holiday_summary.to_csv(results /f"WHY_DO_KIDS_LEAVE_THE_LIGHTS_ON.csv", index=False)