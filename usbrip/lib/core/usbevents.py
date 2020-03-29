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
import stat
from datetime import datetime
from collections import OrderedDict, defaultdict
from string import printable
from subprocess import check_output
from io import StringIO
from random import randint

from terminaltables import AsciiTable, SingleTable
from termcolor import colored, cprint
from tqdm import tqdm

import usbrip.lib.core.config as cfg
from usbrip.lib.core.common import BULLET
from usbrip.lib.core.common import ABSENCE
from usbrip.lib.core.common import SEPARATOR
from usbrip.lib.core.common import COLUMN_NAMES
from usbrip.lib.core.common import intersect_event_sets
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
	TableClass = SingleTable if cfg.ISATTY and cfg.ISUTF8 else AsciiTable

	@time_it_if_debug(cfg.DEBUG, time_it)
	def __new__(cls, files=None):
		try:
			if files:
				filtered_history = []
				for file in files:
					filtered_history.extend(_read_log_file(file))

			else:
				print_info('Trying to run journalctl...')

				# child_env = os.environ.copy()
				# child_env['LANG'] = 'en_US.utf-8'
				# journalctl_out = check_output(['journalctl'], env=child_env).decode('utf-8')

				try:
					journalctl_out = check_output([
						'journalctl',
						'-o',
						'short-iso-precise'
					]).decode('utf-8')

				except Exception as e:
					print_warning(f'Failed to run journalctl: {str(e)}')
					filtered_history = _get_filtered_history()

				else:
					if '-- Logs begin at' in journalctl_out:
						print_info('Successfully runned journalctl')

						filtered_history = _read_log_file(
							None,
							log=StringIO(journalctl_out),
							total=journalctl_out.count('\n')
						)

					else:
						print_warning(f'An error occured when running journalctl: {journalctl_out}')
						filtered_history = _get_filtered_history()

		except USBRipError as e:
			print_critical(str(e), initial_error=e.errors['initial_error'])
			return None

		all_events = _parse_history(filtered_history)

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
			choice, abs_filename = _output_choice('event history', 'history.json')
			if choice == '2':
				try:
					_dump_events(self._events_to_show, 'event history', abs_filename, indent)
				except USBRipError as e:
					print_critical(str(e), initial_error=e.errors['initial_error'])
				return

		# elif choice == '1' or choice == '':

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
		abs_input_dump = os.path.abspath(input_dump)

		print_info(f'Opening USB event dump: "{abs_input_dump}"')

		try:
			with open(abs_input_dump, 'r', encoding='utf-8') as dump:
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

	# ------------------ USB Events GenAuth -------------------

	@time_it_if_debug(cfg.DEBUG, time_it)
	def generate_auth_json(self, output_auth, attributes, *, indent=4, sieve=None):
		self._events_to_show = _filter_events(self._all_events, sieve)
		if not self._events_to_show:
			print_info('No USB devices found!')

		rand_id = f'usbrip-{randint(1000, 9999)}'
		self._events_to_show += [{
			'conn':     rand_id,
			'host':     rand_id,
			'vid':      rand_id,
			'pid':      rand_id,
			'prod':     rand_id,
			'manufact': rand_id,
			'serial':   rand_id,
			'port':     rand_id,
			'disconn':  rand_id
		}]

		abs_output_auth = os.path.abspath(output_auth)

		try:
			dirname = os.path.dirname(abs_output_auth)
			os_makedirs(dirname)
		except USBRipError as e:
			print_critical(str(e), initial_error=e.errors['initial_error'])
			return 1
		else:
			print_info(f'Created directory "{dirname}/"')

		try:
			auth_json = open(abs_output_auth, 'w', encoding='utf-8')
		except PermissionError as e:
			print_critical(f'Permission denied: "{abs_output_auth}". Retry with sudo', initial_error=str(e))
			return 1

		print_info('Generating authorized device list (JSON)')

		if not attributes:
			attributes = ('vid', 'pid', 'prod', 'manufact', 'serial')

		auth = defaultdict(set)
		for event in tqdm(self._events_to_show, ncols=80, unit='dev'):
			for key, val in event.items():
				if key in attributes and val is not None:
					auth[key].add(val)

		auth = {key: list(vals) for key, vals in auth.items()}

		for key in auth.keys():
			auth[key].sort()

		json.dump(auth, auth_json, sort_keys=True, indent=indent)
		auth_json.close()

		os.chmod(abs_output_auth, stat.S_IRUSR | stat.S_IWUSR)  # 600

		print_info(f'New authorized device list: "{abs_output_auth}"')

	# ----------------- USB Events Violations ------------------

	@time_it_if_debug(cfg.DEBUG, time_it)
	def search_violations(self, input_auth, attributes, columns, *, indent=4, sieve=None, repres=None):
		abs_input_auth = os.path.abspath(input_auth)

		print_info(f'Opening authorized device list: "{abs_input_auth}"')

		try:
			auth = _process_auth_list(abs_input_auth, indent)
		except json.decoder.JSONDecodeError as e:
			print_critical('Failed to decode authorized device list (JSON)', initial_error=str(e))
			return

		print_info('Searching for violations')

		if not attributes:
			attributes = auth.keys()

		auth_sets = [set(auth[attr]) for attr in attributes]

		for event in tqdm(self._all_events, ncols=80, unit='dev'):
			try:
				if any(
					event[key] is not None and
					event[key] not in vals
					for key, vals in zip(attributes, auth_sets)
				):
					self._violations.append(event)
			except KeyError as e:
				print_critical('No such attribute in authorized device list', initial_error=str(e))
				return

		self._events_to_show = _filter_events(self._violations, sieve)
		if not self._events_to_show:
			print_info('No USB violation events found!')
			return

		if not cfg.QUIET and cfg.ISATTY:
			choice, abs_filename = _output_choice('violation', 'viol.json')
			if choice == '2':
				try:
					_dump_events(self._events_to_show, 'violations', abs_filename, indent)
				except USBRipError as e:
					print_critical(str(e), initial_error=e.errors['initial_error'])
				return

		# elif choice == '1' or choice == '':

		if columns:
			table_data = [[COLUMN_NAMES[name] for name in columns]]
		else:
			columns = [key for key in COLUMN_NAMES.keys()]
			table_data = [[val for val in COLUMN_NAMES.values()]]

		_represent_events(self._events_to_show, columns, table_data, 'USB-Violation-Events', repres)


