#from rpy2.robjects import numpy2ri, pandas2ri
import backtrader as bt
import pandas as pd
import datetime
import random
from strategies.MacdLong import *
# from strategies.MacdLongSyn import *
from strategies.MacdShort import *
from strategies.Momentum import *
from strategies.MomentumLS import *
# from strategies.PriceChannel import *
#from SortinoRatio import *

if __name__ == '__main__':
    # Settings
    capital = 100000
    strategy = StMtLS
    stock = 'hsiFuture'
    timeframe = '60'
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
            'period1': 17,
            'period2': 184,
            'entryfilter1': 0.0072660153084895375,
            'entryfilter2': 0.0038406294508541265,
            'closefilter1': 0.0056889566092680425,
            'closefilter2': -0.004211449679059789,
            'stop_loss': 0.016,
            'percent': 0.1,
            'commission': 0.001,
            'usePercent': use_Percent,
            'useMargin': use_Margin,
        }
    elif strategy == StMtLS:
        testpara = {
            'Long_period1': 17,
            'Long_period2': 184,
            'Long_entryfilter1': 0.0072660153084895375,
            'Long_entryfilter2': 0.0038406294508541265,
            'Long_closefilter1': 0.0056889566092680425,
            'Long_closefilter2': -0.004211449679059789,

            'Short_period1': 30,
            'Short_period2': 157,
            'Short_entryfilter1': 0.007295490900426151,
            'Short_entryfilter2': -0.056614124244711836,
            'Short_closefilter1': -0.029243447352066337,
            'Short_closefilter2': -0.026287410208317,

            'stop_loss': 0.016,
            'percent': 0.1,
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
        df = pd.read_csv('RawData\SPY.csv', index_col='Date',
                         parse_dates=True)  # ['2009-03-07':]
        data = bt.feeds.PandasData(dataname=df, openinterest=None)
        # data = bt.feeds.YahooFinanceData(dataname='^HSI',
        #                                  fromdate=datetime.datetime(
        #                                           1986, 12, 31),
        #                                  todate=datetime.date.today(),
        #                                  reverse=False, period='D')
        cerebro.adddata(data)
    elif timeframe == '60':
        df = pd.read_csv('ProccessedData\TVC_HSI, 60.csv')
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
    cerebro.addanalyzer(bt.analyzers.Calmar, _name='CM')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='DD')
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='SP')
    # cerebro.addanalyzer(bt.analyzers.Returns, _name='RT')
    #cerebro.addanalyzer(SortinoRatio, _name='ST')
    cerebro.addobserver(bt.observers.Value)
    cerebro.addobserver(bt.observers.Trades)
    cerebro.addobserver(bt.observers.BuySell)
    cerebro.addobserver(bt.observers.DrawDown)

    cerebro.addstrategy(strategy, **testpara)

    # testpara2 = {
    #         'period1': 30,
    #         'period2': 157,
    #         'entryfilter1': 0.007295490900426151,
    #         'entryfilter2': -0.056614124244711836,
    #         'closefilter1': -0.029243447352066337,
    #         'closefilter2': -0.026287410208317,
    #         'stop_loss': 0.016,
    #         'percent': 0.1,
    #         'commission': 0.001,
    #         'usePercent': use_Percent,
    #         'useMargin': use_Margin,
    #     }
    # cerebro.addstrategy(StMtShort, **testpara2)

    # printlog=False, percent=testpara['percent'], stop_loss=testpara[
    #     'stop_loss'], period1=18, period2=149, entryfilter1=120, entryfilter2=-16, closefilter1=0, closefilter2=-96, useMargin=use_Margin, usePercent=use_Percent, commission=testpara['commission'])
    print(strategy, "|use_Percent =", use_Percent, "|use_Margin =", use_Margin,
          "|cheat_on_open_bool =", cheat_on_open_bool, "|timeframe =",
          timeframe)
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
    result = cerebro.run(cheat_on_open=cheat_on_open_bool)
    print(result[0].analyzers.getbyname('CM').calmar)
    print(result[0].analyzers.getbyname('SP').get_analysis()['sharperatio'])
    print(
        'Final Portfolio:%.2f%%  CalmarAlt Ratio:%.5f  MDD:%.1f%%' #Calmar Ratio:%.5f' #Sharpe Ratio:%.5f'
        # Sortino Ratio:%.5f 
        % (cerebro.broker.getvalue() * 100 / capital,
           result[0].analyzers.getbyname('CMA').calmaralt, 
        #    [i for i in result[0].analyzers.getbyname(
        #            'ST').get_analysis().values()][0],
           result[0].analyzers.getbyname('DD').get_analysis().max.drawdown))
        #    result[0].analyzers.getbyname('CM').calmar))
        #    result[0].analyzers.getbyname('SP').get_analysis().sharperatio ))
    # print("Return:", result[0].analyzers.PF.get_analysis())     RT from CR:%.5f
    # pyfoliozer = result[0].analyzers.getbyname('PF')
    # returns, positions, transactions, gross_lev = pyfoliozer.get_pf_items()
    # import pyfolio as pf
    # # pf.create_returns_tear_sheet(returns,
    # #                              positions=positions,
    # #                              transactions=transactions,
    # #                              live_start_date='2014-02-13',  # This date is sample specific
    # #                              round_trips=True)
    # pf.create_full_tear_sheet(
    #     returns,
    #     positions=positions,
    #     transactions=transactions,
    #     live_start_date='2014-02-13',  # This date is sample specific
    #     round_trips=True)

    # cerebro.plot(volume=False, cash=False)
    # output = pd.DataFrame(final_results_list,
    #                       columns=['close_fastlen', 'close_slowlen', 'profit'])
    # output = output.sort_values(by=['profit'], ascending=False)
    # print("close_fastlen:",
    #       output.at[0, 'close_fastlen'], "close_slowlen:", output.at[
    #           0, 'close_slowlen'], "profit:{:.2%}".format(output.at[0, 'profit']))
    # output.to_csv("output.csv")
