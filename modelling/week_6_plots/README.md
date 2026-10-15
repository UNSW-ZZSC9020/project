# Week 6: fixed one-year training / one-year test rerun

## Reproduce

From the repository root:

```bash
python modelling/rerun_week_6.py
```

The runner executes the existing code cells from `modelling/final_modelling.ipynb`, adjusting input data, dates, output location and test labels. The original notebook and Week 3/4 plots are unchanged. It uses the same OLS, tree and GAM settings, calendar controls, forecast features, baselines, plotting sizes and 150-dpi PNG format.

## Dates and evaluation

- Training targets: 1 August 2024 through 31 July 2025.
- Test targets: 1 August 2025 through 31 July 2026 (17,520 half-hours).
- Fixed training: no monthly retraining and no fitting on test-year rows.
- Forecasts use observed history before each target half-hour, including earlier test-year observations. This is rolling one-step prediction, not a year-ahead forecast.
- The forecast history requirements and missing training values leave 17,178 common forecast training targets; 17,513 common explanatory training rows.
- The diagnostic OLS specification (`Add demand history`) and forecast example (`Tree with PV`) are fixed from the previous notebook findings rather than chosen using the new test scores.
- The test period was previously explored in the project: this is a retrospective chronological comparison, not an untouched independent final test.

## Input preparation and caveats

Inputs are the demand, rooftop PV, maximum-temperature and daily solar-exposure workbooks in `data/NSW/`. Weather measurement columns are selected explicitly. Raw files are not changed.

The PV workbook contains repeated timestamps, often with different values. The rerun follows the existing Weeks 1–6 pipeline's median-per-timestamp rule. Source type/quality identifiers are absent from this workbook, so those different values cannot be confirmed as equivalent measurements. This is an important limitation; results are conditional on this consolidation policy, and are not directly comparable with earlier measurement-filtered PV inputs.

The full half-hour grid is retained before calculating differences and lags. Missing PV remains missing. The grid contains one missing demand value (1 August 2024 at 00:00), two missing PV values, 96 missing maximum-temperature rows and 48 missing solar-exposure rows. Missing weather is filled from training medians only in explanatory models. Forecast models do not use completed-day weather. See `data_quality.json` for source duplicate counts.

Source timestamps are kept unchanged. Timezone, interval conventions and publication delays remain unverified, so forecasts remain **pseudo-forecasts**. No AEMO benchmark was added: the reused final notebook does not include one.

## Results

| Forecast model | Test MAE (MW) | Test RMSE (MW) |
| --- | ---: | ---: |
| Tree with PV | 68.75 | 100.33 |
| GAM with PV | 72.28 | 103.71 |
| Tree without PV | 73.10 | 106.10 |
| OLS with PV | 76.23 | 109.58 |
| OLS without PV | 77.64 | 111.24 |
| Previous day | 103.59 | 158.95 |
| Previous week | 115.01 | 171.64 |
| Zero change | 209.43 | 266.95 |

Adding PV reduced tree MAE by **4.35 MW**; paired whole-day bootstrap 95% interval: **3.84–4.86 MW**, using the existing 2,000-replicate method. GAM predictions clipped 154 test rows outside the training input ranges, following the original notebook's policy.

## Plots

1. `01_explanatory_models.png`: three current-change OLS models on the full test year.
2. `02_forecast_errors.png`: full-year forecast errors and baselines.
3. `03_pv_gain_by_group.png`: tree PV gain by full test-year season and time block.
4. `04_daily_uncertainty.png`: paired daily-bootstrap uncertainty in tree PV gain.
5. `05_residual_checks.png`: OLS training-fit diagnostics, not test residuals.
6. `06_forecast_example.png`: fixed tree-with-PV example for 1–2 July 2026.
7. `07_forecast_errors_with_gam.png`: full-year forecast comparison including GAM.
8. `08_gam_by_window.png`: GAM/OLS/tree-with-PV comparison; the single window is now the entire test year.

CSV files retain metrics, coefficients, predictions and seasonal summaries for checking the figures. The explanatory models describe current associations; they are not forecasts and do not establish causation.
