"""External benchmark, subgroup error analysis, paired-day bootstrap and model graphs."""
from common import *
from sklearn.metrics import mean_absolute_error,mean_squared_error
import matplotlib.pyplot as plt
def save(n): plt.tight_layout(); plt.savefig(FIG/n,dpi=180,bbox_inches='tight'); plt.close()
def main():
 x=pd.read_csv(PROCESSED/'holdout_predictions.csv',parse_dates=['DATETIME']); y=x.TARGET_DELTA_DEMAND_MW
 rows=pd.read_csv(TAB/'model_metrics.csv')
 valid=x.AEMO_DELTA_FORECAST_MW.notna(); rows=pd.concat([rows,pd.DataFrame([{'model':'AEMO POE50','specification':'aligned benchmark','MAE_MW':mean_absolute_error(y[valid],x.loc[valid,'AEMO_DELTA_FORECAST_MW']),'RMSE_MW':mean_squared_error(y[valid],x.loc[valid,'AEMO_DELTA_FORECAST_MW'])**.5}])],ignore_index=True); rows.to_csv(TAB/'model_metrics_with_aemo.csv',index=False)
 rows.assign(label=rows.model+' '+rows.specification).plot.bar(x='label',y='MAE_MW',legend=False,title='Chronological holdout MAE'); plt.ylabel('MAE (MW)'); save('figure_06_model_comparison.png')
 x['TIME_BLOCK']=pd.cut(x.DATETIME.dt.hour,[-1,5,11,17,23],labels=['00:00-06:00','06:00-12:00','12:00-18:00','18:00-24:00'])
 def gain(g): return pd.Series({'MAE_without_PV':np.abs(g.TARGET_DELTA_DEMAND_MW-g.pred_Tree_without_PV).mean(),'MAE_with_PV':np.abs(g.TARGET_DELTA_DEMAND_MW-g.pred_Tree_with_PV).mean()})
 tb=x.groupby('TIME_BLOCK',observed=True).apply(gain); tb['PV_GAIN_MW']=tb.MAE_without_PV-tb.MAE_with_PV; tb.to_csv(TAB/'pv_gain_by_time_block.csv'); tb.PV_GAIN_MW.plot.bar(title='Tree MAE reduction from adding PV by time block'); plt.ylabel('MAE reduction (MW)'); save('figure_08_pv_gain_by_time_block.png')
 x['SEASON']=np.select([x.DATETIME.dt.month.isin([12,1,2]),x.DATETIME.dt.month.isin([3,4,5]),x.DATETIME.dt.month.isin([6,7,8])],['Summer','Autumn','Winter'],'Spring'); ss=x.groupby('SEASON').apply(gain); ss['PV_GAIN_MW']=ss.MAE_without_PV-ss.MAE_with_PV; ss.to_csv(TAB/'pv_gain_by_season.csv'); ss.PV_GAIN_MW.plot.bar(title='Tree MAE reduction from adding PV by season'); plt.ylabel('MAE reduction (MW)'); save('figure_09_pv_gain_by_season.png')
 x['DATE']=x.DATETIME.dt.date; daily=x.groupby('DATE').apply(lambda g:np.abs(g.TARGET_DELTA_DEMAND_MW-g.pred_Tree_without_PV).mean()-np.abs(g.TARGET_DELTA_DEMAND_MW-g.pred_Tree_with_PV).mean()); rng=np.random.default_rng(SEED); boot=np.array([rng.choice(daily,len(daily),replace=True).mean() for _ in range(2000)]); pd.DataFrame({'bootstrap_gain_MW':boot}).to_csv(TAB/'paired_daily_bootstrap_pv_gain.csv',index=False); plt.hist(boot,bins=40); plt.axvline(0,color='black'); plt.title('Paired daily bootstrap: tree MAE gain from PV'); plt.xlabel('MAE reduction (MW)'); save('figure_17_bootstrap_uncertainty.png')
 ex=x.iloc[:192]; plt.figure(figsize=(12,4)); plt.plot(ex.DATETIME,ex.TARGET_DELTA_DEMAND_MW,label='Observed'); plt.plot(ex.DATETIME,ex.pred_Tree_without_PV,label='Tree without PV'); plt.plot(ex.DATETIME,ex.pred_Tree_with_PV,label='Tree with PV'); plt.legend(); plt.ylabel('Next-half-hour change (MW)'); plt.title('Representative holdout forecast'); save('figure_10_forecast_example.png')
 res=y-x.pred_Tree_with_PV; fig,ax=plt.subplots(1,2,figsize=(11,4)); ax[0].hist(res,bins=60); ax[0].set(title='Residual distribution',xlabel='MW'); ax[1].plot(x.DATETIME.iloc[:500],res.iloc[:500]); ax[1].set(title='Residual sequence',ylabel='MW'); save('figure_11_residual_diagnostics.png')
 print('Validation tables and figures written')
if __name__=='__main__': main()
