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

'''
mount - Does Ubuntu log when USB devices are connected? - Ask Ubuntu
	https://askubuntu.com/questions/142050/does-ubuntu-log-when-usb-devices-are-connected
ubuntu 14.04 - method by which I can track down a list of flash drives - Super User
	https://superuser.com/questions/1041548/method-by-which-i-can-track-down-a-list-of-flash-drives
monitoring - Monitor history of USB flash drives - Unix & Linux Stack Exchange
	https://unix.stackexchange.com/questions/152240/monitor-history-of-usb-flash-drives
'''

__author__ = 'Sam Freeside (@snovvcrash)'
__email__  = 'snovvcrash@protonmail[.]ch'
__site__   = 'https://github.com/snovvcrash/usbrip'
__brief__  = 'USB events handler'

import re
import codecs
import gzip
import json
import itertools
import operator
import os
from collections import OrderedDict, defaultdict
from string import printable

from terminaltables import AsciiTable, SingleTable
from termcolor import colored, cprint

import usbrip.lib.core.config as cfg
from usbrip.lib.core.common import BULLET
from usbrip.lib.core.common import ABSENCE
from usbrip.lib.core.common import SEPARATOR
from usbrip.lib.core.common import COLUMN_NAMES
from usbrip.lib.core.common import MONTH_ENUM
from usbrip.lib.core.common import DefaultOrderedDict
from usbrip.lib.core.common import root_dir_join
from usbrip.lib.core.common import os_makedirs
from usbrip.lib.core.common import list_files
from usbrip.lib.core.common import print_info
from usbrip.lib.core.common import print_warning
from usbrip.lib.core.common import print_critical
from usbrip.lib.core.common import USBRipError
from usbrip.lib.utils.debug import time_it
from usbrip.lib.utils.debug import time_it_if_debug


# ----------------------------------------------------------
# ----------------------- USB Events -----------------------
# ----------------------------------------------------------


