#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Usage: python3 usbrip.py [-h]

"""LICENSE

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
"""

__author__ = 'Sam Freeside (@snovvcrash)'
__email__  = 'snovvcrash@protonmail[.]ch'

__date__  = '2018-03-21'
__site__  = 'https://github.com/snovvcrash/usbrip'
__brief__ = 'usbrip project\'s driver program.'


import re
import os
import sys

try:
	import usbrip.lib.core.config as cfg
	cfg.DEBUG = '--debug' in sys.argv

	import usbrip.lib.utils.timing as timing

	from usbrip.lib.core.usbevents import USBEvents
	from usbrip.lib.core.usbstorage import USBStorage
	from usbrip.lib.core.usbids import USBIDs

except PermissionError:
	sys.exit('Permission denied. Retry with sudo')

from usbrip.lib.core.common import BANNER
from usbrip.lib.core.common import COLUMN_NAMES
from usbrip.lib.core.common import is_correct
from usbrip.lib.core.common import print_critical
from usbrip.lib.core.common import USBRipError
from usbrip.lib.parse.cliopts import cmd_line_options


# ----------------------------------------------------------
# -------------------------- Main --------------------------
# ----------------------------------------------------------


def main():
	if not len(sys.argv) > 1:
		print(BANNER + '\n')
		usbrip_arg_error()

	parser = cmd_line_options()
	args = parser.parse_args()

	if 'quiet' in args and not args.quiet:
		print(BANNER + '\n')
	else:
		cfg.QUIET = True

	# ----------------------------------------------------------
	# ------------------------- Banner -------------------------
	# ----------------------------------------------------------

	if args.subparser == 'banner':
		print(BANNER)

	# ----------------------------------------------------------
	# ----------------------- USB Events -----------------------
	# ----------------------------------------------------------

	elif args.subparser == 'events' and args.ue_subparser:
		sieve, repres = validate_ue_args(args)

		# ------------------- USB Events History -------------------

		if args.ue_subparser == 'history':
			timing.begin()
			ueh = USBEvents(args.file)
			if ueh:
				ueh.event_history(
					args.column,
					sieve=sieve,
					repres=repres
				)

		# -------------------- USB Events Open ---------------------

		elif args.ue_subparser == 'open':
			timing.begin()
			USBEvents.open_dump(
				args.input,
				args.column,
				sieve=sieve,
				repres=repres
			)

		# ------------------ USB Events Gen Auth -------------------

		elif args.ue_subparser == 'gen_auth':
			timing.begin()
			ueg = USBEvents(args.file)
			if ueg:
				if ueg.generate_auth_json(
					args.output,
					args.attribute,
					sieve=sieve
				):
					usbrip_internal_error()
			else:
				usbrip_internal_error()

		# ----------------- USB Events Violations ------------------

		elif args.ue_subparser == 'violations':
			timing.begin()
			uev = USBEvents(args.file)
			if uev:
				uev.search_violations(
					args.input,
					args.attribute,
					args.column,
					sieve=sieve,
					repres=repres
				)

	# ----------------------------------------------------------
	# ---------------------- USB Storage -----------------------
	# ----------------------------------------------------------

	elif args.subparser == 'storage' and args.us_subparser:
		if os.geteuid() != 0:
			sys.exit('Permission denied. Retry with sudo')

		sieve, repres = validate_us_args(args)
		timing.begin()
		us = USBStorage()

		# -------------------- USB Storage List --------------------

		if args.us_subparser == 'list':
			us.list_storage(
				args.storage_type,
				args.password
			)

		# -------------------- USB Storage Open --------------------

		elif args.us_subparser == 'open':
			us.open_storage(
				args.storage_type,
				args.password,
				args.column,
				sieve=sieve,
				repres=repres
			)

		# ------------------- USB Storage Update -------------------

		elif args.us_subparser == 'update':
			if us.update_storage(
				args.storage_type,
				args.password,
				input_auth=args.input,
				attributes=args.attribute,
				compression_level=args.lvl,
				sieve=sieve
			):
				usbrip_internal_error()

		# ------------------- USB Storage Create -------------------

		elif args.us_subparser == 'create':
			if us.create_storage(
				args.storage_type,
				password=args.password,
				input_auth=args.input,
				attributes=args.attribute,
				compression_level=args.lvl,
				sieve=sieve
			):
				usbrip_internal_error()

		# ------------------- USB Storage Passwd -------------------

		elif args.us_subparser == 'passwd':
			us.change_password(
				args.storage_type,
				args.old,
				args.new,
				compression_level=args.lvl
			)

	# ----------------------------------------------------------
	# ------------------------ USB IDs -------------------------
	# ----------------------------------------------------------

	elif args.subparser == 'ids' and args.ui_subparser:
		validate_ui_args(args)
		timing.begin()
		ui = USBIDs()

		# --------------------- USB IDs Search ---------------------

		if args.ui_subparser == 'search':
			ui.search_ids(
				args.vid,
				args.pid,
				offline=args.offline
			)

		# -------------------- USB IDs Download --------------------

		elif args.ui_subparser == 'download':
			try:
				usb_ids = ui.prepare_database(offline=False)
			except USBRipError as e:
				print_critical(str(e), errcode=e.errors['errcode'], initial_error=e.errors['initial_error'])
			else:
				usb_ids.close()

	else:
		subparser = ' ' + args.subparser + ' '
		usbrip_arg_error('Choose one of the usbrip {} actions'.format(args.subparser), subparser=subparser)


# ----------------------------------------------------------
# ------------------ Argument validation -------------------
# ----------------------------------------------------------

