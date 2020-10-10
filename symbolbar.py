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
Module to show the selected symbols in tabbed bar
"""
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QTabBar, QWidget, QVBoxLayout, QHBoxLayout, QLabel

from denariotrader import DenarioTrader
from config import Config

class SymbolBar(QTabBar):
    symbolChanged = pyqtSignal(str)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTabsClosable(True)
        self.setMovable(True)
        self.setShape(QTabBar.RoundedWest)
        self.tabCloseRequested.connect(self.OnCloseTab)
        self.currentChanged.connect(self.__OnCurrentChanged)
        self.__symbolWidgets = dict()

        self.AddSymbol("BTC/USDT")

    def tabSizeHint(self, index):
        s = QTabBar.tabSizeHint(self, index)
        s.setHeight(s.height() - 10)
        return s

    def paintEvent(self, event):
        painter = QtWidgets.QStylePainter(self)
        opt = QtWidgets.QStyleOptionTab()

        for i in range(self.count()):
            self.initStyleOption(opt, i)
            painter.drawControl(QtWidgets.QStyle.CE_TabBarTabShape, opt)
            painter.save()

            s = opt.rect.size()
            s.transpose()
            r = QtCore.QRect(QtCore.QPoint(), s)
            r.moveCenter(opt.rect.center())
            opt.rect = r

            c = self.tabRect(i).center()

            painter.translate(c)
            painter.rotate(90)
            painter.translate(-c)
            painter.drawControl(QtWidgets.QStyle.CE_TabBarTabLabel, opt)
            painter.restore()

    @pyqtSlot(int)
    def OnCloseTab (self, currentIndex: int):
        print(f"OnCloseTab: {currentIndex}")
        widget = self.tabButton(currentIndex, QTabBar.LeftSide)
        #currentQWidget = self.widget(currentIndex)
        #currentQWidget.deleteLater()
        self.removeTab(currentIndex)

    def AddSymbol(self, symbol: str) -> int:
        print(f"Adding Symbol {symbol}")

        symbolWidget = TabSymbolWidget(symbol)

        index = self.addTab(None)
        self.setTabButton(index, QTabBar.LeftSide, symbolWidget)
        return index

    @pyqtSlot(str)
    def OnShowSymbol(self, symbol: str):
        for index in range(self.count()):
            if self.tabButton(index, QTabBar.LeftSide).symbol == symbol:
                # found the index enable it outside the loop.
                break
        else:
            index = self.AddSymbol(symbol)

        self.setCurrentIndex(index)

    @pyqtSlot(int)
    def __OnCurrentChanged(self, currentIndex: int):
        symbolWidget = self.tabButton(currentIndex, QTabBar.LeftSide)
        if symbolWidget is not None:
            self.symbolChanged.emit(symbolWidget.symbol)

class TabSymbolWidget(QWidget):
    def __init__(self, symbol, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.__symbol = symbol

        self.lblName = QtWidgets.QLabel(symbol)
        self.lblName.setMinimumWidth(160)
        self.lblName.setAlignment(Qt.AlignCenter)

        self.lblPrice = QtWidgets.QLabel("0.0")
        self.lblPrice.setMinimumWidth(100)
        self.lblPrice.setAlignment(Qt.AlignLeft)
        self.lblPercentage = QtWidgets.QLabel("0.0%")
        self.lblPercentage.setMinimumWidth(60)
        self.lblPercentage.setAlignment(Qt.AlignRight)

        # Create layout
        self.vLayout = QVBoxLayout()
        self.vLayout.setSpacing(0)
        self.vLayout.setContentsMargins(0, 0, 0, 0)
        self.hLayout = QHBoxLayout()
        self.hLayout.setSpacing(0)
        self.hLayout.setContentsMargins(0, 0, 0, 0)

        # Add button's to layout
        self.vLayout.addWidget(self.lblName)
        self.hLayout.addWidget(self.lblPrice)
        self.hLayout.addWidget(self.lblPercentage)
        self.vLayout.addLayout(self.hLayout)

        self.setLayout(self.vLayout)

        self.OnUpdateStats()

    @pyqtSlot()
    def OnUpdateStats(self):
        trader = DenarioTrader.GetInstance()
        ticker = trader.tickers[self.__symbol]
        self.lblPrice.setText(f"{ticker['last']}")
        self.lblPercentage.setText(f"{ticker['percentage']:.1f}%")
        color = Config()['pallet']['positive'] if ticker['change'] >= 0 else Config()['pallet']['negative']
        style = "QLabel {{ color : {}; }}".format(color.name())
        self.lblPrice.setStyleSheet(style);
        self.lblPercentage.setStyleSheet(style);

    @property
    def symbol(self):
        return self.__symbol
