# Final modelling notes

22 September 2026 · [Workbook](final_modelling.ipynb)

## What I did

I kept the final workbook simple: three OLS regression models, one fixed tree forecast model and one fixed GAM comparison. OLS estimates a straight-line relationship after allowing for the other listed inputs. The tree model learns simple decision rules; a GAM can fit smooth curved relationships.

- I used **1 August 2025–31 July 2026** and recalculated demand/PV changes and short lags.
- I used four 14-day validation windows: November 2025, February 2026, May 2026 and July 2026. This checks the models across seasons while keeping time order.
- I kept missing PV values missing and corrected the missing PV row's derived ramp label in memory only. I did not change the source data.
- I used daily weather only in the current-change OLS models. I did not use it in forecasts because completed-day weather would not be known at every forecast time.

I left August 2026 out of this workbook because we had already looked at Week 3 results for that period. I could still use August as a clearly labelled comparison, but not as an independent final test. This is a transparency choice, not a claim that August comparisons are invalid.

## Main findings

### Current demand-change models

Mean validation MAE was **93.59 MW** for the base OLS model, **93.17 MW** after adding one earlier PV-change value, and **73.65 MW** after adding one earlier demand-change value. MAE is the average size of the model errors, so lower is better. Recent demand movement helped more than the extra PV lag.

The base model's PV coefficient was **−0.737** (95% HAC interval **−0.765 to −0.709**). In this model, a 100 MW increase in current PV change was associated with about 73.7 MW less current demand change, after allowing for time, day, season, temperature and solar exposure. This is an association in the supplied data, not proof that PV causes the change.

Adding earlier demand change reduced the 30-minute residual correlation from **0.683 to 0.193**, but one-day correlation remained **0.425**. A residual is the part the model did not explain, so there are still regular patterns missing from the model.

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

RMSE gives more weight to large errors. The fixed GAM with PV performed better than both OLS models, but not as well as the tree with PV; it had 25 validation rows outside its earlier training range, which were clipped rather than extrapolated. Adding observed PV history improved the fixed tree's MAE by **4.64 MW**, with a paired daily-bootstrap 95% interval of **3.22–6.02 MW**. OLS did not improve when PV was added, so PV's forecast value was model-dependent.

These are rolling one-step pseudo-forecasts: for each target half-hour, I assume the previous half-hour's demand and PV are available. The supplied data does not say when values were published or revised, so we cannot call this a verified real-time forecast result.

## What this does and does not answer

The workbook supports a clear answer to two questions: current PV and demand changes are strongly related after basic controls, and observed PV improved this fixed tree forecast across the four validation windows. It does not establish a causal PV effect, prove the result will hold in future years, or show how the models would perform using confirmed real-time data.

The most useful next step is to collect genuinely new, time-aligned data and run the same fixed comparison once. The main notebook can be reused with a new input file and changed date boundaries; see [data_engineer_handover.md](handover_bel.md). New data and confirmed timing are more important than tuning or adding further models.

## Plot guide

| Plot | What it shows |
| --- | --- |
| [01 — Explanatory models](week_4_plots/01_explanatory_models.png) | The three OLS models across the four validation windows. |
| [02 — Forecast errors](week_4_plots/02_forecast_errors.png) | Average forecast errors for the models and simple baselines. |
| [03 — PV gain by group](week_4_plots/03_pv_gain_by_group.png) | Where adding PV helped the tree by season window and source-clock period. Positive values favour PV. |
| [04 — Daily uncertainty](week_4_plots/04_daily_uncertainty.png) | The range of tree PV gains when I resample whole days. |
| [05 — Residual checks](week_4_plots/05_residual_checks.png) | Remaining unexplained error patterns in the OLS models. |
| [06 — Forecast example](week_4_plots/06_forecast_example.png) | The selected tree forecast against observations for 1–2 July 2026. |

## Limits and next steps

We still need confirmation of the AEMO clock, interval dates, publication delays and PV quality definitions. Sydney weather is a local proxy, not weather across NSW. A future comparison should use a new data period, fixed models, confirmed input availability and, if available, an AEMO forecast with the same issue time and forecast horizon.

I included one fixed GAM comparison but left out tuning and larger sensitivity checks to keep the workbook readable. The existing environment is enough to rerun it; no new packages are needed.
