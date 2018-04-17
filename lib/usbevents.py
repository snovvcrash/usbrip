#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
@file usbevents.py
@author Sam Freeside <snovvcrash@protonmail.com>
@date 2018-03

@brief USB events handler

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

"""
mount - Does Ubuntu log when USB devices are connected? - Ask Ubuntu
	https://askubuntu.com/questions/142050/does-ubuntu-log-when-usb-devices-are-connected
ubuntu 14.04 - method by which I can track down a list of flash drives - Super User
	https://superuser.com/questions/1041548/method-by-which-i-can-track-down-a-list-of-flash-drives
monitoring - Monitor history of USB flash drives - Unix & Linux Stack Exchange
	https://unix.stackexchange.com/questions/152240/monitor-history-of-usb-flash-drives
"""

import re
import gzip
import json
import itertools
import operator
import os
import sys

from collections import OrderedDict, defaultdict
from terminaltables import AsciiTable, SingleTable
from termcolor import colored, cprint
from calendar import month_name
from string import printable

from lib.common import BULLET
from lib.common import ABSENCE
from lib.common import SEPARATOR
from lib.common import ISATTY
from lib.common import COLUMN_NAMES
from lib.common import DefaultOrderedDict
from lib.common import root_dir_join
from lib.common import os_makedirs
from lib.common import list_files
from lib.common import print_info
from lib.common import print_warning
from lib.common import print_critical
from lib.common import USBRipError
from lib.common import DEBUG
from lib.common import time_it
from lib.common import time_it_if_debug

# ----------------------------------------------------------
# ----------------------- USB Events -----------------------
# ----------------------------------------------------------

