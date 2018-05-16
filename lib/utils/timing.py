#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
@file timing.py
@author Sam Freeside <snovvcrash@protonmail.com>
@date 2018-04

@brief Program run time meter.

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

import atexit
import time
import datetime

START = time.time()


def tick(msg, fmt='%H:%M:%S', taken=None):
	#fmt = '%Y-%m-%d %H:%M:%S'
	now = time.strftime(fmt, time.localtime())
	print('%s %s' % (msg, now))
	if taken:
		taken = datetime.timedelta(seconds=taken)
		print('[*] Time taken: %s' % taken)


def final():
	end = time.time()
	taken = end - START
	tick('[*] Shutted down at', taken=taken)


def begin(*, quiet):
	if not quiet:
		atexit.register(final)
		tick('[*] Started at')
