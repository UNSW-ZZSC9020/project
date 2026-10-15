# NSW1 Historical Modelling Dataset Week 4 v2

## Coverage
- Start: 2025-08-01 00:00:00
- End: 2026-08-31 23:30:00
- Rows: 19,008
- Frequency: half-hourly

## Changes from Week 3
1. Re-sorted by timestamp.
2. Recomputed 1-, 2- and 4-interval PV and demand lags.
3. Recomputed PV and demand interval changes.
4. Corrected PV ramp direction so a missing PV change remains missing.
5. Added statewide NSW public-holiday flag and name.
6. Added dataset version and documented timezone assumption.

## Missing-value policy
The missing rooftop PV observation is retained as missing. It is not changed to zero or labelled as `No change`.

## Modelling use
Chronological train, validation and test splits must be used. Features that would not be available before the target interval must not be used in pseudo-forecast or forecast models.

## Important caveat
The project has not yet verified when previous-half-hour demand and PV values become available. Forecast comparisons should remain labelled pseudo-forecasts until publication timing is confirmed.

## Public holidays
Statewide NSW public holidays were taken from the NSW Government calendar. The Bank Holiday was excluded because it is not a declared public holiday for all NSW workers. Local public holidays and local event days were also excluded.
