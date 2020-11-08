# -*- coding: utf-8 -*-
#
# Interface module to the exchange.
#
# Copyright (C) 2020  Cedric Schmeits <cedric@aerofx.nl>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Interface to the exchange
"""

__all__ = ["DenarioTrader"]

from PyQt5.QtCore import QObject, QTimer, pyqtSignal

from typing import Any, Dict
from datetime import datetime, timedelta
import ccxt
from ccxt import Exchange
from pandas import DataFrame, DatetimeIndex, to_datetime


from config import Config


class DenarioTrader(QObject):
    """Trader class"""
    exchangeChanged = pyqtSignal(Exchange)

    DEFAULT_DATAFRAME_COLUMNS = ['date', 'open', 'high', 'low', 'close', 'volume']
    __instance = None

    @classmethod
    def GetInstance(cls):
        """ Static access method. """
        if cls.__instance == None:
            raise Exception("Class should be started with StartUp method")
        return cls.__instance

    def __init__(self, options):
        """ Virtually private constructor. """
        if DenarioTrader.__instance != None:
            raise Exception("This class is a singleton!")
        else:
            super().__init__()
            DenarioTrader.__instance = self

        self.__exchanges = dict()
        self.__LoadExchanges()
        self.ReloadExchange()

        # creating a timer object
        self.timer = QTimer(self)
        self.timer.start(301)

    def __LoadExchanges(self):
        for name in ccxt.exchanges:
            try:
                self.__exchanges[name] = getattr(ccxt, name)().describe()
            except Exception as err:
                print(f"exchange {name} failed with: {err}")

    def __OnTimer(self):
        if self.__exchange is not None:
            self.__exchange.load_markets()

    def ReloadExchange(self):
        # configure api key and secret for binance.com
        config = Config()
        activeExchange = config['denario']['activeExchange']
        if activeExchange:
            for exchangeConfig in config['exchanges']:
                if exchangeConfig['id'] == activeExchange:
                    break
            else:
                exchangeConfig = None
        else:
            exchangeConfig = None

        if exchangeConfig is not None:
            exchangeClass = getattr(ccxt, exchangeConfig['id'].lower())
            exchange = exchangeClass({'apiKey': exchangeConfig['key'],
                                      'secret': exchangeConfig['secret'],
                                      'timeout': 30000,
                                      'enableRateLimit': True})
            exchange.load_markets()

            # start a worker process to move the received stream_data from the stream_buffer to a print function
            self.__exchange = exchange
        else:
            self.__exchange = None

        self.UpdateTickers(True)
        self.exchangeChanged.emit(self.exchange)

    def __Shutdown(self):
        """Shutdown method"""
        pass

    @property
    def exchange(self):
        return self.__exchange

    @property
    def exchanges(self):
        return self.__exchanges

    @property
    def tickers(self) -> Dict:
        return self.UpdateTickers()

    def UpdateTickers(self, force=False):
        """Updating of the tickers"""
        if self.__exchange is not None and self.__exchange.has['fetchTickers']:
            # Only update the tickers once every 5 minutes
            if force or (datetime.now() - self.__tickersUpdateTime) > timedelta(minutes=5):
                self.__tickers = self.__exchange.fetchTickers()
                self.__tickersUpdateTime = datetime.fromtimestamp(next(iter(self.__tickers.values()))['timestamp']/1000)
        elif force:
            self.__tickers = dict()

        return self.__tickers

    def GetOhlcv(self, symbol, *args, **kwargs) -> DataFrame:
        """
        :return: DataFrame
        """
        if self.__exchange is not None:
            ohlcv = self.__exchange.fetchOHLCV(symbol, *args, **kwargs)
            df = DataFrame(ohlcv, columns=self.DEFAULT_DATAFRAME_COLUMNS)

            df['date'] = to_datetime(df['date'], unit='ms') #, utc=True, infer_datetime_format=True)

            # Some exchanges return int values for Volume and even for OHLC.
            # Convert them since TA-LIB indicators used in the strategy assume floats
            # and fail with exception...
            df = df.astype(dtype={'open': 'float', 'high': 'float', 'low': 'float', 'close': 'float',
                                  'volume': 'float'})
        else:
            df = DataFrame([], columns=self.DEFAULT_DATAFRAME_COLUMNS)

        return df

    @classmethod
    def SelectExchange(cls, newExchange):
            symbolChanged = pyqtSignal(str)


    @classmethod
    def StartUp(cls, options):
        """Startup method"""
        DenarioTrader(options)

    @classmethod
    def Shutdown(cls):
        """Shutdown the denario trader"""
        cls.__instance.__Shutdown()
        cls.__instance = None
