## https://discuss.streamlit.io/t/launching-streamlit-webapp-from-desktop-shortcut/26297
## pipreqs (to create requirement file needed for streamshare)
## cd to current folder 
## streamlit run OI_Analysis_Streamlit_cloud.py

########################## Initialization - Lib and Settings #####################

import streamlit as st
from streamlit_autorefresh import st_autorefresh

import pandas as pd
import numpy as np
import datetime
from datetime import timedelta
import time
from os import path
from nsepython import * 

import plotly.express as px 
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# import custom functions 
import dashboard_functions

########################## Streamlit Settings #####################
st.set_page_config(layout="wide")
st_autorefresh(interval= 60 * 1000, key="dataframerefresh")   # every 5 min



#################################################################################

################################### Computations ################################

#################################################################################


########## Download Option Chain ##########

# Create a drop down box where instrument and expiry can be selected.
Instrument_name = 'BANKNIFTY'

# expiry_dates = dashboard_functions.get_expiry(Instrument_name) #[datetime.datetime.strptime(x, '%d-%b-%Y').date() for x in expiry_list(Instrument_name)]

# expiry =  expiry_dates[0]
# Option_df, ltp, crontime,maxpain,pcr = dashboard_functions.Calculate_OptionChain_fetch(Instrument_name,expiry.strftime('%d-%b-%Y'))


### Unfortunately NSE doesnt allow requrests from servers and Fetching/webscrapping expiry or option chain is not possible when hosted on the server
### using static files for streamlit server -


# Get the list of all files and directories
import os
path = "./Data"
dir_list = os.listdir(path) 
dir_list.sort()
# st.write(dir_list)
filename = [x for x in dir_list if x.startswith("G")][-1]

Option_df = pd.read_csv("./Data/"+dir_list[-1])

# st.dataframe(Option_df)
Option_df = Option_df[["Call_COI","Call_OI","Call_IV","Call_LTP","Strike_Price","Put_LTP","Put_IV","Put_OI","Put_COI"]]

expiry = datetime.datetime.strptime(filename[7:17], '%Y_%m_%d').date()

ltp = pd.read_csv("./Data/"+filename).ltp.iloc[-1]
crontime = pd.read_csv("./Data/"+filename)["Unnamed: 0"].iloc[-1]
crontime = datetime.datetime.strptime(crontime, '%Y-%m-%d %H:%M:%S').strftime('%d-%b-%Y %H:%M:%S')

maxpain = dashboard_functions.maxpain_fn(Option_df)
pcr = Option_df.Put_OI.sum()/Option_df.Call_OI.sum()




Option_df = Option_df.astype(float) ## Need to convert everything to float
Option_df_sum = round(Option_df.sum(),2)[["Call_OI","Put_OI","Call_IV","Put_IV"]]



########## Calculate Greeks ##########

import py_vollib_vectorized
from datetime import timedelta
import pytz
IST = pytz.timezone('Asia/Kolkata')


## Segregating CE PE
Option_df_ce = Option_df[["Strike_Price","Call_LTP","Call_IV","Call_OI","Call_COI"]].copy()
columns = ["Strike_Price","LTP","IV","OI","COI"]
Option_df_ce.columns = columns
Option_df_ce = Option_df_ce[Option_df_ce.LTP !=0]
Option_df_ce["type"] = 'c'

Option_df_pe = Option_df[["Strike_Price","Put_LTP","Put_IV","Put_OI","Put_COI"]].copy()
columns = ["Strike_Price","LTP","IV","OI","COI"]
Option_df_pe.columns = columns
Option_df_pe = Option_df_pe[Option_df_pe.LTP !=0]
Option_df_pe["type"] = 'p'

greeks_df_all = pd.concat([Option_df_ce,Option_df_pe])
greeks_df_all = greeks_df_all.reset_index(drop = True)



## Required parameters for black scholes

underlying_Price = ltp
Interest_Rate = 0.1 # As mentioned on NSE website


Expiry_time = datetime.datetime(expiry.year,expiry.month,expiry.day,15,30,00,0) 
Current_time = datetime.datetime.strptime(crontime, '%d-%b-%Y %H:%M:%S')
Time_to_Expiration = (Expiry_time - Current_time)/timedelta(days=1)/365


