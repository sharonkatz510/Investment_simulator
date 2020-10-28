import pandas as pd
import pandas_datareader.yahoo.daily as pdr
import yfinance as yf
from datetime import date
import numpy as np
import pickle
#


class Portfolio:
    """Bundle of assets with different weights"""

    def __init__(self, tickers, period=10, initAmount=500000, weights: list = None, finance=None):
        """
        :param tickers: list of tickers with somw general info
        :param period: time period in years
        :param initAmount: money in fund
        :param weights: list of weights for averaging
        """
        self.finance = finance or get_all_ticker_close(tickers, period)
        self.initAmount = initAmount
        self.summary = get_all_ticker_info(tickers)
        self.summary['weight'] = np.array(weights) or (1/len(tickers))*np.ones(len(tickers))
        # extract currency exposure
        self.currencySplit = dict_weighted_count(self.summary, 'currency')
        # extract region exposure
        self.marketSplit = dict_weighted_count(self.summary, 'market')

    def cagr(self):
        cagrs = np.array([x.cagr() for x in self.assets])
        return np.sum(self.summary['weight']*cagrs)

    def save_to_pickle(self, path: str):
        """
        Save portfolio to pickle file, compatible with load_portfolio_from_pickle function
        :param path: (string) path to new pickle file
        """
        with open(path, 'wb') as fid:
            pickle.dump(self, fid)  # number of assets to load


def get_all_ticker_close(tickers, period):
    start_date = date.today().replace(year=date.today().year - period)
    end_date = date.today()
    query = pdr.YahooDailyReader(tickers, start=start_date, end=end_date, interval='m')
    data = query.read()
    return data['Adj Close']


def get_all_ticker_info(tickers):
    data = []
    for tick in tickers:
        tickerData = yf.Ticker(tick)
        data.append(pd.DataFrame.from_dict(tickerData.info, orient='index', columns=[tick]))
    data = pd.concat(data, axis=1, join='inner').transpose()
    info = data[['currency', 'shortName', 'market', 'exchange']]
    info['ticker'] = tickers
    info.rename(columns={'shortName': 'name'}, inplace=True)
    return info


def read_portfolio_from_pickle(path):
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


if __name__ == '__main__':
    tickers = ['CSPX.L', 'IWB', 'SWDA.L','VTI',
               'VB','IWM','VTV','VOE','VBR','IMEA.SW',
               'VT','VSS','VXUS','VWO']

    ptf = Portfolio(tickers, period=8)
    # saving to pickle
    # ptf.save_to_pickle('portfolio.pkl')
    # plotting
    # ptf.plot()

