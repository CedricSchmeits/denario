#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# This module implements the about box.
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

from PyQt5 import QtCore, QtGui, uic
from PyQt5.QtWidgets import QDialog
from PyQt5.QtCore import Qt
from PyQt5.uic import loadUi

from config import __version__

class AboutDlg(QDialog):
    """About dialog."""
    def __init__(self, parent=None):
        super().__init__(parent)
        # Load the about dialog
        loadUi(os.path.join(os.path.abspath(os.path.dirname(__file__)), "about.ui"), self)

        self.lblVersion.setText(f"v{__version__}")

    def keyPressEvent(self, evt):
        if evt.key() == Qt.Key_Escape:
            self.close()