class USBEvents:

	# SingleTable (uses ANSI escape codes) when termianl output, else (| or > for example) AsciiTable (only ASCII)
	TableClass = SingleTable if ISATTY else AsciiTable

	# If True -> supress banner, info messages and user iteraction
	QUIET = False

	@time_it_if_debug(DEBUG, time_it)
	def __init__(self, files=None, *, quiet=False):
		if quiet:
			USBEvents.QUIET = quiet

		if files:
			raw_history = DefaultOrderedDict(list)
			for file in files:
				raw_history.update(_read_log_file(file))
		else:
			try:
				raw_history = _get_raw_history()
			except USBRipError as e:
				print_critical(str(e))

		divided_history = _divide_history(raw_history)

		self._all_events = _parse_history(divided_history)
		self._violations, self._events_to_show = [], None

	# ------------------- USB Events History -------------------

	@time_it_if_debug(DEBUG, time_it)
	def event_history(self, columns, *, sieve=None, repres=None):
		if columns:
			table_data = [[COLUMN_NAMES[name] for name in columns]]
		else:
			columns = [key for key in COLUMN_NAMES.keys()]
			table_data = [[val for val in COLUMN_NAMES.values()]]

		self._events_to_show = _filter_events(self._all_events, sieve)
		if not self._events_to_show:
			print_info('No USB events found!', quiet=USBEvents.QUIET)
			return

		if not USBEvents.QUIET and ISATTY:
			number, filename = _output_choice('event history', 'history.json', 'history/')
			if number is None:
				return
			elif number == 1:
				_json_dump(self._events_to_show, 'event history', filename)
				return

		_represent_events(self._events_to_show, columns, table_data, 'USB-History-Events', repres)

	# ---------------- USB Events Gen Auth JSON ----------------

	@time_it_if_debug(DEBUG, time_it)
	def generate_auth_json(self, output_auth, *, sieve=None):
		try:
			dirname = os.path.dirname(filename)
			os_makedirs(dirname)
		except USBRipError as e:
			print_critical(str(e), initial_error=e.errors['initial_error'])
			return
		else:
			print_info('Created \'{}\''.format(dirname))

		try:
			auth_json = open(output_auth, 'w')
		except PermissionError as e:
			print_critical('Permission denied: \'{}\''.format(output_auth), initial_error=str(e))
			return

		self._events_to_show = _filter_events(self._all_events, sieve)
		if not self._events_to_show:
			print_info('No USB violation events found!', quiet=USBEvents.QUIET)
			json.dump([], auth_json)
			auth_json.close()
			return

		print_info('Generating authorized device list (JSON)', quiet=USBEvents.QUIET)

		auth = defaultdict(list)
		for event in self._events_to_show:
			for key, val in event.items():
				if key in ('vid', 'pid', 'prod', 'manufact', 'serial') and \
                   val is not None                                     and \
                   val not in auth[key]:
					auth[key].append(val)

		for key in auth.keys():
			auth[key].sort()

		json.dump(auth, auth_json, sort_keys=True, indent=4)
		auth_json.close()

		print_info('New authorized device list: \'{}\''.format(output_auth), quiet=USBEvents.QUIET)

	# ----------------- USB Events Violations ------------------

	@time_it_if_debug(DEBUG, time_it)
	def search_violations(self, input_auth, columns, *, sieve=None, repres=None):
		try:
			auth = _process_auth_json(input_auth)
		except json.decoder.JSONDecodeError as e:
			print_critical('Failed to decode authorized device list (JSON)', initial_error=str(e))
			return

		if columns:
			table_data = [[COLUMN_NAMES[name] for name in columns]]
		else:
			columns = [key for key in COLUMN_NAMES.keys()]
			table_data = [[val for val in COLUMN_NAMES.values()]]

		print_info('Searching for violations', quiet=USBEvents.QUIET)

		for event in self._all_events:
			try:
				if any(event[key] not in vals and event[key] is not None for key, vals in auth.items()):
					self._violations.append(event)
			except KeyError as e:
				print_critical('Invalid structure of authorized device list (JSON)', initial_error=str(e))
				return

		self._events_to_show = _filter_events(self._violations, sieve)
		if not self._events_to_show:
			print_info('No USB violation events found!', quiet=USBEvents.QUIET)
			json.dump([], auth_json)
			auth_json.close()
			return

		if not USBEvents.QUIET and ISATTY:
			number, filename = _output_choice('violation', 'viol.json', 'violations/')
			if number is None:
				return
			elif number == 1:
				_json_dump(self._events_to_show, 'violation', filename)
				return

		_represent_events(self._events_to_show, columns, table_data, 'USB-Violation-Events', repres)

# ----------------------------------------------------------
# ----------------------- Utilities ------------------------
# ----------------------------------------------------------

def _get_raw_history():
	raw_history = DefaultOrderedDict(list)

	print_info('Searching for log files: \'/var/log/syslog*\' or \'/var/log/messages*\'', quiet=USBEvents.QUIET)

	syslog_files = sorted([ filename
                            for filename in list_files('/var/log/')
                            if filename.rsplit('/', 1)[1].startswith('syslog') ])

	if len(syslog_files) > 0:
		for syslog in syslog_files:
			raw_history.update(_read_log_file(syslog))
	else:
		messages_files = sorted([ filename
                                  for filename in list_files('/var/log/')
                                  if filename.rsplit('/', 1)[1].startswith('messages') ])

		if len(messages_files) > 0:
			for messages in messages_files:
				raw_history.update(_read_log_file(messages))
		else:
			raise USBRipError('None of log file types was found!')

	return raw_history

def _read_log_file(filename):
	filtered = DefaultOrderedDict(list)

	if filename.endswith('.gz'):
		print_info('Unpacking \'{}\''.format(filename), quiet=USBEvents.QUIET)
		try:
			log = gzip.open(filename, 'rb')
		except PermissionError as e:
			print_warning('Permission denied: \'{}\''.format(filename), initial_error=str(e))
			return filtered
		else:
			sentinel = b''
			filename = filename[:-3]
	else:
		log = open(filename, 'r')
		sentinel = ''

	print_info('Reading \'{}\''.format(filename), quiet=USBEvents.QUIET)
	regex = re.compile(r'usb')
	for line in iter(log.readline, sentinel):
		if isinstance(line, bytes):
			line = line.decode(encoding='utf-8')
		if regex.search(line):
			filtered[line[:15]].append(line)  # line[:15] == 'Mon dd hh:mm:ss'

	log.close()
	return filtered

