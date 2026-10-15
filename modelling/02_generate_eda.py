"""Generate all descriptive tables and graphs directly from the processed dataset."""
from common import *
import matplotlib.pyplot as plt

def save(name): plt.tight_layout(); plt.savefig(FIG/name,dpi=180,bbox_inches='tight'); plt.close()
def main():
 x=pd.read_csv(PROCESSED/'modelling_dataset.csv',parse_dates=['DATETIME','DATE'])
 x.describe(include='all').transpose().to_csv(TAB/'descriptive_statistics.csv')
 cols=['ROOFTOP_PV_MW','OPERATIONAL_DEMAND_MW','DELTA_PV_MW','DELTA_DEMAND_MW','MAX_TEMP_C','MIN_TEMP_C','RAINFALL_MM','SOLAR_EXPOSURE_MJ_M2']
 x[cols].corr().to_csv(TAB/'correlation_matrix.csv')
 fig,ax=plt.subplots(1,2,figsize=(11,4)); ax[0].hist(np.log1p(x.ROOFTOP_PV_MW.dropna()),bins=50); ax[0].set(title='log(1 + rooftop PV)',xlabel='log MW',ylabel='Intervals'); ax[1].hist(x.OPERATIONAL_DEMAND_MW.dropna(),bins=50); ax[1].set(title='Operational demand',xlabel='MW',ylabel='Intervals'); save('figure_01_univariate_distributions.png')
 annual=x.groupby('YEAR').ROOFTOP_PV_MW.mean(); annual.to_csv(TAB/'annual_pv_growth.csv'); annual.plot(marker='o',title='Average rooftop PV by year'); plt.ylabel('MW'); save('figure_02_pv_growth_2017_2026.png')
 prof=x.groupby(['SEASON','HOUR'])[['ROOFTOP_PV_MW','OPERATIONAL_DEMAND_MW']].mean().reset_index(); prof.to_csv(TAB/'seasonal_profiles.csv',index=False); fig,ax=plt.subplots(1,2,figsize=(11,4)); [g.plot('HOUR','ROOFTOP_PV_MW',ax=ax[0],label=s) for s,g in prof.groupby('SEASON')]; [g.plot('HOUR','OPERATIONAL_DEMAND_MW',ax=ax[1],label=s) for s,g in prof.groupby('SEASON')]; ax[0].set(title='Rooftop PV profile',ylabel='MW'); ax[1].set(title='Demand profile',ylabel='MW'); save('figure_03_seasonal_profiles.png')
 c=x[cols].corr(); plt.figure(figsize=(8,6)); plt.imshow(c,cmap='coolwarm',vmin=-1,vmax=1); plt.xticks(range(len(c)),c.columns,rotation=80); plt.yticks(range(len(c)),c.columns); plt.colorbar(label='Correlation'); save('figure_04_correlation_matrix.png')
 q=pd.qcut(x.ROOFTOP_PV_MW,20,duplicates='drop'); b=x.groupby(q,observed=True)[['ROOFTOP_PV_MW','DELTA_DEMAND_MW']].mean(); b.to_csv(TAB/'binned_nonlinearity.csv'); b.plot(x='ROOFTOP_PV_MW',y='DELTA_DEMAND_MW',marker='o',legend=False,title='Binned non-linear PV-demand relationship'); plt.xlabel('Mean rooftop PV (MW)'); plt.ylabel('Mean demand change (MW)'); save('figure_05_binned_nonlinearity.png')
 print('EDA tables and figures written')
if __name__=='__main__': main()
