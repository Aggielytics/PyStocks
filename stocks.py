import datetime

import pandas_datareader.data as web


class Stocks:
    def __init__(self) -> None:
        self.start = datetime.datetime(2020, 1, 1)
        self.end = datetime.datetime(2020, 12, 3)

        self.favs_stocks = {
            "IBM": "IBM", "Apple": "AAPL", "Microsoft": "MSFT", "Moderna": "MRNA",
            "Pfizer": "PFE", "Novavax": "NVAX", "AstraZeneca": "AZN", "Schlumberger": "SLB",
            "EOG": "EOG", "Google": "GOOG", "Tesla": "TSLA", "Motorola": "MSI", "AT&T": "T",
            "Ford": "F", "Uber": "UBER", "Genral Electric": "GE", "Qualcomm": "QCOM",
            "Exxon Mobil": "XOM", "Amyris": "AMRS", "Toyota": "TM"}

    def getStockNames(self):
        return self.favs_stocks.keys()

    def getStockSymbol(self, stockName):
        return self.favs_stocks.get(stockName)

    def get_Stocks_html_options(self):
        dict_list = []
        for i in self.favs_stocks.keys():
            dict_list.append({'label': i, 'value': self.favs_stocks.get(i)})

        return dict_list

    def getWebStocks(self):
        df = web.DataReader(list(self.favs_stocks.values()), "stooq", start=self.start, end=self.end)
        df.to_csv("")
