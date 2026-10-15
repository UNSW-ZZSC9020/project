"""Fit matched with-PV and without-PV models on the same chronological holdout."""
from common import *
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder,StandardScaler,SplineTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error,mean_squared_error
import statsmodels.api as sm
import joblib
BASE=['DEMAND_LAG_1','DELTA_DEMAND_MW','HOUR','WEEKEND_FLAG','MONTH','MAX_TEMP_C','MIN_TEMP_C','RAINFALL_MM','SOLAR_EXPOSURE_MJ_M2']; PV=['ROOFTOP_PV_MW','DELTA_PV_MW']
def metrics(y,p): return {'MAE_MW':mean_absolute_error(y,p),'RMSE_MW':mean_squared_error(y,p)**0.5}
def design(cols): return make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),LinearRegression())
def tree(): return make_pipeline(SimpleImputer(strategy='median'),HistGradientBoostingRegressor(max_iter=100,max_leaf_nodes=15,learning_rate=.08,min_samples_leaf=30,l2_regularization=1,random_state=SEED))
def main():
 x=pd.read_csv(PROCESSED/'modelling_dataset.csv',parse_dates=['DATETIME']).dropna(subset=['TARGET_DELTA_DEMAND_MW']).sort_values('DATETIME'); cut=int(len(x)*.8); tr,te=x.iloc[:cut],x.iloc[cut:].copy(); ytr=tr.TARGET_DELTA_DEMAND_MW; yte=te.TARGET_DELTA_DEMAND_MW
 rows=[]
 for name,model in [('OLS',design(BASE)),('Tree',tree())]:
  for flag,cols in [('without_PV',BASE),('with_PV',BASE+PV)]:
   model.fit(tr[cols],ytr); p=model.predict(te[cols]); te[f'pred_{name}_{flag}']=p; rows.append({'model':name,'specification':flag,**metrics(yte,p)})
 # Spline-additive comparison: splines over numeric predictors, then linear regression.
 for flag,cols in [('without_PV',BASE),('with_PV',BASE+PV)]:
  model=make_pipeline(SimpleImputer(strategy='median'),SplineTransformer(n_knots=5,degree=3),LinearRegression()); model.fit(tr[cols],ytr); p=model.predict(te[cols]); te[f'pred_Spline_{flag}']=p; rows.append({'model':'Spline','specification':flag,**metrics(yte,p)})
 # HAC OLS supports coefficient interpretation; prediction comparison stays matched.
 z=tr[BASE+PV].copy(); z=z.fillna(z.median(numeric_only=True)); fit=sm.OLS(ytr,sm.add_constant(z)).fit(cov_type='HAC',cov_kwds={'maxlags':48}); pd.DataFrame({'coefficient':fit.params,'std_error_HAC':fit.bse,'p_value':fit.pvalues}).to_csv(MODELS/'ols_hac_coefficients.csv')
 pd.DataFrame(rows).to_csv(TAB/'model_metrics.csv',index=False); te.to_csv(PROCESSED/'holdout_predictions.csv',index=False)
 json.dump({'seed':SEED,'train_fraction':.8,'tree':{'max_iter':100,'max_leaf_nodes':15,'learning_rate':.08,'min_samples_leaf':30,'l2_regularization':1},'target':'TARGET_DELTA_DEMAND_MW','base_features':BASE,'pv_features':PV},open(MODELS/'model_settings.json','w'),indent=2)
 print(pd.DataFrame(rows).to_string(index=False))
if __name__=='__main__': main()
