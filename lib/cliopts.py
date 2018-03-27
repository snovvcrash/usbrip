#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
@file cliopts.py
@author Sam Freeside <snovvcrash@protonmail.com>
@date 2018-03

@brief Command line option parser

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

import os

from argparse import ArgumentParser

from lib.common import root_dir_join

def cmd_line_options():
	parser = ArgumentParser()
	subparsers = parser.add_subparsers(dest='subparser')

	# ----------------------------------------------------------
	# ------------------------- Banner -------------------------
	# ----------------------------------------------------------

	ue_parser = subparsers.add_parser('banner',
                                      help='show tool banner')

	# ----------------------------------------------------------
	# ----------------------- USB Events -----------------------
	# ----------------------------------------------------------

	ue_parser = subparsers.add_parser('events',
                                      help='work with USB events')

	ue_subparsers = ue_parser.add_subparsers(dest='ue_subparser')

	# ------------------- USB Events History -------------------

	ueh_parser = ue_subparsers.add_parser('history',
                                          help='show USB event history')

	ueh_parser.add_argument('-q',
                            '--quiet',
                            action='store_true',
                            help='supress banner, info messages and user iteraction')

	ueh_group_table_list = ueh_parser.add_mutually_exclusive_group()

	ueh_group_table_list.add_argument('-t',
                                      '--table',
                                      action='store_true',
                                      help='represent as table (not list)')

	ueh_group_table_list.add_argument('-l',
                                      '--list',
                                      action='store_true',
                                      help='represent as list (not table)')

	ueh_parser.add_argument('-e',
                            '--external',
                            action='store_true',
                            help='show only those devices which have \'disconnect\' date')

	ueh_parser.add_argument('-n',
                            '--number',
                            type=int,
                            default=-1,
                            help='number of events to show')

	ueh_parser.add_argument('-d',
                            '--dates',
                            nargs='+',
                            type=str,
                            default=[],
                            help='filter by DATES')

	ueh_parser.add_argument('-c',
                            '--columns',
                            nargs='+',
                            type=str,
                            default=[],
                            help='columns to show (options: \'conn\', '     \
                                                           '\'user\', '     \
                                                           '\'vid\', '      \
                                                           '\'pid\', '      \
                                                           '\'prod\', '     \
                                                           '\'manufact\', ' \
                                                           '\'serial\', '   \
                                                           '\'port\', '     \
                                                           '\'disconn\'.)')

	ueh_parser.add_argument('-f',
                            '--files',
                            nargs='+',
                            type=str,
                            default=[],
                            help='obtain log from FILES')

    # ---------------- USB Events Gen Auth JSON ----------------

	ueg_parser = ue_subparsers.add_parser('gen_auth',
                                          help='generate authorized device list (JSON)')

	ueg_parser.add_argument('output',
                            type=str,
                            help='set output path')

	ueg_parser.add_argument('-q',
                            '--quiet',
                            action='store_true',
                            help='supress banner, info messages and user iteraction')

	ueg_parser.add_argument('-e',
                            '--external',
                            action='store_true',
                            help='show only those devices which have \'disconnect\' date')

	ueg_parser.add_argument('-n',
                            '--number',
                            type=int,
                            default=-1,
                            help='number of events to show')

	ueg_parser.add_argument('-d',
                            '--dates',
                            nargs='+',
                            type=str,
                            default=[],
                            help='filter by DATES')

	ueg_parser.add_argument('-f',
                            '--files',
                            nargs='+',
                            type=str,
                            default=[],
                            help='obtain log from FILES')

	# ----------------- USB Events Violations ------------------

	uev_parser = ue_subparsers.add_parser('violations',
                                          help='search USB event history for violations ' \
                                               '(show USB devices that do appear in hist' \
                                               'ory and do NOT appear in authorized devi' \
                                               'ce list (JSON))')

	uev_parser.add_argument('input',
                            type=str,
                            help='set input path')

	uev_parser.add_argument('-q',
                            '--quiet',
                            action='store_true',
                            help='supress banner, info messages and user iteraction')

	uev_group_table_list = uev_parser.add_mutually_exclusive_group()

	uev_group_table_list.add_argument('-t',
                                      '--table',
                                      action='store_true',
                                      help='represent as table (not list)')

	uev_group_table_list.add_argument('-l',
                                      '--list',
                                      action='store_true',
                                      help='represent as list (not table)')

	uev_parser.add_argument('-e',
                            '--external',
                            action='store_true',
                            help='show only those devices which have \'disconnect\' date')

	uev_parser.add_argument('-n',
                            '--number',
                            type=int,
                            default=-1,
                            help='number of events to show')

	uev_parser.add_argument('-d',
                            '--dates',
                            nargs='+',
                            type=str,
                            default=[],
                            help='filter by DATES')

	uev_parser.add_argument('-c',
                            '--columns',
                            nargs='+',
                            type=str,
                            default=[],
                            help='columns to show (options: \'conn\', '     \
                                                           '\'user\', '     \
                                                           '\'vid\', '      \
                                                           '\'pid\', '      \
                                                           '\'prod\', '     \
                                                           '\'manufact\', ' \
                                                           '\'serial\', '   \
                                                           '\'port\', '     \
                                                           '\'disconn\'.)')

	uev_parser.add_argument('-f',
                            '--files',
                            nargs='+',
                            type=str,
                            default=[],
                            help='obtain log from FILES')

	# ----------------------------------------------------------
	# ------------------------ USB IDs -------------------------
	# ----------------------------------------------------------

	ui_parser = subparsers.add_parser('ids',
                                      help='work with USB IDs')

	ui_subparsers = ui_parser.add_subparsers(dest='ui_subparser')

	# --------------------- USB IDs Search ---------------------

	uis_parser = ui_subparsers.add_parser('search',
                                          help='search by VID and/or PID; ' \
                                               'ids database path is \'{}\''.format(root_dir_join('usb_ids/usb.ids')))

	uis_parser.add_argument('--vid',
                            type=str,
                            default=None,
                            help='vendor ID')
	
	uis_parser.add_argument('--pid',
                            type=str,
                            default=None,
                            help='product ID')

	uis_parser.add_argument('-q',
                            '--quiet',
                            action='store_true',
                            help='supress banner, info messages and user iteraction')

	uis_parser.add_argument('--offline',
                            action='store_true',
                            help='offline mode (no database download/update)')

	# -------------------- USB IDs Download --------------------

	uid_parser = ui_subparsers.add_parser('download',
                                          help='download/update database;' \
                                               'ids database path is \'{}\''.format(root_dir_join('usb_ids/usb.ids')))

	uid_parser.add_argument('-q',
                            '--quiet',
                            action='store_true',
                            help='supress banner, info messages and user iteraction')

	return parser
