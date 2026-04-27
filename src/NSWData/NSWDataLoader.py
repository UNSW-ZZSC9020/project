import pickle
import os
from pathlib import Path
import pickle
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from torch.utils.data import DataLoader
from NSWData.NSWDataSet import LSTMDataSet, TransformersDataSet
from ModelFiles.ModelConfigs import LSTMConfig, TransformersConfig

class NSWDataLoader:
    output_dir = ''
    
    def __init__(self, train_size: float = 0.7, val_size: float = 0.1):
        self._set_repo_path()
        self.train_size = train_size
        self.val_size = val_size

    def _set_repo_path(self) -> None:
        # try different approaches to get the repo path.
        # based on all our individual modelling notebooks.
        possible_paths = [
            os.path.join("capstone_project_GroupA", "data", "NSW"),
            str(Path.cwd().resolve().parents[0] / 'data' / 'NSW'),
            str(Path.cwd().resolve().parents[1] / 'data' / 'NSW'),
            str(Path.cwd().resolve().parents[2] / 'data' / 'NSW'),
            os.path.join(str(os.getcwd()), "data", "NSW"),
        ]
        for path in possible_paths:
            if os.path.exists(path):
                print(f'Found NSW data path: {path}')
                self.nsw_path = path
                NSWDataLoader.output_dir = os.path.join(self.nsw_path, "..", ".." ,"results")
                os.makedirs(NSWDataLoader.output_dir, exist_ok=True)
                return
        raise FileNotFoundError("NSW data path not found.")

    def load_data(self) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Loads the NSW dataset from CSV files. If the processed CSV files do not exist, it extracts and processes the raw data from zip files.
        Returns:
            A tuple containing six pandas DataFrames: train, validation, test, train_scaled, val_scaled, test_scaled.
        """
        for _ in range(3): # try 3 times to extract data if files are not found (to handle potential
            if not os.path.exists(os.path.join(self.nsw_path, "train.csv")) \
                or not os.path.exists(os.path.join(self.nsw_path, "validation.csv")) \
                or not os.path.exists(os.path.join(self.nsw_path, "test.csv")) \
                or not os.path.exists(os.path.join(self.nsw_path, "train_scaled.csv")) \
                or not os.path.exists(os.path.join(self.nsw_path, "val_scaled.csv")) \
                or not os.path.exists(os.path.join(self.nsw_path, "test_scaled.csv")) \
                or not os.path.exists(os.path.join(self.nsw_path, "scaler.pkl")):
                self.extract_data_from_zip()
            else:
                break
        train = pd.read_csv(os.path.join(self.nsw_path, "train.csv"), index_col=0, parse_dates=True)
        train.index.freq = '30min'
        validation = pd.read_csv(os.path.join(self.nsw_path, "validation.csv"), index_col=0, parse_dates=True)
        validation.index.freq = '30min'
        test = pd.read_csv(os.path.join(self.nsw_path, "test.csv"), index_col=0, parse_dates=True)
        test.index.freq = '30min'
        train_scaled = pd.read_csv(os.path.join(self.nsw_path, "train_scaled.csv"), index_col=0, parse_dates=True)
        train_scaled.index.freq = '30min'
        val_scaled = pd.read_csv(os.path.join(self.nsw_path, "val_scaled.csv"), index_col=0, parse_dates=True)
        val_scaled.index.freq = '30min'
        test_scaled = pd.read_csv(os.path.join(self.nsw_path, "test_scaled.csv"), index_col=0, parse_dates=True)
        test_scaled.index.freq = '30min'
        scaler = pickle.load(open(os.path.join(self.nsw_path, "scaler.pkl"), 'rb'))
        self.train = train
        self.validation = validation
        self.test = test
        self.train_scaled = train_scaled
        self.val_scaled = val_scaled
        self.test_scaled = test_scaled
        self.scaler = scaler
        return train, validation, test, train_scaled, val_scaled, test_scaled, scaler
    
    @classmethod
    def data_provider(cls, train_df, val_df, test_df, config, flag):
        
        if isinstance(config, TransformersConfig):
            Data = TransformersDataSet
        elif isinstance(config, LSTMConfig):
            Data = LSTMDataSet
        else:
            raise ValueError("Unsupported config type for data provider.")
        
        data_set = Data(
            config=config,
            train_df=train_df,
            val_df=val_df,
            test_df=test_df,
            flag=flag
        )
        print(flag, len(data_set))
        indices = None
        drop_last = True
        if flag == 'test' or flag == 'val':
            shuffle_flag = False
            step = getattr(config, 'eval_step_size', 1)

            if getattr(config, 'forecast_last_step_only', False):
                print("Config forecast_last_step_only is True: setting eval_step_size to 1 for evaluation loops to ensure we are evaluating on every single time step within the forecast horizon.")
                step = 1
            else:
                if config.eval_step_size > config.forecast_horizon:
                    print(f"Warning: eval_step_size {config.eval_step_size} is greater than forecast_horizon {config.forecast_horizon}. Setting eval_step_size to forecast_horizon.")
                step = min(config.eval_step_size, len(data_set), config.forecast_horizon)
            indices = list(range(0, len(data_set), step))
            drop_last = False
        else:
            shuffle_flag = True
        data_loader = DataLoader(
            data_set,
            batch_size=config.batch_size,
            sampler=indices if flag in ['test', 'val'] else None,
            shuffle=shuffle_flag,
            num_workers=config.num_workers,
            drop_last=drop_last)
        return data_set, data_loader
    
    def extract_data_from_zip(self) -> None:
        """This function performs the following steps:
        1. Reads the raw CSV files (demand, temperature, forecast) from the provided zip files.
        2. Converts date columns to datetime format and rounds to nearest 30 minutes.
        3. Processes the forecast data to pivot it into a wide format (P01, P02, ..., P48).
        4. Merges the demand, temperature, and forecast datasets on the DATETIME column.
        5. Cleans the merged dataset by reindexing to a complete 30-minute timeline and interpolating missing values.
        6. Computes error metrics (RMSE and TSE) for the forecasts.
        7. Adds lag features for demand (1 day ago, 1 week ago, 1 year ago).
        8. Splits the final dataset into train, validation, and test sets based on the specified proportions.
        9. Saves the processed datasets to CSV files for later use.
        """
        BASE_FEATURES = [
                "LOG_TOTALDEMAND",
                "TOTALDEMAND",
                "TEMPERATURE",
                "demand_1_day_ago",
                "demand_1_week_ago",
                "demand_1_year_ago",
                'TEMP_SQUARED',
                'HOUR',
                'DAYOFWEEK',
                'IS_WEEKEND',
                'IS_ABOVE_35_DEGREES'
            ]
        def _compute_merged_se(df_merged: pd.DataFrame) -> pd.DataFrame:
            p_cols = [f"P{i:02d}" for i in range(1, 49)]
            # Compute squared errors
            sq_errors = (df_merged[p_cols].sub(df_merged["TOTALDEMAND"], axis=0)) ** 2
            # (1) RMSE per datetime
            df_merged["RMSE_48"] = np.sqrt(sq_errors.mean(axis=1))
            # (2) Total squared error (sum of squared errors)
            df_merged["TSE_48"] = sq_errors.sum(axis=1)
            return df_merged

        def _clean_merged(df_merged: pd.DataFrame) -> pd.DataFrame:
            if "REGIONID" in df_merged.columns:
                df_merged = df_merged.drop(columns=["REGIONID"])

            # Create full 30-min time index
            full_index = pd.date_range(
                start=df_merged.index.min(),
                end=df_merged.index.max(),
                freq="30min"
            )

            # Reindex to full timeline
            df_merged = df_merged.reindex(full_index)
            df_merged.index.name = "DATETIME"

            # =========================================================
            # Handle missing values
            # =========================================================

            # Interpolate numeric columns using time method
            numeric_cols = ["TOTALDEMAND", "TEMPERATURE",
            "P01", "P02", "P03", "P04", "P05", "P06", "P07", "P08", "P09", "P10",
            "P11", "P12", "P13", "P14", "P15", "P16", "P17", "P18", "P19", "P20",
            "P21", "P22", "P23", "P24", "P25", "P26", "P27", "P28", "P29", "P30",
            "P31", "P32", "P33", "P34", "P35", "P36", "P37", "P38", "P39", "P40",
            "P41", "P42", "P43", "P44", "P45", "P46", "P47", "P48"]

            df_merged[numeric_cols] = (
                df_merged[numeric_cols]
                .interpolate(method="time")
                .ffill()
                .bfill()
            )
            assert not df_merged.isnull().sum().any(), "There are still missing values after interpolation!"
            return df_merged

        def _merge_datasets(df_demand: pd.DataFrame, df_temp: pd.DataFrame, df_forecast: pd.DataFrame) -> pd.DataFrame:
            df_merged = df_demand.merge(df_temp, on="DATETIME", how="inner")
            df_merged = df_merged.merge(df_forecast, on="DATETIME", how="left")
            df_merged = df_merged.sort_values("DATETIME") # Sort by time
            df_merged = df_merged.set_index("DATETIME")   # Set as time index
            df_merged = df_merged.asfreq("30min")         # Ensure frequency is set
            return df_merged

        def _process_forecast_data(df_forecast: pd.DataFrame, demand_start_date: pd.Timestamp, demand_end_date: pd.Timestamp) -> pd.DataFrame:
            # =========================================================
            # 1. Handle duplicates (same DATETIME + PERIODID)
            # =========================================================
            # Keep only PERIODID 1–48
            df_forecast_48 = df_forecast[df_forecast["PERIODID"].between(1, 48)].copy()
            # Keep only relevant columns
            df_forecast_48 = df_forecast_48[["TARGET_DATETIME", "PERIODID", "FORECASTDEMAND"]]
            # Rename TARGET_DATETIME → DATETIME
            df_forecast_48 = df_forecast_48.rename(columns={"TARGET_DATETIME": "DATETIME"})
            df_forecast_48 = (
                df_forecast_48
                .groupby(["DATETIME", "PERIODID"], as_index=False)["FORECASTDEMAND"]
                .mean()
            )

            # =========================================================
            # 2. Pivot to wide format → P01 ... P48
            # =========================================================
            df_forecast_wide = df_forecast_48.pivot(
                index="DATETIME",
                columns="PERIODID",
                values="FORECASTDEMAND"
            )
            df_forecast_wide.columns = [f"P{int(c):02d}" for c in df_forecast_wide.columns]
                    
            # =========================================================
            # 3. Build full datetime index (same as demand)
            # =========================================================
            forecast_index = pd.date_range(
                start=demand_start_date,
                end=demand_end_date,
                freq="30min"
            )
            df_forecast_wide = (
                df_forecast_wide
                .reindex(forecast_index)
            )
            df_forecast_wide.index.name = "DATETIME"

            # =========================================================
            # 4. Interpolate missing values (IMPORTANT)
            # =========================================================
            # Interpolate each horizon separately (column-wise)
            df_forecast_wide = df_forecast_wide.interpolate(method="time")
            # Fill any edge missing values
            df_forecast_wide = df_forecast_wide.ffill().bfill()

            # =========================================================
            # 5. Reset index
            # =========================================================
            df_forecast_wide = df_forecast_wide.reset_index()
            return df_forecast_wide

        def _convert_to_date_time(df_demand: pd.DataFrame, df_temp: pd.DataFrame, df_forecast: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
            df_demand["DATETIME"] = pd.to_datetime(df_demand["DATETIME"], dayfirst=True)
            df_temp["DATETIME"] = pd.to_datetime(df_temp["DATETIME"], dayfirst=True)
            df_forecast["LASTCHANGED"] = pd.to_datetime(df_forecast["LASTCHANGED"])
            df_forecast["TARGET_DATETIME"] = (
                df_forecast["LASTCHANGED"] + pd.to_timedelta(df_forecast["PERIODID"] * 30, unit="m")
            )
            return df_demand, df_temp, df_forecast

        def _round_df_to_30min(df_demand: pd.DataFrame, df_temp: pd.DataFrame, df_forecast: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
            df_demand["DATETIME"] = df_demand["DATETIME"].dt.floor("30min")
            df_temp["DATETIME"] = df_temp["DATETIME"].dt.floor("30min")
            df_forecast["TARGET_DATETIME"] = df_forecast["TARGET_DATETIME"].dt.floor("30min")
            return df_demand, df_temp, df_forecast

        def _add_features(df_merged: pd.DataFrame) -> pd.DataFrame:
            df_merged["demand_1_day_ago"] = df_merged["TOTALDEMAND"].shift(48)
            df_merged["demand_1_week_ago"] = df_merged["TOTALDEMAND"].shift(48 * 7)
            df_merged["demand_1_year_ago"] = df_merged["TOTALDEMAND"].shift(48 * 365)

            df_merged['TEMP_SQUARED'] = df_merged['TEMPERATURE'] ** 2
            df_merged['HOUR'] = df_merged.index.hour
            df_merged['DAYOFWEEK'] = df_merged.index.dayofweek
            df_merged['IS_WEEKEND'] = (df_merged['DAYOFWEEK'] >= 5).astype(int)
            df_merged['IS_ABOVE_35_DEGREES'] = (df_merged['TEMPERATURE'] > 35).astype(int)

            df_merged['LOG_TOTALDEMAND'] = np.log(df_merged['TOTALDEMAND'])
            df_model = df_merged.dropna(subset=BASE_FEATURES)
            non_forecast_cols = BASE_FEATURES + ["RMSE_48", "TSE_48"]
            df_model = df_model[BASE_FEATURES + df_model.columns.difference(non_forecast_cols).tolist() + ["RMSE_48", "TSE_48"]]
            return df_model
        
        def _train_val_test_split(df_model: pd.DataFrame, base_features: list[str]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
            n = len(df_model)
            train_size = int(n * self.train_size)
            val_size = int(n * self.val_size)
            train       = df_model.iloc[:train_size]
            validation  = df_model.iloc[train_size:train_size + val_size]
            test        = df_model.iloc[train_size + val_size:]
            scaler = StandardScaler()
            train_scaled = scaler.fit_transform(train)
            val_scaled = scaler.transform(validation)
            test_scaled = scaler.transform(test)
            train_scaled = pd.DataFrame(train_scaled, columns=train.columns, index=train.index)
            val_scaled = pd.DataFrame(val_scaled, columns=validation.columns, index=validation.index)
            test_scaled = pd.DataFrame(test_scaled, columns=test.columns, index=test.index)
            
            # we keep all columns in test for later comparison with forecasted demand
            return train[base_features], validation[base_features], test, train_scaled[base_features], val_scaled[base_features], test_scaled[base_features], scaler

        part_a = os.path.join(self.nsw_path, "forecastdemand_nsw.csv.zip.partaa")
        part_b = os.path.join(self.nsw_path, "forecastdemand_nsw.csv.zip.partab")
        forecast_zip = os.path.join(self.nsw_path, "forecastdemand_nsw.csv.zip")

        with open(forecast_zip, "wb") as outfile:
            for p in [part_a, part_b]:
                with open(p, "rb") as infile:
                    outfile.write(infile.read())

        df_demand = pd.read_csv(os.path.join(self.nsw_path, "totaldemand_nsw.csv.zip"))
        df_temp = pd.read_csv(os.path.join(self.nsw_path, "temperature_nsw.csv.zip"))
        df_forecast = pd.read_csv(os.path.join(self.nsw_path, "forecastdemand_nsw.csv.zip"))
        df_demand, df_temp, df_forecast = _convert_to_date_time(df_demand, df_temp, df_forecast)
        df_demand, df_temp, df_forecast = _round_df_to_30min(df_demand, df_temp, df_forecast)
        df_forecast = _process_forecast_data(df_forecast, df_demand["DATETIME"].min(), df_demand["DATETIME"].max())
        df_temp = df_temp.groupby("DATETIME", as_index=False)[["TEMPERATURE"]].mean()
        df_merged = _merge_datasets(df_demand, df_temp, df_forecast)
        df_merged = _clean_merged(df_merged)
        df_merged = _compute_merged_se(df_merged)
        df_model = _add_features(df_merged)

        n = len(df_model)
        base_features = BASE_FEATURES + ["RMSE_48", "TSE_48"]
        train, validation, test, train_scaled, val_scaled, test_scaled, scaler = _train_val_test_split(df_model, base_features)
        # Create folder if it does not exist
        os.makedirs(self.nsw_path, exist_ok=True)

        # Save main modelling dataset
        df_model[base_features].to_csv(os.path.join(self.nsw_path, "df_model.csv"))

        # Save train / validation / test splits
        train.to_csv(os.path.join(self.nsw_path, "train.csv"))
        validation.to_csv(os.path.join(self.nsw_path, "validation.csv"))
        test.to_csv(os.path.join(self.nsw_path, "test.csv"))

        # Save scaled datasets (used for LSTM and PatchTST models)
        train_scaled.to_csv(os.path.join(self.nsw_path, "train_scaled.csv"))
        val_scaled.to_csv(os.path.join(self.nsw_path, "val_scaled.csv"))
        test_scaled.to_csv(os.path.join(self.nsw_path, "test_scaled.csv"))

        # Save the scaler for later inverse transformation
        scaler_path = os.path.join(self.nsw_path, "scaler.pkl")
        with open(scaler_path, "wb") as f:
            pickle.dump(scaler, f)

        # Display confirmation
        print("Saved files to:", self.nsw_path)
        print(os.listdir(self.nsw_path))

        




if __name__ == "__main__":
    nsw_data_loader = NSWDataLoader()
    train, validation, test, train_scaled, val_scaled, test_scaled, scaler = nsw_data_loader.load_data()