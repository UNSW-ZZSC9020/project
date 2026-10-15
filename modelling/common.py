from pathlib import Path
import pandas as pd
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'data'/'raw'; PROCESSED=ROOT/'data'/'processed'; FIG=ROOT/'outputs'/'figures'; TAB=ROOT/'outputs'/'tables'; MODELS=ROOT/'outputs'/'models'
for p in [PROCESSED,FIG,TAB,MODELS]: p.mkdir(parents=True,exist_ok=True)
SEED=42

def read_first_sheet(path):
    return pd.read_excel(path, sheet_name=0, engine='openpyxl')

def find_col(df, candidates):
    lookup={str(c).strip().upper():c for c in df.columns}
    for c in candidates:
        if c.upper() in lookup:return lookup[c.upper()]
    raise KeyError(f'Missing one of {candidates}; found {list(df.columns)}')

def parse_dt(s):
    return pd.to_datetime(s, errors='coerce', dayfirst=True)

def season(month):
    return np.select([month.isin([12,1,2]),month.isin([3,4,5]),month.isin([6,7,8])],['Summer','Autumn','Winter'],'Spring')
