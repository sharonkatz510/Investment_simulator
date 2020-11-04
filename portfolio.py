import pandas as pd
import pandas_datareader.yahoo.daily as pdr
import yahooquery as yq
from datetime import date
import numpy as np
import pickle
#


class Portfolio:
    """Bundle of assets with different weights"""
    def __init__(self, tickers, period=10, weights: list = None, finance=None):
        """
        :param tickers: list of tickers with somw general info
        :param period: time period in years
        :param weights: list of weights for averaging
        """
        self.period = period
        self.finance = finance or get_all_ticker_close(tickers, period)
        self.summary = get_all_ticker_info(tickers)
        self.summary['weight'] = np.array(weights)/np.array(weights).sum() if weights else \
            (1/self.summary.shape[0])*np.ones(self.summary.shape[0])
        # extract currency exposure
        self.currencySplit = get_weighted_count(self.summary, 'currency')

    def save_to_pickle(self, path: str):
        """
        Save portfolio to pickle file, compatible with load_portfolio_from_pickle function
        :param path: (string) path to new pickle file
        """
        with open(path, 'wb') as fid:
            pickle.dump(self, fid)  # number of assets to load

    def update(self, tickers=None, period=None, weights=None):
        """
        Update portfolio when passing new tickers, period or weights
        :param tickers: (str or list) assets symbols
        :param period: (int) number of years
        :param weights: (list) weights for assets in portfolio
        :return: updated portfolio
        """
        if tickers or period:
            self.finance = get_all_ticker_close(tickers, period or self.period)
        if tickers:
            self.summary = get_all_ticker_info(tickers)
        if weights and (len(weights) == self.summary.shape[0]):
            self.summary['weight'] = np.array(weights)/np.array(weights).sum()
        elif 'weight' not in self.summary.columns:
            self.summary['weight'] = (1/self.summary.shape[0])*np.ones(self.summary.shape[0])
        self.currencySplit = get_weighted_count(self.summary, 'currency')
        return self

    def get_scaled_prices(self):
        """
        Scale prices of assets to start from 100%
        :return: scaled prices matrix of shape: time x n_assets
        """
        prices_scaled = self.finance.apply(lambda x: x / x[x.first_valid_index()], axis=0).fillna(method='ffill')
        return prices_scaled.rename(columns=self.summary['name'].to_dict())

    def get_combined_worth(self):
        """
        Calculate portfolio revenue w/ respect to each asset revenue and weight
        :return: combined worth (as % of start value) vector
        """
        prices_scaled = self.finance.apply(lambda x: x / x[x.first_valid_index()], axis=0).fillna(method='ffill')
        w = self.summary['weight']
        w.index = prices_scaled.columns
        return (prices_scaled * w.transpose()).sum(axis=1).to_frame(name='Combined value')

    def remove(self, tick):
        """
        Remove asset from portfolio
        :param tick: (str) symbol
        :return: updated portfolio
        """
        if tick in self.finance.columns:
            self.summary.drop(tick, axis=0, inplace=True)
            self.finance.drop(tick, axis=1, inplace=True)
            self.update()
        return self

    def add(self, tick):
        """
        Add asset to portfolio
        :param tick: (str) symbol
        :return: updated portfolio
        """
        dat = get_all_ticker_close(tick, self.period).to_frame().rename(columns={'Adj Close': tick})
        self.finance = self.finance.join(dat)
        info = get_all_ticker_info(tick)
        self.summary.drop('weight', axis=1, inplace=True)
        self.summary = self.summary.append(info)
        self.update()
        return self

    def get_sector_split(self):
        """
        Get sector split of portfolio w/ respect to assets weights
        :return: pandas.Series w/ indices=sectors and values= % of portfolio
        """
        query = yq.Ticker(self.summary['ticker'].to_list())
        data = pd.DataFrame.from_dict(query.fund_sector_weightings)
        mult = np.array(data) * np.array(self.summary['weight'].transpose())
        return pd.Series(mult.sum(axis=1), index=data.index)


def get_all_ticker_close(tickers, period):
    """
    Extract adj. close data for all tickers in the time period
    :param tickers: (str or list of strings) assets symbols
    :param period: (int) time period in years
    :return: pandas.DataFrame of adj. close prices where indices=Dates columns= assets symbols
    """
    start_date = date.today().replace(year=date.today().year - period)
    end_date = date.today()
    query = pdr.YahooDailyReader(tickers, start=start_date, end=end_date, interval='w')
    data = query.read()
    return data['Adj Close']


def get_all_ticker_info(tickers):
    """
    Extract fundamental information about assets
    :param tickers: (str or list of strings) assets symbols
    :return: panda.DataFrame of assets fund. info where indices=symbols, columns={'ticker','exchange','name','currency'}
    """
    query = yq.Ticker(tickers)
    currency = pd.DataFrame.from_dict(query.summary_detail).loc['currency', :]
    data = pd.DataFrame.from_dict(query.quote_type).loc[['symbol', 'exchange', 'shortName'], :]
    data = data.append(currency)
    data.rename(index={'shortName': 'name', 'symbol': 'ticker'}, inplace=True)
    return data.transpose()


def read_portfolio_from_pickle(path):
    """
    :param path: (str) path to pickle file
    :return: Portfolio object
    """
    with open(path, 'rb') as fid:
        portfolio = pickle.load(fid)
    return portfolio


def get_weighted_count(df: pd.DataFrame, column: str):
    """
    calculate distributions in data
    :param df: (DataFrame) with a column with the specified name, and a 'weight' colummn
    :param column: column name of the specific column in df
    :return: dictionary where keys = unique values in df[column] , and values = sum(<index weight>*<appeared or not>)
    """
    dic = dict()
    for key in df[column].unique():
        dic[key] = ((df[column] == key) * df['weight']).sum()
    return pd.DataFrame.from_dict(dic, orient='index', columns=['weight'])


__all__ = ['Portfolio', 'read_portfolio_from_pickle', 'get_all_ticker_info',
           'get_weighted_count', 'get_all_ticker_close']