class USBEvents:

	# SingleTable (uses ANSI escape codes) when termianl output, else (| or > for example) AsciiTable (only ASCII)
	TableClass = SingleTable if cfg.ISATTY else AsciiTable

	@time_it_if_debug(cfg.DEBUG, time_it)
	def __new__(cls, files=None):
		if files:
			raw_history = DefaultOrderedDict(default_factory=list)
			for file in files:
				raw_history.update(_read_log_file(file))
		else:
			try:
				raw_history = _get_raw_history()
			except USBRipError as e:
				print_critical(str(e))
				return None

		divided_history = _divide_history(raw_history)
		all_events = _parse_history(divided_history)

		instance = super().__new__(cls)
		instance._all_events = all_events  # self._all_events
		instance._violations = []          # self._violations
		instance._events_to_show = None    # self._events_to_show
		return instance

	# ------------------- USB Events History -------------------

	@time_it_if_debug(cfg.DEBUG, time_it)
	def event_history(self, columns, *, indent=4, sieve=None, repres=None):
		self._events_to_show = _filter_events(self._all_events, sieve)
		if not self._events_to_show:
			print_info('No USB events found!')
			return

		if not cfg.QUIET and cfg.ISATTY:
			number, filename = _output_choice('event history', 'history.json', 'history/')
			if number is None:
				return
			elif number == 1:
				try:
					_dump_events(self._events_to_show, 'event history', filename, indent)
				except USBRipError as e:
					print_critical(str(e), initial_error=e.errors['initial_error'])
				return

		if columns:
			table_data = [[COLUMN_NAMES[name] for name in columns]]
		else:
			columns = [key for key in COLUMN_NAMES.keys()]
			table_data = [[val for val in COLUMN_NAMES.values()]]

		_represent_events(self._events_to_show, columns, table_data, 'USB-History-Events', repres)

	# -------------------- USB Events Open ---------------------

	@staticmethod
	@time_it_if_debug(cfg.DEBUG, time_it)
	def open_dump(input_dump, columns, *, sieve=None, repres=None):
		print_info(f'Opening USB event dump: "{os.path.abspath(input_dump)}"')

		try:
			with open(input_dump, 'r', encoding='utf-8') as dump:
				events_dumped = json.load(dump)
		except json.decoder.JSONDecodeError as e:
			print_critical('Failed to decode event dump (JSON)', initial_error=str(e))
			return

		if not events_dumped:
			print_critical('This dump is empty!')
			return

		events_to_show = _filter_events(events_dumped, sieve)
		if not events_to_show:
			print_info('No USB events found!')
			return

		if columns:
			table_data = [[COLUMN_NAMES[name] for name in columns]]
		else:
			columns = [key for key in COLUMN_NAMES.keys()]
			table_data = [[val for val in COLUMN_NAMES.values()]]

		_represent_events(events_to_show, columns, table_data, 'USB-Event-Dump', repres)

	# ------------------ USB Events Gen Auth -------------------

	@time_it_if_debug(cfg.DEBUG, time_it)
	def generate_auth_json(self, output_auth, attributes, *, indent=4, sieve=None):
		self._events_to_show = _filter_events(self._all_events, sieve)
		if not self._events_to_show:
			print_info('No USB devices found!')
			return 1

		try:
			dirname = os.path.dirname(output_auth)
			os_makedirs(dirname)
		except USBRipError as e:
			print_critical(str(e), initial_error=e.errors['initial_error'])
			return 1
		else:
			print_info(f'Created "{dirname}"')

		try:
			auth_json = open(output_auth, 'w', encoding='utf-8')
		except PermissionError as e:
			print_critical(f'Permission denied: "{output_auth}". Retry with sudo', initial_error=str(e))
			return 1

		print_info('Generating authorized device list (JSON)')

		if not attributes:
			attributes = ('vid', 'pid', 'prod', 'manufact', 'serial')

		auth = defaultdict(list)
		for event in self._events_to_show:
			for key, val in event.items():
				if (key in attributes and
					val is not None and
					val not in auth[key]):
					auth[key].append(val)

		for key in auth.keys():
			auth[key].sort()

		json.dump(auth, auth_json, sort_keys=True, indent=indent)
		auth_json.close()

		print_info(f'New authorized device list: "{os.path.abspath(output_auth)}"')

	# ----------------- USB Events Violations ------------------

	@time_it_if_debug(cfg.DEBUG, time_it)
	def search_violations(self, input_auth, attributes, columns, *, indent=4, sieve=None, repres=None):
		print_info(f'Opening authorized device list: "{os.path.abspath(input_auth)}"')

		try:
			auth = _process_auth_list(input_auth, indent)
		except json.decoder.JSONDecodeError as e:
			print_critical('Failed to decode authorized device list (JSON)', initial_error=str(e))
			return

		print_info('Searching for violations')

		if not attributes:
			attributes = auth.keys()

		for event in self._all_events:
			try:
				if any(event[key] not in vals and
                       event[key] is not None
                       for key, vals in zip(attributes, auth.values())):
					self._violations.append(event)
			except KeyError as e:
				print_critical('No such attribute in authorized device list', initial_error=str(e))
				return

		self._events_to_show = _filter_events(self._violations, sieve)
		if not self._events_to_show:
			print_info('No USB violation events found!')
			return

		if not cfg.QUIET and cfg.ISATTY:
			number, filename = _output_choice('violation', 'viol.json', 'violations/')
			if number is None:
				return
			elif number == 1:
				try:
					_dump_events(self._events_to_show, 'violations', filename, indent)
				except USBRipError as e:
					print_critical(str(e), initial_error=e.errors['initial_error'])
				return

		if columns:
			table_data = [[COLUMN_NAMES[name] for name in columns]]
		else:
			columns = [key for key in COLUMN_NAMES.keys()]
			table_data = [[val for val in COLUMN_NAMES.values()]]

		_represent_events(self._events_to_show, columns, table_data, 'USB-Violation-Events', repres)


# ----------------------------------------------------------
# ----------------------- Utilities ------------------------
# ----------------------------------------------------------