## Calculating IV and Greeks

greeks_df_all['iv'] = py_vollib_vectorized.vectorized_implied_volatility(greeks_df_all.LTP, underlying_Price, greeks_df_all.Strike_Price, Time_to_Expiration,Interest_Rate, greeks_df_all.type, model='black_scholes', return_as='dataframe')

greeks_df_all['vega'] = py_vollib_vectorized.vectorized_vega(greeks_df_all.type, underlying_Price, greeks_df_all.Strike_Price, Time_to_Expiration, Interest_Rate, greeks_df_all.iv, model='black_scholes', return_as='dataframe') 
greeks_df_all['theta'] = py_vollib_vectorized.vectorized_theta(greeks_df_all.type, underlying_Price, greeks_df_all.Strike_Price, Time_to_Expiration, Interest_Rate, greeks_df_all.iv, model='black_scholes', return_as='dataframe') 
greeks_df_all['delta'] = py_vollib_vectorized.vectorized_delta(greeks_df_all.type, underlying_Price, greeks_df_all.Strike_Price, Time_to_Expiration, Interest_Rate, greeks_df_all.iv, model='black_scholes', return_as='dataframe')
greeks_df_all['gamma'] = py_vollib_vectorized.vectorized_gamma(greeks_df_all.type, underlying_Price, greeks_df_all.Strike_Price, Time_to_Expiration, Interest_Rate, greeks_df_all.iv, model='black_scholes', return_as='dataframe')

PE_df = greeks_df_all[greeks_df_all["type"]=="p"].copy()
CE_df = greeks_df_all[greeks_df_all["type"]=="c"].copy()


## Saving -ve PE delta so that CE and PE can be compared on the graph
data_greeks=[[CE_df["gamma"].sum(),CE_df["vega"].sum(),CE_df["theta"].sum(),CE_df["delta"].sum() ,-PE_df["delta"].sum(),PE_df["theta"].sum(),PE_df["vega"].sum()  ,PE_df["gamma"].sum()]]
greeks_sum=pd.DataFrame(data_greeks,columns=["c_gamma","c_vega","c_theta","c_delta","p_delta","p_theta","p_vega","p_gamma"])


##### Unnecssary step - to display greeks
columns = ['Strike_Price','iv',"vega",'theta','delta','gamma']
greeks_df = pd.merge(greeks_df_all[greeks_df_all.type =='c'][columns],greeks_df_all[greeks_df_all.type =='p'][columns], on='Strike_Price')
columns =["Strike_Price","Call_IV","c_vega","c_theta","c_delta","c_gamma","Put_IV","p_vega","p_theta","p_delta","p_gamma"]
greeks_df.columns = columns
greeks_df = greeks_df[["c_gamma","c_vega","c_theta","c_delta","Call_IV","Strike_Price","Put_IV","p_delta","p_theta","p_vega","p_gamma"]]

############# Append data to existing file ###############

timestamp = datetime.datetime.now()

# Combine DataFrames horizontally
results_df = pd.concat([ Option_df_sum.to_frame().T , greeks_sum], axis=1)
results_df.index = [Current_time] # Substitute it with crontime
results_df['maxpain'] = maxpain

# # Append to Existing File
path_save = "./Data/Greeks_"  + expiry.strftime('%Y_%m_%d')  + "_"+Instrument_name + ".csv"
# results_df.to_csv(path_save, mode='a',header=not (path.exists(path_save)))

############# Load All data ####################

df = pd.read_csv(path_save)     
df["Unnamed: 0"]=pd.to_datetime(df["Unnamed: 0"],format='%Y-%m-%d %H:%M:%S.%f%z')
df["oi_direction"] = df["Put_OI"] - df["Call_OI"] 
df.rename(columns={'Unnamed: 0': 'Timestamp'}, inplace=True)
# df['Timestamp'] = df['Unnamed: 0'].dt.strftime('%r')

# Get todays data
Today = df.Timestamp.iloc[-1].date() #datetime.datetime.now().date()
df = df[df['Timestamp'].dt.date == Today]
df
############################ Prepare Graphs ############################

