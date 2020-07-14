import backtrader as bt
import pandas as pd
import numpy as np


def initiate(upper, population):
    no_paras = 8
    candidates = pd.DataFrame(np.random.randint(1, upper, size=(population, 6)), columns=[
                              'fastlen', 'slowlen', 'signallen', 'close_fastlen', 'close_slowlen', 'close_signallen'])
    candidates['topfilter_macd'] = np.random.randint(0, 200, size=population)
    candidates['topfilter_signal'] = np.random.randint(0, 200, size=population)
    candidates['botfilter_macd'] = np.random.randint(0, 200, size=population)
    candidates['botfilter_signal'] = np.random.randint(0, 200, size=population)
    candidates['mutation'] = None
    return candidates, no_paras


class StMacdMtLong(bt.Strategy):
    params = (
        ('fastlen', 12),
        ('slowlen', 26),
        ('signallen', 9),
        ('close_fastlen', 12),
        ('close_slowlen', 26),
        ('close_signallen', 9),
        ('topfilter_macd', 0),
        ('botfilter_signal', 0),
        ('topfilter_macd', 0),
        ('botfilter_signal', 0),
        ('printlog', False),
        ('stop_loss', 1000),
        ('percent', 0.1),
        ('usePercent', True),
        ('useMargin', True),
        ('commission', 0.01)
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
        self.macd = bt.indicators.MACD(self.dataclose,
                                       period_me1=self.params.fastlen,
                                       period_me2=self.params.slowlen,
                                       period_signal=self.params.signallen,
                                       plot=False)

        # self.close_fema = bt.indicators.EMA(
        #     self.dataclose, period=self.params.close_fastlen, plot=False)
        # self.close_sema = bt.indicators.EMA(
        #     self.dataclose, period=self.params.close_slowlen, plot=False)

        # self.close_macd = self.close_fema - self.close_sema

        # self.close_macdsignal = bt.indicators.EMA(
        #     self.close_macd, period=self.params.close_signallen, plot=False)

        self.close_macd = bt.indicators.MACD(self.dataclose,
                                             period_me1=self.params.close_fastlen,
                                             period_me2=self.params.close_slowlen,
                                             period_signal=self.params.close_signallen,
                                             plot=False)

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
                self.stop_price = (self.buyprice - self.params.stop_loss)
                self.log(
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Commission:%.2f, Cash: %.2f, Position:%d' %
                    (order.executed.price,
                     order.executed.value,
                     self.buycomm,
                     self.broker.get_cash(),
                     self.position.size))

            elif order.p.exectype == bt.Order.Stop:
                self.log('Order stop loss, Price: %.2f, Position:%d' %
                         (order.executed.price,
                          self.position.size))

            else:  # Close
                self.log('Close EXECUTED, Price: %.2f, Cost: %.2f, Cash: %.2f, Position:%d' %
                         (order.executed.price,
                          order.executed.value,
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

    def next(self):
        # Simply log the closing price of the series from the reference
        # self.log('Close, %.2f' % self.dataclose[0])

        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return
        # macd.append(self.macd.macd[0])
        # signal.append(self.macd.signal[0])
        # Check if we are in the market
        if not self.position:

            # Not yet ... we MIGHT BUY if ...

            if self.macd.macd[0] >= self.params.botfilter_macd and self.macd.signal[0] >= self.params.botfilter_signal : 

                # BUY, BUY, BUY!!! (with all possible default parameters)
                self.log('BUY CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                if self.params.usePercent:
                    if self.params.useMargin:
                        size = int(self.broker.get_cash() *
                                   self.params.percent / self.params.stop_loss)
                    else:
                        size = int(self.broker.get_cash() *
                                   self.params.percent / self.dataclose[0])
                else:
                    size = 1
                if size != 0:
                    self.order = self.buy(size=size)

        else:

            if self.close_macd.macd[0] <= self.params.topfilter_macd and self.close_macd.signal[0] <= self.params.topfilter_signal:
                # SELL, SELL, SELL!!! (with all possible default parameters)
                self.log('close CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.order = self.close(oco=self.exitOrder)
            
            elif self.datas[0].low[0] <= self.stop_price or self.dataclose[0] <= self.stop_price:
                self.exitOrder = self.close(
                    exectype=bt.Order.Stop, price=self.stop_price)

    def stop(self):
        self.log('(Entry: %d\\%d\\%d botFilter: %d)(Close: %d\\%d\\%d topFilter: %d) Cutloss: %.1f Percent: %d Commission: %.1f%% Ending Value %.2f' %
                 (self.params.fastlen, self.params.slowlen, self.params.signallen, self.params.botfilter_macd, self.params.botfilter_signal,
                  self.params.close_fastlen, self.params.close_slowlen, self.params.close_signallen, self.params.topfilter_macd, self.params.topfilter_signal, 
                  self.params.stop_loss,
                  self.params.percent,
                  self.broker.getcommissioninfo(self.data).getcommission(1, None)*100/self.params.stop_loss, self.broker.getvalue()), doprint=True)
