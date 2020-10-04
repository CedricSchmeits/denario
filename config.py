#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# This module implements the configuration.
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
Configuration module of the denario package
"""

__all__ = ["Config"]

import json
import os
import argparse
import sys
from PyQt5.QtGui import QColor

def _ShowLicense():
    print("""    Denario  Copyright (C) 2020  Cedric Schmeits <cedric@aerofx.nl>

This program comes with ABSOLUTELY NO WARRANTY;
This is free software, and you are welcome to redistribute
it under certain conditions;
""")


class Config:
    """Basic configuration holder"""
    __instance = None

    def __new__(cls):
        if Config.__instance is None:
            parser = argparse.ArgumentParser(description="Denario the crypto trading application.")
            parser.add_argument("-e", "--exchange", default=None, help="Exchange to trade on.")
            parser.add_argument("-s", "--sandbox", action="store_true",
                                default=False, help="Run in sandbox mode")
            parser.add_argument("-c", "--config",
                                help="Set the configuration file")

            subParser = parser.add_subparsers(help='Sub command help')
            license = subParser.add_parser("license", help="Show the license.")
            license.set_defaults(func=_ShowLicense)

            args = parser.parse_args()

            if hasattr(args, 'func'):
                args.func()
                sys.exit()
            else:
                if args.config:
                    configFile = args.config
                else:
                    sandbox = ".sandbox" if args.sandbox else ""
                    configFile = os.path.expanduser(f"~/.local/share/denario/config{sandbox}.json")

                if os.path.exists(configFile):
                    print(f"Using configuration file: {configFile}")
                    with open(configFile, 'r') as fHandle:
                        Config.__instance = json.load(fHandle)
                        if args.exchange:
                            Config.__instance['exchange']['name'] = args.exchange
                        Config.FillPalletDefaults()
                else:
                    raise Exception("file {} does not exists".format(configFile))
        return Config.__instance

    @classmethod
    def FillPalletDefaults(cls):
        if 'pallet' not in Config.__instance:
            Config.__instance['pallet'] = dict()

        defaultPallet = {'background':              QColor(29, 32, 32),
                         'foreground':              QColor(240, 240, 240),
                         'positive':                QColor(38, 166, 154),   # green
                         'negative':                QColor(244, 67, 36),    # red
                         'rowOdd':                  QColor(24, 0, 0),       # dark red
                         'rowEven':                 QColor(0, 0, 24),       # dark blue
                         'crossForground':          QColor(38, 38, 38),
                         'crossBackground':         QColor(182, 182, 182)
                        }

        # convert pallet values to colors
        for name, color in Config.__instance['pallet'].items():
            if isinstance(color, (list, tupple)):
                Config.__instance['pallet'][name] = QColor(*color)
            else:
                Config.__instance['pallet'][name] = QColor(color)

            if name in defaultPallet:
                defaultPallet.pop(name)

        Config.__instance['pallet'].update(defaultPallet)


    def __getitem__(self, key):
        pass
