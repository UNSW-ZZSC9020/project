# Sample data reference

`sample_data.csv` contains **synthetic data only**: 17,520 NSW1 half-hourly rows, from 1 January 2026 00:00 to 31 December 2026 23:30. It is for testing code and agreeing the input format, not drawing conclusions about NSW demand. The generator is `modelling/sample_data/generate_sample_data.py`. From the repository root, run `python modelling/sample_data/generate_sample_data.py` to recreate the CSV. It always writes beside the script and overwrites the existing sample.

The seven existing field names follow `data/Data_Dictionary.xlsx`. Weather fields are proposed additions from `modelling/modelling_notes.md`.

| Field | Meaning and sample generation |
| --- | --- |
| `INTERVAL_DATETIME` | Interval ending timestamp, spaced 30 minutes apart. Uses fixed AEST (`+10:00`) throughout, not daylight-saving time. |
| `REGIONID` | NEM region identifier; always `NSW1`. |
| `OPERATIONAL_DEMAND_MW` | Operational demand in MW. Simulated from daily peaks, calendar effects, temperature and random variation, less a PV contribution, with small adjustment/response effects. These assumptions are not fitted relationships. |
| `OPERATIONAL_DEMAND_ADJUSTMENT_MW` | Demand adjustment in MW. Usually zero; occasional negative values generated alongside simulated demand response. Not an AEMO adjustment rule. |
| `WDR_ESTIMATE_MW` | Wholesale demand response estimate in MW. Usually zero; occasional simulated events of 8–38 MW. |
| `ROOFTOP_PV_POWER_MW` | Estimated rooftop PV output in MW. Simulated from daylight, season and cloud cover, with small random variation; zero overnight. |
| `PV_QUALITY_INDICATOR` | Source quality score. Fixed at `1.00` for this sample; its meaning and valid range must be confirmed from the real source, not inferred here. |
| `TEMPERATURE_C` | Representative air temperature in °C for the interval. Seasonal and daily cycles plus random variation. Not tied to an actual weather station. |
| `CLOUD_COVER_PERCENT` | Representative cloud cover, 0–100%. Simulated daily cloud conditions plus within-day variation. |
| `SOLAR_EXPOSURE_30MIN_MJ_M2` | Solar energy per square metre over the ending half-hour, in MJ/m². Simulated daylight and seasonal profile reduced by cloud, with random variation; zero overnight. Not a daily total or power in W/m². |

