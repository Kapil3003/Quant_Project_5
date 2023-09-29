########################## Initialization - Lib and Settings #####################


import streamlit as st
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



#################################################################################

################################### Required Functions ##########################

#################################################################################

def maxpain_fn(Option_chain):

    i=0
    pain = []
    while i<len(Option_chain):
        
        pain_tmp = 0
        ATM_p = Option_chain.iloc[i]['Strike_Price']

        # All strike price below ATM_p (call= o PE = full)
        j=0
        while j<i:
            pain_tmp = pain_tmp+ Option_chain.iloc[j]['Call_OI'] * (ATM_p - Option_chain.iloc[j]['Strike_Price'])
            j = j+1

        # All strike price above ATM_p (call= full PE = 0)
        k=len(Option_chain)-1
        while k>i:
            pain_tmp = pain_tmp+ Option_chain.iloc[k]['Put_OI'] * (Option_chain.iloc[k]['Strike_Price']- ATM_p)
            #print(Option_chain.iloc[k]['Strike_Price'])       
            k = k-1

        pain.append(pain_tmp)
        i=i+1

    maxpain = Option_chain.iloc[pain.index(min(pain))]['Strike_Price']
    
    return maxpain

def Calculate_OptionChain_fetch(Instrument_name,expiry):
    
	Option_chain, ltp, crontime = oi_chain_builder(Instrument_name,expiry,"compact")

	Option_chain=Option_chain[['PUTS_Chng in OI','PUTS_OI','PUTS_IV','PUTS_LTP','Strike Price','CALLS_LTP','CALLS_IV','CALLS_OI','CALLS_Chng in OI']]
	columns = ["Put_COI","Put_OI","Put_IV","Put_LTP","Strike_Price","Call_LTP","Call_IV","Call_OI","Call_COI"]
	Option_chain.columns = columns

	maxpain=maxpain_fn(Option_chain)

	Option_chain  = Option_chain[["Call_COI","Call_OI","Call_IV","Call_LTP","Strike_Price","Put_LTP","Put_IV","Put_OI","Put_COI"]]

	pcr = Option_chain.Put_OI.sum()/Option_chain.Call_OI.sum()
	# Option_chain.to_csv(path_d  + Instrument_name + ".csv")


	return Option_chain, ltp, crontime,maxpain,pcr

@st.cache_data 
def get_expiry(Instrument_name):
	print("Get Expiry running")
	return [datetime.datetime.strptime(x, '%d-%b-%Y').date() for x in expiry_list(Instrument_name)]


#################################################################################

################################### Graphs Functions ############################

#################################################################################

def get_option_chain_plot (Option_chain_df,Instrument_name):
	Option_chain_plot = make_subplots( rows = 10, cols = 3,
	specs=[
	        [{"type": "bar", "rowspan": 6, "colspan": 3}, None, None],
	        [    None, None, None],
	        [    None, None, None],
	        [    None, None, None],
	        [    None, None, None],
	        [    None, None, None],
	        [    None, None, None],
	        [    {"type": "bar", "rowspan": 3, "colspan": 3}, None, None],
	        [    None, None, None],
	        [    None, None, None],
	                
	      ],
	subplot_titles=("OI","COI", "","","","", "","")
	)


	Option_chain_plot.add_trace(
	    go.Bar(
	        x=Option_chain_df['Strike_Price'],
	        y=Option_chain_df['Call_COI'],
	        name='CE_COI',
	        marker=dict(color="green"), 
	        showlegend=True,
	        width = 100,
	    ),
	    row=8, col=1)

	Option_chain_plot.add_trace(
		go.Bar(
			x=Option_chain_df['Strike_Price'],
			y=Option_chain_df['Put_COI'],
			name='PE_COI',
			marker=dict(color="red"), 
			showlegend=True,
			width = 50,
		),
		row=8, col=1)

	Option_chain_plot.update_layout(barmode='overlay')
	Option_chain_plot.update_layout(barmode='overlay')

	Option_chain_plot.add_trace(
		go.Bar(
			x=Option_chain_df['Strike_Price'],
			y=Option_chain_df['Call_OI'],    
			name='CE_OI',
			marker=dict(color="green"), 
			showlegend=True,
			width = 100,
		),
		row=1, col=1)

	Option_chain_plot.add_trace(
		go.Bar(
			x=Option_chain_df['Strike_Price'],
			y=Option_chain_df['Put_OI'],    
			name='PE_OI',
			marker=dict(color="red"), 
			showlegend=True,
			width = 50,
		),
		row=1, col=1)

	Option_chain_plot.update_layout(
		height=600 ,# width=1440,
		template="plotly_dark",
		title = "Option Chain Open Interest Analysis:-" + str(Instrument_name),
		#showlegend=True, 
		#legend=dict(yanchor="top",y=0.5,xanchor="left",x=0.5),
		#legend_orientation="h",
		#legend=dict(x=0.65, y=0.8),

		geo = dict(
			projection_type="orthographic",
			showcoastlines=True,
			landcolor="white", 
			showland= True,
			showocean = True,
			lakecolor="LightBlue"
	    ),)    


	return Option_chain_plot


# Graph properties
background = {
'plot_bgcolor': 'rgba(0, 0, 0, 0)',
'paper_bgcolor': 'rgba(0, 0, 0, 0)',
}
grid_thickness = 1;
grid_colour = "grey"
background_colour = "black"
blue_color = '#0000ff'
red_color = "#ff0000"
width_line= 3
shape_height = 300
shape_width = 900

def multi_line_chart(Tilte,df,x_name,y_name1,y_name2):

	chart_multi = px.line(df, x=x_name, y=[y_name1,y_name2],height = shape_height,width = shape_width,title=Tilte,color_discrete_map={
		y_name1: "blue",
		y_name2: "red"
	})

	chart_multi.layout.plot_bgcolor= background_colour
	chart_multi.update_traces( line_width=width_line)
	chart_multi.update_xaxes( gridwidth=grid_thickness,gridcolor=grid_colour)
	chart_multi.update_yaxes( gridwidth=grid_thickness,gridcolor=grid_colour)
	chart_multi.layout.yaxis.title=Tilte

	return chart_multi


def line_chart(Tilte,df,x_name,y_name):

	line_chart = px.line(df, x=x_name, y=y_name,height = shape_height,width = shape_width,title=Tilte)

	line_chart.layout.plot_bgcolor= background_colour
	line_chart.update_traces( line_width=width_line)
	line_chart.update_xaxes( gridwidth=grid_thickness,gridcolor=grid_colour)
	line_chart.update_yaxes( gridwidth=grid_thickness,gridcolor=grid_colour)
	line_chart.layout.yaxis.title=Tilte

	return line_chart