def _divide_history(raw_history):
	divided_history = OrderedDict()
	for date, logs in raw_history.items():
		merged_logs = ''.join([line for line in logs])
		if 'New USB device found' in merged_logs:
			divided_history[(date, 'c')] = logs
		elif 'disconnect' in merged_logs:
			divided_history[(date, 'd')] = logs

	return divided_history

def _parse_history(divided_history):
	re_vid      = re.compile(r'idVendor=(\w+)')
	re_pid      = re.compile(r'idProduct=(\w+)')
	re_prod     = re.compile(r'Product: (.*?$)')
	re_manufact = re.compile(r'Manufacturer: (.*?$)')
	re_serial   = re.compile(r'SerialNumber: (.*?$)')
	re_port     = re.compile(r'usb (.*[0-9]):')

	all_events = []
	for (date, action), logs in _sort_by_date(divided_history.items()):
		if action == 'c':
			record_collection = []
			curr, link, interrupted = -1, -1, False

			for line in logs:
				if 'New USB device found' in line:
					user = line[16:].split(' ', 1)[0]  # line[:16] == 'Mon dd hh:mm:ss '
					vid = re_vid.search(line).group(1)
					pid = re_pid.search(line).group(1)
					port = re_port.search(line).group(1)

					event = { 'conn':        date,
                              'user':        user,
                              'vid':          vid,
                              'pid':          pid,
                              'prod':        None,
                              'manufact':    None,
                              'serial':      None,
                              'port':        port,
                              'disconn':     None }

					record_collection.append(event)
					curr += 1
					link = 1
					interrupted = False
					
				else:
					if not interrupted:
						if link == 1:
							link = 2
						elif link == 2:
							try:  # if 'Product:' in line
								prod = re_prod.search(line).group(1)
							except AttributeError:
								interrupted = True
							else:
								record_collection[curr]['prod'] = prod
								link = 3
						elif link == 3:
							try:  # if 'Manufacturer:' in line
								manufact = re_manufact.search(line).group(1)
							except AttributeError:
								interrupted = True
							else:
								record_collection[curr]['manufact'] = manufact
								link = 4
						elif link == 4:
							try:  # if 'SerialNumber:' in line
								serial = re_serial.search(line).group(1)
							except AttributeError:
								pass
							else:
								record_collection[curr]['serial'] = serial
							finally:
								interrupted = True
					else:
						continue

			all_events.extend(record_collection)

		elif action == 'd':
			for line in logs:
				if 'disconnect' in line:
					port = re_port.search(line).group(1)
					for i in range(len(all_events)-1, -1, -1):
						if all_events[i]['port'] == port:
							all_events[i]['disconn'] = date
							break

	return all_events

def _sort_by_date(unsorted_log):
	# "usorted_log" is a list of ( ('Mon dd hh:mm:ss', 'EVENT'), ['LOG_DATA'] )
	MONTH_ENUM = { m[:3]: str(i) for i, m in enumerate(month_name[1:]) }
	return sorted(unsorted_log, key=lambda i: MONTH_ENUM[i[0][0][:3]] + i[0][0][3:])

def _process_auth_json(input_auth):
	with open(input_auth, 'r+') as auth_json:
		#auth = json.load(auth_json, object_pairs_hook=OrderedDict)
		auth = json.load(auth_json)
		auth_json.seek(0)
		for key, vals in auth.items():
			auth[key] = list(filter(None, vals))
			if not _is_sorted(vals):
				auth[key].sort()
		json.dump(auth, auth_json, sort_keys=True, indent=4)
		auth_json.truncate()

	return auth

