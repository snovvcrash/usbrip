#!/opt/usbrip/venv/bin/python
# -*- coding: UTF-8 -*-

"""
@file usbrip.py
@author Sam Freeside <snovvcrash@protonmail.com>
@date 2018-03

@brief usbrip project's driver program.

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

import re
import os
import sys

from lib.core import USBEvents
from lib.core import USBIDs

from lib.core.cliopts import cmd_line_options
from lib.core.common import BANNER
from lib.core.common import COLUMN_NAMES
from lib.core.common import USBRipError
from lib.core.common import print_critical


# ----------------------------------------------------------
# ------------------- Error Message Gen --------------------
# ----------------------------------------------------------


def usbrip_error(message, *, subparser=' '):
	print('usage: python3 {}{}[-h]\n'.format(sys.argv[0], subparser))
	print(sys.argv[0].rsplit('/', 1)[-1] + ': error: ' + message, file=sys.stderr)
	sys.exit(1)


# ----------------------------------------------------------
# -------------------------- Main --------------------------
# ----------------------------------------------------------


def main():
	if not len(sys.argv) > 1:
		print(BANNER + '\n')
		usbrip_error('No arguments were passed')

	parser = cmd_line_options()
	args = parser.parse_args()

	if 'quiet' in args and not args.quiet:
		print(BANNER + '\n')

	# ----------------------------------------------------------
	# ------------------------- Banner -------------------------
	# ----------------------------------------------------------

	if args.subparser == 'banner':
		print(BANNER)

	# ----------------------------------------------------------
	# ----------------------- USB Events -----------------------
	# ----------------------------------------------------------

	elif args.subparser == 'events' and args.ue_subparser:
		if 'column' in args and args.column:
			for column in args.column:
				if column not in COLUMN_NAMES.keys():
					usbrip_error(column + ': Invalid column name')

		if 'attribute' in args and args.attribute:
			for attribute in args.attribute:
				if attribute not in ('vid', 'pid', 'prod', 'manufact', 'serial'):
					usbrip_error(attribute + ': Invalid attribute name')

		if 'date' in args and args.date:
			re_date = re.compile(r'^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+[1-3]?[0-9]$')
			for i in range(len(args.date)):
				if not re_date.search(args.date[i]):
					usbrip_error(args.date[i] + ': Wrong date format')
				date_parts = args.date[i].split()
				args.date[i] = ' '.join(date_parts) if len(date_parts[-1]) == 2 else '  '.join(date_parts)

		if 'file' in args and args.file:
			for file in args.file:
				if not os.path.exists(file):
					usbrip_error(file + ': Path does not exist')

		sieve = dict(zip(('external', 'number', 'dates'), (args.external, args.number, args.date)))
		repres = dict.fromkeys(('table', 'list', 'smart'), False)

		if 'table' in args and args.table:
			repres['table'] = True
		elif 'list' in args and args.list:
			repres['list'] = True
		else:
			repres['smart'] = True

		# ------------------- USB Events History -------------------

		if args.ue_subparser == 'history':
			ueh = USBEvents(args.file, quiet=args.quiet)
			ueh.event_history(args.column, sieve=sieve, repres=repres)

		# ------------------ USB Events Gen Auth -------------------

		elif args.ue_subparser == 'gen_auth':
			if os.path.exists(args.output):
				usbrip_error(args.output + ': Path already exists')

			ueg = USBEvents(args.file, quiet=args.quiet)
			ueg.generate_auth_json(args.output, args.attribute, sieve=sieve)

		# ----------------- USB Events Violations ------------------

		elif args.ue_subparser == 'violations':
			if not os.path.exists(args.input):
				usbrip_error(args.input + ': Path does not exist')

			uev = USBEvents(args.file, quiet=args.quiet)
			uev.search_violations(args.input, args.attribute, args.column, sieve=sieve, repres=repres)

	# ----------------------------------------------------------
	# ------------------------ USB IDs -------------------------
	# ----------------------------------------------------------

	elif args.subparser == 'ids' and args.ui_subparser:
		ui = USBIDs(quiet=args.quiet)

		# --------------------- USB IDs Search ---------------------

		if args.ui_subparser == 'search':
			if not args.vid and not args.pid:
				usbrip_error('At least one of --vid/--pid or --download option should be specified')

			ui.search_ids(args.vid, args.pid, offline=args.offline)

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
		usbrip_error('Choose one of the usbrip {} actions'.format(args.subparser), subparser=subparser)


# ----------------------------------------------------------
# ------------------------- Start --------------------------
# ----------------------------------------------------------


if __name__ == '__main__':
	main()