# ----------------------------------------------------------
# ----------------------- Utilities ------------------------
# ----------------------------------------------------------


def _get_filtered_history():
	filtered_history = []

	print_info('Searching for log files: "/var/log/syslog*" or "/var/log/messages*"')

	syslog_files = sorted([
		filename
		for filename in list_files('/var/log/')
		if filename.rsplit('/', 1)[1].startswith('syslog')
	])

	if syslog_files:
		for syslog in syslog_files:
			filtered_history.extend(_read_log_file(syslog))
	else:
		messages_files = sorted([
			filename
			for filename in list_files('/var/log/')
			if filename.rsplit('/', 1)[1].startswith('messages')
		])

		if messages_files:
			for messages in messages_files:
				filtered_history.extend(_read_log_file(messages))
		else:
			raise USBRipError('None of log file types was found!')

	return filtered_history


def _read_log_file(filename, log=None, total=None):
	filtered = []

	if log is None:
		abs_filename = os.path.abspath(filename)

		if abs_filename.endswith('.gz'):
			print_info(f'Unpacking "{abs_filename}"')

			try:
				log = gzip.open(abs_filename, 'rb')
			except PermissionError as e:
				print_warning(
					f'Permission denied: "{abs_filename}". Retry with sudo',
					initial_error=str(e)
				)
				return filtered
			else:
				end_of_file = b''
				abs_filename = os.path.splitext(abs_filename)

		else:
			log = codecs.open(abs_filename, 'r', encoding='utf-8', errors='ignore')
			end_of_file = ''

		total = sum(1 for line in log)
		log.seek(0)

		print_info(f'Reading "{abs_filename}"')

	else:
		abs_filename = 'journalctl output'
		end_of_file = ''
		print_info(f'Reading journalctl output')

	regex = re.compile(r'(?:]|:) usb (.*?): ')
	for line in tqdm(iter(log.readline, end_of_file), ncols=80, unit='line', total=total):
		if isinstance(line, bytes):
			line = line.decode('utf-8', errors='ignore')

		if regex.search(line):
			# Case 1 -- Modified Timestamp ("%Y-%m-%dT%H:%M:%S.%f%z")

			date = line[:32].strip()
			if date.count(':') == 3:
				date = ''.join(line[:32].rsplit(':', 1))  # rreplace(':', '', 1) to remove the last ':' from "1970-01-01T00:00:00.000000-00:00" timestamp if there is one

			try:
				date = datetime.strptime(date, '%Y-%m-%dT%H:%M:%S.%f%z')  # ex. "1970-01-01T00:00:00.000000-0000"

			except ValueError:
				# Case 2 -- Non-Modified Timestamp ("%b %d %H:%M:%S")

				date = line[:15].strip()
				if '  ' in date:
					date = date.replace('  ', ' 0', 1)  # pad day of the week with zero

				try:
					date = datetime.strptime(date, '%b %d %H:%M:%S')  # ex. "Mar 18 13:56:07"
				except ValueError as e:
					raise USBRipError(f'Wrong timestamp format found in "{abs_filename}"', errors={'initial_error': str(e)})
				else:
					date = date.strftime('????-%m-%d %H:%M:%S')
					logline = line[15:].strip()

			else:
				date = date.strftime('%Y-%m-%d %H:%M:%S')
				logline = line[32:].strip()

			if any(pat in line for pat in ('New USB device found, ', 'Product: ', 'Manufacturer: ', 'SerialNumber: ')):
				filtered.append((date, 'c', logline))
			elif 'disconnect' in line:
				filtered.append((date, 'd', logline))

	log.close()
	return filtered


