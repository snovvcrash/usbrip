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
USB Vendor/Device IDs Database - Linux-USB.org
	http://www.linux-usb.org/usb.ids
'''

__author__ = 'Sam Freeside (@snovvcrash)'
__email__  = 'snovvcrash@protonmail[.]ch'
__site__   = 'https://github.com/snovvcrash/usbrip'
__brief__  = 'USB IDs handler'

import re
import socket
import os
from pathlib import Path

from urllib.request import urlopen

import usbrip.lib.core.config as cfg
from usbrip.lib.core.common import os_makedirs
from usbrip.lib.core.common import print_info
from usbrip.lib.core.common import print_warning
from usbrip.lib.core.common import print_critical
from usbrip.lib.core.common import USBRipError
from usbrip.lib.utils.debug import time_it
from usbrip.lib.utils.debug import time_it_if_debug


# ----------------------------------------------------------
# ------------------------ USB IDs -------------------------
# ----------------------------------------------------------


class USBIDs:

	_INTERNET_CONNECTION_ERROR = -1
	_SERVER_TIMEOUT_ERROR      = -2
	_SERVER_CONTENT_ERROR      = -3

	@staticmethod
	@time_it_if_debug(cfg.DEBUG, time_it)
	def search_ids(vid, pid, *, offline=True):
		if offline:
			print_warning('Offline mode')

		try:
			usb_ids = USBIDs.prepare_database(offline=offline)
		except USBRipError as e:
			print_critical(str(e), errcode=e.errors['errcode'], initial_error=e.errors['initial_error'])
		else:
			_search_ids_helper(usb_ids, vid, pid)
			usb_ids.close()

	@staticmethod
	@time_it_if_debug(cfg.DEBUG, time_it)
	def prepare_database(*, offline=True):
		filename = f'{os.path.abspath(str(Path.home()))}/.config/usbrip/usb.ids'
		file_exists = os.path.isfile(filename)

		if file_exists and offline:
			usb_ids = open(filename, 'r', encoding='utf-8')
		elif file_exists and not offline:
			usb_ids = _update_database(filename)
		elif not file_exists and not offline:
			print_warning('No local database found, trying to download')
			usb_ids = _download_database(filename)
		elif not file_exists and offline:
			raise USBRipError('No local database found')

		return usb_ids


# ----------------------------------------------------------
# ----------------------- Utilities ------------------------
# ----------------------------------------------------------


def _update_database(filename):
	try:
		usb_ids = open(filename, 'r+', encoding='utf-8')
	except PermissionError as e:
		raise USBRipError(
			f'Permission denied: "{filename}"',
			errors={'initial_error': str(e)}
		)

	print_info('Getting current database version')
	curr_ver, curr_date = _get_current_version(usb_ids)
	print(f'Version:  {curr_ver}')
	print(f'Date:     {curr_date}')

	print_info('Checking local database for update')
	db, latest_ver, latest_date, errcode, e = _get_latest_version()

	if errcode:
		if errcode == USBIDs._INTERNET_CONNECTION_ERROR:
			print_warning(
				'No internet connection, using current version',
				errcode=errcode
			)

		elif errcode == USBIDs._SERVER_TIMEOUT_ERROR:
			print_warning(
				'Server timeout, using current version',
				errcode=errcode,
				initial_error=e
			)

		elif errcode == USBIDs._SERVER_CONTENT_ERROR:
			print_warning(
				'Server error, using current version',
				errcode=errcode,
				initial_error=e
			)

		return usb_ids

	if curr_ver != latest_ver and curr_date != latest_date:  # if there's newer database version
		print('Updating database... ', end='')

		usb_ids.write(db)
		usb_ids.truncate()
		usb_ids.seek(0)

		print('Done\n')

		print(f'Version:  {latest_ver}')
		print(f'Date:     {latest_date}')

	print_info('Local database is up-to-date')

	return usb_ids


def _download_database(filename):
	try:
		dirname = os.path.dirname(filename)
		os_makedirs(dirname)
	except USBRipError as e:
		raise USBRipError(str(e), errors={'initial_error': e.errors['initial_error']})
	else:
		print_info(f'Created directory "{dirname}/"')

	try:
		usb_ids = open(filename, 'w+', encoding='utf-8')
	except PermissionError as e:
		raise USBRipError(
			f'Permission denied: "{filename}"',
			errors={'initial_error': str(e)}
		)

	db, latest_ver, latest_date, errcode, e = _get_latest_version()

	if errcode:
		usb_ids.close()
		os.remove(filename)

		if errcode == USBIDs._INTERNET_CONNECTION_ERROR:
			errmsg = 'No internet connection'
		elif errcode == USBIDs._SERVER_TIMEOUT_ERROR:
			errmsg = 'Server timeout'
		elif errcode == USBIDs._SERVER_CONTENT_ERROR:
			errmsg = 'Server content error: no version or date found'

		raise USBRipError(errmsg, errors={'errcode': errcode, 'initial_error': e})

	usb_ids.write(db)
	usb_ids.seek(0)

	print_info('Database downloaded')

	print(f'Version:  {latest_ver}')
	print(f'Date:     {latest_date}')

	return usb_ids


def _get_current_version(usb_ids):
	db = usb_ids.read()
	usb_ids.seek(0)

	try:
		curr_ver = re.search(r'^# Version:\s*(.*?$)', db, re.MULTILINE).group(1)
		curr_date = re.search(r'^# Date:\s*(.*?$)', db, re.MULTILINE).group(1)
	except AttributeError as e:
		raise USBRipError(
			'Invalid database content structure: no version or date found',
			errors={'initial_error': str(e)}
		)

	return (curr_ver, curr_date)


def _get_latest_version():
	connected, errcode, e = _check_connection('www.google.com')
	if not connected:
		return (None, -1, -1, errcode, e)

	print_info('Getting latest version and date')

	try:
		html = urlopen('http://www.linux-usb.org/usb.ids', timeout=10).read()
		#from requests import get
		#resp = get('http://www.linux-usb.org/usb.ids', timeout=10)
	except socket.timeout as e:
	#except requests.exceptions.Timeout as e:
		return (None, -1, -1, USBIDs._SERVER_TIMEOUT_ERROR, str(e))

	db = html.decode('cp1252')
	#soup = BeautifulSoup(resp.text, 'html.parser')
	#db = soup.text

	try:
		latest_ver  = re.search(r'^# Version:\s*(.*?$)', db, re.MULTILINE).group(1)
		latest_date = re.search(r'^# Date:\s*(.*?$)', db, re.MULTILINE).group(1)
	except AttributeError as e:
		return (None, -1, -1, USBIDs._SERVER_CONTENT_ERROR, str(e))

	return (db, latest_ver, latest_date, 0, '')


def _check_connection(hostname):
	try:
		host = socket.gethostbyname(hostname)
		socket.create_connection((host, 80), 2)
		return (True, 0, '')
	except Exception as e:
		return (False, USBIDs._INTERNET_CONNECTION_ERROR, str(e))


def _search_ids_helper(usb_ids, vid, pid):
	print('Searching for matches... ', end='')

	if vid and pid:
		re_vid = re.compile(rf'^{vid}  (.*?$)')
		re_pid = re.compile(rf'^\t{pid}  (.*?$)')

		for line in iter(usb_ids.readline, ''):
			vid_match = re_vid.match(line)
			if vid_match:
				for subline in iter(usb_ids.readline, ''):
					if subline[0] == '\t':
						pid_match = re_pid.match(subline)
						if pid_match:
							print('Done\n')
							print(f'Vendor:   {vid_match.group(1)}')
							print(f'Product:  {pid_match.group(1)}')
							break
					else:
						print('Done\n')
						print('No such pair of (vendor, product) found')
						break
				print()
				return

		print('Done\n')
		print('No such vendor found')

	else:  # if (vid and not pid) or (pid and not vid):
		if vid and not pid:
			matches = re.findall(rf'^{vid}  (.*?$)', usb_ids.read(), re.MULTILINE)
		else:  # if pid and not vid
			matches = re.findall(rf'^\t{pid}  (.*?$)', usb_ids.read(), re.MULTILINE)

		print('Done\n')
		print('| Possible products:')

		if not matches:
			print('|_    no results')
		else:
			for i, match in enumerate(matches):
				if i != len(matches)-1:
					print(f'|     {match}')
				else:
					print(f'|_    {match}')

	print()
