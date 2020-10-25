#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Denario the crypto trading application.
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
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
Denario the crypto trading application.
"""
import argparse
import os
import sys
import warnings
import pyqtgraph as pg
from PyQt5 import QtCore, QtGui, uic
from PyQt5.QtCore import QFile, QTextStream, pyqtSlot, QSignalMapper
from PyQt5.QtWidgets import QApplication, QMainWindow, QAction
from PyQt5.uic import loadUi
import qdarkstyle

from denariotrader import DenarioTrader
from about import AboutDlg
from exchangeedit import ExchangeEditDlg
from config import Config

class Denario(QMainWindow):
    """Denario application, main window."""
    def __init__(self, config, parent=None):
        # Initialize UI
        super().__init__(parent)
        loadUi(os.path.join(os.path.abspath(os.path.dirname(__file__)), "denario.ui"), self)

        self.__trader = DenarioTrader.GetInstance()
        self.wgtSelectSymbol.symbolSelected.connect(self.wgtBar.OnShowSymbol)
        self.wgtBar.symbolChanged.connect(self.wgtChart.UpdateSymbol)
        print("showing")
        self.showMaximized()
        self.show()

        for action in self.menuExchanges.actions():
            print(action)
            if action.text() == "":
                self.__exchangeSeperator = action
                break
        else:
            raise Exception("exchange seperator not found")

        self.exchangeMapper = QSignalMapper(self)
        self.exchangeMapper.mapped[str].connect(self.OnSelectExchange)
        self.MenuAddAllExchanges()

    def MenuAddAllExchanges(self):
        # first clear out all old actions
        for action in self.menuExchanges.actions():
            if action == self.__exchangeSeperator:
                break
            else:
                self.menuExchanges.removeAction(action)

        # now create the new ones
        config = Config()
        for exchange in config['exchanges']:
            self.AddExchangeMenuAction(exchange['id'])

    def AddExchangeMenuAction(self, exchId):
        """Add action items to the Exchange menu for the exchange"""
        name = self.__trader.exchanges[exchId]['name']
        action = QAction(name, self)
        action.setCheckable(True)
        if exchId == Config()['denario']['activeExchange']:
            action.setChecked(True)
            self.setWindowTitle(f"Denario - {name}")

        action.triggered.connect(self.exchangeMapper.map)
        self.exchangeMapper.setMapping(action, name)
        self.menuExchanges.insertAction(self.__exchangeSeperator, action)

    @pyqtSlot()
    def OnAboutClicked(self):
        """Launch the about dialog."""
        dlg = AboutDlg()
        dlg.exec()

    @pyqtSlot()
    def OnAbout(self):
        """Launch the about dialog."""
        dlg = AboutDlg()
        dlg.exec()

    @pyqtSlot()
    def OnExchangeEdit(self):
        """Launch the exchange edit dialog."""
        dlg = ExchangeEditDlg(self)
        dlg.exec()
        self.MenuAddAllExchanges()

    @pyqtSlot(str)
    def OnSelectExchange(self, name):
        for action in self.menuExchanges.actions():
            if action == self.__exchangeSeperator:
                break
            elif action.isChecked() and action.text() != name:
                action.setChecked(False)

        self.setWindowTitle(f"Denario - {name}")
        # find the matching exchange idea
        for exchange in self.__trader.exchanges.values():
            if exchange['name'] == name:
                Config()['denario']['activeExchange'] = exchange['id']
                self.__trader.ReloadExchange()
                break
        else:
            raise Exception(f"Exchange id for '{name}' not found")


def Main():
    config = Config()

    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_X11InitThreads)
    app = QApplication(sys.argv)
    app.setWindowIcon(QtGui.QIcon('logo.svg'))
    app.setApplicationName("Denario")

    # setting theme
    app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt5'))

    pg.setConfigOption('background', config['pallet']['background'])
    pg.setConfigOption('foreground', config['pallet']['foreground'])
    # Enable antialiasing for prettier plots
    pg.setConfigOptions(antialias=True)
    #pg.setConfigOptions(useOpenGL=True) # borders don't match candles in openGL....

    DenarioTrader.StartUp(config)
    try:
        denario = Denario(config)

        # Start Qt event loop unless running in interactive mode or using pyside.
        if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
            app.exec_()
    finally:
        DenarioTrader.Shutdown()
        del app


if __name__ == '__main__':
    Main()
