import backtrader as bt
import pandas as pd
import datetime
import random
import numpy as np
from strategies.MacdLong import *
# from strategies.MacdShort import *
# from SortinoRatio import *
# from strategies.MacdLongSyn import *
# from strategies.MacdLongPair import *

stock = 'hsiFuture'
if stock == 'hsiFuture':
    data = bt.feeds.GenericCSVData(
        dataname='ProccessedData\hsi future 60M resampled.csv',
        fromdate=datetime.datetime(2010, 2, 1),
        todate=datetime.datetime(2020, 5, 23),
        dtformat=('%Y-%m-%d %H:%M:%S'),
        datetime=0,
        open=1,
        high=2,
        low=3,
        close=4,
        volume=None,
        openinterest=None,
        timeframe=bt.TimeFrame.Minutes,
        compression=60)

elif stock == 'hsi':
    df = pd.read_csv('ProccessedData\TVC_HSI, 60.csv')
    df.index = pd.to_datetime(df['time'], unit='s')
    df = df[['open', 'high', 'low', 'close']].rename(columns={
        "open": "Open",
        "high": "High",
        "low": "Low",
        "close": "Close"
    })  # ['2014-01-02':'2019-01-01']
    data = bt.feeds.PandasData(dataname=df, volume=None, openinterest=None)
    # dataDaily = bt.feeds.YahooFinanceData(dataname='^HSI',
    #                                     fromdate=datetime.datetime(1986, 12, 31),
    #                                     todate=datetime.date.today(),
    #                                     reverse=False, period='D')


def returnmaxpara(k, result, maxpara, testpara, **kwargs):
    # k=0 : don't need to pick and calculate the average of profit of neighbours
    # k=N : sort by the N th parameter and calculate the neighbours profit average to avoid island parameter
    final_results_list = []
    for run in result:
        for strategy in run:
            profit = strategy.analyzers.getbyname('CMA').calmaralt
            # profit = [i for i in strategy.analyzers.getbyname(
            #     'ST').get_analysis().values()][0]
            final_results_list.append([
                profit,
                strategy.params.fastlen,
                strategy.params.slowlen,
                strategy.params.signallen,
                strategy.params.close_fastlen,
                strategy.params.close_slowlen,
                strategy.params.close_signallen,
                strategy.params.topfilter,
                strategy.params.botfilter,
                strategy.params.stop_loss,
                strategy.params.percent
            ])

    if k == 0:
        final_results_list = sorted(final_results_list,
                                    key=lambda x: x[0],
                                    reverse=True)
    else:
        final_results_list = sorted(final_results_list,
                                    key=lambda x: x[k],
                                    reverse=False)
        for i in range(len(final_results_list)):
            if i != 0 and i != len(final_results_list) - 1:
                final_results_list[i].append(
                    (final_results_list[i - 1][0] + final_results_list[i][0] +
                     final_results_list[i + 1][0]) / 3)
            else:
                final_results_list[i].append(0)
        final_results_list = sorted(final_results_list,
                                    key=lambda x: x[-1],
                                    reverse=True)

    if final_results_list[0][0] > maxpara['profit']:
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
    cerebro.resampledata(data, timeframe=bt.TimeFrame.Minutes, compression=60)
    #cerebro.addanalyzer(bt.analyzers.Returns, _name='RT')
    cerebro.addanalyzer(bt.analyzers.CalmarAlt, _name='CMA')
    # cerebro.addanalyzer(SortinoRatio, _name='ST') #dont use this fitness indicator again. it has problems to present the better strategy

    cerebro.broker.setcash(capital)
    cerebro.optstrategy(
        Strat,
        printlog=False,
        percent=testpara['percent'],
        stop_loss=testpara['stop_loss'],
        fastlen=testpara['fastlen'],
        slowlen=testpara['slowlen'],
        signallen=testpara['signallen'],
        close_fastlen=testpara['close_fastlen'],
        close_slowlen=testpara['close_slowlen'],
        close_signallen=testpara['close_signallen'],
        topfilter=testpara['topfilter'],
        botfilter=testpara['botfilter'],
        useMargin=use_Margin)
    result = cerebro.run(optreturn=True)
    return result

