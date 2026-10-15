"""Generate synthetic source-style inputs, not observations or fitted results."""

import csv
import math
import random
from datetime import date, datetime, timedelta
from pathlib import Path

# Use the same random values each time and save beside this script.
random.seed(9020)
OUTPUT = Path(__file__).resolve().with_name('sample_data.csv')

# Create one interval ending timestamp for each half-hour of 2026.
START = datetime(2026, 1, 1, 0, 0)
INTERVALS = [START + timedelta(minutes=30 * i) for i in range(365 * 48)]

# The sample includes the NSW public-holiday dates represented in the 2026 calendar.
NSW_PUBLIC_HOLIDAYS = {
    date(2026, 1, 1), date(2026, 1, 26),
    date(2026, 4, 3), date(2026, 4, 4), date(2026, 4, 5), date(2026, 4, 6),
    date(2026, 4, 25), date(2026, 6, 8), date(2026, 10, 5),
    date(2026, 12, 25), date(2026, 12, 26), date(2026, 12, 28),
}


# Make a smooth peak: centre sets its time and width sets its spread.
def gaussian(value, centre, width):
    return math.exp(-0.5 * ((value - centre) / width) ** 2)


# Give each day a weather pattern shared by its half-hourly rows.
# Sine/cosine curves create cycles; random.gauss adds random variation.
daily_weather = {}
for day_index in range(365):
    current_date = date(2026, 1, 1) + timedelta(days=day_index)
    annual_cycle = math.cos(2 * math.pi * (day_index - 15) / 365)
    daily_weather[current_date] = {
        'annual_cycle': annual_cycle,
        'cloud': min(0.94, max(0.04, random.betavariate(2.3, 2.5))),
        'temperature_offset': random.gauss(0, 2.0),
        'demand_offset': random.gauss(0, 135),
    }

rows = []
previous_noise = 0.0

for timestamp in INTERVALS:
    current_date = timestamp.date()
    state = daily_weather[current_date]
    day_index = (current_date - date(2026, 1, 1)).days
    hour = timestamp.hour + timestamp.minute / 60
    weekday = timestamp.weekday()
    is_weekend = weekday >= 5
    is_public_holiday = current_date in NSW_PUBLIC_HOLIDAYS

    # Approximate daylight hours, keeping timestamps in fixed AEST.
    day_length = 12 + 2.1 * math.cos(2 * math.pi * (day_index - 10) / 365)
    solar_noon = 12.5 + 0.45 * math.cos(2 * math.pi * (day_index - 10) / 365)
    solar_position = math.pi * (hour - (solar_noon - day_length / 2)) / day_length
    solar_shape = max(0.0, math.sin(solar_position))

    # Keep cloud cover between 0 and 100%; vary temperature through the day.
    cloud_cover = min(100, max(0, 100 * (
        state['cloud'] + 0.12 * math.sin(hour * 1.7 + day_index) + random.gauss(0, 0.07)
    )))
    temperature = (
        16.8 + 5.8 * state['annual_cycle'] + state['temperature_offset']
        + 3.9 * math.sin(2 * math.pi * (hour - 8) / 24) + random.gauss(0, 0.35)
    )
    # Reduce half-hourly solar exposure under cloud and set it to zero at night.
    clear_solar_peak = 1.10 + 0.22 * state['annual_cycle']
    solar_exposure = max(
        0,
        clear_solar_peak * solar_shape * (1 - 0.73 * cloud_cover / 100) + random.gauss(0, 0.025),
    )
    if solar_shape == 0:
        solar_exposure = 0.0

    # PV follows daylight and cloud cover, with a little extra variation.
    pv = 2050 * (solar_shape ** 0.82) * (1 - 0.70 * cloud_cover / 100) * (0.88 + 0.12 * state['annual_cycle'])
    pv += random.gauss(0, 13) if solar_shape > 0 else 0
    pv = max(0, pv)

    # Build demand from daily peaks, calendar effects and heating/cooling.
    morning_peak = 820 * gaussian(hour, 8.0, 1.55)
    evening_peak = 1750 * gaussian(hour, 18.6, 2.05)
    daytime_activity = 370 * gaussian(hour, 13.0, 3.8)
    weekday_effect = 360 if not is_weekend and 7 <= hour < 19 else 0
    holiday_effect = -560 if is_public_holiday and 8 <= hour < 20 else 0
    heating_cooling = max(0, 14 - temperature) * 125 + max(0, temperature - 25) * 105
    # Carry some random demand variation into the next interval.
    previous_noise = 0.66 * previous_noise + random.gauss(0, 58)
    gross_demand = (
        6500 + 340 * abs(state['annual_cycle']) + morning_peak + evening_peak + daytime_activity
        + weekday_effect + holiday_effect + heating_cooling + state['demand_offset'] + previous_noise
    )

    # Add a few small demand-response events. These are not AEMO rules.
    demand_adjustment = 0.0
    wdr = 0.0
    if random.random() < 0.0035 and 15 <= hour <= 20 and not is_weekend:
        wdr = round(random.uniform(8, 38), 1)
        demand_adjustment = round(-wdr * random.uniform(0.25, 0.55), 1)
    # This assumed PV effect is for testing, not an estimated relationship.
    demand = max(4500, gross_demand - 0.42 * pv + demand_adjustment - wdr)

    # Round the measurements to keep the CSV readable.
    demand = round(demand, 1)
    pv = round(pv, 1)
    temperature = round(temperature, 1)
    cloud_cover = round(cloud_cover, 1)
    solar_exposure = round(solar_exposure, 3)

    # Save input fields only; the notebook calculates changes and other features.
    rows.append({
        'INTERVAL_DATETIME': timestamp.strftime('%Y-%m-%dT%H:%M:%S+10:00'),
        'REGIONID': 'NSW1',
        'OPERATIONAL_DEMAND_MW': demand,
        'OPERATIONAL_DEMAND_ADJUSTMENT_MW': demand_adjustment,
        'WDR_ESTIMATE_MW': wdr,
        'ROOFTOP_PV_POWER_MW': pv,
        'PV_QUALITY_INDICATOR': '1.00',  # Sample score; confirm real source codes.
        'TEMPERATURE_C': temperature,
        'CLOUD_COVER_PERCENT': cloud_cover,
        'SOLAR_EXPOSURE_30MIN_MJ_M2': solar_exposure,
    })

# Replace the sample CSV with the same reproducible data on each run.
with OUTPUT.open('w', newline='', encoding='utf-8') as file:
    writer = csv.DictWriter(file, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)

print(f'Wrote {len(rows):,} rows and {len(rows[0])} columns to {OUTPUT}')
