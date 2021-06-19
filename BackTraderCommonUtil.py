import pandas as pd
import backtrader as bt
import pyfolio as pf
import matplotlib.pyplot as plt
from pandas.tseries.offsets import BDay

class CustomDataLoader(bt.feeds.PandasData):
    lines = ('AdjClose', 'Signal',)
    params = (
        ('AdjClose', -1),
        ('Signal', -1),
    )
    datafields = bt.feeds.PandasData.datafields + (['AdjClose', 'Signal'])


class BaseStrategy(bt.Strategy):

    def __init__(self):
        super().__init__()
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
        # print(self.data.datetime.date())
        self.log('OPERATION PROFIT, GROSS {0:8.2f}, NET {1:8.2f}'.format(trade.pnl, trade.pnlcomm))


class BackTraderCommonUtil():

    def init(self):
        pass

    def runPortfolio(self, strategy, dataDict, symbol, period, params):
        cerebro = bt.Cerebro(cheat_on_open=params['cheat_on_open'])  # We initialize the `cerebro` backtester.
        for s in symbol:
            data = CustomDataLoader(dataname=dataDict[s].copy())
            cerebro.adddata(data, name=s)

        cerebro.addstrategy(strategy, period, cerebro)  # We add the strategy described in the `Strategy class` cell
        cerebro.broker.setcash(params['cash'])  # We set an initial trading capital of $100,000
        # https://www.backtrader.com/blog/posts/2016-12-06-shorting-cash/shorting-cash/
        # cerebro.broker.set_shortcash(False)
        cerebro.broker.setcommission(commission=params['commission'])

        # Add the analyzers we are interested in
        cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="ta")
        cerebro.addanalyzer(bt.analyzers.SQN, _name="sqn")
        cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='mysharpe')
        cerebro.addanalyzer(bt.analyzers.AnnualReturn, _name='myannual')
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name='mydrawdown')
        cerebro.addanalyzer(bt.analyzers.Returns, timeframe=bt.TimeFrame.Days, compression=1, tann=365)
        cerebro.addanalyzer(bt.analyzers.TimeReturn, timeframe=bt.TimeFrame.NoTimeFrame)
        cerebro.addanalyzer(bt.analyzers.TimeReturn, timeframe=bt.TimeFrame.NoTimeFrame, data=data,
                            _name='buyandhold')
        # pyfolio is a Python library for performance and risk analysis of financial portfolios developed by Quantopian Inc.
        cerebro.addanalyzer(bt.analyzers.PyFolio, _name='pyfolio')

        print('Starting Portfolio Value: {0:8.2f}'.format(cerebro.broker.getvalue()))
        strategyOutput = cerebro.run()
        print('Final Portfolio Value: {0:8.2f}'.format(cerebro.broker.getvalue()))

        return strategyOutput, cerebro

    def printAnalyzer(self, strategyOutput, cerebro):
        results = strategyOutput[0]
        self.printTradeAnalysis(results.analyzers.ta.get_analysis())
        self.printSQN(results.analyzers.sqn.get_analysis())

        # Get final portfolio Value
        portvalue = cerebro.broker.getvalue()

        # Print out the final result
        print('Final Portfolio Value: ${}'.format(portvalue))

        print('Sharpe Ratio:', results.analyzers.mysharpe.get_analysis()['sharperatio'])
        for key, value in results.analyzers.myannual.get_analysis().items():
            print('Annual Return:', key, "=", round(value * 100, 2), "%")

        #     print('Drawdown Info:', results.analyzers.mydrawdown.get_analysis())
        print('Max Drawdown: %.2f%%' % results.analyzers.mydrawdown.get_analysis().max.drawdown)

    def printTradeAnalysis(self, analyzer):
        '''
        Function to print the Technical Analysis results in a nice format.

        Strike Rate: This is the a percentage that represents the number of times you win vs the total number of
                    trades you placed (win rate / total trades). It can help identify to whether you have an edge in the market.
                    Some people aim for to get the strike rate as high as possible. Usually with lots of small wins.
                    Others are happy with lower strike rates but aim for big wins and small losses.
        '''
        # Get the results we are interested in
        total_open = analyzer.total.open
        total_closed = analyzer.total.closed
        total_won = analyzer.won.total
        total_lost = analyzer.lost.total
        win_streak = analyzer.streak.won.longest
        lose_streak = analyzer.streak.lost.longest
        pnl_net = round(analyzer.pnl.net.total, 2)
        strike_rate = (total_won / total_closed) * 100
        # Designate the rows
        h1 = ['Total Open', 'Total Closed', 'Total Won', 'Total Lost']
        h2 = ['Strike Rate', 'Win Streak', 'Losing Streak', 'PnL Net']
        r1 = [total_open, total_closed, total_won, total_lost]
        r2 = [round(strike_rate, 2), win_streak, lose_streak, pnl_net]
        # Check which set of headers is the longest.
        if len(h1) > len(h2):
            header_length = len(h1)
        else:
            header_length = len(h2)
        # Print the rows
        print_list = [h1, r1, h2, r2]
        row_format = "{:<20}" * (header_length + 1)
        print("Trade Analysis Results:")
        for row in print_list:
            print(row_format.format('', *row))

    def printSQN(self, analyzer):
        '''
        SQN measures the relationship between the mean (expectancy) and the standard deviation of the R-multiple
        distribution generated by a trading system. It also makes an adjustment for the number of trades involved
        For more information see: http://www.vantharp.com/tharp-concepts/sqn.asp

        Note: The Backtrader documentation provides a helpful ranking system for SQN:
        1.6 – 1.9 Below average
        2.0 – 2.4 Average
        2.5 – 2.9 Good
        3.0 – 5.0 Excellent
        5.1 – 6.9 Superb
        7.0 – Holy Grail?
        '''
        sqn = round(analyzer.sqn, 2)
        print('SQN: {}'.format(sqn))

    def pyfolioAnalyzer(self, strategyOutput, cerebro):
        results = strategyOutput[0]
        pyfoliozer = results.analyzers.pyfolio
        returns, positions, transactions, gross_lev = pyfoliozer.get_pf_items()
        returns.name = 'Strategy'
        returns.head(2)

        # get benchmark returns
        #     benchmark_rets= stock['returns']
        #     benchmark_rets.index = benchmark_rets.index.tz_localize('UTC')
        #     benchmark_rets = benchmark_rets.filter(returns.index)
        #     benchmark_rets.name = 'Nifty-50'
        #     benchmark_rets.head(2)
        benchmark_rets = None

        # get performance statistics for strategy
        pf.show_perf_stats(returns)
        # plot performance for strategy vs benchmark
        fig, ax = plt.subplots(nrows=2, ncols=2, figsize=(16, 9), constrained_layout=True)
        axes = ax.flatten()
        #     pf.plot_drawdown_periods(returns=returns, ax=axes[0])
        #     axes[0].grid(True)
        pf.plot_rolling_returns(returns=returns,
                                factor_returns=benchmark_rets,
                                ax=axes[1], title='Strategy vs Nothing')
        axes[1].grid(True)
        pf.plot_drawdown_underwater(returns=returns, ax=axes[2])
        axes[2].grid(True)
        pf.plot_rolling_sharpe(returns=returns, ax=axes[3])
        axes[3].grid(True)
        plt.grid(True)
        plt.legend()
        plt.tight_layout()