def shift(testpara, maxpara, k):
    if k == 0:
        maxpara, testpara = returnmaxpara(
            0,
            result,
            maxpara,
            testpara,
            slowlen=range(maxpara['fastlen'], upper,
                          max(1,int((upper - maxpara['fastlen']) / 10)))) # max(1, ) for ValueError: range() arg 3 must not be zero
    if k == 1:
        maxpara, testpara = returnmaxpara(0,
                                          result,
                                          maxpara,
                                          testpara,
                                          signallen=range(1, upper, step))
    if k == 2:
        maxpara, testpara = returnmaxpara(
            0,
            result,
            maxpara,
            testpara,
            close_fastlen=range(1, maxpara['close_slowlen'],
                                max(1,int(maxpara['close_slowlen'] / 10)))) # max(1, ) for ValueError: range() arg 3 must not be zero
    if k == 3:
        maxpara, testpara = returnmaxpara(
            0,
            result,
            maxpara,
            testpara,
            close_slowlen=range(maxpara['close_fastlen'], upper,
                                max(1,int((upper - maxpara['close_fastlen']) / 10)))) # max(1, ) for ValueError: range() arg 3 must not be zero
    if k == 4:
        maxpara, testpara = returnmaxpara(0,
                                          result,
                                          maxpara,
                                          testpara,
                                          close_signallen=range(
                                              1, upper, step))
    if k == 5:
        maxpara, testpara = returnmaxpara(0,
                                          result,
                                          maxpara,
                                          testpara,
                                          topfilter=range(-1000, 1001, 100))
    if k == 6:
        maxpara, testpara = returnmaxpara(0,
                                          result,
                                          maxpara,
                                          testpara,
                                          botfilter=range(-1000, 1001, 100))
    if k == 7:
        maxpara, testpara = returnmaxpara(0, result, maxpara, testpara)
    return maxpara, testpara

def shift_stagetwo(testpara, maxpara, k):
    if k == 0:
        maxpara, testpara = returnmaxpara(0,
                                          result,
                                          maxpara,
                                          testpara,
                                          slowlen=range(
                                              max(1,
                                                  maxpara['slowlen'] - step),
                                              maxpara['slowlen'] + step))
    if k == 1:
        maxpara, testpara = returnmaxpara(0,
                                          result,
                                          maxpara,
                                          testpara,
                                          signallen=range(
                                              max(1,
                                                  maxpara['signallen'] - step),
                                              maxpara['signallen'] + step))
    if k == 2:
        maxpara, testpara = returnmaxpara(
            0,
            result,
            maxpara,
            testpara,
            close_fastlen=range(max(1, maxpara['close_fastlen'] - step),
                                maxpara['close_fastlen'] + step))
    if k == 3:
        maxpara, testpara = returnmaxpara(
            0,
            result,
            maxpara,
            testpara,
            close_slowlen=range(max(1, maxpara['close_slowlen'] - step),
                                maxpara['close_slowlen'] + step))
    if k == 4:
        maxpara, testpara = returnmaxpara(
            0,
            result,
            maxpara,
            testpara,
            close_signallen=range(max(1, maxpara['close_signallen'] - step),
                                  maxpara['close_signallen'] + step))
    if k == 5:
        maxpara, testpara = returnmaxpara(0,
                                          result,
                                          maxpara,
                                          testpara,
                                          topfilter=range(-1000, 1000, 100))
    if k == 6:
        maxpara, testpara = returnmaxpara(0,
                                          result,
                                          maxpara,
                                          testpara,
                                          botfilter=range(-1000, 1000, 100))
    if k == 7:
        maxpara, testpara = returnmaxpara(0, result, maxpara, testpara)
    return maxpara, testpara


