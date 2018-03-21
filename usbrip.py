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
	print(BANNER)
	
	if not len(sys.argv) > 1:
		usbrip_error('No arguments were passed')

	parser = cmd_line_options()
	args = parser.parse_args()

	# ----------------------------------------------------------
	# ----------------------- USB Events -----------------------
	# ----------------------------------------------------------

	if args.subparser == 'events' and args.ue_subparser:
		if args.files:
			for file in args.files:
				if not os.path.exists(file):
					usbrip_error(file + ': Path does not exist')

		if args.dates:
			re_date = re.compile(r'^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) [\s1-3][0-9]$')
			for date in args.dates:
				if not re_date.search(date):
					usbrip_error(date + ': Wrong date format')

		sieve = dict(zip(('external', 'dates', 'number'), (args.external, args.dates, args.number)))

		# ------------------- USB Events History -------------------

		if args.ue_subparser == 'history':
			if args.columns:
				for name in args.columns:
					if name not in COLUMN_NAMES.keys():
						usbrip_error(name + ': Invalid column name')

			repres = dict.fromkeys(('table', 'list', 'smart'), False)

			if args.table:
				repres['table'] = True
			elif args.list:
				repres['list'] = True
			else:
				repres['smart'] = True

			ueh = USBEvents(args.files)
			ueh.event_history(args.columns, sieve=sieve, repres=repres, quiet=args.quiet)

		# ---------------- USB Events Gen Auth JSON ----------------

		elif args.ue_subparser == 'gen_auth':
			if os.path.exists(args.output):
				usbrip_error(args.output + ': Path already exists')

			ueg = USBEvents(args.files)
			ueg.generate_auth_json(args.output)

		# ----------------- USB Events Violations ------------------

		elif args.ue_subparser == 'violations':
			if not os.path.exists(args.input):
				usbrip_error(args.input + ': Path does not exist')

			repres = dict.fromkeys(('table', 'list', 'smart'), False)

			if args.table:
				repres['table'] = True
			elif args.list:
				repres['list'] = True
			else:
				repres['smart'] = True

			uev = USBEvents(args.files)
			uev.search_violations(args.input, sieve=sieve, repres=repres, quiet=args.quiet)

	# ----------------------------------------------------------
	# ------------------------ USB IDs -------------------------
	# ----------------------------------------------------------

	elif args.subparser == 'ids' and args.ui_subparser:
		ui = USBIDs()

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
