import backtrader as bt
import pandas as pd
import datetime
import random
import numpy as np
from StrategyMacdLong import *
from StrategyMacdShort import *
from strategyPriceChannel import *

df = pd.read_csv('exportSignal.csv')
df.index = pd.to_datetime(df['time'], unit='s')
df = df[['open', 'high', 'low', 'close']].rename(
    columns={"open": "Open", "high": "High", "low": "Low", "close": "Close"})  # ['2014-01-02':'2017-01-01']
data = bt.feeds.PandasData(dataname=df, volume=None, openinterest=None)


def returnmaxpara(result, maxpara, testpara, **kwargs):
    final_results_list = []
    for run in result:
        for strategy in run:
            # profit = (strategy.broker.get_value() - capital) / capital
            # profit = strategy.analyzers.RT.get_analysis()
            profit = strategy.analyzers.CMA.calmaralt
            final_results_list.append(
                [profit, strategy.params.periodH, strategy.params.periodL, strategy.params.stop_loss, strategy.params.percent])
    final_results_list = sorted(
        final_results_list, key=lambda x: x[0], reverse=True)
    if(final_results_list[0][0] > maxpara['profit']):
        maxpara['profit'] = final_results_list[0][0]
        maxpara['periodH'] = final_results_list[0][1]
        maxpara['periodL'] = final_results_list[0][2]
        maxpara['stop_loss'] = final_results_list[0][3]
        maxpara['percent'] = final_results_list[0][4]

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
        Strat, printlog=False, percent=testpara['percent'], stop_loss=testpara['stop_loss'], periodH=testpara['periodH'], periodL=testpara['periodL'], useMargin=use_Margin)

    result = cerebro.run(optreturn=True, cheat_on_open=True)
    return result


capital = 100000.0
if __name__ == '__main__':
    Strat = StPCLong
    print(Strat)
    mps = []
    upper = 100
    codes = [
        "maxpara,testpara = returnmaxpara(result,maxpara,testpara, periodL=range(2, %d))" %
        upper,
        "maxpara,testpara = returnmaxpara(result,maxpara,testpara, stop_loss=range(1000, 0, -100))",
        "maxpara,testpara = returnmaxpara(result,maxpara,testpara, percent=np.arange(0.1, 0.6, 0.1))",
        "maxpara, testpara = returnmaxpara(result, maxpara, testpara)"
    ]

    for i in range(1):
        old_maxpara = [{} for i in range(5)]
        # mid = random.randint(2, upper)
        # mid2 = random.randint(2, upper)
        maxpara = {
            'profit': 0,
            # 'periodH': random.randint(2, upper),
            # 'periodL': random.randint(2, upper),
            'periodH': 13,
            'periodL': 18,
            'stop_loss': 100,
            'percent': 0.1
        }
        testpara = maxpara.copy()
        while old_maxpara[0] != maxpara:
            print("Next iteration")
            old_maxpara[0] = maxpara.copy()
            testpara['periodH'] = range(2, upper)
            for k in [0, 1, 2, 3]:  # range(10):
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