def _is_sorted(iterable, reverse=False):
	def pairwise(iterable):
		a, b = itertools.tee(iterable)
		next(b, None)
		return zip(a, b)

	compare = operator.ge if reverse else operator.le

	return all(compare(current_element, next_element)
               for current_element, next_element
               in pairwise(iterable))

def _filter_events(all_events, sieve=None):
	if not sieve:
		sieve = { 'external': False,
                  'number':      -1,
                  'dates':       [] }
	else:
		print_info('Filtering events', quiet=USBEvents.QUIET)

	if sieve['external']:
		events_to_show = [event for event in all_events if event['disconn'] is not None]
	else:
		events_to_show = all_events

	if sieve['dates']:
		events_to_show = [event for date in sieve['dates'] for event in events_to_show if event['conn'][:6] == date]

	if not len(events_to_show):
		return None

	SIZE = len(events_to_show)
	if sieve['number'] == -1 or sieve['number'] >= SIZE:
		if sieve['number'] > SIZE:
			print_warning('USB action history has only {} entries instead of requested {}, ' \
                          'displaying all of them...'.format(SIZE, sieve['number']))
		sieve['number'] = SIZE

	return [events_to_show[SIZE-i] for i in range(sieve['number'], 0, -1)]

def _represent_events(events_to_show, columns, table_data, title, repres=None):
	print_info('Preparing gathered events', quiet=USBEvents.QUIET)

	if not repres:
		repres = { 'table': False,
                   'list':  False,
                   'smart':  True }

	max_len = { 'conn':     15,
                'user':     max(max(len(event['user']) for event in events_to_show), len('User')),
                'vid':       4,
                'pid':       4,
                'prod':     max(max(len(str(event['prod'])) for event in events_to_show), len('Product')),
                'manufact': max(max(len(str(event['manufact'])) for event in events_to_show), len('Manufacturer')),
                'serial':   max(max(len(str(event['serial'])) for event in events_to_show), len('Serial Number')),
                'port':     max(max(len(event['port']) for event in events_to_show), len('Port')),
                'disconn':  15 }

	for event in events_to_show:
		if 'conn' in columns:
			try:
				prev_cday
			except NameError:
				prev_cday = ''
			curr_cday = event['conn'][:6]
			if prev_cday != curr_cday:
				cday = ['{} {}'.format(curr_cday, BULLET*8)]  # 8 == len(event['conn'] - event['conn'][:6] - 1)
				table_data.append(cday + [SEPARATOR*max_len[name] for name in columns if name != 'conn'])
			prev_cday = curr_cday

		row = []
		for name in columns:
			if event[name] is None:
				event[name] = ABSENCE

			item = event[name]
			if name == 'conn' and ISATTY:
				item = colored(item, 'green')
			elif name == 'disconn' and ISATTY:
				item = colored(item, 'red')

			row.append(item)

		table_data.append(row)

	if ISATTY:
		event_table = _build_single_table(USBEvents.TableClass, table_data, colored(title, 'white', attrs=['bold']))
	else:
		event_table = _build_single_table(USBEvents.TableClass, table_data, title)

	# Display as table
	if repres['smart'] and event_table.ok or repres['table']:
		print_info('Representation: Table', quiet=USBEvents.QUIET)
		print('\n' + event_table.table)

	# Display as list
	elif repres['smart'] and not event_table.ok or repres['list']:
		if not event_table.ok:
			print_warning('Terminal window is too small to display table properly')
			print_warning('Representation: List')

		max_len = max(len(str(val)) for event in events_to_show for val in event.values()) + \
                  len('Serial Number:  ')  # max length string
		if not max_len // 2: max_len += 1
		date_sep_len = (max_len - 8) // 2

		if ISATTY:
			cprint('\n' + title, 'white', attrs=['bold'])
		else:
			print('\n' + title)

		prev_cday = ''
		for event in events_to_show:
			curr_cday = event['conn'][:6]
			if prev_cday != curr_cday:
				print(SEPARATOR * max_len)
				print('{} {} {}'.format(BULLET*date_sep_len, curr_cday, BULLET*date_sep_len))
				print(SEPARATOR * max_len)
			else:
				print(SEPARATOR * max_len)
			prev_cday = curr_cday

			if ISATTY:
				print(colored('Connected:      ', 'magenta', attrs=['bold']) + colored(event['conn'], 'green'))
				print(colored('User:           ', 'magenta', attrs=['bold']) + event['user'])
				print(colored('VID:            ', 'magenta', attrs=['bold']) + event['vid'])
				print(colored('PID:            ', 'magenta', attrs=['bold']) + event['pid'])
				print(colored('Product:        ', 'magenta', attrs=['bold']) + str(event['prod']))
				print(colored('Manufacturer:   ', 'magenta', attrs=['bold']) + str(event['manufact']))
				print(colored('Serial Number:  ', 'magenta', attrs=['bold']) + str(event['serial']))
				print(colored('Bus-Port:       ', 'magenta', attrs=['bold']) + event['port'])
				print(colored('Disconnected:   ', 'magenta', attrs=['bold']) + colored(event['disconn'], 'red'))
			else:
				print('Connected:      ' + event['conn'])
				print('User:           ' + event['user'])
				print('VID:            ' + event['vid'])
				print('PID:            ' + event['pid'])
				print('Product:        ' + str(event['prod']))
				print('Manufacturer:   ' + str(event['manufact']))
				print('Serial Number:  ' + str(event['serial']))
				print('Bus-Port:       ' + event['port'])
				print('Disconnected:   ' + event['disconn'])
		print(SEPARATOR * max_len)