def _parse_history(filtered_history):
	re_vid      = re.compile(r'idVendor=(\w+)')
	re_pid      = re.compile(r'idProduct=(\w+)')
	re_prod     = re.compile(r'Product: (.*?$)')
	re_manufact = re.compile(r'Manufacturer: (.*?$)')
	re_serial   = re.compile(r'SerialNumber: (.*?$)')
	re_port     = re.compile(r'usb (.*[0-9]):')

	all_events, curr, link, interrupted = [], -1, 1, False
	for date, action, logline in filtered_history:
		if action == 'c':
			if 'New USB device found, ' in logline:
				host = logline.split(' ', 1)[0]  # logline -> '<HOST> <REST>'

				try:
					vid = re_vid.search(logline).group(1)
				except AttributeError:
					vid = None
				try:
					pid = re_pid.search(logline).group(1)
				except AttributeError:
					pid = None
				try:
					port = re_port.search(logline).group(1)
				except AttributeError:
					port = None

				event = {
					'conn':     date,
					'host':     host,
					'vid':       vid,
					'pid':       pid,
					'prod':     None,
					'manufact': None,
					'serial':   None,
					'port':     port,
					'disconn':  None
				}

				all_events.append(event)
				curr += 1
				link = 2
				interrupted = False

			elif not interrupted:
				if link == 2:
					try:  # if 'Product: ' in logline
						prod = re_prod.search(logline).group(1)
					except AttributeError:
						interrupted = True
					else:
						all_events[curr]['prod'] = prod
						link = 3
				elif link == 3:
					try:  # if 'Manufacturer: ' in logline
						manufact = re_manufact.search(logline).group(1)
					except AttributeError:
						interrupted = True
					else:
						all_events[curr]['manufact'] = manufact
						link = 4
				elif link == 4:
					try:  # if 'SerialNumber: ' in logline
						serial = re_serial.search(logline).group(1)
					except AttributeError:
						pass
					else:
						all_events[curr]['serial'] = serial
					finally:
						interrupted = True

			else:
				continue

		elif action == 'd':
			try:
				port = re_port.search(logline).group(1)
			except AttributeError:
				pass
			else:
				for i in range(len(all_events)-1, -1, -1):
					if all_events[i]['port'] == port:
						all_events[i]['disconn'] = date
						break

	return all_events


