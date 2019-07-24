#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""LICENSE

Copyright (C) 2019 Sam Freeside

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
__brief__  = 'Common items'

import os
import sys
import time
import random
from calendar import month_name
from collections import OrderedDict, Callable

from termcolor import colored, cprint

import usbrip.lib.core.config as cfg
from usbrip import __version__


# ----------------------------------------------------------
# ---------------- Configuration file path -----------------
# ----------------------------------------------------------


CONFIG_FILE = '/var/opt/usbrip/usbrip.ini'


# ----------------------------------------------------------
# ------------------- Unicode constants --------------------
# ----------------------------------------------------------


BULLET    = '\u2022'  # '•', U_BULLET
ABSENCE   = '\u2205'  # '∅', U_EMPTY_SET
SEPARATOR = '\u2212'  # '−', U_MINUS_SIGN


# ----------------------------------------------------------
# ------------------------- Banner -------------------------
# ----------------------------------------------------------


VERSION = __version__
SITE = __site__

VERSION_FORMATTED = '\033[0m\033[1;37m{\033[1;34mv%s\033[1;37m}\033[0m' % VERSION
SITE_FORMATTED = '\033[0m\033[4;37m%s\033[0m' % SITE

BANNER = '''\033[1;33m\
                       
         _     {{4}}    %s\033[1;33m
 _ _ ___| |_ ___[+]___ 
| | |_ -| . |  _[*] . |
|___|___|___|_| [?]  _|
               x[^]_|   %s
                       \
''' % (VERSION_FORMATTED, SITE_FORMATTED)

E = ('E', 'e', '3')
N = ('N', 'n')
S = ('S', 's', '5')
I = ('I', 'i', '1', '!')

E,N,S,I = list(map(lambda x: random.choice(x), (E,N,S,I)))
E,N,S,I = list(map(lambda x: colored(x, 'green', 'on_blue') + '\033[1;33m', (E,N,S,I)))

BANNER = BANNER.replace('+', E, 1)
BANNER = BANNER.replace('*', N, 1)
BANNER = BANNER.replace('?', S, 1)
BANNER = BANNER.replace('^', I, 1)


# ----------------------------------------------------------
# -------------------- Exception class ---------------------
# ----------------------------------------------------------


class USBRipError(Exception):
	def __init__(self, message, *, errors=None):
		super().__init__(message)
		if not errors:
			errors = {}
		self.errors = errors
		self.errors.setdefault('errcode', 0)
		self.errors.setdefault('initial_error', '')


# ----------------------------------------------------------
# ----------------------- USB Events -----------------------
# ----------------------------------------------------------


COLUMN_NAMES = OrderedDict()

if cfg.ISATTY:
	COLUMN_NAMES['conn']     = colored('Connected',     'magenta', attrs=['bold'])
	COLUMN_NAMES['user']     = colored('User',          'magenta', attrs=['bold'])
	COLUMN_NAMES['vid']      = colored('VID',           'magenta', attrs=['bold'])
	COLUMN_NAMES['pid']      = colored('PID',           'magenta', attrs=['bold'])
	COLUMN_NAMES['prod']     = colored('Product',       'magenta', attrs=['bold'])
	COLUMN_NAMES['manufact'] = colored('Manufacturer',  'magenta', attrs=['bold'])
	COLUMN_NAMES['serial']   = colored('Serial Number', 'magenta', attrs=['bold'])
	COLUMN_NAMES['port']     = colored('Port',          'magenta', attrs=['bold'])
	COLUMN_NAMES['disconn']  = colored('Disconnected',  'magenta', attrs=['bold'])
else:
	COLUMN_NAMES['conn']     = 'Connected'
	COLUMN_NAMES['user']     = 'User'
	COLUMN_NAMES['vid']      = 'VID'
	COLUMN_NAMES['pid']      = 'PID'
	COLUMN_NAMES['prod']     = 'Product'
	COLUMN_NAMES['manufact'] = 'Manufacturer'
	COLUMN_NAMES['serial']   = 'Serial Number'
	COLUMN_NAMES['port']     = 'Port'
	COLUMN_NAMES['disconn']  = 'Disconnected'


# ----------------------------------------------------------
# --------------------- Dates sorting ----------------------
# ----------------------------------------------------------