capital = 100000.0
if __name__ == '__main__':

    mps = []
    Strat = StMacdLong
    print(Strat)
    upper = 100
    step = int(upper / 10)

    for i in range(100):
        mid = random.randint(1, upper)
        mid2 = random.randint(1, upper)
        fastlen_int = random.randint(2, mid + 1)
        slowlen_int = random.randint(mid, upper)
        maxpara = {
            'profit': 0,
            'fastlen': fastlen_int,
            'slowlen': slowlen_int,
            'signallen': random.randint(1, 101),
            'close_fastlen': fastlen_int,
            'close_slowlen': slowlen_int,
            'close_signallen': random.randint(1, 31),
            # 'fastlen': 9,
            # 'slowlen': 20,
            # 'signallen': 3,
            # 'close_fastlen': 10,
            # 'close_slowlen': 21,
            # 'close_signallen': 4,
            'topfilter': -9999,
            'botfilter': -9999,
            'stop_loss': 300,
            'percent': 0.15
        }
        testpara = maxpara.copy()
        old_maxpara = [{} for i in range(11)]  # len(maxpara.keys()))]

        # # for stop loss and percent parameters

        # print("For stop_loss")
        # maxpara['profit'] = 0
        # testpara = maxpara.copy()
        # testpara['stop_loss'] = range(500, 0, -100)
        # result = opt(testpara, Strat)
        # maxpara, testpara = returnmaxpara(
        #     0, result, maxpara, testpara)
        # print(maxpara)

        # print("For percent")
        # testpara['percent'] = [0.1, 0.2, 0.3, 0.4, 0.5]
        # result = opt(testpara, Strat)
        # maxpara, testpara = returnmaxpara(
        #     0, result, maxpara, testpara)
        # print(maxpara)

        while old_maxpara[0] != maxpara:
            print("Next iteration")
            old_maxpara[0] = maxpara.copy()
            testpara['fastlen'] = np.append(range(2, maxpara['slowlen'], step),
                                            maxpara['fastlen'])
            # testpara['close_fastlen']=range(1, maxpara['close_slowlen'],
            #                     int(maxpara['close_slowlen'] / 10))
            for k in [0,1,2,3, 4, 7]:  # range(8):
                if old_maxpara[k + 1] != maxpara:
                    result = opt(testpara, Strat)
                    maxpara, testpara = shift(testpara, maxpara, k)
                    old_maxpara[k + 1] = maxpara.copy()
                    print(maxpara)

        maxpara['profit'] = 0
        old_maxpara = [{} for i in range(11)]  # len(maxpara.keys()))]
        testpara = maxpara.copy()
        while old_maxpara[0] != maxpara:
            codes2 = []
            print("Next iteration")
            old_maxpara[0] = maxpara.copy()
            testpara['fastlen'] = range(max(1, maxpara['fastlen'] - step),
                                        maxpara['fastlen'] + step)
            # testpara['close_fastlen']=range(max(1, maxpara['close_fastlen'] - step),
            #                     maxpara['close_fastlen'] + step)
            for k in [0,1,2,3, 4,5,6, 7]:  # range(8):
                if old_maxpara[k + 1] != maxpara:
                    result = opt(testpara, Strat)
                    maxpara, testpara = shift_stagetwo(testpara, maxpara, k)
                    old_maxpara[k + 1] = maxpara.copy()
                    print(maxpara)
        # for stop loss and percent parameters again

        print("For stop_loss")
        maxpara['profit'] = 0
        testpara = maxpara.copy()
        testpara['stop_loss'] = range(500, 100, -100)
        result = opt(testpara, Strat)
        maxpara, testpara = returnmaxpara(0, result, maxpara, testpara)
        print(maxpara)
        # print("For percent")
        # testpara['percent'] = [0.1, 0.2, 0.3, 0.4, 0.5]
        # result = opt(testpara, Strat)
        # maxpara, testpara = returnmaxpara(
        #     0, result, maxpara, testpara)
        # print(maxpara)

        print("Next Parameters")
        mps.append(maxpara)
        with open('output.txt', 'w') as f:
            for item in mps:
                f.write("%s\n" % item)
    print("Complete!")
