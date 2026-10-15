# Week 4 — things to try next

Starting from the [Week 3 notes](week_3_modelling_notes.md). Suggested work, not decisions already made.

1. **Sort out timing and provenance first.** Confirm the AEMO clock, interval-ending dates, BoM observation-day rules and when demand/PV become available. Check the original PV source and quality-flag definitions. Fix the missing PV row's “No change” label in a derived copy, not by overwriting the source.
2. **Use several chronological validation windows.** Try expanding-window checks across different seasons, allowing enough history for the lags. The August test has already been seen; reserve genuinely new data for another final test if available.
3. **Simplify the lagged OLS.** Compare no PV lags, one lag and a short lag set. The middle-lag VIFs were around 11.8 and extra lags barely improved validation error. Keep PCA off the main path unless simpler inputs still cause problems.
4. **Work on the residual patterns.** Try season-specific daily profiles, temperature curves and a small number of demand-history terms. Check how these alter the meaning of the PV coefficient. Compare HAC bandwidths and day-clustered uncertainty; residual dependence was still strong at 30 minutes and one day.
5. **Check where PV helps forecasts.** Compare the same PV/non-PV models by daylight period, ramp size and season. Add previous-day/week seasonal baselines. Use paired daily error differences or a day-block bootstrap to see how uncertain the small tree improvement is. Keep publication delays in the features.
6. **Improve weather coverage if practical.** Look for time-aligned observations from more than Sydney Airport, or genuinely issued weather forecasts. Daily totals are fine for retrospective comparisons but cannot be treated as known throughout the day. Repeat the quality-flag and missing-weather sensitivity checks.
7. **Only then tune the alternatives.** Try a small chronological search over GAM smoothness and tree size. Check GAM curves and errors outside the training range. Investigate an AEMO forecast benchmark only after matching forecast horizon, issue time and coverage.

Keep the next agreed work in `initial_modelling.ipynb` unless it becomes unwieldy. Save plots beside the notebook, record what changed and why, and update `requirements.txt` if any packages are added. Agree on the next experiments before changing the models; do not tune against the used August test.
