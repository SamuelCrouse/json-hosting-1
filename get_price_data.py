import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd

def getPrices(ticker):
    data = pd.DataFrame(yf.download(tickers=[ticker], start=datetime.today()-timedelta(7), end=datetime.today()+timedelta(1), interval='1m', period='1d'))

    return data

if __name__ == "__main__":
    data = getPrices("SPY")
    data = data.reset_index()
    data['Datetime'] = data['Datetime'].astype(str)
    print(data)
