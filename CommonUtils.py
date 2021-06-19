import pandas,numpy

class CommonUtils():

    def init(self):
        pass

    def priceReturns(self,priceData, period, col='vwap', retType='normal'):
        '''
        function will return symbols return
        priceDict: Dictionary containing price data with keys as symbols
        period: Tuple containing start date and end date
        col: columns on which returns need to be calculated
        type: log return or non-log return
        '''
        symRet = None
        _priceData = priceData.copy()

        def ret_g_df(priceDf, retType):
            if retType == 'normal':
                temp = priceDf.pct_change()
            elif retType == 'log':
                temp = numpy.log(priceDf / priceDf.shift(1))
            else:
                raise NotImplementedError

            return temp

        if isinstance(_priceData, dict):
            for keys in _priceData:
                priceDf = _priceData[keys]
                temp = ret_g_df(priceDf[[col]].copy(), retType=retType)
                temp.columns = [keys]
                if symRet is None:
                    symRet = temp.copy()
                else:
                    symRet = symRet.join(temp, how='outer')

        elif isinstance(_priceData, pandas.DataFrame):
            symRet = ret_g_df(_priceData, retType=retType)

        symRet = symRet.truncate(period[0], period[1])
        return symRet


    def createPosition(self,factorValue, type='xs', weightage='rank'):
        '''
        write comments
        '''
        originalDf = factorValue.copy()
        _factorValue = factorValue.copy()
        rankDf = _factorValue.rank(axis=1, ascending=False, pct=False)
        midRank = rankDf.mean(axis=1, skipna=True)
        positionDf = rankDf.apply(lambda x: midRank - x, axis=0)
        if type == 'xs':
            if weightage == 'rank':
                posAdd = positionDf.apply(lambda x: sum(x[x > 0]), axis=1)
                positionDf = positionDf.divide(posAdd, axis='index')
            elif weightage == 'equal':
                def func(row):
                    posAdd = sum(row[row > 0])
                    negAdd = -1 * (sum(row[row < 0]))
                    row[row > 0] = row[row > 0] / posAdd
                    row[row < 0] = row[row < 0] / negAdd
                    return row

                signedDf = numpy.sign(positionDf)
                positionDf = signedDf.apply(func, axis=1)

        else:
            raise NotImplementedError
        positionDf[numpy.isnan(originalDf)] = numpy.nan

        return positionDf


    def convertDict_To_Df_g_Col(self,dictData, col):
        output = None
        _dictData = dictData.copy()
        for keys in _dictData:
            priceDf = _dictData[keys]
            temp = priceDf[[col]]
            temp.columns = [keys]
            if output is None:
                output = temp.copy()
            else:
                output = output.join(temp, how='outer')
        output.columns.name = col
        return output

    # ### Long only setup

    # We have set cheat_on_open = True.This means that we calculated the signals on day t's close price,
    # but calculated the number of shares we wanted to buy based on day t+1's open price.
    def next_open(self):
        if not self.position:
            if self.data_predicted > 0:
                # calculate the max number of shares ('all-in')
                size = int(self.broker.getcash() / self.datas[0].open)
                # buy order
                self.log(
                    f'BUY CREATED --- Size: {size}, Cash: {self.broker.getcash():.2f}, Open: {self.data_open[0]}, Close: {self.data_close[0]}')
                self.buy(size=size)
        else:
            if self.data_predicted < 0:
                # sell order
                self.log(f'SELL CREATED --- Size: {self.position.size}')
                self.sell(size=self.position.size)




