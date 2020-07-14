import backtrader as bt
import pandas as pd
import datetime
import random
import numpy as np
from StrategyMacdLong import *
from StrategyMacdShort import *

# df = pd.read_csv('exportSignal.csv')
# df.index = pd.to_datetime(df['time'], unit='s')
# df = df[['open', 'high', 'low', 'close']].rename(
#     columns={"open": "Open", "high": "High", "low": "Low", "close": "Close"})['2014-01-02':'2017-01-01']
# data = bt.feeds.PandasData(dataname=df, volume=None, openinterest=None)

df = pd.read_csv('Data\SMH_Adj.csv',
                 index_col='Date', parse_dates=True)
data = bt.feeds.PandasData(dataname=df, openinterest=None)


def returnmaxpara(result, maxpara, testpara, **kwargs):
    final_results_list = []
    for run in result:
        for strategy in run:
            # profit = (strategy.broker.get_value() - capital) / capital
            # profit = strategy.analyzers.RT.get_analysis()
            profit = strategy.analyzers.CMA.calmaralt

            final_results_list.append([profit, strategy.params.fastlen, strategy.params.slowlen, strategy.params.signallen, strategy.params.close_fastlen,
                                       strategy.params.close_slowlen, strategy.params.close_signallen, strategy.params.topfilter, strategy.params.botfilter, strategy.params.stop_loss, strategy.params.percent])
    final_results_list = sorted(
        final_results_list, key=lambda x: x[0], reverse=True)
    if(final_results_list[0][0] > maxpara['profit']):
        maxpara['profit'] = final_results_list[0][0]
        maxpara['fastlen'] = final_results_list[0][1]
        maxpara['slowlen'] = final_results_list[0][2]
        maxpara['signallen'] = final_results_list[0][3]
        maxpara['close_fastlen'] = final_results_list[0][4]
        maxpara['close_slowlen'] = final_results_list[0][5]
        maxpara['close_signallen'] = final_results_list[0][6]
        maxpara['topfilter'] = final_results_list[0][7]
        maxpara['botfilter'] = final_results_list[0][8]
        maxpara['stop_loss'] = final_results_list[0][9]
        maxpara['percent'] = final_results_list[0][10]

    testpara = maxpara.copy()
    for key, value in kwargs.items():
        testpara[str(key)] = value
    return maxpara, testpara


def opt(testpara, Strat):
    use_Margin = True
    cerebro = bt.Cerebro(stdstats=False)
    cerebro.resampledata(data,
                         timeframe=bt.TimeFrame.Minutes,
                         compression=60)
    # cerebro.addanalyzer(bt.analyzers.Returns, _name='RT')
    cerebro.addanalyzer(bt.analyzers.CalmarAlt, _name='CMA')
    cerebro.broker.setcash(capital)
    cerebro.optstrategy(
        Strat, printlog=False, percent=testpara['percent'], stop_loss=testpara['stop_loss'], fastlen=testpara['fastlen'], slowlen=testpara['slowlen'], signallen=testpara['signallen'],
        close_fastlen=testpara['close_fastlen'], close_slowlen=testpara['close_slowlen'], close_signallen=testpara['close_signallen'], topfilter=testpara['topfilter'], botfilter=testpara['botfilter'], useMargin=use_Margin)

    result = cerebro.run(optreturn=True)
    return result


capital = 100000.0
if __name__ == '__main__':
    Strat = StMacdLong
    print(Strat)
    mps = []
    upper = 50
    codes = [
        "maxpara,testpara = returnmaxpara(result,maxpara,testpara, slowlen=range(1, %d))" %
        upper,
        "maxpara,testpara = returnmaxpara(result,maxpara,testpara, signallen=range(1, %d))" %
        upper,
        "maxpara,testpara = returnmaxpara(result,maxpara,testpara, close_fastlen=range(1, %d))" %
        upper,
        "maxpara,testpara = returnmaxpara(result,maxpara,testpara, close_slowlen=range(1, %d))" %
        upper,
        "maxpara,testpara = returnmaxpara(result,maxpara,testpara, close_signallen=range(1, %d))" %
        upper,
        "maxpara,testpara = returnmaxpara(result,maxpara,testpara, topfilter=range(-2000, 1000,100))",
        "maxpara,testpara = returnmaxpara(result,maxpara,testpara, botfilter=range(-2000, 1000,100))",
        "maxpara,testpara = returnmaxpara(result,maxpara,testpara, stop_loss=range(500, 0, -100))",
        "maxpara,testpara = returnmaxpara(result,maxpara,testpara, percent=np.arange(0.1, 0.6, 0.1))",
        "maxpara, testpara = returnmaxpara(result, maxpara, testpara)"
    ]

    for i in range(1):
        old_maxpara = [{} for i in range(11)]
        mid = random.randint(2, upper)
        mid2 = random.randint(2, upper)
        maxpara = {
            'profit': 0,
            'fastlen': random.randint(2, mid),
            'slowlen': random.randint(mid, upper),
            'signallen': random.randint(2, upper),
            'close_fastlen': random.randint(2, mid2),
            'close_slowlen': random.randint(mid2, upper),
            'close_signallen': random.randint(2, upper),
            # 'fastlen': 82,
            # 'slowlen': 161,
            # 'signallen': 21,
            # 'close_fastlen': 5,
            # 'close_slowlen': 1,
            # 'close_signallen': 11,
            'topfilter': -2000,
            'botfilter': -2000,
            'stop_loss': 5,
            'percent': 0.1
        }
        testpara = maxpara.copy()
        while old_maxpara[0] != maxpara:
            print("Next iteration")
            old_maxpara[0] = maxpara.copy()
            testpara['fastlen'] = range(2, upper)
            for k in [0, 1, 2, 3, 4, 7, 8, 9]:  # range(10):
                if old_maxpara[k+1] != maxpara:
                    result = opt(testpara, Strat)
                    exec(codes[k])
                    old_maxpara[k+1] = maxpara.copy()
                    print(maxpara)
        print("Next Parameters")
        mps.append(maxpara)
        with open('output.txt', 'w') as f:
            for item in mps:
                f.write("%s\n" % item)
    print("Complete!")
