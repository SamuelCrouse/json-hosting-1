import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd
from pathlib import Path
import os
from datetime import datetime as dt
import math

def getPricesMinute(ticker):
    data = pd.DataFrame(yf.download(tickers=[ticker], start=datetime.today()-timedelta(7), end=datetime.today()+timedelta(1), interval='1m', period='1d'))

    return data

def getPrices30Days(ticker):
    data = pd.DataFrame(yf.download(tickers=[ticker], start=datetime.today()-timedelta(30), end=datetime.today()+timedelta(1), interval='1d', period='1d'))

    return data


def update_price_data(tickers):
    """ Documentation
    Takes in a list of strings, writes 30 days of daily price data to a price_data directory ('x') and returns None.
    
    :param: tickers: list(str): Takes in a list of strings of tickers and writes data to a directory called price_data.
    """

    """
        Get all price data and add it to price_data directory
    """
    for item in tickers:
        if str(item).lower() == 'nan':
            continue

        """
            Retreive and sort price data
        """
        priceData = getPrices30Days(item)
        priceData = priceData.reset_index()
        

        """
            Add the price data to where it is stored
        """
        pricesPath = Path(__file__).parent.joinpath('price_data').joinpath(item + '.csv')

        print("writing " + item + " to:", pricesPath)

        if os.path.exists(pricesPath):
            priceData.to_csv(pricesPath)
        else:
            os.makedirs(os.path.dirname(pricesPath), exist_ok=True)
            priceData.to_csv(pricesPath)

    return None



def read_prices(ticker):
    """ Documentation
    Reads a tickers data from the price_data directory and returns pd dataframe.
    
    :param: ticker: str: The ticker to read from the price_data dir.
    :returns: data: pd.Dataframe
    """

    pricesPath = Path(__file__).parent.joinpath('price_data').joinpath(ticker + '.csv')
    data = pd.read_csv(pricesPath)

    return data


def readDayCloseAsJSON(ticker):
    """ Documentation
    Reads a tickers data from the price_data directory and returns the closes as a json object with keys of style:
        "4 16 2025"
    
    :param: ticker: str: The ticker to read from the price_data dir.
    :returns: dict: data
    """

    df = read_prices(ticker)

    # separate the price data into lists of days
    dtime = list(df["Date"])[1:]    # remove header
    opens = [float(x) for x in list(df["Open"])[1:]]  # remove header
    closes = [float(x) for x in list(df["Close"])[1:]]  # remove header

    dtime = [dt.strptime(date, '%Y-%m-%d') for date in dtime]

    dailyPriceData = {}
    daysData = []
    lastDate = dtime[0]
    # for each new day, add the days prices to a new list in daily data
    for i in range(len(dtime)):
        if dtime[i].day != lastDate.day:
            dailyPriceData[str(lastDate.month) + " " + str(lastDate.day) + " " + str(lastDate.year)] = daysData
            daysData = []
            lastDate = dtime[i]

        daysData.append({"open": opens[i], "close": closes[i]})
    dailyPriceData[str(lastDate.month) + " " + str(lastDate.day) + " " + str(lastDate.year)] = daysData

    return dailyPriceData


if __name__ == "__main__":
    """
    data = getPricesMinute("SPY")
    data = data.reset_index()
    print(data)
    # """
    
    """
    data = getPrices30Days("SPY")
    data = data.reset_index()
    print(data)
    # """

    """
    # update_price_data(['SPY', 'TSLA'])
    # print(read_prices('SPY'))
    data = readDayCloseAsJSON('SPY')
    i1 = data['4 15 2025'][0]['open']
    # """