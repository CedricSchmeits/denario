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

from PyQt5.QtCore import QObject

from typing import Any, Dict
from datetime import datetime, timedelta
import ccxt

from config import Config


class DenarioTrader(QObject):
    """Trader class"""
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
            DenarioTrader.__instance = self

        # configure api key and secret for binance.com
        exchangeClass = getattr(ccxt, Config()['exchange']['name'])
        exchange = exchangeClass({'apiKey': Config()['exchange']['key'],
                                  'secret': Config()['exchange']['secret'],
                                  'timeout': 30000,
                                  'enableRateLimit': True})
        exchange.load_markets()

        # start a worker process to move the received stream_data from the stream_buffer to a print function
        self.__exchange = exchange
        self.__tickers = dict()
        self.UpdateTickers(True)


    def __Shutdown(self):
        """Shutdown method"""
        pass

    @property
    def exchange(self):
        return self.__exchange

    @property
    def tickers(self) -> Dict:
        return self.UpdateTickers()

    def UpdateTickers(self, force=False):
        """Updating of the tickers"""
        if self.__exchange.has['fetchTickers']:
            # Only update the tickers once every 5 minutes
            if force or (datetime.now() - self.__tickersUpdateTime) > timedelta(minutes=5):
                self.__tickers = self.__exchange.fetchTickers()
                self.__tickersUpdateTime = datetime.fromtimestamp(next(iter(self.__tickers.values()))['timestamp']/1000)
        return self.__tickers

    @classmethod
    def StartUp(cls, options):
        """Startup method"""
        DenarioTrader(options)

    @classmethod
    def Shutdown(cls):
        """Shutdown the denario trader"""
        cls.__instance.__Shutdown()
        cls.__instance = None
