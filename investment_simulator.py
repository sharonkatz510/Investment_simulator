import matplotlib.pyplot as plt
import pandas as pd
import pandas_datareader.yahoo.daily as pdr
from datetime import date
import numpy as np
from functools import reduce
from collections import namedtuple
#


class Asset:
    """Holds important info about the specific asset"""

    def __init__(self, period: int=10, **kwargs):
        """
        :param ticker: string
        :param period: time period in years, default = 10
        """
        self.name = kwargs['name']
        self.region = kwargs['region'] or 'N/A'
        self.domicil = kwargs['domicil'] or 'N/A'
        self.start_date = date.today().replace(year=date.today().year-period)
        self.end_date = date.today()
        query = pdr.YahooDailyReader(ticker, start=self.start_date, end=self.end_date, interval='d')
        data = query.read()
        self.start_val = data.loc[data.index[0], 'Close']
        self.end_val = data.loc[data.index[-1], 'Close']
        self.price = data.loc[:, 'Close']

    def cagr(self):
        cagr = (self.end_val / self.start_val) ** (365 / (self.end_date - self.start_date).days) - 1
        return cagr


class Portfolio:
    """Bundle of assets with different weights"""

    def __init__(self, assets, period=10, amount=500000, weights=None):
        """
        :param tickers: list of tickers with somw general info
        :param period: time period in years
        :param amount: money in fund
        :param weights: weights for averaging
        """
        self.assets = [Asset(period, x._asdict()) for x in tickers]
        self.weights = weights or (1/len(tickers))*np.ones(len(tickers))
        self.amount = amount
        self.tickers = [x.name for x in tickers]

    def cagr(self):
        cagrs = np.array([x.cagr() for x in self.assets])
        return np.sum(self.weights*cagrs)

    def plot(self):
        prices = [x.price.to_frame() for x in self.assets]  # extract prices
        # merge and scale prices to start from 1$
        prices_merged = reduce(lambda left, right: pd.merge(left, right, on=['Date'],
                                                        how='outer'), prices).dropna()
        prices_scaled = prices_merged.div(prices_merged.iloc[0, :])
        prices_scaled = prices_scaled*self.amount
        combined = np.sum(np.array(prices_scaled)*self.weights, 1)  # combined portfolio worth
        # plot all assets
        plt.figure()
        for i in range(len(self.assets)):
            plt.plot(prices_scaled.iloc[:,i])

        plt.legend([x.name for x in self.assets]) ; plt.title('asset comparison') ; plt.xlabel('Date') ;
        plt.ylabel('price relative to start price')
        # plot combined portfolio revenue
        plt.figure()
        plt.plot(prices_merged.index, combined)
        plt.title('Combined portfolio worth'); plt.ylabel('$') ; plt.xlabel('Date')
        # plot pie chart of assets
        plt.figure()
        plt.pie(self.weights, labels=self.tickers)


tickers = ['CSPX.L', 'IWB', 'SWDA.L','VTI',
           'VB','IWM','VTV','VOE','VBR','IMEA.SW',
           'VT','VSS','VXUS','VWO']


ptf = Portfolio(tickers, period=5)
ptf.plot()
