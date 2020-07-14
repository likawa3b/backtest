import backtrader as bt
import pandas as pd
import numpy as np
from rpy2.robjects import numpy2ri, pandas2ri
from rpy2.robjects.packages import importr
# The R package PerformanceAnalytics, containing the R function VaR
# utils = importr('utils')
# utils.install_packages('PerformanceAnalytics')
pa = importr("PerformanceAnalytics")
numpy2ri.activate()
pandas2ri.activate()


class SortinoRatio(bt.Analyzer):
    """
    Computes the Sortino ratio metric for the whole account using the strategy, based on the R package
    PerformanceAnalytics SortinoRatio function
    """
    params = {
        "MAR": 0}    # Minimum Acceptable Return (perhaps the risk-free rate?); must be in same periodicity
    # as data

    def __init__(self):
        self.acct_return = dict()
        self.acct_last = self.strategy.broker.get_value()
        self.sortinodict = dict()

    def next(self):
        if len(self.data) > 1:
            # I use log returns
            curdate = self.strategy.datetime.date(0)
            self.acct_return[curdate] = np.log(
                self.strategy.broker.get_value()) - np.log(self.acct_last)
            self.acct_last = self.strategy.broker.get_value()

    def stop(self):
        # Need to pass a time-series-like object to SortinoRatio
        srs = pd.Series(self.acct_return)
        srs.sort_index(inplace=True)
        self.sortinodict['sortinoratio'] = pa.SortinoRatio(srs, MAR=self.params.MAR)[
            0]    # Get Sortino Ratio
        del self.acct_return              # This dict is of no use to us anymore

    def get_analysis(self):
        return self.sortinodict