def _build_single_table(TableClass, table_data, title, align='right', inner_row_border=False):
	single_table = TableClass(table_data)
	single_table.title = title
	for i in range(len(table_data[0])):
		single_table.justify_columns[i] = align
	if inner_row_border:
		single_table.inner_row_border = True
	return single_table

def _json_dump(events_to_show, list_name, filename):
	print_info('Generating {} list (JSON)'.format(list_name), quiet=USBEvents.QUIET)

	out = OrderedDict()
	for event in events_to_show:
		out[event['conn']] = OrderedDict()
		for key, val in sorted(event.items()):
			if key != 'conn':
				out[event['conn']][key] = val

	try:
		with open(filename, 'w') as out_json:
			json.dump(out, out_json, indent=4)
	except PermissionError as e:
		print_critical('Permission denied: \'{}\''.format(filename), initial_error=str(e))
		return

	print_info('New {} list: \'{}\''.format(list_name, filename), quiet=USBEvents.QUIET)

def _output_choice(list_name, default_filename, dirname):
	while True:
		print('[?] How would you like your {} list to be generated?\n'.format(list_name))

		print('    1. JSON-file')
		print('    2. Terminal stdout')

		number = input('\n[>] Please enter the number of your choice: ')

		if number == '1':
			while True:
				filename = input('[>] Please enter the base name for the output file ' \
                                 '(default is \'{}\'): '.format(default_filename))

				if all(c in printable for c in filename) and len(filename) < 256:
					if not filename:
						filename = default_filename
					elif filename[-5:] != '.json':
						filename = filename + '.json'

					filename = root_dir_join(dirname + filename)

					try:
						dirname = os.path.dirname(filename)
						os_makedirs(dirname)
					except USBRipError as e:
						print_critical(str(e), initial_error=e.errors['initial_error'])
						return (None, '')
					else:
						print_info('Created \'{}\''.format(dirname))

					overwrite = True
					if os.path.exists(filename):
						while True:
							overwrite = input('[?] File exists. Would you like to overwrite it? [Y/n]: ')
							if len(overwrite) == 1 and overwrite in 'Yy':
								overwrite = True
								break
							elif len(overwrite) == 1 and overwrite in 'Nn':
								overwrite = False
								break

					if overwrite:
						return (int(number), filename)

		elif number == '2':
			return (int(number), '')
