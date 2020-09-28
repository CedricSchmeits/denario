#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Provide date an time based upon the timestamps
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
Provide date an time based upon the timestamps
"""

__all__ = ["DateTimeAxisItem"]

from time import mktime
from datetime import datetime, timedelta
from numpy import ceil

from pyqtgraph import AxisItem



class DateTimeAxisItem(AxisItem):
    # Max width in pixels reserved for each label in axis
    labelWidth = 80

    def __init__(self, timeFrame, *args, **kwargs):
        AxisItem.__init__(self, *args, **kwargs)
        self.__timeFrame = timeFrame

    @property
    def timeFrame(self):
        return self.__timeFrame
    @timeFrame.setter
    def timeFrame(self, value):
        self.__timeFrame = value

    def tickValues(self, minVal, maxVal, size):
        """
        Rounding around date/time values instead of decimal numbers
        """
        maxSteps = int(size / self.labelWidth)

        startTime = datetime.fromtimestamp(minVal)
        endTime = datetime.fromtimestamp(maxVal)

        dT = endTime - startTime
        dx = maxVal - minVal
        ticks = []

        dT /= maxSteps
        if dT < self.timeFrame:
            # lets not set a smaller timeframe than the candles
            dT = self.timeFrame

        if dT.days > 0:
            startTime = startTime.replace(hour=0, minute=0,
                                          second=0, microsecond=0)
            dT = timedelta(days=dT.days)
            for days in (1, 3, 10, 31, 120, 180, 365):
                if dT.days < days:
                    dT = timedelta(days=days)
                    dDays = timedelta(days=days - (startTime.day % days))
                    startTime = startTime + dDays
                    break
        else:
            hour = dT.seconds // 3600
            if hour > 0:
                startTime = startTime.replace(minute=0,
                                              second=0, microsecond=0)
                for hours in (1, 3, 12, 24):
                    if hour <= hours:
                        dT = timedelta(seconds=hours * 3600)
                        dHours = timedelta(hours=hours - (startTime.hour % hours))
                        startTime = startTime + dHours
                        break
            else:
                startTime = startTime.replace(second=0, microsecond=0)
                minute = dT.seconds // 60
                for minutes in (5, 15, 30, 60):
                    if minute < minutes:
                        dT = timedelta(seconds=minutes * 60)
                        dMinutes = timedelta(minutes=minutes - (startTime.minute % minutes))
                        startTime = startTime + dMinutes
                        break

        while startTime < endTime:
            # make sure that we are on day 1 (even if always sum 31 days)
            ticks.append(mktime(startTime.timetuple()))
            startTime += dT

        length = len(ticks)
        if length > maxSteps:
            majticks = ticks[::int(ceil(float(length) / maxSteps))]

        return [(dT.total_seconds(), ticks)]

    def tickStrings(self, values, scale, spacing):
        """Reimplemented from PlotItem to adjust to the range"""
        ret = []

        for tick in values:
            capital = False
            tickTime = datetime.fromtimestamp(tick)
            if tickTime.second != 0:
                fmt = "%H:%M:%S"
            elif tickTime.minute != 0 or tickTime.hour != 0:
                fmt = "%H:%M"
            elif tickTime.day != 1:
                fmt = "%d"
            elif tickTime.month != 1:
                fmt = "%b"
            else:
                fmt = "%Y"
            ret.append(tickTime.strftime(fmt))

        return ret
