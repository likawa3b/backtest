import pandas as pd
import random
import numpy as np
import datetime
import matplotlib.pyplot as plt
from GA_fitness import *
from strategies.Momentum import *


def select(candidates):
    candidates['probability'] = minp + \
        (maxp - minp) * (candidates.index) / (len(candidates.index) - 1)
    # candidates['probability'] = candidates['profit'] - candidates.iloc[0, 7]
    candidates.iloc[-int((len(candidates.index)) * keep_percent):, -1] = 99
    candidates = candidates.sample(frac=0.5, weights='probability')
    candidates = candidates.reset_index(drop=True)
    return candidates


def crossover(father, mother, no_paras):
    position1 = random.randint(0, no_paras - 3)
    position2 = random.randint(position1 + 1, no_paras - 1) + 1
    son1 = father[0:position1].append(mother[position1:position2]).append(
        father[position2:no_paras])
    son2 = mother[0:position1].append(father[position1:position2]).append(
        mother[position2:no_paras])
    return son1, son2


def reproduce(parents, no_paras, candidates):
    parents = parents.sample(frac=1)
    parents = parents.reset_index(drop=True)
    pairsOfParents = int(len(parents) / 2)
    for i in range(pairsOfParents):
        if random.random() <= cross_rate:
            parents.iloc[i], parents.iloc[i + pairsOfParents] = crossover(
                parents.iloc[i], parents.iloc[i + pairsOfParents], no_paras)

            if (candidates == parents.iloc[i, :no_paras]).all(1).any():
                # print('Duplicated!')
                # Individual Mutation
                p = random.randint(2, no_paras - 1)
                if p < 2:
                    parents.iloc[i, p] = random.randint(2, upper)
                elif p >= 2:
                    parents.iloc[i, p] = random.uniform(
                        -filterrange, filterrange)

            if (candidates == parents.iloc[i + pairsOfParents, :no_paras]
                ).all(1).any():
                # print('Duplicated!')
                p = random.randint(2, no_paras - 1)
                if p < 2:
                    parents.iloc[i + pairsOfParents, p] = random.randint(
                        2, upper)
                elif p >= 2:
                    parents.iloc[i + pairsOfParents, p] = random.uniform(
                        -filterrange, filterrange)
    return parents


def rangeSearch(best_one, column):
    sons = pd.DataFrame([best_one] * 10)
    for i in range(10):
        if column <= 1:
            pass
            # sons.iloc[i, column] = max((sons.iloc[i, column] + i - 5), 2)
        else:
            sons.iloc[i, column] = sons.iloc[i, column] + \
                ((0.2/9*i)-0.1)*filterrange
    return sons


def mutation(sons, no_paras):
    sons['mutation'] = np.random.rand(int(len(sons)), 1)
    mutes = sons.loc[sons['mutation'] <= muta_rate]
    for i in mutes.iterrows():
        p = random.randint(2, no_paras - 1)
        if p < 2:
            i[1][p] = random.randint(2, upper)
        elif p >= 2:
            i[1][p] = random.uniform(-filterrange, filterrange)
    sons.loc[sons['mutation'] <= muta_rate] = mutes
    return sons


generations = 1000
population = 200
keep_percent = 0.01
cross_rate = 1
muta_rate = 0.5
upper = 200
filterrange = 0.1 #Momentum Entry/Close filter range 
minp = 0.0
maxp = 1.0

if __name__ == '__main__':
    stock = 'future'
    capital = 100000.0
    strat = StMtLong
    testpara = {
        "usePercent": True,
        'useMargin': True,
        'stop_loss': 0.016,
        'percent': 0.1
    }

    if stock == 'HSI' or stock == 'hsi':
        df = pd.read_csv('ProccessedData\TVC_HSI, 60.csv')
        df.index = pd.to_datetime(df['time'], unit='s')
        df = df[['open', 'high', 'low',
                 'close']].rename(columns={
                     "open": "Open",
                     "high": "High",
                     "low": "Low",
                     "close": "Close"
                 })  # ['2014-01-02':'2017-01-01']
        data = bt.feeds.PandasData(dataname=df, volume=None, openinterest=None)
    elif stock == 'future':
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
    elif stock == 'SMH':
        df = pd.read_csv('RawData\SMH_Adj.csv',
                         index_col='Date',
                         parse_dates=True)
        data = bt.feeds.PandasData(dataname=df, openinterest=None)
    elif stock == 'SPY':
        df = pd.read_csv('RawData\SPY.csv', index_col='Date', parse_dates=True)
        data = bt.feeds.PandasData(dataname=df, openinterest=None)
    else:
        data = bt.feeds.YahooFinanceData(dataname=stock,
                                         fromdate=datetime.datetime(
                                             1993, 1, 29),
                                         todate=datetime.date.today(),
                                         reverse=False,
                                         period='D')

    print(strat, "|use Percent =", testpara['usePercent'], "|use Margin =",
          testpara['useMargin'])

    outputreuse = False
    if outputreuse:
        seeds = pd.read_csv('output.csv',
                            index_col=0).drop_duplicates().iloc[-15:, :6]
        seedsx = [[
            26, 141, 0.013198363982972444, -0.016699831347744068, -0.0005,
            0.00015
        ]]
        seedsdf = seeds.append(pd.DataFrame(seedsx,
                                            columns=[
                                                'period1', 'period2',
                                                'entryfilter1', 'entryfilter2',
                                                'closefilter1', 'closefilter2'
                                            ]),
                               ignore_index=True)
        print(seedsdf)
        candidates, no_paras = initiate(upper, population, filterrange,
                                        outputreuse, seedsdf)
    else:
        candidates, no_paras = initiate(upper, population, filterrange,
                                        outputreuse)
    candidates = evaluate(candidates, data, no_paras, strat, stock, capital,
                          testpara)
    candidates = candidates.sort_values(by=['profit'],
                                        ascending=True).reset_index(drop=True)
    print(candidates)
    candidates.to_csv('output.csv')
    best = []
    for i in range(generations):
        parents = select(candidates.iloc[-population:])
        sons = reproduce(parents, no_paras, candidates.iloc[:, :no_paras])
        sons = mutation(sons, no_paras)
        best_sons = rangeSearch(candidates.iloc[-1], int(i % no_paras))
        sons.append(best_sons, ignore_index=True)
        sons = evaluate(sons, data, no_paras, strat, stock, capital, testpara)
        candidates = sons.append(parents, ignore_index=True)
        candidates = candidates.sort_values(
            by=['profit'], ascending=True).reset_index(drop=True)
        print(candidates)
        candidates.to_csv('output.csv')
        best.append(candidates.iloc[-1]['profit'])
    # candidates = evaluate(candidates, data,strat,stock, capital,testpara)
    # candidates = candidates.sort_values(
    #     by=['profit'], ascending=False).reset_index(drop=True)
    candidates.to_csv('output.csv')
    print(best)
    plt.plot(best)
    plt.show()
    # candidates
