import streamlit as st
import plotly
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import pytz
import ta

from autogui import autogui

def get_data(ticker, period, interval):
    data = (
        yf.Ticker(ticker)
        .history(interval=interval,period=period)
    ).reset_index()
    return data


def process_data(data):
    data.rename(columns={'Date': 'Datetime'}, inplace=True)
    return data
    if data.index.tzinfo is None:
        data.index = data.index.tz_localize('UTC')
    data.index = data.index.tz_convert('US/Eastern')
#    data.reset_index(inplace=True)
    data.rename(columns={'Date': 'Datetime'}, inplace=True)
    return data



def stock_plot(data: pd.DataFrame, forecast: pd.DataFrame = None) -> plotly.graph_objs.Figure:
    """
    {IO}{VISUALIZATION} You are also a specialist in stock market. Given a
dataframe with typical stock price columns and Date, and another dataframe
forecast (if exists) with column `Price`, build a plot of the price over time
(Close price) and a dashed line for forecasting. Provide the figure but never
plot it.
    """

    plotly_fig = autogui("Stock price plot", init_prompt="plot price curve with candle stick or simple line. Also add a checkbox to whether or not plot the prediction in dashed line", model="MODEL_NAME", provider="PROVIDER_NAME")
    return plotly_fig


    

def stock_forecast(data: pd.DataFrame) -> pd.DataFrame:
    """
    {IO} You are a specialist in implementing time series forecasting solutions
from a given stock price dataframe which has the typical data columns.
Solutions must provide another dataframe as output, with the prediction curve
under columns `Date` and `Price`. Make sure to keep dates in the right format
and avoid data leakage and do not use tensorflow. Always return a dataframe,
never a figure or any kind of plot.
    """

    prices = autogui("Forecasting", init_prompt="predict future prices based on dynamic systems. make forecast horizon customizable, as well as all other involve parameters", model="MODEL_NAME", provider="PROVIDER_NAME")

    return prices




st.set_page_config(layout="wide")
header_area = st.empty()
tab_graph, tab_data = st.tabs(["Graph","Data"])

st.sidebar.header('Graph')

c1,c2 = st.sidebar.columns([0.3,0.7])

def_ticker = 'ADBE'
ticker = c1.text_input('Ticker', def_ticker)
ticker = ticker if ticker else def_ticker

periods = ['1d', '1wk', '1mo', '1y', 'max']
time_period = c2.select_slider('Time Period',periods, value='1y')
intervmap = dict(d='1m', wk='30m', mo='1d', y='1wk', ax='1wk')
time_interval = intervmap.get(time_period[1:])
time_interval = c2.select_slider('Time interval (granularity)',set(intervmap.values()),value=intervmap.get(time_period[1:]))

plot_config = st.sidebar.container()

data = get_data(ticker, time_period, time_interval)
#data = process_data(data)

if data.shape[0] <= 1:
    c2.markdown(":material/error: <sub>Interval not available.</sub>", unsafe_allow_html=True)
    st.stop()


st.sidebar.header('Forecasting')


with st.sidebar:
    fore_data = stock_forecast(data)
    tab_data.subheader('Forecast')
    tab_data.write(fore_data)

with plot_config:
    fig = stock_plot(data, fore_data)

if fig:
    tab_graph.plotly_chart(fig, use_container_width=True)




# METRICS FOR CURRENT TICKER
c1,c2,c3,c4 = tab_graph.columns(4)

last_close = data['Close'].iloc[-1]
prev_close = data['Close'].iloc[0]
change = last_close - prev_close
c1.metric(
    label=f"Last Price",
    value=f"{last_close:.2f} USD",
    delta=f"{change:.2f} ({(change / prev_close) * 100:.2f}%)"
)
c2.metric("High", f"{data['High'].max():.2f} USD")
c3.metric("Low", f"{data['Low'].min():.2f} USD")
c4.metric("Volume", f"{data['Volume'].sum():,}")



tab_data.subheader('Historical Data')
tab_data.dataframe(data.set_index('Date')[['Open', 'High', 'Low', 'Close', 'Volume']])



# METRICS FROM TICKERS ON THE HEADER
stock_symbols = ['AAPL', 'GOOGL', 'AMZN', 'MSFT', 'NVDA']
cols = header_area.columns(len(stock_symbols))
for i,symbol in enumerate(stock_symbols):
    real_time_data = get_data(symbol, '1d', '1m')
    if not real_time_data.empty:
        last_price = float(real_time_data['Close'].values[-1])
        change = float(last_price - real_time_data['Open'].values[0])
        pct_change = (change / float(real_time_data['Open'].values[0])) * 100
        cols[i].metric(f"{symbol}", f"{last_price:.2f} USD", f"{change:.2f} ({pct_change:.2f}%)")


