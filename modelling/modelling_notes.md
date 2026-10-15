# Modelling objectives

The modelling should answer three main questions:

1. **How strongly are short-term changes in rooftop PV associated with changes in NSW operational demand?**
   - Primary variables: `ΔPV` and `ΔDemand`
   - Estimate the direction, size and uncertainty of the relationship.
   - Express the result in meaningful units where possible, such as the expected change in demand (MW) for a given change in rooftop PV (MW).

2. **Does the PV-demand relationship change under different conditions?**
   - Time of day
   - Season
   - Temperature
   - Cloud cover / solar exposure
   - Potentially weekdays vs weekends or holidays

3. **Does including rooftop PV improve short-term demand prediction?**
   - Compare a non-PV baseline with a PV-enhanced model.
   - If suitable AEMO forecast data is available, also compare both models against the AEMO forecast.
   - Evaluate all forecasting models on the same held-out chronological period.

# Modelling definitions

- Use half-hourly intervals, initially including all times of day.
- Main outcome: `ΔDemand(t) = Demand(t) − Demand(t−1)`, where demand is NSW `OPERATIONAL_DEMAND_MW`.
- Main predictor: `ΔPV(t) = PV(t) − PV(t−1)`, using `ROOFTOP_PV_POWER_MW`.
- Both changes are measured in MW, with `t−1` referring to the previous half-hour interval.
- Initial controls: time of day, weekday, season, weekend/public holiday indicators, temperature and cloud cover/solar exposure where available.
- Initially consider current PV change and lags of 30–120 minutes, as outlined below.
- Initial forecast horizon: 30 minutes ahead, predicting `ΔDemand(t+1)` using only information available at time `t`. Unlike the explanatory model, this cannot use observed PV or weather from the target interval.

# Modelling data requirements

The modelling dataset should contain one row per NSW half-hour interval.

Current available fields (from `data/Data_Dictionary.xlsx`)
- `INTERVAL_DATETIME`: interval ending timestamp
- `REGIONID`, `OPERATIONAL_DEMAND_MW` and `ROOFTOP_PV_POWER_MW`.
- `PV_QUALITY_INDICATOR` and any other available data-quality flags.

Additional derived fields required for modelling:
- Derived `ΔDemand`, `ΔPV` and lagged PV changes at 30, 60, 90 and 120 minutes.

Additional fields that need to be sourced:
- Temperature and cloud cover/solar exposure where available.
- Derived time of day, weekday, month/season and weekend/public holiday indicators.

# Primary statistical model
**Options Considered:**
- Multiple Linear Regression (OLS)
	- Models a continuous outcome as a linear combination of multiple predictor variables, estimating coefficients by minimising the sum of squared prediction errors.
	- Simple, interpretable, and well suited to estimating how changes in rooftop PV are associated with changes in demand while controlling for weather, time of day, season and other factors.
- Generalised Additive Model (GAM)
	- Models an outcome using a combination of flexible, smooth functions of predictor variables, allowing non-linear relationships without specifying their exact shape in advance.
	- More flexible than linear regression and useful if important relationships are clearly curved or nonlinear, but harder to explain.
- Dynamic / Distributed Lag Regression
	- Models an outcome using current and previous values of one or more predictors, allowing effects to occur gradually or with a time delay.
	- Useful for testing whether PV changes affect demand immediately or over the following 30–120 minutes, but can become harder to interpret if too many lags are included.

Based on the different characteristics of each model, the following option is proposed:
- Use **multiple linear regression** as the primary model
	- This will make it easier to test different scenarios, and be simpler to explain in a report, since the aim is also to quantify the relationships between rooftop PV generation and demand
- A small number of lagged PV variables will be added in later stages to test delayed effects (i.e. change in rooftop PV generation not immediately being reflected in change in demand)
- GAM may be used as a secondary model if clear nonlinear relationships emerge
- To test predictive performance, XGBoost (a complex machine-learning model) may be used as a benchmark to compare to

## Lag analysis

The lag analysis should investigate whether changes in rooftop PV are associated with demand changes immediately or over the following few half-hour intervals.
### Candidate lags

At 30-minute resolution, initially test:

- 0 minutes: `ΔPV(t)`
- 30 minutes: `ΔPV(t-1)`
- 60 minutes: `ΔPV(t-2)`
- 90 minutes: `ΔPV(t-3)`
- 120 minutes: `ΔPV(t-4)`

### Proposed approach
1. Plot and inspect `ΔPV` and `ΔDemand`.
2. Calculate simple correlation between contemporaneous `ΔPV` and `ΔDemand`.
3. Run cross-correlation over a limited window around the current interval.
4. Use the cross-correlation results as exploratory evidence rather than automatically selecting the strongest lag.
5. Fit a small number of candidate lagged regression models using the training period.
6. Compare their performance and stability on the validation period.
7. Keep the final lag structure simple and physically plausible.

Negative lags, where future PV appears to explain current demand, will not be considered.

