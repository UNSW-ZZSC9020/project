# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""


import pandas as pd
import zipfile as zp
import numpy as np
import os as os
import matplotlib.pyplot as plt


#zf = zp.ZipFile(r'temp\temperature_nsw.csv.zip')
#result=pd.read_csv(zf.open('temperature_nsw.csv'),index_col=1,nrows=100)
#result=pd.read_csv(zf.open('temperature_nsw.csv'))
#saving the required fields into another csv file
#print(result.dtypes)
#print(result['LOCATION'].astype(str))

'''
def create_holiday_file():
    file_dir = 'temp/PublicHolidays'
    
    for f in os.listdir(file_dir):
        file_path = file_dir + '/' + f
        df = pd.read_csv(file_path, header=None, skiprows=[0],usecols=[0,1,4])
        df = df.loc[df[4].str.contains('NSW', case=False)]
        #print(df.head())
'''

def mod_read_csv(file_names):
    return pd.read_csv(file_names, header=None, skiprows=[0],usecols=[0,1,4])            
        
def get_nsw_holidays():
    file_dir = os.getcwd() + '\\temp\\PublicHolidays\\'
    #print(file_dir)
    os.chdir(file_dir)
    file_names = os.listdir(file_dir)
    #print(file_names)
    df = pd.concat(map(mod_read_csv, file_names))
    df = df.loc[df[4].str.contains('NSW', case=False) | df[4].str.contains('NAT', case=False)]
    df = df.iloc[:,[0,1]]
    df.columns = ['Holiday_Date','Description']
    df['Holiday_Date'] = pd.to_datetime(df['Holiday_Date'], format='%Y%m%d')
    df = df.drop_duplicates()
    #print(df.head(20))
    #df.to_csv('..\\holidays.csv')
    return df


def create_date_dim(start, end):

    df_holidays = get_nsw_holidays()

    df = pd.DataFrame({"Calendar_Date": pd.date_range(start, end)})
    df["DayOfWeek"] = df.Calendar_Date.dt.isocalendar().day
    df["Week"] = df.Calendar_Date.dt.week
    df["Quarter"] = df.Calendar_Date.dt.quarter
    df["Month"] = df.Calendar_Date.dt.month
    df["Year"] = df.Calendar_Date.dt.year
    df["Year_half"] = (df.Quarter + 1) // 2
    df["Summer"] = df.Month
    df['Summer'] = df['Summer'].apply(lambda x: 1 if x in [12, 1, 2] else 0)
    df["Autumn"] = df.Month
    df['Autumn'] = df['Autumn'].apply(lambda x: 1 if x in [3, 4, 5] else 0)
    df["Winter"] = df.Month
    df['Winter'] = df['Winter'].apply(lambda x: 1 if x in [6, 7, 8] else 0)
    df["Spring"] = df.Month
    df['Spring'] = df['Spring'].apply(lambda x: 1 if x in [9, 10, 11] else 0)
    df["is_weekday"] = np.where(df["DayOfWeek"] > 5 , 0, 1)
    
    
    
    full_data = df.merge(df_holidays, left_on='Calendar_Date', right_on='Holiday_Date', how='left')
    full_data["is_holiday"] = np.where(full_data["Holiday_Date"].isnull() == True, 0, 1)    
    full_data = full_data.drop("Holiday_Date", axis=1)
    return full_data

df_date_dm = create_date_dim('2014-01-01','2022-12-31')

#df_date_dm.to_csv('..\\date_dim.csv')
#print(df_date_dm.columns)




def data_prep_plot():
    #print('here')
    df_demand = pd.read_csv('D:/UNSW/Capstone/Temp/totaldemand_nsw.csv')
    df_date = pd.read_csv('D:/UNSW/Capstone/Temp/date_dim.csv')
    df_demand['DATETIME'] = pd.to_datetime(df_demand['DATETIME'], format='%d/%m/%Y %H:%M')
    df_demand['DEMAND_DATE'] = pd.to_datetime(df_demand.DATETIME.dt.date, format='%Y-%m-%d')
    df_date['Calendar_Date'] = pd.to_datetime(df_date['Calendar_Date'], format='%Y-%m-%d')
    
    
    #print(df_demand.head(5))
    #print(df_date.head(5))
    #print(df_demand.dtypes)
    #print(df_date.dtypes)
    #print(df_demand.REGIONID.unique())
    
    df_final = df_demand.merge(df_date, left_on='DEMAND_DATE', right_on='Calendar_Date')
    #print(df_final.head(10))
    return df_final
    
