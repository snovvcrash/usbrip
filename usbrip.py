#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
@file usbrip.py
@author Sam Freeside <snovvcrash@protonmail.com>
@date 2018-03

@brief usbrip project's driver program

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

from argparse import ArgumentParser

from lib import USBEvents
from lib import USBIDs

from lib.cliopts import cmd_line_options
from lib.common import BANNER
from lib.common import COLUMN_NAMES
from lib.common import USBRipError
from lib.common import print_critical

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
				for name in args.column:
					if name not in COLUMN_NAMES.keys():
						usbrip_error(name + ': Invalid column name')

		if 'date' in args and args.date:
			re_date = re.compile(r'^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) [\s1-3][0-9]$')
			for date in args.date:
				if not re_date.search(date):
					usbrip_error(date + ': Wrong date format')

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

		# ---------------- USB Events Gen Auth JSON ----------------

		elif args.ue_subparser == 'gen_auth':
			if os.path.exists(args.output):
				usbrip_error(args.output + ': Path already exists')

			ueg = USBEvents(args.file, quiet=args.quiet)
			ueg.generate_auth_json(args.output, sieve=sieve)

		# ----------------- USB Events Violations ------------------

		elif args.ue_subparser == 'violations':
			if not os.path.exists(args.input):
				usbrip_error(args.input + ': Path does not exist')

			uev = USBEvents(args.file, quiet=args.quiet)
			uev.search_violations(args.input, args.column, sieve=sieve, repres=repres)

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
				print_critical(str(e), errcode=e.errors['errcode'], initial_error=e.error['initial_error'])
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
