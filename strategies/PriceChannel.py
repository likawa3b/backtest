import backtrader as bt
import pandas as pd
import numpy as np


def initiate(upper, population):
    no_paras = 2
    candidates = pd.DataFrame(np.random.randint(1, upper, size=(population, 2)), columns=[
                              'periodH', 'periodL'])
    candidates['mutation'] = None
    return candidates, no_paras


class StPC(bt.Strategy):
    params = (
        ('periodH', 20),
        ('periodL', 20),
        ('printlog', False),
        ('stop_loss', 300),
        ('percent', 0.1),
        ('usePercent', True),
        ('useMargin', True),
        ('commission', 0.001)
    )

    def log(self, txt, dt=None, doprint=False):
        ''' Logging function fot this strategy'''
        if self.params.printlog or doprint:
            dt = dt or self.datas[0].datetime.date(0)
            print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close

        if self.params.useMargin:
            self.broker.setcommission(
                commission=self.params.commission*self.params.stop_loss, margin=self.params.stop_loss)

        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None
        self.stop_price = 0
        self.hh = bt.indicators.Highest(
            self.data.high(-1), period=self.params.periodH, plot=False)
        self.ll = bt.indicators.Lowest(
            self.data.low(-1), period=self.params.periodL, plot=False)

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
                self.log('Close EXECUTED, Price: %.2f, Cost: %.2f, Cash: %.2f, Position:%d' %
                         (order.executed.price,
                          order.executed.value,
                          self.broker.get_cash(),
                          self.position.size))
            else:
                self.price = order.executed.price
                self.comm = order.executed.comm
                if order.isbuy():
                    self.stop_price = (self.price - self.params.stop_loss)
                    self.log(
                        'BUY EXECUTED, Price: %.2f, Cost: %.2f, Commission:%.2f, Cash: %.2f, Position:%d' %
                        (self.price,
                         order.executed.value,
                         self.comm,
                         self.broker.get_cash(),
                         self.position.size))
                elif order.issell():
                    self.stop_price = (self.price + self.params.stop_loss)
                    self.log(
                        'SELL EXECUTED, Price: %.2f, Cost: %.2f, Commission:%.2f, Cash: %.2f, Position:%d' %
                        (self.price,
                         order.executed.value,
                         self.comm,
                         self.broker.get_cash(),
                         self.position.size))

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
        self.log('(periodH: %d\\periodL: %d) Ending Value %.2f Stoploss: %d' %
                 (self.params.periodH, self.params.periodL, self.broker.getvalue(), self.params.stop_loss), doprint=True)


class StPCLong(StPC):

    def next_open(self):
        # Simply log the closing price of the series from the reference
        # self.log('Close, %.2f' % self.dataclose[0])

        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return

        # Check if we are in the market
        if not self.position:

            # Not yet ... we MIGHT BUY if ...

            if self.datas[0].open[0] > self.hh:

                # BUY, BUY, BUY!!! (with all possible default parameters)
                self.log('BUY CREATE, %.2f' % self.datas[0].open[0])

                # Keep track of the created order to avoid a 2nd order
                if self.params.usePercent:
                    if self.params.useMargin:
                        size = int(self.broker.get_cash() *
                                   self.params.percent / self.params.stop_loss)
                    else:
                        size = int(self.broker.get_cash() *
                                   self.params.percent / self.datas[0].open[0])
                else:
                    size = 1
                if size != 0:
                    self.order = self.buy(size=size)

        else:

            if self.datas[0].open[0] < self.ll:
                # SELL, SELL, SELL!!! (with all possible default parameters)
                self.log('close CREATE, %.2f' % self.datas[0].open[0])

                # Keep track of the created order to avoid a 2nd order
                self.order = self.close(oco=self.exitOrder)
            elif self.datas[0].low[0] <= self.stop_price or self.datas[0].open[0] <= self.stop_price:
                self.exitOrder = self.close(
                    exectype=bt.Order.Stop, price=self.stop_price)


class StPCShort(StPC):

    def next_open(self):
        # Simply log the closing price of the series from the reference
        # self.log('Close, %.2f' % self.dataclose[0])

        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return

        # Check if we are in the market
        if not self.position:

            if self.datas[0].open[0] < self.ll:

                # SELL, SELL, SELL!!! (with all possible default parameters)
                self.log('SELL CREATE, %.2f' % self.datas[0].open[0])

                # Keep track of the created order to avoid a 2nd order
                if self.params.usePercent:
                    if self.params.useMargin:
                        size = int(self.broker.get_cash() *
                                   self.params.percent / self.params.stop_loss)
                    else:
                        size = int(self.broker.get_cash() *
                                   self.params.percent / self.datas[0].open[0])
                else:
                    size = 1
                if size != 0:
                    self.order = self.sell(size=size)

        else:

            if self.datas[0].open[0] > self.hh:
                # Close
                self.log('close CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.order = self.close(oco=self.exitOrder)
            elif self.datas[0].high[0] >= self.stop_price or self.datas[0].open[0] >= self.stop_price:
                self.exitOrder = self.close(
                    exectype=bt.Order.Stop, price=self.stop_price)
