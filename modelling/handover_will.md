## What I did

I used half-hourly NSW rooftop PV and operational demand data from 1 August 2025 to 31 July 2026. The final workbook, `final_modelling.ipynb`, asks two separate questions:

1. How are current changes in PV and demand related after basic time and weather controls?
2. Does observed PV improve a forecast of demand change in the next half-hour?

I used four chronological 14-day validation windows across different seasons. This is better than a random split because it keeps the order of events, but it is still development validation rather than a new final test.

For fuller method wording and results, look at `final_modelling_notes.md` and the plain-language explanations in `final_modelling.ipynb`.

## Main results to use

### Current relationship

- The base OLS result was **−0.737** for the PV-change coefficient, with a 95% HAC interval of **−0.765 to −0.709**.
- In plain terms, a 100 MW increase in current PV change was associated with about 73.7 MW less current demand change after allowing for time, day, season, maximum temperature and solar exposure.
- Adding one earlier PV change barely changed average validation error: **93.59 MW** to **93.17 MW**.
- Adding one earlier demand change reduced average validation MAE to **73.65 MW**.

Possible wording:

> We found a strong negative adjusted association between simultaneous rooftop PV and operational-demand changes. This result does not establish that PV caused the demand change, because other unmeasured factors and time patterns may remain.

### Next-half-hour forecasts

| Model | MAE (MW) | RMSE (MW) |
| --- | ---: | ---: |
| Zero change | 209.85 | 265.61 |
| Previous-day change | 111.12 | 170.94 |
| Previous-week change | 113.89 | 171.25 |
| OLS without PV | 81.85 | 116.74 |
| OLS with PV | 82.23 | 116.30 |
| GAM with PV | 78.17 | 110.00 |
| Tree without PV | 78.47 | 112.75 |
| **Tree with PV** | **73.83** | **106.75** |

Possible wording:

> The fixed tree forecast with observed PV had the lowest average error across the four validation windows. The fixed GAM with PV was better than both OLS models but not the PV tree. Adding PV reduced tree MAE by 4.64 MW, with a paired daily-bootstrap 95% interval of 3.22–6.02 MW, while adding PV did not improve OLS MAE.

## Things to clarify in the report

- Do not call the OLS coefficient causal.
- Check with Bel whether to call the forecasts real-time forecasts. They assume the previous half-hour's demand and PV were available, but currently unconfirmed
- Do not compare the Week 4 scores directly with Week 3 August scores. They use different dates and training histories.
- Sydney Airport weather is a local proxy, not weather across all NSW rooftop PV systems.
- Residual patterns remain after the regression models, especially at a one-day lag.
- The daily-bootstrap interval measures variation across the available days; it does not prove the same gain will occur in future years or cover every modelling choice.
- The GAM is one fixed comparison, not a tuned best-case model; 25 validation rows were clipped to its earlier training range.

## Useful figures

Use the saved plots from `week_4_plots/`:

- `01_explanatory_models.png`: simple OLS comparison across the seasonal windows.
- `02_forecast_errors.png`: main forecast-model comparison.
- `03_pv_gain_by_group.png`: where PV helped the tree by season window and time of day.
- `04_daily_uncertainty.png`: uncertainty around the tree PV gain.
- `05_residual_checks.png`: remaining OLS error patterns.
- `06_forecast_example.png`: two-day forecast illustration; use as an example, not proof of overall performance.