'''
def _sort_by_date(unsorted_log):
	"""For old syslog format."""
	# "usorted_log" is a list of ( ('Mon dd hh:mm:ss', 'EVENT'), ['LOG_DATA'] )
	return sorted(unsorted_log, key=lambda i: MONTH_ENUM[i[0][0][:3]] + i[0][0][3:])
'''


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

	return all(
		compare(current_element, next_element)
		for current_element, next_element
		in pairwise(iterable)
	)


def _filter_events(all_events, sieve):
	# default_sieve = {
	#    'external': False,
	#    'dates':       [],
	#    'fields':      {},
	#    'number':      -1
	# }

	if sieve is None or sieve == {'external': False, 'dates': [], 'fields': {}, 'number': -1}:
		return all_events

	else:
		print_info('Filtering events')

		events_by_external = []
		if sieve['external']:
			for event in all_events:
				if event['disconn'] is not None:
					events_by_external.append(event)
					continue
		else:
			events_by_external = all_events

		events_by_date = []
		if sieve['dates']:
			for event in all_events:
				for date in sieve['dates']:
					if event['conn'].startswith(date):
						events_by_date.append(event)
						break
				continue
		else:
			events_by_date = all_events

		event_intersection = intersect_event_sets(events_by_external, events_by_date)

		events_to_show = []
		if sieve['fields']:
			for event in event_intersection:
				for key, vals in sieve['fields'].items():
					if any(event[key] == val for val in vals):
						events_to_show.append(event)
						break
		else:
			events_to_show = event_intersection

		if not events_to_show:
			return []

		SIZE = len(events_to_show)
		if sieve['number'] <= -1 or sieve['number'] > SIZE:
			if sieve['number'] < -1:
				print_warning(
					f'usbrip can\'t handle dark matter \"--number={sieve["number"]}\", so it will show '
					f'all {SIZE} USB history entries available'
				)

			elif sieve['number'] > SIZE:
				print_warning(
					f'USB history has only {SIZE} entries instead of requested {sieve["number"]}, '
					f'displaying all of them...'
				)

			sieve['number'] = SIZE

		return [events_to_show[SIZE-i] for i in range(sieve['number'], 0, -1)]


