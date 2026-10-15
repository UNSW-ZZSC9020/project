## What I have done

`final_modelling.ipynb` uses the supplied half-hourly NSW1 data from 1 August 2025 to 31 July 2026. I rebuild demand and PV changes in the notebook, then compare simple current-change models and next-half-hour forecasts.

For the detailed Week 3 outputs, use [initial_modelling.ipynb](initial_modelling.ipynb). It contains clearly labelled correlation, cross-correlation, regression, diagnostic, MAE and RMSE results.

The forecast inputs are deliberately limited to values assumed available before the target half-hour: earlier demand, earlier demand changes, earlier PV, earlier PV changes and calendar fields. Completed-day weather is not used for forecasts.

# What's left to do
### Timing information to collect

It's currently not clearly stated whether the previous half-hour demand data was available when the model needs to make a prediction. Without this, the notebook can only say that it **assumes** the previous half-hour's demand and PV were available. We cannot claim a real-time forecast.

If possible we should clarify when it was published, and record that in the data.

Other things to record/clarify:

- whether `DATETIME` is interval ending or interval starting
- the time zone and daylight-saving treatment
- the definition of each PV quality flag

## Possible Additional Modelling

The main priority is a **new period of data** that has not been used to choose the current models so that we can test how the model we select performs on new data.

We would need the same half-hourly NSW1 demand and rooftop PV coverage after the existing data, plus the information below.

### Minimum fields for the current notebook

The extended file needs these exact column names:

| Field | Use |
| --- | --- |
| `DATETIME` | Half-hour timestamp. Keep the source clock and interval convention unchanged. |
| `OPERATIONAL_DEMAND_MW` | Demand level used to calculate changes and demand history. |
| `ROOFTOP_PV_MW` | PV level used to calculate changes and PV history. |
| `MAX_TEMP_C` | Used only in the current-change OLS models. |
| `SOLAR_EXPOSURE_MJ_M2` | Used only in the current-change OLS models. |

We should also retain `PV_QUALITY_INDICATOR`, original source identifiers, source file names, download dates and any revision information. They are needed to check provenance even though the short final notebook does not currently use every one.



## Preparing the new data

1. Keep all source files unchanged.
2. Create a new combined CSV rather than overwriting `NSW1_Historical_Modelling_Dataset_Week3.csv`.
3. Append new rows after the existing rows, with one row per NSW1 half-hour.
4. Check for duplicate timestamps, missing half-hours, missing demand/PV and changes in units or field definitions.
5. Check that the new data uses the same timestamp convention before joining it to the existing file.
6. Keep missing PV values missing. Do not turn them into zero or “No change”.
7. Record the source, access date and any preparation decisions in the project changelog.

## Reusing `final_modelling.ipynb`

The feature and model code can be reused. Make a copy of the notebook for the new-data run so the current final workbook stays unchanged.

1. In the first code cell, change the CSV path to the new combined file.
2. Replace the hard-coded `2026-08-01` cutoff with a named date just before the genuinely new test period. This lets us include the existing August data in training if it is before the new test period.
3. Keep the current OLS and tree settings fixed. Do not choose new settings after looking at the new test errors.
4. Keep the four earlier validation windows for development checks, or move them only if we agree before testing.
5. Add one final section after the existing forecast comparison: train the fixed models on every eligible row before the new test start, then score the new period once.
6. Report the test dates, row count, MAE and RMSE for the tree with and without PV, OLS with and without PV, and the three existing baselines.
7. State whether the values used by each forecast were genuinely available at that time. If publication timing is still unknown, keep the label “pseudo-forecast”.

The notebook currently has no final-test cell. The data preparation and forecast feature code do not need to be rewritten; the only new modelling step is the final fixed-model score on the new period.