def draw_plot_1(df_plot):
    
    
    #df_plot[df_plot['Year'] == 2015].plot(x='Month', y='TOTALDEMAND', title='Total Demand in NSW in 2015')
    
    print(df_plot.dtypes)
    df_plot = df_plot.loc[(df_plot['Year'] > 2014) & (df_plot['Year'] < 2020)]
    print(df_plot.Year.unique())
    rslt_df0 = df_plot[['Month','TOTALDEMAND']].loc[(df_plot['is_holiday'] == 0) | (df_plot['is_weekday'] == 1)]
    rslt_df1 = df_plot[['Month','TOTALDEMAND']].loc[(df_plot['is_holiday'] == 1) | (df_plot['is_weekday'] ==0)]
    print(rslt_df0.tail(10))
    mnth_labels = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
    plt.plot(rslt_df0.groupby('Month').mean())
    plt.xticks(mnth_labels)
    plt.plot(rslt_df1.groupby('Month').mean())

def draw_plot_2(df_plot):
    
    
    #df_plot[df_plot['Year'] == 2015].plot(x='Month', y='TOTALDEMAND', title='Total Demand in NSW in 2015')
    
    print(df_plot.dtypes)
    #df_plot = df_plot.loc[(df_plot['Year'] > 2014) & (df_plot['Year'] < 2020)]
    #print(df_plot.loc[df_plot.DATETIME.dt.time >= pd.Timestamp('07:00:00').time()])
    
    df_plot["Peak"] = np.where((df_plot.DATETIME.dt.time >= pd.Timestamp('07:00:00').time()) & (df_plot.DATETIME.dt.time <= pd.Timestamp('22:00:00').time()), 1, 0)
    #print(df_plot[['DATETIME','peak']])
     
    rslt_df0 = df_plot[['Month','TOTALDEMAND']].loc[((df_plot['is_holiday'] == 0) | (df_plot['is_weekday'] == 1)) & (df_plot['Peak']==1)]
    rslt_df1 = df_plot[['Month','TOTALDEMAND']].loc[((df_plot['is_holiday'] == 0) | (df_plot['is_weekday'] == 1))]
    rslt_df2 = df_plot[['Month','TOTALDEMAND']].loc[((df_plot['is_holiday'] == 0) | (df_plot['is_weekday'] == 1)) & (df_plot['Peak']==0)]
    #mnth_labels = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
    plt.plot(rslt_df0.groupby('Month').mean(), color='blue', linestyle='--')
    plt.plot(rslt_df1.groupby('Month').mean(), color='darkblue')
    plt.plot(rslt_df2.groupby('Month').mean(), color='lightblue', linestyle='--')
    
    
def draw_plot_3(df_plot):
    
    
    print(df_plot.dtypes)
    #df_plot = df_plot.loc[(df_plot['Year'] > 2014) & (df_plot['Year'] < 2020)]
    #print(df_plot.loc[df_plot.DATETIME.dt.time >= pd.Timestamp('07:00:00').time()])
    
    df_plot["Peak"] = np.where((df_plot.DATETIME.dt.time >= pd.Timestamp('07:00:00').time()) & (df_plot.DATETIME.dt.time <= pd.Timestamp('22:00:00').time()), 1, 0)
    #print(df_plot[['DATETIME','peak']])
     
    rslt_df0 = df_plot[['Month','TOTALDEMAND']].loc[((df_plot['is_holiday'] == 0) | (df_plot['is_weekday'] == 1)) & (df_plot['Peak']==1)]
    rslt_df1 = df_plot[['Month','TOTALDEMAND']].loc[((df_plot['is_holiday'] == 0) | (df_plot['is_weekday'] == 1))]
    rslt_df2 = df_plot[['Month','TOTALDEMAND']].loc[((df_plot['is_holiday'] == 0) | (df_plot['is_weekday'] == 1)) & (df_plot['Peak']==0)]
    #mnth_labels = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
    plt.plot(rslt_df0.groupby('Month').mean(), color='blue', linestyle='--')
    plt.plot(rslt_df1.groupby('Month').mean(), color='darkblue')
    plt.plot(rslt_df2.groupby('Month').mean(), color='lightblue', linestyle='--')
    
 
    
df_plot = data_prep_plot()
#draw_plot_1(df_plot)
draw_plot_2(df_plot)
draw_plot_3(df_plot)
    
 