# ----------------------- USB Events -----------------------


def validate_ue_args(args):
	_validate_column_args(args)
	_validate_attribute_args(args)
	_validate_io_args(args)
	_validate_file_args(args)

	return (_validate_sieve_args(args), _validate_repres_args(args))


# ---------------------- USB Storage -----------------------


def validate_us_args(args):
	_validate_storage_type_args(args)
	_validate_password_args(args)
	_validate_compression_level_args(args)
	_validate_io_args(args)
	_validate_attribute_args(args)

	return (_validate_sieve_args(args), _validate_repres_args(args))


# ------------------------ USB IDs -------------------------


def validate_ui_args(args):
	_validate_vid_pid_args(args)


# ----------------------------------------------------------
# ---------------- Error Message Generators ----------------
# ----------------------------------------------------------


def usbrip_arg_error(message=None, *, subparser=' '):
	if message:
		print('Usage: python3 {}{}[-h]\n'.format(sys.argv[0], subparser))
		print(sys.argv[0].rsplit('/', 1)[-1] + ': argument error: ' + message, file=sys.stderr)
	else:
		print('Usage: python3 {} [-h]'.format(sys.argv[0]))

	sys.exit(1)


def usbrip_internal_error():
	print(sys.argv[0].rsplit('/', 1)[-1] + ': Internal error occured', file=sys.stderr)
	sys.exit(1)


# ----------------------------------------------------------
# ----------------------- Utilities ------------------------
# ----------------------------------------------------------


def _validate_column_args(args):
	if 'column' in args and args.column:
		for column in args.column:
			if column not in COLUMN_NAMES.keys():
				usbrip_arg_error(column + ': Invalid column name')


def _validate_sieve_args(args):
	if 'external' in args:
		sieve = dict(zip(('external', 'number', 'dates', 'fields'),
                         (args.external, args.number, args.date, {})))

		if args.date:
			re_date = re.compile(r'^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+[1-3]?[0-9]$')
			for i in range(len(args.date)):
				if not re_date.search(args.date[i]):
					usbrip_arg_error(args.date[i] + ': Wrong date format')
				date_parts = args.date[i].split()
				args.date[i] = ' '.join(date_parts) if len(date_parts[-1]) == 2 else '  '.join(date_parts)

		if args.user:
			sieve['fields']['user'] = args.user
		if args.vid:
			sieve['fields']['vid'] = args.vid
		if args.pid:
			sieve['fields']['pid'] = args.pid
		if args.prod:
			sieve['fields']['prod'] = args.prod
		if args.manufact:
			sieve['fields']['manufact'] = args.manufact
		if args.serial:
			sieve['fields']['serial'] = args.serial
		if args.port:
			sieve['fields']['port'] = args.port

		return sieve

	return None


def _validate_repres_args(args):
	if 'table' in args or 'list' in args:
		repres = dict.fromkeys(('table', 'list', 'smart'), False)

		if 'table' in args and args.table:
			repres['table'] = True
		elif 'list' in args and args.list:
			repres['list'] = True
		else:
			repres['smart'] = True

		return repres

	return None


def _validate_io_args(args):
	if 'input' in args and args.input:
		if not os.path.exists(args.input):
			usbrip_arg_error(args.input + ': Path does not exist')
		elif not os.path.isfile(args.input):
			usbrip_arg_error(args.input + ': Not a regular file')

	if 'output' in args and os.path.exists(args.output):
		usbrip_arg_error(args.output + ': Path already exists')


def _validate_attribute_args(args):
	if 'attribute' in args and args.attribute:
		for attribute in args.attribute:
			if attribute not in ('vid', 'pid', 'prod', 'manufact', 'serial'):
				usbrip_arg_error(attribute + ': Invalid attribute name')


def _validate_storage_type_args(args):
	if args.storage_type not in ('history', 'violations'):
		usbrip_arg_error(args.storage_type + ': Invalid storage type')

	if args.storage_type == 'history':
		if 'input' in args and args.input:
			usbrip_arg_error('Cannot use \'--input\' swith with history storage')
		if 'attribute' in args and args.attribute:
			usbrip_arg_error('Cannot use \'--attribute\' swith with history storage')
	elif args.storage_type == 'violations':
		if 'input' in args and args.input is None:
			usbrip_arg_error('Please specify input path for the list of authorized devices (-i)')


def _validate_password_args(args):
	errmsg = ': Password must be at least 8 chars long and contain at least ' \
             '1 lowercase letter, at least 1 uppercase letter and at least '  \
             '1 digit'

	if 'password' in args and args.password and not is_correct(args.password):
		usbrip_arg_error(args.password + errmsg)

	if 'new' in args and args.new and not is_correct(args.new):
		usbrip_arg_error(args.new + errmsg)

	if 'old' in args and args.old and not is_correct(args.old):
		usbrip_arg_error(args.old + errmsg)


def _validate_compression_level_args(args):
	if 'lvl' in args and args.lvl and (len(args.lvl) > 1 or args.lvl not in '0123456789'):
		usbrip_arg_error(args.lvl + ': Invalid compression level')


def _validate_file_args(args):
	if 'file' in args and args.file:
		for file in args.file:
			if not os.path.exists(file):
				usbrip_arg_error(file + ': Path does not exist')
			elif not os.path.isfile(file):
				usbrip_arg_error(file + ': Not a regular file')


def _validate_vid_pid_args(args):
	if 'vid' in args and 'pid' in args and not args.vid and not args.pid:
		usbrip_arg_error('At least one of --vid/--pid or --download option should be specified')
