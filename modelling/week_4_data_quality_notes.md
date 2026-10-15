# Week 4 data quality and modelling handover notes

- Common Week 3 integrated dataset contained 19,008 half-hourly records from 1 August 2025 to 31 August 2026.
- Previous checks found no duplicate timestamps and no missing half-hour intervals.
- The missing rooftop PV value is retained as missing and must not be treated as zero or “No change”.
- Lag and change variables are generated after chronological sorting.
- Completed-day weather is not used in next-half-hour forecasts.
- Previous-half-hour demand/PV publication timing is not confirmed, so forecasts remain pseudo-forecasts.
- Sydney Airport daily weather is a local proxy for NSW1, not statewide half-hourly weather.
- AEMO interval convention, timezone, daylight-saving treatment and PV quality-flag definitions remain items for confirmation.
