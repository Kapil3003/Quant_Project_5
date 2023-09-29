## https://discuss.streamlit.io/t/launching-streamlit-webapp-from-desktop-shortcut/26297
## pipreqs (to create requirement file needed for streamshare)
## cd to current folder 
## streamlit run GBM_simulation_Streamlit.py

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



# Create a function for GBM simulation 
import numpy as np 

def simulate_gbm(S0, mu,sigma, days, num_simulations):
    
    # Time increment (daily)
    ## As we have daily returns - instead of scaling time,mu,sigma statistically, 
    ## Lets just make this simple by always having increament of one day.             
    dt = 1 
    
    ## Creating simulation array of number of days * num of simulations 
    simulations = np.zeros((days+1, num_simulations))
    
    ## # Calculating Random component assuming normal distribution
    wt_array = np.random.normal(size = (days,num_simulations))
    
    for i in range(num_simulations):  # for every simulation
        
        price_path = [S0] # initial price
                
        for j in range(days): # for each day 
            
                
            Wt = wt_array[j,i]  
            price = price_path[-1] * np.exp((mu - 0.5 * sigma**2) * dt + sigma * Wt)
            price_path.append(price)
            
            
        simulations[:, i] = price_path[:]
        
    return simulations


## Testing simulate_gbm
S0 = 100
mu =  estimated_drift 
sigma = estimated_volatility
num_sim = 1000
num_days = 25

test_simulate = simulate_gbm(S0, mu,sigma, num_days, num_sim)

## Plot test results
plt.figure(figsize=(14, 7))
plt.plot(test_simulate)
plt.xlabel("Trading Days")
plt.ylabel("Stock Price")
plt.title(
    " Realizations of Geometric Brownian Motion \n $dS_t = \mu S_t dt + \sigma S_t dW_t$\n $S_0 = {0}, \mu = {1} \%, \sigma = {2} \% $\n Number of Simulations = {3} ".format(round(S0,2), round(mu,6), round(sigma,6),num_sim)
)
plt.grid(True)
plt.tight_layout()
plt.xticks(rotation=45)  
plt.show()