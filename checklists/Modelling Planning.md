# Week 2 Tasks
The main goal for Week 2 is to establish a working modelling framework and produce the first simple results.

- [x] Finalise modelling definitions
- [x] Define modelling data requirements
- [ ] Set up modelling .ipynb notebook structure
- [x] Run basic modelling EDA (Bel)
- [ ] Fit the first simple regression
- [ ] Set up evaluation code (define functions for calculating simple evaluation metrics)

# Week 3 Initial Plan

Week 3 should move from initial exploration to a defensible primary statistical model.

**Build out the primary regression model**
  - Start with `ΔPV`
  - Add time and calendar controls
  - Add weather variables
  - Add selected PV lags
  - Add a small number of useful interaction terms

**Test whether the PV-demand relationship changes by:**
  - hour of day
  - season
  - cloud cover / solar conditions
  - temperature
**Finalise lag selection**
  - Compare the 30, 60, 90 and 120 minute lag options
  - Keep the simplest lag structure that improves the model and makes sense physically

**Run model diagnostics**
  - Check residuals
  - Check autocorrelation
  - Check heteroskedasticity
  - Check for influential observations
  - Check for multicollinearity between PV, weather and lagged variables
  - Use robust or HAC standard errors if needed

**Compare OLS with a GAM if the initial results show clear nonlinear behaviour**

**Set up the forecasting comparison**
  - Build or refine the non-PV baseline model
  - Build the equivalent PV-enhanced model
  - Compare both using validation MAE and RMSE
