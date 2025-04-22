# -*- coding: utf-8 -*-
"""
Created on Wed Apr 16 13:05:08 2025

@author: PRATHAM
"""

import yfinance as yf
import pandas as pd
import datetime as dt  
import numpy as np
import time

    
def ATR(DF, n):
    df = DF.copy()
    df["H-L"] = df["High"] - df["Low"]
    df["H-PC"] = abs(df["High"] - df["Close"].shift(1))
    df["L-PC"] = abs(df["Low"] - df["Close"].shift(1))
    df["TR"] = df[["H-L","H-PC","L-PC"]].max(axis=1, skipna=False)
    df["ATR"] = df["TR"].ewm(com=n, min_periods=n).mean()
    return df["ATR"]
    
def CAGR(DF):
    df = DF.copy()
    df["Cumilative_Returns"] = (1 + df["ret"]).cumprod()
    n = len(df) / 252
    return (df["Cumilative_Returns"].iloc[-1].item() ** (1/n)) - 1

def Volatility(DF):
    df = DF.copy()
    return df["ret"].std() * np.sqrt(252)

def Sharpe(DF , safeReturn):
    df = DF.copy()
    sharpe = (CAGR(df) - safeReturn) / Volatility(df)
    return sharpe

def max_dd(DF):
    df = DF.copy()
    df["cumilative_returns"] = (1 + df["ret"]).cumprod()
    df["max_cumilative_return"] = df["cumilative_returns"].cummax()
    df["drawdown"] = df["max_cumilative_return"] - df["cumilative_returns"]
    pct_drop = (df["drawdown"] /df["max_cumilative_return"] ).max()
    return pct_drop

def calmar_ratio(DF):
    df = DF.copy()
    return CAGR(df) / max_dd(df)

tickers = ["INFY.NS" , "HDFCBANK.NS" , "RELIANCE.NS" , "TCS.NS"]
ohlcv_data = {}

for ticker in tickers:
    temp = yf.download(ticker , start = "2015-04-01" , end = "2025-04-01" , interval="1d")
    temp.dropna(how = "any" , inplace=True)
    ohlcv_data[ticker] = temp
    
ticker_dict = ohlcv_data.copy()
ticker_signal = {}
ticker_ret = {}
for ticker in tickers:
    ticker_dict[ticker]["ATR"] = ATR(ticker_dict[ticker], 20)
    ticker_dict[ticker]["rolling_max"] = ticker_dict[ticker]["High"].rolling(20).max()
    ticker_dict[ticker]["rolling_min"] = ticker_dict[ticker]["Low"].rolling(20).min()
    ticker_dict[ticker]["rolling_max_vol"] = ticker_dict[ticker]["Volume"].rolling(20).max()
    ticker_dict[ticker].dropna(inplace=True)
    ticker_signal[ticker] = ""
    ticker_ret[ticker] = [0]
    

        
for ticker in tickers:
    for i in range(1,len(ticker_dict[ticker])):
        if ticker_signal[ticker] == "":
            ticker_ret[ticker].append(0)
            if ticker_dict[ticker]["High"].iloc[i].item()>=ticker_dict[ticker]["rolling_max"].iloc[i].item() and \
               ticker_dict[ticker]["Volume"].iloc[i].item()>1.5*ticker_dict[ticker]["rolling_max_vol"].iloc[i-1].item():
                   ticker_signal[ticker] = "Buy"
            elif ticker_dict[ticker]["Low"].iloc[i].item()<=ticker_dict[ticker]["rolling_min"].iloc[i].item() and \
               ticker_dict[ticker]["Volume"].iloc[i].item()>1.5*ticker_dict[ticker]["rolling_max_vol"].iloc[i-1].item():
                   ticker_signal[ticker] = "Sell"
        
        elif ticker_signal[ticker] == "Buy":
            if ticker_dict[ticker]["Low"].iloc[i].item() < ticker_dict[ticker]["Close"].iloc[i-1].item() - ticker_dict[ticker]["ATR"].iloc[i-1].item():
                ticker_signal[ticker] = ""
                returns = ((ticker_dict[ticker]["Close"].iloc[i-1].item() - ticker_dict[ticker]["ATR"].iloc[i-1].item()) / ticker_dict[ticker]["Close"].iloc[i-1].item()) - 1
                ticker_ret[ticker].append(returns)
            elif ticker_dict[ticker]["Low"].iloc[i].item() <=  ticker_dict[ticker]["rolling_min"].iloc[i].item() and \
                ticker_dict[ticker]["Volume"].iloc[i].item() > 1.5* ticker_dict[ticker]["rolling_max_vol"].iloc[i-1].item():
                    ticker_signal[ticker] = "Sell"
                    ticker_ret[ticker].append((ticker_dict[ticker]["Close"].iloc[i].item() / ticker_dict[ticker]["Close"].iloc[i-1].item()))
            else:
                ticker_ret[ticker].append((ticker_dict[ticker]["Close"].iloc[i].item() / ticker_dict[ticker]["Close"].iloc[i-1].item()) - 1)

        elif ticker_signal[ticker] == "Sell":
            if ticker_dict[ticker]["High"].iloc[i].item() < ticker_dict[ticker]["Close"].iloc[i-1].item() + ticker_dict[ticker]["ATR"].iloc[i-1].item():
                ticker_signal[ticker] = ""
                returns = ((ticker_dict[ticker]["Close"].iloc[i-1].item() + ticker_dict[ticker]["ATR"].iloc[i-1].item()) / ticker_dict[ticker]["Close"].iloc[i-1].item()) - 1
                ticker_ret[ticker].append(returns)
            elif ticker_dict[ticker]["High"].iloc[i].item() <=  ticker_dict[ticker]["rolling_max"].iloc[i].item() and \
                ticker_dict[ticker]["Volume"].iloc[i].item() > 1.5* ticker_dict[ticker]["rolling_max_vol"].iloc[i-1].item():
                    ticker_signal[ticker] = "Sell"
                    ticker_ret[ticker].append((ticker_dict[ticker]["Close"].iloc[i].item() / ticker_dict[ticker]["Close"].iloc[i-1].item()))
            else:
                ticker_ret[ticker].append((ticker_dict[ticker]["Close"].iloc[i].item() / ticker_dict[ticker]["Close"].iloc[i-1].item()) - 1 )
           
    ticker_dict[ticker]["ret"] = np.array(ticker_ret[ticker])
    
    
strategy_return_df = pd.DataFrame()
for ticker in tickers:
    strategy_return_df[ticker] = ticker_dict[ticker]["ret"]
    
strategy_return_df["ret"] = strategy_return_df.mean(axis=1)
cagr = CAGR(strategy_return_df)
sharpe = Sharpe(strategy_return_df, 0.07)
dd = max_dd(strategy_return_df)
calamar = calmar_ratio(strategy_return_df)
