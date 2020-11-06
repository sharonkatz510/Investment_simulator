from datetime import date
import numpy as np
import pandas as pd
import pickle
import pandas_datareader.yahoo.daily as pdr
import yahooquery as yq
#


class Portfolio:
    """Bundle of assets with different weights"""
    def __init__(self, tickers: list = None, period: int = 10, weights: list = None,
                 finance: pd.DataFrame = None, summary: pd.DataFrame = None):
        self.period = period
        if finance is not None:
            self.finance = finance
            self.summary = summary
        elif tickers is not None:
            self.finance = get_all_ticker_close(tickers, period)
            self.summary = get_all_ticker_info(tickers)
        if 'weight' not in self.summary.columns:
            self.summary['weight'] = np.array(weights)/np.array(weights).sum() if weights else \
                (1/self.summary.shape[0])*np.ones(self.summary.shape[0])

    def save_to_pickle(self, path: str):
        """
        Read portfolio from pickle file
        :param path: relative path to pickle file
        """
        with open(path, 'wb') as fid:
            pickle.dump(self, fid)  # number of assets to load

    def update(self, tickers: list = None, period: int = None, weights: list = None):
        """
        Update portfolio w/ new tickers, period or weights
        :param tickers: list of strings with asset symbols
        :param period: time period in years
        :param weights: list of weights corresponding to asset symbols
        :return: updated Portfolio
        """
        if tickers:
            self.finance = get_all_ticker_close(tickers, period or self.period)
            self.summary = get_all_ticker_info(tickers)
        elif period:
            tickers = self.finance.columns
            self.finance = get_all_ticker_close(tickers, period)
        if weights and (len(weights) == self.summary.shape[0]):
            self.summary['weight'] = np.array(weights)/np.array(weights).sum()
        elif 'weight' not in self.summary.columns:
            self.summary['weight'] = (1/self.summary.shape[0])*np.ones(self.summary.shape[0])
        return self

    def get_scaled_prices(self) -> pd.DataFrame:
        """
        Scale asset prices to % of initial value
        :return: DataFrame of asset adjusted-scaled prices over the time period
        """
        prices_scaled = self.finance.apply(lambda x: x / x[x.first_valid_index()], axis=0).fillna(method='ffill')
        return prices_scaled.rename(columns=self.summary['name'].to_dict())

    def get_combined_worth(self) -> pd.DataFrame:
        """
        Extract Portfolio revenue relative to start point w/ respect to asset weights
        :return: Time series with worth as % of initial worth
        """
        prices_scaled = self.finance.apply(lambda x: x / x[x.first_valid_index()], axis=0).fillna(method='ffill')
        w = self.summary['weight']
        w.index = prices_scaled.columns
        return (prices_scaled * w.transpose()).sum(axis=1).to_frame(name='Combined value')

    def remove(self, tick: str):
        """
        Remove asset from portfolio
        :param tick: string object of asset symbol
        :return: updated Portfolio
        """
        if tick in self.finance.columns:
            self.summary.drop(tick, axis=0, inplace=True)
            self.finance.drop(tick, axis=1, inplace=True)
        return self.update()

    def add(self, tick: str):
        """
        Add asset to portfolio
        :param tick: string object of asset symbol
        :return: updated Portfolio
        """
        dat = get_all_ticker_close(tick, self.period).to_frame().rename(columns={'Adj Close': tick})
        self.finance = self.finance.join(dat)
        info = get_all_ticker_info(tick)
        self.summary.drop('weight', axis=1, inplace=True)
        self.summary = self.summary.append(info)
        return self.update()

    def get_sector_split(self) -> pd.DataFrame:
        """
        Get sector distribution of portfolio w/ respect to weights
        """
        query = yq.Ticker(self.summary['ticker'].to_list())
        data = pd.DataFrame.from_dict(query.fund_sector_weightings)
        mult = np.array(data) * np.array(self.summary['weight'].transpose())
        return pd.Series(mult.sum(axis=1), index=data.index)

    def get_currency_split(self) -> pd.DataFrame:
        """
        Get currency distribution of portfolio w/ respect to weights
        """
        return get_weighted_count(self.summary, 'currency')


def get_all_ticker_close(tickers: str or list, period: int) -> pd.DataFrame:
    """
    Extract adjusted closing prices for asset/s over a period of time
    :param tickers: string or list of strings with asset symbols
    :param period: Time period in years
    :return: DataFrame with time series/es of asset adjusted closing prices
    """
    start_date = date.today().replace(year=date.today().year - period)
    end_date = date.today()
    query = pdr.YahooDailyReader(tickers, start=start_date, end=end_date, interval='w')
    data = query.read()
    return data['Adj Close']


def get_all_ticker_info(tickers: str or list) -> pd.DataFrame:
    """
    Extract fundamental information about assets
    :param tickers: string or list of strings with asset symbols
    :return: DataFrame with the assets and the following characteristics: currency, ticker and name
    """
    query = yq.Ticker(tickers)
    currency = pd.DataFrame.from_dict(query.summary_detail).loc['currency', :]
    data = pd.DataFrame.from_dict(query.quote_type).loc[['symbol', 'exchange', 'shortName'], :]
    data = data.append(currency)
    data.rename(index={'shortName': 'name', 'symbol': 'ticker'}, inplace=True)
    return data.transpose()


def read_portfolio_from_pickle(path: str) -> Portfolio:
    """
    Read portfolio from pickle file
    :param path: local path to pickle file
    :return: Portfolio object
    """
    with open(path, 'rb') as fid:
        portfolio = pickle.load(fid)
    return portfolio


def get_weighted_count(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """
    calculate distributions in data
    :param df: DataFrame with a column of the specified name, and a 'weight' colummn
    :param column: column name of the specific column in df
    :return: dictionary where keys = unique values in df[column] , and values = sum(<index weight>*<appeared or not>)
    """
    dic = dict()
    for key in df[column].unique():
        dic[key] = ((df[column] == key) * df['weight']).sum()
    return pd.DataFrame.from_dict(dic, orient='index', columns=['weight'])


__all__ = ['Portfolio', 'read_portfolio_from_pickle', 'get_all_ticker_info',
           'get_weighted_count', 'get_all_ticker_close']