class Execution(BaseStrategy):

    def __init__(self, period, cerebro):
        super().__init__()
        self.cerebro = cerebro
        self.period = period

    # it should be next if cheat_on_open is false
    def next_open(self):
        print(self.period)
        for i, d in enumerate(self.datas):
            current_size = self.getposition(d).size
            if pd.isnull(current_size):
                current_size = 0

            if self.data.datetime.date() >= self.period[0].date() and self.data.datetime.date() < self.period[
                1].date() - BDay(1):
                # print('instrument', d)
                print("date at t", self.data.datetime.date())
                print("signal value", d.Signal[0])
                print("open value t+1", d.open[1])
                print("value of the portfolio", self.cerebro.broker.getvalue())

                # target_size=int(self.cerebro.broker.getvalue()*d.Signal[0]/d.open[1])
                target_size = int(self.cerebro.broker.getvalue() * d.Signal / d.open)
                order_size = target_size - current_size

                if order_size < 0:
                    self.log('SELL CREATE SIZE {0:8.2f},{1}'.format(abs(order_size), d._name))
                    #                     self.sell(d,size=abs(order_size), exectype=bt.Order.Limit, price= d.open[1])
                    self.sell(d, size=abs(order_size))
                if order_size > 0:
                    self.log('BUY CREATE SIZE {0:8.2f},{1}'.format(abs(order_size), d._name))
                    #                     self.buy(d,size=abs(order_size), exectype=bt.Order.Limit, price= d.open[1])
                    self.buy(d, size=abs(order_size))
