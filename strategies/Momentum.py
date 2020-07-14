import backtrader as bt
import pandas as pd
import numpy as np


def initiate(upper, population, filterrange, outputreuse, *args):
    no_paras = 6

    if outputreuse:
        for df in args:
            seedslength = len(df.index)
    else:
        seedslength = 0
    candidates = pd.DataFrame(np.random.randint(1,
                                                upper,
                                                size=(population - seedslength,
                                                      2)),
                              columns=['period1', 'period2'])
    # candidates = pd.DataFrame([[30, 157]], columns=[
    #     'period1', 'period2'])
    # candidates = candidates.loc[candidates.index.repeat(
    #     population - seedslength)].reset_index(drop=True)
    candidates = candidates.join(
        pd.DataFrame(np.random.uniform(-filterrange,
                                       filterrange,
                                       size=(population - seedslength, 4)),
                     columns=[
                         'entryfilter1', 'entryfilter2', 'closefilter1',
                         'closefilter2'
                     ]))
    if outputreuse:
        for df in args:
            candidates = candidates.append(df, ignore_index=True)

    candidates['mutation'] = None
    return candidates, no_paras


class StMt(bt.Strategy):
    params = (('period1', 12), ('period2', 12), ('entryfilter1', 0),
              ('entryfilter2', 0), ('closefilter1', 0), ('closefilter2', 0),
              ('printlog', False), ('stop_loss', 0.01), ('percent', 0.1),
              ('usePercent', True), ('useMargin', True), ('commission', 0.02))

    def log(self, txt, dt=None, doprint=False):
        ''' Logging function fot this strategy'''
        if self.params.printlog or doprint:
            dt = dt or self.datas[0].datetime.date(0)
            print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        # !!! You cannot access self.dataclose[0] in here
        self.dataclose = self.datas[0].close

        if self.params.useMargin:
            self.broker.setcommission(commission=self.params.commission *
                                      self.params.stop_loss,
                                      margin=self.params.stop_loss)

        # To keep track of pending orders and buy price/commission
        self.order = None
        self.exitOrder = None
        self.buyprice = None
        self.buycomm = None
        self.stop_price = 0

        self.mom = bt.indicators.Momentum(self.dataclose,
                                          period=self.params.period1,
                                          plot=False)
        self.momO = self.mom / self.dataclose(-self.params.period1)

        self.momC = bt.indicators.Momentum(self.mom,
                                           period=self.params.period2,
                                           plot=False)
        self.momCO = self.momC / self.dataclose(-self.params.period2)

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.p.exectype == bt.Order.Stop:
                self.log('Order stop loss, Position:%d' % self.position.size)

            elif order.p.exectype == bt.Order.Close:  # Close
                self.log(
                    'Close EXECUTED, Price: %.2f, Cost: %.2f, Cash: %.2f, Position:%d'
                    % (order.executed.price, order.executed.value,
                       self.broker.get_cash(), self.position.size))
            else:
                self.price = order.executed.price
                self.comm = order.executed.comm
                if order.isbuy():
                    self.stop_price = (self.price -
                                       self.price * self.params.stop_loss)
                    self.log(
                        'BUY EXECUTED, Price: %.2f, Cost: %.2f, Commission:%.2f, Cash: %.2f, Position:%d'
                        % (self.price, order.executed.value, self.comm,
                           self.broker.get_cash(), self.position.size))
                elif order.issell():
                    self.stop_price = (self.price +
                                       self.price * self.params.stop_loss)
                    self.log(
                        'SELL EXECUTED, Price: %.2f, Cost: %.2f, Commission:%.2f, Cash: %.2f, Position:%d'
                        % (self.price, order.executed.value, self.comm,
                           self.broker.get_cash(), self.position.size))

            self.bar_executed = len(self)

        elif order.status in [order.Rejected]:
            self.log('Order Rejected')
        elif order.status in [order.Canceled]:
            self.log('Order Canceled')
        elif order.status in [order.Margin]:
            self.log('Order Margin')
        # Write down: no pending order
        self.order = None
        self.exitOrder = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))

    def stop(self):
        self.log(
            '(period1: %d\\period2: %d) (entry1: %.3f\\entry2: %.3f) (close1: %.3f\\close2: %.3f) Cutloss: %.3f Percent: %.1f Ending Value %.2f'
            % (self.params.period1, self.params.period2,
               self.params.entryfilter1, self.params.entryfilter2,
               self.params.closefilter1, self.params.closefilter2,
               self.params.stop_loss, self.params.percent,
               self.broker.getvalue()),
            doprint=True)


class StMtLong(StMt):
    def next(self):
        # Simply log the closing price of the series from the reference
        # self.log('Close, %.2f' % self.dataclose[0])

        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return

        # Check if we are in the market
        if not self.position:

            # Not yet ... we MIGHT BUY if ...
            if (self.momO[0]) > self.params.entryfilter1 and (
                    self.momCO[0]) > self.params.entryfilter2:

                # BUY, BUY, BUY!!! (with all possible default parameters)
                self.log('BUY CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                if self.params.usePercent:
                    if self.params.useMargin:
                        size = int(
                            (self.broker.get_cash() * self.params.percent) /
                            (self.params.stop_loss * self.dataclose[0]))
                    else:
                        size = int(
                            (self.broker.get_cash() * self.params.percent) /
                            self.dataclose[0])
                else:
                    size = 1
                if size != 0:
                    self.order = self.buy(size=size)

        else:

            if (self.momO[0]) < self.params.closefilter1 and (
                    self.momCO[0]) < self.params.closefilter2:
                # SELL, SELL, SELL!!! (with all possible default parameters)
                self.log('close CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.order = self.close(oco=self.exitOrder)
            elif self.datas[0].low[0] <= self.stop_price or self.dataclose[
                    0] <= self.stop_price:
                self.exitOrder = self.close(exectype=bt.Order.Stop,
                                            price=self.stop_price)


class StMtShort(StMt):
    def next(self):

        # Simply log the closing price of the series from the reference
        # self.log('Close, %.2f' % self.dataclose[0])

        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return

        # Check if we are in the market
        if not self.position:

            if (self.momO[0]) < self.params.entryfilter1 and (
                    self.momCO[0]) < self.params.entryfilter2:

                # SELL, SELL, SELL!!! (with all possible default parameters)
                self.log('SELL CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                if self.params.usePercent:
                    if self.params.useMargin:
                        size = int(self.broker.get_cash() *
                                   self.params.percent /
                                   (self.params.stop_loss * self.dataclose[0]))
                    else:
                        size = int(self.broker.get_cash() *
                                   self.params.percent / self.dataclose[0])
                else:
                    size = 1
                if size != 0:
                    self.order = self.sell(size=size)

        else:

            if (self.momO[0]) > self.params.closefilter1 and (
                    self.momCO[0]) > self.params.closefilter2:
                # Close
                self.log('close CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.order = self.close(oco=self.exitOrder)
            elif self.datas[0].high[0] >= self.stop_price or self.dataclose[
                    0] >= self.stop_price:
                self.exitOrder = self.close(exectype=bt.Order.Stop,
                                            price=self.stop_price)
