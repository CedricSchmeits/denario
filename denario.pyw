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
from PyQt5.QtCore import QFile, QTextStream
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.uic import loadUi
import qdarkstyle

from denariotrader import DenarioTrader
from config import Config

class Denario(QMainWindow):
    """Denario application, main window."""

    def __init__(self, config, parent=None):
        # Initialize UI
        super().__init__(parent)
        loadUi(os.path.join(os.path.abspath(os.path.dirname(__file__)), "denario.ui"), self)

        self.wgtSelectSymbol.symbolSelected.connect(self.wgtBar.OnShowSymbol)
        self.wgtBar.symbolChanged.connect(self.wgtChart.UpdateSymbol)
        print("showing")
        self.showMaximized()
        self.show()


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