MONTH_ENUM = {m[:3]: hex(i+1)[2:].upper() for i, m in enumerate(month_name[1:])}


# ----------------------------------------------------------
# -------------------- Data Structures ---------------------
# ----------------------------------------------------------


class DefaultOrderedDict(OrderedDict):
	def __init__(self, *args, default_factory=None, **kwargs):
		if default_factory is not None and not isinstance(default_factory, Callable):
			raise TypeError('first argument must be callable')
		OrderedDict.__init__(self, *args, **kwargs)
		self._default_factory = default_factory

	def __getitem__(self, key):
		try:
			return OrderedDict.__getitem__(self, key)
		except KeyError:
			return self.__missing__(key)

	def __missing__(self, key):
		if self._default_factory is None:
			raise KeyError(key)
		self[key] = value = self._default_factory()
		return value

	def __reduce__(self):
		if self._default_factory is None:
			args = tuple()
		else:
			args = self._default_factory,
		return type(self), args, None, None, self.items()

	def copy(self):
		return self.__copy__()

	def __copy__(self):
		return type(self)(self._default_factory, self)

	def __deepcopy__(self, memo):
		import copy
		return type(self)(self._default_factory, copy.deepcopy(self.items()))

	def __repr__(self):
		return f'OrderedDefaultDict({self._default_factory!s}, {OrderedDict.__repr__(self)!s})'


# ----------------------------------------------------------
# ----------------------- Utilities ------------------------
# ----------------------------------------------------------


def root_dir_join(name):
	return os.path.join(os.path.abspath(__file__).rsplit('/', 3)[0], name)


def os_makedirs(dirname):
	try:
		os.makedirs(dirname)
	except PermissionError as e:
		raise USBRipError(
			f'Permission denied: "{dirname}"',
			errors={'initial_error': str(e)}
		)
	except OSError as e:  # exists
		if not os.path.isdir(dirname):
			raise USBRipError(
				f'Path exists and it is not a directory: "{dirname}"',
				errors={'initial_error': str(e)}
			)


def traverse_dir(source_dir):
	return [os.path.join(root, filename)
            for root, dirnames, filenames in os.walk(source_dir)
            for filename in filenames]


def list_files(source_dir):
	return [os.path.join(source_dir, filename)
            for filename in os.listdir(source_dir)
            if os.path.isfile(os.path.join(source_dir, filename))]


# ----------------------------------------------------------
# ------------------------ Messages ------------------------
# ----------------------------------------------------------


def _get_time(fmt='%H:%M:%S'):
	return time.strftime(fmt, time.localtime())


def print_info(message):
	if cfg.QUIET:
		return

	if cfg.ISATTY:
		cprint(f'[{_get_time()}] [INFO] {message}', 'green')
	else:
		print(f'[{_get_time("%Y-%m-%d %H:%M:%S")}] [INFO] {message}')


def print_warning(message, *, errcode=0, initial_error=''):
	if cfg.QUIET:
		return

	if cfg.DEBUG:
		if errcode:
			print(f'ERRCODE: {errcode}')
		if initial_error:
			print(initial_error, file=sys.stderr)

	if cfg.ISATTY:
		cprint(f'[{_get_time()}] [WARNING] {message}', 'yellow')
	else:
		print(f'[{_get_time("%Y-%m-%d %H:%M:%S")}] [WARNING] {message}')


def print_critical(message, *, errcode=0, initial_error=''):
	if cfg.DEBUG:
		if errcode:
			print(f'ERRCODE: {errcode}')
		if initial_error:
			print(initial_error, file=sys.stderr)

	if cfg.ISATTY:
		cprint(f'[{_get_time()}] [CRITICAL] {message}', 'white', 'on_red', attrs=['bold'])
	else:
		print(f'[{_get_time("%Y-%m-%d %H:%M:%S")}] [CRITICAL] {message}')


def print_secret(message, *, secret=''):
	if cfg.ISATTY:
		cprint(
			'[{}] [SECRET] {} {}'.format(
				_get_time(),
				colored(message, 'white', attrs=['bold']),
				colored(secret, 'white', 'on_grey', attrs=['bold'])
			),
			'white', attrs=['bold']
		)
	else:
		print(f'[{_get_time("%Y-%m-%d %H:%M:%S")}] [SECRET] {message} {secret}')
