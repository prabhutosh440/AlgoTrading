import pandas as pd
from datetime import datetime
from nsepy import get_history
from pandas.tseries.offsets import BDay
import yfinance as yf
from CommonUtils import CommonUtils
from Factor import Factor
from BackTraderCommonUtil import Execution, BackTraderCommonUtil
import matplotlib.pyplot as plt

'''Getting the stocks data'''
# symbol=['SBIN.NS','HDFC.NS','ICICIBANK.NS','AXISBANK.NS','KOTAKBANK.NS','CHOLAFIN.NS','MANAPPURAM.NS','SRTRANSFIN.NS','BAJFINANCE.NS','PEL.NS']
symbol = ['SBIN', 'HDFC', 'ICICIBANK', 'AXISBANK', 'KOTAKBANK', 'CHOLAFIN', 'MANAPPURAM','SRTRANSFIN', 'BAJFINANCE', 'PEL']
period = (datetime(2020, 1, 1), datetime(2020, 12, 31))
lookback = BDay(1)
dataPeriod = (period[0] - lookback - BDay(5), period[1])
datas = {}
for s in symbol:
    temp = get_history(s, start=dataPeriod[0], end=dataPeriod[1])
    temp.index = pd.to_datetime(temp.index)
    #     temp=yf.download(s, start=dataPeriod[0], end=dataPeriod[1])
    #     temp.index=pd.to_datetime(temp.index)
    #     temp=temp.filter(['Open','High','Low','Close','Volume','Adj Close']).rename(columns={'Adj Close':'AdjClose'})
    #     temp = temp.dropna(how='all')
    #     temp['Signal']=1
    datas[s] = temp
    datas[s] = temp

'''Creating Signal and Setting it in datas which will be passed to backtrader'''
cmu = CommonUtils()
btCmu = BackTraderCommonUtil()
factor = Factor()
subsetSym = symbol.copy()
symRet = cmu.priceReturns(datas.copy(), dataPeriod, col='VWAP')
factorValue = factor.reversalFactor(symRet, lookback)
factorValue = factorValue[subsetSym]
position = cmu.createPosition(factorValue, weightage='rank')
position = position.truncate(period[0], period[1])
position = position.fillna(method='ffill').fillna(0.0)

dataModel = datas.copy()
for keys in subsetSym:
    temp = position[[keys]]
    temp.columns = ['Signal']
    dataModel[keys] = dataModel[keys].join(temp)
    dataModel[keys] = dataModel[keys][dataModel[keys].index > period[0]]

'''Calling the backtrader'''
params = {'cash': 1000000.0, 'commission': 0.0, 'cheat_on_open': True}
strategyOutput, cerebro = btCmu.runPortfolio(Execution, dataModel, subsetSym,
                                                   (datetime(2020, 1, 1), datetime(2020, 12, 31)), params)

'''Print the Backtest Results'''
btCmu.printAnalyzer(strategyOutput, cerebro)
btCmu.pyfolioAnalyzer(strategyOutput, cerebro)

'''Finally plot the end results'''
# cerebro.plot(style='candlestick')
# plt.rcParams['figure.figsize'] = (16, 8)
# cerebro.plot(iplot=False)