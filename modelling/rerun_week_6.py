"""Rerun final_modelling.ipynb code with a fixed one-year train/test split.

Run from the repository root: python modelling/rerun_week_6.py
Original notebooks and plots are not modified. See week_6_plots/README.md.
"""
import os
os.environ.setdefault('MPLBACKEND', 'Agg')
os.environ.setdefault('OMP_NUM_THREADS', '1')
os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')
from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'data' / 'NSW'
DEST = ROOT / 'modelling' / 'week_6_plots'
DEST.mkdir(exist_ok=True)
TRAIN_START = pd.Timestamp('2024-08-01')
TEST_START = pd.Timestamp('2025-08-01')
TEST_END = pd.Timestamp('2026-08-01')


def prepare_data():
    demand = pd.read_excel(SOURCE / 'Operational Demand 202408 - 202608.xlsx')
    pv = pd.read_excel(SOURCE / 'Rooftop PV Actual 2017-2026.xlsx')
    demand = demand.loc[demand.REGIONID.eq('NSW1')].set_index('INTERVAL_DATETIME')
    assert not demand.index.has_duplicates
    pv = pv.loc[pv.REGIONID.eq('NSW1')]
    pv = pv.loc[pv.INTERVAL_DATETIME.ge(TRAIN_START) & pv.INTERVAL_DATETIME.lt(TEST_END)]
    groups = pv.groupby('INTERVAL_DATETIME')['POWER']
    # Same duplicate-consolidation policy as the existing Weeks 1–6 pipeline.
    solar = groups.median().rename('ROOFTOP_PV_MW')
    raw = demand[['OPERATIONALDEMAND']].rename(columns={'OPERATIONALDEMAND': 'OPERATIONAL_DEMAND_MW'})
    # Keep the source clock; reindex so lags never jump over missing intervals.
    grid = pd.date_range(TRAIN_START, TEST_END, freq='30min', inclusive='left')
    raw = raw.reindex(grid).join(solar)
    for filename, measurement, output in [
        ('Daily Max Temperature.xlsx', 'Maximum temperature (Degree C)', 'MAX_TEMP_C'),
        ('Daily Solar Exposure.xlsx', 'Daily global solar exposure (MJ/m*m)', 'SOLAR_EXPOSURE_MJ_M2'),
    ]:
        weather = pd.read_excel(SOURCE / filename).set_index('Date')[measurement]
        assert not weather.index.has_duplicates
        raw[output] = pd.Series(raw.index.normalize(), index=raw.index).map(weather)
    raw.index.name = 'DATETIME'
    quality = {
        'source_pv_rows': len(pv),
        'pv_timestamps_with_multiple_records': int(groups.size().gt(1).sum()),
        'pv_timestamps_with_different_nonmissing_values': int(groups.nunique().gt(1).sum()),
        'missing_values_on_complete_grid': raw.isna().sum().to_dict(),
        'training_start': str(TRAIN_START), 'test_start': str(TEST_START), 'test_end_exclusive': str(TEST_END),
    }
    (DEST / 'data_quality.json').write_text(json.dumps(quality, indent=2))
    return raw


if __name__ == '__main__':
    notebook = json.loads((ROOT / 'modelling' / 'final_modelling.ipynb').read_text())
    namespace = {'__name__': '__main__', 'prepared_raw': prepare_data(), 'run_root': ROOT}
    replacements = {
        3: [
            ("ROOT = Path.cwd().parent if Path.cwd().name == 'modelling' else Path.cwd()", 'ROOT = run_root'),
            ("PLOTS = ROOT / 'modelling' / 'week_4_plots'", "PLOTS = ROOT / 'modelling' / 'week_6_plots'"),
            ("raw = pd.read_csv(ROOT / 'data' / 'NSW1_Historical_Modelling_Dataset_Week3.csv', parse_dates=['DATETIME'])\nraw = raw.set_index('DATETIME').sort_index()", 'raw = prepared_raw.sort_index()'),
        ],
        7: [("folds = {'Spring': '2025-11-01', 'Summer': '2026-02-01',\n         'Autumn': '2026-05-01', 'Winter': '2026-07-01'}", "folds = {'Test year': '2025-08-01'}")],
        11: [("selected_ols = explanatory_summary.index[0]", "selected_ols = 'Add demand history'"),
             ("ylabel='Validation MAE (MW)'", "ylabel='Test MAE (MW)'")],
        14: [("X_explain = explanatory_matrix(explanatory, data)", "explanatory = explanatory.loc[explanatory.index < '2025-08-01']\nX_explain = explanatory_matrix(explanatory, data.loc[data.index < '2025-08-01'])")],
        19: [("assert training.index.max() < validation.index.min() and len(validation) == 672", "assert training.index.max() < pd.Timestamp('2025-08-01') <= validation.index.min()\n    assert len(validation) > 17000")],
        22: [("selected_forecast = forecast_summary.index[0]", "selected_forecast = 'Tree with PV'"),
             ('Next-half-hour development validation', 'Next-half-hour fixed-year test')],
        25: [('Next-half-hour validation, including GAM', 'Next-half-hour fixed-year test, including GAM'),
             ("ylabel='Validation MAE (MW)'", "ylabel='Test MAE (MW)'")],
        33: [('First two winter validation days', 'Two winter test days')],
    }
    for i, cell in enumerate(notebook['cells']):
        if cell['cell_type'] != 'code':
            continue
        code = ''.join(cell['source'])
        for old, new in replacements.get(i, []):
            assert old in code, (i, old)
            code = code.replace(old, new)
        # Every model uses the same fixed first year, and scores the full second year.
        code = code.replace('start + pd.Timedelta(days=14)', "pd.Timestamp('2026-08-01')")
        code = code.replace('validation targets', 'test targets')
        print(f'Executing original notebook cell {i}', flush=True)
        exec(compile(code, f'final_modelling.ipynb:cell-{i}', 'exec'), namespace)
    for name in ['explanatory_scores', 'explanatory_summary', 'coefficients', 'forecast_summary',
                 'comparison_with_gam', 'outputs', 'gam_outputs', 'residual_table']:
        namespace[name].to_csv(DEST / f'{name}.csv', index=name not in ['outputs', 'gam_outputs', 'explanatory_scores'])
    paired = namespace['paired'].copy()
    months = paired['Target'].dt.month
    paired['Season'] = months.map({12:'Summer',1:'Summer',2:'Summer',3:'Autumn',4:'Autumn',5:'Autumn',6:'Winter',7:'Winter',8:'Winter',9:'Spring',10:'Spring',11:'Spring'})
    paired.groupby('Season')['Gain MW'].agg(['mean', 'size']).to_csv(DEST / 'pv_gain_by_season.csv')
    # Same two-panel format as plot 03, now covering whole seasons rather than short windows.
    plt = namespace['plt']
    figure, axes = plt.subplots(1, 2, figsize=(10, 3.5))
    for axis, column in zip(axes, ['Season', 'Period']):
        paired.groupby(column, observed=True)['Gain MW'].mean().plot.barh(ax=axis)
        axis.axvline(0, color='grey', linewidth=0.8)
        axis.set(xlabel='MAE gain from PV (MW)', ylabel='', title=column)
    namespace['save_plot'](figure, '03_pv_gain_by_group.png')
    print(f'Complete: {DEST}', flush=True)
