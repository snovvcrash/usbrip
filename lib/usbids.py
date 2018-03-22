#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
@file usbids.py
@author Sam Freeside <snovvcrash@protonmail.com>
@date 2018-03

@brief USB IDs handler

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
vendor ID - Linux-USB.org
	http://www.linux-usb.org/usb.ids
systemd/usb.ids at master · systemd/systemd
	https://raw.githubusercontent.com/systemd/systemd/master/hwdb/usb.ids
"""

import re
import socket
import requests
import os
import sys

from bs4 import BeautifulSoup

from lib.common import root_dir_join
from lib.common import os_makedirs
from lib.common import print_info
from lib.common import print_warning
from lib.common import print_critical
from lib.common import USBRipError
from lib.common import DEBUG
from lib.common import time_it
from lib.common import time_it_if_debug

# ----------------------------------------------------------
# ------------------------ USB IDs -------------------------
# ----------------------------------------------------------

class USBIDs:

	_INTERNET_CONNECTION_ERROR = -1
	_SERVER_TIMEOUT_ERROR      = -2
	_SERVER_CONTENT_ERROR      = -3

	@staticmethod
	@time_it_if_debug(DEBUG, time_it)
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
	@time_it_if_debug(DEBUG, time_it)
	def prepare_database(*, offline=True):
		filename = root_dir_join('usb_ids/usb.ids')
		file_exists = os.path.isfile(filename)

		if file_exists and offline:
			usb_ids = open(filename, 'r')
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
		usb_ids = open(filename, 'r+')
	except PermissionError as e:
		print_critical('Permission denied: \'{}\''.format(filename), initial_error=str(e))
		return

	print_info('Getting current database version')
	curr_ver, curr_date = _get_current_version(usb_ids)
	print('Version:  {}'.format(curr_ver))
	print('Date:     {}'.format(curr_date))

	print_info('Checking local database for update')
	db, latest_ver, latest_date, error, e = _get_latest_version()

	if error:
		if error == USBIDs._INTERNET_CONNECTION_ERROR:
			print_warning('No internet connection, using current version', errcode=error)
		elif error == USBIDs._SERVER_TIMEOUT_ERROR:
			print_warning('Server timeout, using current version', errcode=error, initial_error=e)
		elif error == USBIDs._SERVER_CONTENT_ERROR:
			print_warning('Server error, using current version', errcode=error, initial_error=e)
		return usb_ids

	if curr_ver != latest_ver and curr_date != latest_date:  # if there's newer database version
		print('Updating database... ', end='')

		usb_ids.write(db)
		usb_ids.seek(0)
		usb_ids.truncate()

		print('Done\n')

		print('Version:  {}'.format(latest_ver))
		print('Date:     {}'.format(latest_date))

	print_info('Local database is up-to-date')

	return usb_ids

def _download_database(filename):
	try:
		os_makedirs(os.path.dirname(filename))
	except USBRipError as e:
		print_critical(str(e), initial_error=e.errors['initial_error'])
		return

	try:
		usb_ids = open(filename, 'w+')
	except PermissionError as e:
		print_critical('Permission denied: \'{}\''.format(filename), initial_error=str(e))
		return

	db, latest_ver, latest_date, error, e = _get_latest_version()

	if error:
		usb_ids.close()
		os.remove(filename)
		if error == USBIDs._INTERNET_CONNECTION_ERROR:
			raise USBRipError('No internet connection')
		elif error == USBIDs._SERVER_TIMEOUT_ERROR:
			raise USBRipError('Server timeout', errors={'errcode': error, 'initial_error': e} )
		elif error == USBIDs._SERVER_CONTENT_ERROR:
			raise USBRipError('Server content error: no version or date found',
                              errors={'errcode': error, 'initial_error': e} )

	usb_ids.write(db)
	usb_ids.seek(0)

	print_info('Database downloaded')

	print('Version:  {}'.format(latest_ver))
	print('Date:     {}'.format(latest_date))

	return usb_ids

def _get_current_version(usb_ids):
	db = usb_ids.read()
	usb_ids.seek(0)

	try:
		curr_ver = re.search(r'^# Version:\s*(.*?$)', db, re.MULTILINE).group(1)
		curr_date = re.search(r'^# Date:\s*(.*?$)', db, re.MULTILINE).group(1)
	except AttributeError as e:
		raise USBRipError('Invalid database content structure: no version or date found',
                          errors={'initial_error': str(e)} )

	return (curr_ver, curr_date)

def _get_latest_version():
	connected, error, e = _check_connection('www.google.com')
	if not connected:
		return (None, -1, -1, error, e)

	print_info('Getting latest version and date')

	try:
		resp = requests.get('http://www.linux-usb.org/usb.ids', timeout=10)
	except requests.exceptions.Timeout as e:
		return (None, -1, -1, USBIDs._SERVER_TIMEOUT_ERROR, str(e))

	soup = BeautifulSoup(resp.text, 'html.parser')
	db = soup.text
	
	try:
		latest_ver  = re.search(r'^# Version:\s*(.*?$)', db, re.MULTILINE).group(1)
		latest_date = re.search(r'^# Date:\s*(.*?$)', db, re.MULTILINE).group(1)
	except AttributeError as e:
		return (None, -1, -1, USBIDs._SERVER_CONTENT_ERROR, str(e))

	return (db, latest_ver, latest_date, 0, '')

def _check_connection(hostname):
	try:
		host = socket.gethostbyname(hostname)
		s = socket.create_connection((host, 80), 2)
		return (True, 0, '')
	except Exception as e:
		return (False, USBIDs._INTERNET_CONNECTION_ERROR, str(e))

def _search_ids_helper(usb_ids, vid, pid):
	print('Searching for matches... ', end='')

	if vid and pid:
		re_vid = re.compile(r'^{}  (.*?$)'.format(vid))
		re_pid = re.compile(r'^\t{}  (.*?$)'.format(pid))

		for line in iter(usb_ids.readline, ''):
			vid_match = re_vid.match(line)
			if vid_match:
				for subline in iter(usb_ids.readline, ''):
					if subline[0] == '\t':
						pid_match = re_pid.match(subline)
						if pid_match:
							print('Done\n')
							print('Vendor:   {}'.format(vid_match.group(1)))
							print('Product:  {}'.format(pid_match.group(1)))
							break
					else:
						print('Done\n')
						print('No such pair of (vendor, product) found')
						break
				return

		print('Done\n')
		print('No such vendor found')

	else:  # if (vid and not pid) or (pid and not vid):
		if vid and not pid:
			matches = re.findall(r'^{}  (.*?$)'.format(vid), usb_ids.read(), re.MULTILINE)
		else:  # if pid and not vid
			matches = re.findall(r'^\t{}  (.*?$)'.format(pid), usb_ids.read(), re.MULTILINE)

		print('Done\n')
		print('| Possible products:')

		if not matches:
			print('|_    no results')
		else:
			for i, match in enumerate(matches):
				if i != len(matches)-1:
					print('|     {}'.format(match))
				else:
					print('|_    {}'.format(match))
