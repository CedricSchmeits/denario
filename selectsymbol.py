# -*- coding: utf-8 -*-
#
# This module implements the candle chart.
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
Module for selecting symbols
"""
import os

from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex, pyqtSlot, pyqtSignal
from PyQt5.QtGui import QColor

from denariotrader import DenarioTrader, Exchange
from config import Config


class TreeSymbolModel(QAbstractTableModel):
    symbolsChanged = pyqtSignal()
    def __init__(self, exchange):
        super().__init__()

        self.__rowCount = None
        self.__columnCount = 2
        self.__exchange = exchange
        self.__trader = DenarioTrader.GetInstance()
        self.__trader.exchangeChanged.connect(self.OnChangedExchange)
        self.__search = ""
        self.__sorting = (0, Qt.AscendingOrder)

        config = Config()['pallet']
        self.__oddColor = config['rowOdd']
        self.__evenColor = config['rowEven']
        self.OnSearchChanged("")

    @pyqtSlot(str)
    def OnSearchChanged(self, search: str):
        self.__search = search.upper()
        self.tickers = list()
        for symbol, ticker in self.__trader.tickers.items():
            if self.__search in symbol and self.__exchange.markets[symbol]['active']:
                self.tickers.append(ticker)

        if self.__sorting[0] == 0:
            func = lambda ticker: ticker['symbol']
        elif self.__sorting[0] == 1:
            func = lambda ticker: ticker['close']

        self.tickers = sorted(self.tickers, key=func, reverse=self.__sorting[1] != Qt.AscendingOrder)
        self.__rowCount = len(self.tickers)
        self.symbolsChanged.emit()

    @pyqtSlot(Exchange)
    def OnChangedExchange(self, exchange):
        self.__exchange = exchange
        self.OnSearchChanged(self.__search)

    def rowCount(self, parent: QModelIndex=QModelIndex()):
        return self.__rowCount

    def columnCount(self, parent: QModelIndex=QModelIndex()):
        return self.__columnCount

    def sort(self, column, order=Qt.AscendingOrder):
        self.__sorting = (column, order)
        self.OnSearchChanged(self.__search)


    def headerData(self,
                   section: int,
                   orientation: Qt.Orientation,
                   role: Qt.ItemDataRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            return ("Market", "Price")[section]
        else:
            return "{}".format(section)

    def data(self, index: QModelIndex, role: Qt.ItemDataRole=Qt.DisplayRole):
        column = index.column()
        row = index.row()

        if role == Qt.DisplayRole:
            ticker = self.tickers[row]
            symbol = ticker['symbol']
            if column == 0:
                return symbol
            elif column == 1:
                close = ticker['close']
                precision = self.__exchange.markets[symbol]['precision']['price']
                return f"{close:.{precision}f}"
        elif role == Qt.BackgroundRole:
            if index.row() & 1:
                return self.__oddColor
            else:
                return self.__evenColor
        elif role == Qt.TextAlignmentRole:
            if column == 0:
                return Qt.AlignLeft
            else:
                return Qt.AlignRight

        return None

class SelectSymbol(QWidget):
    symbolSelected = pyqtSignal(str)
    def __init__(self, parent=None):
        super().__init__(parent)

        loadUi(os.path.join(os.path.abspath(os.path.dirname(__file__)), "selectsymbol.ui"), self)

        self.__symbolModel = TreeSymbolModel(DenarioTrader.GetInstance().exchange)
        self.tableSymbols.setModel(self.__symbolModel)
        self.editSearch.textChanged.connect(self.__symbolModel.OnSearchChanged)
        self.__symbolModel.symbolsChanged.connect(self.tableSymbols.update)
        self.tableSymbols.setSortingEnabled(True);
        self.tableSymbols.sortByColumn(0, Qt.AscendingOrder)

    def OnShowAll(self):
        print("Show All")
        self.btnAll.setEnabled(False)
        self.btnFavorites.setEnabled(True)

    def OnShowFavorites(self):
        print("Show favorites")
        self.btnAll.setEnabled(True)
        self.btnFavorites.setEnabled(False)

    @pyqtSlot(QModelIndex)
    def OnSymbolSelected(self, index: QModelIndex):
        symbol = self.__symbolModel.tickers[index.row()]['symbol']
        self.symbolSelected.emit(symbol)