def _get_raw_history():
	raw_history = DefaultOrderedDict(default_factory=list)

	print_info('Searching for log files: "/var/log/syslog*" or "/var/log/messages*"')

	syslog_files = sorted([filename
                           for filename in list_files('/var/log/')
                           if filename.rsplit('/', 1)[1].startswith('syslog')])

	if syslog_files:
		for syslog in syslog_files:
			raw_history.update(_read_log_file(syslog))
	else:
		messages_files = sorted([filename
                                 for filename in list_files('/var/log/')
                                 if filename.rsplit('/', 1)[1].startswith('messages')])

		if messages_files:
			for messages in messages_files:
				raw_history.update(_read_log_file(messages))
		else:
			raise USBRipError('None of log file types was found!')

	return raw_history


def _read_log_file(filename):
	filtered = DefaultOrderedDict(default_factory=list)

	if filename.endswith('.gz'):
		print_info(f'Unpacking "{os.path.abspath(filename)}"')

		try:
			log = gzip.open(filename, 'rb')
		except PermissionError as e:
			print_warning(
				f'Permission denied: "{os.path.abspath(filename)}". Retry with sudo',
				initial_error=str(e)
			)
			return filtered
		else:
			end_of_file = b''
			filename = filename[:-3]

	else:
		log = codecs.open(filename, 'r', encoding='utf-8', errors='ignore')
		end_of_file = ''

	print_info(f'Reading "{os.path.abspath(filename)}"')
	regex = re.compile(r'usb')
	for line in iter(log.readline, end_of_file):
		if isinstance(line, bytes):
			line = line.decode(encoding='utf-8', errors='ignore')
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

					try:
						vid = re_vid.search(line).group(1)
					except AttributeError:
						vid = None
					try:
						pid = re_pid.search(line).group(1)
					except AttributeError:
						pid = None
					try:
						port = re_port.search(line).group(1)
					except AttributeError:
						port = None

					event = {
						'conn':     date,
						'user':     user,
						'vid':      vid,
						'pid':      pid,
						'prod':     None,
						'manufact': None,
						'serial':   None,
						'port':     port,
						'disconn':  None
					}

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
					try:
						port = re_port.search(line).group(1)
					except AttributeError:
						pass
					else:
						for i in range(len(all_events)-1, -1, -1):
							if all_events[i]['port'] == port:
								all_events[i]['disconn'] = date
								break

	return all_events


def _sort_by_date(unsorted_log):
	# "usorted_log" is a list of ( ('Mon dd hh:mm:ss', 'EVENT'), ['LOG_DATA'] )
	return sorted(unsorted_log, key=lambda i: MONTH_ENUM[i[0][0][:3]] + i[0][0][3:])


def _process_auth_list(input_auth, indent):
	with open(input_auth, 'r+', encoding='utf-8') as auth_json:
		#auth = json.load(auth_json, object_pairs_hook=OrderedDict)
		auth = json.load(auth_json)
		auth_json.seek(0)
		for key, vals in auth.items():
			auth[key] = list(filter(None, vals))
			if not _is_sorted(vals):
				auth[key].sort()
		json.dump(auth, auth_json, sort_keys=True, indent=indent)
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


def _filter_events(all_events, sieve):
	if sieve is None:
		sieve = {
			'external': False,
			'number':      -1,
			'dates':       [],
			'fields':      {}
		}

	if sieve != {'external': False, 'number': -1, 'dates': [], 'fields': {}}:
		print_info('Filtering events')

	events_to_show = all_events

	if sieve['fields']:
		events_to_show = []
		for key, vals in sieve['fields'].items():
			events_to_show += [event for event in all_events for val in vals if event[key] == val]

	if sieve['external']:
		events_to_show = [event for event in all_events if event['disconn'] is not None]

	if sieve['dates']:
		events_to_show = [event for date in sieve['dates'] for event in events_to_show if event['conn'][:6] == date]

	if not events_to_show:
		return []

	SIZE = len(events_to_show)
	if sieve['number'] == -1 or sieve['number'] >= SIZE:
		if sieve['number'] > SIZE:
			print_warning(
				f'USB action history has only {SIZE} entries instead of requested {sieve["number"]}, '
				f'displaying all of them...'
			)

		sieve['number'] = SIZE

	return [events_to_show[SIZE-i] for i in range(sieve['number'], 0, -1)]


