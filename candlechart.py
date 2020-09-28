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
from datetime import datetime, timedelta
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QColor, QPainter, QPicture
from PyQt5.QtCore import Qt, QDateTime, QPointF, QRectF
import pyqtgraph as pg

from denariotrader import DenarioTrader
from timeaxis import DateTimeAxisItem
import pickle


class CandlestickItem(pg.GraphicsObject):
    def __init__(self, data):
        pg.GraphicsObject.__init__(self)
        self.data = data  ## data must have fields: time, open, close, min, max
        self.generatePicture()

    def generatePicture(self):
        ## pre-computing a QPicture object allows paint() to run much more quickly,
        ## rather than re-drawing the shapes every time.
        self.picture = QPicture()
        painter = QPainter(self.picture)
        painter.setPen(pg.mkPen('w'))
        width = (self.data[1][0] - self.data[0][0]) / 3000.
        for (timestamp, open, high, low, close, _volume) in self.data:
            timestamp /= 1000
            #print(t, open, high, low, close)
            painter.drawLine(QPointF(timestamp, low), QPointF(timestamp, high))
            if open > close:
                painter.setBrush(pg.mkBrush('r'))
            else:
                painter.setBrush(pg.mkBrush('g'))
            painter.drawRect(QRectF(timestamp - width, open, width * 2, close - open))
        painter.end()

    def paint(self, p, *args):
        p.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        ## boundingRect _must_ indicate the entire area that will be drawn on
        ## or else we will get artifacts and possibly crashing.
        ## (in this case, QPicture does all the work of computing the bouning rect for us)
        return QRectF(self.picture.boundingRect())


class CandleChart(QWidget):
    limit = 500

    def __init__(self, parent=None):
        # Initialize UI
        super().__init__(parent)

        loadUi(os.path.join(os.path.abspath(os.path.dirname(__file__)), "candlechart.ui"), self)


        self.__exchange = DenarioTrader.GetInstance().exchange

        self.__timeAxis = DateTimeAxisItem(self.timeFrame[1], orientation='bottom')
        self.__legends = self.gpvChart.addLegend(offset=(600, 10))
        self.__plotItem = self.gpvChart.getPlotItem()
        self.__plotItem.setLogMode(x=False, y=False)
        self.__plotItem.setAutoVisible(x=None, y=True)
        self.__plotItem.setMouseEnabled(y=False)
        self.__plotItem.setAxisItems({'bottom': self.__timeAxis})
        self.__plotItem.showGrid(x=True, y=True)
        #self.gpvChart.setState({'autoVisibleOnly': [False, True]})

        self.UpdateSymbol()


    def UpdateSymbol(self, symbol : str = "BTC/USDT") -> None:
        timeFrame, _dTime = self.timeFrame
        if os.path.exists("ohlcv.bin"):
            with open("ohlcv.bin", 'rb') as ohlcvFile:
                ohlcv = pickle.load(ohlcvFile)
        else:
            ohlcv = self.__exchange.fetchOHLCV(symbol, timeFrame, limit=self.limit)
            with open("ohlcv.bin", 'wb') as ohlcvFile:
                #print(ohlcv)
                pickle.dump(ohlcv, ohlcvFile)

        item = CandlestickItem(ohlcv)
        self.gpvChart.addItem(item)


    def mouseReleaseEvent(self, event):
        print(event)
        return
        p1 = event.pos()
        p2 = self.mapToScene(p1)
        p3 = self.chart().mapFromScene(p2)
        p4 = self.chart().mapToValue(p3)
        if self.chart():
            for serie in self.chart().series():
                QApplication.postEvent(serie, ReleasePosEvent(p4))
        QChartView.mouseReleaseEvent(self, event)



    #def wheelEvent(self, event):
    #    print(event.angleDelta())
    #    print(dir(self.__plotItem))
    #    print(self.__plotItem.viewRange())
        #if event.angleDelta().y() > 0:
        #    self.plotItem.zoomIn()
        #else:
        #    self.plotItem.zoomOut()
        #self.plotItem.setXRange()

    #    event.accept()

    @property
    def timeFrame(self):
        timeFrame = self.cmbTimeFrame.currentText()
        number, frame = timeFrame.split()
        if "minute" in frame:
            frame = "m"
            dTime = timedelta(minutes=int(number))
        elif "hour" in frame:
            frame = "h"
            dTime = timedelta(hours=int(number))
        elif "day" in frame:
            frame = "d"
            dTime = timedelta(days=int(number))
        elif "week" in frame:
            frame = "w"
            dTime = timedelta(days=7 * int(number))
        elif "month" in frame:
            frame = "M"
            dTime = timedelta(days=31 * int(number))
        else:
            raise Exception(f"Unknown timeframe: {timeFrame}")
        return (f"{number}{frame}", dTime)
