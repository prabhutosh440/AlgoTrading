class Factor():
    def init(self):
        pass

    def reversalFactor(self,priceReturn, lookback):
        aggRet = priceReturn.rolling(lookback.n, min_periods = lookback.n).sum()
        revRet = aggRet * -1
        return revRet
