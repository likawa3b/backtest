import backtrader as bt
import pandas as pd
from strategies.MacdLong import *
from strategies.MacdShort import *
from strategies.Momentum import *
import itertools


class Cerebro_GA(bt.Cerebro):
    def optstrategy_GA(self, strategy, paras, *args):
        self._dooptimize = True

        args = self.iterize(args)
        optargs = itertools.product(*args)

        paraskwargs = paras.to_dict('index')
        paraskwargsmap = map(dict, paraskwargs.values())
        # print(paraskwargsmap)
        it = itertools.product([strategy], optargs, paraskwargsmap)

        self.strats.append(it)
        # return it


def evaluate(candidates, data, no_paras,
             strat, stock, capital, testpara):

    cerebro = Cerebro_GA(stdstats=False)
    cerebro.broker.setcash(capital)
    if stock == 'HSI' or stock == 'hsi' or stock == 'future':
        cerebro.resampledata(data,
                             timeframe=bt.TimeFrame.Minutes,
                             compression=60)
    else:
        cerebro.adddata(data)
    cerebro.addanalyzer(bt.analyzers.Returns, _name='RT')
    if testpara['useMargin']:
        cerebro.broker.setcommission(margin=testpara['stop_loss'])
    # cerebro.addanalyzer(bt.analyzers.CalmarAlt, _name='CMA')
    # cerebro.addobserver(bt.observers.Value)
    # cerebro.addobserver(bt.observers.Trades)
    # cerebro.addobserver(bt.observers.BuySell)
    # cerebro.addobserver(bt.observers.DrawDown)

    paras = candidates.iloc[:, 0:no_paras].copy()
    paras.loc[:, 'stop_loss'] = testpara['stop_loss']
    paras.loc[:, 'usePercent'] = testpara['usePercent']
    paras.loc[:, 'useMargin'] = testpara['useMargin']
    if testpara['usePercent']:
        paras.loc[:, 'percent'] = testpara['percent']

    cerebro.optstrategy_GA(strat, paras)
    # print(it)
    # print(type(it))
    # for i in it:
    #     print(i)

    result = cerebro.run()
    profit_list = []
    for run in result:
        for strategy in run:
            # profit = strategy.analyzers.getbyname('CMA').calmaralt
            # profit_list.append(profit)
            profit = strategy.analyzers.RT.get_analysis()
            profit_list.append(profit['rtot'])
        #     print(type(strategy))
        # profit = (strategy.broker.get_value() - capital) / capital
    candidates['profit'] = pd.Series(profit_list)
    # print(profit_list)
    return candidates

    # print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
    #
    # print('Final Portfolio: %.2f%%' %
    #       (cerebro.broker.getvalue() * 100 / capital))
