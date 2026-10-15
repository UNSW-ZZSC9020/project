from pathlib import Path
import pandas as pd, numpy as np
INPUT=Path("NSW1_Historical_Modelling_Dataset_Week3.csv")
OUTPUT=Path("NSW1_Historical_Modelling_Dataset_Week4_v2.csv")
df=pd.read_csv(INPUT); df.columns=[c.strip().replace("\\_","_") for c in df.columns]; df["DATETIME"]=pd.to_datetime(df["DATETIME"]); df=df.sort_values("DATETIME").reset_index(drop=True)
for lag in (1,2,4):
    df[f"PV_LAG_{lag}"]=df["ROOFTOP_PV_MW"].shift(lag); df[f"DEMAND_LAG_{lag}"]=df["OPERATIONAL_DEMAND_MW"].shift(lag)
df["DELTA_PV_MW"]=df["ROOFTOP_PV_MW"].diff(); df["DELTA_DEMAND_MW"]=df["OPERATIONAL_DEMAND_MW"].diff()
df["PV_RAMP_DIRECTION"]=np.select([df.DELTA_PV_MW>0,df.DELTA_PV_MW<0],["Increase","Decrease"],"No change"); df.loc[df.DELTA_PV_MW.isna(),"PV_RAMP_DIRECTION"]=np.nan
holidays={"2025-10-06":"Labour Day","2025-12-25":"Christmas Day","2025-12-26":"Boxing Day","2026-01-01":"New Year's Day","2026-01-26":"Australia Day","2026-04-03":"Good Friday","2026-04-04":"Easter Saturday","2026-04-05":"Easter Sunday","2026-04-06":"Easter Monday","2026-04-25":"Anzac Day","2026-04-27":"Additional public holiday for Anzac Day","2026-06-08":"King's Birthday"}
key=df.DATETIME.dt.strftime("%Y-%m-%d"); df["NSW_PUBLIC_HOLIDAY_FLAG"]=key.isin(holidays).astype("int8"); df["NSW_PUBLIC_HOLIDAY_NAME"]=key.map(holidays).fillna(""); df["DATASET_VERSION"]="Week4_v2"; df["SOURCE_TIMEZONE"]="Australia/Sydney (assumption; confirm with AEMO metadata)"
df.to_csv(OUTPUT,index=False,date_format="%Y-%m-%d %H:%M:%S")
