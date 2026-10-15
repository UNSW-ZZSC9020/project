"""Prepare the common half-hourly modelling table. All transformations are explicit and auditable."""
from common import *

def weather(path, output_name):
    d=read_first_sheet(path); dc=find_col(d,['DATE']); vc=[c for c in d.columns if c!=dc and pd.api.types.is_numeric_dtype(d[c])]
    if not vc: raise ValueError(f'No numeric weather measurement in {path.name}')
    out=pd.DataFrame({'DATE':parse_dt(d[dc]).dt.normalize(),output_name:pd.to_numeric(d[vc[-1]],errors='coerce')})
    return out.groupby('DATE',as_index=False)[output_name].median()

def main():
    pv=read_first_sheet(RAW/'Rooftop PV Actual 2017-2026.xlsx')
    demand=read_first_sheet(RAW/'Operational Demand 202408 - 202608.xlsx')
    fc=read_first_sheet(RAW/'Operational Demand Forecast 202408 - 202608.xlsx')
    pdt=find_col(pv,['INTERVAL_DATETIME']); preg=find_col(pv,['REGIONID']); pval=find_col(pv,['POWER','ROOFTOP_PV_MW'])
    ddt=find_col(demand,['INTERVAL_DATETIME']); dreg=find_col(demand,['REGIONID']); dval=find_col(demand,['OPERATIONALDEMAND','OPERATIONAL_DEMAND_MW'])
    fdt=find_col(fc,['INTERVAL_DATETIME']); freg=find_col(fc,['REGIONID']); fver=find_col(fc,['VERSION_DATETIME']); fval=find_col(fc,['DEMAND_FORECAST_POE50'])
    pv=pd.DataFrame({'DATETIME':parse_dt(pv[pdt]),'REGIONID':pv[preg].astype(str),'ROOFTOP_PV_MW':pd.to_numeric(pv[pval],errors='coerce')})
    pv=pv[pv.REGIONID.eq('NSW1')].groupby('DATETIME',as_index=False).agg(ROOFTOP_PV_MW=('ROOFTOP_PV_MW','median'),SOURCE_RECORD_COUNT=('ROOFTOP_PV_MW','size'))
    demand=pd.DataFrame({'DATETIME':parse_dt(demand[ddt]),'REGIONID':demand[dreg].astype(str),'OPERATIONAL_DEMAND_MW':pd.to_numeric(demand[dval],errors='coerce')})
    demand=demand[demand.REGIONID.eq('NSW1')].groupby('DATETIME',as_index=False).OPERATIONAL_DEMAND_MW.median()
    fc=pd.DataFrame({'DATETIME':parse_dt(fc[fdt]),'REGIONID':fc[freg].astype(str),'VERSION_DATETIME':parse_dt(fc[fver]),'AEMO_POE50_MW':pd.to_numeric(fc[fval],errors='coerce')})
    fc=fc[(fc.REGIONID=='NSW1') & (fc.VERSION_DATETIME<fc.DATETIME)].sort_values(['DATETIME','VERSION_DATETIME']).groupby('DATETIME',as_index=False).tail(1)
    x=demand.merge(pv,on='DATETIME',how='inner').merge(fc[['DATETIME','VERSION_DATETIME','AEMO_POE50_MW']],on='DATETIME',how='left')
    x['DATE']=x.DATETIME.dt.normalize()
    for f,n in [('Daily Max Temperature.xlsx','MAX_TEMP_C'),('Daily Min Temperature.xlsx','MIN_TEMP_C'),('Daily Rainfall.xlsx','RAINFALL_MM'),('Daily Solar Exposure.xlsx','SOLAR_EXPOSURE_MJ_M2')]: x=x.merge(weather(RAW/f,n),on='DATE',how='left')
    x=x.sort_values('DATETIME').reset_index(drop=True)
    x['YEAR']=x.DATETIME.dt.year; x['MONTH']=x.DATETIME.dt.month; x['HOUR']=x.DATETIME.dt.hour; x['MINUTE']=x.DATETIME.dt.minute; x['DAY_OF_WEEK']=x.DATETIME.dt.day_name(); x['WEEKEND_FLAG']=(x.DATETIME.dt.dayofweek>=5).astype(int); x['SEASON']=season(x.MONTH)
    for k in [1,2,4]: x[f'PV_LAG_{k}']=x.ROOFTOP_PV_MW.shift(k); x[f'DEMAND_LAG_{k}']=x.OPERATIONAL_DEMAND_MW.shift(k)
    x['DELTA_PV_MW']=x.ROOFTOP_PV_MW.diff(); x['DELTA_DEMAND_MW']=x.OPERATIONAL_DEMAND_MW.diff(); x['TARGET_DELTA_DEMAND_MW']=x.OPERATIONAL_DEMAND_MW.shift(-1)-x.OPERATIONAL_DEMAND_MW
    x['AEMO_DELTA_FORECAST_MW']=x.AEMO_POE50_MW.shift(-1)-x.OPERATIONAL_DEMAND_MW
    x['PV_RAMP_DIRECTION']=np.select([x.DELTA_PV_MW>0,x.DELTA_PV_MW<0],['Rising','Falling'],'Static')
    x.to_csv(PROCESSED/'modelling_dataset.csv',index=False)
    pd.DataFrame({'metric':['rows','start','end','duplicate timestamps','missing PV'],'value':[len(x),x.DATETIME.min(),x.DATETIME.max(),x.DATETIME.duplicated().sum(),x.ROOFTOP_PV_MW.isna().sum()]}).to_csv(TAB/'data_quality.csv',index=False)
    print(f'Prepared {len(x):,} rows')
if __name__=='__main__': main()
