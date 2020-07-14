#from rpy2.robjects import numpy2ri, pandas2ri
import backtrader as bt
import pandas as pd
import datetime
import random
from StrategyMacdLong import *
from StrategyMacdLongSyn import *
from StrategyMacdShort import *
from strategyMomentum import *
from strategyPriceChannel import *
#from SortinoRatio import *

if __name__ == '__main__':
    # Settings
    capital = 100000
    strategy = StMacdLong
    stock = 'hsiFuture'
    timeframe = '1'
    use_Percent = True
    use_Margin = True
    cheat_on_open_bool = False  # Default = False

    # Strategy Parameters
    if strategy == StMacdLong or strategy == StMacdShort:
        testpara = {
            'fastlen': 53, 'slowlen': 69, 'signallen': 72, 'close_fastlen': 1, 'close_slowlen': 98, 'close_signallen': 5, 'topfilter': -9999, 'botfilter': -9999, 'stop_loss': 200, 'percent': 0.15,
            'commission': 0.001,
            'usePercent': use_Percent,
            'useMargin': use_Margin,
        }
    elif strategy == StMtLong or strategy == StMtShort:
        testpara = {
            'period1': 26,
            'period2': 141,
            'entryfilter1': 0.013198363982972444,
            'entryfilter2': -0.016699831347744068,
            'closefilter1': -0.04364941298855934,
            'closefilter2': -0.030744038466739967,
            'stop_loss': 0.02,
            'percent': 1.0,
            'commission': 0.001,
            'usePercent': use_Percent,
            'useMargin': use_Margin,
        }
    elif strategy == StPCLong or strategy == StPCShort:
        testpara = {
            'periodH': 13,
            'periodL': 18,
            'stop_loss': 400,
            'percent': 0.1,
            'commission': 0.001,
            'usePercent': use_Percent
        }
        cheat_on_open_bool = True
    elif strategy == StMacdLongSyn:
        testpara = {
            'fastlen': 79,
            'slowlen': 68,
            'signallen': 81,
            'topfilter': -9999,
            'botfilter': -9999,
            'stop_loss': 300,
            'percent': 0.2,
            'commission': 0.001,
            'usePercent': use_Percent,
            'useMargin': use_Margin,
        }

    cerebro = bt.Cerebro(stdstats=False)
    cerebro.broker.setcash(capital)

    if timeframe == 'D':
        df = pd.read_csv('Data\SPY.csv', index_col='Date',
                         parse_dates=True)  # ['2009-03-07':]
        data = bt.feeds.PandasData(dataname=df, openinterest=None)
        # data = bt.feeds.YahooFinanceData(dataname='^HSI',
        #                                  fromdate=datetime.datetime(
        #                                           1986, 12, 31),
        #                                  todate=datetime.date.today(),
        #                                  reverse=False, period='D')
        cerebro.adddata(data)
    elif timeframe == '60':
        df = pd.read_csv('TVC_HSI, 60.csv')
        df.index = pd.to_datetime(df['time'], unit='s')
        df = df[['open', 'high', 'low',
                 'close']].rename(columns={
                     "open": "Open",
                     "high": "High",
                     "low": "Low",
                     "close": "Close"
                 })  # ['2019-10-01':]

        data = bt.feeds.PandasData(dataname=df, volume=None, openinterest=None)
        cerebro.resampledata(data,
                             timeframe=bt.TimeFrame.Minutes,
                             compression=60)
    elif stock == 'hsiFuture':
        data = bt.feeds.GenericCSVData(
            dataname='ProccessedData\hsi future 60M resampled.csv',
            fromdate=datetime.datetime(2010, 2, 1),
            todate=datetime.datetime(2020, 5, 23),
            dtformat=('%Y-%m-%d %H:%M:%S'),
            datetime=0,
            time=-1,
            open=1,
            high=2,
            low=3,
            close=4,
            volume=None,
            openinterest=None,
            timeframe=bt.TimeFrame.Minutes,
            compression=60)
        cerebro.resampledata(data,
                             timeframe=bt.TimeFrame.Minutes,
                             compression=60)
    # cerebro.addanalyzer(bt.analyzers.PyFolio, _name='PF')
    cerebro.addanalyzer(bt.analyzers.CalmarAlt, _name='CMA')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='DD')
    # cerebro.addanalyzer(bt.analyzers.Returns, _name='RT')
    #cerebro.addanalyzer(SortinoRatio, _name='ST')
    cerebro.addobserver(bt.observers.Value)
    cerebro.addobserver(bt.observers.Trades)
    cerebro.addobserver(bt.observers.BuySell)
    cerebro.addobserver(bt.observers.DrawDown)

    cerebro.addstrategy(strategy, **testpara)

    # printlog=False, percent=testpara['percent'], stop_loss=testpara[
    #     'stop_loss'], period1=18, period2=149, entryfilter1=120, entryfilter2=-16, closefilter1=0, closefilter2=-96, useMargin=use_Margin, usePercent=use_Percent, commission=testpara['commission'])
    print(strategy, "|use_Percent =", use_Percent, "|use_Margin =", use_Margin,
          "|cheat_on_open_bool =", cheat_on_open_bool, "|timeframe =",
          timeframe)
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
    result = cerebro.run(cheat_on_open=cheat_on_open_bool)
    # print(result[0].analyzers.getbyname('RT').get_analysis())
    # print(result[0].analyzers.getbyname('DD').get_analysis())
    print(
        'Final Portfolio:%.2f%%  CalmarAlt Ratio:%.5f  MDD:%.1f%%'
        # Sortino Ratio:%.5f 
        % (cerebro.broker.getvalue() * 100 / capital,
           result[0].analyzers.getbyname('CMA').calmaralt, 
        #    [i for i in result[0].analyzers.getbyname(
        #            'ST').get_analysis().values()][0],
           result[0].analyzers.getbyname('DD').get_analysis().max.drawdown))
    # print("Return:", result[0].analyzers.PF.get_analysis())     RT from CR:%.5f
    # pyfoliozer = result[0].analyzers.getbyname('PF')
    # returns, positions, transactions, gross_lev = pyfoliozer.get_pf_items()
    # import pyfolio as pf
    # pf.create_returns_tear_sheet(returns,
    #                              positions=positions,
    #                              transactions=transactions,
    #                              live_start_date='2014-02-13',  # This date is sample specific
    #                              round_trips=True)
    # pf.create_full_tear_sheet(
    #     returns,
    #     positions=positions,
    #     transactions=transactions,
    #     live_start_date='2014-02-13',  # This date is sample specific
    #     round_trips=True)

    cerebro.plot(volume=False, cash=False)
    # output = pd.DataFrame(final_results_list,
    #                       columns=['close_fastlen', 'close_slowlen', 'profit'])
    # output = output.sort_values(by=['profit'], ascending=False)
    # print("close_fastlen:",
    #       output.at[0, 'close_fastlen'], "close_slowlen:", output.at[
    #           0, 'close_slowlen'], "profit:{:.2%}".format(output.at[0, 'profit']))
    # output.to_csv("output.csv")