def _represent_events(events_to_show, columns, table_data, title, repres):
	print_info('Preparing collected events')

	if repres is None:
		repres = {
			'table': False,
			'list':  False,
			'smart':  True
		}

	max_len = {
		'conn':     19,
		'host':     max(max(len(event['host']) for event in events_to_show), len('Host')),
		'vid':       4,
		'pid':       4,
		'prod':     max(max(len(str(event['prod'])) for event in events_to_show), len('Product')),
		'manufact': max(max(len(str(event['manufact'])) for event in events_to_show), len('Manufacturer')),
		'serial':   max(max(len(str(event['serial'])) for event in events_to_show), len('Serial Number')),
		'port':     max(max(len(event['port']) for event in events_to_show), len('Port')),
		'disconn':  19
	}

	prev_cday = ''
	for event in events_to_show:
		if 'conn' in columns:
			curr_cday = event['conn'][:10]
			if prev_cday != curr_cday:
				cday = [f'{curr_cday} {BULLET * (len(event["conn"])-len(curr_cday)-1)}']
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
		print_info('Representation: table')
		print('\n' + event_table.table)

	# Display as list
	elif not cfg.ISATTY or (repres['smart'] and not event_table.ok or repres['list']):
		if not event_table.ok:
			print_warning('Terminal window is too small to display table properly')
			print_warning('Representation: list')
		else:
			print_info('Representation: list')

		max_len = max(len(str(val)) for event in events_to_show for val in event.values()) + len('Serial Number:  ')  # max length string
		if not max_len // 2:
			max_len += 1

		if cfg.ISATTY:
			cprint('\n' + title, 'white', attrs=['bold'])
		else:
			print('\n' + title)

		print(SEPARATOR * max_len)

		for event in events_to_show:
			if cfg.ISATTY:
				print(colored('Connected:      ', 'magenta', attrs=['bold']) + colored(event['conn'], 'green'))
				print(colored('Host:           ', 'magenta', attrs=['bold']) + event['host'])
				print(colored('VID:            ', 'magenta', attrs=['bold']) + event['vid'])
				print(colored('PID:            ', 'magenta', attrs=['bold']) + event['pid'])
				print(colored('Product:        ', 'magenta', attrs=['bold']) + str(event['prod']))
				print(colored('Manufacturer:   ', 'magenta', attrs=['bold']) + str(event['manufact']))
				print(colored('Serial Number:  ', 'magenta', attrs=['bold']) + str(event['serial']))
				print(colored('Bus-Port:       ', 'magenta', attrs=['bold']) + event['port'])
				print(colored('Disconnected:   ', 'magenta', attrs=['bold']) + colored(event['disconn'], 'red'))
			else:
				print('Connected:      ' + event['conn'])
				print('Host:           ' + event['host'])
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


def _dump_events(events_to_show, list_name, abs_filename, indent):
	print_info(f'Generating {list_name} list (JSON)')

	out = []
	for event in events_to_show:
		tmp_event_dict = OrderedDict()

		for key in ('conn', 'host', 'vid', 'pid', 'prod', 'manufact', 'serial', 'port', 'disconn'):
			tmp_event_dict[key] = event[key]

		out.append(tmp_event_dict)

	try:
		with open(abs_filename, 'w', encoding='utf-8') as out_json:
			json.dump(out, out_json, indent=indent)

	except PermissionError as e:
		raise USBRipError(
			f'Permission denied: "{abs_filename}". Retry with sudo',
			errors={'initial_error': str(e)}
		)

	os.chmod(abs_filename, stat.S_IRUSR | stat.S_IWUSR)  # 600

	print_info(f'New {list_name} list: "{abs_filename}"')


def _output_choice(list_name, default_filename):
	while True:
		print(f'[?] How would you like your {list_name} list to be generated?\n')

		print('    1. Terminal stdout')
		print('    2. JSON-file')

		choice = input('\n[>] Please enter the number of your choice (default 1): ')

		if choice == '1' or choice == '':
			return (choice, '')

		elif choice == '2':
			while True:
				filename = input(
					f'[>] Please enter the output file name '
					f'(default is "{default_filename}"): '
				)

				if all(c in printable for c in filename) and len(filename) < 256:
					if not filename:
						filename = default_filename
					elif os.path.splitext(filename)[-1] != '.json':
						filename = filename + '.json'

					abs_filename = os.path.join(os.path.abspath(os.getcwd()), filename)

					overwrite = True
					if os.path.isfile(abs_filename):
						while True:
							overwrite = input('[?] File exists. Would you like to overwrite it? [Y/n]: ')
							if len(overwrite) == 1 and overwrite in 'Yy' or overwrite == '':
								overwrite = True
								break
							elif len(overwrite) == 1 and overwrite in 'Nn':
								overwrite = False
								break

					if overwrite:
						return (choice, abs_filename)
