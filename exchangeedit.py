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

import os
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QDialog

from config import Config
from denariotrader import DenarioTrader

class ExchangeEditDlg(QDialog):
    """Edit dialog for used exchanges"""
    def __init__(self, parent=None):
        # Initialize UI
        super().__init__(parent)

        loadUi(os.path.join(os.path.abspath(os.path.dirname(__file__)), "exchangeedit.ui"), self)

        self.__trader = DenarioTrader.GetInstance()
        self.__exchanges = dict()
        for exchId, exchange in self.__trader.exchanges.items():
            self.__exchanges[exchange['name']] = dict(id=exchange['id'], used=False)

        self.__selectedExchange = None
        self.__config = Config()
        for exchange in self.__config['exchanges']:
            exchId = exchange['id']
            name = self.__trader.exchanges[exchId]['name']
            self.listExchanges.addItem(name)
            self.__exchanges[name]['used'] = True
            if self.__selectedExchange is None:
                item = self.listExchanges.item(0)
                self.listExchanges.setCurrentItem(item)
                self.OnExchangeSelected(item)

    def OnClose(self):
        Config.Save()
        self.done(QDialog.Accepted)

    def OnExchangeSelected(self, item):
        name = item.text()
        exchId = self.__exchanges[name]['id']
        for exchange in self.__config['exchanges']:
            if exchange['id'] == exchId:
                self.__selectedExchange = (name, exchange)
                break
        else:
            exchange = dict(id=exchId, key="", secret="")
            self.__config['exchanges'].append(exchange)
            self.__selectedExchange = (name, exchange)

        self.cmbName.clear()
        self.cmbName.addItem(name)
        self.__exchanges[name]['used'] = True

        for exchName, otherExchange in self.__exchanges.items():
            if not otherExchange['used']:
                self.cmbName.addItem(exchName)
        self.editKey.setText(exchange['key'])
        self.editSecret.setText(exchange['secret'])
        self.btnDelete.setEnabled(True)

    def OnNameChanged(self, name):
        if self.__selectedExchange is not None:
            self.__exchanges[self.__selectedExchange[0]]['used'] = False
            if name:
                self.__exchanges[name]['used'] = True
                exchId = self.__exchanges[name]['id']
                for exchange in self.__config['exchanges']:
                    if exchange['id'] == exchId:
                        self.__selectedExchange = (name, exchange)
                        break
                self.listExchanges.currentItem().setText(name)

    def OnKeyChanged(self):
        if self.__selectedExchange is not None:
            self.__selectedExchange[1]['key'] = self.editKey.text()

    def OnSecretChanged(self):
        if self.__selectedExchange is not None:
            self.__selectedExchange[1]['secret'] = self.editSecret.text()

    def OnDelete(self):
        if self.__selectedExchange is not None:
            self.editKey.setText("")
            self.editSecret.setText("")
            self.cmbName.clear()

            name = self.__selectedExchange[0]
            self.__exchanges[name]['used'] = False
            exchId = self.__exchanges[name]['id']
            self.btnDelete.setEnabled(False)
            self.__config['exchanges'].remove(self.__selectedExchange[1])
            self.__selectedExchange = None
            row = self.listExchanges.row(self.listExchanges.currentItem())
            self.listExchanges.takeItem(row)

    def OnNew(self):
        # find first unused exchange
        for name, exchange in self.__exchanges.items():
            if not exchange['used']:
                self.listExchanges.addItem(name)
                exchange['used'] = True
                item = self.listExchanges.item(self.listExchanges.count() - 1)
                self.listExchanges.setCurrentItem(item)
                self.OnExchangeSelected(item)
                break
