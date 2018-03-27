#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
@file common.py
@author Sam Freeside <snovvcrash@protonmail.com>
@date 2018-03

@brief Common items

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

import random
import os
import sys

from collections import OrderedDict, Callable
from termcolor import colored, cprint

# ----------------------------------------------------------
# ----------------------- Constants ------------------------
# ----------------------------------------------------------

BULLET    = '\u2022'  # '•', U_BULLET
ABSENCE   = '\u2205'  # '∅', U_EMPTY_SET
SEPARATOR = '\u2212'  # '−', U_MINUS_SIGN

# Enable colored text when terminal output (True), else (| or > for example) no color (False)
ISATTY = True if sys.stdout.isatty() else False

# ----------------------------------------------------------
# ------------------------- Banner -------------------------
# ----------------------------------------------------------

SITE = 'https://github.com/snovvcrash/usbrip'

BANNER = """\033[1;33m\
                       
         _     {{4}}   
 _ _ ___| |_ ___[+]___ 
| | |_ -| . |  _[*] . |
|___|___|___|_| [?]  _|
               x[^]_|   \033[;0m\033[4;37m{!s}\033[;0m
""".format(SITE)

E = ('E', 'e', '3')
N = ('N', 'n')
S = ('S', 's', '5')
I = ('I', 'i', '1', '!')

E,N,S,I = list(map(lambda x: random.choice(x), (E,N,S,I)))

if ISATTY:
	E,N,S,I = list(map(lambda x: colored(x, 'green', 'on_blue')+'\033[1;33m', (E,N,S,I)))
else:
	BANNER = BANNER[7:-5]

BANNER = BANNER.replace('+', E, 1)
BANNER = BANNER.replace('*', N, 1)
BANNER = BANNER.replace('?', S, 1)
BANNER = BANNER.replace('^', I, 1)

# ----------------------------------------------------------
# ------------------------- Debug --------------------------
# ----------------------------------------------------------

DEBUG = False

def time_it(func):
	import functools
	import time
	@functools.wraps(func)
	def wrapper(*args, **kwargs):
		start = time.time()
		result = func(*args, **kwargs)
		end = time.time()
		print('{}: {:.3f} seconds'.format(func.__name__, end-start))
		return result
	return wrapper

class time_it_if_debug():
	def __init__(self, condition, decorator):
		self._condition = condition
		self._decorator = decorator

	def __call__(self, func):
		if not self._condition:
			return func
		return self._decorator(func)

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

if ISATTY:
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
# -------------------- Data Structures ---------------------
# ----------------------------------------------------------

class DefaultOrderedDict(OrderedDict):
	def __init__(self, default_factory=None, *args, **kwargs):
		if (default_factory is not None and not isinstance(default_factory, Callable)):
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
		return 'OrderedDefaultDict({!s}, {!s})'.format(self._default_factory, OrderedDict.__repr__(self))

# ----------------------------------------------------------
# ----------------------- Utilities ------------------------
# ----------------------------------------------------------

def root_dir_join(name):
	return os.path.join(os.path.abspath(__file__).rsplit('/', 2)[0], name)

def os_makedirs(dirname):
	try:
		os.makedirs(dirname)
	except PermissionError as e:
		raise USBRipError('Permission denied: \'{}\''.format(dirname), {'initial_error': str(e)} )
	except OSError as e:  # exists
		if not os.path.isdir(dirname):
			raise USBRipError('Path exists and it is not a directory: \'{}\''.format(dirname),
                              {'initial_error': str(e)} )

def traverse_dir(source_dir):
	return [ os.path.join(root, filename)
			 for root, dirnames, filenames in os.walk(source_dir)
			 for filename in filenames ]

def list_files(source_dir):
	return [ os.path.join(source_dir, filename)
			 for filename in os.listdir(source_dir)
			 if os.path.isfile(os.path.join(source_dir, filename)) ]

# ----------------------------------------------------------
# ------------------------ Messages ------------------------
# ----------------------------------------------------------

def print_info(message, *, quiet=False):
	if quiet:
		return
		
	if ISATTY:
		cprint('[INFO] {}'.format(message), 'green')
	else:
		print('[INFO] {}'.format(message))

def print_warning(message, *, errcode=0, initial_error=''):
	if DEBUG:
		if errcode:
			print('ERRCODE: {}'.format(errcode))
		if initial_error:
			print(initial_error, file=sys.stderr)

	if ISATTY:
		cprint('[WARNING] {}'.format(message), 'yellow')
	else:
		print('[WARNING] {}'.format(message))

def print_critical(message, *, errcode=0, initial_error=''):
	if DEBUG:
		if errcode:
			print('ERRCODE: {}'.format(errcode))
		if initial_error:
			print(initial_error, file=sys.stderr)

	if ISATTY:
		cprint('[CRITICAL] {}'. format(message), 'white', 'on_red', attrs=['bold'])
	else:
		print('[CRITICAL] {}'. format(message))