Option_chain_df =Option_df[["Call_COI","Call_OI","Call_LTP","Strike_Price","Put_LTP","Put_OI","Put_COI"]].copy()
Option_chain_df = Option_chain_df[(Option_chain_df.Strike_Price < ltp + 3000) & (Option_chain_df.Strike_Price > ltp - 3000)]
Option_chain_plot = dashboard_functions.get_option_chain_plot (Option_chain_df,Instrument_name)


theta_chart = dashboard_functions.multi_line_chart("Theta"	,df,"Timestamp","c_theta"	,"p_theta")
delta_chart = dashboard_functions.multi_line_chart("Delta"	,df,"Timestamp","c_delta"	,"p_delta")
vega_chart  = dashboard_functions.multi_line_chart("Vega"	,df,"Timestamp","c_vega"	,"p_vega")
gamma_chart = dashboard_functions.multi_line_chart("Gamma"	,df,"Timestamp","c_gamma"	,"p_gamma")

maxp_chart  = dashboard_functions.line_chart("MaxPain",df,"Timestamp","maxpain")
OI_direction_chart  = dashboard_functions.line_chart("OI_direction",df,"Timestamp","oi_direction")


############################ Streamlit App UI ###########################


st.title("Real-Time Options Chain Data Analysis Dashboard")


col_1, col_2,col_3, col_4,col_5, col_6 = st.columns(6)
with col_1:
	st.metric(label="Instrument", value=Instrument_name)

with col_2:
	st.metric(label="Expiry", value=expiry.strftime('%d-%b-%y'))

with col_3:
	st.metric(label="Last Traded Price", value=ltp)

with col_4:
	st.metric(label="MaxPain", value=maxpain)

with col_5:
	st.metric(label="PCR", value=round(pcr,2))

with col_6:
	st.metric(label="Last Update", value= Current_time.strftime('%H:%M:%S'))


st.divider()
st.header("Open Interest Analysis")

col_1, col_2 = st.columns([2,2])
with col_1:
	st.plotly_chart(OI_direction_chart, use_container_width=True)
	st.plotly_chart(maxp_chart, use_container_width=True)

with col_2:
	st.plotly_chart(Option_chain_plot, use_container_width=True)

st.divider()
st.header("Option Greeks Analysis - OTM options")

col_1, col_2 = st.columns([2,2])

with col_1:
	st.plotly_chart(vega_chart, use_container_width=True)
	st.plotly_chart(gamma_chart, use_container_width=True)
with col_2:
	st.plotly_chart(theta_chart, use_container_width=True)
	st.plotly_chart(delta_chart, use_container_width=True)


st.divider()
st.header("Complete Data")

col_1, col_2 = st.columns([2,2])
with col_1:
	st.subheader("Option Chain")
	st.dataframe(Option_chain_df, use_container_width=True,height=550)


with col_2:
	st.subheader("Option Greeks")
	st.dataframe(greeks_df, use_container_width=True,height=550)



st.divider()

"## Code"

"For detail code refer my github repo :- "
" 1. [[webApp]](https://quantproject1-csovwwndasw9kuk2vpygjp.streamlit.app/) [Predictive Analysis of Stock Trajectories using Geometric Brownian Motion](https://github.com/Kapil3003/Quant_Project_1/blob/main/Project_1_GBM.ipynb)"

" 2. [Comprehensive VaR Analysis: Methods Comparison, Backtesting, and Stress Testing](https://github.com/Kapil3003/Quant_Project_2/blob/main/Project_2_VaR_Analysis.ipynb)"

" 3. [Robust Trading Strategy Development using Walk Forward Optimization](https://github.com/Kapil3003/Quant_Project_3/blob/main/Project_3_StrategyDevelopment.ipynb)"

" 4. [Market Volatility Forecasting: An ExtensiveComparative Study](https://github.com/Kapil3003/Quant_Project_4/blob/main/Project_4_Volatility%20Forecasting.ipynb)"

" 5. [[webApp]](https://quantproject5-gcs2rtyqub8wj8osxwegu2.streamlit.app/) [Real-Time Options Chain Data Analysis Dashboard](https://github.com/Kapil3003/Quant_Project_5)"