def _represent_events(events_to_show, columns, table_data, title, repres):
	print_info('Preparing gathered events')

	if repres is None:
		repres = {
			'table': False,
			'list':  False,
			'smart':  True
		}

	max_len = {
		'conn':     15,
		'user':     max(max(len(event['user']) for event in events_to_show), len('User')),
		'vid':       4,
		'pid':       4,
		'prod':     max(max(len(str(event['prod'])) for event in events_to_show), len('Product')),
		'manufact': max(max(len(str(event['manufact'])) for event in events_to_show), len('Manufacturer')),
		'serial':   max(max(len(str(event['serial'])) for event in events_to_show), len('Serial Number')),
		'port':     max(max(len(event['port']) for event in events_to_show), len('Port')),
		'disconn':  15
	}

	prev_cday = ''
	for event in events_to_show:
		if 'conn' in columns:
			curr_cday = event['conn'][:6]
			if prev_cday != curr_cday:
				cday = [f'{curr_cday} {BULLET*8}']  # 8 == len(event['conn'] - event['conn'][:6] - 1)
				table_data.append(cday + [SEPARATOR*max_len[name] for name in columns if name != 'conn'])
			prev_cday = curr_cday

		row = []
		for name in columns:
			if event[name] is None:
				event[name] = ABSENCE

			item = event[name]
			if name == 'conn' and cfg.ISATTY:
				item = colored(item, 'green')
			elif name == 'disconn' and cfg.ISATTY:
				item = colored(item, 'red')

			row.append(item)

		table_data.append(row)

	event_table = _build_single_table(USBEvents.TableClass, table_data, colored(title, 'white', attrs=['bold']))

	# Display as table
	if cfg.ISATTY and (repres['smart'] and event_table.ok or repres['table']):
		print_info('Representation: Table')
		print('\n' + event_table.table)

	# Display as list
	elif not cfg.ISATTY or (repres['smart'] and not event_table.ok or repres['list']):
		if not event_table.ok:
			print_warning('Terminal window is too small to display table properly')
			print_warning('Representation: List')
		else:
			print_info('Representation: List')

		max_len = max(len(str(val)) for event in events_to_show for val in event.values()) + \
                      len('Serial Number:  ')  # max length string
		if not max_len // 2: max_len += 1
		date_sep_len = (max_len - 8) // 2

		if cfg.ISATTY:
			cprint('\n' + title, 'white', attrs=['bold'])
		else:
			print('\n' + title)

		prev_cday = ''
		for event in events_to_show:
			curr_cday = event['conn'][:6]
			if prev_cday != curr_cday:
				print(SEPARATOR * max_len)
				print(f'{BULLET*date_sep_len} {curr_cday} {BULLET*date_sep_len}')
				print(SEPARATOR * max_len)
			else:
				print(SEPARATOR * max_len)
			prev_cday = curr_cday

			if cfg.ISATTY:
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


def _dump_events(events_to_show, list_name, filename, indent):
	print_info(f'Generating {list_name} list (JSON)')

	out = []
	for event in events_to_show:
		tmp_event_dict = OrderedDict()
		for key in ('conn', 'user', 'vid', 'pid', 'prod', 'manufact', 'serial', 'port', 'disconn'):
			tmp_event_dict[key] = event[key]
		out.append(tmp_event_dict)

	try:
		with open(filename, 'w', encoding='utf-8') as out_json:
			json.dump(out, out_json, indent=indent)
	except PermissionError as e:
		raise USBRipError(
			f'Permission denied: "{os.path.abspath(filename)}". Retry with sudo',
			errors={'initial_error': str(e)}
		)

	print_info(f'New {list_name} list: "{os.path.abspath(filename)}"')


def _output_choice(list_name, default_filename, dirname):
	while True:
		print(f'[?] How would you like your {list_name} list to be generated?\n')

		print('    1. JSON-file')
		print('    2. Terminal stdout')

		number = input('\n[>] Please enter the number of your choice: ')

		if number == '1':
			while True:
				filename = input(
					f'[>] Please enter the base name for the output file '
					f'(default is "{default_filename}"): '
				)

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
						print_info(f'Created "{dirname}"')

					overwrite = True
					if os.path.isfile(filename):
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
