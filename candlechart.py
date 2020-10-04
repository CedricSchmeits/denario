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
from PyQt5.QtCore import Qt, QDateTime, QPointF, QRectF, pyqtSlot
import pyqtgraph as pg

from denariotrader import DenarioTrader
from timeaxis import DateTimeAxisItem
import pickle
from config import Config

class TimeFormater:
    @staticmethod
    def format(value):
        valueTime = datetime.fromtimestamp(value)
        return valueTime.strftime("%x %X")


class CandlestickItem(pg.GraphicsObject):
    def __init__(self, data):
        pg.GraphicsObject.__init__(self)
        ## data must have fields: time, open, close, min, max
        self.data = self.__ProcessData(data)
        pallet = Config()['pallet']
        self.__redPen = pg.mkPen(pallet['negative'])
        self.__redBrush = pg.mkBrush(pallet['negative'])
        self.__greenPen = pg.mkPen(pallet['positive'])
        self.__greenBrush = pg.mkBrush(pallet['positive'])

        self.generatePicture()

    def __ProcessData(self, data):
        result = dict()
        for (timestamp, open, high, low, close, volume) in data:
            result[timestamp / 1000] = (open, high, low, close, volume)
        return result

    def generatePicture(self):
        ## pre-computing a QPicture object allows paint() to run much more quickly,
        ## rather than re-drawing the shapes every time.
        print("generatePicture")
        self.picture = QPicture()
        painter = QPainter(self.picture)
        iterator = iter(self.data)
        width = (next(iterator) - next(iterator)) / -3.
        for timestamp, (open, high, low, close, _volume) in self.data.items():
            #print(t, open, high, low, close)
            if open > close:
                painter.setBrush(self.__redBrush)
                painter.setPen(self.__redPen)
            else:
                painter.setBrush(self.__greenBrush)
                painter.setPen(self.__greenPen)
            painter.drawLine(QPointF(timestamp, low), QPointF(timestamp, high))
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

        self.ChangedTimeframe("1 hour")

        self.__exchange = DenarioTrader.GetInstance().exchange

        self.__timeAxis = DateTimeAxisItem(self.timeDelta, orientation='bottom')
        self.__legends = self.gpvChart.addLegend(offset=(600, 10))
        self.__plotItem = self.gpvChart.getPlotItem()
        self.__plotItem.setLogMode(x=False, y=False)
        self.__plotItem.setAutoVisible(x=None, y=True)
        self.__plotItem.setMouseEnabled(y=False)
        self.__plotItem.setAxisItems({'bottom': self.__timeAxis})
        self.__plotItem.showAxis("right", True)
        self.__plotItem.showAxis("left", False)
        self.__plotItem.showGrid(x=True, y=True)
        pallet = Config()['pallet']
        pen = pg.mkPen(pallet['crossBackground'], style=Qt.DashLine)
        labelOpts={'position': 0.01,
                   'color': pallet['crossForground'],
                   'fill': pg.mkBrush(pallet['crossBackground'])}
        self.__vCrossLine = pg.InfiniteLine(angle=90, movable=False, pen=pen, label=TimeFormater, labelOpts=labelOpts)
        labelOpts['position'] = 0.97
        self.__hCrossLine = pg.InfiniteLine(angle=0, movable=False, pen=pen, label="{value}", labelOpts=labelOpts)
        self.gpvChart.addItem(self.__vCrossLine, ignoreBounds=True)
        self.gpvChart.addItem(self.__hCrossLine, ignoreBounds=True)

        self.__proxy = pg.SignalProxy(self.gpvChart.scene().sigMouseMoved, rateLimit=15, slot=self.Crosshair)
        self.gpvChart.setCursor(Qt.CrossCursor)

        #self.gpvChart.setState({'autoVisibleOnly': [False, True]})

        self.__currentCandles = None

        self.UpdateSymbol()

    @pyqtSlot(str)
    def UpdateSymbol(self, symbol : str = "BTC/USDT") -> None:
        ohlcv = self.__exchange.fetchOHLCV(symbol, self.timeFrame, limit=self.limit)
        precision = self.__exchange.markets[symbol]['precision']['price']
        self.__hCrossLine.label.setFormat(f"{{value:.{precision}f}}")

        if self.__currentCandles is not None:
            self.gpvChart.removeItem(self.__currentCandles)
            self.__currentCandles = None

        self.__currentCandles = CandlestickItem(ohlcv)
        self.gpvChart.addItem(self.__currentCandles)


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

    def Crosshair(self, evt):
        mousepoint = self.__plotItem.vb.mapSceneToView(evt[0])

        crossTime = mousepoint.x()
        # pick the closest value in the current timeDelta
        crossTime = min(self.__currentCandles.data.keys(), key=lambda x: abs(x - crossTime))

        self.__vCrossLine.setPos(crossTime)
        self.__hCrossLine.setPos(mousepoint.y())

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

    def ChangedTimeframe(self, timeframe: str):
        number, frame = timeframe.split()
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

        self.__timeFrame = f"{number}{frame}"
        self.__deltaTime = dTime

    @property
    def timeFrame(self):
        return self.__timeFrame

    @property
    def timeDelta(self):
        return self.__deltaTime
