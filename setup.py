#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@file setup.py
@author Sam Freeside <snovvcrash@protonmail.com>
@date 2018-03

@brief Standalone executable builder (cx_Freeze)

@license
Copyright (C) 2018 Sam Freeside

This file is part of usbrip.

usbrip is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

usbrip is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with usbrip.  If not, see <http://www.gnu.org/licenses/>.
@endlicense
"""

import sys
from cx_Freeze import setup, Executable

build_exe_options = { "packages": ["os"],
                      "excludes": ["tkinter"] }

setup(name = "usbrip",
      version = "0.1",
      description = "A Linux usb-forensic tool",
      options = {"build_exe": build_exe_options},
      executables = [Executable("usbrip.py", base=None)] )
