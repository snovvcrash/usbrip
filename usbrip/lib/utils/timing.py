#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""LICENSE

Copyright (C) 2020 Sam Freeside

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
"""

__author__ = 'Sam Freeside (@snovvcrash)'
__email__  = 'snovvcrash@protonmail[.]ch'
__site__   = 'https://github.com/snovvcrash/usbrip'
__brief__  = 'Program runtime meter'

import atexit
import time
import datetime

import usbrip.lib.core.config as cfg

START = time.time()


def tick(msg, fmt='%H:%M:%S', taken=None):
	now = time.strftime(fmt, time.localtime())
	print('%s %s' % (msg, now))
	if taken:
		taken = datetime.timedelta(seconds=taken)
		print('[*] Time taken: %s' % taken)


def final():
	end = time.time()
	taken = end - START
	tick('[*] Shut down at', fmt='%Y-%m-%d %H:%M:%S', taken=taken)


def begin():
	if not cfg.QUIET:
		atexit.register(final)
		tick('[*] Started at', fmt='%Y-%m-%d %H:%M:%S')
