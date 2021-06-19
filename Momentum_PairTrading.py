#!/usr/bin/env python
# coding: utf-8

# In[20]:


import pandas as pd
import numpy as np
import numpy
import pandas
import backtrader as bt
import math
import matplotlib.pyplot as plt
from datetime import datetime
from nsepy import get_history
from pandas.tseries.offsets import BDay


class HedgeSize(bt.Sizer):
    def _getsizing(self, comminfo, cash, data, isbuy):
        size = int(cash * 0.5 / data.open[0])
        return size


class Buy_Strength(bt.Strategy):

    def __init__(self):
        self.order = None  # Property to keep track of pending orders.  There are no orders when the strategy is initialized.
        self.buyprice = None
        self.buycomm = None

    def log(self, txt, dt=None):
        # Logging function for the strategy.  'txt' is the statement and 'dt' can be used to specify a specific datetime
        dt = dt or self.data.datetime[0]
        dt = bt.num2date(dt)
        print('{0},{1}'.format(dt.isoformat(), txt))

    def notify_order(self, order):
        # 1. If order is submitted/accepted, do nothing
        if order.status in [order.Submitted, order.Accepted]:
            return
        # 2. If order is buy/sell executed, report price executed
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log('BUY EXECUTED, Price: {0:8.2f}, Cost: {1:8.2f}, Comm: {2:8.2f}'.format(
                    order.executed.price,
                    order.executed.value,
                    order.executed.comm))

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:
                self.log('SELL EXECUTED, {0:8.2f}, Cost: {1:8.2f}, Comm{2:8.2f}'.format(
                    order.executed.price,
                    order.executed.value,
                    order.executed.comm))

            self.bar_executed = len(self)  # when was trade executed
        # 3. If order is canceled/margin/rejected, report order canceled
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        self.log('OPERATION PROFIT, GROSS {0:8.2f}, NET {1:8.2f}'.format(
            trade.pnl, trade.pnlcomm))
        print('Portfolio Value: {0:8.2f}'.format(cerebro.broker.getvalue()))

    def next(self):

        for i, d in enumerate(self.datas):
            current_size = self.getposition(d).size
            if pd.isnull(current_size):
                current_size = 0
            target_size = 0
            if d._name == max_return_stock._name:
                target_size = int(cerebro.broker.getvalue() * 0.5 / d.close[0])
            if d._name == min_return_stock._name:
                target_size = -int(cerebro.broker.getvalue() * 0.5 / d.close[0])
            order_size = target_size - current_size
            if order_size < 0:
                self.log('SELL CREATE SIZE {0:8.2f},{1}'.format(abs(order_size), d._name))
                self.sell(d, size=abs(order_size))
            if order_size > 0:
                self.log('BUY CREATE SIZE {0:8.2f},{1}'.format(abs(order_size), d._name))
                self.buy(d, size=abs(order_size))


cerebro = bt.Cerebro()  # We initialize the `cerebro` backtester.
for s in symbol:
    data = bt.feeds.PandasData(dataname=datas[s])
    cerebro.adddata(data, name=s)
cerebro.addstrategy(Buy_Strength)  # We add the strategy described in the `Strategy class` cell
cerebro.broker.setcash(100000.0)  # We set an initial trading capital of $100,000
cerebro.broker.setcommission(commission=0.001)

print('Starting Portfolio Value: {0:8.2f}'.format(cerebro.broker.getvalue()))
cerebro.run()
print('Final Portfolio Value: {0:8.2f}'.format(cerebro.broker.getvalue()))

get_ipython().run_line_magic('matplotlib', 'inline')
cerebro.plot()

