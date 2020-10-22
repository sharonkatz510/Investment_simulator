import pandas as pd
import pandas_datareader.yahoo.daily as pdr
import yfinance as yf
from datetime import date
import numpy as np
from functools import reduce
from bokeh.plotting import figure, output_file, show
from bokeh.layouts import column
from bokeh.palettes import Category20
from bokeh.models import HoverTool, ColumnDataSource
import pickle
#


class Asset:
    """Holds important info about the specific asset"""

    def __init__(self, ticker, period: int = 10, **kwargs):
        """
        :param ticker: string
        :param period: time period in years, default = 10
        :param kwargs: info about ticker to construct from existing data
        """
        self.start_date = date.today().replace(year=date.today().year-period)
        self.end_date = date.today()
        if not kwargs:
            kwargs = get_asset_info(ticker)
            query = pdr.YahooDailyReader(ticker, start=self.start_date, end=self.end_date, interval='d')
            kwargs['data'] = query.read()

        self.ticker = ticker
        self.name = kwargs['longName']
        self.currency = kwargs['currency']
        self.region = kwargs['market']
        self.exchange = kwargs['exchange']
        self.type = kwargs['legalType']
        self.start_val = kwargs['data'].loc[kwargs['data'].index[0], 'Close']
        self.end_val = kwargs['data'].loc[kwargs['data'].index[-1], 'Close']
        self.price = kwargs['data'].loc[:, 'Close']

    def cagr(self):
        cagr = (self.end_val / self.start_val) ** (365 / (self.end_date - self.start_date).days) - 1
        return cagr


class Portfolio:
    """Bundle of assets with different weights"""

    def __init__(self, tickers = None, period=10, initAmount=500000, weights: list = None, assets=None):
        """
        :param tickers: list of tickers with somw general info
        :param period: time period in years
        :param initAmount: money in fund
        :param weights: list of weights for averaging
        :param assets: list of assets to construct from existing
        """
        self.assets = assets or [Asset(x, period) for x in tickers]
        self.initAmount = initAmount
        self.summary = pd.DataFrame.from_dict([x.__dict__ for x in self.assets])
        self.summary['weight'] = np.array(weights) or (1/len(self.assets))*np.ones(len(self.assets))
        # extract currency exposure
        self.summary['usd'] = self.summary['currency'].apply(lambda x: x == 'USD')
        # TODO:extract market and currency exposure

    def cagr(self):
        cagrs = np.array([x.cagr() for x in self.assets])
        return np.sum(self.summary['weight']*cagrs)

    def get_scaled_worth(self):
        """
        Merge all assets time-series to one table and scale to % from starting value
        """
        prices = self.summary['price'].tolist()  # extract prices
        # merge and scale prices to start from 1$
        prices_merged = reduce(lambda left, right: pd.merge(left, right, on=['Date'],
                                                            how='outer'), prices).dropna()
        prices_merged.columns = self.summary['ticker'].tolist()
        prices_scaled = prices_merged.iloc[::7, :].div(prices_merged.iloc[0, :])  # under-sampling for speed
        prices_scaled = prices_scaled * self.initAmount
        return prices_scaled

    def plot(self):
        output_file("plots.html")
        prices_scaled = self.get_scaled_worth()
        combined = np.sum(np.array(prices_scaled)*np.array(self.summary['weight']), 1)  # combined portfolio worth
        # plot all assets
        p1 = plot_multi_asset_line(prices_scaled)   # TODO: fix plot problems
        # plot combined portfolio revenue
        p2 = figure(
            title='Combined portfolio worth', y_axis_label='$', x_axis_label='Date',
            plot_width=1200, sizing_mode="scale_width"
        )
        p2.line(prices_scaled.index, combined)
        # plot pie chart of assets

        show(column(p1, p2))

    def save_to_pickle(self, path: str):
        """
        Save portfolio to pickle file, compatible with load_portfolio_from_pickle function
        :param path: (string) path to new pickle file
        """
        with open(path, 'wb') as fid:
            pickle.dump(len(self.assets), fid)  # number of assets to load
            for asset in self.assets:
                pickle.dump(asset, fid)


def get_asset_info(ticker: str):
    """
    this function gets ticker string and extracts data from yahoo finance
    :param ticker: string
    :return: dictionary with asset info
    """
    tickerData = yf.Ticker(ticker)
    data = tickerData.info
    return data


def load_portfolio_from_pickle(fname: str):
    """
    Extract portfolio from pickle file
    :param fname: file path
    :return: portfolio object
    """
    with open(fname, 'rb') as fid:
        assets = []
        for _ in range(pickle.load(fid)):
            assets.append(pickle.load(fid))
    return Portfolio(assets=assets)


def plot_multi_asset_line(df):
    """

    :param df: (pandas DataFrame) with asset prices indexed by date
    :return: bokeh plot
    """
    pallet = Category20[df.shape[1]]
    p = figure(
        title='asset comparison', x_axis_label='Date', y_axis_label='price relative to start price',
        x_axis_type='datetime', plot_width=1200, sizing_mode="scale_width"
    )
    p.legend.location = 'top_left'
    p.legend.click_policy = 'hide'
    for i in range(df.shape[1]):
        cds = ColumnDataSource(data={
            'date' : (df.index.tolist()),
            'worth' : df.iloc[:, i].tolist()},
        )
        p.line(x='date', y='worth', legend_label=df.columns[i], color = pallet[i], source=cds)

    p.add_tools(HoverTool(
        tooltips=[
            ('date', '@date{%F}'),
            ('worth', '@worth{0,0%}'),
            ('name', '@name')
        ],

        formatters={
            'date': 'datetime'  # use 'datetime' formatter for 'date' field
        },
        mode='mouse'
    ))
    return p


if __name__ == '__main__':
    tickers = ['CSPX.L', 'IWB', 'SWDA.L','VTI',
               'VB','IWM','VTV','VOE','VBR','IMEA.SW',
               'VT','VSS','VXUS','VWO']

    ptf = Portfolio(tickers, period=8)
    # saving to pickle
    ptf.save_to_pickle('portfolio.pkl')
    # plotting
    # ptf.plot()

